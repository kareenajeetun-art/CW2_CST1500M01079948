import streamlit as st
st.title("Hello, Streamlit! ")
st.title("This is my very first Streamlip app! ")

# app.py
"""
Streamlit Cybersecurity Operations Dashboard (example)

Features:
 - Dark-ish dashboard layout (Streamlit theme is used)
 - Sidebar filters: date range, severity, refresh button
 - Top metric cards (total alerts, open incidents, MTTD, P1 MTT)
 - Alerts time-series (last 30 days)
 - Alerts by category (bar chart)
 - Geo IP activity map
 - Top malicious IPs table
 - Log stream (simulated recent events)
 - All data is simulated; replace with your real data sources (SIEM / DB / API)
"""

from datetime import datetime, timedelta
import random
import pandas as pd
import numpy as np
import streamlit as st
import plotly.express as px

# -----------------------------
# Helper: Create simulated dataset
# -----------------------------
@st.cache_data
def generate_example_data(seed: int = 42):
    random.seed(seed)
    np.random.seed(seed)

    # Time series: 180 days (6 months) with daily aggregated alert counts
    days = 180
    end_date = datetime.utcnow().date()
    dates = [end_date - timedelta(days=x) for x in range(days - 1, -1, -1)]
    # simulate baseline + weekly seasonality + some spikes
    baseline = 80
    daily_counts = [
        max(
            0,
            int(
                baseline
                + 20 * np.sin(2 * np.pi * (i / 7.0))  # weekly pattern
                + np.random.normal(0, 12)
                + (40 if np.random.random() < 0.02 else 0)  # random spikes
            ),
        )
        for i in range(days)
    ]

    # categories
    categories = ["Malware", "Phishing", "Unauthorized Access", "DDoS", "Data Leak"]
    category_probs = [0.45, 0.20, 0.18, 0.10, 0.07]

    # Build per-alert synthetic table (sample ~ total ~ sum of daily_counts)
    alerts = []
    ip_samples = [
        ("197.188.1.1", -33.9, 18.4),
        ("205.0.113.5", 37.7, -122.4),
        ("185.21.217.9", 55.4, 12.0),
        ("46.33.30.2", 51.5, -0.1),
        ("37.48.225.19", -1.3, 36.8),
        ("8.8.8.8", 37.4, -122.0),
        ("123.45.67.89", 28.6, 77.2),
        ("98.76.54.32", 40.7, -74.0),
    ]
    severities = ["Low", "Medium", "High", "Critical"]
    priority_map = {"Critical": "P0", "High": "P1", "Medium": "P2", "Low": "P3"}

    alert_id = 1
    for date, cnt in zip(dates, daily_counts):
        for _ in range(cnt):
            cat = np.random.choice(categories, p=category_probs)
            sev = np.random.choice(severities, p=[0.4, 0.35, 0.2, 0.05])
            ip, lat, lon = random.choice(ip_samples)
            alerts.append(
                {
                    "alert_id": f"A-{alert_id}",
                    "timestamp": datetime.combine(date, datetime.min.time())
                    + timedelta(
                        seconds=random.randint(0, 86399)
                    ),  # random second during the day
                    "category": cat,
                    "severity": sev,
                    "priority": priority_map[sev],
                    "src_ip": ip,
                    "lat": lat + np.random.normal(0, 0.5),
                    "lon": lon + np.random.normal(0, 0.5),
                    "msg": f"{cat} alert triggered on host {random.randint(1,200)}",
                }
            )
            alert_id += 1

    alerts_df = pd.DataFrame(alerts)
    alerts_df["date"] = alerts_df["timestamp"].dt.date

    # Summary metrics (example calculations)
    total_alerts = len(alerts_df)
    # open incidents: simulate a small percent
    open_incidents = int(total_alerts * 0.028)  # ~2.8% open
    # mean time to detect (hours) (random simulated)
    mttd_hours = round(random.uniform(0.5, 4.0), 2)
    p1_mtt_hours = round(mttd_hours + random.uniform(1.0, 4.0), 2)

    # Top malicious IPs (count by src_ip)
    ip_counts = alerts_df["src_ip"].value_counts().reset_index()
    ip_counts.columns = ["ip_address", "alerts"]
    # attach a lat/lon sample for mapping convenience (use aggregate mean)
    ip_coords = alerts_df.groupby("src_ip")[["lat", "lon"]].mean().reset_index()
    ip_coords.columns = ["ip_address", "lat", "lon"]
    ip_table = ip_counts.merge(ip_coords, on="ip_address").head(10)

    # Log stream: latest 20 alerts (reverse chronological)
    logs_df = (
        alerts_df.sort_values("timestamp", ascending=False)
        .head(20)
        .loc[:, ["timestamp", "src_ip", "category", "severity", "msg"]]
        .reset_index(drop=True)
    )
    logs_df["ts_str"] = logs_df["timestamp"].dt.strftime("%Y-%m-%d %H:%M:%S")

    # Return everything
    return {
        "alerts_df": alerts_df,
        "daily_counts": pd.DataFrame({"date": dates, "alerts": daily_counts}),
        "total_alerts": total_alerts,
        "open_incidents": open_incidents,
        "mttd_hours": mttd_hours,
        "p1_mtt_hours": p1_mtt_hours,
        "ip_table": ip_table,
        "logs_df": logs_df,
        "categories": categories,
    }


