import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta
import numpy as np

st.set_page_config(layout="wide")
st.title("📊 Unified SAM Telemetry Dashboard")

# ---------- Data Loading (enhanced-first, fallback to basic) ----------
@st.cache_data
def load_data():
    try:
        df = pd.read_csv("telemetry_data_enhanced.csv", parse_dates=["ContractEndDate"])
        df["__enhanced__"] = True
    except Exception:
        df = pd.read_csv("telemetry_data.csv")
        # Fill minimal compatibility columns if missing
        if "CostPerLicense" not in df.columns:
            cost_map = {"Microsoft 365": 15, "Adobe CC": 25, "Oracle DB": 500,
                        "SQL Server": 300, "Zoom": 12, "Salesforce": 120}
            df["CostPerLicense"] = df["Vendor"].map(cost_map).fillna(25)
        if "LastUsedDays" not in df.columns:
            df["LastUsedDays"] = 0
        if "Department" not in df.columns:
            df["Department"] = "Unknown"
        if "ContractEndDate" not in df.columns:
            today = pd.Timestamp.today().normalize()
            df["ContractEndDate"] = today + pd.to_timedelta(np.random.randint(30, 365, size=len(df)), unit="D")
        else:
            df["ContractEndDate"] = pd.to_datetime(df["ContractEndDate"], errors="coerce").fillna(pd.Timestamp.today())
        if "IsEOL" not in df.columns:
            df["IsEOL"] = 0
        if "KnownVulns" not in df.columns:
            df["KnownVulns"] = 0
        if "DaysSincePatch" not in df.columns:
            df["DaysSincePatch"] = 30
        if "Edition" not in df.columns:
            df["Edition"] = "Standard"
        if "LicenseType" not in df.columns:
            df["LicenseType"] = "Subscription"
        df["__enhanced__"] = False
    return df

df = load_data()

# ---------------- Data Quality & Governance banner ----------------
st.caption(f"Data last refreshed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
null_rate = float(df.isna().mean().mean())
st.progress(min(1.0, 1 - null_rate))
src_tag = "Enhanced dataset" if df["__enhanced__"].iloc[0] else "Legacy dataset"
st.caption(f"Data completeness: {(1 - null_rate) * 100:.1f}%  •  Source mode: {src_tag} • Connectors: Endpoint + SaaS (simulated)")

# ---------------- Tabs ----------------
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "🔍 Operational View",
    "💼 CXO View",
    "🖥 Software Inventory & Security",
    "💰 Optimization & Savings",
    "📝 Actionable Items"
])

# Utility: synthesize a 12-month time series of "spend" from SAM data for anomaly detection
def synth_spend_timeseries(df, months=12, seed=7):
    rng = np.random.default_rng(seed)
    base = (df["EntitledLicenses"] * df["CostPerLicense"]).sum()
    # Seasonality + noise
    dates = pd.period_range(end=pd.Timestamp.today(), periods=months, freq="M").to_timestamp()
    season = 0.1 * np.sin(np.linspace(0, 2*np.pi, months))
    noise = rng.normal(0, 0.05, months)
    # occasional spike
    spikes = np.zeros(months)
    for _ in range(2):
        spikes[rng.integers(0, months)] += rng.uniform(0.15, 0.35)
    values = base * (1 + season + noise + spikes)
    return pd.DataFrame({"Month": dates, "Spend": values})

