import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
import numpy as np
import os

st.set_page_config(layout="wide")
st.title("📊 Unified Software Asset Management Telemetry Dashboard")

# ---------- SAM Data Loading (enhanced-first, fallback to basic) ----------
@st.cache_data
def load_sam():
    try:
        df = pd.read_csv("telemetry_data_enhanced.csv", parse_dates=["ContractEndDate"])
        df["__enhanced__"] = True
    except Exception:
        df = pd.read_csv("telemetry_data.csv")
        # Backfill key fields if legacy
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

# ---------- Cloud Spend Loading (optional, powers Cloudability-style views) ----------
@st.cache_data
def load_cloud_spend(path="cloud_spend.csv"):
    if os.path.exists(path):
        df = pd.read_csv(path)
        # Normalize Month to datetime
        if "Month" in df.columns:
            try:
                df["Month"] = pd.to_datetime(df["Month"], format="%Y-%m")
            except Exception:
                df["Month"] = pd.to_datetime(df["Month"])
        return df
    return None

sam = load_sam()
cloud = load_cloud_spend()

# ---------------- Data Quality & Governance banner ----------------
st.caption(f"Data last refreshed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
null_rate = float(sam.isna().mean().mean())
st.progress(min(1.0, 1 - null_rate))
src_tag = "Enhanced dataset" if sam["__enhanced__"].iloc[0] else "Legacy dataset"
st.caption(f"Data completeness: {(1 - null_rate) * 100:.1f}%  •  Source mode: {src_tag} • Connectors: Endpoint + SaaS (simulated)")

# ---------------- Tabs ----------------
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "🔍 Operational View",
    "💼 CXO View",
    "🖥 Software Inventory & Security",
    "💰 Optimization & Savings",
    "📝 Actionable Items"
])

# Utility: synthesize spend if cloud CSV not present
def synth_spend_timeseries(df, months=12, seed=7):
    rng = np.random.default_rng(seed)
    base = (df["EntitledLicenses"] * df["CostPerLicense"]).sum()
    dates = pd.period_range(end=pd.Timestamp.today(), periods=months, freq="M").to_timestamp()
    season = 0.1 * np.sin(np.linspace(0, 2*np.pi, months))
    noise = rng.normal(0, 0.05, months)
    spikes = np.zeros(months)
    for _ in range(2):
        spikes[rng.integers(0, months)] += rng.uniform(0.15, 0.35)
    values = base * (1 + season + noise + spikes)
    return pd.DataFrame({"Month": dates, "Spend": values})

