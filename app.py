import streamlit as st
import requests
import pandas as pd
from concurrent.futures import ThreadPoolExecutor

# ================================================================
# CLÉ API FINNHUB
# En ligne (Streamlit Cloud) : la clé est dans les Secrets.
# ================================================================
try:
    API_KEY = st.secrets["FINNHUB_API_KEY"]
except Exception:
    API_KEY = "A_REMPLIR"
# ================================================================


# ============================================================
# WATCHLIST : les grandes capitalisations qu'on suit
# ============================================================
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
    .brand {
        display: flex; align-items: center; gap: 0.9rem;
    }
    .logo {
        width: 42px; height: 42px; border-radius: 50%;
        background: linear-gradient(135deg, #1e3a8a, #0ea5e9);
        display: flex; align-items: center; justify-content: center;
        font-size: 1.3rem;
    }
    .brand-name {
        font-size: 1.4rem; font-weight: 700; letter-spacing: 4px;
        color: #f8fafc;
    }
    .brand-tag {
        font-size: 0.75rem; color: #64748b;
        text-transform: uppercase; letter-spacing: 2px;
    }

    /* Hero accueil */
    .accueil-hero {
        padding: 2rem 0 2.5rem 0;
    }
    .accueil-titre {
        font-size: 2.4rem; font-weight: 800; color: #f8fafc;
        line-height: 1.15; letter-spacing: -1px;
        margin-bottom: 0.6rem;
    }
    .accueil-subtitre {
        font-size: 1.05rem; color: #94a3b8;
        max-width: 600px;
    }

    /* Onglets Streamlit */
    [data-baseweb="tab-list"] {
        background: rgba(255,255,255,0.03);
        border-radius: 12px;
        padding: 0.3rem;
        gap: 0.2rem;
        border: 1px solid rgba(255,255,255,0.06);
    }
    [data-baseweb="tab"] {
        background: transparent !important;
        border-radius: 8px !important;
        color: #94a3b8 !important;
        font-weight: 600 !important;
        padding: 0.6rem 1.4rem !important;
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
        font-size: 1.5rem; font-weight: 700; color: #f8fafc;
        margin-bottom: 1.2rem;
    }

    /* Cartes transactions récentes */
    .tx-card {
        background: rgba(255,255,255,0.03);
        border: 1px solid rgba(255,255,255,0.08);
        border-radius: 14px;
        padding: 1.1rem 1.3rem;
        margin-bottom: 0.7rem;
        display: grid;
        grid-template-columns: auto 1fr auto auto;
        gap: 1rem;
        align-items: center;
        transition: all 0.15s;
    }
    .tx-card:hover {
        border-color: rgba(14,165,233,0.3);
        background: rgba(14,165,233,0.04);
    }
    .tx-badge {
        width: 40px; height: 40px; border-radius: 10px;
        display: flex; align-items: center; justify-content: center;
        font-weight: 700; font-size: 1.1rem;
    }
    .badge-achat { background: rgba(16,185,129,0.15); color: #10b981; }
    .badge-vente { background: rgba(239,68,68,0.15); color: #ef4444; }

    .tx-nom { font-weight: 600; color: #f1f5f9; font-size: 0.98rem; }
    .tx-meta { font-size: 0.8rem; color: #64748b; margin-top: 0.1rem; }

    .tx-ticker {
        background: rgba(14,165,233,0.12);
        color: #38bdf8;
        padding: 0.3rem 0.7rem;
        border-radius: 8px;
        font-weight: 700; font-size: 0.85rem;
        letter-spacing: 1px;
    }

    .tx-montant {
        font-weight: 700; color: #f8fafc; font-size: 1.05rem;
        text-align: right; min-width: 90px;
    }
    .tx-sens-vert { color: #10b981; font-size: 0.75rem; }
    .tx-sens-rouge { color: #ef4444; font-size: 0.75rem; }

    /* Grille KPI */
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
        text-transform: uppercase; letter-spacing: 1.5px;
        margin-bottom: 0.5rem;
    }
    .kpi-val {
        font-size: 1.7rem; font-weight: 700; color: #f8fafc; line-height: 1.1;
    }
    .kpi-sub { font-size: 0.78rem; color: #64748b; margin-top: 0.3rem; }
    .vert { color: #10b981; }
    .rouge { color: #ef4444; }

    /* Cartes insider / ticker */
    .entity-card {
        background: rgba(255,255,255,0.03);
        border: 1px solid rgba(255,255,255,0.08);
        border-radius: 14px;
        padding: 1.1rem 1.2rem;
        margin-bottom: 0.7rem;
        display: flex; align-items: center; gap: 1rem;
    }
    .entity-avatar {
        width: 48px; height: 48px; border-radius: 50%;
        background: linear-gradient(135deg, #334155, #0f172a);
        display: flex; align-items: center; justify-content: center;
        font-weight: 700; font-size: 0.95rem; color: #f8fafc;
        flex-shrink: 0;
    }
    .entity-avatar.ticker {
        background: linear-gradient(135deg, #1e3a8a, #0ea5e9);
        border-radius: 10px;
        font-size: 0.85rem; letter-spacing: 1px;
    }
    .entity-info { flex: 1; min-width: 0; }
    .entity-name {
        font-weight: 600; color: #f1f5f9; font-size: 1.02rem;
        overflow: hidden; text-overflow: ellipsis; white-space: nowrap;
    }
    .entity-sub { font-size: 0.8rem; color: #64748b; margin-top: 0.15rem; }
    .entity-right { text-align: right; flex-shrink: 0; }
    .entity-val { font-size: 1.1rem; font-weight: 700; color: #f8fafc; }
    .entity-cap { font-size: 0.72rem; color: #64748b; text-transform: uppercase; letter-spacing: 1px; }

    /* Search bar */
    .stTextInput input {
        background: rgba(255,255,255,0.05) !important;
        color: #f8fafc !important;
        border: 1px solid rgba(255,255,255,0.1) !important;
        border-radius: 10px !important;
        padding: 0.7rem 1rem !important;
        font-size: 1.05rem !important;
    }

    /* Boutons */
    .stButton > button {
        background: linear-gradient(135deg, #2563eb, #0ea5e9);
        color: white !important;
        border: none !important;
        border-radius: 10px;
        font-weight: 600;
    }

    /* DataFrames */
    [data-testid="stDataFrame"] {
        background: rgba(255,255,255,0.02);
        border-radius: 14px;
        border: 1px solid rgba(255,255,255,0.08);
        padding: 0.5rem;
    }

    /* Footer */
    .footer-note {
        margin-top: 3rem;
        padding-top: 1.5rem;
        border-top: 1px solid rgba(255,255,255,0.06);
        text-align: center;
        font-size: 0.75rem;
        color: #475569;
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


@st.cache_data(ttl=600, show_spinner=False)
def recuperer_profil(symbole: str, api_key: str) -> dict:
    try:
        r = requests.get(
            "https://finnhub.io/api/v1/stock/profile2",
            params={"symbole": symbole, "token": api_key},
            timeout=10,
        )
        r.raise_for_status()
        return r.json() or {}
    except requests.RequestException:
        return {}


@st.cache_data(ttl=600, show_spinner="Chargement des données de marché...")
def recuperer_toute_watchlist(api_key: str) -> pd.DataFrame:
    """Récupère en parallèle les transactions de tous les tickers de la watchlist."""
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
def initiales(nom: str) -> str:
    parties = [p for p in nom.replace(",", " ").split() if p]
    if not parties:
        return "?"
    if len(parties) == 1:
        return parties[0][:2].upper()
    return (parties[0][0] + parties[-1][0]).upper()


def format_nombre(n: float) -> str:
    if abs(n) >= 1_000_000_000:
        return f"{n/1_000_000_000:.2f}Md"
    if abs(n) >= 1_000_000:
        return f"{n/1_000_000:.2f}M"
    if abs(n) >= 1_000:
        return f"{n/1_000:.1f}k"
    return f"{n:.0f}"


def carte_transaction(row) -> str:
    sens = "achat" if row["change"] > 0 else "vente"
    badge_cls = "badge-achat" if sens == "achat" else "badge-vente"
    badge_ico = "▲" if sens == "achat" else "▼"
    sens_cls = "tx-sens-vert" if sens == "achat" else "tx-sens-rouge"
    sens_lbl = "ACHAT" if sens == "achat" else "VENTE"
    date = row["transactionDate"].strftime("%d %b") if pd.notna(row["transactionDate"]) else "—"
    entreprise = WATCHLIST.get(row["symbol"], row["symbol"])
    montant = row["montant"]
    return f"""
    <div class="tx-card">
        <div class="tx-badge {badge_cls}">{badge_ico}</div>
        <div>
            <div class="tx-nom">{row["name"]}</div>
            <div class="tx-meta">{entreprise} · {date}</div>
        </div>
        <div class="tx-ticker">{row["symbol"]}</div>
        <div class="tx-montant">
            ${format_nombre(montant)}
            <div class="{sens_cls}">{sens_lbl}</div>
        </div>
    </div>
    """


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


# ============================================================
# GARDE
# ============================================================
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
            <div class="accueil-subtitre">Suivez en temps réel les transactions des dirigeants des plus grandes entreprises cotées — données officielles SEC.</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    df_all = recuperer_toute_watchlist(API_KEY)

    if df_all.empty:
        st.warning("Aucune donnée disponible pour le moment.")
    else:
        # ---- KPIs globaux ----
        total_tx = len(df_all)
        volume_global = df_all["montant"].sum()
        nb_insiders_uniques = df_all["name"].nunique()
        nb_entreprises = df_all["symbol"].nunique()
        achats_g = df_all[df_all["change"] > 0]
        ventes_g = df_all[df_all["change"] < 0]
        ratio = (len(achats_g) / max(len(ventes_g), 1))

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
                    <div class="kpi-sub">cumul sur la watchlist</div>
                </div>
                <div class="kpi-card">
                    <div class="kpi-lbl">Dirigeants actifs</div>
                    <div class="kpi-val">{nb_insiders_uniques}</div>
                    <div class="kpi-sub">tous tickers confondus</div>
                </div>
                <div class="kpi-card">
                    <div class="kpi-lbl">Ratio Achats / Ventes</div>
                    <div class="kpi-val">{ratio:.2f}</div>
                    <div class="kpi-sub"><span class="vert">▲ {len(achats_g)}</span> · <span class="rouge">▼ {len(ventes_g)}</span></div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # ---- Gros mouvements récents ----
        st.markdown('<div class="sec-eyebrow">— À la une</div>', unsafe_allow_html=True)
        st.markdown('<div class="sec-title">🔥 Gros mouvements récents</div>', unsafe_allow_html=True)

        gros = df_all.sort_values("montant", ascending=False).head(8)
        for _, row in gros.iterrows():
            st.markdown(carte_transaction(row), unsafe_allow_html=True)

        # ---- Dernières transactions ----
        st.markdown('<div class="sec-eyebrow">— Flux en direct</div>', unsafe_allow_html=True)
        st.markdown('<div class="sec-title">⏱️ Dernières déclarations</div>', unsafe_allow_html=True)

        recents = df_all.dropna(subset=["transactionDate"]).sort_values("transactionDate", ascending=False).head(8)
        for _, row in recents.iterrows():
            st.markdown(carte_transaction(row), unsafe_allow_html=True)


# ============================================================
# INSIDERS
# ============================================================
with tab_insiders:
    st.markdown(
        """
        <div class="accueil-hero">
            <div class="accueil-titre">Les grands noms.</div>
            <div class="accueil-subtitre">Dirigeants les plus actifs sur la watchlist, classés par volume de transactions.</div>
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
                      derniere=("transactionDate", "max"),
                  )
                  .sort_values("volume", ascending=False)
                  .head(20)
                  .reset_index()
        )

        for _, row in top_insiders.iterrows():
            derniere = row["derniere"].strftime("%d %b %Y") if pd.notna(row["derniere"]) else "—"
            st.markdown(
                f"""
                <div class="entity-card">
                    <div class="entity-avatar">{initiales(row["name"])}</div>
                    <div class="entity-info">
                        <div class="entity-name">{row["name"]}</div>
                        <div class="entity-sub">{row["entreprises"]} · dernière op. {derniere}</div>
                    </div>
                    <div class="entity-right">
                        <div class="entity-val">${format_nombre(row["volume"])}</div>
                        <div class="entity-cap">{row["nb_tx"]} transactions</div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )


# ============================================================
# ENTREPRISES
# ============================================================
with tab_tickers:
    st.markdown(
        """
        <div class="accueil-hero">
            <div class="accueil-titre">Watchlist.</div>
            <div class="accueil-subtitre">Les entreprises suivies et leur activité insider récente.</div>
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
                      derniere=("transactionDate", "max"),
                  )
                  .sort_values("volume", ascending=False)
                  .reset_index()
        )

        for _, row in par_entreprise.iterrows():
            nom = WATCHLIST.get(row["symbol"], row["symbol"])
            derniere = row["derniere"].strftime("%d %b %Y") if pd.notna(row["derniere"]) else "—"
            st.markdown(
                f"""
                <div class="entity-card">
                    <div class="entity-avatar ticker">{row["symbol"]}</div>
                    <div class="entity-info">
                        <div class="entity-name">{nom}</div>
                        <div class="entity-sub">{row["nb_insiders"]} dirigeants · dernière op. {derniere}</div>
                    </div>
                    <div class="entity-right">
                        <div class="entity-val">${format_nombre(row["volume"])}</div>
                        <div class="entity-cap">{row["nb_tx"]} transactions</div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )


# ============================================================
# RECHERCHE PAR TICKER
# ============================================================
with tab_recherche:
    st.markdown(
        """
        <div class="accueil-hero">
            <div class="accueil-titre">Analyse ticker.</div>
            <div class="accueil-subtitre">Saisissez un symbole boursier pour voir l'activité complète de ses dirigeants.</div>
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

    # KPIs par ticker
    nb_tx = len(df)
    nb_in = df["name"].nunique()
    vol = df["montant"].sum()
    net = int(df["change"].sum())
    achats_t = df[df["change"] > 0]
    ventes_t = df[df["change"] < 0]
    derniere = df["transactionDate"].max()
    derniere_str = derniere.strftime("%d %b %Y") if pd.notna(derniere) else "—"
    sens_cls = "vert" if net >= 0 else "rouge"
    sens_signe = "+" if net >= 0 else ""

    st.markdown(
        f"""
        <div class="kpi-grid">
            <div class="kpi-card">
                <div class="kpi-lbl">Transactions</div>
                <div class="kpi-val">{nb_tx}</div>
                <div class="kpi-sub"><span class="vert">▲ {len(achats_t)}</span> · <span class="rouge">▼ {len(ventes_t)}</span></div>
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

    # Historique
    st.markdown('<div class="sec-eyebrow">— Historique complet</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="sec-title">Transactions {ticker}</div>', unsafe_allow_html=True)

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
        Données officielles SEC · fournies par Finnhub<br>
        Sentinelle est un outil informatif et ne constitue pas un conseil en investissement.
    </div>
    """,
    unsafe_allow_html=True,
)