# ======================================================
# TAB 1 — OPERATIONAL VIEW (with Anomaly Alerts + filters + search)
# ======================================================
with tab1:
    st.subheader("Operational Telemetry Dashboard")

    # Visual placeholders
    c1, c2, c3, c4 = st.columns(4)
    with c1: st.selectbox("Impact", ["All","High","Medium","Low"])
    with c2: st.selectbox("Urgency", ["All","Critical","High","Low"])
    with c3: st.selectbox("Category", ["All","Software","Hardware","Database","Network"])
    with c4: st.selectbox("State", ["All","Active","Resolved","Closed"])

    # KPI Tiles
    k1, k2, k3, k4 = st.columns(4)
    # Over-usage risk count
    k1.metric("Active Compliance Issues", int((df["ActualUsage"] > df["EntitledLicenses"]).sum()))
    k2.metric("High Impact Risks", int((df["ActualUsage"] > df["EntitledLicenses"]).sum()))
    # Idle detection via LastUsedDays
    idle_threshold = 90
    idle_licenses = int((df["LastUsedDays"] >= idle_threshold).sum())
    k3.metric(f"Unused Licenses ≥{idle_threshold}d", idle_licenses)
    k4.metric("Resolved Issues", 210)  # placeholder

    # Charts
    col1, col2 = st.columns(2)
    with col1:
        fig1 = px.pie(df, names="DeploymentType", title="Usage by Deployment Type")
        st.plotly_chart(fig1, use_container_width=True)
    with col2:
        fig2 = px.treemap(df, path=["Vendor","Product"], values="EntitledLicenses",
                          title="Entitlements by Vendor/Product")
        st.plotly_chart(fig2, use_container_width=True)

    # ---------- NEW: Anomaly Alerts (Spend spikes) ----------
    st.subheader("Anomaly Alerts")
    ts = synth_spend_timeseries(df, months=12)
    # simple anomaly rule: > mean + 2*std
    mean_spend, std_spend = ts["Spend"].mean(), ts["Spend"].std()
    ts["Anomaly"] = ts["Spend"] > (mean_spend + 2*std_spend)
    anomalies = ts[ts["Anomaly"]]
    if not anomalies.empty:
        st.warning(f"Detected {len(anomalies)} unusual monthly spend spike(s).")
        figA = px.line(ts, x="Month", y="Spend", title="Monthly Spend with Anomalies")
        figA.add_scatter(x=anomalies["Month"], y=anomalies["Spend"], mode="markers", name="Anomaly", marker_size=12)
        st.plotly_chart(figA, use_container_width=True)
        st.dataframe(anomalies[["Month","Spend"]].assign(Spend=lambda d: d["Spend"].round(2)))
    else:
        st.success("No spend anomalies detected in the last 12 months.")

    # Funnel
    st.subheader("License Lifecycle Funnel")
    funnel_df = pd.DataFrame({"Stage": ["Purchased","Assigned","Active Use","Expired"],
                              "Count": [20000,18000,15000,3000]})
    fig3 = px.funnel(funnel_df, x="Count", y="Stage", title="License Lifecycle")
    st.plotly_chart(fig3, use_container_width=True)

    # Charts Row 2
    c3, c4 = st.columns(2)
    with c3:
        vendor_usage = df.groupby("Vendor")[["EntitledLicenses","ActualUsage"]].sum().reset_index()
        fig4 = px.bar(vendor_usage, x="Vendor", y=["EntitledLicenses","ActualUsage"],
                      barmode="group", title="Usage vs Entitlements (by Vendor)")
        st.plotly_chart(fig4, use_container_width=True)
    with c4:
        location_usage = df.groupby("Location")[["ActualUsage"]].sum().reset_index()
        fig5 = px.bar(location_usage, x="Location", y="ActualUsage", title="Usage by Location")
        st.plotly_chart(fig5, use_container_width=True)

    # ---------- Filters & Search JUST ABOVE the table ----------
    st.subheader("Detailed Telemetry Records")
    fc1, fc2 = st.columns(2)
    vendor_filter = fc1.multiselect("Filter by Vendor", sorted(df["Vendor"].unique()))
    location_filter = fc2.multiselect("Filter by Location", sorted(df["Location"].unique()))
    base_filtered = df.copy()
    if vendor_filter:
        base_filtered = base_filtered[base_filtered["Vendor"].isin(vendor_filter)]
    if location_filter:
        base_filtered = base_filtered[base_filtered["Location"].isin(location_filter)]

    query = st.text_input("Search records (EmployeeID, DeviceID, Location, Vendor, Product)")
    filtered_df = base_filtered
    if query:
        q = str(query).strip()
        mask = (
            base_filtered["EmployeeID"].astype(str).str.contains(q, case=False, na=False) |
            base_filtered["DeviceID"].astype(str).str.contains(q, case=False, na=False) |
            base_filtered["Location"].astype(str).str.contains(q, case=False, na=False) |
            base_filtered["Vendor"].astype(str).str.contains(q, case=False, na=False) |
            base_filtered["Product"].astype(str).str.contains(q, case=False, na=False)
        )
        filtered_df = base_filtered[mask]

    st.caption(f"Showing {len(filtered_df):,} of {len(df):,} records")
    st.dataframe(filtered_df.head(1000))

    # Download filtered results
    export_csv = filtered_df.to_csv(index=False).encode("utf-8")
    st.download_button("Download filtered telemetry (CSV)", data=export_csv,
                       file_name="telemetry_filtered.csv", mime="text/csv")

