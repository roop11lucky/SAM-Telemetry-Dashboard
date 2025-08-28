import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime

st.set_page_config(layout="wide")
st.title("📊 Unified Software Asset Management Telemetry Dashboard")

@st.cache_data
def load_data():
    return pd.read_csv("telemetry_data.csv")

df = load_data()

# ---------------- Data Quality & Governance banner ----------------
st.caption(f"Data last refreshed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
null_rate = float(df.isna().mean().mean())
st.progress(min(1.0, 1 - null_rate))
st.caption(f"Data completeness: {(1 - null_rate) * 100:.1f}%  •  Sources: Endpoint agents + SaaS connectors (simulated)")

# ---------------- Tabs ----------------
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "🔍 Operational View",
    "💼 CXO View",
    "🖥 Software Inventory & Security",
    "💰 Optimization & Savings",
    "📝 Actionable Items"
])

# ======================================================
# TAB 1 — OPERATIONAL VIEW
# ======================================================
with tab1:
    st.subheader("Operational Telemetry Dashboard")

    # Visual/placeholder filters row (kept for layout parity)
    col1, col2, col3, col4 = st.columns(4)
    with col1: st.selectbox("Impact", ["All","High","Medium","Low"])
    with col2: st.selectbox("Urgency", ["All","Critical","High","Low"])
    with col3: st.selectbox("Category", ["All","Software","Hardware","Database","Network"])
    with col4: st.selectbox("State", ["All","Active","Resolved","Closed"])

    # KPI Tiles
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Active Compliance Issues", int((df["EntitledLicenses"] - df["ActualUsage"]).sum()))
    k2.metric("High Impact Risks", int((df["ActualUsage"] > df["EntitledLicenses"]).sum()))
    k3.metric("Unused Licenses >90d", 340)  # placeholder
    k4.metric("Resolved Issues", 210)       # placeholder

    # Charts
    col1, col2 = st.columns(2)
    with col1:
        fig1 = px.pie(df, names="DeploymentType", title="Usage by Deployment Type")
        st.plotly_chart(fig1, use_container_width=True)
    with col2:
        fig2 = px.treemap(df, path=["Vendor","Product"], values="EntitledLicenses",
                          title="Entitlements by Vendor/Product")
        st.plotly_chart(fig2, use_container_width=True)

    # Funnel
    st.subheader("License Lifecycle Funnel")
    funnel_df = pd.DataFrame({
        "Stage": ["Purchased","Assigned","Active Use","Expired"],
        "Count": [20000,18000,15000,3000]
    })
    fig3 = px.funnel(funnel_df, x="Count", y="Stage", title="License Lifecycle")
    st.plotly_chart(fig3, use_container_width=True)

    # Charts Row 2
    col1, col2 = st.columns(2)
    with col1:
        vendor_usage = df.groupby("Vendor")[["EntitledLicenses","ActualUsage"]].sum().reset_index()
        fig4 = px.bar(vendor_usage, x="Vendor", y=["EntitledLicenses","ActualUsage"],
                      barmode="group", title="Usage vs Entitlements (by Vendor)")
        st.plotly_chart(fig4, use_container_width=True)
    with col2:
        location_usage = df.groupby("Location")[["ActualUsage"]].sum().reset_index()
        fig5 = px.bar(location_usage, x="Location", y="ActualUsage",
                      title="Usage by Location")
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
    st.download_button(
        "Download filtered telemetry (CSV)",
        data=export_csv,
        file_name="telemetry_filtered.csv",
        mime="text/csv"
    )

