import streamlit as st
import requests
import pandas as pd

# ================================================================
# CLÉ API FINNHUB
# En ligne (Streamlit Cloud) : la clé est dans les Secrets.
# En local : remplacer "A_REMPLIR" ci-dessous par votre clé.
# ================================================================
try:
    API_KEY = st.secrets["FINNHUB_API_KEY"]
except Exception:
    API_KEY = "A_REMPLIR"
# ================================================================


st.set_page_config(
    page_title="Sentinelle",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ============================================================
# STYLE — thème sombre inspiré de sentinelleapp.tech
# ============================================================
st.markdown(
    """
    <style>
    /* Fond général */
    .stApp {
        background: radial-gradient(ellipse at top, #0f1729 0%, #060912 100%);
        color: #e2e8f0;
    }
    [data-testid="stHeader"] { background: transparent; }
    [data-testid="stSidebar"] {
        background: #0a1020;
        border-right: 1px solid rgba(255,255,255,0.05);
    }
    [data-testid="stSidebar"] * { color: #cbd5e1 !important; }

    /* Header Sentinelle */
    .sentinelle-header {
        display: flex;
        align-items: center;
        gap: 0.9rem;
        padding: 0.5rem 0 1.8rem 0;
        border-bottom: 1px solid rgba(255,255,255,0.06);
        margin-bottom: 2rem;
    }
    .sentinelle-logo {
        width: 44px; height: 44px;
        border-radius: 50%;
        background: linear-gradient(135deg, #1e3a8a, #0ea5e9);
        display: flex; align-items: center; justify-content: center;
        font-size: 1.4rem;
    }
    .sentinelle-brand {
        font-size: 1.5rem;
        font-weight: 700;
        letter-spacing: 4px;
        color: #f8fafc;
    }

    /* Hero */
    .hero-ticker {
        font-size: 3.5rem;
        font-weight: 800;
        color: #f8fafc;
        margin: 0.5rem 0 0.2rem 0;
        letter-spacing: -1px;
    }
    .hero-nom {
        font-size: 1.2rem;
        color: #64748b;
        margin-bottom: 2rem;
    }

    /* Cartes KPI */
    .kpi-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
        gap: 1rem;
        margin-bottom: 2.5rem;
    }
    .kpi-card {
        background: rgba(255,255,255,0.03);
        border: 1px solid rgba(255,255,255,0.08);
        border-radius: 14px;
        padding: 1.3rem 1.4rem;
        transition: all 0.2s;
    }
    .kpi-card:hover {
        border-color: rgba(14,165,233,0.4);
        background: rgba(14,165,233,0.05);
    }
    .kpi-label {
        font-size: 0.75rem;
        color: #64748b;
        text-transform: uppercase;
        letter-spacing: 1.5px;
        margin-bottom: 0.6rem;
        font-weight: 600;
    }
    .kpi-value {
        font-size: 1.9rem;
        font-weight: 700;
        color: #f8fafc;
        line-height: 1.1;
    }
    .kpi-sub {
        font-size: 0.85rem;
        margin-top: 0.4rem;
    }
    .vert { color: #10b981; }
    .rouge { color: #ef4444; }

    /* Titres de section */
    .section-titre {
        font-size: 0.8rem;
        font-weight: 700;
        color: #0ea5e9;
        text-transform: uppercase;
        letter-spacing: 2px;
        margin: 2rem 0 1rem 0;
    }
    .section-sous-titre {
        font-size: 1.6rem;
        font-weight: 700;
        color: #f8fafc;
        margin-bottom: 1.3rem;
    }

    /* Cartes dirigeants */
    .dirigeant-card {
        background: rgba(255,255,255,0.03);
        border: 1px solid rgba(255,255,255,0.08);
        border-radius: 14px;
        padding: 1.1rem 1.2rem;
        margin-bottom: 0.8rem;
        display: flex;
        align-items: center;
        gap: 1rem;
    }
    .avatar {
        width: 46px; height: 46px;
        border-radius: 50%;
        background: linear-gradient(135deg, #334155, #0f172a);
        display: flex; align-items: center; justify-content: center;
        font-weight: 700; color: #f8fafc; font-size: 1rem;
        flex-shrink: 0;
    }
    .dirigeant-info { flex: 1; min-width: 0; }
    .dirigeant-nom {
        font-weight: 600; color: #f1f5f9;
        font-size: 1.02rem;
        overflow: hidden; text-overflow: ellipsis; white-space: nowrap;
    }
    .dirigeant-date { font-size: 0.8rem; color: #64748b; margin-top: 0.15rem; }
    .dirigeant-actions {
        text-align: right;
        flex-shrink: 0;
    }
    .dirigeant-actions .nb {
        font-size: 1.1rem; font-weight: 700; color: #f8fafc;
    }
    .dirigeant-actions .lbl {
        font-size: 0.72rem; color: #64748b; text-transform: uppercase; letter-spacing: 1px;
    }

    /* Tableau Streamlit */
    [data-testid="stDataFrame"] {
        background: rgba(255,255,255,0.02);
        border-radius: 14px;
        border: 1px solid rgba(255,255,255,0.08);
        padding: 0.5rem;
    }

    /* Bouton */
    .stButton > button {
        background: linear-gradient(135deg, #2563eb, #0ea5e9);
        color: white !important;
        border: none !important;
        border-radius: 10px;
        font-weight: 600;
        padding: 0.6rem 1.2rem;
    }
    .stButton > button:hover {
        background: linear-gradient(135deg, #1d4ed8, #0284c7);
        transform: translateY(-1px);
    }

    /* Input sidebar */
    .stTextInput input {
        background: rgba(255,255,255,0.05) !important;
        color: #f8fafc !important;
        border: 1px solid rgba(255,255,255,0.1) !important;
        border-radius: 8px !important;
    }

    /* Footer */
    .footer-note {
        margin-top: 3rem;
        padding-top: 1.5rem;
        border-top: 1px solid rgba(255,255,255,0.06);
        text-align: center;
        font-size: 0.78rem;
        color: #475569;
    }

    /* Masque footer Streamlit */
    #MainMenu, footer, header { visibility: hidden; }
    </style>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# HEADER
# ============================================================
st.markdown(
    """
    <div class="sentinelle-header">
        <div class="sentinelle-logo">🛡️</div>
        <div class="sentinelle-brand">SENTINELLE</div>
    </div>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# SIDEBAR
# ============================================================
with st.sidebar:
    st.markdown("### 🔍 Recherche")
    ticker_saisi = st.text_input(
        "Ticker à analyser",
        value="AAPL",
        max_chars=10,
        help="Exemple : AAPL, MSFT, TSLA, NVDA...",
    )
    ticker = ticker_saisi.strip().upper()

    st.markdown("---")
    if st.button("🔄 Rafraîchir", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

    st.markdown("---")
    st.caption("Données officielles Finnhub (SEC Form 4).")
    st.caption("Sentinelle ne fournit aucun conseil en investissement.")


# ============================================================
# FONCTIONS DE RÉCUPÉRATION
# ============================================================
@st.cache_data(ttl=300, show_spinner=False)
def recuperer_profil(symbole: str, api_key: str) -> dict:
    try:
        r = requests.get(
            "https://finnhub.io/api/v1/stock/profile2",
            params={"symbol": symbole, "token": api_key},
            timeout=10,
        )
        r.raise_for_status()
        return r.json() or {}
    except requests.RequestException:
        return {}


@st.cache_data(ttl=300, show_spinner=False)
def recuperer_transactions(symbole: str, api_key: str) -> pd.DataFrame:
    try:
        r = requests.get(
            "https://finnhub.io/api/v1/stock/insider-transactions",
            params={"symbol": symbole, "token": api_key},
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
    df["transactionPrice"] = pd.to_numeric(df.get("transactionPrice"), errors="coerce").fillna(0)
    df["change"] = pd.to_numeric(df.get("change"), errors="coerce").fillna(0)
    df["share"] = pd.to_numeric(df.get("share"), errors="coerce").fillna(0)
    df["montant"] = df["change"].abs() * df["transactionPrice"]
    return df.sort_values("transactionDate", ascending=False, na_position="last").reset_index(drop=True)


def initiales(nom: str) -> str:
    """Retourne les initiales d'un nom (ex: 'Tim Cook' -> 'TC')."""
    parties = [p for p in nom.replace(",", " ").split() if p]
    if not parties:
        return "?"
    if len(parties) == 1:
        return parties[0][:2].upper()
    return (parties[0][0] + parties[-1][0]).upper()


def format_nombre(n: float) -> str:
    """Formate un grand nombre : 1_200_000 -> '1,2M'."""
    if abs(n) >= 1_000_000_000:
        return f"{n/1_000_000_000:.2f}Md"
    if abs(n) >= 1_000_000:
        return f"{n/1_000_000:.2f}M"
    if abs(n) >= 1_000:
        return f"{n/1_000:.1f}k"
    return f"{n:.0f}"


# ============================================================
# GARDES
# ============================================================
if API_KEY == "A_REMPLIR":
    st.error("⚠️ Clé API Finnhub manquante. Ajoutez `FINNHUB_API_KEY` dans les Secrets de Streamlit Cloud.")
    st.stop()

if not ticker:
    st.info("👈 Saisissez un ticker dans la barre latérale pour commencer.")
    st.stop()


# ============================================================
# CHARGEMENT
# ============================================================
with st.spinner(""):
    profil = recuperer_profil(ticker, API_KEY)
    df = recuperer_transactions(ticker, API_KEY)

nom_entreprise = profil.get("name") or ticker


# ============================================================
# HERO : Ticker + Nom
# ============================================================
st.markdown(
    f"""
    <div class="hero-ticker">{ticker}</div>
    <div class="hero-nom">{nom_entreprise}</div>
    """,
    unsafe_allow_html=True,
)


if df.empty:
    st.warning(f"Aucune transaction d'initié trouvée pour **{ticker}**.")
    st.stop()


# ============================================================
# KPI CARDS
# ============================================================
nb_transactions = len(df)
nb_inities = df["name"].nunique()
achats = df[df["change"] > 0]
ventes = df[df["change"] < 0]
volume_total = df["montant"].sum()
net_actions = int(df["change"].sum())
derniere_date = df["transactionDate"].max()
derniere_date_str = derniere_date.strftime("%d %b %Y") if pd.notna(derniere_date) else "N/A"

sens_classe = "vert" if net_actions >= 0 else "rouge"
sens_signe = "+" if net_actions >= 0 else ""

st.markdown(
    f"""
    <div class="kpi-grid">
        <div class="kpi-card">
            <div class="kpi-label">Transactions</div>
            <div class="kpi-value">{nb_transactions}</div>
            <div class="kpi-sub"><span class="vert">▲ {len(achats)} achats</span> · <span class="rouge">▼ {len(ventes)} ventes</span></div>
        </div>
        <div class="kpi-card">
            <div class="kpi-label">Dirigeants actifs</div>
            <div class="kpi-value">{nb_inities}</div>
            <div class="kpi-sub">impliqués</div>
        </div>
        <div class="kpi-card">
            <div class="kpi-label">Volume total</div>
            <div class="kpi-value">${format_nombre(volume_total)}</div>
            <div class="kpi-sub">échangé</div>
        </div>
        <div class="kpi-card">
            <div class="kpi-label">Flux net</div>
            <div class="kpi-value {sens_classe}">{sens_signe}{format_nombre(net_actions)}</div>
            <div class="kpi-sub">actions</div>
        </div>
        <div class="kpi-card">
            <div class="kpi-label">Dernière déclaration</div>
            <div class="kpi-value" style="font-size:1.4rem;">{derniere_date_str}</div>
            <div class="kpi-sub">source : SEC</div>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# SECTION : PORTEFEUILLE DES DIRIGEANTS
# ============================================================
st.markdown('<div class="section-titre">— Portefeuille actuel</div>', unsafe_allow_html=True)
st.markdown('<div class="section-sous-titre">Détention par dirigeant</div>', unsafe_allow_html=True)

portefeuille = (
    df.sort_values("transactionDate", ascending=False)
      .drop_duplicates(subset=["name"], keep="first")
      .sort_values("share", ascending=False)
      .head(10)
)

for _, row in portefeuille.iterrows():
    nom = row["name"]
    actions = int(row["share"])
    date_str = row["transactionDate"].strftime("%d %b %Y") if pd.notna(row["transactionDate"]) else "—"
    st.markdown(
        f"""
        <div class="dirigeant-card">
            <div class="avatar">{initiales(nom)}</div>
            <div class="dirigeant-info">
                <div class="dirigeant-nom">{nom}</div>
                <div class="dirigeant-date">Mis à jour · {date_str}</div>
            </div>
            <div class="dirigeant-actions">
                <div class="nb">{actions:,}</div>
                <div class="lbl">actions</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# ============================================================
# SECTION : HISTORIQUE DES TRANSACTIONS
# ============================================================
st.markdown('<div class="section-titre">— Historique</div>', unsafe_allow_html=True)
st.markdown('<div class="section-sous-titre">Transactions déclarées</div>', unsafe_allow_html=True)

historique = pd.DataFrame({
    "Dirigeant": df["name"],
    "Sens": df["change"].apply(lambda x: "▲ Achat" if x > 0 else "▼ Vente"),
    "Actions": df["change"].astype(int).apply(lambda x: f"{x:+,}"),
    "Prix": df["transactionPrice"].apply(lambda x: f"${x:,.2f}"),
    "Montant": df["montant"].apply(lambda x: f"${x:,.0f}"),
    "Date": df["transactionDate"].dt.strftime("%d %b %Y"),
})

st.dataframe(historique, use_container_width=True, hide_index=True, height=420)


# ============================================================
# FOOTER
# ============================================================
st.markdown(
    """
    <div class="footer-note">
        Données issues de Finnhub · SEC Form 4<br>
        Sentinelle ne fournit pas de conseil en investissement. Investir comporte un risque de perte en capital.
    </div>
    """,
    unsafe_allow_html=True,
)
