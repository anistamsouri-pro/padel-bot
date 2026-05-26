"""
reserve_prod.py — Agent de production pour ballejaune.com (Les Pyramides)
Optimisé pour gagner la course aux clics à l'heure d'ouverture des réservations.

Stratégie :
  1. Login + navigation au planning J-cible avant l'heure d'ouverture
  2. Attente précise à la milliseconde de l'heure d'ouverture
  3. Reload + clic immédiat sur le créneau cible (avec fallback sur d'autres terrains)
  4. Cochage des 3 partenaires par leurs IDs (pas de recherche = ultra rapide)
  5. Clic "Réserver"
"""

import os
import time
from datetime import datetime
from dotenv import load_dotenv
from playwright.sync_api import sync_playwright

# ═══════════════════════════════════════════════════════════════════════════════
#   CONFIGURATION DE LA RÉSERVATION
#   Modifie ces valeurs pour chaque nouvelle session
# ═══════════════════════════════════════════════════════════════════════════════

# Cible
TARGET_DATE_OFFSET = 0          # 0=aujourd'hui, 1=demain, 2=après-demain, ...
TARGET_HOUR        = 21         # heure du créneau (0–23)
TARGET_MINUTE      = 0          # minute (0 ou 30 sur des créneaux 1h30)
COURT_PRIORITY     = ["D3", "D4", "D5", "D1", "D2"]   # D3 en premier, puis fallback

# Heure d'ouverture du créneau (passé = action immédiate, pas d'attente)
OPENING_DATETIME   = datetime(2026, 5, 26, 16, 0, 0)   # déjà passée → exécution direct

# Mode sécurité — TRES IMPORTANT
DRY_RUN            = False      # True = NE PAS valider la réservation finale

# Mode visible/headless
HEADLESS           = False      # False pour observer le 1er run, True ensuite

# ═══════════════════════════════════════════════════════════════════════════════
#   CONSTANTES (hardcodées pour gagner du temps)
# ═══════════════════════════════════════════════════════════════════════════════

COURT_IDS = {
    "D1": "75232",
    "D2": "75237",
    "D3": "75238",
    "D4": "75239",
    "D5": "75240",
}

# IDs des 3 partenaires (cf. récap des tests DRY_RUN)
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
    """Print avec timestamp précis (utile pour analyser la chronologie)."""
    print(f"[{datetime.now().strftime('%H:%M:%S.%f')[:-3]}] {msg}")


target_timestart = TARGET_HOUR * 60 + TARGET_MINUTE
planning_url = (
    f"https://ballejaune.com/reservation/"
    f"#date={TARGET_DATE_OFFSET}&group=0&page=0"
)

log("=" * 70)
log("AGENT DE RÉSERVATION BALLEJAUNE — MODE PRODUCTION")
log("=" * 70)
log(f"Cible           : J+{TARGET_DATE_OFFSET} à {TARGET_HOUR}h{TARGET_MINUTE:02d}")
log(f"Terrains (ordre): {COURT_PRIORITY}")
log(f"Ouverture       : {OPENING_DATETIME.strftime('%Y-%m-%d %H:%M:%S')}")
log(f"DRY_RUN         : {DRY_RUN}  {'(SÉCURITÉ ACTIVE)' if DRY_RUN else '(VRAIE RÉSERVATION)'}")
log(f"Headless        : {HEADLESS}")
log("")