# ======================================================
# TAB 2 — CXO VIEW (enhanced + originals)
# ======================================================
with tab2:
    st.subheader("CXO Strategic Dashboard")

    # Editable budget control
    budget = st.number_input("Annual Budget ($)", min_value=0, value=2_800_000, step=50_000)

    # Core financials
    actual_spend = df["EntitledLicenses"].sum() * 50
    effective_spend = df["ActualUsage"].sum() * 50
    overspend = max(0, actual_spend - budget)
    unused_waste = max(0, actual_spend - effective_spend)
    savings_opportunity = overspend + unused_waste

    # Compliance (Audit-Readiness)
    compliance_df = df.groupby("Vendor")[["EntitledLicenses","ActualUsage"]].sum().reset_index()
    compliant_vendors = (compliance_df["ActualUsage"] <= compliance_df["EntitledLicenses"]).sum()
    total_vendors = compliance_df.shape[0]
    compliance_rate = (compliant_vendors / total_vendors) * 100 if total_vendors else 0

    # Unit economics
    employees = 20000  # org size
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
    spend_df = pd.DataFrame({
        "Type": ["Budget","Actual","Effective"],
        "Value": [budget, actual_spend, effective_spend]
    })
    fig_new1 = px.bar(spend_df, x="Type", y="Value", color="Type",
                      title="Budget vs Actual vs Effective Spend")
    st.plotly_chart(fig_new1, use_container_width=True)

    st.markdown("#### Forecast: Budget vs Actual Renewals (Cumulative)")
    forecast_df = pd.DataFrame({
        "Quarter": ["Q1","Q2","Q3","Q4"],
        "Budget": [700000, 1400000, 2100000, 2800000],
        "ActualRenewals": [750000, 1500000, 2300000, 3000000]
    })
    fig_new2 = px.line(forecast_df, x="Quarter", y=["Budget","ActualRenewals"],
                       markers=True, title="Budget vs Actual Renewal Forecast (Cumulative)")
    st.plotly_chart(fig_new2, use_container_width=True)

    # Renewal Calendar (timeline)
    st.markdown("#### Renewal Calendar (Next 12 Months)")
    renewals = pd.DataFrame({
        "Vendor": ["Microsoft 365","Salesforce","Oracle DB","Zoom"],
        "Start": pd.to_datetime(["2025-01-01","2025-03-01","2025-05-01","2025-07-01"]),
        "End":   pd.to_datetime(["2025-03-31","2025-06-30","2025-08-31","2025-10-31"]),
        "Value": [450000, 300000, 500000, 120000]
    })
    fig_tl = px.timeline(renewals, x_start="Start", x_end="End", y="Vendor", color="Value",
                         title="Renewal Calendar")
    fig_tl.update_yaxes(autorange="reversed")
    st.plotly_chart(fig_tl, use_container_width=True)

    st.divider()
    st.markdown("#### Original CXO Visuals")

    # Spend Optimization (Pareto)
    cost_map = {"Microsoft 365": 15, "Adobe CC": 25, "Oracle DB": 500,
                "SQL Server": 300, "Zoom": 12, "Salesforce": 120}
    df_cost = df.copy()
    df_cost["CostPerLicense"] = df_cost["Vendor"].map(cost_map)
    df_cost["TotalCost"] = df_cost["EntitledLicenses"] * df_cost["CostPerLicense"]
    spend_summary = df_cost.groupby("Vendor")[["TotalCost"]].sum().reset_index()

    col1, col2 = st.columns(2)
    with col1:
        fig_old1 = px.bar(spend_summary.sort_values("TotalCost", ascending=False),
                          x="Vendor", y="TotalCost", title="Top Vendors by Spend")
        st.plotly_chart(fig_old1, use_container_width=True)
    with col2:
        fig_old2 = px.pie(spend_summary, names="Vendor", values="TotalCost",
                          title="Spend Distribution by Vendor")
        st.plotly_chart(fig_old2, use_container_width=True)

    # Compliance & Risk Exposure
    st.markdown("#### Compliance & Risk Exposure")
    compliance_df["OverUsage"] = compliance_df["ActualUsage"] - compliance_df["EntitledLicenses"]
    compliance_df["PenaltyRisk($)"] = compliance_df["OverUsage"].apply(lambda x: x*200 if x>0 else 0)
    compliance_df["UnderUtilization"] = compliance_df["EntitledLicenses"] - compliance_df["ActualUsage"]
    compliance_df["WastedSpend($)"] = compliance_df["UnderUtilization"].apply(lambda x: x*50 if x>0 else 0)
    fig_old3 = px.bar(compliance_df, x="Vendor", y=["PenaltyRisk($)", "WastedSpend($)"],
                      barmode="group", title="Compliance Risks & Wasted Spend by Vendor")
    st.plotly_chart(fig_old3, use_container_width=True)

    # Adoption by Department
    st.markdown("#### Adoption by Function (Sample)")
    adoption_df = pd.DataFrame({
        "Department": ["IT","Finance","HR","Marketing","Engineering"],
        "AdoptionRate(%)": [92, 70, 65, 40, 85]
    })
    fig_old4 = px.bar(adoption_df, x="Department", y="AdoptionRate(%)",
                      title="License Adoption by Department", color="AdoptionRate(%)")
    st.plotly_chart(fig_old4, use_container_width=True)

