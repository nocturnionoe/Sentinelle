"""
Sentinelle — suivi des portefeuilles et transactions de personnalités.

Sources :
- SEC EDGAR, formulaires 13F : portefeuilles complets des grands investisseurs
  (toutes leurs lignes d'actions cotées aux US, comparées au trimestre précédent).
- Bargo : transactions déclarées par les membres du Congrès US (STOCK Act).
- Finnhub : transactions des dirigeants sur leur propre société (Form 4), optionnel.
"""
import html
import json
import re
import threading
import time
import xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pandas as pd
import requests
import streamlit as st

# ================================================================
# CONFIGURATION
# ================================================================
st.set_page_config(page_title="Sentinelle", page_icon="◼", layout="wide",
                   initial_sidebar_state="collapsed")


def _secret(nom: str, defaut: str = "") -> str:
    try:
        return st.secrets[nom]
    except Exception:
        return defaut


FINNHUB_KEY = _secret("FINNHUB_API_KEY")
# La SEC exige un User-Agent identifiable ; personnalisable via les Secrets.
SEC_UA = {"User-Agent": _secret("SEC_USER_AGENT", "Sentinelle-App/1.0 (research tool)")}
BARGO_URL = "https://www.bargo.ai/free-apis/congress/v1/trades"
DATA_DIR = Path(__file__).parent / "data"
AUJ = datetime.now(timezone.utc).date()

# Investisseurs suivis : (clé, nom, structure déclarante, CIK SEC)
INVESTISSEURS = [
    ("buffett", "Warren Buffett", "Berkshire Hathaway", 1067983),
    ("ackman", "Bill Ackman", "Pershing Square", 1336528),
    ("dalio", "Ray Dalio", "Bridgewater Associates", 1350694),
    ("gates", "Bill Gates", "Gates Foundation Trust", 1166559),
    ("icahn", "Carl Icahn", "Icahn Enterprises", 921669),
    ("tepper", "David Tepper", "Appaloosa", 1656456),
    ("druckenmiller", "Stanley Druckenmiller", "Duquesne Family Office", 1536411),
    ("soros", "George Soros", "Soros Fund Management", 1029160),
    ("wood", "Cathie Wood", "ARK Invest", 1697748),
    ("klarman", "Seth Klarman", "Baupost Group", 1061768),
    ("loeb", "Dan Loeb", "Third Point", 1040273),
    ("coleman", "Chase Coleman", "Tiger Global", 1167483),
    ("marks", "Howard Marks", "Oaktree Capital", 949509),
    ("lilu", "Li Lu", "Himalaya Capital", 1709323),
    ("smith", "Terry Smith", "Fundsmith", 1569205),
    ("hohn", "Chris Hohn", "TCI Fund Management", 1647251),
    ("peltz", "Nelson Peltz", "Trian Fund Management", 1345471),
    ("son", "Masayoshi Son", "SoftBank Group", 1065521),
]

# Sociétés suivies pour les transactions de dirigeants (Finnhub)
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