with sync_playwright() as p:
    browser = p.chromium.launch(headless=HEADLESS, slow_mo=0)
    context = browser.new_context()
    page = context.new_page()

    # ─── PHASE 1 : LOGIN ──────────────────────────────────────────────────────
    log("PHASE 1 — Login")
    page.goto(CLUB_URL)
    page.wait_for_selector("#form-username", timeout=15000)
    page.fill("#form-username", BJ_EMAIL)
    page.fill("#form-password", BJ_PASSWORD)
    page.get_by_role("button", name="Se connecter").click()
    page.wait_for_load_state("networkidle", timeout=20000)
    page.wait_for_timeout(800)  # laisser le redirect post-login se terminer
    log("✓ Loggé")

    # ─── PHASE 2 : PRÉ-POSITIONNEMENT ─────────────────────────────────────────
    log(f"PHASE 2 — Navigation vers le planning J+{TARGET_DATE_OFFSET}")
    try:
        page.goto(planning_url, wait_until="domcontentloaded", timeout=15000)
    except Exception as e:
        log(f"   ⚠️ Première tentative échouée ({e.__class__.__name__}), retry...")
        page.wait_for_timeout(1000)
        page.goto(planning_url, wait_until="domcontentloaded", timeout=15000)
    page.wait_for_load_state("networkidle", timeout=15000)
    page.wait_for_timeout(800)

    # Fermer bandeaux cookies / notifications
    for label in ["Plus tard", "OK"]:
        try:
            page.get_by_role("button", name=label).click(timeout=1000)
        except Exception:
            pass
    log("✓ Pré-positionné")

    # ─── PHASE 3 : ATTENTE PRÉCISE DE L'OUVERTURE ────────────────────────────
    now = datetime.now()
    wait_seconds = (OPENING_DATETIME - now).total_seconds()
    log(f"PHASE 3 — Attente : {wait_seconds:.1f}s jusqu'à {OPENING_DATETIME.strftime('%H:%M:%S')}")

    if wait_seconds > 2:
        # Sommeil grossier jusqu'à 1.5s avant l'heure
        time.sleep(wait_seconds - 1.5)

    # Polling rapide à 5ms pour précision finale
    while datetime.now() < OPENING_DATETIME:
        time.sleep(0.005)

    log(f"⚡⚡⚡ OUVERTURE ! ⚡⚡⚡")

    # ─── PHASE 4 : ACTION — RELOAD + CLIC SUR LE CRÉNEAU ─────────────────────
    booking_reached = False
    selected_court  = None
    max_attempts    = 30   # ~15 secondes de tentatives max

    for attempt in range(1, max_attempts + 1):
        log(f"PHASE 4 — Tentative #{attempt} : reload + clic")
        try:
            page.reload(wait_until="domcontentloaded", timeout=5000)
        except Exception as e:
            log(f"   ⚠️ Reload échoué : {e}, on retente")
            time.sleep(0.3)
            continue

        # Attendre que les slots soient chargés en Ajax après le reload
        try:
            page.wait_for_selector("a.slot[data-schedule]", timeout=3000)
        except Exception:
            log(f"   ⚠️ Slots pas chargés en Ajax")
            time.sleep(0.3)
            continue

        # Tente chaque terrain par ordre de préférence
        for court_name in COURT_PRIORITY:
            sid = COURT_IDS[court_name]
            slot = page.locator(
                f'a.slot[data-schedule="{sid}"][data-timestart="{target_timestart}"]'
            ).first

            if slot.count() == 0:
                if attempt == 1:
                    log(f"      {court_name}: créneau introuvable")
                continue

            classes = slot.get_attribute("class") or ""
            if attempt == 1:
                log(f"      {court_name}: classes='{classes[:80]}'")

            # On ne tente que les créneaux qui ont l'air libres
            if "slot-free" not in classes:
                continue
            if "slot-expired" in classes:
                continue

            log(f"   → Clic sur {court_name} (classes : {classes[:80]}...)")
            try:
                slot.click(timeout=1500)
            except Exception as e:
                log(f"   ✗ Clic échoué : {e}")
                continue

            # Attendre 400ms pour voir si popup "indisponible" apparaît
            page.wait_for_timeout(400)

            popup = page.locator("text=Réservation indisponible")
            if popup.count() > 0:
                log(f"   ⚠️ Popup 'Réservation indisponible' — on ferme et on recommence")
                try:
                    page.get_by_role("button", name="OK").click(timeout=1000)
                except Exception:
                    pass
                page.wait_for_timeout(150)
                continue   # essayer le terrain suivant ou re-loop

            # Vérifier qu'on est arrivé sur la page de réservation
            if "action=1" in page.url:
                log(f"   ✓ Sur la page de réservation avec {court_name} !")
                booking_reached = True
                selected_court  = court_name
                break

        if booking_reached:
            break

        # Petite pause avant la prochaine tentative complète
        time.sleep(0.2)

    if not booking_reached:
        log(f"✗ ÉCHEC : aucun créneau cliqué après {max_attempts} tentatives.")
        page.screenshot(path="prod-failure.png", full_page=True)
        browser.close()
        raise SystemExit(1)

    # ─── PHASE 5 : SÉLECTION DES PARTENAIRES (rapide, par ID direct) ─────────
    log(f"PHASE 5 — Sélection des 3 partenaires (sur {selected_court})")

    # Bascule sur "Mes favoris" pour que les partenaires soient dans les rangées visibles
    try:
        page.locator("#members-table-button-favorite").click(timeout=2000)
        page.wait_for_timeout(400)
        log("   ✓ Vue 'Mes favoris' activée")
    except Exception:
        log("   ⚠️ Bouton 'Mes favoris' introuvable — on continue sans bascule")

    # Clic direct sur chaque partenaire via son ID
    for pid in PARTNER_IDS:
        try:
            input_loc = page.locator(f'input[name="with_member[]"][value="{pid}"]')
            row = input_loc.locator("xpath=ancestor::tr[1]")
            row.locator(".enhanced-checkbox-render").first.click(timeout=2000)
            log(f"   ✓ Partenaire {pid} coché")
        except Exception as e:
            log(f"   ✗ Échec partenaire {pid} : {e}")

    # ─── PHASE 6 : DÉCISION FINALE (RÉSERVER OU ANNULER) ─────────────────────
    page.screenshot(path="prod-ready-to-reserve.png", full_page=True)
    log("✓ Capture 'prod-ready-to-reserve.png' (avant clic final)")

    if DRY_RUN:
        log("🛡️  DRY_RUN actif → ANNULATION par flèche retour")
        try:
            page.locator(".back-to-schedules-or-choices").first.click()
            page.wait_for_load_state("networkidle", timeout=10000)
            log("✓ Retour propre")
        except Exception as e:
            log(f"⚠️ Retour échoué : {e}")
    else:
        log("🔥 CLIC SUR 'RÉSERVER' — VRAIE RÉSERVATION !")
        page.locator(".reserv-btn-validate").click()
        page.wait_for_load_state("networkidle", timeout=15000)
        page.screenshot(path="prod-reservation-done.png", full_page=True)
        log(f"✓ RÉSERVATION ENVOYÉE — URL = {page.url}")
        log(f"   Terrain : {selected_court}")
        log(f"   Date    : J+{TARGET_DATE_OFFSET}")
        log(f"   Heure   : {TARGET_HOUR}h{TARGET_MINUTE:02d}")

    page.wait_for_timeout(3000)
    browser.close()
    log("=" * 70)
    log("FIN DU SCRIPT")
    log("=" * 70)
