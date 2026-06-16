# 🎾 Tennis Performance Explorer

An interactive analytics app that breaks down professional tennis performance by
**surface, season and opponent** — built end to end with a free, open-source data stack.

**Live app:** _add your Streamlit Cloud link here once deployed_

![Made with Streamlit](https://img.shields.io/badge/Made%20with-Streamlit-FF4B4B)
![Python](https://img.shields.io/badge/Python-3.11-blue)

## What it shows
- Win rate and record, with the **best surface** surfaced automatically
- **Win % by surface** (clay / grass / hard) — the core view
- Ranking trajectory over time
- Serve profile by surface (aces per match, first-serve rate)
- **Head-to-head** records against any opponent
- Recent match log

## Tech stack
- **Streamlit** — the app / UI layer
- **pandas** — data wrangling and metrics
- **Plotly** — interactive charts

No Power BI, no paid tools — everything here runs on free, open-source software and
deploys for free on Streamlit Community Cloud.

## Run it locally
```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py
```

## Deploy for free
1. Push these files to a public GitHub repo.
2. Go to [share.streamlit.io](https://share.streamlit.io), sign in with GitHub.
3. **New app** → pick this repo and `app.py` → **Deploy**.

## Data & attribution
Match data from **Jeff Sackmann / Tennis Abstract**:
[tennis_atp](https://github.com/JeffSackmann/tennis_atp) and
[tennis_wta](https://github.com/JeffSackmann/tennis_wta).

Licensed under **Creative Commons Attribution-NonCommercial-ShareAlike 4.0**.
This project is **non-commercial** and provided for educational / portfolio purposes,
with attribution as required by the license.