# ================================================================
# STYLE
# ================================================================
st.markdown(
    """
<style>
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500&family=IBM+Plex+Sans:wght@400;500;600&family=Source+Serif+4:opsz,wght@8..60,500;8..60,600&display=swap');

:root {
  --bg: #f6f5f1; --surface: #ffffff; --ink: #15171a; --mut: #6a6f76; --faint: #9a9ea4;
  --line: #e2e0d9; --line-soft: #eeece6; --acc: #1d3557;
  --up: #0f7a4d; --up-bg: #e7f3ec; --down: #b42318; --down-bg: #fbeceb; --flat-bg: #efeee9;
  --sans: 'IBM Plex Sans', system-ui, sans-serif;
  --mono: 'IBM Plex Mono', ui-monospace, monospace;
  --serif: 'Source Serif 4', Georgia, serif;
}
html, body, .stApp, button, input, textarea, [data-baseweb] { font-family: var(--sans) !important; }
.stApp { background: var(--bg); color: var(--ink); }
[data-testid="stHeader"], #MainMenu, footer { display: none !important; }
.block-container { padding: 1.6rem 2rem 3rem; max-width: 1160px; }

/* En-tête */
.top { display: flex; align-items: baseline; justify-content: space-between; gap: 1rem;
       padding-bottom: .9rem; border-bottom: 2px solid var(--ink); }
.wordmark { font-family: var(--serif); font-size: 1.55rem; font-weight: 600; letter-spacing: -.01em; }
.top-meta { font-size: .78rem; color: var(--mut); text-align: right; }

/* Onglets */
[data-baseweb="tab-list"] { gap: 1.6rem; border-bottom: 1px solid var(--line); background: none; }
[data-baseweb="tab"] { padding: .85rem 0 !important; background: none !important; color: var(--mut) !important; }
[data-baseweb="tab"] p { font-size: .9rem !important; font-weight: 500 !important; }
[data-baseweb="tab"][aria-selected="true"] { color: var(--ink) !important; }
[data-baseweb="tab-highlight"] { background: var(--ink) !important; height: 2px !important; }
[data-baseweb="tab-border"] { display: none !important; }

/* Titres */
.page-h { font-family: var(--serif); font-size: 1.9rem; font-weight: 600; letter-spacing: -.015em;
          margin: 1.6rem 0 .3rem; line-height: 1.15; }
.page-s { color: var(--mut); font-size: .95rem; max-width: 720px; line-height: 1.5; margin-bottom: 1.4rem; }
.sec { display: flex; align-items: baseline; justify-content: space-between; gap: 1rem;
       margin: 2rem 0 .6rem; }
.sec h3 { font-size: .95rem; font-weight: 600; margin: 0; padding: 0; }
.sec span { font-size: .78rem; color: var(--mut); }

/* Chiffres clés */
.kpis { display: grid; grid-template-columns: repeat(4, 1fr); border: 1px solid var(--line);
        background: var(--surface); border-radius: 3px; }
.kpi { padding: 1rem 1.15rem; border-left: 1px solid var(--line-soft); min-width: 0; }
.kpi:first-child { border-left: 0; }
.kpi-l { font-size: .75rem; color: var(--mut); margin-bottom: .35rem; }
.kpi-v { font-family: var(--mono); font-size: 1.35rem; font-weight: 500; letter-spacing: -.02em;
         white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.kpi-d { font-size: .75rem; color: var(--faint); margin-top: .25rem; }

/* Tableaux */
.tw { border: 1px solid var(--line); background: var(--surface); border-radius: 3px; overflow-x: auto; }
table.t { width: 100%; border-collapse: collapse; font-size: .86rem; }
.t th { text-align: left; font-weight: 500; font-size: .73rem; color: var(--mut);
        padding: .6rem .9rem; border-bottom: 1px solid var(--line); white-space: nowrap; background: #fbfaf7; }
.t td { padding: .58rem .9rem; border-bottom: 1px solid var(--line-soft); vertical-align: middle; }
.t tr:last-child td { border-bottom: 0; }
.t tbody tr:hover td { background: #fbfaf7; }
.t .r { text-align: right; }
.t .num { font-family: var(--mono); font-size: .82rem; white-space: nowrap; font-variant-numeric: tabular-nums; }
.t .rank { color: var(--faint); font-family: var(--mono); font-size: .76rem; width: 1%; }
.nm { font-weight: 500; }
.sub { color: var(--mut); font-size: .76rem; margin-top: .08rem; }
.tk { font-family: var(--mono); font-size: .72rem; color: var(--acc); border: 1px solid var(--line);
      padding: .05rem .32rem; border-radius: 2px; margin-left: .45rem; white-space: nowrap; background: var(--bg); }
.tag { display: inline-block; font-size: .72rem; font-weight: 500; padding: .12rem .45rem; border-radius: 2px;
       white-space: nowrap; }
.tag.up { color: var(--up); background: var(--up-bg); }
.tag.down { color: var(--down); background: var(--down-bg); }
.tag.flat { color: var(--mut); background: var(--flat-bg); }
.up-t { color: var(--up); } .down-t { color: var(--down); } .mut-t { color: var(--faint); }
.bar { display: inline-block; width: 72px; height: 5px; background: var(--line-soft); vertical-align: middle;
       margin-right: .55rem; }
.bar i { display: block; height: 100%; background: var(--acc); }
.note { font-size: .78rem; color: var(--mut); line-height: 1.5; margin-top: .7rem; max-width: 820px; }
.empty { border: 1px dashed var(--line); padding: 1.4rem; text-align: center; color: var(--mut);
         font-size: .88rem; border-radius: 3px; }

/* Widgets Streamlit */
[data-baseweb="select"] > div, .stTextInput input {
  background: var(--surface) !important; border: 1px solid var(--line) !important;
  border-radius: 3px !important; font-size: .9rem !important; box-shadow: none !important; }
[data-testid="stWidgetLabel"] p { font-size: .75rem !important; color: var(--mut) !important; }
[data-testid="stBaseButton-segmented_control"], [data-testid="stBaseButton-segmented_controlActive"] {
  border-radius: 2px !important; font-size: .82rem !important; }
[data-testid="stBaseButton-segmented_controlActive"] {
  background: var(--ink) !important; color: #fff !important; border-color: var(--ink) !important; }
[data-testid="stBaseButton-segmented_controlActive"] p { color: #fff !important; }

.foot { margin-top: 3rem; padding-top: 1rem; border-top: 1px solid var(--line);
        font-size: .75rem; color: var(--faint); line-height: 1.6; }
@media (max-width: 760px) {
  .block-container { padding: 1rem 1rem 2rem; }
  .kpis { grid-template-columns: repeat(2, 1fr); }
  .kpi:nth-child(3) { border-left: 0; }
  .kpi:nth-child(n+3) { border-top: 1px solid var(--line-soft); }
  .top { flex-direction: column; gap: .2rem; } .top-meta { text-align: left; }
}
</style>
""",
    unsafe_allow_html=True,
)


# ================================================================
# FORMATAGE
# ================================================================
NBSP = " "
MOIS = ["janv.", "févr.", "mars", "avr.", "mai", "juin", "juil.", "août", "sept.", "oct.", "nov.", "déc."]


def esc(s) -> str:
    return html.escape("" if s is None else str(s))


def fmt_usd(n) -> str:
    """Montant en dollars, notation française abrégée."""
    try:
        n = float(n)
    except (TypeError, ValueError):
        return "—"
    if pd.isna(n):
        return "—"
    a = abs(n)
    if a >= 1e9:
        s = f"{n / 1e9:.2f}{NBSP}Md"
    elif a >= 1e6:
        s = f"{n / 1e6:.1f}{NBSP}M"
    elif a >= 1e3:
        s = f"{n / 1e3:.0f}{NBSP}k"
    else:
        s = f"{n:.0f}"
    return s.replace(".", ",") + f"{NBSP}$"


def fmt_int(n) -> str:
    try:
        return f"{float(n):,.0f}".replace(",", " ")
    except (TypeError, ValueError):
        return "—"


def fmt_pct(x, signe: bool = False, dec: int = 1) -> str:
    if x is None or pd.isna(x):
        return "—"
    s = f"{x:+.{dec}f}" if signe else f"{x:.{dec}f}"
    return s.replace(".", ",") + f"{NBSP}%"


def fmt_date(d) -> str:
    if d is None or pd.isna(d):
        return "—"
    return f"{d.day} {MOIS[d.month - 1]} {d.year}"


def trimestre(d) -> str:
    return f"T{(d.month - 1) // 3 + 1} {d.year}"


# ================================================================
# COMPOSANTS HTML
# ================================================================
def titre_page(titre: str, sous_titre: str):
    st.html(f'<div class="page-h">{esc(titre)}</div><div class="page-s">{esc(sous_titre)}</div>')


