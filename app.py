import streamlit as st
import requests
import pandas as pd
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta

# ================================================================
# CLÉ API FINNHUB (via Streamlit Secrets)
# ================================================================
try:
    API_KEY = st.secrets["FINNHUB_API_KEY"]
except Exception:
    API_KEY = "A_REMPLIR"

BARGO_BASE = "https://www.bargo.ai/free-apis/congress/v1"

# Fenêtre temporelle : 90 derniers jours
AUJ = datetime.utcnow().date()
DEBUT = AUJ - timedelta(days=90)

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
# STYLE
# ============================================================
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=JetBrains+Mono:wght@500;600&display=swap');

    :root {
      --bg: #050812;
      --card: #0e1424;
      --card-h: #121a2e;
      --border: rgba(255,255,255,0.07);
      --border-h: rgba(99,196,255,0.3);
      --txt: #e8ecf5;
      --mut: #7a8599;
      --dim: #4a556b;
      --acc: #63c4ff;
      --green: #22c55e;
      --red: #f43f5e;
      --gold: #f0b429;
    }

    html, body, .stApp, button, input, textarea {
        font-family: 'Inter', sans-serif !important;
        letter-spacing: -0.01em;
    }

    .stApp {
        background:
            radial-gradient(900px 500px at 15% -5%, rgba(91,141,239,0.1), transparent 60%),
            radial-gradient(700px 400px at 95% 5%, rgba(99,196,255,0.07), transparent 55%),
            linear-gradient(180deg, #0d1326 0%, #050812 100%);
        color: var(--txt);
    }
    [data-testid="stHeader"] { background: transparent; }
    .block-container { padding-top: 1.2rem; max-width: 1180px; }

    .hdr {
        display: flex; align-items: center; justify-content: space-between;
        padding: 0.4rem 0 1.2rem 0;
    }
    .brand { display: flex; align-items: center; gap: 0.8rem; }
    .logo {
        width: 38px; height: 38px; border-radius: 10px;
        display: flex; align-items: center; justify-content: center;
        background: linear-gradient(135deg, #1a2447, #0b1024);
        border: 1px solid rgba(99,196,255,0.3);
        box-shadow: 0 0 20px rgba(99,196,255,0.15);
    }
    .bn { font-size: 1.1rem; font-weight: 800; letter-spacing: 5px; color: #f8fafc; }
    .bt { font-size: 0.68rem; color: var(--mut); text-transform: uppercase; letter-spacing: 2.5px; font-weight: 600; }
    .pill {
        display: inline-flex; align-items: center; gap: 0.4rem;
        padding: 0.35rem 0.75rem;
        background: rgba(240,180,41,0.1);
        border: 1px solid rgba(240,180,41,0.25);
        border-radius: 999px;
        font-size: 0.7rem; font-weight: 600; color: var(--gold);
        letter-spacing: 0.5px;
    }

    .hero { padding: 1rem 0 1.8rem 0; border-bottom: 1px solid var(--border); margin-bottom: 1.5rem; }
    .hero-eb {
        display: inline-block; padding: 0.3rem 0.75rem;
        background: rgba(99,196,255,0.08); border: 1px solid rgba(99,196,255,0.2);
        border-radius: 999px; font-size: 0.68rem; font-weight: 600; color: var(--acc);
        text-transform: uppercase; letter-spacing: 2px; margin-bottom: 1rem;
    }
    .hero-t { font-size: 2.3rem; font-weight: 800; color: #f8fafc; line-height: 1.1; letter-spacing: -0.03em; margin-bottom: 0.6rem; }
    .hero-s { font-size: 1rem; color: var(--mut); max-width: 640px; line-height: 1.5; }

    [data-baseweb="tab-list"] {
        background: rgba(10,15,30,0.5);
        border-radius: 14px; padding: 0.35rem; gap: 0.15rem;
        border: 1px solid var(--border);
    }
    [data-baseweb="tab"] {
        background: transparent !important; border-radius: 10px !important;
        color: var(--mut) !important; font-weight: 600 !important;
        font-size: 0.92rem !important; padding: 0.6rem 1.1rem !important;
    }
    [data-baseweb="tab"][aria-selected="true"] {
        background: linear-gradient(135deg, rgba(99,196,255,0.18), rgba(91,141,239,0.15)) !important;
        color: #f8fafc !important;
        box-shadow: inset 0 0 0 1px rgba(99,196,255,0.25);
    }
    [data-baseweb="tab-highlight"], [data-baseweb="tab-border"] { display: none !important; }

    .sh { display: flex; align-items: baseline; justify-content: space-between; margin: 2rem 0 0.9rem 0; }
    .st-t { font-size: 1.3rem; font-weight: 700; color: #f1f5f9; letter-spacing: -0.02em; }
    .st-m { font-size: 0.78rem; color: var(--mut); font-weight: 500; }

    .sg { display: grid; grid-template-columns: repeat(auto-fit, minmax(170px, 1fr)); gap: 0.8rem; margin-bottom: 0.5rem; }
    .st-c {
        background: var(--card); border: 1px solid var(--border); border-radius: 14px;
        padding: 1rem 1.2rem; position: relative; overflow: hidden;
    }
    .st-c::before {
        content: ''; position: absolute; left: 0; top: 0; height: 2px; width: 100%;
        background: linear-gradient(90deg, var(--acc), transparent); opacity: 0.5;
    }
    .st-l { font-size: 0.66rem; color: var(--mut); font-weight: 600; text-transform: uppercase; letter-spacing: 1.5px; margin-bottom: 0.55rem; }
    .st-v { font-size: 1.6rem; font-weight: 700; color: #f8fafc; line-height: 1.05; letter-spacing: -0.02em; }
    .st-d { font-size: 0.74rem; color: var(--mut); margin-top: 0.3rem; }
    .pos { color: var(--green); }
    .neg { color: var(--red); }

    .row {
        display: grid; grid-template-columns: auto 1fr auto auto;
        gap: 0.9rem; align-items: center;
        padding: 0.85rem 1rem;
        background: var(--card); border: 1px solid var(--border);
        border-radius: 12px; margin-bottom: 0.45rem;
        transition: all 0.12s;
    }
    .row:hover { border-color: var(--border-h); background: var(--card-h); }
    .ri {
        width: 34px; height: 34px; border-radius: 10px;
        display: flex; align-items: center; justify-content: center;
        font-weight: 700; font-size: 0.9rem; flex-shrink: 0;
    }
    .ib { background: rgba(34,197,94,0.14); color: var(--green); }
    .is { background: rgba(244,63,94,0.14); color: var(--red); }
    .rm { min-width: 0; }
    .rn { font-weight: 600; color: #f1f5f9; font-size: 0.95rem; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
    .rs { font-size: 0.77rem; color: var(--mut); margin-top: 0.12rem; }
    .rc {
        padding: 0.3rem 0.6rem; border-radius: 8px; background: rgba(99,196,255,0.08);
        color: var(--acc); font-size: 0.73rem; font-weight: 700;
        font-family: 'JetBrains Mono', monospace; letter-spacing: 0.5px;
    }
    .ra { font-size: 0.95rem; font-weight: 700; color: #f8fafc; font-family: 'JetBrains Mono', monospace; text-align: right; min-width: 90px; }
    .rd { font-size: 0.7rem; color: var(--mut); text-align: right; margin-top: 0.15rem; }

    [data-testid="stExpander"] {
        background: var(--card) !important; border: 1px solid var(--border) !important;
        border-radius: 12px !important; margin-bottom: 0.5rem !important;
        overflow: hidden; transition: all 0.12s;
    }
    [data-testid="stExpander"]:hover { border-color: var(--border-h) !important; }
    [data-testid="stExpander"] summary {
        padding: 0.9rem 1.1rem !important; color: #f1f5f9 !important;
        font-weight: 500 !important; font-size: 0.92rem !important;
    }
    [data-testid="stExpander"] [data-testid="stExpanderDetails"] {
        padding: 0.3rem 1.1rem 1.1rem !important; border-top: 1px solid var(--border);
    }

    .mg { display: grid; grid-template-columns: repeat(auto-fit, minmax(110px, 1fr)); gap: 0.5rem; margin: 0.9rem 0 1rem 0; }
    .mi { background: rgba(255,255,255,0.02); border: 1px solid var(--border); border-radius: 10px; padding: 0.6rem 0.85rem; }
    .ml { font-size: 0.65rem; color: var(--mut); font-weight: 600; text-transform: uppercase; letter-spacing: 1.2px; }
    .mv { font-size: 1.02rem; font-weight: 700; color: #f8fafc; margin-top: 0.2rem; font-family: 'JetBrains Mono', monospace; }

    .ti {
        display: grid; grid-template-columns: 24px 1fr auto auto;
        gap: 0.7rem; align-items: center;
        padding: 0.55rem 0.75rem;
        background: rgba(255,255,255,0.02); border-radius: 8px;
        margin-bottom: 0.25rem; font-size: 0.85rem;
    }
    .ta { font-weight: 700; font-size: 0.95rem; }
    .tx-chip {
        background: rgba(99,196,255,0.1); color: var(--acc);
        padding: 0.18rem 0.5rem; border-radius: 6px;
        font-size: 0.7rem; font-weight: 700;
        font-family: 'JetBrains Mono', monospace;
    }

    .stTextInput input {
        background: var(--card) !important; color: var(--txt) !important;
        border: 1px solid var(--border) !important; border-radius: 10px !important;
        padding: 0.72rem 1rem !important; font-size: 1rem !important;
    }
    .stButton > button {
        background: linear-gradient(135deg, #5b8def, #63c4ff) !important;
        color: white !important; border: none !important;
        border-radius: 10px; font-weight: 600; padding: 0.6rem 1.2rem;
    }

    .info-box {
        background: rgba(99,196,255,0.06);
        border: 1px solid rgba(99,196,255,0.2);
        border-radius: 12px; padding: 0.9rem 1.1rem;
        margin: 1rem 0; font-size: 0.85rem; color: #cbd5e1;
        line-height: 1.5;
    }
    .info-box b { color: var(--acc); }

    .foot {
        margin-top: 3rem; padding: 1.8rem 0 1rem;
        border-top: 1px solid var(--border);
        text-align: center; color: var(--dim); font-size: 0.75rem;
    }
    .foot b { letter-spacing: 3px; color: var(--mut); }

    #MainMenu, footer, header { visibility: hidden; }
    </style>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# HELPERS
# ============================================================
def fmt_num(n) -> str:
    try:
        n = float(n)
    except (TypeError, ValueError):
        return "—"
    if pd.isna(n):
        return "—"
    if abs(n) >= 1e9: return f"{n/1e9:.2f}Md"
    if abs(n) >= 1e6: return f"{n/1e6:.2f}M"
    if abs(n) >= 1e3: return f"{n/1e3:.1f}k"
    return f"{n:.0f}"


MOIS_FR = {"Jan":"janv.", "Feb":"févr.", "Mar":"mars", "Apr":"avr.",
           "May":"mai", "Jun":"juin", "Jul":"juil.", "Aug":"août",
           "Sep":"sept.", "Oct":"oct.", "Nov":"nov.", "Dec":"déc."}


def fmt_date(d) -> str:
    if d is None or pd.isna(d):
        return "—"
    try:
        s = d.strftime("%d %b %Y")
    except Exception:
        return "—"
    for en, fr in MOIS_FR.items():
        s = s.replace(en, fr)
    return s


def safe(s, default="—"):
    if s is None:
        return default
    if isinstance(s, float) and pd.isna(s):
        return default
    s = str(s).strip()
    return s if s else default


# ============================================================
# API — FINNHUB
# ============================================================
@st.cache_data(ttl=1800, show_spinner=False)
def fetch_insider_tx(symbol: str, api_key: str, days: int = 90) -> pd.DataFrame:
    """Récupère les transactions insider pour les X derniers jours."""
    to_d = datetime.utcnow().date()
    from_d = to_d - timedelta(days=days)
    try:
        r = requests.get(
            "https://finnhub.io/api/v1/stock/insider-transactions",
            params={
                "symbol": symbol,
                "token": api_key,
                "from": from_d.isoformat(),
                "to": to_d.isoformat(),
            },
            timeout=10,
        )
        r.raise_for_status()
        data = r.json().get("data", [])
    except requests.RequestException:
        return pd.DataFrame()
    if not data:
        return pd.DataFrame()
    df = pd.DataFrame(data)
    df["transactionDate"] = pd.to_datetime(df.get("transactionDate"), errors="coerce")
    df["filingDate"] = pd.to_datetime(df.get("filingDate"), errors="coerce")
    df["transactionPrice"] = pd.to_numeric(df.get("transactionPrice"), errors="coerce").fillna(0)
    df["change"] = pd.to_numeric(df.get("change"), errors="coerce").fillna(0)
    df["share"] = pd.to_numeric(df.get("share"), errors="coerce").fillna(0)
    df["montant"] = df["change"].abs() * df["transactionPrice"]
    df["symbol"] = symbol
    # Normaliser le nom
    df["name"] = df.get("name", "").astype(str).str.strip()
    # Filtrer les lignes sans montant utile
    df = df[df["transactionPrice"] > 0].copy()
    return df.sort_values("transactionDate", ascending=False, na_position="last").reset_index(drop=True)


@st.cache_data(ttl=1800, show_spinner="Chargement des dirigeants d'entreprise…")
def fetch_all_insiders(api_key: str, days: int = 90) -> pd.DataFrame:
    with ThreadPoolExecutor(max_workers=10) as ex:
        results = list(ex.map(lambda t: fetch_insider_tx(t, api_key, days), WATCHLIST.keys()))
    non_empty = [df for df in results if not df.empty]
    if not non_empty:
        return pd.DataFrame()
    agg = pd.concat(non_empty, ignore_index=True)
    agg["entreprise"] = agg["symbol"].map(WATCHLIST)
    return agg


# ============================================================
# API — BARGO (Congrès US)
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

    def mid_range(s):
        if not isinstance(s, str):
            return 0.0
        s2 = s.replace("$", "").replace(",", "").replace("+", "").strip()
        if "-" in s2:
            a, b = s2.split("-", 1)
            try: return (float(a.strip()) + float(b.strip())) / 2
            except: return 0.0
        try: return float(s2)
        except: return 0.0

    df["montant_est"] = df.get("amount_range", pd.Series(dtype=str)).apply(mid_range)
    for col in ["member", "ticker", "chamber", "state", "type", "asset", "amount_range"]:
        if col in df.columns:
            df[col] = df[col].astype(str).replace({"nan": "", "None": ""})
        else:
            df[col] = ""
    return df.sort_values("transaction_date", ascending=False, na_position="last").reset_index(drop=True)


# ============================================================
# COMPOSANTS HTML
# ============================================================
def row_insider(row) -> str:
    is_buy = row["change"] > 0
    ico = "↑" if is_buy else "↓"
    cls = "ib" if is_buy else "is"
    sens = "A acheté des actions" if is_buy else "A vendu des actions"
    ent = WATCHLIST.get(row["symbol"], row["symbol"])
    return f"""
    <div class="row">
        <div class="ri {cls}">{ico}</div>
        <div class="rm">
            <div class="rn">{safe(row['name'])}</div>
            <div class="rs">{sens} {ent}</div>
        </div>
        <div class="rc">{row['symbol']}</div>
        <div>
            <div class="ra">${fmt_num(row['montant'])}</div>
            <div class="rd">{fmt_date(row['transactionDate'])}</div>
        </div>
    </div>
    """


def row_congress(row) -> str:
    is_buy = "purchase" in (row.get("type") or "").lower()
    ico = "↑" if is_buy else "↓"
    cls = "ib" if is_buy else "is"
    sens = "A acheté" if is_buy else "A vendu"
    ticker = safe(row.get("ticker"), "N/A")
    chamber = (row.get("chamber") or "").capitalize() or "Congrès"
    state = row.get("state") or ""
    return f"""
    <div class="row">
        <div class="ri {cls}">{ico}</div>
        <div class="rm">
            <div class="rn">{safe(row.get('member'))}</div>
            <div class="rs">{sens} · {chamber} {state}</div>
        </div>
        <div class="rc">{ticker}</div>
        <div>
            <div class="ra">${fmt_num(row['montant_est'])}</div>
            <div class="rd">{fmt_date(row['transaction_date'])}</div>
        </div>
    </div>
    """


def mini_kpis(items) -> str:
    html = '<div class="mg">'
    for lbl, val in items:
        html += f'<div class="mi"><div class="ml">{lbl}</div><div class="mv">{val}</div></div>'
    return html + '</div>'


def tx_line(sens, main, sub, ticker, montant, date) -> str:
    is_buy = "achat" in sens.lower()
    arrow = "↑" if is_buy else "↓"
    color = "var(--green)" if is_buy else "var(--red)"
    return f"""
    <div class="ti">
        <div class="ta" style="color:{color}">{arrow}</div>
        <div>
            <div style="color:#e2e8f0; font-weight:500;">{main}</div>
            <div style="color:var(--mut); font-size:0.72rem; margin-top:0.08rem;">{sub}</div>
        </div>
        <div class="tx-chip">{ticker}</div>
        <div style="text-align:right;">
            <div style="color:#f8fafc; font-weight:700; font-family:'JetBrains Mono', monospace;">${fmt_num(montant)}</div>
            <div class="rd">{date}</div>
        </div>
    </div>
    """


def chart_activite(dates_series):
    """Barres : nombre de transactions par semaine, 90 jours."""
    try:
        s = pd.to_datetime(dates_series, errors="coerce").dropna()
        if s.empty:
            return
        s = s[s >= pd.Timestamp(DEBUT)]
        if s.empty:
            return
        weekly = s.dt.to_period("W").value_counts().sort_index()
        df_c = pd.DataFrame({
            "Semaine": [p.start_time for p in weekly.index],
            "Transactions": weekly.values,
        }).set_index("Semaine")
        st.bar_chart(df_c, height=140, use_container_width=True, color="#63c4ff")
    except Exception:
        pass


# ============================================================
# HEADER
# ============================================================
st.markdown(
    f"""
    <div class="hdr">
        <div class="brand">
            <div class="logo">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#63c4ff" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
                    <path d="M12 2L4 6v6c0 5 3.5 9.5 8 10 4.5-0.5 8-5 8-10V6l-8-4z"/>
                    <path d="M12 8v5"/>
                </svg>
            </div>
            <div>
                <div class="bn">SENTINELLE</div>
                <div class="bt">INSIDER · TRACKER</div>
            </div>
        </div>
        <div class="pill">📅 90 DERNIERS JOURS · {DEBUT.strftime('%d/%m')} → {AUJ.strftime('%d/%m')}</div>
    </div>
    """,
    unsafe_allow_html=True,
)


if API_KEY == "A_REMPLIR":
    st.error("⚠️ Clé API Finnhub manquante. Ajoutez `FINNHUB_API_KEY` dans les Secrets de Streamlit Cloud.")
    st.stop()


# Chargement des données (une seule fois, partagé entre tous les onglets)
df_insiders = fetch_all_insiders(API_KEY, days=90)
df_congress = fetch_congress_trades(100)


# ============================================================
# ONGLETS
# ============================================================
tab_acc, tab_dir, tab_elu, tab_ent, tab_rech = st.tabs([
    "Accueil", "Dirigeants", "Élus US", "Entreprises", "Recherche"
])


# ============================================================
# ACCUEIL
# ============================================================
with tab_acc:
    st.markdown(
        """
        <div class="hero">
            <div class="hero-eb">⚡ Flux officiel · SEC + Congrès US</div>
            <div class="hero-t">L'intelligence du capital,<br>sans le bruit.</div>
            <div class="hero-s">Déclarations officielles des dirigeants d'entreprises cotées et des membres du Congrès américain sur les 90 derniers jours.</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    vol_i = float(df_insiders["montant"].sum()) if not df_insiders.empty else 0
    vol_c = float(df_congress["montant_est"].sum()) if not df_congress.empty else 0
    nb_i = int(df_insiders["name"].nunique()) if not df_insiders.empty else 0
    nb_c = int(df_congress["member"].nunique()) if not df_congress.empty else 0
    total_tx = len(df_insiders) + len(df_congress)

    st.markdown(
        f"""
        <div class="sg">
            <div class="st-c"><div class="st-l">Volume dirigeants</div><div class="st-v">${fmt_num(vol_i)}</div><div class="st-d">{nb_i} dirigeants actifs</div></div>
            <div class="st-c"><div class="st-l">Volume élus US</div><div class="st-v">${fmt_num(vol_c)}</div><div class="st-d">{nb_c} membres du Congrès</div></div>
            <div class="st-c"><div class="st-l">Transactions suivies</div><div class="st-v">{total_tx:,}</div><div class="st-d">90 derniers jours</div></div>
            <div class="st-c"><div class="st-l">Entreprises couvertes</div><div class="st-v">{len(WATCHLIST)}</div><div class="st-d">watchlist S&P</div></div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if not df_insiders.empty:
        st.markdown(
            """
            <div class="sh">
                <div class="st-t">🔥 Gros mouvements — dirigeants</div>
                <div class="st-m">Top 6 par montant · 90 derniers jours</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        for _, row in df_insiders.sort_values("montant", ascending=False).head(6).iterrows():
            st.markdown(row_insider(row), unsafe_allow_html=True)
    else:
        st.info("Aucune transaction de dirigeant sur les 90 derniers jours.")

    if not df_congress.empty:
        st.markdown(
            """
            <div class="sh">
                <div class="st-t">🏛️ Gros mouvements — élus US</div>
                <div class="st-m">Top 6 par montant estimé</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        for _, row in df_congress.sort_values("montant_est", ascending=False).head(6).iterrows():
            st.markdown(row_congress(row), unsafe_allow_html=True)
    else:
        st.info("Données du Congrès temporairement indisponibles (limite Bargo API).")


# ============================================================
# DIRIGEANTS
# ============================================================
with tab_dir:
    st.markdown(
        """
        <div class="hero">
            <div class="hero-eb">👔 DIRIGEANTS D'ENTREPRISE</div>
            <div class="hero-t">Les mouvements des insiders.</div>
            <div class="hero-s">Dirigeants les plus actifs sur la watchlist. Cliquez pour voir le détail.</div>
        </div>
        <div class="info-box">
            ⚠️ <b>Important :</b> la SEC n'oblige un dirigeant à déclarer ses trades que sur <b>sa propre entreprise</b>. On voit donc ici tous les trades de Musk sur Tesla, mais pas ses éventuels achats de Microsoft ou Google en tant que simple investisseur (non publics). Pour voir des personnes qui tradent sur TOUT, ouvrez l'onglet <b>Élus US</b>.
        </div>
        """,
        unsafe_allow_html=True,
    )

    if df_insiders.empty:
        st.warning("Aucune donnée disponible.")
    else:
        top_i = (
            df_insiders.groupby("name")
                       .agg(nb=("name","size"), vol=("montant","sum"),
                            entr=("symbol", lambda s: sorted(set(s))))
                       .sort_values("vol", ascending=False).head(25).reset_index()
        )

        for _, row in top_i.iterrows():
            tickers = ", ".join(row["entr"])
            nom_aff = safe(row["name"], "Inconnu")
            label = f"👤   {nom_aff}   ·   {tickers}   ·   ${fmt_num(row['vol'])}   ·   {row['nb']} trades"
            with st.expander(label):
                sub = df_insiders[df_insiders["name"] == row["name"]].copy()
                achats = int((sub["change"] > 0).sum())
                ventes = int((sub["change"] < 0).sum())
                net = int(sub["change"].sum())

                st.markdown(mini_kpis([
                    ("Volume", f"${fmt_num(row['vol'])}"),
                    ("Trades", f"{row['nb']}"),
                    ("Achats", f"🟢 {achats}"),
                    ("Ventes", f"🔴 {ventes}"),
                    ("Flux net", f"{net:+,}"),
                    ("Entreprises", tickers),
                ]), unsafe_allow_html=True)

                chart_activite(sub["transactionDate"])

                st.markdown("<div style='margin-top:1rem; font-weight:600; color:#cbd5e1; font-size:0.85rem;'>Détail des opérations</div>", unsafe_allow_html=True)
                for _, t in sub.sort_values("transactionDate", ascending=False).head(15).iterrows():
                    sens_lbl = "Achat" if t["change"] > 0 else "Vente"
                    ent = WATCHLIST.get(t["symbol"], t["symbol"])
                    st.markdown(tx_line(
                        sens_lbl,
                        f"{sens_lbl} — {ent}",
                        f"{int(t['change']):+,} actions à ${t['transactionPrice']:,.2f}",
                        t["symbol"],
                        t["montant"],
                        fmt_date(t["transactionDate"]),
                    ), unsafe_allow_html=True)
                if row["nb"] > 15:
                    st.caption(f"… et {row['nb'] - 15} trades plus anciens")


# ============================================================
# ÉLUS US
# ============================================================
with tab_elu:
    st.markdown(
        """
        <div class="hero">
            <div class="hero-eb">🏛️ CONGRÈS US · STOCK Act</div>
            <div class="hero-t">Ce que les parlementaires achètent.</div>
            <div class="hero-s">Déclarations officielles des sénateurs et représentants US. Ici on voit TOUS leurs trades, sur toutes les entreprises.</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if df_congress.empty:
        st.warning("Données du Congrès temporairement indisponibles.")
        st.caption("L'API Bargo (gratuite, sans compte) limite à 30 requêtes/jour. Patientez ou on peut passer à un compte Bargo gratuit pour 100 req/jour.")
    else:
        top_m = (
            df_congress.groupby("member")
                       .agg(
                           nb=("member","size"),
                           vol=("montant_est","sum"),
                           chamber=("chamber","first"),
                           state=("state","first"),
                           tickers=("ticker", lambda s: sorted(set(x for x in s if x and x != "nan"))),
                       )
                       .sort_values("vol", ascending=False).head(25).reset_index()
        )

        for _, row in top_m.iterrows():
            chamber_ico = "🏛️" if (row["chamber"] or "").lower() == "senate" else "🏢"
            ch = (row["chamber"] or "").capitalize()
            label = f"{chamber_ico}   {safe(row['member'], 'Inconnu')}   ·   {ch} {row['state']}   ·   ${fmt_num(row['vol'])}   ·   {row['nb']} trades"
            with st.expander(label):
                sub = df_congress[df_congress["member"] == row["member"]].copy()
                achats = int(sub["type"].str.lower().str.contains("purchase", na=False).sum())
                ventes = int(sub["type"].str.lower().str.contains("sale", na=False).sum())
                ticks = row["tickers"][:8]
                ticks_str = ", ".join(ticks) + (f" (+{len(row['tickers']) - 8})" if len(row["tickers"]) > 8 else "")

                st.markdown(mini_kpis([
                    ("Volume est.", f"${fmt_num(row['vol'])}"),
                    ("Trades", f"{row['nb']}"),
                    ("Achats", f"🟢 {achats}"),
                    ("Ventes", f"🔴 {ventes}"),
                    ("Chambre", ch or "—"),
                    ("Tickers tradés", f"{len(row['tickers'])}"),
                ]), unsafe_allow_html=True)

                chart_activite(sub["transaction_date"])

                st.markdown(f"<div style='margin-top:1rem; font-weight:600; color:#cbd5e1; font-size:0.85rem;'>Trades · {ticks_str}</div>", unsafe_allow_html=True)
                for _, t in sub.sort_values("transaction_date", ascending=False).head(15).iterrows():
                    ttype = (t.get("type") or "").lower()
                    sens_lbl = "Achat" if "purchase" in ttype else "Vente"
                    asset = safe(t.get("asset"), safe(t.get("ticker"), "—"))
                    st.markdown(tx_line(
                        sens_lbl,
                        f"{sens_lbl} — {asset}",
                        f"Déclaré le {fmt_date(t['disclosure_date'])}",
                        safe(t.get("ticker"), "N/A"),
                        t["montant_est"],
                        fmt_date(t["transaction_date"]),
                    ), unsafe_allow_html=True)
                if row["nb"] > 15:
                    st.caption(f"… et {row['nb'] - 15} trades plus anciens")


# ============================================================
# ENTREPRISES
# ============================================================
with tab_ent:
    st.markdown(
        """
        <div class="hero">
            <div class="hero-eb">🏢 WATCHLIST</div>
            <div class="hero-t">Entreprises sous radar.</div>
            <div class="hero-s">30 grandes capitalisations US. Cliquez pour explorer l'activité insider par entreprise.</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if df_insiders.empty:
        st.warning("Aucune donnée.")
    else:
        agg = (
            df_insiders.groupby("symbol")
                       .agg(nb=("symbol","size"), vol=("montant","sum"),
                            inside=("name","nunique"))
                       .sort_values("vol", ascending=False).reset_index()
        )

        for _, row in agg.iterrows():
            nom = WATCHLIST.get(row["symbol"], row["symbol"])
            label = f"🏢   {row['symbol']}   ·   {nom}   ·   ${fmt_num(row['vol'])}   ·   {row['inside']} dirigeants"
            with st.expander(label):
                sub = df_insiders[df_insiders["symbol"] == row["symbol"]].copy()
                achats = int((sub["change"] > 0).sum())
                ventes = int((sub["change"] < 0).sum())
                prix_moy = sub["transactionPrice"].mean()

                st.markdown(mini_kpis([
                    ("Volume", f"${fmt_num(row['vol'])}"),
                    ("Trades", f"{row['nb']}"),
                    ("Dirigeants", f"{row['inside']}"),
                    ("Achats", f"🟢 {achats}"),
                    ("Ventes", f"🔴 {ventes}"),
                    ("Prix moyen", f"${prix_moy:,.2f}"),
                ]), unsafe_allow_html=True)

                chart_activite(sub["transactionDate"])

                st.markdown("<div style='margin-top:1rem; font-weight:600; color:#cbd5e1; font-size:0.85rem;'>Dernières opérations</div>", unsafe_allow_html=True)
                for _, t in sub.sort_values("transactionDate", ascending=False).head(12).iterrows():
                    sens_lbl = "Achat" if t["change"] > 0 else "Vente"
                    st.markdown(tx_line(
                        sens_lbl,
                        safe(t["name"]),
                        f"{int(t['change']):+,} actions à ${t['transactionPrice']:,.2f}",
                        t["symbol"],
                        t["montant"],
                        fmt_date(t["transactionDate"]),
                    ), unsafe_allow_html=True)


# ============================================================
# RECHERCHE
# ============================================================
with tab_rech:
    st.markdown(
        """
        <div class="hero">
            <div class="hero-eb">🔍 RECHERCHE</div>
            <div class="hero-t">Analysez un ticker.</div>
            <div class="hero-s">Entrez un symbole boursier (même hors watchlist) pour voir ses mouvements insiders sur 90 jours.</div>
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
    if ticker:
        df_r = fetch_insider_tx(ticker, API_KEY, days=90)
        if df_r.empty:
            st.warning(f"Aucune transaction trouvée pour **{ticker}** sur les 90 derniers jours.")
        else:
            nb = len(df_r)
            nb_in = int(df_r["name"].nunique())
            vol = float(df_r["montant"].sum())
            achats = int((df_r["change"] > 0).sum())
            ventes = int((df_r["change"] < 0).sum())
            net = int(df_r["change"].sum())
            net_cls = "pos" if net >= 0 else "neg"
            net_sgn = "+" if net >= 0 else ""

            st.markdown(
                f"""
                <div class="sg">
                    <div class="st-c"><div class="st-l">Transactions</div><div class="st-v">{nb}</div><div class="st-d"><span class="pos">↑ {achats}</span> · <span class="neg">↓ {ventes}</span></div></div>
                    <div class="st-c"><div class="st-l">Dirigeants</div><div class="st-v">{nb_in}</div><div class="st-d">impliqués</div></div>
                    <div class="st-c"><div class="st-l">Volume</div><div class="st-v">${fmt_num(vol)}</div><div class="st-d">cumul 90j</div></div>
                    <div class="st-c"><div class="st-l">Flux net</div><div class="st-v {net_cls}">{net_sgn}{fmt_num(net)}</div><div class="st-d">actions nettes</div></div>
                </div>
                """,
                unsafe_allow_html=True,
            )

            st.markdown('<div class="sh"><div class="st-t">📈 Activité</div><div class="st-m">90 derniers jours</div></div>', unsafe_allow_html=True)
            chart_activite(df_r["transactionDate"])

            st.markdown('<div class="sh"><div class="st-t">📋 Transactions</div><div class="st-m">cliquez pour les détails</div></div>', unsafe_allow_html=True)
            for _, r in df_r.iterrows():
                sens_lbl = "Achat" if r["change"] > 0 else "Vente"
                ico = "🟢" if r["change"] > 0 else "🔴"
                label = f"{ico}   {safe(r['name'])}   ·   {sens_lbl}   ·   ${fmt_num(r['montant'])}   ·   {fmt_date(r['transactionDate'])}"
                with st.expander(label):
                    st.markdown(mini_kpis([
                        ("Sens", f"{ico} {sens_lbl}"),
                        ("Actions", f"{int(r['change']):+,}"),
                        ("Prix", f"${r['transactionPrice']:,.2f}"),
                        ("Montant", f"${r['montant']:,.0f}"),
                        ("Détention après", f"{int(r['share']):,}"),
                        ("Date", fmt_date(r['transactionDate'])),
                    ]), unsafe_allow_html=True)


# ============================================================
# FOOTER
# ============================================================
st.markdown(
    """
    <div class="foot">
        <b>SENTINELLE</b><br>
        Données SEC Form 4 (Finnhub) · Congrès US (Bargo)<br>
        Outil informatif. Ne constitue pas un conseil en investissement.
    </div>
    """,
    unsafe_allow_html=True,
)
