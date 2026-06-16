"""
Tennis Performance Explorer — Phase 1
A free, open-source data app (Streamlit + pandas + Plotly).

Data: Jeff Sackmann / Tennis Abstract (CC BY-NC-SA 4.0).
https://github.com/JeffSackmann/tennis_atp  &  /tennis_wta
Non-commercial, attribution required. See README.
"""

import io
import pandas as pd
import requests
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go

HEADERS = {"User-Agent": "Mozilla/5.0 (tennis-analytics portfolio app)"}

# --------------------------------------------------------------------------- #
# Page config
# --------------------------------------------------------------------------- #
st.set_page_config(
    page_title="Tennis Performance Explorer",
    page_icon="🎾",
    layout="wide",
)

# Palette grounded in the real surfaces (the signature of the dashboard)
SURFACE_COLORS = {
    "Clay": "#C66B3D",    # terracotta
    "Grass": "#4E8C5A",   # court green
    "Hard": "#2E6DB4",    # hard-court blue
    "Carpet": "#8A6FB0",
    "Unknown": "#9AA0A6",
}
ACCENT = "#A8C84A"  # tennis-ball chartreuse, used sparingly

TOURS = {
    "ATP (men)": {"repo": "tennis_atp", "prefix": "atp_matches_", "default": "Carlos Alcaraz"},
    "WTA (women)": {"repo": "tennis_wta", "prefix": "wta_matches_", "default": "Iga Swiatek"},
}

# The same public GitHub data, via several mirrors. raw.githubusercontent.com
# rate-limits shared cloud IPs (like Streamlit Cloud) and 404s, so we prefer
# CDNs that mirror GitHub. We try each source in order until one responds.
DATA_SOURCES = [
    "https://cdn.jsdelivr.net/gh/JeffSackmann/{repo}@master/{prefix}{year}.csv",
    "https://cdn.statically.io/gh/JeffSackmann/{repo}/master/{prefix}{year}.csv",
    "https://raw.githubusercontent.com/JeffSackmann/{repo}/refs/heads/master/{prefix}{year}.csv",
]
YEARS = tuple(range(2018, 2025))  # 2018–2024 (widen here if you want more history)
MIN_MATCHES = 20  # only show players with at least this many matches in the dropdown

# Light, intentional styling (one signature, kept restrained)
st.markdown(
    """
    <style>
      .block-container {padding-top: 2.2rem;}
      h1 {font-weight: 800; letter-spacing: -0.5px;}
      .lead {color: #5f6368; font-size: 1.02rem; margin-top: -0.5rem;}
      [data-testid="stMetricValue"] {font-weight: 800;}
      .footer {color:#9AA0A6; font-size:0.8rem; margin-top:2rem;}
    </style>
    """,
    unsafe_allow_html=True,
)

STAT_COLS = ["ace", "df", "svpt", "1stIn", "1stWon", "2ndWon", "SvGms", "bpSaved", "bpFaced"]


# --------------------------------------------------------------------------- #
# Data loading (tries several mirrors per file)
# --------------------------------------------------------------------------- #
@st.cache_data(show_spinner=True, ttl=60 * 60 * 24)
def load_matches(repo: str, prefix: str, years: tuple):
    frames, errors = [], []
    for y in years:
        df_year, last_err = None, None
        for template in DATA_SOURCES:
            url = template.format(repo=repo, prefix=prefix, year=y)
            try:
                resp = requests.get(url, headers=HEADERS, timeout=30)
                resp.raise_for_status()
                df_year = pd.read_csv(io.StringIO(resp.text))
                break  # this mirror worked, stop trying others for this year
            except Exception as e:
                last_err = f"{type(e).__name__} — {e}"
                continue
        if df_year is not None:
            df_year["season"] = y
            frames.append(df_year)
        else:
            errors.append(f"{y}: all sources failed ({last_err})")

    if not frames:
        return pd.DataFrame(), errors

    data = pd.concat(frames, ignore_index=True)
    data["surface"] = data["surface"].fillna("Unknown").astype(str).str.title()
    data["surface"] = data["surface"].where(data["surface"].isin(SURFACE_COLORS), "Unknown")
    data["match_date"] = pd.to_datetime(
        data["tourney_date"].astype("Int64").astype(str), format="%Y%m%d", errors="coerce"
    )
    for col in [f"w_{s}" for s in STAT_COLS] + [f"l_{s}" for s in STAT_COLS] + [
        "winner_rank", "loser_rank",
    ]:
        if col in data.columns:
            data[col] = pd.to_numeric(data[col], errors="coerce")
    return data, errors