def section(titre: str, meta: str = ""):
    st.html(f'<div class="sec"><h3>{esc(titre)}</h3><span>{esc(meta)}</span></div>')


def kpis(items):
    """items : liste de (libellé, valeur, détail)."""
    cells = "".join(
        f'<div class="kpi"><div class="kpi-l">{esc(l)}</div><div class="kpi-v">{esc(v)}</div>'
        f'<div class="kpi-d">{esc(d)}</div></div>'
        for l, v, d in items
    )
    st.html(f'<div class="kpis">{cells}</div>')


def table(colonnes, lignes, vide: str = "Aucune donnée."):
    """colonnes : liste de (libellé, classes CSS). lignes : cellules déjà en HTML."""
    if not lignes:
        st.html(f'<div class="empty">{esc(vide)}</div>')
        return
    head = "".join(f'<th class="{c}">{esc(l)}</th>' for l, c in colonnes)
    body = "".join(
        "<tr>" + "".join(f'<td class="{colonnes[i][1]}">{cell}</td>' for i, cell in enumerate(row)) + "</tr>"
        for row in lignes
    )
    st.html(f'<div class="tw"><table class="t"><thead><tr>{head}</tr></thead><tbody>{body}</tbody></table></div>')


def cell_titre(nom: str, ticker: str = "", sous: str = "") -> str:
    tk = f'<span class="tk">{esc(ticker)}</span>' if ticker else ""
    sub = f'<div class="sub">{esc(sous)}</div>' if sous else ""
    return f'<span class="nm">{esc(nom)}</span>{tk}{sub}'


def cell_poids(poids: float, maxi: float) -> str:
    w = 0 if not maxi else max(2, min(100, 100 * poids / maxi))
    return f'<span class="bar"><i style="width:{w:.0f}%"></i></span>{fmt_pct(poids)}'


TAGS = {"Nouvelle": "up", "Renforcée": "up", "Allégée": "down", "Soldée": "down", "Inchangée": "flat",
        "Achat": "up", "Vente": "down"}


def tag(libelle: str) -> str:
    return f'<span class="tag {TAGS.get(libelle, "flat")}">{esc(libelle)}</span>'


def cell_var(row) -> str:
    """Variation du nombre de titres par rapport au trimestre précédent."""
    statut = row["statut"]
    if statut in ("Nouvelle", "Soldée", "Inchangée"):
        return tag(statut)
    cls = "up-t" if row["var"] > 0 else "down-t"
    return f'{tag(statut)} <span class="num {cls}">{fmt_pct(row["var"], signe=True)}</span>'


# ================================================================
# SEC EDGAR — PORTEFEUILLES 13F
# ================================================================
_sec_lock = threading.Lock()
_sec_last = [0.0]


def sec_get(url: str) -> requests.Response:
    """GET sur sec.gov en respectant la limite de débit (10 requêtes/s max)."""
    for essai in range(3):
        with _sec_lock:
            attente = 0.13 - (time.monotonic() - _sec_last[0])
            if attente > 0:
                time.sleep(attente)
            _sec_last[0] = time.monotonic()
        r = requests.get(url, headers=SEC_UA, timeout=20)
        if r.status_code == 429:
            time.sleep(1.5 * (essai + 1))
            continue
        r.raise_for_status()
        return r
    r.raise_for_status()
    return r


def _lire_depot(cik: int, accession: str) -> pd.DataFrame:
    """Table des positions d'un dépôt 13F, agrégée par titre (CUSIP + type d'option)."""
    base = f"https://www.sec.gov/Archives/edgar/data/{cik}/{accession.replace('-', '')}"
    fichiers = sec_get(f"{base}/index.json").json()["directory"]["item"]
    xmls = [f for f in fichiers if f["name"].lower().endswith(".xml") and f["name"] != "primary_doc.xml"]
    if not xmls:
        return pd.DataFrame()
    cible = max(xmls, key=lambda f: int(f.get("size") or 0))["name"]
    racine = ET.fromstring(sec_get(f"{base}/{cible}").content)
    lignes = []
    for it in racine.findall(".//{*}infoTable"):
        lignes.append({
            "cusip": (it.findtext("{*}cusip") or "").strip().upper(),
            "pc": (it.findtext("{*}putCall") or "").strip().capitalize(),
            "emetteur": (it.findtext("{*}nameOfIssuer") or "").strip(),
            "classe": (it.findtext("{*}titleOfClass") or "").strip(),
            "valeur": float(it.findtext("{*}value") or 0),
            "titres": float(it.findtext("{*}shrsOrPrnAmt/{*}sshPrnamt") or 0),
        })
    if not lignes:
        return pd.DataFrame()
    return (pd.DataFrame(lignes)
            .groupby(["cusip", "pc"], as_index=False)
            .agg(emetteur=("emetteur", "first"), classe=("classe", "first"),
                 valeur=("valeur", "sum"), titres=("titres", "sum")))


