# Port Emission Intelligence – ESG M&T

Enterprise-grade Streamlit dashboard delivering ECA vs Non-ECA emission analytics for Port Authority stakeholders. The experience mirrors modern BI platforms with a S&P Global-inspired dark theme, responsive layout, and storytelling insights.

## Highlights
- **Role-aware UX** for Admin, Analyst, Ops Manager, and Regulator personas with persistent filter context.
- **Advanced analytics suite** featuring KPI boards, anomaly detection, dual-axis time series, Sankey flows, and correlation mapping.
- **Spatial intelligence** with Folium heatmaps, ECA boundary overlays, and rich vessel tooltips.
- **Smart storytelling** including quick insights, anomaly watchlists, compliance gauge, and operational recommendations.
- **Export-ready tooling** offering CSV, Excel, and PDF brief downloads plus admin utilities for guardrails and boundary management.

## Tech Stack
- **Frontend:** Streamlit with custom CSS, Plotly visualizations, Folium maps, Streamlit Extras.
- **Data Simulation:** Pandas, NumPy, Faker generating 30-day maritime telemetry (~500 voyages).
- **Environment:** Poetry for reproducible dependency management.

## Getting Started
1. Ensure Poetry is installed (`pipx install poetry` or refer to Poetry docs).
2. Install dependencies and activate the virtual environment:
   ```bash
   poetry install
   poetry shell  # optional – or prefix commands with `poetry run`
   ```
3. Launch the dashboard:
   ```bash
   poetry run streamlit run app.py
   ```
4. Authenticate with any username/password combination, choose a role, and explore the analytics tabs.

> If you adjust dependencies, regenerate the lockfile with `poetry lock` from a network-enabled environment.

> **Note:** All telemetry is simulated for demonstration purposes. The repository intentionally excludes image assets—branding can be applied via CSS or by referencing locally hosted logos outside of version control.

## Project Structure
```
.
├── app.py
├── assets/
│   ├── custom.css
│   └── eca_boundary.geojson
├── components/
│   ├── admin.py
│   ├── comparative_insights.py
│   ├── compliance_alerts.py
│   ├── dashboard_overview.py
│   ├── login.py
│   ├── map_view.py
│   ├── reports.py
│   ├── vessel_analytics.py
│   └── zone_analytics.py
├── data_simulation.py
├── poetry.lock
└── pyproject.toml
```

## Development Scripts
- `poetry run black .` – format code (optional dev dependency).
- `poetry run flake8` – lint the project.
- `poetry run python -m compileall app.py components data_simulation.py` – quick syntax check used in CI.

## Roadmap Ideas
- Integrate live AIS or bunker data feeds.
- Connect to enterprise authentication providers (e.g., Azure AD).
- Replace PDF placeholder with branded report templates.
- Extend Folium view with 3D bathymetry layers or AIS playback.