@st.cache_data(show_spinner=False)
def eligible_players(data: pd.DataFrame, min_matches: int) -> list:
    counts = pd.concat([data["winner_name"], data["loser_name"]]).value_counts()
    return sorted(counts[counts >= min_matches].index.tolist())


@st.cache_data(show_spinner=False)
def player_view(data: pd.DataFrame, player: str) -> pd.DataFrame:
    """All of a player's matches, normalised to that player's point of view."""
    wins = data[data["winner_name"] == player].copy()
    losses = data[data["loser_name"] == player].copy()

    wins["won"], losses["won"] = 1, 0
    wins["opponent"] = wins["loser_name"]
    losses["opponent"] = losses["winner_name"]
    wins["player_rank"] = wins["winner_rank"]
    losses["player_rank"] = losses["loser_rank"]

    for s in STAT_COLS:
        wins[f"p_{s}"] = wins.get(f"w_{s}")
        losses[f"p_{s}"] = losses.get(f"l_{s}")

    keep = ["match_date", "season", "surface", "tourney_name", "round",
            "opponent", "won", "player_rank"] + [f"p_{s}" for s in STAT_COLS]
    out = pd.concat([wins[keep], losses[keep]], ignore_index=True)
    return out.sort_values("match_date").reset_index(drop=True)


# --------------------------------------------------------------------------- #
# Header + controls
# --------------------------------------------------------------------------- #
st.title("🎾 Tennis Performance Explorer")
st.markdown(
    '<p class="lead">How players really perform — broken down by surface, '
    "season and opponent. Built on public ATP/WTA data.</p>",
    unsafe_allow_html=True,
)

with st.sidebar:
    st.header("Filters")
    tour_name = st.radio("Tour", list(TOURS.keys()))
    tour = TOURS[tour_name]

data, load_errors = load_matches(tour["repo"], tour["prefix"], YEARS)

if data.empty:
    st.error("Couldn't load the match data. Error details below:")
    st.code("\n".join(load_errors) if load_errors else "No data returned.")
    st.stop()

with st.sidebar:
    yr_min, yr_max = st.select_slider(
        "Seasons", options=list(YEARS), value=(YEARS[0], YEARS[-1])
    )
    players = eligible_players(data, MIN_MATCHES)
    default_idx = players.index(tour["default"]) if tour["default"] in players else 0
    player = st.selectbox("Player", players, index=default_idx)

season_mask = (data["season"] >= yr_min) & (data["season"] <= yr_max)
data_f = data[season_mask]
pv = player_view(data_f, player)

if pv.empty:
    st.warning(f"No matches for {player} in {yr_min}–{yr_max}.")
    st.stop()

# --------------------------------------------------------------------------- #
# KPI row
# --------------------------------------------------------------------------- #
total = len(pv)
wins = int(pv["won"].sum())
win_pct = wins / total * 100 if total else 0

by_surface = (
    pv.groupby("surface")["won"].agg(["mean", "count"]).reset_index()
    .rename(columns={"mean": "win_pct", "count": "matches"})
)
by_surface["win_pct"] *= 100
played_surfaces = by_surface[by_surface["matches"] >= 5]
best_surface = (
    played_surfaces.sort_values("win_pct", ascending=False)["surface"].iloc[0]
    if not played_surfaces.empty else "—"
)

c1, c2, c3, c4 = st.columns(4)
c1.metric("Matches", f"{total}")
c2.metric("Win rate", f"{win_pct:.0f}%")
c3.metric("Wins – Losses", f"{wins} – {total - wins}")
c4.metric("Best surface", best_surface)