# ======================================================
# TAB 1 — OPERATIONAL VIEW (Anomaly Alerts + filters + search)
# ======================================================
with tab1:
    st.subheader("Operational Telemetry Dashboard")

    # Placeholder filters
    c1, c2, c3, c4 = st.columns(4)
    with c1: st.selectbox("Impact", ["All","High","Medium","Low"])
    with c2: st.selectbox("Urgency", ["All","Critical","High","Low"])
    with c3: st.selectbox("Category", ["All","Software","Hardware","Database","Network"])
    with c4: st.selectbox("State", ["All","Active","Resolved","Closed"])

    # KPI Tiles
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Active Compliance Issues", int((sam["ActualUsage"] > sam["EntitledLicenses"]).sum()))
    k2.metric("High Impact Risks", int((sam["ActualUsage"] > sam["EntitledLicenses"]).sum()))
    idle_threshold = 90
    k3.metric(f"Unused Licenses ≥{idle_threshold}d", int((sam["LastUsedDays"] >= idle_threshold).sum()))
    k4.metric("Resolved Issues", 210)

    # Charts
    col1, col2 = st.columns(2)
    with col1:
        fig1 = px.pie(sam, names="DeploymentType", title="Usage by Deployment Type")
        st.plotly_chart(fig1, use_container_width=True)
    with col2:
        fig2 = px.treemap(sam, path=["Vendor","Product"], values="EntitledLicenses",
                          title="Entitlements by Vendor/Product")
        st.plotly_chart(fig2, use_container_width=True)

    # ---------- Anomaly Alerts ----------
    st.subheader("Anomaly Alerts")
    if cloud is not None:
        monthly = cloud.groupby("Month").apply(lambda x: (x["OnDemandCost"] + x["DiscountedCost"]).sum()).reset_index(name="Spend")
    else:
        monthly = synth_spend_timeseries(sam, months=12)
    mean_spend, std_spend = monthly["Spend"].mean(), monthly["Spend"].std()
    monthly["Anomaly"] = monthly["Spend"] > (mean_spend + 2*std_spend)
    anomalies = monthly[monthly["Anomaly"]]
    if not anomalies.empty:
        st.warning(f"Detected {len(anomalies)} unusual monthly spend spike(s).")
    else:
        st.success("No spend anomalies detected in the last 12 months.")
    figA = px.line(monthly, x="Month", y="Spend", title="Monthly Cloud Spend (Anomaly Detection)")
    if not anomalies.empty:
        figA.add_scatter(x=anomalies["Month"], y=anomalies["Spend"], mode="markers", name="Anomaly", marker_size=12)
    st.plotly_chart(figA, use_container_width=True)

    # Funnel
    st.subheader("License Lifecycle Funnel")
    funnel_df = pd.DataFrame({"Stage": ["Purchased","Assigned","Active Use","Expired"],
                              "Count": [20000,18000,15000,3000]})
    st.plotly_chart(px.funnel(funnel_df, x="Count", y="Stage", title="License Lifecycle"), use_container_width=True)

    # Charts Row 2
    c5, c6 = st.columns(2)
    with c5:
        vendor_usage = sam.groupby("Vendor")[["EntitledLicenses","ActualUsage"]].sum().reset_index()
        st.plotly_chart(px.bar(vendor_usage, x="Vendor", y=["EntitledLicenses","ActualUsage"],
                               barmode="group", title="Usage vs Entitlements (by Vendor)"),
                        use_container_width=True)
    with c6:
        location_usage = sam.groupby("Location")[["ActualUsage"]].sum().reset_index()
        st.plotly_chart(px.bar(location_usage, x="Location", y="ActualUsage", title="Usage by Location"),
                        use_container_width=True)

    # ---------- Filters & Search JUST ABOVE the table ----------
    st.subheader("Detailed Telemetry Records")
    fc1, fc2 = st.columns(2)
    vendor_filter = fc1.multiselect("Filter by Vendor", sorted(sam["Vendor"].unique()))
    location_filter = fc2.multiselect("Filter by Location", sorted(sam["Location"].unique()))
    base_filtered = sam.copy()
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
    st.caption(f"Showing {len(filtered_df):,} of {len(sam):,} records")
    st.dataframe(filtered_df.head(1000))
    st.download_button("Download filtered telemetry (CSV)", data=filtered_df.to_csv(index=False).encode("utf-8"),
                       file_name="telemetry_filtered.csv", mime="text/csv")

