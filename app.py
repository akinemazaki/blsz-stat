"""BLSZ statisztika online viewer - Streamlit app.

Futtatas lokalisan:    streamlit run app.py
Streamlit Cloud:       push GitHub-ra, deploy app.py-t
"""
import streamlit as st
import pandas as pd
from pathlib import Path

st.set_page_config(page_title="BLSZ Statisztika", layout="wide", page_icon="⚽")

XLSX = Path(__file__).parent / "blsz_stat.xlsx"


@st.cache_data
def load_sheets(path, mtime):
    """Beolvas minden lapot az xlsx-bol egy dict-be.
    A mtime parameter cache-buster: ha a fajl frissult, uj cache-key lesz."""
    return pd.read_excel(path, sheet_name=None, engine="openpyxl")


if not XLSX.exists():
    st.error(f"Hianyzo fajl: {XLSX.name}. Masold ide a friss xlsx-et.")
    st.stop()

sheets = load_sheets(XLSX, XLSX.stat().st_mtime)
sheet_names = list(sheets.keys())

# Lapok kategorizalva: tabella vs stats
tabella_sheets = [n for n in sheet_names if n.startswith("tabella_")]
stats_sheets = [n for n in sheet_names if n.startswith("stats_")]

# Sidebar
st.sidebar.title("⚽ BLSZ Statisztika")
view = st.sidebar.radio(
    "Nézet",
    ["Tabella", "Játékos statisztika"],
)

# Letoltes link a teljes xlsx-hez
with open(XLSX, "rb") as _f:
    st.sidebar.download_button(
        label="📥 Teljes xlsx letöltése",
        data=_f.read(),
        file_name=XLSX.name,
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        use_container_width=True,
    )

if view == "Tabella":
    if not tabella_sheets:
        st.warning("Nincs tabella lap.")
        st.stop()
    selected = st.sidebar.selectbox("Liga", tabella_sheets)
    df = sheets[selected]
    st.title(selected.replace("tabella_", "Tabella – ").replace("_", " "))
    st.dataframe(df, use_container_width=True, height=720, hide_index=True)
    st.caption(f"{len(df)} sor")

else:  # Játékos statisztika
    if not stats_sheets:
        st.warning("Nincs stats lap.")
        st.stop()
    selected = st.sidebar.selectbox("Liga", stats_sheets)
    df = sheets[selected].copy()
    st.title(selected.replace("stats_", "Statisztika – ").replace("_", " "))

    # Szuro: csapat
    if "team" in df.columns:
        teams = sorted(df["team"].dropna().astype(str).unique())
        selected_teams = st.sidebar.multiselect(
            "Csapat", teams, default=teams,
        )
        df = df[df["team"].astype(str).isin(selected_teams)]

    # Kereso: jatekos nev
    if "player" in df.columns:
        search = st.sidebar.text_input("Keresés (név)")
        if search:
            df = df[df["player"].astype(str).str.contains(search, case=False, na=False)]

    # Csak akt jatekosok kapcsolo
    if "akt/last" in df.columns:
        only_akt = st.sidebar.checkbox("Csak aktív (akt = igen)", value=False)
        if only_akt:
            df = df[df["akt/last"].astype(str).str.startswith("igen")]

    # Oszlop-config: szukebb link, kek alahuzott; team es player rogzitve a bal oldalon.
    column_config = {}
    if "link" in df.columns:
        column_config["link"] = st.column_config.LinkColumn(
            "MLSZ",
            help="Játékos MLSZ adatbank oldala",
            display_text="↗",
            width="small",
            pinned=True,
        )
    if "team" in df.columns:
        column_config["team"] = st.column_config.Column("team", pinned=True)
    if "player" in df.columns:
        column_config["player"] = st.column_config.Column("player", pinned=True)

    st.dataframe(
        df,
        use_container_width=True,
        height=720,
        hide_index=True,
        column_config=column_config,
    )
    st.caption(f"{len(df)} sor")
