import random
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Dict, List, Tuple

import numpy as np
import pandas as pd
from faker import Faker


fake = Faker()
Faker.seed(42)
np.random.seed(42)
random.seed(42)


PORT_COORDINATES = {
    "Singapore": {"lat": 1.264, "lon": 103.822},
    "Rotterdam": {"lat": 51.9244, "lon": 4.4777},
    "Los Angeles": {"lat": 33.7406, "lon": -118.2760},
}

FUEL_TYPES = ["HFO", "MGO", "LNG", "Hybrid"]
ZONES = ["ECA", "Non-ECA"]
ROLE_TITLES = {
    "Admin": "Port Emission Intelligence – ESG M&T",
    "Analyst": "Analyst Workbench – Emission Insights",
    "Ops Manager": "Operations Control – Emission Readiness",
    "Regulator": "Regulator Oversight – Compliance Monitor",
}


@dataclass
class EmissionSummary:
    eca_total: float
    non_eca_total: float
    compliance_rate: float
    alerts: int
    top_emitters: List[str]


def generate_vessel_dataframe(days: int = 30, records: int = 200) -> pd.DataFrame:
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)

    dates = pd.date_range(start=start_date, end=end_date, freq="6H")
    selected_dates = np.random.choice(dates, size=records)

    imo_numbers = np.random.randint(9000000, 9999999, size=records)
    vessel_names = [f"MV_{fake.color_name()}_{i:03d}" for i in range(records)]
    zones = np.random.choice(ZONES, size=records, p=[0.45, 0.55])
    fuel_types = np.random.choice(FUEL_TYPES, size=records, p=[0.4, 0.3, 0.2, 0.1])
    co2 = np.round(np.random.uniform(5, 20, size=records), 2)
    sox = np.round(np.random.uniform(0.1, 2.0, size=records), 2)
    nox = np.round(np.random.uniform(0.5, 3.0, size=records), 2)
    dwell_time = np.random.randint(12, 96, size=records)
    speed = np.round(np.random.uniform(8, 18, size=records), 1)
    compliance_flags = np.random.choice([True, False], size=records, p=[0.85, 0.15])

    latitudes = np.round(np.random.uniform(1.20, 1.33, size=records), 5)
    longitudes = np.round(np.random.uniform(103.6, 104.0, size=records), 5)

    df = pd.DataFrame(
        {
            "IMO_Number": imo_numbers,
            "Vessel_Name": vessel_names,
            "Zone": zones,
            "Fuel_Type": fuel_types,
            "CO2_tons": co2,
            "SOx_tons": sox,
            "NOx_tons": nox,
            "Dwell_Time_hr": dwell_time,
            "Speed_knots": speed,
            "Compliance_Flag": compliance_flags,
            "Date": selected_dates,
            "Lat": latitudes,
            "Lon": longitudes,
        }
    )

    df.sort_values("Date", inplace=True)
    df.reset_index(drop=True, inplace=True)
    return df


def calculate_kpis(df: pd.DataFrame) -> Dict[str, float]:
    total_co2 = float(df["CO2_tons"].sum())
    avg_co2 = float(df.groupby("IMO_Number")["CO2_tons"].mean().mean())
    zone_contribution = df.groupby("Zone")["CO2_tons"].sum()
    total_zone_emissions = zone_contribution.sum()
    eca_percent = (
        float(zone_contribution.get("ECA", 0)) / total_zone_emissions * 100
        if total_zone_emissions
        else 0.0
    )
    compliance_rate = float(df["Compliance_Flag"].mean() * 100)
    alerts = int((df["CO2_tons"] > 15).sum())

    return {
        "total_co2": round(total_co2, 2),
        "avg_co2": round(avg_co2, 2),
        "eca_percent": round(eca_percent, 1),
        "non_eca_percent": round(100 - eca_percent, 1),
        "compliance_rate": round(compliance_rate, 1),
        "alerts": alerts,
    }


def generate_time_series(df: pd.DataFrame) -> pd.DataFrame:
    daily = df.copy()
    daily["Date"] = daily["Date"].dt.date
    summary = (
        daily.groupby(["Date", "Zone"])["CO2_tons"].sum().reset_index().pivot(
            index="Date", columns="Zone", values="CO2_tons"
        )
    )
    summary = summary.fillna(0).reset_index()
    return summary


def fuel_mix(df: pd.DataFrame) -> pd.DataFrame:
    return (
        df.groupby("Fuel_Type")["CO2_tons"].sum().reset_index().sort_values("CO2_tons", ascending=False)
    )


def comparative_view(df: pd.DataFrame) -> pd.DataFrame:
    df_copy = df.copy()
    df_copy["Date"] = df_copy["Date"].dt.date
    comparison = (
        df_copy.groupby(["Date", "Zone"])["CO2_tons"].sum().reset_index()
    )
    return comparison


def build_emission_summary(df: pd.DataFrame) -> EmissionSummary:
    zone_totals = df.groupby("Zone")["CO2_tons"].sum()
    eca_total = float(zone_totals.get("ECA", 0.0))
    non_eca_total = float(zone_totals.get("Non-ECA", 0.0))
    compliance_rate = float(df["Compliance_Flag"].mean() * 100)
    alerts_df = df[df["CO2_tons"] > 15]
    top_emitters = (
        df.groupby("Vessel_Name")["CO2_tons"].sum().sort_values(ascending=False).head(5).index.tolist()
    )
    return EmissionSummary(
        eca_total=round(eca_total, 2),
        non_eca_total=round(non_eca_total, 2),
        compliance_rate=round(compliance_rate, 1),
        alerts=len(alerts_df),
        top_emitters=top_emitters,
    )


def regression_dataset(df: pd.DataFrame) -> Tuple[pd.DataFrame, float]:
    pivot = df[["Speed_knots", "CO2_tons"]].dropna()
    correlation = float(pivot["Speed_knots"].corr(pivot["CO2_tons"]))
    return pivot, round(correlation, 2)


def vessel_filters(df: pd.DataFrame, zone: str | None = None) -> pd.DataFrame:
    filtered = df.copy()
    if zone and zone != "All":
        filtered = filtered[filtered["Zone"] == zone]
    return filtered


def generate_sankey_data(df: pd.DataFrame) -> Dict[str, List]:
    nodes = list(FUEL_TYPES) + ZONES + ["CO2"]
    node_index = {name: idx for idx, name in enumerate(nodes)}

    sources: List[int] = []
    targets: List[int] = []
    values: List[float] = []

    for fuel in FUEL_TYPES:
        for zone in ZONES:
            mask = (df["Fuel_Type"] == fuel) & (df["Zone"] == zone)
            value = float(df.loc[mask, "CO2_tons"].sum())
            if value == 0:
                continue
            sources.append(node_index[fuel])
            targets.append(node_index[zone])
            values.append(round(value, 2))

    for zone in ZONES:
        value = float(df.loc[df["Zone"] == zone, "CO2_tons"].sum())
        if value == 0:
            continue
        sources.append(node_index[zone])
        targets.append(node_index["CO2"])
        values.append(round(value, 2))

    return {
        "nodes": nodes,
        "sources": sources,
        "targets": targets,
        "values": values,
    }


def role_header(role: str) -> str:
    return ROLE_TITLES.get(role, ROLE_TITLES["Analyst"])
