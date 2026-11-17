import os
from datetime import date
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st
from sqlalchemy import create_engine, text
from sqlalchemy.engine import URL
from pipeline.config import settings

st.set_page_config(page_title="Cambridge Crime Intelligence", page_icon="📊", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Space+Grotesk:wght@500;600;700&display=swap');
html, body, [class*="css"] {font-family:'DM Sans',sans-serif}
.stApp {background:radial-gradient(circle at 85% 0%,rgba(49,130,206,.10),transparent 28%),linear-gradient(180deg,#0b1220 0%,#0e1728 100%);color:#e8eef8}
[data-testid="stHeader"] {background:rgba(11,18,32,.75)}
[data-testid="stSidebar"] {background:#101b2d;border-right:1px solid rgba(148,163,184,.14)}
[data-testid="stSidebar"] * {color:#dce6f5}
h1,h2,h3 {font-family:'Space Grotesk',sans-serif!important;color:#f4f7fb;letter-spacing:-.03em}
h1 {font-size:2.3rem!important}
p,label,.stCaption {color:#a9b8cc}
.hero {padding:1.55rem 1.8rem;border:1px solid rgba(148,163,184,.2);border-radius:20px;background:linear-gradient(120deg,#172b46,#0f1d31);margin:.4rem 0 1.35rem;box-shadow:0 18px 55px rgba(0,0,0,.18)}
.eyebrow {color:#75c8ff;font-size:.72rem;font-weight:700;letter-spacing:.16em;text-transform:uppercase}
.hero-subtitle {color:#b4c3d7;margin-top:.4rem}
.metric-card {background:linear-gradient(145deg,#17263b,#132034);border:1px solid rgba(148,163,184,.16);border-radius:16px;padding:1rem 1.15rem;min-height:108px}
.metric-label {color:#9fb0c6;font-size:.78rem;font-weight:700;letter-spacing:.06em}
.metric-value {color:#f5f8fc;font-family:'Space Grotesk',sans-serif;font-size:1.8rem;font-weight:700;margin-top:.35rem}
.section-note {color:#91a4bd;font-size:.86rem;margin-top:-.5rem;margin-bottom:.8rem}
div[data-testid="stPlotlyChart"] {background:rgba(19,32,52,.72);border:1px solid rgba(148,163,184,.13);border-radius:16px;padding:.4rem}
.stButton>button,.stDownloadButton>button {border-radius:10px;border:1px solid rgba(90,176,255,.45);background:linear-gradient(100deg,#1676c5,#2457b7);color:white;font-weight:700;min-height:2.55rem}
.stButton>button:hover,.stDownloadButton>button:hover {color:white;border-color:#8acbff}
hr {border-color:rgba(148,163,184,.16)}
</style>
""", unsafe_allow_html=True)

@st.cache_resource
def get_engine():
    if settings.database_type == "sqlite":
        db_path = Path(settings.sqlite_path)
        db_path.parent.mkdir(parents=True, exist_ok=True)
        return create_engine(f"sqlite:///{db_path.as_posix()}", connect_args={"check_same_thread": False})
    url = URL.create(
        drivername="postgresql+psycopg2",
        username=settings.db_user,
        password=settings.db_password,
        host=settings.db_host,
        port=settings.db_port,
        database=settings.db_name,
    )
    return create_engine(url, pool_pre_ping=True)

@st.cache_data(ttl=300)
def load_data():
    query = text("""
        SELECT date_time AS incident_datetime, type AS incident_type,
               subtype AS incident_subtype, location, day_of_week, hour
        FROM cpd_incidents
        WHERE date_time IS NOT NULL
        ORDER BY date_time DESC
    """)
    with get_engine().connect() as conn:
        data = pd.read_sql(query, conn)
    data["incident_datetime"] = pd.to_datetime(data["incident_datetime"], errors="coerce")
    for col in ["incident_type", "incident_subtype", "location", "day_of_week"]:
        data[col] = data[col].fillna("Unknown")
    data["hour"] = pd.to_numeric(data["hour"], errors="coerce")
    data = data.dropna(subset=["incident_datetime"]).copy()
    data["incident_date"] = data["incident_datetime"].dt.date
    return data

def trigger_prefect():
    # timeout=0 submits the deployment run and returns without waiting for completion.
    from prefect.deployments import run_deployment
    deployment = os.getenv("PREFECT_DEPLOYMENT_NAME", "Cambridge Crime Monitoring Pipeline/daily-crime-monitor")
    return run_deployment(name=deployment, timeout=0)

def metric(label, value, color):
    st.markdown(f'<div class="metric-card"><div class="metric-label">{label}</div><div class="metric-value" style="color:{color}">{value}</div></div>', unsafe_allow_html=True)

def polish(fig):
    fig.update_layout(template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                      font=dict(family="DM Sans", color="#c6d3e3"), margin=dict(l=18,r=18,t=25,b=18),
                      hoverlabel=dict(bgcolor="#17263b", bordercolor="#42617f"))
    fig.update_xaxes(showgrid=True, gridcolor="rgba(148,163,184,.12)", zeroline=False)
    fig.update_yaxes(showgrid=True, gridcolor="rgba(148,163,184,.12)", zeroline=False)
    return fig

st.markdown('''<div class="hero"><div class="eyebrow">PUBLIC SAFETY · DATA INTELLIGENCE</div><h1>Cambridge Crime Intelligence</h1><div class="hero-subtitle">Explore incident patterns, monitor reporting activity, and launch the data pipeline from one workspace.</div></div>''', unsafe_allow_html=True)

# Sidebar actions
st.sidebar.title("Control centre")
st.sidebar.caption("Database and pipeline controls")
st.sidebar.markdown(f"**Connected database:** `{settings.database_type.upper()}`")
if st.sidebar.button("↻ Refresh dashboard data", use_container_width=True):
    load_data.clear()
    st.rerun()
st.sidebar.divider()
st.sidebar.markdown("**Prefect pipeline**")
st.sidebar.caption("Submit a run of the registered deployment. It runs in the background.")

from pipeline.flow import crime_pipeline

if st.sidebar.button("▶ Run pipeline now", use_container_width=True):
    try:
        with st.spinner("Running crime pipeline..."):
            flow_run = crime_pipeline()

        st.sidebar.success("Pipeline completed successfully!")
        st.sidebar.write(f"Flow run ID: {flow_run}")

        load_data.clear()
        st.rerun()

    except Exception as exc:
        st.sidebar.error("Pipeline execution failed.")
        st.sidebar.exception(exc)
        
if st.session_state.get("last_prefect_run_id"):
    st.sidebar.caption("Most recently submitted run")
    st.sidebar.code(st.session_state["last_prefect_run_id"], language=None)
prefect_ui = os.getenv("PREFECT_UI_URL", "http://localhost:4200").rstrip("/")
st.sidebar.markdown(f"[Open Prefect UI ↗]({prefect_ui})")
st.sidebar.divider()
st.sidebar.caption("Source: Cambridge Police Department Daily Log")

try:
    df = load_data()
except Exception as exc:
    st.error(f"Unable to load data from the configured {settings.database_type.upper()} database.")
    st.exception(exc)
    st.stop()
if df.empty:
    st.warning("The database query returned no usable incident records. Check the table and date_time values.")
    st.stop()

# Filters
st.subheader("Explore incidents")
st.markdown('<div class="section-note">Filter by reporting period, incident category, or location.</div>', unsafe_allow_html=True)
min_date, max_date = df["incident_datetime"].min().date(), df["incident_datetime"].max().date()
default_end = min(max_date, date.today()) if min_date <= date.today() else max_date
f1, f2, f3 = st.columns([1.25,1,1])
with f1:
    date_range = st.date_input("Incident date range", value=(min_date, default_end), min_value=min_date, max_value=max_date)
with f2:
    types = sorted(df["incident_type"].unique().tolist())
    selected_types = st.multiselect("Incident categories", types, default=types)
with f3:
    locations = sorted(df["location"].unique().tolist())
    selected_locations = st.multiselect("Locations", locations)

filtered = df[df["incident_type"].isin(selected_types)].copy()
if selected_locations:
    filtered = filtered[filtered["location"].isin(selected_locations)]
if isinstance(date_range, (tuple,list)) and len(date_range) == 2:
    start_date, end_date = date_range
    if start_date and end_date:
        filtered = filtered[filtered["incident_datetime"].dt.date.between(start_date, end_date)]
if filtered.empty:
    st.warning("No incidents match these filters. Widen the date range or clear a filter.")
    st.stop()

# KPIs
st.subheader("At a glance")
total = len(filtered)
days = max(filtered["incident_date"].nunique(), 1)
k1,k2,k3,k4 = st.columns(4)
with k1: metric("TOTAL INCIDENTS", f"{total:,}", "#75c8ff")
with k2: metric("INCIDENT CATEGORIES", f"{filtered['incident_type'].nunique():,}", "#a78bfa")
with k3: metric("REPORTED LOCATIONS", f"{filtered['location'].nunique():,}", "#34d399")
with k4: metric("DAILY AVERAGE", f"{total/days:.1f}", "#fbbf24")
st.divider()

# Monthly and category charts
st.subheader("Incident trends")
left,right = st.columns([1.5,1])
with left:
    st.markdown("**Monthly incident volume**")
    monthly = filtered.set_index("incident_datetime").resample("MS").size().reset_index(name="incidents")
    fig = px.area(monthly, x="incident_datetime", y="incidents", markers=True,
                  labels={"incident_datetime":"Month","incidents":"Incidents"})
    fig.update_traces(line=dict(color="#56b4f5",width=3), fillcolor="rgba(56,145,220,.16)", marker=dict(size=7))
    fig.update_layout(hovermode="x unified")
    st.plotly_chart(polish(fig), use_container_width=True)
with right:
    st.markdown("**Most common incident types**")
    counts = filtered["incident_type"].value_counts().head(10).sort_values().rename_axis("type").reset_index(name="incidents")
    fig = px.bar(counts, x="incidents", y="type", orientation="h", labels={"type":"Incident type","incidents":"Incidents"})
    fig.update_traces(marker_color="#7c8cf8", marker_line_width=0)
    st.plotly_chart(polish(fig), use_container_width=True)

left,right = st.columns(2)
with left:
    st.markdown("**Top incident subtypes**")
    counts = filtered["incident_subtype"].value_counts().head(10).sort_values().rename_axis("subtype").reset_index(name="incidents")
    fig = px.bar(counts, x="incidents", y="subtype", orientation="h", labels={"subtype":"Subtype","incidents":"Incidents"})
    fig.update_traces(marker_color="#39bfa4", marker_line_width=0)
    st.plotly_chart(polish(fig), use_container_width=True)
with right:
    st.markdown("**Incidents by day of week**")
    order = ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"]
    counts = filtered["day_of_week"].value_counts().reindex(order,fill_value=0).rename_axis("day").reset_index(name="incidents")
    fig = px.bar(counts, x="day", y="incidents", labels={"day":"Day","incidents":"Incidents"})
    fig.update_traces(marker_color="#e6a34a", marker_line_width=0)
    st.plotly_chart(polish(fig), use_container_width=True)

left,right = st.columns(2)
with left:
    st.markdown("**Incidents by hour**")
    counts = filtered.dropna(subset=["hour"]).groupby("hour").size().reset_index(name="incidents").sort_values("hour")
    fig = px.bar(counts, x="hour", y="incidents", labels={"hour":"Hour of day","incidents":"Incidents"})
    fig.update_traces(marker_color="#4ea6d8", marker_line_width=0)
    fig.update_xaxes(dtick=1)
    st.plotly_chart(polish(fig), use_container_width=True)
with right:
    st.markdown("**Top reported locations**")
    counts = filtered["location"].value_counts().head(10).sort_values().rename_axis("location").reset_index(name="incidents")
    fig = px.bar(counts, x="incidents", y="location", orientation="h", labels={"location":"Location","incidents":"Incidents"})
    fig.update_traces(marker_color="#b17ce8", marker_line_width=0)
    st.plotly_chart(polish(fig), use_container_width=True)

# Records
st.divider()
st.subheader("Incident records")
display = filtered.sort_values("incident_datetime",ascending=False).copy()
display["incident_datetime"] = display["incident_datetime"].dt.strftime("%Y-%m-%d %H:%M")
cols = ["incident_datetime","incident_type","incident_subtype","location","day_of_week","hour"]
d1,d2 = st.columns([4,1])
with d1: st.caption(f"{len(display):,} matching records")
with d2:
    st.download_button("↓ Download CSV", data=display[cols].to_csv(index=False).encode("utf-8"),
                       file_name="cambridge_crime_incidents.csv", mime="text/csv", use_container_width=True)
st.dataframe(display[cols], use_container_width=True, hide_index=True, height=420)
st.caption(f"Cambridge Police Department Daily Log · {settings.database_type.upper()} · Dashboard cache: 5 minutes")
