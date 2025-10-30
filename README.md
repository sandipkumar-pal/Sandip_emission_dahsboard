# Port Emission Intelligence – ESG M&T

Streamlit-based mockup dashboard showcasing ECA vs Non-ECA emission analytics for a Port Authority. The app features role-based navigation, KPI intelligence, map visualizations, and compliance insights aligned with an S&P Global dark theme.

## Features
- Secure login experience with role-aware navigation (Admin / Analyst / Ops Manager / Regulator).
- Executive overview with KPI cards, zone analytics, and Sankey insights.
- Folium spatial view showing simulated vessels, ECA boundary, and tooltip drill-downs.
- Vessel & voyage analytics table with export, comparative benchmarking, and compliance alerting.
- Admin panel for managing guardrails, reviewing system metadata, and future ECA boundary ingestion.

## Tech Stack
- Streamlit, Plotly, Folium for the UI layer.
- NumPy, Pandas, Faker for synthetic maritime telemetry.
- Standard `requirements.txt` for dependency management.

## Getting Started
1. Create and activate a virtual environment (optional but recommended).
2. Install dependencies with pip:
   ```bash
   pip install -r requirements.txt
   ```
3. Launch the dashboard:
   ```bash
   streamlit run app.py
   ```
4. Use any credentials to log in and select a role to explore the tailored insights.

> **Note:** All datasets are simulated for demonstration purposes only.

### Branding the Dashboard

Add your own organization logo (PNG recommended) at `assets/port_logo.png` if you would like
it rendered on the login screen and sidebar. When the file is absent, the app gracefully
falls back to a typography-based header so the repository remains binary-free for easier
version control and PR automation.
