import streamlit as st
import requests
import pandas as pd

# ================================================================
# CLÉ API FINNHUB
# En ligne (Streamlit Cloud) : la clé est stockée dans les Secrets.
# En local : vous pouvez la mettre en dur ci-dessous à la place de "A_REMPLIR".
# ================================================================
try:
    import streamlit as _st_boot
    API_KEY = _st_boot.secrets["FINNHUB_API_KEY"]
except Exception:
    API_KEY = "A_REMPLIR"
# ================================================================


# --- Configuration de la page Streamlit ---
st.set_page_config(
    page_title="Sentinelle — Transactions d'initiés",
    page_icon="🕵️",
    layout="wide",
)


# --- Style global ---
st.markdown(
    """
    <style>
    .titre-sentinelle {
        font-size: 3.2rem;
        font-weight: 800;
        background: linear-gradient(90deg, #1e3a8a, #06b6d4, #10b981);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
        padding: 1rem 0 0.2rem 0;
        letter-spacing: 2px;
    }
    .sous-titre {
        text-align: center;
        color: #64748b;
        font-size: 1.15rem;
        margin-bottom: 1.5rem;
    }
    .titre-section {
        font-size: 1.5rem;
        font-weight: 700;
        color: #1e3a8a;
        border-left: 4px solid #06b6d4;
        padding-left: 0.8rem;
        margin: 1.5rem 0 1rem 0;
    }
    </style>
    <div class="titre-sentinelle">🕵️ SENTINELLE</div>
    <div class="sous-titre">Analyse Premium des transactions d'initiés boursiers</div>
    """,
    unsafe_allow_html=True,
)


# --- Sidebar : saisie du ticker ---
with st.sidebar:
    st.markdown("### ⚙️ Paramètres d'analyse")
    ticker_saisi = st.text_input(
        "Ticker à analyser",
        value="AAPL",
        max_chars=10,
        help="Exemple : AAPL, MSFT, TSLA, NVDA...",
    )
    ticker = ticker_saisi.strip().upper()

    st.markdown("---")
    rafraichir = st.button("🔄 Rafraîchir les données", use_container_width=True, type="primary")
    if rafraichir:
        st.cache_data.clear()

    st.markdown("---")
    st.caption("Source : [Finnhub.io](https://finnhub.io)")


@st.cache_data(ttl=300, show_spinner=False)
def recuperer_profil(symbole: str, api_key: str) -> dict:
    """Récupère le profil de l'entreprise (nom, logo, etc.)."""
    url = "https://finnhub.io/api/v1/stock/profile2"
    params = {"symbol": symbole, "token": api_key}
    try:
        r = requests.get(url, params=params, timeout=10)
        r.raise_for_status()
        return r.json() or {}
    except requests.RequestException:
        return {}


@st.cache_data(ttl=300, show_spinner=False)
def recuperer_transactions(symbole: str, api_key: str) -> pd.DataFrame:
    """Récupère les transactions d'initiés pour le ticker donné."""
    url = "https://finnhub.io/api/v1/stock/insider-transactions"
    params = {"symbol": symbole, "token": api_key}
    try:
        r = requests.get(url, params=params, timeout=10)
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
    df = df.sort_values("transactionDate", ascending=False, na_position="last").reset_index(drop=True)
    return df


# --- Vérification de la clé API ---
if API_KEY == "A_REMPLIR":
    st.error("⚠️ Veuillez renseigner votre clé API Finnhub dans la variable `API_KEY` en haut du fichier.")
    st.info("Créez un compte gratuit sur [finnhub.io](https://finnhub.io) pour obtenir votre clé.")
    st.stop()

if not ticker:
    st.info("👈 Saisissez un ticker dans la barre latérale pour commencer.")
    st.stop()


# --- Chargement des données ---
with st.spinner(f"Chargement des données pour {ticker}..."):
    profil = recuperer_profil(ticker, API_KEY)
    df = recuperer_transactions(ticker, API_KEY)

nom_entreprise = profil.get("name") or ticker
logo = profil.get("logo")

# --- En-tête entreprise ---
col_logo, col_nom = st.columns([1, 8])
with col_logo:
    if logo:
        st.image(logo, width=70)
with col_nom:
    st.markdown(f"## {nom_entreprise}  &nbsp; `{ticker}`")
    if profil.get("finnhubIndustry"):
        st.caption(f"Secteur : {profil['finnhubIndustry']}  ·  {profil.get('exchange', '')}")


if df.empty:
    st.warning(f"Aucune transaction d'initié trouvée pour **{ticker}**. Vérifiez le symbole ou réessayez plus tard.")
    st.stop()


# --- SECTION METRICS ---
st.markdown('<div class="titre-section">📊 Résumé de l\'activité</div>', unsafe_allow_html=True)

nb_transactions = len(df)
nb_inities = df["name"].nunique()
achats = df[df["change"] > 0]
ventes = df[df["change"] < 0]
volume_total = df["montant"].sum()
net_actions = int(df["change"].sum())
derniere_date = df["transactionDate"].max()
derniere_date_str = derniere_date.strftime("%Y-%m-%d") if pd.notna(derniere_date) else "N/A"

m1, m2, m3, m4, m5 = st.columns(5)
m1.metric("Transactions", f"{nb_transactions}")
m2.metric("Dirigeants actifs", f"{nb_inities}")
m3.metric(
    "Achats / Ventes",
    f"{len(achats)} / {len(ventes)}",
    delta=f"Net : {net_actions:+,} actions",
)
m4.metric("Volume total", f"${volume_total:,.0f}")
m5.metric("Dernière opération", derniere_date_str)


# --- SECTION PORTEFEUILLE ---
st.markdown('<div class="titre-section">💼 Portefeuille actuel des dirigeants</div>', unsafe_allow_html=True)
st.caption("Détention actuelle d'actions après la dernière transaction enregistrée pour chaque dirigeant.")

# Dernière transaction par dirigeant -> détention actuelle (champ 'share')
portefeuille = (
    df.sort_values("transactionDate", ascending=False)
      .drop_duplicates(subset=["name"], keep="first")
      .loc[:, ["name", "share", "change", "transactionDate"]]
      .rename(columns={
          "name": "Dirigeant",
          "share": "Actions détenues",
          "change": "Dernière variation",
          "transactionDate": "Date de mise à jour",
      })
)
portefeuille = portefeuille.sort_values("Actions détenues", ascending=False).reset_index(drop=True)
portefeuille["Date de mise à jour"] = portefeuille["Date de mise à jour"].dt.strftime("%Y-%m-%d")

st.dataframe(
    portefeuille,
    use_container_width=True,
    hide_index=True,
    column_config={
        "Actions détenues": st.column_config.NumberColumn(format="%d"),
        "Dernière variation": st.column_config.NumberColumn(format="%+d"),
    },
)


# --- SECTION HISTORIQUE ---
st.markdown('<div class="titre-section">📜 Historique des transactions</div>', unsafe_allow_html=True)

historique = pd.DataFrame({
    "Nom du dirigeant": df["name"],
    "Entreprise": nom_entreprise,
    "Ticker": ticker,
    "Variation (actions)": df["change"].astype(int),
    "Prix unitaire": df["transactionPrice"].apply(lambda x: f"${x:,.2f}"),
    "Montant": df["montant"].apply(lambda x: f"${x:,.2f}"),
    "Date": df["transactionDate"].dt.strftime("%Y-%m-%d"),
})

st.dataframe(historique, use_container_width=True, hide_index=True)