def _charger_investisseur(inv) -> dict | None:
    """Dernier 13F d'un investisseur, comparé au trimestre précédent."""
    cle, nom, fonds, cik = inv
    try:
        rec = sec_get(f"https://data.sec.gov/submissions/CIK{cik:010d}.json").json()["filings"]["recent"]
        depots, vus = [], set()
        for form, acc, rep, dep in zip(rec["form"], rec["accessionNumber"], rec["reportDate"], rec["filingDate"]):
            if form == "13F-HR" and rep not in vus:
                vus.add(rep)
                depots.append((acc, rep, dep))
            if len(depots) == 2:
                break
        if not depots:
            return None
        cur = _lire_depot(cik, depots[0][0])
        if cur.empty:
            return None
        prev = _lire_depot(cik, depots[1][0]) if len(depots) > 1 else pd.DataFrame()
    except Exception:
        return None

    if prev.empty:
        df = cur.assign(valeur_prec=0.0, titres_prec=0.0)
    else:
        df = cur.merge(prev[["cusip", "pc", "emetteur", "classe", "valeur", "titres"]],
                       on=["cusip", "pc"], how="outer", suffixes=("", "_prec"))
        df["emetteur"] = df["emetteur"].fillna(df["emetteur_prec"])
        df["classe"] = df["classe"].fillna(df["classe_prec"])
        df = df.drop(columns=["emetteur_prec", "classe_prec"])
    for c in ("valeur", "titres", "valeur_prec", "titres_prec"):
        df[c] = df[c].fillna(0.0)

    def statut(r):
        if prev.empty:
            return "Inchangée"
        if r["titres_prec"] == 0:
            return "Nouvelle"
        if r["titres"] == 0:
            return "Soldée"
        v = r["titres"] / r["titres_prec"] - 1
        return "Renforcée" if v > 0.01 else "Allégée" if v < -0.01 else "Inchangée"

    df["statut"] = df.apply(statut, axis=1)
    df["var"] = ((df["titres"] / df["titres_prec"].where(df["titres_prec"] > 0) - 1) * 100)
    total = df["valeur"].sum()
    df["poids"] = 100 * df["valeur"] / total if total else 0.0
    # Flux estimé : variation du nombre de titres valorisée au dernier cours connu
    # (neutralise l'effet de la simple variation de cours entre deux trimestres).
    prix = (df["valeur"] / df["titres"].where(df["titres"] > 0)).fillna(
        df["valeur_prec"] / df["titres_prec"].where(df["titres_prec"] > 0)).fillna(0)
    df["delta_valeur"] = (df["titres"] - df["titres_prec"]) * prix
    df = df.sort_values("valeur", ascending=False).reset_index(drop=True)
    return {
        "cle": cle, "nom": nom, "fonds": fonds, "cik": cik, "df": df, "total": total,
        "periode": pd.Timestamp(depots[0][1]), "depose": pd.Timestamp(depots[0][2]),
        "comparaison": pd.Timestamp(depots[1][1]) if len(depots) > 1 else None,
    }


# --- Correspondance nom d'émetteur -> ticker (meilleure approximation) -------
_ABREV = {
    "FINL": "FINANCIAL", "FIN": "FINANCIAL", "INTL": "INTERNATIONAL", "TECHNOLOGIES": "TECH",
    "TECHNOLOGY": "TECH", "SVCS": "SERVICES", "SVC": "SERVICE", "PPTYS": "PROPERTIES", "MTRS": "MOTORS",
    "MTR": "MOTOR", "PETE": "PETROLEUM", "COMMUNICATIONS": "COMM", "COMMUNS": "COMM",
    "PHARMACEUTICALS": "PHARMA", "PHARMACEUTICAL": "PHARMA", "LABS": "LABORATORIES", "ENTMT": "ENTERTAINMENT",
    "SYS": "SYSTEMS", "MGMT": "MANAGEMENT", "RES": "RESOURCES", "AMER": "AMERICA", "BK": "BANK",
    "NATL": "NATIONAL", "INDS": "INDUSTRIES", "WHSL": "WHOLESALE", "CAP": "CAPITAL", "SOLUTIONS": "SOLTNS",
    "SOLUTION": "SOLTNS", "HEALTHCARE": "HLTHCR", "HLTHCARE": "HLTHCR", "ENTERPRISES": "ENT",
    "ENTERPRISE": "ENT", "PRODS": "PRODUCTS", "MATLS": "MATERIALS", "ELEC": "ELECTRIC", "PWR": "POWER",
    "TR": "TRUST", "MACHS": "MACHINES", "BUSINESS": "BUS", "DEV": "DEVELOPMENT", "CTLS": "CONTROLS",
    "AIRLS": "AIRLINES", "LINES": "LINES", "MED": "MEDICAL", "INS": "INSURANCE", "EXPL": "EXPLORATION",
    "INVT": "INVESTMENT", "MANUFAC": "MANUFACTURING", "TECHN": "TECH", "TECHNOLOG": "TECH", "RLTY": "REALTY", "CTRS": "CENTERS", "RESH": "RESEARCH", "MFG": "MANUFACTURING",
}
_VIDES = {"INC", "INCORPORATED", "CORP", "CORPORATION", "CO", "COMPANY", "COS", "LTD", "LIMITED", "PLC", "LP", "LLC", "SA", "NV",
          "AG", "SE", "THE", "NEW", "DEL", "COM", "CL", "A", "B", "C", "ADR", "ADS", "SPONSORED", "HOLDINGS",
          "HOLDING", "HLDGS", "HLDG", "GROUP", "GRP", "AND", "N", "V", "S", "DE", "MD", "OF"}


def _norme(nom: str) -> str:
    mots = re.sub(r"[^A-Z0-9 ]", " ", nom.upper().replace("&", " ").replace(".COM", "COM")).split()
    return " ".join(_ABREV.get(m, m) for m in mots if m not in _VIDES)


_FONDS = re.compile(r"\b(TR|TRUST|ETF|FUND|FDS|SPDR|ISHARES|VANGUARD|INVESCO|PROSHARES|DIREXION|INDEX)\b")


def _table_tickers() -> dict:
    """Index nom normalisé -> (ticker, raison sociale), plus un index sur les 3 et 2 premiers mots."""
    try:
        data = sec_get("https://www.sec.gov/files/company_tickers.json").json()
    except Exception:
        return {}
    table_ = {}
    for e in data.values():  # trié par capitalisation : le ticker principal passe en premier
        cle = _norme(e["title"])
        val = (e["ticker"], e["title"])
        table_.setdefault(cle, val)
        mots = cle.split()
        for n in (3, 2):
            if len(mots) > n and len(mots[0]) >= 4:
                table_.setdefault("~" + " ".join(mots[:n]), val)
    return table_


def _trouver_ticker(emetteur: str, tickers: dict):
    """Rapproche un nom d'émetteur 13F (abrégé) d'un ticker. Les fonds et ETF sont ignorés."""
    if _FONDS.search(emetteur.upper()):
        return None
    cle = _norme(emetteur)
    if cle in tickers:
        return tickers[cle]
    mots = cle.split()
    for n in (3, 2):
        if len(mots) >= n and len(mots[0]) >= 4:
            trouve = tickers.get("~" + " ".join(mots[:n]))
            if trouve:
                return trouve
    return None