# ======================================================
# TAB 2 — CXO VIEW (business-grade + originals)
# ======================================================
with tab2:
    st.subheader("CXO Strategic Dashboard")

    budget = st.number_input("Annual Budget ($)", min_value=0, value=2_800_000, step=50_000)

    # Financials using CostPerLicense where possible
    actual_spend = (df["EntitledLicenses"] * df["CostPerLicense"]).sum()
    effective_spend = (df["ActualUsage"] * df["CostPerLicense"]).sum()
    overspend = max(0.0, actual_spend - budget)
    unused_waste = max(0.0, actual_spend - effective_spend)
    savings_opportunity = overspend + unused_waste

    compliance_df = df.groupby("Vendor")[["EntitledLicenses","ActualUsage"]].sum().reset_index()
    compliant_vendors = (compliance_df["ActualUsage"] <= compliance_df["EntitledLicenses"]).sum()
    total_vendors = compliance_df.shape[0]
    compliance_rate = (compliant_vendors / total_vendors) * 100 if total_vendors else 0

    employees = df["EmployeeID"].nunique()
    active_users = df.loc[df["ActualUsage"] > 0, "EmployeeID"].nunique()
    cost_per_employee = actual_spend / max(1, employees)
    cost_per_active_user = effective_spend / max(1, active_users)

    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Budget ($)", f"{budget:,.0f}")
    k2.metric("Actual Spend ($)", f"{actual_spend:,.0f}")
    k3.metric("Effective Spend ($)", f"{effective_spend:,.0f}")
    k4.metric("Savings Opportunity ($)", f"{savings_opportunity:,.0f}")

    u1, u2, u3 = st.columns(3)
    u1.metric("Compliance % (Audit Ready)", f"{compliance_rate:.2f}%")
    u2.metric("Cost per Employee", f"${cost_per_employee:,.2f}")
    u3.metric("Cost per Active User", f"${cost_per_active_user:,.2f}")

    # New business charts
    st.markdown("#### Budget vs Actual vs Effective")
    spend_df = pd.DataFrame({"Type": ["Budget","Actual","Effective"],
                             "Value": [budget, actual_spend, effective_spend]})
    fig_new1 = px.bar(spend_df, x="Type", y="Value", color="Type",
                      title="Budget vs Actual vs Effective Spend")
    st.plotly_chart(fig_new1, use_container_width=True)

    st.markdown("#### Forecast: Budget vs Actual Renewals (Cumulative)")
    renewals_df = df.copy()
    renewals_df["ContractEndDate"] = pd.to_datetime(renewals_df["ContractEndDate"], errors="coerce")
    renewals_df["Quarter"] = renewals_df["ContractEndDate"].dt.to_period("Q").astype(str)
    renewals_value = renewals_df.groupby("Quarter").apply(
        lambda x: (x["EntitledLicenses"] * x["CostPerLicense"]).sum()
    ).reset_index(name="ActualRenewals")
    q_order = sorted(renewals_value["Quarter"].unique())
    q_budget = np.linspace(budget/len(q_order), budget, num=len(q_order)) if len(q_order) else []
    if len(q_order):
        forecast_df = pd.DataFrame({
            "Quarter": q_order,
            "Budget": q_budget,
            "ActualRenewals": renewals_value.set_index("Quarter").loc[q_order]["ActualRenewals"].values
        })
        fig_new2 = px.line(forecast_df, x="Quarter", y=["Budget","ActualRenewals"],
                           markers=True, title="Budget vs Actual Renewal Forecast (Cumulative)")
        st.plotly_chart(fig_new2, use_container_width=True)
    else:
        st.info("No upcoming renewals to forecast.")

    # Renewal Calendar (timeline)
    st.markdown("#### Renewal Calendar (Next 12 Months)")
    next12 = pd.Timestamp.today().normalize() + pd.offsets.Day(365)
    cal = (df.loc[df["ContractEndDate"].between(pd.Timestamp.today().normalize(), next12)]
             .groupby(["Vendor","ContractEndDate"])
             .apply(lambda x: (x["EntitledLicenses"] * x["CostPerLicense"]).sum())
             .reset_index(name="Value"))
    if not cal.empty:
        cal["Start"] = cal["ContractEndDate"] - pd.to_timedelta(90, unit="D")
        fig_tl = px.timeline(cal, x_start="Start", x_end="ContractEndDate", y="Vendor", color="Value",
                             title="Renewal Calendar")
        fig_tl.update_yaxes(autorange="reversed")
        st.plotly_chart(fig_tl, use_container_width=True)
    else:
        st.info("No renewals in the next 12 months based on ContractEndDate.")

    st.divider()
    st.markdown("#### Original CXO Visuals")

    df_cost = df.copy()
    df_cost["TotalCost"] = df_cost["EntitledLicenses"] * df_cost["CostPerLicense"]
    spend_summary = df_cost.groupby("Vendor")[["TotalCost"]].sum().reset_index()

    c5, c6 = st.columns(2)
    with c5:
        fig_old1 = px.bar(spend_summary.sort_values("TotalCost", ascending=False),
                          x="Vendor", y="TotalCost", title="Top Vendors by Spend")
        st.plotly_chart(fig_old1, use_container_width=True)
    with c6:
        fig_old2 = px.pie(spend_summary, names="Vendor", values="TotalCost",
                          title="Spend Distribution by Vendor")
        st.plotly_chart(fig_old2, use_container_width=True)

    comp = df.groupby("Vendor")[["EntitledLicenses","ActualUsage","CostPerLicense"]].sum().reset_index()
    comp["OverUsage"] = comp["ActualUsage"] - comp["EntitledLicenses"]
    comp["PenaltyRisk($)"] = comp["OverUsage"].apply(lambda x: max(0, x) * 200)
    comp["UnderUtilization"] = comp["EntitledLicenses"] - comp["ActualUsage"]
    comp["WastedSpend($)"] = comp["UnderUtilization"].clip(lower=0) * comp["CostPerLicense"]
    fig_old3 = px.bar(comp, x="Vendor", y=["PenaltyRisk($)", "WastedSpend($)"],
                      barmode="group", title="Compliance Risks & Wasted Spend by Vendor")
    st.plotly_chart(fig_old3, use_container_width=True)

    st.markdown("#### Adoption by Function (Sample)")
    adoption_df = df.groupby("Department").apply(lambda x: (x["ActualUsage"] > 0).mean()*100).reset_index(name="AdoptionRate(%)")
    if adoption_df.empty:
        adoption_df = pd.DataFrame({"Department":["IT","Finance","HR","Marketing","Engineering"], "AdoptionRate(%)":[92,70,65,40,85]})
    fig_old4 = px.bar(adoption_df, x="Department", y="AdoptionRate(%)",
                      title="License Adoption by Department", color="AdoptionRate(%)")
    st.plotly_chart(fig_old4, use_container_width=True)

