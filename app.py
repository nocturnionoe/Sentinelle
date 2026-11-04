import streamlit as st
import requests
import pandas as pd
from concurrent.futures import ThreadPoolExecutor

# ================================================================
# CLÉ API FINNHUB
# ================================================================
try:
    API_KEY = st.secrets["FINNHUB_API_KEY"]
except Exception:
    API_KEY = "A_REMPLIR"
# ================================================================


WATCHLIST = {
    "AAPL":  "Apple",
    "MSFT":  "Microsoft",
    "GOOGL": "Alphabet",
    "AMZN":  "Amazon",
    "META":  "Meta",
    "TSLA":  "Tesla",
    "NVDA":  "NVIDIA",
    "JPM":   "JPMorgan Chase",
    "V":     "Visa",
    "WMT":   "Walmart",
    "JNJ":   "Johnson & Johnson",
    "XOM":   "Exxon Mobil",
    "BAC":   "Bank of America",
    "DIS":   "Walt Disney",
    "NFLX":  "Netflix",
    "KO":    "Coca-Cola",
    "PEP":   "PepsiCo",
    "ORCL":  "Oracle",
    "CRM":   "Salesforce",
    "AMD":   "AMD",
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
    .stApp {
        background: radial-gradient(ellipse at top, #0f1729 0%, #060912 60%);
        color: #e2e8f0;
    }
    [data-testid="stHeader"] { background: transparent; }
    .block-container { padding-top: 1.5rem; max-width: 1100px; }

    /* Header */
    .app-header {
        display: flex; align-items: center; justify-content: space-between;
        padding: 0.3rem 0 1.5rem 0;
        border-bottom: 1px solid rgba(255,255,255,0.06);
        margin-bottom: 1.5rem;
    }
    .brand { display: flex; align-items: center; gap: 0.9rem; }
    .logo {
        width: 42px; height: 42px; border-radius: 50%;
        background: linear-gradient(135deg, #1e3a8a, #0ea5e9);
        display: flex; align-items: center; justify-content: center;
        font-size: 1.3rem;
    }
    .brand-name {
        font-size: 1.4rem; font-weight: 700; letter-spacing: 4px; color: #f8fafc;
    }
    .brand-tag {
        font-size: 0.75rem; color: #64748b;
        text-transform: uppercase; letter-spacing: 2px;
    }

    /* Hero */
    .accueil-hero { padding: 1.5rem 0 2rem 0; }
    .accueil-titre {
        font-size: 2.2rem; font-weight: 800; color: #f8fafc;
        line-height: 1.15; letter-spacing: -1px; margin-bottom: 0.6rem;
    }
    .accueil-subtitre { font-size: 1rem; color: #94a3b8; max-width: 620px; }

    /* Onglets */
    [data-baseweb="tab-list"] {
        background: rgba(255,255,255,0.03);
        border-radius: 12px; padding: 0.3rem; gap: 0.2rem;
        border: 1px solid rgba(255,255,255,0.06);
    }
    [data-baseweb="tab"] {
        background: transparent !important;
        border-radius: 8px !important;
        color: #94a3b8 !important;
        font-weight: 600 !important;
        padding: 0.6rem 1.2rem !important;
    }
    [data-baseweb="tab"][aria-selected="true"] {
        background: linear-gradient(135deg, #2563eb, #0ea5e9) !important;
        color: white !important;
    }
    [data-baseweb="tab-highlight"], [data-baseweb="tab-border"] { display: none !important; }

    /* Titres section */
    .sec-eyebrow {
        font-size: 0.72rem; font-weight: 700; color: #0ea5e9;
        text-transform: uppercase; letter-spacing: 2.5px;
        margin: 2rem 0 0.3rem 0;
    }
    .sec-title {
        font-size: 1.5rem; font-weight: 700; color: #f8fafc; margin-bottom: 1.2rem;
    }

    /* KPI */
    .kpi-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(170px, 1fr));
        gap: 0.9rem;
        margin: 0.5rem 0 2rem 0;
    }
    .kpi-card {
        background: rgba(255,255,255,0.03);
        border: 1px solid rgba(255,255,255,0.08);
        border-radius: 14px;
        padding: 1.1rem 1.2rem;
    }
    .kpi-lbl {
        font-size: 0.7rem; color: #64748b; font-weight: 600;
        text-transform: uppercase; letter-spacing: 1.5px; margin-bottom: 0.5rem;
    }
    .kpi-val {
        font-size: 1.7rem; font-weight: 700; color: #f8fafc; line-height: 1.1;
    }
    .kpi-sub { font-size: 0.78rem; color: #64748b; margin-top: 0.3rem; }
    .vert { color: #10b981; }
    .rouge { color: #ef4444; }

    /* Expanders : stylés comme des cartes cliquables */
    [data-testid="stExpander"] {
        background: rgba(255,255,255,0.03) !important;
        border: 1px solid rgba(255,255,255,0.08) !important;
        border-radius: 14px !important;
        margin-bottom: 0.7rem !important;
        transition: all 0.15s;
        overflow: hidden;
    }
    [data-testid="stExpander"]:hover {
        border-color: rgba(14,165,233,0.35) !important;
        background: rgba(14,165,233,0.04) !important;
    }
    [data-testid="stExpander"] summary {
        padding: 1rem 1.3rem !important;
        font-size: 0.98rem !important;
        color: #f1f5f9 !important;
        font-weight: 500 !important;
    }
    [data-testid="stExpander"] summary:hover { color: #38bdf8 !important; }
    [data-testid="stExpander"] [data-testid="stExpanderDetails"] {
        padding: 0 1.3rem 1.2rem 1.3rem !important;
        border-top: 1px solid rgba(255,255,255,0.05);
    }

    /* Mini KPI dans un expander */
    .mini-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(110px, 1fr));
        gap: 0.5rem;
        margin: 1rem 0;
    }
    .mini-kpi {
        background: rgba(255,255,255,0.03);
        border-radius: 10px;
        padding: 0.7rem 0.9rem;
        border: 1px solid rgba(255,255,255,0.06);
    }
    .mini-lbl {
        font-size: 0.65rem; color: #64748b; font-weight: 600;
        text-transform: uppercase; letter-spacing: 1px;
    }
    .mini-val {
        font-size: 1.1rem; font-weight: 700; color: #f8fafc; margin-top: 0.2rem;
    }

    /* Input */
    .stTextInput input {
        background: rgba(255,255,255,0.05) !important;
        color: #f8fafc !important;
        border: 1px solid rgba(255,255,255,0.1) !important;
        border-radius: 10px !important;
        padding: 0.7rem 1rem !important;
        font-size: 1.05rem !important;
    }

    .stButton > button {
        background: linear-gradient(135deg, #2563eb, #0ea5e9);
        color: white !important;
        border: none !important;
        border-radius: 10px;
        font-weight: 600;
    }

    [data-testid="stDataFrame"] {
        background: rgba(255,255,255,0.02);
        border-radius: 12px;
        border: 1px solid rgba(255,255,255,0.08);
    }

    .footer-note {
        margin-top: 3rem; padding-top: 1.5rem;
        border-top: 1px solid rgba(255,255,255,0.06);
        text-align: center; font-size: 0.75rem; color: #475569;
    }

    #MainMenu, footer, header { visibility: hidden; }
    </style>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# API
# ============================================================
@st.cache_data(ttl=600, show_spinner=False)
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
    df["symbol"] = symbole
    return df.sort_values("transactionDate", ascending=False, na_position="last").reset_index(drop=True)


@st.cache_data(ttl=600, show_spinner="Chargement des données de marché...")
def recuperer_toute_watchlist(api_key: str) -> pd.DataFrame:
    with ThreadPoolExecutor(max_workers=8) as ex:
        resultats = list(ex.map(lambda t: recuperer_transactions(t, api_key), WATCHLIST.keys()))
    non_vides = [df for df in resultats if not df.empty]
    if not non_vides:
        return pd.DataFrame()
    agg = pd.concat(non_vides, ignore_index=True)
    agg["entreprise"] = agg["symbol"].map(WATCHLIST)
    return agg


# ============================================================
# HELPERS
# ============================================================
def format_nombre(n: float) -> str:
    if abs(n) >= 1_000_000_000:
        return f"{n/1_000_000_000:.2f}Md"
    if abs(n) >= 1_000_000:
        return f"{n/1_000_000:.2f}M"
    if abs(n) >= 1_000:
        return f"{n/1_000:.1f}k"
    return f"{n:.0f}"


def date_fr(d) -> str:
    return d.strftime("%d %b %Y") if pd.notna(d) else "—"


def bloc_mini_kpi(items):
    """items = [(label, value), ...]"""
    html = '<div class="mini-grid">'
    for lbl, val in items:
        html += f'<div class="mini-kpi"><div class="mini-lbl">{lbl}</div><div class="mini-val">{val}</div></div>'
    html += '</div>'
    st.markdown(html, unsafe_allow_html=True)


def details_transaction(row):
    """Panneau de détails pour UNE transaction (dans un expander)."""
    sens = "Achat" if row["change"] > 0 else "Vente"
    couleur = "🟢" if row["change"] > 0 else "🔴"
    bloc_mini_kpi([
        ("Sens", f"{couleur} {sens}"),
        ("Actions", f"{int(row['change']):+,}"),
        ("Prix unitaire", f"${row['transactionPrice']:,.2f}"),
        ("Montant", f"${row['montant']:,.0f}"),
        ("Détention après op.", f"{int(row['share']):,}"),
        ("Date", date_fr(row["transactionDate"])),
    ])
    nom_ent = WATCHLIST.get(row["symbol"], row["symbol"])
    st.caption(f"📄 Déclaration officielle SEC (Form 4) · {row['name']} · {nom_ent} ({row['symbol']})")


def details_insider(nom: str, df_all: pd.DataFrame):
    """Panneau de détails pour UN insider : toutes ses transactions."""
    sous = df_all[df_all["name"] == nom].copy()
    volume = sous["montant"].sum()
    nb_tx = len(sous)
    achats = (sous["change"] > 0).sum()
    ventes = (sous["change"] < 0).sum()
    entreprises = ", ".join(sorted(set(sous["symbol"])))
    net = int(sous["change"].sum())

    bloc_mini_kpi([
        ("Volume total", f"${format_nombre(volume)}"),
        ("Transactions", f"{nb_tx}"),
        ("Achats", f"🟢 {achats}"),
        ("Ventes", f"🔴 {ventes}"),
        ("Flux net", f"{net:+,}"),
        ("Entreprises", entreprises),
    ])

    tab = pd.DataFrame({
        "Ticker": sous["symbol"],
        "Sens": sous["change"].apply(lambda x: "▲ Achat" if x > 0 else "▼ Vente"),
        "Actions": sous["change"].astype(int).apply(lambda x: f"{x:+,}"),
        "Prix": sous["transactionPrice"].apply(lambda x: f"${x:,.2f}"),
        "Montant": sous["montant"].apply(lambda x: f"${x:,.0f}"),
        "Date": sous["transactionDate"].dt.strftime("%d %b %Y"),
    })
    st.dataframe(tab, use_container_width=True, hide_index=True, height=min(300, 50 + 36 * len(tab)))


def details_entreprise(symbole: str, df_all: pd.DataFrame):
    """Panneau de détails pour UNE entreprise."""
    sous = df_all[df_all["symbol"] == symbole].copy()
    volume = sous["montant"].sum()
    nb_tx = len(sous)
    nb_insiders = sous["name"].nunique()
    achats = (sous["change"] > 0).sum()
    ventes = (sous["change"] < 0).sum()
    net = int(sous["change"].sum())

    bloc_mini_kpi([
        ("Volume cumulé", f"${format_nombre(volume)}"),
        ("Transactions", f"{nb_tx}"),
        ("Dirigeants", f"{nb_insiders}"),
        ("Achats", f"🟢 {achats}"),
        ("Ventes", f"🔴 {ventes}"),
        ("Flux net", f"{net:+,}"),
    ])

    st.markdown("**Dirigeants impliqués**")
    top_in = (
        sous.groupby("name")
            .agg(nb=("name", "size"), vol=("montant", "sum"))
            .sort_values("vol", ascending=False)
            .head(10)
    )
    tab_in = pd.DataFrame({
        "Dirigeant": top_in.index,
        "Transactions": top_in["nb"].values,
        "Volume": [f"${format_nombre(v)}" for v in top_in["vol"].values],
    })
    st.dataframe(tab_in, use_container_width=True, hide_index=True, height=min(300, 50 + 36 * len(tab_in)))

    st.markdown("**Historique complet**")
    tab = pd.DataFrame({
        "Dirigeant": sous["name"],
        "Sens": sous["change"].apply(lambda x: "▲ Achat" if x > 0 else "▼ Vente"),
        "Actions": sous["change"].astype(int).apply(lambda x: f"{x:+,}"),
        "Prix": sous["transactionPrice"].apply(lambda x: f"${x:,.2f}"),
        "Montant": sous["montant"].apply(lambda x: f"${x:,.0f}"),
        "Date": sous["transactionDate"].dt.strftime("%d %b %Y"),
    })
    st.dataframe(tab, use_container_width=True, hide_index=True, height=min(400, 50 + 36 * len(tab)))


# ============================================================
# HEADER
# ============================================================
st.markdown(
    """
    <div class="app-header">
        <div class="brand">
            <div class="logo">🛡️</div>
            <div>
                <div class="brand-name">SENTINELLE</div>
                <div class="brand-tag">INSIDER TRACKER</div>
            </div>
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
tab_accueil, tab_insiders, tab_tickers, tab_recherche = st.tabs(
    ["🏠 Accueil", "👥 Insiders", "🏢 Entreprises", "🔍 Recherche"]
)


# ============================================================
# ACCUEIL
# ============================================================
with tab_accueil:
    st.markdown(
        """
        <div class="accueil-hero">
            <div class="accueil-titre">Les mouvements qui comptent,<br>avant tout le monde.</div>
            <div class="accueil-subtitre">Suivez les transactions des dirigeants des plus grandes entreprises cotées — cliquez sur chaque ligne pour les détails.</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    df_all = recuperer_toute_watchlist(API_KEY)

    if df_all.empty:
        st.warning("Aucune donnée disponible pour le moment.")
    else:
        total_tx = len(df_all)
        volume_global = df_all["montant"].sum()
        nb_insiders_uniques = df_all["name"].nunique()
        nb_entreprises = df_all["symbol"].nunique()
        achats_g = (df_all["change"] > 0).sum()
        ventes_g = (df_all["change"] < 0).sum()
        ratio = (achats_g / max(ventes_g, 1))

        st.markdown(
            f"""
            <div class="kpi-grid">
                <div class="kpi-card">
                    <div class="kpi-lbl">Transactions suivies</div>
                    <div class="kpi-val">{total_tx:,}</div>
                    <div class="kpi-sub">sur {nb_entreprises} entreprises</div>
                </div>
                <div class="kpi-card">
                    <div class="kpi-lbl">Volume échangé</div>
                    <div class="kpi-val">${format_nombre(volume_global)}</div>
                    <div class="kpi-sub">cumul watchlist</div>
                </div>
                <div class="kpi-card">
                    <div class="kpi-lbl">Dirigeants actifs</div>
                    <div class="kpi-val">{nb_insiders_uniques}</div>
                    <div class="kpi-sub">tous tickers</div>
                </div>
                <div class="kpi-card">
                    <div class="kpi-lbl">Ratio Achats/Ventes</div>
                    <div class="kpi-val">{ratio:.2f}</div>
                    <div class="kpi-sub"><span class="vert">▲ {achats_g}</span> · <span class="rouge">▼ {ventes_g}</span></div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # --- Gros mouvements récents ---
        st.markdown('<div class="sec-eyebrow">— À la une</div>', unsafe_allow_html=True)
        st.markdown('<div class="sec-title">🔥 Gros mouvements récents</div>', unsafe_allow_html=True)

        gros = df_all.sort_values("montant", ascending=False).head(10).reset_index(drop=True)
        for i, row in gros.iterrows():
            flag = "🟢 ACHAT" if row["change"] > 0 else "🔴 VENTE"
            label = f"{flag}  ·  {row['name']}  ·  {row['symbol']}  ·  ${format_nombre(row['montant'])}  ·  {date_fr(row['transactionDate'])}"
            with st.expander(label):
                details_transaction(row)

        # --- Dernières déclarations ---
        st.markdown('<div class="sec-eyebrow">— Flux en direct</div>', unsafe_allow_html=True)
        st.markdown('<div class="sec-title">⏱️ Dernières déclarations</div>', unsafe_allow_html=True)

        recents = df_all.dropna(subset=["transactionDate"]).sort_values("transactionDate", ascending=False).head(10).reset_index(drop=True)
        for i, row in recents.iterrows():
            flag = "🟢" if row["change"] > 0 else "🔴"
            label = f"{flag}  {date_fr(row['transactionDate'])}  ·  {row['name']}  ·  {row['symbol']}  ·  ${format_nombre(row['montant'])}"
            with st.expander(label):
                details_transaction(row)


# ============================================================
# INSIDERS
# ============================================================
with tab_insiders:
    st.markdown(
        """
        <div class="accueil-hero">
            <div class="accueil-titre">Les grands noms.</div>
            <div class="accueil-subtitre">Cliquez sur un dirigeant pour voir le détail de toutes ses opérations.</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    df_all = recuperer_toute_watchlist(API_KEY)

    if df_all.empty:
        st.warning("Aucune donnée disponible.")
    else:
        top_insiders = (
            df_all.groupby("name")
                  .agg(
                      nb_tx=("name", "size"),
                      volume=("montant", "sum"),
                      entreprises=("symbol", lambda s: ", ".join(sorted(set(s)))),
                  )
                  .sort_values("volume", ascending=False)
                  .head(25)
                  .reset_index()
        )

        for _, row in top_insiders.iterrows():
            label = f"👤  {row['name']}  ·  {row['entreprises']}  ·  ${format_nombre(row['volume'])}  ·  {row['nb_tx']} tx"
            with st.expander(label):
                details_insider(row["name"], df_all)


# ============================================================
# ENTREPRISES
# ============================================================
with tab_tickers:
    st.markdown(
        """
        <div class="accueil-hero">
            <div class="accueil-titre">Watchlist.</div>
            <div class="accueil-subtitre">Cliquez sur une entreprise pour voir son activité insider détaillée.</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    df_all = recuperer_toute_watchlist(API_KEY)

    if df_all.empty:
        st.warning("Aucune donnée disponible.")
    else:
        par_entreprise = (
            df_all.groupby("symbol")
                  .agg(
                      nb_tx=("symbol", "size"),
                      volume=("montant", "sum"),
                      nb_insiders=("name", "nunique"),
                  )
                  .sort_values("volume", ascending=False)
                  .reset_index()
        )

        for _, row in par_entreprise.iterrows():
            nom = WATCHLIST.get(row["symbol"], row["symbol"])
            label = f"🏢  {row['symbol']}  ·  {nom}  ·  ${format_nombre(row['volume'])}  ·  {row['nb_insiders']} dirigeants  ·  {row['nb_tx']} tx"
            with st.expander(label):
                details_entreprise(row["symbol"], df_all)


# ============================================================
# RECHERCHE
# ============================================================
with tab_recherche:
    st.markdown(
        """
        <div class="accueil-hero">
            <div class="accueil-titre">Analyse d'un ticker.</div>
            <div class="accueil-subtitre">Saisissez un symbole boursier (pas forcément dans la watchlist) pour voir toute son activité insider.</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    col_input, col_bouton = st.columns([4, 1])
    with col_input:
        ticker_saisi = st.text_input(
            "Ticker",
            value="AAPL",
            max_chars=10,
            placeholder="AAPL, MSFT, TSLA...",
            label_visibility="collapsed",
        )
    with col_bouton:
        if st.button("🔄 Actualiser", use_container_width=True):
            st.cache_data.clear()
            st.rerun()

    ticker = ticker_saisi.strip().upper()
    if not ticker:
        st.info("Saisissez un ticker pour afficher l'analyse.")
        st.stop()

    df = recuperer_transactions(ticker, API_KEY)
    if df.empty:
        st.warning(f"Aucune transaction trouvée pour **{ticker}**.")
        st.stop()

    nb_tx = len(df)
    nb_in = df["name"].nunique()
    vol = df["montant"].sum()
    net = int(df["change"].sum())
    achats_t = (df["change"] > 0).sum()
    ventes_t = (df["change"] < 0).sum()
    derniere = df["transactionDate"].max()
    derniere_str = date_fr(derniere)
    sens_cls = "vert" if net >= 0 else "rouge"
    sens_signe = "+" if net >= 0 else ""

    st.markdown(
        f"""
        <div class="kpi-grid">
            <div class="kpi-card">
                <div class="kpi-lbl">Transactions</div>
                <div class="kpi-val">{nb_tx}</div>
                <div class="kpi-sub"><span class="vert">▲ {achats_t}</span> · <span class="rouge">▼ {ventes_t}</span></div>
            </div>
            <div class="kpi-card">
                <div class="kpi-lbl">Dirigeants</div>
                <div class="kpi-val">{nb_in}</div>
                <div class="kpi-sub">impliqués</div>
            </div>
            <div class="kpi-card">
                <div class="kpi-lbl">Volume</div>
                <div class="kpi-val">${format_nombre(vol)}</div>
                <div class="kpi-sub">cumul</div>
            </div>
            <div class="kpi-card">
                <div class="kpi-lbl">Flux net</div>
                <div class="kpi-val {sens_cls}">{sens_signe}{format_nombre(net)}</div>
                <div class="kpi-sub">actions</div>
            </div>
            <div class="kpi-card">
                <div class="kpi-lbl">Dernière</div>
                <div class="kpi-val" style="font-size:1.3rem;">{derniere_str}</div>
                <div class="kpi-sub">déclaration</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown('<div class="sec-eyebrow">— Transactions</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="sec-title">Cliquez sur une opération pour les détails</div>', unsafe_allow_html=True)

    for _, row in df.iterrows():
        flag = "🟢 ACHAT" if row["change"] > 0 else "🔴 VENTE"
        label = f"{flag}  ·  {row['name']}  ·  ${format_nombre(row['montant'])}  ·  {date_fr(row['transactionDate'])}"
        with st.expander(label):
            details_transaction(row)


# ============================================================
# FOOTER
# ============================================================
st.markdown(
    """
    <div class="footer-note">
        Données officielles SEC · fournies par Finnhub<br>
        Sentinelle est un outil informatif et ne constitue pas un conseil en investissement.
    </div>
    """,
    unsafe_allow_html=True,
)
