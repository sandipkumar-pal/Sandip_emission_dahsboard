from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Dict, Iterable, List

import numpy as np
import pandas as pd
from faker import Faker

faker = Faker()

ZONES = ["ECA", "Non-ECA"]
FUEL_TYPES = ["HFO", "MGO", "LNG", "Hybrid"]
VESSEL_TYPES = ["Bulk Carrier", "Container", "Tanker", "Ro-Ro", "Offshore"]
DEFAULT_ALERT_THRESHOLD = 15.0


@dataclass
class FilterSet:
    start: pd.Timestamp
    end: pd.Timestamp
    zones: Iterable[str]
    vessel_types: Iterable[str]
    fuel_types: Iterable[str]


def generate_vessel_dataframe(rows: int = 500, seed: int | None = 42) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    end_date = pd.Timestamp.utcnow().normalize()
    start_date = end_date - pd.Timedelta(days=29)
    dates = rng.choice(
        pd.date_range(start_date, end_date, freq="D"), size=rows
    )

    zones = rng.choice(ZONES, size=rows, p=[0.45, 0.55])
    fuel_types = rng.choice(FUEL_TYPES, size=rows, p=[0.42, 0.32, 0.18, 0.08])
    vessel_types = rng.choice(VESSEL_TYPES, size=rows)

    base_co2 = rng.normal(loc=12.5, scale=3.2, size=rows)
    eca_adjustment = np.where(zones == "ECA", rng.normal(1.2, 0.25, rows), 1)
    co2 = np.clip(base_co2 * eca_adjustment, 4.5, 24)

    sox = np.clip(rng.normal(loc=1.05, scale=0.35, size=rows), 0.1, 2.4)
    nox = np.clip(rng.normal(loc=1.95, scale=0.55, size=rows), 0.5, 3.8)
    speed = np.clip(rng.normal(loc=13, scale=2.8, size=rows), 7, 20)
    dwell = np.clip(rng.normal(loc=48, scale=18, size=rows), 8, 110)

    compliance = co2 < DEFAULT_ALERT_THRESHOLD
    compliance = np.where(rng.random(rows) < 0.12, ~compliance, compliance)

    base_lat, base_lon = 1.265, 103.82
    lat = base_lat + rng.normal(0, 0.08, rows)
    lon = base_lon + rng.normal(0, 0.12, rows)

    records = []
    for idx in range(rows):
        imo_number = rng.integers(9100000, 9899999)
        vessel_name = f"MV_{faker.color_name().replace(' ', '')}_{idx:03d}"
        record = {
            "IMO_Number": int(imo_number),
            "Vessel_Name": vessel_name,
            "Zone": zones[idx],
            "Fuel_Type": fuel_types[idx],
            "Vessel_Type": vessel_types[idx],
            "CO2_tons": float(np.round(co2[idx], 2)),
            "SOx_tons": float(np.round(sox[idx], 2)),
            "NOx_tons": float(np.round(nox[idx], 2)),
            "Speed_knots": float(np.round(speed[idx], 2)),
            "Dwell_Time_hr": float(np.round(dwell[idx], 1)),
            "Compliance_Flag": bool(compliance[idx]),
            "Date": pd.Timestamp(dates[idx]),
            "Lat": float(np.round(lat[idx], 5)),
            "Lon": float(np.round(lon[idx], 5)),
        }
        records.append(record)

    df = pd.DataFrame(records)
    df["Emission_Intensity"] = (df["CO2_tons"] / df["Dwell_Time_hr"].replace(0, np.nan)).round(3)
    df["Month"] = df["Date"].dt.to_period("M").dt.to_timestamp()
    df.sort_values("Date", inplace=True)
    return df


def get_default_filters(df: pd.DataFrame) -> FilterSet:
    return FilterSet(
        start=df["Date"].min().normalize(),
        end=df["Date"].max().normalize(),
        zones=ZONES,
        vessel_types=sorted(df["Vessel_Type"].unique()),
        fuel_types=sorted(df["Fuel_Type"].unique()),
    )


def apply_filters(df: pd.DataFrame, filters: FilterSet) -> pd.DataFrame:
    mask = (
        (df["Date"] >= pd.Timestamp(filters.start))
        & (df["Date"] <= pd.Timestamp(filters.end) + pd.Timedelta(days=1) - pd.Timedelta(seconds=1))
        & (df["Zone"].isin(filters.zones))
        & (df["Vessel_Type"].isin(filters.vessel_types))
        & (df["Fuel_Type"].isin(filters.fuel_types))
    )
    return df.loc[mask].copy()