# ======================================================
# TAB 2 — CXO VIEW (business-grade + originals)
# ======================================================
with tab2:
    st.subheader("CXO Strategic Dashboard")

    budget = st.number_input("Annual Budget ($)", min_value=0, value=2_800_000, step=50_000)

    actual_spend = (sam["EntitledLicenses"] * sam["CostPerLicense"]).sum()
    effective_spend = (sam["ActualUsage"] * sam["CostPerLicense"]).sum()
    overspend = max(0.0, actual_spend - budget)
    unused_waste = max(0.0, actual_spend - effective_spend)
    savings_opportunity = overspend + unused_waste

    compliance_df = sam.groupby("Vendor")[["EntitledLicenses","ActualUsage"]].sum().reset_index()
    compliant_vendors = (compliance_df["ActualUsage"] <= compliance_df["EntitledLicenses"]).sum()
    total_vendors = compliance_df.shape[0]
    compliance_rate = (compliant_vendors / total_vendors) * 100 if total_vendors else 0

    employees = sam["EmployeeID"].nunique()
    active_users = sam.loc[sam["ActualUsage"] > 0, "EmployeeID"].nunique()
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

    # Budget vs Actual vs Effective
    st.plotly_chart(px.bar(pd.DataFrame({"Type":["Budget","Actual","Effective"],
                                         "Value":[budget, actual_spend, effective_spend]}),
                           x="Type", y="Value", color="Type",
                           title="Budget vs Actual vs Effective Spend"),
                    use_container_width=True)

    # Forecast from ContractEndDate
    renewals_df = sam.copy()
    renewals_df["Quarter"] = pd.to_datetime(renewals_df["ContractEndDate"]).dt.to_period("Q").astype(str)
    renewals_value = renewals_df.groupby("Quarter").apply(
        lambda x: (x["EntitledLicenses"] * x["CostPerLicense"]).sum()).reset_index(name="ActualRenewals")
    if not renewals_value.empty:
        q_order = sorted(renewals_value["Quarter"].unique())
        q_budget = np.linspace(budget/len(q_order), budget, num=len(q_order))
        forecast_df = pd.DataFrame({"Quarter": q_order,
                                    "Budget": q_budget,
                                    "ActualRenewals": renewals_value.set_index("Quarter").loc[q_order]["ActualRenewals"].values})
        st.plotly_chart(px.line(forecast_df, x="Quarter", y=["Budget","ActualRenewals"],
                                markers=True, title="Budget vs Actual Renewal Forecast (Cumulative)"),
                        use_container_width=True)
    else:
        st.info("No upcoming renewals to forecast.")

    # Renewal Calendar (timeline)
    next12 = pd.Timestamp.today().normalize() + pd.offsets.Day(365)
    cal = (sam.loc[sam["ContractEndDate"].between(pd.Timestamp.today().normalize(), next12)]
             .groupby(["Vendor","ContractEndDate"])
             .apply(lambda x: (x["EntitledLicenses"] * x["CostPerLicense"]).sum())
             .reset_index(name="Value"))
    if not cal.empty:
        cal["Start"] = cal["ContractEndDate"] - pd.to_timedelta(90, unit="D")
        fig_tl = px.timeline(cal, x_start="Start", x_end="ContractEndDate", y="Vendor", color="Value",
                             title="Renewal Calendar")
        fig_tl.update_yaxes(autorange="reversed")
        st.plotly_chart(fig_tl, use_container_width=True)

    st.divider()
    st.markdown("#### Original CXO Visuals")

    df_cost = sam.copy()
    df_cost["TotalCost"] = df_cost["EntitledLicenses"] * df_cost["CostPerLicense"]
    spend_summary = df_cost.groupby("Vendor")[["TotalCost"]].sum().reset_index()

    c5, c6 = st.columns(2)
    with c5:
        st.plotly_chart(px.bar(spend_summary.sort_values("TotalCost", ascending=False),
                               x="Vendor", y="TotalCost", title="Top Vendors by Spend"),
                        use_container_width=True)
    with c6:
        st.plotly_chart(px.pie(spend_summary, names="Vendor", values="TotalCost",
                               title="Spend Distribution by Vendor"),
                        use_container_width=True)

    comp = sam.groupby("Vendor")[["EntitledLicenses","ActualUsage","CostPerLicense"]].sum().reset_index()
    comp["OverUsage"] = comp["ActualUsage"] - comp["EntitledLicenses"]
    comp["PenaltyRisk($)"] = comp["OverUsage"].apply(lambda x: max(0, x) * 200)
    comp["UnderUtilization"] = comp["EntitledLicenses"] - comp["ActualUsage"]
    comp["WastedSpend($)"] = comp["UnderUtilization"].clip(lower=0) * comp["CostPerLicense"]
    st.plotly_chart(px.bar(comp, x="Vendor", y=["PenaltyRisk($)", "WastedSpend($)"],
                           barmode="group", title="Compliance Risks & Wasted Spend by Vendor"),
                    use_container_width=True)

    adoption_df = sam.groupby("Department").apply(lambda x: (x["ActualUsage"] > 0).mean()*100).reset_index(name="AdoptionRate(%)")
    if adoption_df.empty:
        adoption_df = pd.DataFrame({"Department":["IT","Finance","HR","Marketing","Engineering"], "AdoptionRate(%)":[92,70,65,40,85]})
    st.plotly_chart(px.bar(adoption_df, x="Department", y="AdoptionRate(%)",
                           title="License Adoption by Department", color="AdoptionRate(%)"),
                    use_container_width=True)