# ======================================================
# TAB 3 — SOFTWARE INVENTORY & SECURITY
# ======================================================
with tab3:
    st.subheader("Software Inventory & Security")

    inventory_summary = df.groupby("Product")[["EntitledLicenses"]].count().reset_index()
    inventory_summary.columns = ["Product", "Installations"]
    fig11 = px.bar(inventory_summary.sort_values("Installations", ascending=False).head(10),
                   x="Product", y="Installations", title="Top 10 Installed Products")
    st.plotly_chart(fig11, use_container_width=True)

    # Simulated security signals
    security_df = df.groupby("Vendor")[["EntitledLicenses"]].count().reset_index()
    security_df.columns = ["Vendor", "Installations"]
    security_df["EOL %"] = [12, 8, 5, 10, 6, 4]
    security_df["Vulnerable %"] = [5, 3, 2, 4, 2, 1]
    fig12 = px.bar(security_df, x="Vendor", y=["EOL %", "Vulnerable %"],
                   barmode="group", title="Security Risks by Vendor")
    st.plotly_chart(fig12, use_container_width=True)

    st.subheader("Full Installed Software Inventory")
    st.dataframe(df[["EmployeeID","DeviceID","Location","Vendor","Product"]].sample(50))

# ======================================================
# TAB 4 — OPTIMIZATION & SAVINGS
# ======================================================
with tab4:
    st.subheader("Optimization & Savings")

    optimization_df = df.groupby("Vendor")[["EntitledLicenses","ActualUsage"]].sum().reset_index()
    optimization_df["UnusedLicenses"] = optimization_df["EntitledLicenses"] - optimization_df["ActualUsage"]
    optimization_df["ShelfwareSavings($)"] = optimization_df["UnusedLicenses"] * 50

    total_shelfware = optimization_df["ShelfwareSavings($)"].sum()
    base_downgrade_savings = 65000
    consolidation_savings = 40000

    # Scenario sliders
    st.markdown("#### Scenario Planning")
    rec_rate = st.slider("Reclaim % of shelfware", 0, 100, 40)
    dwn_rate = st.slider("Downgrade % of candidates", 0, 100, 30)

    scenario_shelfware = total_shelfware * (rec_rate / 100)
    scenario_downgrade = base_downgrade_savings * (dwn_rate / 100)
    scenario_total = scenario_shelfware + scenario_downgrade + consolidation_savings

    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Scenario Savings ($)", f"{scenario_total:,.0f}")
    k2.metric("Shelfware Savings ($)", f"{scenario_shelfware:,.0f}")
    k3.metric("Downgrade Savings ($)", f"{scenario_downgrade:,.0f}")
    k4.metric("Consolidation Savings ($)", f"{consolidation_savings:,.0f}")

    fig13 = px.bar(optimization_df, x="Vendor", y="ShelfwareSavings($)",
                   title="Shelfware Savings by Vendor (Baseline, before scenario)")
    st.plotly_chart(fig13, use_container_width=True)

    forecast_savings = pd.DataFrame({
        "Category": ["Shelfware (Scenario)", "Downgrades (Scenario)", "Consolidation (Fixed)"],
        "Savings($)": [scenario_shelfware, scenario_downgrade, consolidation_savings]
    })
    fig14 = px.bar(forecast_savings, x="Category", y="Savings($)", color="Category",
                   title="Forecasted Optimization Savings (Scenario)")
    st.plotly_chart(fig14, use_container_width=True)

    st.subheader("Downgrade Opportunities")
    recs = pd.DataFrame({
        "Vendor": ["Microsoft 365","Adobe CC","Salesforce"],
        "Recommendation": [
            "Downgrade 200 Pro users to Basic",
            "Reclaim 120 unused Photoshop licenses",
            "Reassign 50 inactive CRM Cloud seats"
        ],
        "Estimated Savings ($)": [30000, 15000, 20000]
    })
    st.table(recs)

    st.subheader("Vendor Consolidation Suggestions")
    consolidation = pd.DataFrame({
        "Overlap": ["Slack + Teams","Zoom + Google Meet"],
        "Recommendation": ["Consolidate to Teams only","Consolidate to Zoom only"],
        "Estimated Savings ($)": [25000, 15000]
    })
    st.table(consolidation)

    st.subheader("Idle SaaS Licenses (>90 days)")
    idle = pd.DataFrame({
        "Vendor": ["Microsoft 365","Salesforce","Zoom"],
        "Idle Licenses": [120, 60, 40],
        "Savings Potential ($)": [6000, 7200, 2000]
    })
    st.table(idle)