_SUFFIXES = {"CO", "CORP", "INC", "LTD", "PLC", "NEW", "DEL", "COM", "CL", "THE", "OF", "AND"}


def _joli_nom(nom: str) -> str:
    """Casse lisible : les noms 13F sont en capitales, les sigles courts sont conservés."""
    nom = re.sub(r"\s*/[A-Z]{2,3}/?\s*$", "", nom.strip())
    mots = [m.lower() if m in ("OF", "AND", "DE") else
            m.capitalize() if m.isupper() and (len(m) > 3 or m in _SUFFIXES) else m
            for m in nom.split()]
    return " ".join(mots).replace("'S", "'s")


@st.cache_data(ttl=6 * 3600, show_spinner="Lecture des portefeuilles déclarés à la SEC…")
def charger_portefeuilles() -> dict:
    with ThreadPoolExecutor(max_workers=4) as ex:
        res = list(ex.map(_charger_investisseur, INVESTISSEURS))
    tickers = _table_tickers()
    out = {}
    for p in res:
        if p is None:
            continue
        df = p["df"]
        corr = df["emetteur"].map(lambda n: _trouver_ticker(n, tickers))
        df["ticker"] = corr.map(lambda c: c[0] if c else "")
        df["nom"] = [(_joli_nom(c[1]) if c else _joli_nom(n)) for c, n in zip(corr, df["emetteur"])]
        out[p["cle"]] = p
    return out


def portefeuilles() -> dict:
    """Ne conserve pas en cache un chargement vide (SEC momentanément inaccessible)."""
    pf = charger_portefeuilles()
    if not pf:
        charger_portefeuilles.clear()
    return pf


def toutes_positions(pf: dict) -> pd.DataFrame:
    """Concatène les positions de tous les investisseurs."""
    blocs = [p["df"].assign(inv=p["nom"], inv_cle=p["cle"]) for p in pf.values()]
    return pd.concat(blocs, ignore_index=True) if blocs else pd.DataFrame()


# ================================================================
# CONGRÈS US (Bargo)
# ================================================================
@st.cache_data(ttl=24 * 3600, show_spinner="Chargement des transactions du Congrès…")
def charger_congres() -> tuple[pd.DataFrame, str]:
    """Renvoie (transactions, origine). Quota Bargo : 100 lignes/jour, d'où le cache disque."""
    cache, seed = DATA_DIR / "congres_cache.json", DATA_DIR / "congres_seed.json"
    trades, origine = [], "direct"
    try:
        r = requests.get(BARGO_URL, params={"limit": 100}, timeout=15)
        r.raise_for_status()
        trades = r.json().get("trades", [])
    except (requests.RequestException, ValueError):
        trades = []
    if trades:
        try:
            DATA_DIR.mkdir(exist_ok=True)
            cache.write_text(json.dumps({"trades": trades}), encoding="utf-8")
        except OSError:
            pass
    else:
        origine = "cache"
        for f in (cache, seed):
            try:
                trades = json.loads(f.read_text(encoding="utf-8")).get("trades", [])
            except (OSError, ValueError):
                trades = []
            if trades:
                break
    if not trades:
        return pd.DataFrame(), "indisponible"
    df = pd.DataFrame(trades)
    for c in ("member", "ticker", "chamber", "state", "type", "asset", "amount_range"):
        df[c] = df[c].fillna("").astype(str) if c in df.columns else ""
    for c in ("amount_low", "amount_high", "perf_pct"):
        df[c] = pd.to_numeric(df[c], errors="coerce") if c in df.columns else float("nan")
    for c in ("transaction_date", "disclosure_date"):
        df[c] = pd.to_datetime(df[c], errors="coerce") if c in df.columns else pd.NaT
    df["montant"] = df[["amount_low", "amount_high"]].mean(axis=1).fillna(0)
    df["sens"] = df["type"].str.lower().map(lambda t: "Achat" if "purchase" in t else "Vente")
    df["actif"] = df["asset"].str.replace(r"\s*[\(\[].*$", "", regex=True).str.strip()
    return df.sort_values("transaction_date", ascending=False, na_position="last").reset_index(drop=True), origine


def lignes_congres(df: pd.DataFrame) -> list:
    out = []
    for _, r in df.iterrows():
        chambre = {"senate": "Sénat", "house": "Chambre"}.get(r["chamber"].lower(), "Congrès")
        perf = r["perf_pct"]
        perf_html = ('<span class="mut-t">—</span>' if pd.isna(perf) else
                     f'<span class="{"up-t" if perf >= 0 else "down-t"}">{fmt_pct(perf, signe=True)}</span>')
        out.append([
            esc(fmt_date(r["transaction_date"])),
            cell_titre(r["member"], sous=f"{chambre} · {r['state']}".strip(" ·")),
            tag(r["sens"]),
            cell_titre(r["actif"] or r["ticker"] or "—", r["ticker"]),
            esc(r["amount_range"] or fmt_usd(r["montant"])),
            perf_html,
        ])
    return out


COLS_CONGRES = [("Date", "num"), ("Élu", ""), ("Sens", ""), ("Actif", ""),
                ("Montant déclaré", "num r"), ("Perf. depuis", "num r")]


