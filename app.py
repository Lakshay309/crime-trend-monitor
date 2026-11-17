
import os
from pathlib import Path
from datetime import date

import pandas as pd
import plotly.express as px
import streamlit as st

from sqlalchemy import create_engine, text
from sqlalchemy.engine import URL

from pipeline.config import settings


st.set_page_config(
    page_title="Cambridge Crime Trends",
    page_icon="📊",
    layout="wide",
)

st.title("Cambridge Crime Trends")
st.caption(
    "Crime incident monitoring and trend analysis — "
    "Cambridge, Massachusetts"
)


@st.cache_resource
def get_engine():
    """Create an engine for the configured database."""

    if settings.database_type == "sqlite":
        db_path = Path(settings.sqlite_path)
        db_path.parent.mkdir(parents=True, exist_ok=True)

        database_url = f"sqlite:///{db_path.as_posix()}"

        return create_engine(
            database_url,
            connect_args={"check_same_thread": False},
        )

    database_url = URL.create(
        drivername="postgresql+psycopg2",
        username=settings.db_user,
        password=settings.db_password,
        host=settings.db_host,
        port=settings.db_port,
        database=os.getenv("DB_NAME", settings.db_name),
    )

    return create_engine(
        database_url,
        pool_pre_ping=True,
    )


@st.cache_data(ttl=300)
def load_data():
    """Load incident records from the configured database."""

    query = text("""
        SELECT
            date_time AS incident_datetime,
            type AS incident_type,
            subtype AS incident_subtype,
            location,
            day_of_week,
            hour
        FROM cpd_incidents
        WHERE date_time IS NOT NULL
        ORDER BY date_time DESC
    """)

    with get_engine().connect() as connection:
        df = pd.read_sql(query, connection)

    df["incident_datetime"] = pd.to_datetime(
        df["incident_datetime"], errors="coerce"
    )

    df["incident_type"] = df["incident_type"].fillna("Unknown")
    df["incident_subtype"] = df["incident_subtype"].fillna("Unknown")
    df["location"] = df["location"].fillna("Unknown")
    df["hour"] = pd.to_numeric(df["hour"], errors="coerce")

    df = df.dropna(subset=["incident_datetime"])
    df["incident_date"] = df["incident_datetime"].dt.date

    return df


try:
    df = load_data()

except Exception as exc:
    st.error(
        f"Could not load crime data from "
        f"{settings.database_type.upper()}."
    )
    st.exception(exc)
    st.stop()


if df.empty:
    st.warning("No incident records are available.")
    st.stop()


# Sidebar filters
st.sidebar.header("Dashboard Filters")

today = date.today()

min_date = df["incident_datetime"].min().date()
max_date = today

date_range = st.sidebar.date_input(
    "Incident date range",
    value=(min_date, max_date),
    min_value=min_date,
    max_value=max_date,
)

types = sorted(df["incident_type"].unique().tolist())

selected_types = st.sidebar.multiselect(
    "Incident type",
    types,
    default=types,
)

locations = sorted(df["location"].unique().tolist())

selected_locations = st.sidebar.multiselect(
    "Location",
    locations,
)

filtered = df[
    df["incident_type"].isin(selected_types)
].copy()

if selected_locations:
    filtered = filtered[
        filtered["location"].isin(selected_locations)
    ]

if isinstance(date_range, (tuple, list)) and len(date_range) == 2:
    start_date, end_date = date_range

    filtered = filtered[
        (filtered["incident_datetime"].dt.date >= start_date)
        & (filtered["incident_datetime"].dt.date <= end_date)
    ]

if filtered.empty:
    st.warning("No incidents match the selected filters.")
    st.stop()


# KPI cards
total = len(filtered)
unique_types = filtered["incident_type"].nunique()
unique_locations = filtered["location"].nunique()

average_daily = (
    total / max(filtered["incident_date"].nunique(), 1)
)

col1, col2, col3, col4 = st.columns(4)

col1.metric("Total incidents", f"{total:,}")
col2.metric("Incident categories", f"{unique_types:,}")
col3.metric("Reported locations", f"{unique_locations:,}")
col4.metric("Average incidents/day", f"{average_daily:.1f}")