def calculate_kpis(df: pd.DataFrame) -> Dict[str, float]:
    total_co2 = float(df["CO2_tons"].sum())
    avg_per_vessel = float(df.groupby("IMO_Number")["CO2_tons"].mean().mean()) if not df.empty else 0.0
    eca_share = (
        float(df.loc[df["Zone"] == "ECA", "CO2_tons"].sum()) / total_co2 * 100 if total_co2 else 0.0
    )
    non_eca_share = 100 - eca_share if total_co2 else 0.0
    compliance_rate = float(df["Compliance_Flag"].mean() * 100) if not df.empty else 0.0
    alerts = int((df["CO2_tons"] > DEFAULT_ALERT_THRESHOLD).sum())
    emission_intensity = (
        float(df["CO2_tons"].sum() / df["Dwell_Time_hr"].sum()) * 24 if df["Dwell_Time_hr"].sum() else 0.0
    )

    latest_week = df[df["Date"] >= df["Date"].max() - pd.Timedelta(days=6)]
    previous_week = df[
        (df["Date"] < df["Date"].max() - pd.Timedelta(days=6))
        & (df["Date"] >= df["Date"].max() - pd.Timedelta(days=13))
    ]
    eca_week = latest_week.loc[latest_week["Zone"] == "ECA", "CO2_tons"].sum()
    eca_prev = previous_week.loc[previous_week["Zone"] == "ECA", "CO2_tons"].sum()
    delta_week = ((eca_week - eca_prev) / eca_prev * 100) if eca_prev else 0.0

    return {
        "total_co2": round(total_co2, 2),
        "avg_co2": round(avg_per_vessel, 2),
        "eca_percent": round(eca_share, 1),
        "non_eca_percent": round(non_eca_share, 1),
        "compliance_rate": round(compliance_rate, 1),
        "alerts": alerts,
        "emission_intensity": round(emission_intensity, 2),
        "eca_weekly_change": round(delta_week, 1),
    }


def generate_time_series(df: pd.DataFrame) -> pd.DataFrame:
    ts = (
        df.groupby(["Date", "Zone"])["CO2_tons"].sum().reset_index().pivot_table(
            index="Date", columns="Zone", values="CO2_tons", fill_value=0
        )
    )
    ts = ts.sort_index().reset_index()
    if "ECA" not in ts.columns:
        ts["ECA"] = 0.0
    if "Non-ECA" not in ts.columns:
        ts["Non-ECA"] = 0.0
    return ts


def fuel_mix(df: pd.DataFrame) -> pd.DataFrame:
    return (
        df.groupby(["Fuel_Type", "Zone"])["CO2_tons"].sum().reset_index()
    )


def build_emission_summary(df: pd.DataFrame) -> Dict[str, object]:
    zone_totals = df.groupby("Zone")["CO2_tons"].sum()
    compliance = df["Compliance_Flag"].mean() * 100 if not df.empty else 0.0
    top_emitters = (
        df.sort_values("CO2_tons", ascending=False)
        .head(5)[["IMO_Number", "Vessel_Name", "Zone", "CO2_tons", "Fuel_Type", "Compliance_Flag"]]
    )
    return {
        "eca_total": round(float(zone_totals.get("ECA", 0.0)), 2),
        "non_eca_total": round(float(zone_totals.get("Non-ECA", 0.0)), 2),
        "compliance": round(float(compliance), 1),
        "top_emitters": top_emitters,
    }


def generate_sankey_data(df: pd.DataFrame) -> Dict[str, List[int]]:
    zone_totals = df.groupby(["Fuel_Type", "Zone"])["CO2_tons"].sum().reset_index()
    if zone_totals.empty:
        return {"nodes": [], "sources": [], "targets": [], "values": []}

    fuel_nodes = zone_totals["Fuel_Type"].unique().tolist()
    zone_nodes = ["ECA Emissions", "Non-ECA Emissions"]
    nodes = fuel_nodes + zone_nodes
    node_index = {name: idx for idx, name in enumerate(nodes)}

    sources = [node_index[row["Fuel_Type"]] for _, row in zone_totals.iterrows()]
    targets = [node_index[f"{row['Zone']} Emissions"] for _, row in zone_totals.iterrows()]
    values = [float(round(row["CO2_tons"], 2)) for _, row in zone_totals.iterrows()]

    return {"nodes": nodes, "sources": sources, "targets": targets, "values": values}


def correlation_matrix(df: pd.DataFrame) -> pd.DataFrame:
    metrics = ["Speed_knots", "Dwell_Time_hr", "CO2_tons", "SOx_tons", "NOx_tons"]
    return df[metrics].corr().round(2)


def highlight_anomalies(df: pd.DataFrame, sigma: float = 1.5) -> pd.DataFrame:
    threshold = df["CO2_tons"].mean() + sigma * df["CO2_tons"].std()
    return df[df["CO2_tons"] > threshold].sort_values("CO2_tons", ascending=False)[
        [
            "IMO_Number",
            "Vessel_Name",
            "Zone",
            "Fuel_Type",
            "CO2_tons",
            "Speed_knots",
            "Dwell_Time_hr",
            "Date",
        ]
    ]