st.divider()

# --------------------------------------------------------------------------- #
# Win % by surface (the signature chart)  +  ranking over time
# --------------------------------------------------------------------------- #
left, right = st.columns([1, 1])

with left:
    st.subheader("Win rate by surface")
    bs = by_surface.sort_values("win_pct", ascending=False)
    fig = px.bar(
        bs, x="surface", y="win_pct",
        text=bs["win_pct"].round(0).astype(int).astype(str) + "%",
        color="surface", color_discrete_map=SURFACE_COLORS,
    )
    fig.update_traces(textposition="outside", cliponaxis=False)
    fig.update_layout(
        showlegend=False, yaxis_title="Win %", xaxis_title="",
        yaxis_range=[0, 100], height=360, margin=dict(t=10, b=10),
        plot_bgcolor="rgba(0,0,0,0)",
    )
    st.plotly_chart(fig, use_container_width=True)

with right:
    st.subheader("Ranking over time")
    rank_ts = pv.dropna(subset=["player_rank", "match_date"])
    if not rank_ts.empty:
        fig2 = go.Figure(go.Scatter(
            x=rank_ts["match_date"], y=rank_ts["player_rank"],
            mode="lines", line=dict(color=ACCENT, width=2.5),
        ))
        fig2.update_yaxes(autorange="reversed", title="ATP/WTA rank")
        fig2.update_layout(height=360, margin=dict(t=10, b=10),
                           plot_bgcolor="rgba(0,0,0,0)", xaxis_title="")
        st.plotly_chart(fig2, use_container_width=True)
    else:
        st.info("No ranking data in this range.")

# --------------------------------------------------------------------------- #
# Serve profile + Head-to-head
# --------------------------------------------------------------------------- #
left2, right2 = st.columns([1, 1])

with left2:
    st.subheader("Serve profile by surface")
    sp = pv.groupby("surface").agg(ace_per_match=("p_ace", "mean")).reset_index()
    fig3 = px.bar(
        sp, x="surface", y="ace_per_match", color="surface",
        color_discrete_map=SURFACE_COLORS,
        text=sp["ace_per_match"].round(1).astype(str),
    )
    fig3.update_traces(textposition="outside", cliponaxis=False)
    fig3.update_layout(showlegend=False, yaxis_title="Aces / match",
                       xaxis_title="", height=320, margin=dict(t=10, b=10),
                       plot_bgcolor="rgba(0,0,0,0)")
    st.plotly_chart(fig3, use_container_width=True)

with right2:
    st.subheader("Head-to-head")
    opponents = sorted(pv["opponent"].value_counts().index.tolist())
    if opponents:
        opp = st.selectbox("Opponent", opponents)
        h2h = pv[pv["opponent"] == opp]
        w = int(h2h["won"].sum())
        l = len(h2h) - w
        st.metric(f"{player} vs {opp}", f"{w} – {l}")
        st.dataframe(
            h2h[["match_date", "tourney_name", "surface", "round", "won"]]
            .assign(result=lambda d: d["won"].map({1: "Win", 0: "Loss"}))
            .drop(columns="won")
            .sort_values("match_date", ascending=False),
            hide_index=True, use_container_width=True,
        )

# --------------------------------------------------------------------------- #
# Recent matches
# --------------------------------------------------------------------------- #
st.subheader("Recent matches")
recent = (pv.sort_values("match_date", ascending=False)
          .assign(result=lambda d: d["won"].map({1: "Win", 0: "Loss"}))
          [["match_date", "tourney_name", "surface", "round", "opponent", "result"]]
          .head(25))
st.dataframe(recent, hide_index=True, use_container_width=True)

st.markdown(
    '<p class="footer">Data: Jeff Sackmann / Tennis Abstract '
    "(CC BY-NC-SA 4.0). Non-commercial use. "
    "Built with Streamlit · pandas · Plotly.</p>",
    unsafe_allow_html=True,
)