# ======================================================
# TAB 3 — SOFTWARE INVENTORY & SECURITY
# ======================================================
with tab3:
    st.subheader("Software Inventory & Security")

    inventory_summary = sam.groupby("Product")["DeviceID"].count().reset_index(name="Installations")
    st.plotly_chart(px.bar(inventory_summary.sort_values("Installations", ascending=False).head(10),
                           x="Product", y="Installations", title="Top 10 Installed Products"),
                    use_container_width=True)

    sec = sam.groupby("Vendor").agg(
        Installations=("DeviceID","count"),
        EOL_Count=("IsEOL","sum"),
        Vuln_Count=("KnownVulns","sum"),
        AvgPatchAge=("DaysSincePatch","mean")
    ).reset_index()
    st.plotly_chart(px.scatter(sec, x="Vuln_Count", y="EOL_Count", size="Installations", hover_name="Vendor",
                               hover_data={"AvgPatchAge":":.1f","Installations":":,"},
                               title="Security Exposure (Vulnerabilities vs EOL) • bubble=Installations"),
                    use_container_width=True)

    st.subheader("Full Installed Software Inventory")
    cols_show = ["EmployeeID","DeviceID","Location","Department","Vendor","Product","Edition","ProductVersion"]
    cols_show = [c for c in cols_show if c in sam.columns]
    st.dataframe(sam[cols_show].sample(min(50, len(sam))))