# ================================================================
# DIRIGEANTS (Finnhub, Form 4)
# ================================================================
@st.cache_data(ttl=1800, show_spinner=False)
def fetch_insider_tx(symbol: str, api_key: str, days: int = 90) -> pd.DataFrame:
    """Achats et ventes sur le marché (codes P et S) des dirigeants d'une société."""
    try:
        r = requests.get(
            "https://finnhub.io/api/v1/stock/insider-transactions",
            params={"symbol": symbol, "token": api_key,
                    "from": (AUJ - timedelta(days=days)).isoformat(), "to": AUJ.isoformat()},
            timeout=10,
        )
        r.raise_for_status()
        data = r.json().get("data", [])
    except (requests.RequestException, ValueError):
        return pd.DataFrame()
    if not data:
        return pd.DataFrame()
    df = pd.DataFrame(data)
    for c in ("transactionPrice", "change", "share"):
        df[c] = pd.to_numeric(df.get(c), errors="coerce").fillna(0)
    df["transactionDate"] = pd.to_datetime(df.get("transactionDate"), errors="coerce")
    df["name"] = df.get("name", "").astype(str).str.strip().str.title()
    if "transactionCode" in df.columns:
        df = df[df["transactionCode"].isin(["P", "S"])]
    df = df[df["transactionPrice"] > 0].copy()
    df["montant"] = df["change"].abs() * df["transactionPrice"]
    df["sens"] = df["change"].map(lambda c: "Achat" if c > 0 else "Vente")
    df["symbol"] = symbol
    return df.sort_values("transactionDate", ascending=False).reset_index(drop=True)


@st.cache_data(ttl=1800, show_spinner="Chargement des transactions de dirigeants…")
def charger_dirigeants(api_key: str) -> pd.DataFrame:
    with ThreadPoolExecutor(max_workers=8) as ex:
        res = [d for d in ex.map(lambda t: fetch_insider_tx.__wrapped__(t, api_key), WATCHLIST) if not d.empty]
    return pd.concat(res, ignore_index=True) if res else pd.DataFrame()


def lignes_dirigeants(df: pd.DataFrame) -> list:
    return [[
        esc(fmt_date(r["transactionDate"])),
        cell_titre(r["name"] or "—"),
        tag(r["sens"]),
        cell_titre(WATCHLIST.get(r["symbol"], r["symbol"]), r["symbol"]),
        f'{fmt_int(abs(r["change"]))} à {r["transactionPrice"]:,.2f}{NBSP}$'.replace(",", " "),
        esc(fmt_usd(r["montant"])),
    ] for _, r in df.iterrows()]


COLS_DIRIGEANTS = [("Date", "num"), ("Dirigeant", ""), ("Sens", ""), ("Société", ""),
                   ("Titres", "num r"), ("Montant", "num r")]


# ================================================================
# CHARGEMENT
# ================================================================
PF = portefeuilles()
POS = toutes_positions(PF)
CONGRES, CONGRES_SRC = charger_congres()

st.html(
    f'<div class="top"><div class="wordmark">Sentinelle</div>'
    f'<div class="top-meta">Portefeuilles et transactions déclarés · mis à jour le {fmt_date(AUJ)}</div></div>'
)

t_vue, t_inv, t_elus, t_dir, t_titre = st.tabs(
    ["Vue d'ensemble", "Investisseurs", "Élus américains", "Dirigeants", "Par titre"])


# ================================================================
# VUE D'ENSEMBLE
# ================================================================
with t_vue:
    titre_page("Où va l'argent des grands noms",
               "Portefeuilles complets des investisseurs les plus suivis, tels que déclarés à la SEC, "
               "et transactions personnelles des membres du Congrès américain.")
    if not PF:
        st.html('<div class="empty">Les données de la SEC sont momentanément inaccessibles. Rechargez la page.</div>')
    else:
        actions = POS[(POS["pc"] == "") & (POS["valeur"] > 0)]
        periode = max(p["periode"] for p in PF.values())
        kpis([
            ("Investisseurs suivis", str(len(PF)), "déclarations 13F"),
            ("Encours déclarés", fmt_usd(sum(p["total"] for p in PF.values())), "actions cotées aux États-Unis"),
            ("Nouvelles positions", fmt_int((POS["statut"] == "Nouvelle").sum()), f"ouvertes au {trimestre(periode)}"),
            ("Transactions d'élus", fmt_int(len(CONGRES)), "dernières déclarations"),
        ])

        def consensus(statuts, titre_, meta):
            sub = POS[(POS["pc"] == "") & POS["statut"].isin(statuts)]
            g = (sub.groupby("nom")  # par société : regroupe les classes d'actions (ex. Alphabet A et C)
                 .agg(ticker=("ticker", "first"), n=("inv", "nunique"),
                      qui=("inv", lambda s: ", ".join(sorted({x.split()[-1] for x in s}))),
                      flux=("delta_valeur", "sum"))
                 .sort_values(["n", "flux"], ascending=[False, statuts[0] != "Nouvelle"]).head(8))
            section(titre_, meta)
            table([("Titre", ""), ("Investisseurs", ""), ("Flux estimé", "num r")],
                  [[cell_titre(nom_, r["ticker"]),
                    f'<span class="nm">{r["n"]}</span><div class="sub">{esc(r["qui"])}</div>',
                    esc(fmt_usd(r["flux"]))] for nom_, r in g.iterrows()])

        c1, c2 = st.columns(2, gap="large")
        with c1:
            consensus(["Nouvelle", "Renforcée"], "Les plus achetés", "positions ouvertes ou renforcées")
        with c2:
            consensus(["Soldée", "Allégée"], "Les plus vendus", "positions soldées ou allégées")

        section("Nouvelles positions les plus importantes", "dernier trimestre déclaré")
        nouv = POS[(POS["statut"] == "Nouvelle")].sort_values("valeur", ascending=False).head(10)
        table([("Investisseur", ""), ("Titre", ""), ("Valeur", "num r"), ("Poids du portefeuille", "num r")],
              [[cell_titre(r["inv"], sous=PF[r["inv_cle"]]["fonds"]),
                cell_titre(r["nom"], r["ticker"], r["pc"] and f"Option {r['pc'].lower()}"),
                esc(fmt_usd(r["valeur"])), esc(fmt_pct(r["poids"]))] for _, r in nouv.iterrows()])

    section("Dernières transactions au Congrès", "déclarations STOCK Act")
    table(COLS_CONGRES, lignes_congres(CONGRES.head(8)), "Données du Congrès indisponibles pour le moment.")