# ======================================================
# TAB 3 — SOFTWARE INVENTORY & SECURITY (enhanced)
# ======================================================
with tab3:
    st.subheader("Software Inventory & Security")

    inventory_summary = df.groupby("Product")["DeviceID"].count().reset_index(name="Installations")
    fig11 = px.bar(inventory_summary.sort_values("Installations", ascending=False).head(10),
                   x="Product", y="Installations", title="Top 10 Installed Products")
    st.plotly_chart(fig11, use_container_width=True)

    sec = df.groupby("Vendor").agg(
        Installations=("DeviceID","count"),
        EOL_Count=("IsEOL","sum"),
        Vuln_Count=("KnownVulns","sum"),
        AvgPatchAge=("DaysSincePatch","mean")
    ).reset_index()
    fig12 = px.scatter(
        sec, x="Vuln_Count", y="EOL_Count", size="Installations", hover_name="Vendor",
        hover_data={"AvgPatchAge":":.1f","Installations":":,"},
        title="Security Exposure (Vulnerabilities vs EOL) • bubble=Installations"
    )
    st.plotly_chart(fig12, use_container_width=True)

    st.subheader("Full Installed Software Inventory")
    cols_show = ["EmployeeID","DeviceID","Location","Department","Vendor","Product","Edition","ProductVersion"]
    cols_show = [c for c in cols_show if c in df.columns]
    st.dataframe(df[cols_show].sample(min(50, len(df))))

