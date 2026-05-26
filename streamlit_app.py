"""
streamlit_app.py — Interface graphique du Padel Bot (dark, polished)
Lance avec : streamlit run streamlit_app.py
"""

import streamlit as st
from datetime import datetime, date, timedelta, time as time_module
import json
import os
import subprocess

# ═══════════════════════════════════════════════════════════════════════════════
#   CONFIG STREAMLIT
# ═══════════════════════════════════════════════════════════════════════════════

st.set_page_config(
    page_title="Padel Bot — Les Pyramides",
    page_icon="🎾",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ═══════════════════════════════════════════════════════════════════════════════
#   CSS — DARK PROFESSIONAL THEME
# ═══════════════════════════════════════════════════════════════════════════════

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Manrope:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;600&display=swap');

/* ─── Globals ─── */
.stApp {
    background:
        radial-gradient(1200px 600px at 10% -10%, rgba(212, 255, 54, 0.08) 0%, transparent 60%),
        radial-gradient(900px 500px at 100% 0%, rgba(94, 185, 255, 0.06) 0%, transparent 60%),
        radial-gradient(700px 400px at 50% 100%, rgba(45, 212, 122, 0.05) 0%, transparent 60%),
        linear-gradient(180deg, #07091a 0%, #0d1126 50%, #07091a 100%);
    background-attachment: fixed;
    font-family: 'Manrope', -apple-system, BlinkMacSystemFont, sans-serif;
    color: #e8eaf2;
    min-height: 100vh;
}

/* Subtle moving noise/grain overlay */
.stApp::before {
    content: "";
    position: fixed;
    inset: 0;
    pointer-events: none;
    z-index: 0;
    opacity: 0.4;
    background-image:
        radial-gradient(rgba(255,255,255,0.04) 1px, transparent 1px);
    background-size: 3px 3px;
}

/* Hide Streamlit chrome */
#MainMenu, header[data-testid="stHeader"], footer { visibility: hidden; }
.stDeployButton { display: none; }

/* Main container width */
.block-container {
    max-width: 980px !important;
    padding-top: 2rem !important;
    padding-bottom: 4rem !important;
    position: relative;
    z-index: 1;
}

/* ─── Hero ─── */
.hero {
    position: relative;
    text-align: center;
    padding: 2.5rem 1rem 1.5rem;
    margin-bottom: 2rem;
    overflow: hidden;
    border-radius: 24px;
    background:
        linear-gradient(135deg, rgba(212, 255, 54, 0.04) 0%, rgba(94, 185, 255, 0.03) 100%);
    border: 1px solid rgba(255, 255, 255, 0.06);
    backdrop-filter: blur(8px);
}

.hero-eyebrow {
    display: inline-flex;
    align-items: center;
    gap: 8px;
    padding: 6px 14px;
    border-radius: 999px;
    background: rgba(212, 255, 54, 0.1);
    border: 1px solid rgba(212, 255, 54, 0.25);
    color: #d4ff36;
    font-size: 12px;
    font-weight: 600;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    margin-bottom: 1.5rem;
}

.hero-eyebrow .dot {
    width: 6px; height: 6px; border-radius: 999px;
    background: #d4ff36;
    box-shadow: 0 0 12px #d4ff36;
    animation: pulse 2s ease-in-out infinite;
}

@keyframes pulse {
    0%, 100% { opacity: 1; transform: scale(1); }
    50% { opacity: 0.6; transform: scale(1.3); }
}

.hero-title {
    font-size: clamp(2.5rem, 5vw, 4rem);
    font-weight: 800;
    line-height: 1.05;
    letter-spacing: -0.03em;
    margin: 0 0 1rem 0;
    background: linear-gradient(180deg, #ffffff 0%, #b0b5cc 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
}

.hero-title .accent {
    background: linear-gradient(135deg, #d4ff36 0%, #a8ff00 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    position: relative;
    display: inline-block;
}

.hero-subtitle {
    font-size: 1.05rem;
    color: #8b91a8;
    margin: 0 auto;
    max-width: 540px;
    line-height: 1.6;
    font-weight: 400;
}

/* Floating tennis ball */
.ball {
    position: absolute;
    width: 60px; height: 60px;
    border-radius: 50%;
    background: radial-gradient(circle at 30% 30%, #e6ff66 0%, #c0e62e 50%, #8aa800 100%);
    box-shadow:
        0 0 40px rgba(212, 255, 54, 0.5),
        inset -8px -8px 14px rgba(0,0,0,0.2);
    opacity: 0.85;
}

.ball::before, .ball::after {
    content: "";
    position: absolute;
    inset: 0;
    border-radius: 50%;
    border: 2px solid rgba(255,255,255,0.4);
    clip-path: polygon(0 0, 100% 0, 100% 50%, 50% 100%, 0 100%);
}

.ball.ball-1 { top: 15%; right: 8%; animation: float 6s ease-in-out infinite; }
.ball.ball-2 { bottom: 20%; left: 6%; width: 36px; height: 36px; opacity: 0.4; animation: float 8s ease-in-out infinite 2s; }

@keyframes float {
    0%, 100% { transform: translateY(0) rotate(0deg); }
    50% { transform: translateY(-20px) rotate(180deg); }
}

/* ─── Section card ─── */
.card {
    background: linear-gradient(180deg, rgba(255,255,255,0.04) 0%, rgba(255,255,255,0.02) 100%);
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 20px;
    padding: 2rem;
    margin-bottom: 1.5rem;
    backdrop-filter: blur(12px);
    transition: border-color 0.3s ease, transform 0.3s ease;
}

.card:hover {
    border-color: rgba(212, 255, 54, 0.2);
}

.section-label {
    display: flex;
    align-items: center;
    gap: 12px;
    margin-bottom: 1.25rem;
}

.section-label .num {
    width: 32px; height: 32px;
    border-radius: 10px;
    background: linear-gradient(135deg, rgba(212, 255, 54, 0.15) 0%, rgba(212, 255, 54, 0.05) 100%);
    border: 1px solid rgba(212, 255, 54, 0.3);
    color: #d4ff36;
    display: flex;
    align-items: center;
    justify-content: center;
    font-weight: 700;
    font-size: 14px;
}

.section-label h3 {
    margin: 0;
    font-size: 1.2rem;
    font-weight: 700;
    color: #ffffff;
    letter-spacing: -0.01em;
}

/* ─── Streamlit widgets dark theme ─── */
label, .stMarkdown p, .stMarkdown li, .stCaption, [data-testid="stMarkdownContainer"] {
    color: #b8bdd4 !important;
}

/* Inputs (date, text) */
.stDateInput input,
.stTextInput input,
.stTimeInput input {
    background: rgba(255,255,255,0.04) !important;
    border: 1px solid rgba(255,255,255,0.1) !important;
    color: #ffffff !important;
    border-radius: 12px !important;
    padding: 12px 14px !important;
    font-family: 'Manrope', sans-serif !important;
    font-size: 15px !important;
    transition: all 0.2s ease;
}

.stDateInput input:focus, .stTextInput input:focus, .stTimeInput input:focus {
    border-color: rgba(212, 255, 54, 0.5) !important;
    box-shadow: 0 0 0 3px rgba(212, 255, 54, 0.1) !important;
}

/* Selectbox */
.stSelectbox > div > div {
    background: rgba(255,255,255,0.04) !important;
    border: 1px solid rgba(255,255,255,0.1) !important;
    border-radius: 12px !important;
    color: #ffffff !important;
}

.stSelectbox > div > div:hover {
    border-color: rgba(212, 255, 54, 0.4) !important;
}

/* MultiSelect */
.stMultiSelect > div > div {
    background: rgba(255,255,255,0.04) !important;
    border: 1px solid rgba(255,255,255,0.1) !important;
    border-radius: 12px !important;
    min-height: 50px !important;
}

.stMultiSelect span[data-baseweb="tag"] {
    background: linear-gradient(135deg, #d4ff36 0%, #a8ff00 100%) !important;
    color: #07091a !important;
    border: none !important;
    border-radius: 8px !important;
    font-weight: 700 !important;
    padding: 4px 12px !important;
}

.stMultiSelect span[data-baseweb="tag"] svg {
    color: #07091a !important;
}

/* Checkbox */
.stCheckbox label {
    color: #b8bdd4 !important;
    font-weight: 500 !important;
}

.stCheckbox > label > div:first-child {
    background: rgba(255,255,255,0.06) !important;
    border: 1px solid rgba(255,255,255,0.15) !important;
}

/* Primary button (LANCER LE BOT) */
.stButton > button {
    background: linear-gradient(135deg, #d4ff36 0%, #a8ff00 100%) !important;
    color: #07091a !important;
    border: none !important;
    border-radius: 14px !important;
    padding: 18px 32px !important;
    font-family: 'Manrope', sans-serif !important;
    font-weight: 800 !important;
    font-size: 16px !important;
    letter-spacing: 0.02em !important;
    text-transform: uppercase !important;
    box-shadow:
        0 8px 24px rgba(212, 255, 54, 0.3),
        inset 0 1px 0 rgba(255,255,255,0.4) !important;
    transition: all 0.2s ease !important;
    position: relative !important;
    overflow: hidden !important;
}

.stButton > button:hover {
    transform: translateY(-2px) !important;
    box-shadow:
        0 12px 36px rgba(212, 255, 54, 0.5),
        inset 0 1px 0 rgba(255,255,255,0.5) !important;
    background: linear-gradient(135deg, #e6ff66 0%, #c0ff36 100%) !important;
}

.stButton > button:active {
    transform: translateY(0) !important;
}

/* Glowing pulse around the button */
.stButton {
    position: relative;
}
.stButton::before {
    content: "";
    position: absolute;
    inset: -4px;
    border-radius: 18px;
    background: linear-gradient(135deg, #d4ff36, #a8ff00, #d4ff36);
    background-size: 200% 200%;
    z-index: -1;
    opacity: 0.4;
    filter: blur(16px);
    animation: glow-shift 4s ease infinite;
}

@keyframes glow-shift {
    0%, 100% { background-position: 0% 50%; opacity: 0.4; }
    50% { background-position: 100% 50%; opacity: 0.6; }
}

/* ─── Status / countdown ─── */
.status-card {
    background: linear-gradient(135deg, rgba(94, 185, 255, 0.08) 0%, rgba(94, 185, 255, 0.03) 100%);
    border: 1px solid rgba(94, 185, 255, 0.2);
    border-radius: 20px;
    padding: 1.5rem 2rem;
    margin-bottom: 1.5rem;
    display: flex;
    align-items: center;
    gap: 1.25rem;
}

.status-card.success {
    background: linear-gradient(135deg, rgba(45, 212, 122, 0.1) 0%, rgba(45, 212, 122, 0.03) 100%);
    border-color: rgba(45, 212, 122, 0.3);
}

.status-icon {
    width: 56px; height: 56px;
    flex-shrink: 0;
    border-radius: 16px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 28px;
    background: rgba(255,255,255,0.06);
}

.status-icon.blue { color: #5eb9ff; box-shadow: 0 0 24px rgba(94, 185, 255, 0.2); }
.status-icon.green { color: #2dd47a; box-shadow: 0 0 24px rgba(45, 212, 122, 0.2); }

.status-content h4 {
    margin: 0 0 4px 0;
    font-size: 0.85rem;
    font-weight: 600;
    color: #8b91a8;
    text-transform: uppercase;
    letter-spacing: 0.08em;
}

.status-content .target-line {
    font-size: 1.15rem;
    font-weight: 700;
    color: #ffffff;
    margin: 0;
}

.status-content .countdown {
    margin-top: 6px;
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.95rem;
    color: #d4ff36;
    font-weight: 600;
}

/* ─── Result panels ─── */
.result {
    margin-top: 1rem;
    border-radius: 16px;
    padding: 1.25rem 1.5rem;
    border: 1px solid;
    font-size: 0.95rem;
}

.result.success {
    background: rgba(45, 212, 122, 0.08);
    border-color: rgba(45, 212, 122, 0.3);
    color: #b6f3d3;
}

.result.error {
    background: rgba(255, 78, 78, 0.08);
    border-color: rgba(255, 78, 78, 0.3);
    color: #ffb4b4;
}

.result code {
    background: rgba(0,0,0,0.4) !important;
    color: #d4ff36 !important;
    padding: 2px 8px;
    border-radius: 6px;
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 0.85rem;
}

/* st.info, st.success, st.error overrides */
[data-testid="stAlert"] {
    background: rgba(94, 185, 255, 0.05) !important;
    border: 1px solid rgba(94, 185, 255, 0.2) !important;
    border-radius: 14px !important;
    color: #c5dafa !important;
    padding: 14px 18px !important;
}

[data-testid="stAlert"][data-baseweb="notification"] {
    backdrop-filter: blur(6px);
}

/* Caption styling */
.stCaption {
    font-size: 0.85rem !important;
    color: #6c7290 !important;
    font-weight: 400;
}

/* Expander */
.streamlit-expanderHeader, [data-testid="stExpander"] summary {
    background: rgba(255,255,255,0.03) !important;
    border: 1px solid rgba(255,255,255,0.06) !important;
    border-radius: 12px !important;
    color: #b8bdd4 !important;
    font-weight: 600 !important;
}

[data-testid="stExpander"] {
    border: none !important;
    background: transparent !important;
}

/* Divider */
hr {
    border: none !important;
    height: 1px !important;
    background: linear-gradient(90deg, transparent, rgba(255,255,255,0.1), transparent) !important;
    margin: 2.5rem 0 !important;
}

/* Court chips preview */
.court-chips {
    display: flex;
    gap: 8px;
    flex-wrap: wrap;
    margin-top: 12px;
}
.court-chips .chip {
    padding: 6px 14px;
    border-radius: 999px;
    background: rgba(212, 255, 54, 0.08);
    border: 1px solid rgba(212, 255, 54, 0.25);
    color: #d4ff36;
    font-weight: 600;
    font-size: 0.85rem;
    font-family: 'JetBrains Mono', monospace;
}
.court-chips .chip.idx {
    background: linear-gradient(135deg, #d4ff36 0%, #a8ff00 100%);
    color: #07091a;
}

/* Footer */
.footer {
    text-align: center;
    margin-top: 3rem;
    padding-top: 2rem;
    border-top: 1px solid rgba(255,255,255,0.06);
    color: #5c637e;
    font-size: 0.85rem;
}
.footer .ball-small {
    display: inline-block;
    width: 10px;
    height: 10px;
    border-radius: 50%;
    background: #d4ff36;
    box-shadow: 0 0 8px #d4ff36;
    vertical-align: middle;
    margin: 0 4px;
}
</style>
""", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════════════
#   HERO
# ═══════════════════════════════════════════════════════════════════════════════

st.markdown("""
<div class="hero">
    <div class="ball ball-1"></div>
    <div class="ball ball-2"></div>
    <div class="hero-eyebrow"><span class="dot"></span> Les Pyramides · Padel Bot</div>
    <h1 class="hero-title">Réserve ton créneau<br><span class="accent">plus vite que l'éclair.</span></h1>
    <p class="hero-subtitle">L'agent automatique qui décroche tes terrains à la milliseconde près, à l'instant où les réservations s'ouvrent sur ballejaune.</p>
</div>
""", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════════════
#   FORMULAIRE
# ═══════════════════════════════════════════════════════════════════════════════

with st.form("booking_form", clear_on_submit=False):
    # ─── 1. Quand ─────────────────────────
    st.markdown("""
    <div class="section-label">
        <div class="num">1</div>
        <h3>Quand veux-tu jouer ?</h3>
    </div>
    """, unsafe_allow_html=True)

    col_date, col_time = st.columns(2)
    with col_date:
        target_date = st.date_input(
            "Jour",
            value=date.today() + timedelta(days=2),
            min_value=date.today(),
            max_value=date.today() + timedelta(days=14),
            format="DD/MM/YYYY",
        )

    with col_time:
        time_options = ["07:30", "09:00", "10:30", "12:00", "13:30",
                        "15:00", "16:30", "18:00", "19:30", "21:00"]
        target_time = st.selectbox("Heure du créneau", time_options, index=8)

    st.markdown("<br>", unsafe_allow_html=True)

    # ─── 2. Terrains ──────────────────────
    st.markdown("""
    <div class="section-label">
        <div class="num">2</div>
        <h3>Quels terrains ?</h3>
    </div>
    """, unsafe_allow_html=True)

    st.caption("Ordre de préférence — le premier sera tenté en priorité, fallback dans l'ordre.")
    court_priority = st.multiselect(
        " ",
        options=["D1", "D2", "D3", "D4", "D5"],
        default=["D4", "D5", "D3", "D1", "D2"],
        label_visibility="collapsed",
    )

    st.markdown("<br>", unsafe_allow_html=True)

    # ─── 3. Options ───────────────────────
    st.markdown("""
    <div class="section-label">
        <div class="num">3</div>
        <h3>Options</h3>
    </div>
    """, unsafe_allow_html=True)

    col_opt1, col_opt2 = st.columns(2)
    with col_opt1:
        dry_run = st.checkbox(
            "Mode test (DRY_RUN)",
            value=False,
            help="Le bot va jusqu'à la page de réservation mais N'EFFECTUE PAS le clic final.",
        )
    with col_opt2:
        headless = st.checkbox(
            "Mode invisible (headless)",
            value=False,
            help="Le navigateur Chromium tourne sans s'afficher.",
        )

    st.markdown("<br>", unsafe_allow_html=True)
    submitted = st.form_submit_button("🚀 Lancer le bot", type="primary", use_container_width=True)

# ═══════════════════════════════════════════════════════════════════════════════
#   AFFICHAGE — Plan d'exécution
# ═══════════════════════════════════════════════════════════════════════════════

# Compute opening time
weekday = target_date.weekday()
if weekday < 5:
    opening_dt = datetime.combine(target_date - timedelta(days=2), time_module(17, 0))
    rule = "Semaine · ouverture J-2 à 17h00"
else:
    opening_dt = datetime.combine(target_date - timedelta(days=1), time_module(19, 30))
    rule = "Week-end · ouverture J-1 à 19h30 (à confirmer)"

now = datetime.now()
delta_sec = (opening_dt - now).total_seconds()

JOURS_FR = {"Monday": "Lundi", "Tuesday": "Mardi", "Wednesday": "Mercredi",
            "Thursday": "Jeudi", "Friday": "Vendredi", "Saturday": "Samedi", "Sunday": "Dimanche"}
MOIS_FR = {"January": "janvier", "February": "février", "March": "mars", "April": "avril",
           "May": "mai", "June": "juin", "July": "juillet", "August": "août",
           "September": "septembre", "October": "octobre", "November": "novembre", "December": "décembre"}

jour_fr = JOURS_FR.get(target_date.strftime("%A"), target_date.strftime("%A"))
mois_fr = MOIS_FR.get(target_date.strftime("%B"), target_date.strftime("%B"))
date_label = f"{jour_fr} {target_date.day} {mois_fr} {target_date.year} · {target_time}"

jour_op_fr = JOURS_FR.get(opening_dt.strftime("%A"), opening_dt.strftime("%A"))
mois_op_fr = MOIS_FR.get(opening_dt.strftime("%B"), opening_dt.strftime("%B"))
opening_label = f"{jour_op_fr} {opening_dt.day} {mois_op_fr} à {opening_dt.strftime('%H:%M')}"

if delta_sec > 0:
    hours, rem = divmod(int(delta_sec), 3600)
    minutes, seconds = divmod(rem, 60)
    days = hours // 24
    if days >= 1:
        countdown_str = f"⏳ Dans {days}j {hours % 24}h {minutes:02d}m"
    elif hours > 0:
        countdown_str = f"⏳ Dans {hours}h {minutes:02d}m {seconds:02d}s"
    else:
        countdown_str = f"⏳ Dans {minutes}m {seconds:02d}s"
    status_html = f"""
    <div class="status-card">
        <div class="status-icon blue">⏰</div>
        <div class="status-content">
            <h4>Plan d'exécution · {rule}</h4>
            <p class="target-line">Créneau : {date_label}</p>
            <p class="target-line" style="font-weight:500;color:#5eb9ff;">Ouverture : {opening_label}</p>
            <div class="countdown">{countdown_str}</div>
        </div>
    </div>
    """
else:
    status_html = f"""
    <div class="status-card success">
        <div class="status-icon green">⚡</div>
        <div class="status-content">
            <h4>Créneau déjà ouvert · {rule}</h4>
            <p class="target-line">Créneau : {date_label}</p>
            <div class="countdown" style="color:#2dd47a;">▶ Action immédiate dès lancement</div>
        </div>
    </div>
    """
st.markdown(status_html, unsafe_allow_html=True)

# Court priority preview as chips
if court_priority:
    chips_html = '<div class="court-chips">'
    for i, c in enumerate(court_priority):
        cls = "chip idx" if i == 0 else "chip"
        prefix = f"#{i+1} · " if i == 0 else f"#{i+1} · "
        chips_html += f'<span class="{cls}">{prefix}PADEL {c}</span>'
    chips_html += '</div>'
    st.markdown(chips_html, unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════════════
#   LANCEMENT
# ═══════════════════════════════════════════════════════════════════════════════

if submitted:
    if not court_priority:
        st.error("⚠️ Tu dois sélectionner au moins un terrain.")
    else:
        date_offset = (target_date - date.today()).days
        hour, minute = map(int, target_time.split(":"))

        config = {
            "target_date_offset": date_offset,
            "target_hour": hour,
            "target_minute": minute,
            "court_priority": court_priority,
            "opening_iso": opening_dt.isoformat(),
            "dry_run": dry_run,
            "headless": headless,
        }

        agent_dir = os.path.expanduser("~/padel-agent")
        config_path = os.path.join(agent_dir, "booking_config.json")
        log_path = os.path.join(agent_dir, "bot.log")

        os.makedirs(agent_dir, exist_ok=True)
        with open(config_path, "w") as f:
            json.dump(config, f, indent=2, ensure_ascii=False)

        cmd = (
            f"cd {agent_dir} && "
            f"source .venv/bin/activate && "
            f"python reserve_with_config.py > {log_path} 2>&1 &"
        )
        try:
            subprocess.Popen(["/bin/bash", "-c", cmd])
            st.markdown(f"""
            <div class="result success">
                🤖 <strong>Bot lancé en arrière-plan !</strong><br>
                Tu peux fermer cet onglet, le bot continue tout seul.<br><br>
                Pour suivre les logs en direct, ouvre un nouveau Terminal et lance :<br>
                <code>tail -f {log_path}</code>
            </div>
            """, unsafe_allow_html=True)
        except Exception as e:
            st.markdown(f"""
            <div class="result error">
                ⚠️ Échec du lancement automatique : {e}<br>
                <strong>Lance manuellement dans un Terminal :</strong><br>
                <code>cd {agent_dir} && source .venv/bin/activate && python reserve_with_config.py</code>
            </div>
            """, unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════════════
#   FOOTER + INFO
# ═══════════════════════════════════════════════════════════════════════════════

st.markdown("<br>", unsafe_allow_html=True)

with st.expander("🛠️  Comment ça marche ?"):
    st.markdown("""
- **Le bot calcule automatiquement l'heure d'ouverture** des réservations selon les règles du club :
  - **Semaine** (Lun→Ven) → J-2 à **17h00**
  - **Week-end** (Sam·Dim) → J-1 à **19h30**
- Si l'ouverture est dans le futur, il **attend précisément à la milliseconde** avant d'agir.
- Si l'ouverture est passée (créneau déjà bookable), il **agit immédiatement**.
- Il essaie les terrains **dans l'ordre que tu as choisi**. Si le premier est pris, il tente le suivant.
- Tes 3 partenaires (SARL DIGITEASE 2, SARL DIGITEASE, RISKCON ADVISORY 1) sont sélectionnés automatiquement par leur ID.
- En conditions optimales, le bot finalise une réservation en **≈ 2 secondes** après l'ouverture du créneau.
""")

st.markdown("""
<div class="footer">
    Padel Bot <span class="ball-small"></span> Les Pyramides
    <br><span style="opacity:0.5;font-size:0.75rem;">Made with Streamlit + Playwright</span>
</div>
""", unsafe_allow_html=True)
