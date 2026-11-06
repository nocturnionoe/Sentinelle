import streamlit as st
import requests
import pandas as pd
from concurrent.futures import ThreadPoolExecutor

# ================================================================
# CLÉ API FINNHUB (via Streamlit Secrets)
# ================================================================
try:
    API_KEY = st.secrets["FINNHUB_API_KEY"]
except Exception:
    API_KEY = "A_REMPLIR"
# ================================================================

BARGO_BASE = "https://www.bargo.ai/free-apis/congress/v1"

# Watchlist élargie — ~30 grandes capitalisations US
WATCHLIST = {
    "AAPL": "Apple", "MSFT": "Microsoft", "GOOGL": "Alphabet", "AMZN": "Amazon",
    "META": "Meta", "TSLA": "Tesla", "NVDA": "NVIDIA", "JPM": "JPMorgan Chase",
    "V": "Visa", "WMT": "Walmart", "JNJ": "Johnson & Johnson", "XOM": "Exxon Mobil",
    "BAC": "Bank of America", "DIS": "Walt Disney", "NFLX": "Netflix", "KO": "Coca-Cola",
    "PEP": "PepsiCo", "ORCL": "Oracle", "CRM": "Salesforce", "AMD": "AMD",
    "INTC": "Intel", "CSCO": "Cisco", "IBM": "IBM", "GS": "Goldman Sachs",
    "MS": "Morgan Stanley", "BA": "Boeing", "MCD": "McDonald's", "NKE": "Nike",
    "COST": "Costco", "PG": "Procter & Gamble", "UNH": "UnitedHealth",
}


st.set_page_config(
    page_title="Sentinelle",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="collapsed",
)


