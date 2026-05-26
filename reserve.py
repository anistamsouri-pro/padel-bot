"""
reserve.py — Agent de réservation automatique sur ballejaune.com
Étapes A + B + C en mode test (DRY_RUN = True par défaut).
"""

import os
from dotenv import load_dotenv
from playwright.sync_api import sync_playwright

# Charger les identifiants depuis .env
load_dotenv()
BJ_EMAIL = os.getenv("BJ_EMAIL")
BJ_PASSWORD = os.getenv("BJ_PASSWORD")
CLUB_URL = os.getenv("CLUB_URL")

if not (BJ_EMAIL and BJ_PASSWORD and CLUB_URL):
    raise SystemExit("ERREUR : variables manquantes dans .env (BJ_EMAIL, BJ_PASSWORD, CLUB_URL).")

with sync_playwright() as p:
    # Lancer Chromium en mode visible, avec un léger ralenti pour observer
    browser = p.chromium.launch(headless=False, slow_mo=300)
    context = browser.new_context()
    page = context.new_page()

    # === ÉTAPE A : LOGIN ===
    print("→ Ouverture de la page de réservation...")
    page.goto(CLUB_URL)

    print("→ Attente du formulaire de login...")
    page.wait_for_selector("#form-username", timeout=15000)

    print("→ Remplissage des identifiants...")
    page.fill("#form-username", BJ_EMAIL)
    page.fill("#form-password", BJ_PASSWORD)

    print("→ Clic sur 'Se connecter'...")
    page.get_by_role("button", name="Se connecter").click()

    print("→ Attente du chargement post-login...")
    page.wait_for_load_state("networkidle", timeout=20000)
    page.screenshot(path="login-success.png", full_page=True)
    print("✓ Login validé. Capture : login-success.png")

    # === ÉTAPE B : NAVIGATION VERS LE PLANNING ===
    TARGET_DATE = 0
    TARGET_GROUP = 0
    TARGET_PAGE = 0
    planning_url = (
        f"https://ballejaune.com/reservation/"
        f"#date={TARGET_DATE}&group={TARGET_GROUP}&page={TARGET_PAGE}"
    )
    print(f"→ Navigation vers le planning : {planning_url}")
    page.goto(planning_url)
    page.wait_for_load_state("networkidle", timeout=20000)
    page.wait_for_timeout(2000)
    page.screenshot(path="planning.png", full_page=True)
    print("✓ Planning capturé : planning.png")

    # Fermeture des bandeaux éventuels (cookies, notifications)
    print("\n→ Fermeture des bandeaux éventuels (cookies, notifications)...")
    for label in ["Plus tard", "OK"]:
        try:
            page.get_by_role("button", name=label).click(timeout=1500)
            print(f"   ✓ Bouton '{label}' cliqué")
        except Exception:
            pass

    # === ÉTAPE B.3 : DÉCOUVERTE DES TERRAINS PADEL D1-D5 ===
    print("\n=== DÉCOUVERTE DES TERRAINS PADEL ===")
    all_padel = page.locator(".schedule-container").filter(has_text="PADEL D")
    schedule_ids = {}
    for i in range(all_padel.count()):
        container = all_padel.nth(i)
        name_elem = container.locator(".schedule-header-name .media-body").first
        name = " ".join((name_elem.text_content() or "").split())
        first_slot = container.locator("a[data-schedule]").first
        sid = first_slot.get_attribute("data-schedule") if first_slot.count() > 0 else None
        if sid and name.startswith("PADEL D") and len(name) >= 8:
            schedule_ids[name] = sid

    print(f"→ {len(schedule_ids)} terrains PADEL D1-D5 identifiés :")
    for n, s in schedule_ids.items():
        print(f"   {n:25s} → {s}")

    # === ÉTAPE B.4 : CLIC SUR LE 1ER CRÉNEAU LIBRE DU TERRAIN CIBLE ===
    TARGET_COURT = "PADEL D3"
    target_schedule_id = schedule_ids.get(TARGET_COURT)
    if not target_schedule_id:
        print(f"\n✗ {TARGET_COURT} introuvable.")
        browser.close()
        raise SystemExit()

    print(f"\n=== B.4 : CLIC SUR UN CRÉNEAU LIBRE ({TARGET_COURT}) ===")
    free_slot = page.locator(
        f'a.slot.slot-free-full[data-schedule="{target_schedule_id}"]'
    ).first

    if free_slot.count() == 0:
        print(f"✗ Aucun créneau libre sur {TARGET_COURT} aujourd'hui.")
        browser.close()
        raise SystemExit()

    timestart = free_slot.get_attribute("data-timestart")
    duration = free_slot.get_attribute("data-duration")
    h = int(timestart) // 60
    m = int(timestart) % 60
    print(f"✓ 1er créneau libre détecté : {h}h{m:02d} (durée {duration}min, timestart={timestart})")

    print("→ Clic sur le créneau...")
    free_slot.scroll_into_view_if_needed()
    free_slot.click()

    print("→ Attente de la page de réservation...")
    page.wait_for_url("**action=1**", timeout=10000)
    page.wait_for_load_state("networkidle", timeout=10000)
    page.screenshot(path="booking-page.png", full_page=True)
    print(f"✓ Sur la page de réservation. URL = {page.url}")

    print("\n→ Éléments détectés sur la page de réservation :")
    print(f"   .reserv-btn-validate         (bouton Réserver) : {page.locator('.reserv-btn-validate').count()}")
    print(f"   .ajaxtable-search-input      (recherche)       : {page.locator('.ajaxtable-search-input').count()}")
    print(f"   #members-table               (membres)         : {page.locator('#members-table').count()}")
    print(f"   .back-to-schedules-or-choices (flèche retour)  : {page.locator('.back-to-schedules-or-choices').count()}")

    # === ÉTAPE C : SÉLECTION DES PARTENAIRES + (ÉVENTUEL) CLIC RÉSERVER ===
    DRY_RUN = True  # ⚠️ NE PASSER À False QUE pour une VRAIE réservation

    def _norm(s):
        """Normalise les espaces multiples en un seul espace."""
        return " ".join((s or "").split())

    partners = [os.getenv(k) for k in ("PARTNER_1", "PARTNER_2", "PARTNER_3")]
    partners = [p for p in partners if p]

    selection_ok = True
    partner_ids = {}

    if not partners:
        print("\n⚠️  Aucun PARTNER_x dans .env, sélection ignorée.")
        selection_ok = False
    else:
        print(f"\n=== ÉTAPE C : Sélection de {len(partners)} partenaire(s) ===")

        # Bascule sur la vue "Mes favoris"
        print("\n→ Bascule sur la vue 'Mes favoris'...")
        favoris_selectors = [
            "#members-table-button-favorite",      # ID stable (le plus fiable)
            "a:has-text('Mes favoris')",
            "button:has-text('Mes favoris')",
            ".btn-heart",
            "[role='button']:has-text('Mes favoris')",
        ]
        favoris_clicked = False
        for selector in favoris_selectors:
            try:
                page.locator(selector).first.click(timeout=1500)
                favoris_clicked = True
                print(f"   ✓ Cliqué via sélecteur : {selector}")
                break
            except Exception:
                pass

        if favoris_clicked:
            page.wait_for_timeout(800)
        else:
            print("   ⚠️ Aucun sélecteur 'Mes favoris' n'a fonctionné.")
            print("   → On continue sur la liste complète (peut-être plus lent).")

        # Recherche + cochage de chaque partenaire
        for i, partner_name in enumerate(partners, 1):
            print(f"\n→ Partenaire {i} : '{partner_name}'")
            search_query = partner_name.split(",")[0].strip()
            print(f"   → Recherche : '{search_query}'")

            search = page.locator(".ajaxtable-search-input")
            search.fill(search_query)
            search.dispatch_event("input")
            search.dispatch_event("keyup")
            page.wait_for_timeout(1500)

            current_value = search.input_value()
            if current_value != search_query:
                print(f"   ⚠️ Valeur attendue '{search_query}', trouvée '{current_value}'")

            rows = page.locator("#members-table tbody tr:visible")
            n_rows = rows.count()
            print(f"   → {n_rows} ligne(s) visible(s) après filtrage")

            norm_target = _norm(partner_name)
            found_idx = -1
            for j in range(n_rows):
                row_text = _norm(rows.nth(j).text_content() or "")
                if norm_target in row_text:
                    found_idx = j
                    break

            if found_idx < 0:
                print(f"   ✗ Aucune ligne visible ne contient '{partner_name}'.")
                if n_rows > 0:
                    print(f"   → Top 5 résultats visibles :")
                    for j in range(min(5, n_rows)):
                        txt = _norm(rows.nth(j).text_content() or "")[:100]
                        print(f"      [{j}] {txt}")
                selection_ok = False
                break

            checkbox = rows.nth(found_idx).locator('input[name="with_member[]"]')
            member_id = checkbox.get_attribute("value")
            partner_ids[partner_name] = member_id

            # La case input est invisible (display:none) → on clique sur ce qui est VRAIMENT visible.
            # Stratégies par ordre de préférence : le label stylé, puis la cellule, puis la ligne.
            click_targets = [
                ".enhanced-checkbox-render",  # le <label> visible
                "td.checkbox-row",            # la cellule contenant la case
                "td.link-row",                # cellule alternative cliquable
            ]
            checkbox_done = False
            for sel in click_targets:
                target = rows.nth(found_idx).locator(sel).first
                if target.count() > 0:
                    try:
                        target.click(timeout=3000)
                        checkbox_done = True
                        print(f"   ✓ Cliqué via '{sel}' — member_id = {member_id}")
                        break
                    except Exception:
                        continue

            if not checkbox_done:
                # Dernier recours : dispatch_event directement sur l'input caché
                try:
                    checkbox.dispatch_event("click")
                    checkbox_done = True
                    print(f"   ✓ Coché via dispatch_event — member_id = {member_id}")
                except Exception as e:
                    print(f"   ✗ Impossible de cocher : {e}")
                    selection_ok = False
                    break

            # Vérifier que la case est bien cochée (sécurité)
            page.wait_for_timeout(250)
            try:
                is_checked = checkbox.is_checked()
                if not is_checked:
                    print(f"   ⚠️ La case ne semble PAS cochée après clic (état checked=False)")
            except Exception:
                pass

        # Vider la recherche après les sélections (non bloquant : la barre peut
        # être cachée par ballejaune quand le bon nombre de joueurs est atteint)
        try:
            search = page.locator(".ajaxtable-search-input")
            search.fill("", timeout=2000)
            search.dispatch_event("input")
            search.dispatch_event("keyup")
            page.wait_for_timeout(300)
        except Exception:
            print("   (Barre de recherche cachée — ballejaune l'a probablement "
                  "masquée car les 3 partenaires suffisent. On continue.)")

    page.screenshot(path="ready-to-reserve.png", full_page=True)
    print("\n✓ Capture 'ready-to-reserve.png' enregistrée.")

    if partner_ids:
        print("\n→ IDs des partenaires (à hardcoder pour la prod ultra-rapide) :")
        for n, mid in partner_ids.items():
            print(f"   {n:25s} → {mid}")

    # === DÉCISION FINALE : RÉSERVER OU ANNULER ===
    if DRY_RUN or not selection_ok:
        reason = "DRY_RUN actif" if DRY_RUN else "sélection partenaire échouée"
        print(f"\n🛡️  {reason} → on N'EFFECTUE PAS la réservation.")
        print("→ Clic sur la flèche retour pour annuler proprement...")
        page.locator(".back-to-schedules-or-choices").first.click()
        page.wait_for_load_state("networkidle", timeout=10000)
        page.screenshot(path="back-to-planning.png", full_page=True)
        print(f"✓ Retour effectué. URL = {page.url}")
    else:
        print("\n🔥 DRY_RUN = False → CLIC SUR 'Réserver' (vraie réservation !)")
        page.locator(".reserv-btn-validate").click()
        page.wait_for_load_state("networkidle", timeout=15000)
        page.screenshot(path="reservation-done.png", full_page=True)
        print(f"✓ Réservation envoyée. URL = {page.url}")

    print("\n→ Pause 5 secondes...")
    page.wait_for_timeout(5000)

    browser.close()
    print("✓ Fin du script.")