st.divider()


# Monthly trend
st.subheader("Monthly Crime Trends")

monthly = (
    filtered.set_index("incident_datetime")
    .resample("MS")
    .size()
    .reset_index(name="incidents")
)

fig_monthly = px.line(
    monthly,
    x="incident_datetime",
    y="incidents",
    markers=True,
    labels={
        "incident_datetime": "Month",
        "incidents": "Number of incidents",
    },
)

fig_monthly.update_layout(hovermode="x unified")

st.plotly_chart(fig_monthly, use_container_width=True)


# Category and subtype charts
left, right = st.columns(2)

with left:
    st.subheader("Most Common Incident Types")

    type_counts = (
        filtered["incident_type"]
        .value_counts()
        .head(10)
        .sort_values()
        .reset_index()
    )

    type_counts.columns = ["type", "incidents"]

    fig_types = px.bar(
        type_counts,
        x="incidents",
        y="type",
        orientation="h",
        labels={
            "type": "Incident type",
            "incidents": "Incidents",
        },
    )

    st.plotly_chart(fig_types, use_container_width=True)


with right:
    st.subheader("Top Crime Subtypes")

    subtype_counts = (
        filtered["incident_subtype"]
        .value_counts()
        .head(10)
        .sort_values()
        .reset_index()
    )

    subtype_counts.columns = ["subtype", "incidents"]

    fig_subtypes = px.bar(
        subtype_counts,
        x="incidents",
        y="subtype",
        orientation="h",
        labels={
            "subtype": "Subtype",
            "incidents": "Incidents",
        },
    )

    st.plotly_chart(fig_subtypes, use_container_width=True)


# Day and hour analysis
left, right = st.columns(2)

with left:
    st.subheader("Incidents by Day of Week")

    day_order = [
        "Monday",
        "Tuesday",
        "Wednesday",
        "Thursday",
        "Friday",
        "Saturday",
        "Sunday",
    ]

    day_counts = (
        filtered["day_of_week"]
        .value_counts()
        .reindex(day_order, fill_value=0)
        .rename_axis("day")
        .reset_index(name="incidents")
    )

    fig_days = px.bar(
        day_counts,
        x="day",
        y="incidents",
        labels={
            "day": "Day",
            "incidents": "Incidents",
        },
    )

    st.plotly_chart(fig_days, use_container_width=True)


with right:
    st.subheader("Incidents by Hour")

    hourly = (
        filtered.groupby("hour")
        .size()
        .reset_index(name="incidents")
        .dropna(subset=["hour"])
    )

    fig_hours = px.bar(
        hourly,
        x="hour",
        y="incidents",
        labels={
            "hour": "Hour of day",
            "incidents": "Incidents",
        },
    )

    fig_hours.update_xaxes(dtick=1)

    st.plotly_chart(fig_hours, use_container_width=True)


# Location analysis
st.subheader("Top Incident Locations")

top_locations = (
    filtered["location"]
    .value_counts()
    .head(10)
    .sort_values()
    .reset_index()
)

top_locations.columns = ["location", "incidents"]

fig_locations = px.bar(
    top_locations,
    x="incidents",
    y="location",
    orientation="h",
    labels={
        "location": "Location",
        "incidents": "Incidents",
    },
)

st.plotly_chart(fig_locations, use_container_width=True)


# Data table and download
st.subheader("Incident Records")

display_df = filtered.sort_values(
    "incident_datetime",
    ascending=False,
).copy()

display_df["incident_datetime"] = (
    display_df["incident_datetime"].dt.strftime("%Y-%m-%d %H:%M")
)

st.dataframe(
    display_df[
        [
            "incident_datetime",
            "incident_type",
            "incident_subtype",
            "location",
            "day_of_week",
            "hour",
        ]
    ],
    use_container_width=True,
    hide_index=True,
)

st.download_button(
    "Download filtered incidents as CSV",
    data=display_df.to_csv(index=False).encode("utf-8"),
    file_name="cambridge_crime_incidents.csv",
    mime="text/csv",
)

st.caption("Data source: Cambridge Police Department Daily Log.")
