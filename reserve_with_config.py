"""
reserve_with_config.py — Version du bot qui lit sa config dans booking_config.json
Lancé automatiquement par l'interface graphique (streamlit_app.py).
"""

import os
import json
import time
from datetime import datetime
from dotenv import load_dotenv
from playwright.sync_api import sync_playwright

# ═══════════════════════════════════════════════════════════════════════════════
#   LECTURE DE LA CONFIG
# ═══════════════════════════════════════════════════════════════════════════════

CONFIG_PATH = os.path.expanduser("~/padel-agent/booking_config.json")

if not os.path.exists(CONFIG_PATH):
    raise SystemExit(f"ERREUR : config introuvable à {CONFIG_PATH}")

with open(CONFIG_PATH) as f:
    cfg = json.load(f)

TARGET_DATE_OFFSET = cfg["target_date_offset"]
TARGET_HOUR        = cfg["target_hour"]
TARGET_MINUTE      = cfg["target_minute"]
COURT_PRIORITY     = cfg["court_priority"]
OPENING_DATETIME   = datetime.fromisoformat(cfg["opening_iso"])
DRY_RUN            = cfg.get("dry_run", False)
HEADLESS           = cfg.get("headless", False)

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
    print(f"[{datetime.now().strftime('%H:%M:%S.%f')[:-3]}] {msg}", flush=True)


target_timestart = TARGET_HOUR * 60 + TARGET_MINUTE
planning_url = (
    f"https://ballejaune.com/reservation/"
    f"#date={TARGET_DATE_OFFSET}&group=0&page=0"
)

log("=" * 70)
log("AGENT DE RÉSERVATION — Config depuis GUI")
log("=" * 70)
log(f"Cible           : J+{TARGET_DATE_OFFSET} à {TARGET_HOUR}h{TARGET_MINUTE:02d}")
log(f"Terrains (ordre): {COURT_PRIORITY}")
log(f"Ouverture       : {OPENING_DATETIME.strftime('%Y-%m-%d %H:%M:%S')}")
log(f"DRY_RUN         : {DRY_RUN}  {'(SÉCURITÉ ACTIVE)' if DRY_RUN else '(VRAIE RÉSERVATION)'}")
log("")

with sync_playwright() as p:
    browser = p.chromium.launch(headless=HEADLESS, slow_mo=0)
    context = browser.new_context()
    page = context.new_page()

    # PHASE 1 : Login
    log("PHASE 1 — Login")
    page.goto(CLUB_URL)
    page.wait_for_selector("#form-username", timeout=15000)
    page.fill("#form-username", BJ_EMAIL)
    page.fill("#form-password", BJ_PASSWORD)
    page.get_by_role("button", name="Se connecter").click()
    page.wait_for_load_state("networkidle", timeout=20000)
    page.wait_for_timeout(800)
    log("✓ Loggé")

    # PHASE 2 : Pré-positionnement
    log(f"PHASE 2 — Navigation vers le planning J+{TARGET_DATE_OFFSET}")
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
    log("✓ Pré-positionné")

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

    for attempt in range(1, 31):
        log(f"PHASE 4 — Tentative #{attempt}")
        try:
            page.reload(wait_until="domcontentloaded", timeout=5000)
        except Exception as e:
            log(f"   ⚠️ Reload échoué : {e}")
            time.sleep(0.3)
            continue

        try:
            page.wait_for_selector("a.slot[data-schedule]", timeout=3000)
        except Exception:
            log(f"   ⚠️ Slots pas chargés en Ajax")
            time.sleep(0.3)
            continue

        for court_name in COURT_PRIORITY:
            sid = COURT_IDS.get(court_name)
            if not sid:
                continue
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

            if "slot-free" not in classes:
                continue
            if "slot-expired" in classes:
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
        page.screenshot(path=os.path.expanduser("~/padel-agent/prod-failure.png"), full_page=True)
        browser.close()
        raise SystemExit(1)

    # PHASE 5 : Partenaires
    log(f"PHASE 5 — Sélection des 3 partenaires (sur {selected_court})")
    try:
        page.locator("#members-table-button-favorite").click(timeout=2000)
        page.wait_for_timeout(400)
    except Exception:
        pass

    for pid in PARTNER_IDS:
        try:
            input_loc = page.locator(f'input[name="with_member[]"][value="{pid}"]')
            row = input_loc.locator("xpath=ancestor::tr[1]")
            row.locator(".enhanced-checkbox-render").first.click(timeout=2000)
            log(f"   ✓ Partenaire {pid}")
        except Exception as e:
            log(f"   ✗ Échec partenaire {pid} : {e}")

    # PHASE 6 : Décision finale
    page.screenshot(path=os.path.expanduser("~/padel-agent/prod-ready-to-reserve.png"), full_page=True)

    if DRY_RUN:
        log("🛡️  DRY_RUN actif → ANNULATION via flèche retour")
        try:
            page.locator(".back-to-schedules-or-choices").first.click()
            page.wait_for_load_state("networkidle", timeout=10000)
        except Exception:
            pass
    else:
        log("🔥 CLIC SUR 'RÉSERVER' — VRAIE RÉSERVATION !")
        page.locator(".reserv-btn-validate").click()
        page.wait_for_load_state("networkidle", timeout=15000)
        page.screenshot(path=os.path.expanduser("~/padel-agent/prod-reservation-done.png"), full_page=True)
        log(f"✓ RÉSERVATION ENVOYÉE — URL = {page.url}")
        log(f"   Terrain : {selected_court}")
        log(f"   Date    : J+{TARGET_DATE_OFFSET}")
        log(f"   Heure   : {TARGET_HOUR}h{TARGET_MINUTE:02d}")

    page.wait_for_timeout(2000)
    browser.close()
    log("=" * 70)
    log("FIN DU SCRIPT")
    log("=" * 70)
