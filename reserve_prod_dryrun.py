"""
reserve_prod_dryrun.py — Test DRY_RUN du script de production
À lancer entre 15h45 et 15h50 pour validation avant le vrai run à 17h00.
"""

import os
import time
from datetime import datetime
from dotenv import load_dotenv
from playwright.sync_api import sync_playwright

# ═══════════════════════════════════════════════════════════════════════════════
#   CONFIGURATION — DRY_RUN
# ═══════════════════════════════════════════════════════════════════════════════

# Cible : créneau d'aujourd'hui 21h00 (probablement déjà libre et ouvert)
TARGET_DATE_OFFSET = 0
TARGET_HOUR        = 21
TARGET_MINUTE      = 0
COURT_PRIORITY     = ["D3", "D1", "D2", "D4", "D5"]

# Ouverture à 15h50 aujourd'hui (test rapide du timing)
OPENING_DATETIME   = datetime(2026, 5, 26, 16, 12, 0)

# ⚠️ DRY_RUN ACTIF — on N'EFFECTUE PAS la réservation
DRY_RUN            = True

# Visible pour observer le test
HEADLESS           = False

# ═══════════════════════════════════════════════════════════════════════════════
#   CONSTANTES (hardcodées)
# ═══════════════════════════════════════════════════════════════════════════════

COURT_IDS = {
    "D1": "75232", "D2": "75237", "D3": "75238",
    "D4": "75239", "D5": "75240",
}

PARTNER_IDS = [
    "2100520",   # SARL DIGITEASE 2, Ste
    "1864766",   # SARL DIGITEASE, Ste
    "1861177",   # RISKCON ADVISORY, 1
]

# ═══════════════════════════════════════════════════════════════════════════════
#   EXÉCUTION
# ═══════════════════════════════════════════════════════════════════════════════

load_dotenv()
BJ_EMAIL    = os.getenv("BJ_EMAIL")
BJ_PASSWORD = os.getenv("BJ_PASSWORD")
CLUB_URL    = os.getenv("CLUB_URL")

if not (BJ_EMAIL and BJ_PASSWORD and CLUB_URL):
    raise SystemExit("ERREUR : variables manquantes dans .env")


def log(msg):
    print(f"[{datetime.now().strftime('%H:%M:%S.%f')[:-3]}] {msg}")


target_timestart = TARGET_HOUR * 60 + TARGET_MINUTE
planning_url = (
    f"https://ballejaune.com/reservation/"
    f"#date={TARGET_DATE_OFFSET}&group=0&page=0"
)

log("=" * 70)
log("DRY_RUN DU SCRIPT DE PRODUCTION")
log("=" * 70)
log(f"Cible           : J+{TARGET_DATE_OFFSET} à {TARGET_HOUR}h{TARGET_MINUTE:02d}")
log(f"Terrains (ordre): {COURT_PRIORITY}")
log(f"Ouverture       : {OPENING_DATETIME.strftime('%Y-%m-%d %H:%M:%S')}")
log(f"DRY_RUN         : {DRY_RUN}  (SÉCURITÉ ACTIVE, aucune réservation possible)")
log("")