# ======================================================
# TAB 4 — OPTIMIZATION & SAVINGS (SAM + Cloud Analytics)
# ======================================================
with tab4:
    st.subheader("Optimization & Savings")

    by_vendor = df.groupby("Vendor")[["EntitledLicenses","ActualUsage","CostPerLicense"]].sum().reset_index()
    by_vendor["UnusedLicenses"] = (by_vendor["EntitledLicenses"] - by_vendor["ActualUsage"]).clip(lower=0)
    by_vendor["ShelfwareSavings($)"] = by_vendor["UnusedLicenses"] * by_vendor["CostPerLicense"]

    total_shelfware = by_vendor["ShelfwareSavings($)"].sum()
    base_downgrade_savings = 65000
    consolidation_savings = 40000

    st.markdown("#### Scenario Planning (SAM)")
    rec_rate = st.slider("Reclaim % of shelfware", 0, 100, 40)
    dwn_rate = st.slider("Downgrade % of candidates", 0, 100, 30)

    scenario_shelfware = total_shelfware * (rec_rate / 100)

    if {"Vendor","Edition","ActualUsage","CostPerLicense"}.issubset(df.columns):
        m365 = df[(df["Vendor"] == "Microsoft 365") & (df["Edition"].isin(["E5","E3"])) & (df["ActualUsage"] <= 1)]
        savings_per = np.where(m365["Edition"]=="E5", 0.8*m365["CostPerLicense"], 0.4*m365["CostPerLicense"])
        potential_downgrade_savings = savings_per.sum()
    else:
        potential_downgrade_savings = base_downgrade_savings

    scenario_downgrade = potential_downgrade_savings * (dwn_rate / 100)
    scenario_total = scenario_shelfware + scenario_downgrade + consolidation_savings

    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Scenario Savings ($)", f"{scenario_total:,.0f}")
    k2.metric("Shelfware Savings ($)", f"{scenario_shelfware:,.0f}")
    k3.metric("Downgrade Savings ($)", f"{scenario_downgrade:,.0f}")
    k4.metric("Consolidation Savings ($)", f"{consolidation_savings:,.0f}")

    fig13 = px.bar(by_vendor, x="Vendor", y="ShelfwareSavings($)",
                   title="Shelfware Savings by Vendor (Baseline)")
    st.plotly_chart(fig13, use_container_width=True)

    forecast_savings = pd.DataFrame({
        "Category": ["Shelfware (Scenario)", "Downgrades (Scenario)", "Consolidation (Fixed)"],
        "Savings($)": [scenario_shelfware, scenario_downgrade, consolidation_savings]
    })
    fig14 = px.bar(forecast_savings, x="Category", y="Savings($)", color="Category",
                   title="Forecasted Optimization Savings (Scenario)")
    st.plotly_chart(fig14, use_container_width=True)

    # ---------- NEW: Cloud Analytics block ----------
    st.markdown("### Cloud Analytics (Cloudability-style)")
    st.caption("Modeled demo data to illustrate Cloudability-like insights")

    # Commitment Discount Coverage (AWS/Azure/GCP)
    coverage = pd.DataFrame({
        "Cloud": ["AWS","Azure","GCP"],
        "Discounted(%)": [68, 55, 62],
        "OnDemand(%)": [32, 45, 38]
    })
    coverage_long = coverage.melt(id_vars="Cloud", var_name="Type", value_name="Percent")
    fig_cov = px.bar(coverage_long, x="Cloud", y="Percent", color="Type", barmode="stack",
                     title="Commitment Discount Coverage (Discounted vs On-Demand)")
    st.plotly_chart(fig_cov, use_container_width=True)

    # Rightsizing Recommendations (simulated cloud resources)
    st.subheader("Rightsizing Recommendations")
    rightsizing = pd.DataFrame({
        "ResourceID": [f"res-{i:04d}" for i in range(1, 11)],
        "Cloud": np.random.choice(["AWS","Azure","GCP"], 10),
        "Service": np.random.choice(["Compute/VM","Database","Cache"], 10),
        "Region": np.random.choice(["us-east-1","us-west-2","eu-west-1","ap-south-1"], 10),
        "CurrentSize": np.random.choice(["m5.4xlarge","m5.2xlarge","m5.xlarge","db.r6g.2xlarge","n2-standard-8"], 10),
        "RecommendedSize": np.random.choice(["m5.2xlarge","m5.xlarge","m5.large","db.r6g.xlarge","n2-standard-4"], 10),
        "AvgCPU%": np.random.uniform(8, 28, 10).round(1),
        "AvgMem%": np.random.uniform(12, 35, 10).round(1),
        "MonthlySavings($)": np.random.randint(150, 1200, 10)
    })
    rightsizing = rightsizing.sort_values("MonthlySavings($)", ascending=False)
    st.dataframe(rightsizing, use_container_width=True)

    # Idle SaaS Licenses via LastUsedDays
    st.subheader(f"Idle SaaS Licenses (LastUsedDays ≥ {idle_threshold})")
    idle = (df[df["LastUsedDays"] >= idle_threshold]
              .groupby("Vendor")
              .agg(**{
                  "Idle Licenses": ("EmployeeID","count"),
                  "Savings Potential ($)": ("CostPerLicense","sum")
              }).reset_index())
    if idle.empty:
        st.info("No idle licenses found under current threshold.")
    else:
        st.table(idle.sort_values("Savings Potential ($)", ascending=False))