# ======================================================
# TAB 5 — ACTIONABLE ITEMS
# ======================================================
with tab5:
    st.subheader("📝 Actionable Items")

    st.markdown("### Compliance Actions")
    compliance_actions = pd.DataFrame({
        "Action": [
            "Reconcile 50 Oracle DB licenses",
            "Remove 30 unauthorized Adobe installs"
        ],
        "Priority": ["High","Medium"],
        "Owner": ["Software Asset Management Team","IT Security"]
    })
    st.table(compliance_actions)

    st.markdown("### Cost Optimization Actions")
    cost_actions = pd.DataFrame({
        "Action": [
            "Reharvest 120 inactive M365 licenses",
            "Downgrade 200 users to Basic edition",
            "Consolidate Zoom into Teams"
        ],
        "Priority": ["High","High","Medium"],
        "Owner": ["Procurement","IT Ops","Procurement"]
    })
    st.table(cost_actions)

    st.markdown("### Security Actions")
    security_actions = pd.DataFrame({
        "Action": [
            "Upgrade 80 Win7 devices",
            "Patch Oracle 19c installations"
        ],
        "Priority": ["High","High"],
        "Owner": ["IT Ops","DBA Team"]
    })
    st.table(security_actions)

    st.markdown("### Renewal Actions")
    renewal_actions = pd.DataFrame({
        "Action": [
            "Negotiate Salesforce renewal (Q2)",
            "Evaluate Oracle contract renewal"
        ],
        "Priority": ["Medium","High"],
        "Owner": ["Procurement","CIO Office"]
    })
    st.table(renewal_actions)

    st.markdown("### Governance Actions")
    governance_actions = pd.DataFrame({
        "Action": [
            "Create policy for auto-reclaim unused >90d",
            "Enforce SaaS assignment approval"
        ],
        "Priority": ["Medium","Medium"],
        "Owner": ["Governance","IT Ops"]
    })
    st.table(governance_actions)

    # Download all actions as CSV
    all_actions = pd.concat([compliance_actions, cost_actions, security_actions, renewal_actions, governance_actions], ignore_index=True)
    actions_csv = all_actions.to_csv(index=False).encode("utf-8")
    st.download_button(
        "Download Actionable Items (CSV)",
        data=actions_csv,
        file_name="sam_actionable_items.csv",
        mime="text/csv"
    )