# -----------------------------
# Main Dashboard
# -----------------------------
def main():
    st.set_page_config(page_title="Cybersecurity Operations Dashboard", layout="wide")

    # Title
    st.markdown("<h1 style='margin-bottom:0'>🔒 Cybersecurity Operations Dashboard</h1>", unsafe_allow_html=True)

    # Load/generate example data
    data = generate_example_data(seed=42)
    alerts_df = data["alerts_df"]
    daily_counts = data["daily_counts"]
    ip_table = data["ip_table"]
    logs_df = data["logs_df"]

    # Sidebar - Filters
    st.sidebar.header("Filters")
    # Date range picker (default last 90 days)
    min_date = alerts_df["date"].min()
    max_date = alerts_df["date"].max()
    default_start = max_date - timedelta(days=89)
    date_range = st.sidebar.date_input("Date range", value=(default_start, max_date), min_value=min_date, max_value=max_date)
    if isinstance(date_range, tuple) and len(date_range) == 2:
        start_date, end_date = date_range
    else:
        start_date, end_date = default_start, max_date

    # Severity multi-select (checkbox style)
    severity_options = ["Low", "Medium", "High", "Critical"]
    default_selected = ["Medium", "High", "Critical"]
    selected_severity = st.sidebar.multiselect("Severity", options=severity_options, default=default_selected)

    # Refresh button (recompute / rerun)
    if st.sidebar.button("Refresh data"):
        # For demo, just clear cache and rerun — but for real app you'd fetch new data.
        generate_example_data.clear()
        st.experimental_rerun()

    st.sidebar.caption("Demo data: replace generate_example_data() with your real dataset.")

    # Apply filters to the alerts dataset
    filtered = alerts_df[
        (alerts_df["date"] >= start_date)
        & (alerts_df["date"] <= end_date)
        & (alerts_df["severity"].isin(selected_severity))
    ]

    # Top metric cards
    col1, col2, col3, col4 = st.columns(4)
    total_alerts = len(filtered)
    open_incidents = int(total_alerts * 0.03)  # example
    mttd = data["mttd_hours"]
    p1_mtt = data["p1_mtt_hours"]

    col1.metric("Total Alerts", f"{total_alerts:,}")
    col2.metric("Open Incidents", f"{open_incidents:,}")
    col3.metric("Mean Time to Detect (hrs)", f"{mttd} h")
    col4.metric("P1 Mean Time to Respond (hrs)", f"{p1_mtt} h")

    st.markdown("---")

    # Main content: charts and panels
    left_col, middle_col, right_col = st.columns([1.2, 1.2, 0.9])

    # Left: Alerts time-series
    with left_col:
        st.subheader("Alerts (daily)")
        # build daily series from filtered
        daily = (
            filtered.groupby("date")["alert_id"]
            .count()
            .reindex(pd.date_range(start_date, end_date).date, fill_value=0)
            .reset_index()
        )
        daily.columns = ["date", "alerts"]
        fig_ts = px.line(daily, x="date", y="alerts", title="", markers=False)
        fig_ts.update_layout(margin=dict(l=0, r=0, t=20, b=0), height=300, template="plotly_dark")
        st.plotly_chart(fig_ts, use_container_width=True)

    # Middle: Alerts by category + top IPs table
    with middle_col:
        st.subheader("Alerts by Category")
        cat_counts = filtered["category"].value_counts().reindex(data["categories"]).fillna(0).reset_index()
        cat_counts.columns = ["category", "count"]
        fig_bar = px.bar(cat_counts, x="category", y="count", title="", text="count")
        fig_bar.update_layout(margin=dict(l=0, r=0, t=20, b=0), height=300, template="plotly_dark")
        fig_bar.update_traces(textposition="outside")
        st.plotly_chart(fig_bar, use_container_width=True)

        st.subheader("Top Malicious IPs")
        # Show top 8 ip addresses from filtered (recompute)
        top_ips = (
            filtered["src_ip"]
            .value_counts()
            .reset_index()
            .rename(columns={"index": "ip_address", "src_ip": "alerts"})
            .head(10)
        )
        # merge lat/lon if possible
        ip_coords = ip_table[["ip_address", "lat", "lon"]]
        top_ips = top_ips.merge(ip_coords, on="ip_address", how="left")
        st.table(top_ips.rename(columns={"ip_address": "IP Address", "src_ip": "Alerts", "alerts": "Alerts"}).assign(Alerts=top_ips["alerts"]))

    # Right: Log stream
    with right_col:
        st.subheader("Log Stream")
        # show latest logs from filtered
        logs = (
            filtered.sort_values("timestamp", ascending=False)
            .head(12)
            .loc[:, ["timestamp", "src_ip", "category", "severity", "msg"]]
            .reset_index(drop=True)
        )
        if logs.empty:
            st.info("No events in the selected time range / severity.")
        else:
            # pretty display
            for i, row in logs.iterrows():
                ts = row["timestamp"].strftime("%Y-%m-%d %H:%M:%S")
                sev = row["severity"]
                msg = row["msg"]
                ip = row["src_ip"]
                st.markdown(f"**{ts}**  ·  `{ip}`  ·  _{sev}_  \n> {msg}")

    st.markdown("---")

    # Bottom row: Geo map and optional raw table
    map_col, raw_col = st.columns([1.4, 1])

    with map_col:
        st.subheader("Geo IP Activity")
        # get map points from filtered aggregated by ip
        map_points = filtered.groupby("src_ip")[["lat", "lon"]].mean().reset_index()
        map_points.columns = ["ip_address", "lat", "lon"]
        if map_points.empty:
            st.info("No geo data to display for the selected filters.")
        else:
            # st.map expects a DataFrame with 'lat' and 'lon'
            st.map(map_points.rename(columns={"lat": "lat", "lon": "lon"}), use_container_width=True)

    with raw_col:
        st.subheader("Recent Alerts (table)")
        st.dataframe(filtered.sort_values("timestamp", ascending=False).head(200).loc[:, ["timestamp", "alert_id", "src_ip", "category", "severity", "priority"]])

    # Footer / tips
    st.markdown(
        """
        ---
        **Notes**
        - This example uses simulated data. Replace `generate_example_data()` with your real alert feed (e.g., Elastic, Splunk, SIEM API).
        - For production dashboards, secure endpoints, pagination for large tables, and authentication (e.g., Streamlit auth, reverse proxy) are recommended.
        - To convert the map to a nicer deck.gl visualization, use `pydeck` / `st.pydeck_chart` with proper clustering.
        """
    )


if __name__ == "__main__":
    main()