# ======================================================
# TAB 5 — ACTIONABLE ITEMS
# ======================================================
with tab5:
    st.subheader("📝 Actionable Items")

    st.markdown("### Compliance Actions")
    compliance_actions = pd.DataFrame({
        "Action": [
            "Reconcile Oracle DB over-usage by true-up",
            "Remove 30 unauthorized Adobe installs"
        ],
        "Priority": ["High","Medium"],
        "Owner": ["SAM Team","IT Security"]
    })
    st.table(compliance_actions)

    st.markdown("### Cost Optimization Actions")
    cost_actions = pd.DataFrame({
        "Action": [
            "Reharvest all licenses with LastUsedDays ≥ 90",
            "Downgrade 200 Microsoft 365 E5/E3 → Standard",
            "Consolidate Zoom into Teams for meetings"
        ],
        "Priority": ["High","High","Medium"],
        "Owner": ["Procurement","IT Ops","Procurement"]
    })
    st.table(cost_actions)

    st.markdown("### Security Actions")
    security_actions = pd.DataFrame({
        "Action": [
            "Retire EOL software (IsEOL==1) by vendor",
            "Patch high AvgPatchAge vendors (>60 days)"
        ],
        "Priority": ["High","High"],
        "Owner": ["IT Ops","Security Engineering"]
    })
    st.table(security_actions)

    st.markdown("### Renewal Actions")
    renewal_actions = pd.DataFrame({
        "Action": [
            "Negotiate Salesforce renewal using utilization evidence",
            "Stage Oracle contract optimization ahead of end date"
        ],
        "Priority": ["Medium","High"],
        "Owner": ["Procurement","CIO Office"]
    })
    st.table(renewal_actions)

    st.markdown("### Governance Actions")
    governance_actions = pd.DataFrame({
        "Action": [
            "Auto-reclaim policy for LastUsedDays ≥ 90",
            "Require approval workflow for SaaS assignments"
        ],
        "Priority": ["Medium","Medium"],
        "Owner": ["Governance","IT Ops"]
    })
    st.table(governance_actions)

    # Download all actions as CSV
    all_actions = pd.concat(
        [compliance_actions, cost_actions, security_actions, renewal_actions, governance_actions],
        ignore_index=True
    )
    actions_csv = all_actions.to_csv(index=False).encode("utf-8")
    st.download_button("Download Actionable Items (CSV)", data=actions_csv,
                       file_name="sam_actionable_items.csv", mime="text/csv")