with sync_playwright() as p:
    browser = p.chromium.launch(headless=HEADLESS, slow_mo=0)
    context = browser.new_context()
    page = context.new_page()

    # PHASE 1 : Login
    log("PHASE 1 — Login")
    t0 = time.time()
    page.goto(CLUB_URL)
    page.wait_for_selector("#form-username", timeout=15000)
    page.fill("#form-username", BJ_EMAIL)
    page.fill("#form-password", BJ_PASSWORD)
    page.get_by_role("button", name="Se connecter").click()
    page.wait_for_load_state("networkidle", timeout=20000)
    page.wait_for_timeout(800)  # laisser le redirect post-login se terminer
    log(f"✓ Loggé en {time.time()-t0:.2f}s")

    # PHASE 2 : Pré-positionnement
    log(f"PHASE 2 — Navigation vers le planning J+{TARGET_DATE_OFFSET}")
    t0 = time.time()
    try:
        page.goto(planning_url, wait_until="domcontentloaded", timeout=15000)
    except Exception as e:
        log(f"   ⚠️ Première tentative échouée ({e.__class__.__name__}), retry...")
        page.wait_for_timeout(1000)
        page.goto(planning_url, wait_until="domcontentloaded", timeout=15000)
    page.wait_for_load_state("networkidle", timeout=15000)
    page.wait_for_timeout(800)
    for label in ["Plus tard", "OK"]:
        try:
            page.get_by_role("button", name=label).click(timeout=1000)
        except Exception:
            pass
    log(f"✓ Pré-positionné en {time.time()-t0:.2f}s")

    # PHASE 3 : Attente
    now = datetime.now()
    wait_seconds = (OPENING_DATETIME - now).total_seconds()
    log(f"PHASE 3 — Attente : {wait_seconds:.1f}s jusqu'à {OPENING_DATETIME.strftime('%H:%M:%S')}")

    if wait_seconds > 2:
        time.sleep(wait_seconds - 1.5)
    while datetime.now() < OPENING_DATETIME:
        time.sleep(0.005)

    log("⚡⚡⚡ OUVERTURE ! ⚡⚡⚡")

    # PHASE 4 : Action
    booking_reached = False
    selected_court  = None
    t_action_start  = time.time()

    for attempt in range(1, 16):    # 15 tentatives max au lieu de 30
        log(f"PHASE 4 — Tentative #{attempt}")
        try:
            page.reload(wait_until="domcontentloaded", timeout=5000)
        except Exception as e:
            log(f"   ⚠️ Reload échoué : {e}")
            time.sleep(0.3)
            continue

        # Attendre que les slots soient chargés en Ajax après le reload
        try:
            page.wait_for_selector("a.slot[data-schedule]", timeout=3000)
        except Exception:
            log(f"   ⚠️ Aucun slot dans le DOM (Ajax pas revenu)")
            time.sleep(0.3)
            continue

        for court_name in COURT_PRIORITY:
            sid = COURT_IDS[court_name]
            slot = page.locator(
                f'a.slot[data-schedule="{sid}"][data-timestart="{target_timestart}"]'
            ).first

            if slot.count() == 0:
                if attempt == 1:
                    log(f"      {court_name}: créneau introuvable dans le DOM")
                continue

            classes = slot.get_attribute("class") or ""
            is_free    = "slot-free"    in classes
            is_full    = "slot-free-full" in classes
            is_expired = "slot-expired" in classes
            is_booked  = "slot-booked"  in classes

            if attempt == 1:
                log(f"      {court_name}: free={is_free} full={is_full} "
                    f"booked={is_booked} expired={is_expired}")
                log(f"         classes='{classes[:100]}'")

            if not is_free or is_expired:
                continue

            log(f"   → Clic sur {court_name}")
            try:
                slot.click(timeout=1500)
            except Exception as e:
                log(f"   ✗ Clic échoué : {e}")
                continue

            page.wait_for_timeout(400)
            popup = page.locator("text=Réservation indisponible")
            if popup.count() > 0:
                log(f"   ⚠️ Popup 'indisponible' — on ferme et on recommence")
                try:
                    page.get_by_role("button", name="OK").click(timeout=1000)
                except Exception:
                    pass
                page.wait_for_timeout(150)
                continue

            if "action=1" in page.url:
                log(f"   ✓ Sur la page de réservation avec {court_name} !")
                booking_reached = True
                selected_court  = court_name
                break

        if booking_reached:
            break
        time.sleep(0.2)

    if not booking_reached:
        log("✗ ÉCHEC : aucun créneau cliqué après 30 tentatives.")
        page.screenshot(path="prod-failure.png", full_page=True)
        browser.close()
        raise SystemExit(1)

    log(f"✓ Page de réservation atteinte en {time.time()-t_action_start:.2f}s")

    # PHASE 5 : Partenaires (rapide, par ID)
    log("PHASE 5 — Sélection des 3 partenaires")
    t_p_start = time.time()
    try:
        page.locator("#members-table-button-favorite").click(timeout=2000)
        page.wait_for_timeout(400)
        log("   ✓ 'Mes favoris' activé")
    except Exception:
        log("   ⚠️ Mes favoris introuvable")

    for pid in PARTNER_IDS:
        try:
            input_loc = page.locator(f'input[name="with_member[]"][value="{pid}"]')
            row = input_loc.locator("xpath=ancestor::tr[1]")
            row.locator(".enhanced-checkbox-render").first.click(timeout=2000)
            log(f"   ✓ Partenaire {pid}")
        except Exception as e:
            log(f"   ✗ Échec partenaire {pid} : {e}")
    log(f"✓ Partenaires sélectionnés en {time.time()-t_p_start:.2f}s")

    # PHASE 6 : DRY_RUN actif → on annule
    page.screenshot(path="dryrun-ready-to-reserve.png", full_page=True)
    log("✓ Capture 'dryrun-ready-to-reserve.png' enregistrée")

    log("🛡️  DRY_RUN actif → ANNULATION via flèche retour")
    try:
        page.locator(".back-to-schedules-or-choices").first.click()
        page.wait_for_load_state("networkidle", timeout=10000)
        log("✓ Retour propre")
    except Exception as e:
        log(f"⚠️ Retour échoué : {e}")

    page.wait_for_timeout(2000)
    browser.close()
    log("=" * 70)
    log("FIN DU DRY_RUN")
    log("=" * 70)