# ================================================================
# INVESTISSEURS
# ================================================================
with t_inv:
    titre_page("Investisseurs",
               "Chaque trimestre, tout gérant de plus de 100 M$ publie l'intégralité de ses positions en actions "
               "américaines. On y lit ce qu'il détient, ce qu'il vient d'acheter et ce qu'il a vendu.")
    if not PF:
        st.html('<div class="empty">Données SEC indisponibles.</div>')
    else:
        ordre = sorted(PF.values(), key=lambda p: -p["total"])
        cles = [p["cle"] for p in ordre]
        c_sel, _ = st.columns([2, 3])
        with c_sel:
            choix = st.selectbox("Investisseur", cles,
                                 format_func=lambda k: f"{PF[k]['nom']} — {PF[k]['fonds']}")
        p = PF[choix]
        df = p["df"]
        detenu = df[df["valeur"] > 0]
        top10 = detenu["poids"].head(10).sum()
        kpis([
            ("Encours déclaré", fmt_usd(p["total"]), p["fonds"]),
            ("Positions", fmt_int(len(detenu)), f"{(df['statut'] == 'Nouvelle').sum()} nouvelles · "
                                                f"{(df['statut'] == 'Soldée').sum()} soldées"),
            ("Poids des 10 premières", fmt_pct(top10, dec=0), "concentration"),
            ("Trimestre", trimestre(p["periode"]), f"déposé le {fmt_date(p['depose'])}"),
        ])

        vues = ["Portefeuille", "Nouvelles", "Renforcées", "Allégées", "Soldées"]
        vue = st.segmented_control("Vue", vues, default="Portefeuille", label_visibility="collapsed",
                                   key="vue_inv") or "Portefeuille"
        filtre = {"Nouvelles": "Nouvelle", "Renforcées": "Renforcée", "Allégées": "Allégée", "Soldées": "Soldée"}
        if vue == "Portefeuille":
            sel = detenu
        else:
            sel = df[df["statut"] == filtre[vue]]
            sel = sel.sort_values("valeur_prec" if vue == "Soldées" else "valeur", ascending=False)

        LIMITE = 60
        maxi = detenu["poids"].max() if not detenu.empty else 0
        lignes = []
        for i, (_, r) in enumerate(sel.head(LIMITE).iterrows(), 1):
            # La classe n'est affichée que si elle apporte une information (pas « COM », « SHS »…)
            classe = "" if r["classe"].upper().startswith(("COM", "SHS", "ORD", "CAP STK")) else r["classe"].title()
            sous = " · ".join(x for x in [r["pc"] and f"Option {r['pc'].lower()}", classe] if x)
            if vue == "Soldées":
                lignes.append([str(i), cell_titre(r["nom"], r["ticker"], sous), esc(fmt_usd(r["valeur_prec"])),
                               esc(fmt_int(r["titres_prec"])), cell_var(r)])
            else:
                lignes.append([str(i), cell_titre(r["nom"], r["ticker"], sous), cell_poids(r["poids"], maxi),
                               esc(fmt_usd(r["valeur"])), esc(fmt_int(r["titres"])), cell_var(r)])
        if vue == "Soldées":
            cols = [("", "rank"), ("Titre", ""), ("Valeur au trimestre précédent", "num r"),
                    ("Titres vendus", "num r"), ("Mouvement", "")]
        else:
            cols = [("", "rank"), ("Titre", ""), ("Poids", "num"), ("Valeur", "num r"),
                    ("Titres", "num r"), ("Mouvement", "")]
        comp = f"par rapport au {trimestre(p['comparaison'])}" if p["comparaison"] is not None else ""
        section(f"{vue} · {p['nom']}", f"{len(sel)} lignes {comp}".strip())
        table(cols, lignes, "Aucune ligne dans cette catégorie ce trimestre.")
        if len(sel) > LIMITE:
            st.html(f'<div class="note">{LIMITE} premières lignes affichées sur {len(sel)}.</div>')
        st.html('<div class="note">Un 13F ne couvre que les positions longues en actions et options cotées aux '
                'États-Unis, à la date de fin de trimestre. Il est publié jusqu\'à 45 jours plus tard : les '
                'ventes à découvert, la trésorerie, les obligations et les titres étrangers n\'y figurent pas.</div>')

        section("Tous les investisseurs suivis", "classés par encours")
        table([("Investisseur", ""), ("Encours", "num r"), ("Positions", "num r"), ("Première ligne", ""),
               ("Nouvelles", "num r"), ("Soldées", "num r"), ("Trimestre", "num r")],
              [[cell_titre(q["nom"], sous=q["fonds"]), esc(fmt_usd(q["total"])),
                esc(fmt_int((q["df"]["valeur"] > 0).sum())),
                cell_titre(q["df"].iloc[0]["nom"], q["df"].iloc[0]["ticker"], fmt_pct(q["df"].iloc[0]["poids"])),
                str((q["df"]["statut"] == "Nouvelle").sum()), str((q["df"]["statut"] == "Soldée").sum()),
                esc(trimestre(q["periode"]))] for q in ordre])