# ============================================================
# STYLE — typographie Inter, palette raffinée, moins "fait par IA"
# ============================================================
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&family=JetBrains+Mono:wght@500;600&display=swap');

    :root {
      --bg: #050812;
      --bg-grad-1: #0d1326;
      --bg-grad-2: #050812;
      --card: #0e1424;
      --card-hover: #121a2e;
      --border: rgba(255,255,255,0.06);
      --border-hover: rgba(99,196,255,0.25);
      --txt: #e8ecf5;
      --txt-muted: #7a8599;
      --txt-dim: #4a556b;
      --accent: #63c4ff;
      --accent-2: #5b8def;
      --green: #22c55e;
      --red: #f43f5e;
      --gold: #f0b429;
    }

    html, body, [class*="css"], .stApp, button, input, textarea {
        font-family: 'Inter', -apple-system, sans-serif !important;
        font-feature-settings: 'cv11', 'ss01', 'ss03';
        letter-spacing: -0.01em;
    }

    .stApp {
        background:
            radial-gradient(1200px 600px at 20% -10%, rgba(91,141,239,0.12), transparent 60%),
            radial-gradient(900px 500px at 90% 0%, rgba(99,196,255,0.08), transparent 55%),
            linear-gradient(180deg, var(--bg-grad-1) 0%, var(--bg-grad-2) 100%);
        color: var(--txt);
    }
    [data-testid="stHeader"] { background: transparent; }
    .block-container { padding-top: 1.2rem; max-width: 1180px; }

    /* ===== HEADER ===== */
    .app-header {
        display: flex; align-items: center; justify-content: space-between;
        padding: 0.4rem 0 1.4rem 0;
        margin-bottom: 1rem;
    }
    .brand { display: flex; align-items: center; gap: 0.85rem; }
    .brand-logo {
        width: 38px; height: 38px;
        display: flex; align-items: center; justify-content: center;
        background: linear-gradient(135deg, #1a2447 0%, #0b1024 100%);
        border: 1px solid rgba(99,196,255,0.3);
        border-radius: 10px;
        box-shadow: 0 0 20px rgba(99,196,255,0.15);
    }
    .brand-name {
        font-size: 1.1rem; font-weight: 800; letter-spacing: 5px; color: #f8fafc;
    }
    .brand-tag {
        font-size: 0.68rem; color: var(--txt-muted);
        text-transform: uppercase; letter-spacing: 2.5px; font-weight: 600;
    }
    .status-pill {
        display: inline-flex; align-items: center; gap: 0.4rem;
        padding: 0.35rem 0.75rem;
        background: rgba(34,197,94,0.1);
        border: 1px solid rgba(34,197,94,0.25);
        border-radius: 999px;
        font-size: 0.72rem; font-weight: 600; color: var(--green);
        letter-spacing: 0.5px;
    }
    .status-dot {
        width: 6px; height: 6px; border-radius: 50%;
        background: var(--green);
        box-shadow: 0 0 10px var(--green);
        animation: pulse 2s infinite;
    }
    @keyframes pulse {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.4; }
    }

    /* ===== HERO ===== */
    .hero {
        padding: 1.5rem 0 2.2rem 0;
        border-bottom: 1px solid var(--border);
        margin-bottom: 2rem;
    }
    .hero-eyebrow {
        display: inline-block;
        padding: 0.3rem 0.75rem;
        background: rgba(99,196,255,0.08);
        border: 1px solid rgba(99,196,255,0.2);
        border-radius: 999px;
        font-size: 0.68rem; font-weight: 600; color: var(--accent);
        text-transform: uppercase; letter-spacing: 2px;
        margin-bottom: 1rem;
    }
    .hero-title {
        font-size: 2.6rem; font-weight: 800; color: #f8fafc;
        line-height: 1.1; letter-spacing: -0.03em;
        margin-bottom: 0.7rem;
    }
    .hero-sub {
        font-size: 1.02rem; color: var(--txt-muted);
        max-width: 640px; line-height: 1.55;
    }

    /* ===== ONGLETS ===== */
    [data-baseweb="tab-list"] {
        background: rgba(10,15,30,0.5);
        backdrop-filter: blur(10px);
        border-radius: 14px; padding: 0.35rem;
        gap: 0.15rem;
        border: 1px solid var(--border);
    }
    [data-baseweb="tab"] {
        background: transparent !important;
        border-radius: 10px !important;
        color: var(--txt-muted) !important;
        font-weight: 600 !important;
        font-size: 0.92rem !important;
        padding: 0.65rem 1.1rem !important;
        transition: all 0.15s;
    }
    [data-baseweb="tab"]:hover { color: var(--txt) !important; }
    [data-baseweb="tab"][aria-selected="true"] {
        background: linear-gradient(135deg, rgba(99,196,255,0.18), rgba(91,141,239,0.15)) !important;
        color: #f8fafc !important;
        box-shadow: inset 0 0 0 1px rgba(99,196,255,0.25);
    }
    [data-baseweb="tab-highlight"], [data-baseweb="tab-border"] { display: none !important; }

    /* ===== SECTIONS ===== */
    .section-head {
        display: flex; align-items: baseline; justify-content: space-between;
        margin: 2.5rem 0 1rem 0;
    }
    .section-title {
        font-size: 1.35rem; font-weight: 700; color: #f1f5f9;
        letter-spacing: -0.02em;
    }
    .section-meta {
        font-size: 0.78rem; color: var(--txt-muted); font-weight: 500;
    }

    /* ===== STAT TILES (grosses KPI) ===== */
    .stat-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
        gap: 0.9rem;
        margin-bottom: 1rem;
    }
    .stat-tile {
        background: var(--card);
        border: 1px solid var(--border);
        border-radius: 14px;
        padding: 1.1rem 1.25rem;
        position: relative;
        overflow: hidden;
    }
    .stat-tile::before {
        content: ''; position: absolute; left: 0; top: 0; height: 2px; width: 100%;
        background: linear-gradient(90deg, var(--accent), transparent);
        opacity: 0.5;
    }
    .stat-tile-label {
        font-size: 0.68rem; color: var(--txt-muted); font-weight: 600;
        text-transform: uppercase; letter-spacing: 1.5px;
        margin-bottom: 0.65rem;
    }
    .stat-tile-value {
        font-size: 1.75rem; font-weight: 700; color: #f8fafc;
        line-height: 1.05; font-family: 'Inter', sans-serif;
        letter-spacing: -0.02em;
    }
    .stat-tile-delta {
        font-size: 0.76rem; color: var(--txt-muted); margin-top: 0.35rem;
    }
    .pos { color: var(--green); }
    .neg { color: var(--red); }

    /* ===== LIGNES (type row) ===== */
    .row {
        display: grid;
        grid-template-columns: auto 1fr auto auto;
        gap: 0.9rem; align-items: center;
        padding: 0.95rem 1rem;
        background: var(--card);
        border: 1px solid var(--border);
        border-radius: 12px;
        margin-bottom: 0.5rem;
        transition: all 0.12s;
    }
    .row:hover {
        border-color: var(--border-hover);
        background: var(--card-hover);
        transform: translateY(-1px);
    }
    .row-icon {
        width: 36px; height: 36px; border-radius: 10px;
        display: flex; align-items: center; justify-content: center;
        font-weight: 700; font-size: 0.85rem;
        flex-shrink: 0;
    }
    .ico-buy { background: rgba(34,197,94,0.14); color: var(--green); }
    .ico-sell { background: rgba(244,63,94,0.14); color: var(--red); }
    .ico-house { background: rgba(240,180,41,0.14); color: var(--gold); }
    .ico-senate { background: rgba(99,196,255,0.14); color: var(--accent); }

    .row-main {
        min-width: 0;
    }
    .row-name {
        font-weight: 600; color: #f1f5f9; font-size: 0.96rem;
        overflow: hidden; text-overflow: ellipsis; white-space: nowrap;
    }
    .row-sub {
        font-size: 0.78rem; color: var(--txt-muted); margin-top: 0.15rem;
    }
    .row-chip {
        padding: 0.35rem 0.6rem; border-radius: 8px;
        background: rgba(255,255,255,0.05);
        color: var(--accent);
        font-size: 0.75rem; font-weight: 700;
        font-family: 'JetBrains Mono', monospace;
        letter-spacing: 0.5px;
    }
    .row-amount {
        font-size: 0.98rem; font-weight: 700; color: #f8fafc;
        font-family: 'JetBrains Mono', monospace;
        text-align: right; min-width: 95px;
    }
    .row-date {
        font-size: 0.72rem; color: var(--txt-muted);
        font-weight: 500; text-align: right; margin-top: 0.15rem;
    }

    /* ===== EXPANDERS (drill-down) ===== */
    [data-testid="stExpander"] {
        background: var(--card) !important;
        border: 1px solid var(--border) !important;
        border-radius: 12px !important;
        margin-bottom: 0.55rem !important;
        transition: all 0.12s;
        overflow: hidden;
    }
    [data-testid="stExpander"]:hover {
        border-color: var(--border-hover) !important;
        background: var(--card-hover) !important;
    }
    [data-testid="stExpander"] summary {
        padding: 0.95rem 1.1rem !important;
        color: #f1f5f9 !important;
        font-weight: 500 !important;
        font-size: 0.93rem !important;
    }
    [data-testid="stExpander"] [data-testid="stExpanderDetails"] {
        padding: 0.3rem 1.1rem 1.1rem 1.1rem !important;
        border-top: 1px solid var(--border);
    }

    /* ===== MINI KPIs dans expander ===== */
    .mini-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(110px, 1fr));
        gap: 0.5rem; margin: 0.9rem 0 1rem 0;
    }
    .mini {
        background: rgba(255,255,255,0.02);
        border: 1px solid var(--border);
        border-radius: 10px;
        padding: 0.65rem 0.85rem;
    }
    .mini-lbl {
        font-size: 0.65rem; color: var(--txt-muted); font-weight: 600;
        text-transform: uppercase; letter-spacing: 1.2px;
    }
    .mini-val {
        font-size: 1.05rem; font-weight: 700; color: #f8fafc; margin-top: 0.2rem;
        font-family: 'JetBrains Mono', monospace;
    }

    /* ===== TRANSACTIONS COMPACTES (dans detail) ===== */
    .tx-item {
        display: grid;
        grid-template-columns: 30px 1fr auto auto;
        gap: 0.7rem; align-items: center;
        padding: 0.65rem 0.8rem;
        background: rgba(255,255,255,0.02);
        border-radius: 8px;
        margin-bottom: 0.3rem;
        font-size: 0.85rem;
    }
    .tx-arrow { font-weight: 700; font-size: 0.95rem; }
    .tx-info { color: #e2e8f0; font-weight: 500; }
    .tx-info-sub { color: var(--txt-muted); font-size: 0.72rem; margin-top: 0.1rem; }
    .tx-amt {
        color: #f8fafc; font-weight: 700;
        font-family: 'JetBrains Mono', monospace;
    }
    .tx-ticker-sm {
        background: rgba(99,196,255,0.1);
        color: var(--accent);
        padding: 0.2rem 0.5rem; border-radius: 6px;
        font-size: 0.72rem; font-weight: 700;
        font-family: 'JetBrains Mono', monospace;
    }

    /* ===== INPUTS / BOUTONS ===== */
    .stTextInput input {
        background: var(--card) !important;
        color: var(--txt) !important;
        border: 1px solid var(--border) !important;
        border-radius: 10px !important;
        padding: 0.75rem 1rem !important;
        font-size: 1rem !important;
        font-family: 'Inter', sans-serif !important;
    }
    .stTextInput input:focus { border-color: var(--accent) !important; }
    .stButton > button {
        background: linear-gradient(135deg, #5b8def, #63c4ff) !important;
        color: white !important; border: none !important;
        border-radius: 10px; font-weight: 600;
        padding: 0.65rem 1.2rem;
    }

    /* ===== CHARTS ===== */
    [data-testid="stVegaLiteChart"], [data-testid="stAltairChart"] {
        background: var(--card);
        border: 1px solid var(--border);
        border-radius: 12px;
        padding: 0.8rem;
    }

    /* ===== FOOTER ===== */
    .footer {
        margin-top: 4rem; padding: 2rem 0 1rem 0;
        border-top: 1px solid var(--border);
        text-align: center; color: var(--txt-dim);
        font-size: 0.75rem;
    }
    .footer-brand {
        font-weight: 700; letter-spacing: 3px; color: var(--txt-muted);
        margin-bottom: 0.6rem;
    }

    #MainMenu, footer, header { visibility: hidden; }

    /* Scrollbar discrète */
    ::-webkit-scrollbar { width: 10px; height: 10px; }
    ::-webkit-scrollbar-track { background: transparent; }
    ::-webkit-scrollbar-thumb {
        background: rgba(255,255,255,0.08);
        border-radius: 10px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# API — FINNHUB (dirigeants d'entreprise)
# ============================================================
@st.cache_data(ttl=1800, show_spinner=False)
def fetch_insider_tx(symbol: str, api_key: str) -> pd.DataFrame:
    try:
        r = requests.get(
            "https://finnhub.io/api/v1/stock/insider-transactions",
            params={"symbol": symbol, "token": api_key}, timeout=10,
        )
        r.raise_for_status()
        data = r.json().get("data", [])
    except requests.RequestException:
        return pd.DataFrame()
    if not data:
        return pd.DataFrame()
    df = pd.DataFrame(data)
    df["transactionDate"] = pd.to_datetime(df.get("transactionDate"), errors="coerce")
    df["transactionPrice"] = pd.to_numeric(df.get("transactionPrice"), errors="coerce").fillna(0)
    df["change"] = pd.to_numeric(df.get("change"), errors="coerce").fillna(0)
    df["share"] = pd.to_numeric(df.get("share"), errors="coerce").fillna(0)
    df["montant"] = df["change"].abs() * df["transactionPrice"]
    df["symbol"] = symbol
    return df.sort_values("transactionDate", ascending=False, na_position="last").reset_index(drop=True)


@st.cache_data(ttl=1800, show_spinner="Chargement des dirigeants d'entreprise…")
def fetch_all_insiders(api_key: str) -> pd.DataFrame:
    with ThreadPoolExecutor(max_workers=10) as ex:
        results = list(ex.map(lambda t: fetch_insider_tx(t, api_key), WATCHLIST.keys()))
    non_empty = [df for df in results if not df.empty]
    if not non_empty:
        return pd.DataFrame()
    agg = pd.concat(non_empty, ignore_index=True)
    agg["entreprise"] = agg["symbol"].map(WATCHLIST)
    return agg


# ============================================================
# API — BARGO (élus US, Congrès)
# ============================================================
@st.cache_data(ttl=3600, show_spinner="Chargement des trades du Congrès US…")
def fetch_congress_trades(limit: int = 100) -> pd.DataFrame:
    try:
        r = requests.get(f"{BARGO_BASE}/trades", params={"limit": limit}, timeout=15)
        r.raise_for_status()
        trades = r.json().get("trades", [])
    except requests.RequestException:
        return pd.DataFrame()
    if not trades:
        return pd.DataFrame()
    df = pd.DataFrame(trades)
    df["transaction_date"] = pd.to_datetime(df.get("transaction_date"), errors="coerce")
    df["disclosure_date"] = pd.to_datetime(df.get("disclosure_date"), errors="coerce")
    # Montant estimé : milieu de la fourchette
    def mid_range(s):
        if not isinstance(s, str):
            return 0.0
        s = s.replace("$", "").replace(",", "").replace("+", "").strip()
        if "-" in s:
            a, b = s.split("-", 1)
            try: return (float(a.strip()) + float(b.strip())) / 2
            except: return 0.0
        try: return float(s)
        except: return 0.0
    df["montant_est"] = df.get("amount_range", "").apply(mid_range)
    return df.sort_values("transaction_date", ascending=False, na_position="last").reset_index(drop=True)


# ============================================================
# HELPERS
# ============================================================
def fmt_num(n: float) -> str:
    if n is None or pd.isna(n):
        return "—"
    n = float(n)
    if abs(n) >= 1e9: return f"{n/1e9:.2f}Md"
    if abs(n) >= 1e6: return f"{n/1e6:.2f}M"
    if abs(n) >= 1e3: return f"{n/1e3:.1f}k"
    return f"{n:.0f}"


def fmt_date(d) -> str:
    MOIS = {"Jan":"janv.", "Feb":"févr.", "Mar":"mars", "Apr":"avr.",
            "May":"mai", "Jun":"juin", "Jul":"juil.", "Aug":"août",
            "Sep":"sept.", "Oct":"oct.", "Nov":"nov.", "Dec":"déc."}
    if pd.isna(d):
        return "—"
    s = d.strftime("%d %b %Y")
    for en, fr in MOIS.items():
        s = s.replace(en, fr)
    return s


def html_row_insider(row):
    """Ligne pour une transaction d'insider (corporate)."""
    is_buy = row["change"] > 0
    ico = "↑" if is_buy else "↓"
    cls = "ico-buy" if is_buy else "ico-sell"
    sens = "A acheté" if is_buy else "A vendu"
    entreprise = WATCHLIST.get(row["symbol"], row["symbol"])
    return f"""
    <div class="row">
        <div class="row-icon {cls}">{ico}</div>
        <div class="row-main">
            <div class="row-name">{row['name']}</div>
            <div class="row-sub">{sens} des actions {entreprise}</div>
        </div>
        <div class="row-chip">{row['symbol']}</div>
        <div>
            <div class="row-amount">${fmt_num(row['montant'])}</div>
            <div class="row-date">{fmt_date(row['transactionDate'])}</div>
        </div>
    </div>
    """


def html_row_congress(row):
    """Ligne pour un trade du Congrès."""
    ttype = (row.get("type") or "").lower()
    is_buy = "purchase" in ttype
    ico = "↑" if is_buy else "↓"
    cls = "ico-buy" if is_buy else "ico-sell"
    sens = "A acheté" if is_buy else "A vendu"
    ticker = row.get("ticker") or "—"
    chamber = (row.get("chamber") or "").capitalize() or "Congrès"
    state = row.get("state") or ""
    return f"""
    <div class="row">
        <div class="row-icon {cls}">{ico}</div>
        <div class="row-main">
            <div class="row-name">{row.get('member', '—')}</div>
            <div class="row-sub">{sens} · {chamber} · {state}</div>
        </div>
        <div class="row-chip">{ticker}</div>
        <div>
            <div class="row-amount">${fmt_num(row['montant_est'])}</div>
            <div class="row-date">{fmt_date(row['transaction_date'])}</div>
        </div>
    </div>
    """


def html_mini_kpis(items):
    html = '<div class="mini-grid">'
    for lbl, val in items:
        html += f'<div class="mini"><div class="mini-lbl">{lbl}</div><div class="mini-val">{val}</div></div>'
    return html + '</div>'


def html_tx_item(sens, main, sub, ticker, montant, date):
    is_buy = "achat" in sens.lower() or "purchase" in sens.lower()
    arrow = "↑" if is_buy else "↓"
    color = "var(--green)" if is_buy else "var(--red)"
    return f"""
    <div class="tx-item">
        <div class="tx-arrow" style="color:{color}">{arrow}</div>
        <div>
            <div class="tx-info">{main}</div>
            <div class="tx-info-sub">{sub}</div>
        </div>
        <div class="tx-ticker-sm">{ticker}</div>
        <div style="text-align:right;">
            <div class="tx-amt">${fmt_num(montant)}</div>
            <div class="row-date">{date}</div>
        </div>
    </div>
    """


def activity_chart(dates_series, title=""):
    """Petit chart : nombre de transactions par jour."""
    if dates_series.empty:
        return
    counts = (
        dates_series.dropna()
        .dt.floor("D")
        .value_counts()
        .sort_index()
        .tail(30)
    )
    if counts.empty:
        return
    df_chart = pd.DataFrame({"Date": counts.index, "Transactions": counts.values})
    df_chart = df_chart.set_index("Date")
    st.bar_chart(df_chart, height=160, use_container_width=True, color="#63c4ff")


# ============================================================
# HEADER
# ============================================================
st.markdown(
    """
    <div class="app-header">
        <div class="brand">
            <div class="brand-logo">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#63c4ff" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
                    <path d="M12 2L4 6v6c0 5 3.5 9.5 8 10 4.5-0.5 8-5 8-10V6l-8-4z"/>
                    <path d="M12 8v5"/>
                </svg>
            </div>
            <div>
                <div class="brand-name">SENTINELLE</div>
                <div class="brand-tag">INSIDER · TRACKER</div>
            </div>
        </div>
        <div class="status-pill">
            <span class="status-dot"></span>
            DONNÉES EN DIRECT
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)


if API_KEY == "A_REMPLIR":
    st.error("⚠️ Clé API Finnhub manquante. Ajoutez `FINNHUB_API_KEY` dans les Secrets de Streamlit Cloud.")
    st.stop()


# ============================================================
# ONGLETS
# ============================================================
tab_accueil, tab_dirigeants, tab_elus, tab_entreprises, tab_recherche = st.tabs([
    "Accueil", "Dirigeants", "Élus US", "Entreprises", "Recherche"
])


# ============================================================
# ACCUEIL
# ============================================================
with tab_accueil:
    st.markdown(
        """
        <div class="hero">
            <div class="hero-eyebrow">⚡ Flux officiel · SEC + Congrès US</div>
            <div class="hero-title">L'intelligence du capital, sans le bruit.</div>
            <div class="hero-sub">Suivez les mouvements qui comptent — déclarations officielles des dirigeants d'entreprises cotées et des membres du Congrès américain — avant que le marché ne les intègre.</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    df_insiders = fetch_all_insiders(API_KEY)
    df_congress = fetch_congress_trades(100)

    # Stats globales
    vol_i = df_insiders["montant"].sum() if not df_insiders.empty else 0
    vol_c = df_congress["montant_est"].sum() if not df_congress.empty else 0
    nb_i = df_insiders["name"].nunique() if not df_insiders.empty else 0
    nb_c = df_congress["member"].nunique() if not df_congress.empty else 0

    st.markdown(
        f"""
        <div class="stat-grid">
            <div class="stat-tile">
                <div class="stat-tile-label">Volume dirigeants</div>
                <div class="stat-tile-value">${fmt_num(vol_i)}</div>
                <div class="stat-tile-delta">{nb_i} dirigeants actifs</div>
            </div>
            <div class="stat-tile">
                <div class="stat-tile-label">Volume élus US</div>
                <div class="stat-tile-value">${fmt_num(vol_c)}</div>
                <div class="stat-tile-delta">{nb_c} membres du Congrès</div>
            </div>
            <div class="stat-tile">
                <div class="stat-tile-label">Transactions suivies</div>
                <div class="stat-tile-value">{len(df_insiders) + len(df_congress):,}</div>
                <div class="stat-tile-delta">90 derniers jours</div>
            </div>
            <div class="stat-tile">
                <div class="stat-tile-label">Entreprises couvertes</div>
                <div class="stat-tile-value">{len(WATCHLIST)}</div>
                <div class="stat-tile-delta">watchlist S&P</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # --- Gros mouvements dirigeants ---
    if not df_insiders.empty:
        st.markdown(
            """
            <div class="section-head">
                <div class="section-title">🔥 Gros mouvements — dirigeants</div>
                <div class="section-meta">Top 6 par montant</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        top_insiders = df_insiders.sort_values("montant", ascending=False).head(6)
        for _, row in top_insiders.iterrows():
            st.markdown(html_row_insider(row), unsafe_allow_html=True)

    # --- Gros mouvements élus ---
    if not df_congress.empty:
        st.markdown(
            """
            <div class="section-head">
                <div class="section-title">🏛️ Gros mouvements — élus US</div>
                <div class="section-meta">Top 6 par montant estimé</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        top_congress = df_congress.sort_values("montant_est", ascending=False).head(6)
        for _, row in top_congress.iterrows():
            st.markdown(html_row_congress(row), unsafe_allow_html=True)

    # --- Chart activité ---
    if not df_insiders.empty or not df_congress.empty:
        st.markdown(
            """
            <div class="section-head">
                <div class="section-title">📊 Activité sur 30 jours</div>
                <div class="section-meta">Transactions par jour</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        all_dates = pd.concat([
            df_insiders["transactionDate"] if not df_insiders.empty else pd.Series(dtype="datetime64[ns]"),
            df_congress["transaction_date"] if not df_congress.empty else pd.Series(dtype="datetime64[ns]"),
        ])
        activity_chart(all_dates)


# ============================================================
# DIRIGEANTS
# ============================================================
with tab_dirigeants:
    st.markdown(
        """
        <div class="hero">
            <div class="hero-eyebrow">👔 CORPORATE INSIDERS</div>
            <div class="hero-title">Les grands noms des conseils d'administration.</div>
            <div class="hero-sub">Dirigeants les plus actifs de la watchlist. Cliquez sur une carte pour voir le détail de leurs transactions, entreprise par entreprise.</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    df_all = fetch_all_insiders(API_KEY)
    if df_all.empty:
        st.warning("Aucune donnée disponible.")
    else:
        top_i = (
            df_all.groupby("name")
                  .agg(nb=("name","size"), vol=("montant","sum"),
                       entr=("symbol", lambda s: sorted(set(s))))
                  .sort_values("vol", ascending=False).head(25).reset_index()
        )

        for _, row in top_i.iterrows():
            tickers = ", ".join(row["entr"])
            label = f"👤   {row['name']}   ·   ${fmt_num(row['vol'])}   ·   {row['nb']} transactions"
            with st.expander(label):
                sub = df_all[df_all["name"] == row["name"]].copy()
                achats = (sub["change"] > 0).sum()
                ventes = (sub["change"] < 0).sum()
                net = int(sub["change"].sum())

                st.markdown(
                    html_mini_kpis([
                        ("Volume", f"${fmt_num(row['vol'])}"),
                        ("Transactions", f"{row['nb']}"),
                        ("Achats", f"🟢 {achats}"),
                        ("Ventes", f"🔴 {ventes}"),
                        ("Flux net", f"{net:+,}"),
                        ("Entreprises", tickers),
                    ]),
                    unsafe_allow_html=True,
                )

                # Chart activité
                activity_chart(sub["transactionDate"])

                # Liste des transactions (compactes)
                st.markdown("<div style='margin-top:1rem; font-weight:600; color:#cbd5e1; font-size:0.85rem;'>Détail des opérations</div>", unsafe_allow_html=True)
                for _, t in sub.sort_values("transactionDate", ascending=False).head(15).iterrows():
                    sens = "Achat" if t["change"] > 0 else "Vente"
                    nom_ent = WATCHLIST.get(t["symbol"], t["symbol"])
                    st.markdown(
                        html_tx_item(
                            sens,
                            f"{sens} — {nom_ent}",
                            f"{int(t['change']):+,} actions à ${t['transactionPrice']:,.2f}",
                            t["symbol"],
                            t["montant"],
                            fmt_date(t["transactionDate"]),
                        ),
                        unsafe_allow_html=True,
                    )

                if row["nb"] > 15:
                    st.caption(f"… et {row['nb'] - 15} transactions plus anciennes")


# ============================================================
# ÉLUS US
# ============================================================
with tab_elus:
    st.markdown(
        """
        <div class="hero">
            <div class="hero-eyebrow">🏛️ CONGRÈS US · STOCK Act</div>
            <div class="hero-title">Ce que les sénateurs et représentants achètent.</div>
            <div class="hero-sub">Déclarations officielles des membres du Congrès américain (House + Senate) sur les 90 derniers jours. Cliquez sur un élu pour voir tous ses trades, toutes entreprises confondues.</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    df_c = fetch_congress_trades(100)
    if df_c.empty:
        st.warning("Données du Congrès temporairement indisponibles (rate-limit Bargo API). Réessayez dans quelques minutes.")
    else:
        # Classement des élus par volume
        top_m = (
            df_c.groupby("member")
                .agg(
                    nb=("member","size"),
                    vol=("montant_est","sum"),
                    chamber=("chamber","first"),
                    state=("state","first"),
                    tickers=("ticker", lambda s: sorted(set(x for x in s if x))),
                )
                .sort_values("vol", ascending=False)
                .head(25).reset_index()
        )

        # Chart global : répartition house / senate
        chambre_counts = df_c["chamber"].value_counts()

        for _, row in top_m.iterrows():
            chamber_ico = "🏛️" if (row["chamber"] or "").lower() == "senate" else "🏢"
            label = f"{chamber_ico}   {row['member']}   ·   {(row['chamber'] or '').capitalize()} {row['state']}   ·   ${fmt_num(row['vol'])}   ·   {row['nb']} trades"

            with st.expander(label):
                sub = df_c[df_c["member"] == row["member"]].copy()
                achats = sub["type"].str.lower().str.contains("purchase", na=False).sum()
                ventes = sub["type"].str.lower().str.contains("sale", na=False).sum()
                tickers_list = ", ".join(row["tickers"][:6])
                if len(row["tickers"]) > 6:
                    tickers_list += f" (+{len(row['tickers'])-6})"

                st.markdown(
                    html_mini_kpis([
                        ("Volume estimé", f"${fmt_num(row['vol'])}"),
                        ("Trades", f"{row['nb']}"),
                        ("Achats", f"🟢 {achats}"),
                        ("Ventes", f"🔴 {ventes}"),
                        ("Chambre", (row["chamber"] or "—").capitalize()),
                        ("Tickers tradés", f"{len(row['tickers'])}"),
                    ]),
                    unsafe_allow_html=True,
                )

                activity_chart(sub["transaction_date"])

                st.markdown(f"<div style='margin-top:1rem; font-weight:600; color:#cbd5e1; font-size:0.85rem;'>Détail des trades · {tickers_list}</div>", unsafe_allow_html=True)
                for _, t in sub.sort_values("transaction_date", ascending=False).head(15).iterrows():
                    ttype = (t.get("type") or "").lower()
                    sens = "Achat" if "purchase" in ttype else "Vente"
                    asset = t.get("asset") or t.get("ticker") or "—"
                    st.markdown(
                        html_tx_item(
                            sens,
                            f"{sens} — {asset}",
                            f"Déclaré le {fmt_date(t['disclosure_date'])}",
                            t.get("ticker") or "—",
                            t["montant_est"],
                            fmt_date(t["transaction_date"]),
                        ),
                        unsafe_allow_html=True,
                    )

                if row["nb"] > 15:
                    st.caption(f"… et {row['nb'] - 15} trades plus anciens (données Bargo limitées aux 90 derniers jours)")


# ============================================================
# ENTREPRISES
# ============================================================
with tab_entreprises:
    st.markdown(
        """
        <div class="hero">
            <div class="hero-eyebrow">🏢 WATCHLIST</div>
            <div class="hero-title">Les entreprises sous radar.</div>
            <div class="hero-sub">Trente grandes capitalisations américaines suivies en continu. Cliquez pour explorer l'activité insider par entreprise.</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    df_all = fetch_all_insiders(API_KEY)
    if df_all.empty:
        st.warning("Aucune donnée.")
    else:
        agg = (
            df_all.groupby("symbol")
                  .agg(nb=("symbol","size"), vol=("montant","sum"),
                       inside=("name","nunique"))
                  .sort_values("vol", ascending=False).reset_index()
        )

        for _, row in agg.iterrows():
            nom = WATCHLIST.get(row["symbol"], row["symbol"])
            label = f"🏢   {row['symbol']}   ·   {nom}   ·   ${fmt_num(row['vol'])}   ·   {row['inside']} dirigeants"
            with st.expander(label):
                sub = df_all[df_all["symbol"] == row["symbol"]].copy()
                achats = (sub["change"] > 0).sum()
                ventes = (sub["change"] < 0).sum()

                st.markdown(
                    html_mini_kpis([
                        ("Volume", f"${fmt_num(row['vol'])}"),
                        ("Transactions", f"{row['nb']}"),
                        ("Dirigeants", f"{row['inside']}"),
                        ("Achats", f"🟢 {achats}"),
                        ("Ventes", f"🔴 {ventes}"),
                        ("Prix moyen", f"${sub['transactionPrice'].mean():,.2f}"),
                    ]),
                    unsafe_allow_html=True,
                )

                activity_chart(sub["transactionDate"])

                st.markdown("<div style='margin-top:1rem; font-weight:600; color:#cbd5e1; font-size:0.85rem;'>Dernières opérations</div>", unsafe_allow_html=True)
                for _, t in sub.head(12).iterrows():
                    sens = "Achat" if t["change"] > 0 else "Vente"
                    st.markdown(
                        html_tx_item(
                            sens,
                            f"{t['name']}",
                            f"{int(t['change']):+,} actions à ${t['transactionPrice']:,.2f}",
                            t["symbol"],
                            t["montant"],
                            fmt_date(t["transactionDate"]),
                        ),
                        unsafe_allow_html=True,
                    )


# ============================================================
# RECHERCHE
# ============================================================
with tab_recherche:
    st.markdown(
        """
        <div class="hero">
            <div class="hero-eyebrow">🔍 RECHERCHE</div>
            <div class="hero-title">Analysez n'importe quel ticker.</div>
            <div class="hero-sub">Entrez un symbole boursier (même hors watchlist) pour voir l'activité complète de ses dirigeants.</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    col_in, col_btn = st.columns([4, 1])
    with col_in:
        saisi = st.text_input("Ticker", value="AAPL", max_chars=10,
                              placeholder="AAPL, MSFT, TSLA…",
                              label_visibility="collapsed")
    with col_btn:
        if st.button("Actualiser", use_container_width=True):
            st.cache_data.clear()
            st.rerun()

    ticker = saisi.strip().upper()
    if not ticker:
        st.info("Saisissez un ticker.")
        st.stop()

    df = fetch_insider_tx(ticker, API_KEY)
    if df.empty:
        st.warning(f"Aucune transaction trouvée pour **{ticker}**.")
        st.stop()

    nb = len(df)
    nb_in = df["name"].nunique()
    vol = df["montant"].sum()
    achats = (df["change"] > 0).sum()
    ventes = (df["change"] < 0).sum()
    net = int(df["change"].sum())
    net_cls = "pos" if net >= 0 else "neg"
    net_sgn = "+" if net >= 0 else ""

    st.markdown(
        f"""
        <div class="stat-grid">
            <div class="stat-tile">
                <div class="stat-tile-label">Transactions</div>
                <div class="stat-tile-value">{nb}</div>
                <div class="stat-tile-delta"><span class="pos">↑ {achats}</span> · <span class="neg">↓ {ventes}</span></div>
            </div>
            <div class="stat-tile">
                <div class="stat-tile-label">Dirigeants</div>
                <div class="stat-tile-value">{nb_in}</div>
                <div class="stat-tile-delta">impliqués</div>
            </div>
            <div class="stat-tile">
                <div class="stat-tile-label">Volume</div>
                <div class="stat-tile-value">${fmt_num(vol)}</div>
                <div class="stat-tile-delta">cumul période</div>
            </div>
            <div class="stat-tile">
                <div class="stat-tile-label">Flux net</div>
                <div class="stat-tile-value {net_cls}">{net_sgn}{fmt_num(net)}</div>
                <div class="stat-tile-delta">actions nettes</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        f"""
        <div class="section-head">
            <div class="section-title">📈 Activité {ticker}</div>
            <div class="section-meta">30 derniers jours</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    activity_chart(df["transactionDate"])

    st.markdown(
        """
        <div class="section-head">
            <div class="section-title">📋 Toutes les transactions</div>
            <div class="section-meta">cliquez pour les détails</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    for _, row in df.iterrows():
        sens = "Achat" if row["change"] > 0 else "Vente"
        label = f"{'🟢' if row['change']>0 else '🔴'}   {row['name']}   ·   {sens}   ·   ${fmt_num(row['montant'])}   ·   {fmt_date(row['transactionDate'])}"
        with st.expander(label):
            st.markdown(
                html_mini_kpis([
                    ("Sens", f"{'🟢 Achat' if row['change']>0 else '🔴 Vente'}"),
                    ("Actions", f"{int(row['change']):+,}"),
                    ("Prix unitaire", f"${row['transactionPrice']:,.2f}"),
                    ("Montant", f"${row['montant']:,.0f}"),
                    ("Détention après", f"{int(row['share']):,}"),
                    ("Date", fmt_date(row['transactionDate'])),
                ]),
                unsafe_allow_html=True,
            )


# ============================================================
# FOOTER
# ============================================================
st.markdown(
    """
    <div class="footer">
        <div class="footer-brand">SENTINELLE</div>
        Données officielles SEC Form 4 (Finnhub) · Bargo API pour le Congrès US<br>
        Sentinelle est un outil informatif et ne constitue pas un conseil en investissement.
    </div>
    """,
    unsafe_allow_html=True,
)