def quick_insight(df: pd.DataFrame) -> str:
    if df.empty:
        return "No telemetry available for the selected slice."

    latest_date = df["Date"].max()
    last_week = df[df["Date"] >= latest_date - pd.Timedelta(days=6)]
    prev_week = df[
        (df["Date"] < latest_date - pd.Timedelta(days=6))
        & (df["Date"] >= latest_date - pd.Timedelta(days=13))
    ]

    eca_change = _percentage_shift(last_week, prev_week, zone="ECA")
    non_eca_change = _percentage_shift(last_week, prev_week, zone="Non-ECA")

    if eca_change > 8:
        return f"⚠ ECA CO₂ rose {eca_change:.0f}% over the last week, driven by intensified bulk carrier calls."
    if non_eca_change < -5:
        return (
            f"✅ Non-ECA CO₂ fell {abs(non_eca_change):.0f}% as slow-steaming policies improved port-side dwell efficiency."
        )
    return "ℹ Emissions remain steady week-on-week with no material deviations detected."


def _percentage_shift(current: pd.DataFrame, previous: pd.DataFrame, zone: str) -> float:
    curr = current.loc[current["Zone"] == zone, "CO2_tons"].sum()
    prev = previous.loc[previous["Zone"] == zone, "CO2_tons"].sum()
    if prev == 0:
        return 0.0
    return (curr - prev) / prev * 100


def zone_snapshot(df: pd.DataFrame) -> List[Dict[str, object]]:
    cards = []
    grouped = df.groupby("Zone")
    for zone, frame in grouped:
        cards.append(
            {
                "zone": zone,
                "co2": round(float(frame["CO2_tons"].sum()), 2),
                "intensity": round(float(frame["Emission_Intensity"].mean()), 2),
                "compliance": round(float(frame["Compliance_Flag"].mean() * 100), 1),
                "alerts": int((frame["CO2_tons"] > DEFAULT_ALERT_THRESHOLD).sum()),
            }
        )
    return cards


def comparative_port_profile(df: pd.DataFrame) -> pd.DataFrame:
    current_month = df["Month"].max()
    historical = df[df["Month"] == current_month]
    synthetic = historical.copy()
    synthetic = synthetic.assign(
        Zone=lambda x: x["Zone"],
        Port=lambda x: np.where(x["Zone"] == "ECA", "Port Jurong", "Port Sentosa"),
    )

    primary = historical.assign(Port="Port Singapore")
    comparative = pd.concat([primary, synthetic], ignore_index=True)
    summary = (
        comparative.groupby(["Port", "Zone"])["CO2_tons"].sum().reset_index().sort_values("CO2_tons", ascending=False)
    )
    return summary


def speed_co2_relationship(df: pd.DataFrame) -> pd.DataFrame:
    return df[["Speed_knots", "CO2_tons", "Dwell_Time_hr", "Zone", "Vessel_Type", "Fuel_Type"]]


def monthly_trend(df: pd.DataFrame) -> pd.DataFrame:
    return (
        df.groupby(["Month", "Zone"])["CO2_tons"].sum().reset_index()
    )


def compliance_summary(df: pd.DataFrame) -> Dict[str, object]:
    compliance_rate = df["Compliance_Flag"].mean() * 100 if not df.empty else 0.0
    alert_df = df[df["CO2_tons"] > DEFAULT_ALERT_THRESHOLD]
    return {
        "rate": round(float(compliance_rate), 1),
        "alerts": alert_df.sort_values("CO2_tons", ascending=False)[
            ["IMO_Number", "Vessel_Name", "Zone", "CO2_tons", "SOx_tons", "NOx_tons", "Date"]
        ],
    }


def export_payload(df: pd.DataFrame) -> Dict[str, bytes | None]:
    csv_bytes = df.to_csv(index=False).encode("utf-8")

    from io import BytesIO

    excel_bytes: bytes | None = None
    excel_buffer = BytesIO()
    try:
        with pd.ExcelWriter(excel_buffer, engine="openpyxl") as writer:
            df.to_excel(writer, index=False, sheet_name="emissions")
        excel_bytes = excel_buffer.getvalue()
    except ImportError:
        excel_bytes = None

    return {"csv": csv_bytes, "excel": excel_bytes}


def pdf_placeholder(summary: Dict[str, object]) -> bytes:
    lines = [
        "Port Emission Intelligence – Executive Brief",
        "===========================================",
        f"ECA Total Emissions: {summary['eca_total']} t",
        f"Non-ECA Total Emissions: {summary['non_eca_total']} t",
        f"Compliance Rate: {summary['compliance']}%",
        "",
        "Top Emitters:",
    ]
    for _, row in summary["top_emitters"].iterrows():
        lines.append(
            f"- {row['Vessel_Name']} ({row['IMO_Number']}) – {row['CO2_tons']} t CO₂ – {row['Zone']}"
        )
    lines.append("\nGenerated: " + datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC"))
    return "\n".join(lines).encode("utf-8")