# ================================================================
# ÉLUS AMÉRICAINS
# ================================================================
with t_elus:
    titre_page("Élus américains",
               "Sénateurs et représentants doivent déclarer sous 45 jours chaque transaction personnelle, "
               "sur n'importe quel titre. Les montants sont publiés par tranches.")
    if CONGRES.empty:
        st.html('<div class="empty">Données du Congrès indisponibles pour le moment (quota de la source atteint).</div>')
    else:
        achats = CONGRES[CONGRES["sens"] == "Achat"]
        kpis([
            ("Transactions", fmt_int(len(CONGRES)), "dernières déclarations"),
            ("Élus actifs", str(CONGRES["member"].nunique()), "sur la période"),
            ("Achats", fmt_pct(100 * len(achats) / len(CONGRES), dec=0), f"{len(achats)} opérations"),
            ("Volume estimé", fmt_usd(CONGRES["montant"].sum()), "milieu des tranches"),
        ])
        c1, c2, _ = st.columns([2, 2, 1])
        with c1:
            membres = ["Tous les élus"] + sorted(CONGRES["member"].unique())
            m = st.selectbox("Élu", membres)
        with c2:
            sens = st.segmented_control("Sens", ["Tout", "Achats", "Ventes"], default="Tout",
                                        key="sens_elus") or "Tout"
        sel = CONGRES
        if m != "Tous les élus":
            sel = sel[sel["member"] == m]
        if sens != "Tout":
            sel = sel[sel["sens"] == sens[:-1]]
        section("Transactions", f"{len(sel)} lignes")
        table(COLS_CONGRES, lignes_congres(sel.head(100)), "Aucune transaction pour ce filtre.")
        st.html('<div class="note">« Perf. depuis » : évolution du cours entre la date de transaction et la '
                'dernière clôture.' + (' Dernières données en cache : la source limite le nombre de requêtes '
                                       'quotidiennes.' if CONGRES_SRC == "cache" else "") + '</div>')


# ================================================================
# DIRIGEANTS
# ================================================================
with t_dir:
    titre_page("Dirigeants",
               "Achats et ventes sur le marché des dirigeants et administrateurs, sur les titres de leur propre "
               "société. Attributions gratuites et exercices d'options sont exclus.")
    if not FINNHUB_KEY:
        st.html('<div class="empty">Ajoutez <b>FINNHUB_API_KEY</b> dans les Secrets Streamlit pour activer '
                'cette section. Le reste du site fonctionne sans clé.</div>')
    else:
        DIR = charger_dirigeants(FINNHUB_KEY)
        if DIR.empty:
            st.html('<div class="empty">Aucune transaction sur les 90 derniers jours.</div>')
        else:
            ach, ven = DIR[DIR["sens"] == "Achat"], DIR[DIR["sens"] == "Vente"]
            kpis([
                ("Transactions", fmt_int(len(DIR)), "90 derniers jours"),
                ("Achats", fmt_usd(ach["montant"].sum()), f"{len(ach)} opérations"),
                ("Ventes", fmt_usd(ven["montant"].sum()), f"{len(ven)} opérations"),
                ("Sociétés", str(DIR["symbol"].nunique()), f"sur {len(WATCHLIST)} suivies"),
            ])
            c1, c2, _ = st.columns([2, 2, 1])
            with c1:
                soc = st.selectbox("Société", ["Toutes"] + sorted(DIR["symbol"].unique()),
                                   format_func=lambda s: s if s == "Toutes" else f"{WATCHLIST.get(s, s)} ({s})")
            with c2:
                sens_d = st.segmented_control("Sens", ["Tout", "Achats", "Ventes"], default="Tout",
                                              key="sens_dir") or "Tout"
            sel = DIR if soc == "Toutes" else DIR[DIR["symbol"] == soc]
            if sens_d != "Tout":
                sel = sel[sel["sens"] == sens_d[:-1]]
            sel = sel.sort_values("montant", ascending=False)
            section("Transactions", f"{len(sel)} lignes · classées par montant")
            table(COLS_DIRIGEANTS, lignes_dirigeants(sel.head(80)), "Aucune transaction pour ce filtre.")


# ================================================================
# PAR TITRE
# ================================================================
with t_titre:
    titre_page("Par titre", "Qui détient une action, qui l'achète et qui la vend, toutes sources confondues.")
    c_q, _ = st.columns([2, 3])
    with c_q:
        q = st.text_input("Ticker ou nom de société", value="NVDA", placeholder="NVDA, Apple, Occidental…").strip()
    if q:
        qu = q.upper()
        if not POS.empty:
            m = (POS["ticker"] == qu) | POS["nom"].str.upper().str.contains(qu, regex=False) \
                | POS["emetteur"].str.upper().str.contains(qu, regex=False)
            if (POS["ticker"] == qu).any():  # un ticker exact prime sur la recherche par nom
                m = POS["ticker"] == qu
            det = POS[m].sort_values("valeur", ascending=False)
        else:
            det = pd.DataFrame()
        section("Chez les investisseurs suivis", f"{len(det)} lignes")
        table([("Investisseur", ""), ("Titre", ""), ("Valeur", "num r"), ("Poids du portefeuille", "num r"),
               ("Mouvement", "")],
              [[cell_titre(r["inv"], sous=PF[r["inv_cle"]]["fonds"]),
                cell_titre(r["nom"], r["ticker"], r["pc"] and f"Option {r['pc'].lower()}"),
                esc(fmt_usd(r["valeur"] if r["valeur"] else r["valeur_prec"])), esc(fmt_pct(r["poids"])),
                cell_var(r)] for _, r in det.head(40).iterrows()],
              f"Aucun investisseur suivi ne déclare de position correspondant à « {q} ».")

        if not CONGRES.empty:
            mc = (CONGRES["ticker"].str.upper() == qu) | CONGRES["asset"].str.upper().str.contains(qu, regex=False)
            section("Au Congrès", f"{int(mc.sum())} transactions")
            table(COLS_CONGRES, lignes_congres(CONGRES[mc].head(30)),
                  f"Aucune transaction récente d'élu sur « {q} ».")

        if FINNHUB_KEY and re.fullmatch(r"[A-Z.\-]{1,6}", qu):
            ins = fetch_insider_tx(qu, FINNHUB_KEY)
            section("Dirigeants de la société", f"{len(ins)} transactions · 90 jours")
            table(COLS_DIRIGEANTS, lignes_dirigeants(ins.head(30)),
                  "Aucun achat ni vente de dirigeant sur 90 jours.")


st.html(
    '<div class="foot">Sources : SEC EDGAR (formulaires 13F et 4), déclarations du Congrès des États-Unis '
    '(STOCK Act, via Bargo), Finnhub. Données déclaratives publiées avec retard. '
    'Outil d\'information, ne constitue pas un conseil en investissement.</div>'
)