# ======================================================
# TAB 4 — OPTIMIZATION & SAVINGS (Software Asset Management + Cloud Analytics)
# ======================================================
with tab4:
    st.subheader("Optimization & Savings")

    by_vendor = sam.groupby("Vendor")[["EntitledLicenses","ActualUsage","CostPerLicense"]].sum().reset_index()
    by_vendor["UnusedLicenses"] = (by_vendor["EntitledLicenses"] - by_vendor["ActualUsage"]).clip(lower=0)
    by_vendor["ShelfwareSavings($)"] = by_vendor["UnusedLicenses"] * by_vendor["CostPerLicense"]

    total_shelfware = by_vendor["ShelfwareSavings($)"].sum()
    base_downgrade_savings = 65000
    consolidation_savings = 40000

    st.markdown("#### Scenario Planning (SAM)")
    rec_rate = st.slider("Reclaim % of shelfware", 0, 100, 40)
    dwn_rate = st.slider("Downgrade % of candidates", 0, 100, 30)

    scenario_shelfware = total_shelfware * (rec_rate / 100)

    if {"Vendor","Edition","ActualUsage","CostPerLicense"}.issubset(sam.columns):
        m365 = sam[(sam["Vendor"] == "Microsoft 365") & (sam["Edition"].isin(["E5","E3"])) & (sam["ActualUsage"] <= 1)]
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

    st.plotly_chart(px.bar(by_vendor, x="Vendor", y="ShelfwareSavings($)",
                           title="Shelfware Savings by Vendor (Baseline)"),
                    use_container_width=True)

    forecast_savings = pd.DataFrame({
        "Category": ["Shelfware (Scenario)", "Downgrades (Scenario)", "Consolidation (Fixed)"],
        "Savings($)": [scenario_shelfware, scenario_downgrade, consolidation_savings]
    })
    st.plotly_chart(px.bar(forecast_savings, x="Category", y="Savings($)", color="Category",
                           title="Forecasted Optimization Savings (Scenario)"),
                    use_container_width=True)

    # ---------- Cloud Analytics (uses cloud_spend.csv if present) ----------
    st.markdown("### Cloud Analytics (Cloudability-style)")
    if cloud is not None:
        # Commitment Discount Coverage: use most recent month
        latest_month = cloud["Month"].max()
        latest = cloud[cloud["Month"] == latest_month].copy()
        cov = latest.groupby("Cloud").agg(Discounted=("DiscountedCost","sum"),
                                          OnDemand=("OnDemandCost","sum")).reset_index()
        cov["Total"] = cov["Discounted"] + cov["OnDemand"]
        cov["Discounted(%)"] = (cov["Discounted"] / cov["Total"] * 100).round(1)
        cov["OnDemand(%)"] = (cov["OnDemand"] / cov["Total"] * 100).round(1)
        cov_long = cov.melt(id_vars=["Cloud"], value_vars=["Discounted(%)","OnDemand(%)"],
                            var_name="Type", value_name="Percent")
        st.plotly_chart(px.bar(cov_long, x="Cloud", y="Percent", color="Type", barmode="stack",
                               title=f"Commitment Discount Coverage — {latest_month.strftime('%Y-%m')}"),
                        use_container_width=True)

        # Rightsizing Recommendations: from latest month, low CPU & Mem
        snap = latest.copy()
        candidates = snap[(snap["AvgCPUPercent"] < 20) & (snap["AvgMemPercent"] < 30)].copy()
        # Recommend one size down (simple mapping)
        order = ["nano","micro","small","medium","large","xlarge","2xlarge"]
        down_map = {order[i]: (order[i-1] if i>0 else order[0]) for i in range(len(order))}
        candidates["RecommendedSize"] = candidates["InstanceSize"].map(down_map)
        # Estimate savings ≈ 30% of current monthly total for the resource
        candidates["MonthlySavings($)"] = ((candidates["OnDemandCost"] + candidates["DiscountedCost"]) * 0.30).round(2)
        show_cols = ["ResourceID","Cloud","Service","Region","InstanceSize","RecommendedSize",
                     "AvgCPUPercent","AvgMemPercent","MonthlySavings($)"]
        st.subheader("Rightsizing Recommendations")
        st.dataframe(candidates.sort_values("MonthlySavings($)", ascending=False)[show_cols], use_container_width=True)
    else:
        st.info("No cloud_spend.csv detected — showing simulated coverage & rightsizing.")
        # Simulated coverage
        coverage = pd.DataFrame({"Cloud": ["AWS","Azure","GCP"],
                                 "Discounted(%)": [68, 55, 62],
                                 "OnDemand(%)": [32, 45, 38]})
        cov_long = coverage.melt(id_vars="Cloud", var_name="Type", value_name="Percent")
        st.plotly_chart(px.bar(cov_long, x="Cloud", y="Percent", color="Type", barmode="stack",
                               title="Commitment Discount Coverage (Simulated)"),
                        use_container_width=True)
        # Simulated rightsizing
        rightsizing = pd.DataFrame({
            "ResourceID": [f"res-{i:04d}" for i in range(1, 11)],
            "Cloud": np.random.choice(["AWS","Azure","GCP"], 10),
            "Service": np.random.choice(["Compute/VM","Database","Cache"], 10),
            "Region": np.random.choice(["us-east-1","us-west-2","eu-west-1","ap-south-1"], 10),
            "InstanceSize": np.random.choice(["m5.4xlarge","m5.2xlarge","m5.xlarge"], 10),
            "RecommendedSize": np.random.choice(["m5.2xlarge","m5.xlarge","m5.large"], 10),
            "AvgCPUPercent": np.random.uniform(8, 28, 10).round(1),
            "AvgMemPercent": np.random.uniform(12, 35, 10).round(1),
            "MonthlySavings($)": np.random.randint(150, 1200, 10)
        })
        st.dataframe(rightsizing.sort_values("MonthlySavings($)", ascending=False), use_container_width=True)

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
        "Owner": ["Software Asset Management Team","IT Security"]
    })
    st.table(compliance_actions)

    st.markdown("### Cost Optimization Actions")
    cost_actions = pd.DataFrame({
        "Action": [
            "Reharvest licenses with LastUsedDays ≥ 90",
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
    all_actions = pd.concat([compliance_actions, cost_actions, security_actions, renewal_actions, governance_actions], ignore_index=True)
    st.download_button("Download Actionable Items (CSV)",
                       data=all_actions.to_csv(index=False).encode("utf-8"),
                       file_name="sam_actionable_items.csv",
                       mime="text/csv")
