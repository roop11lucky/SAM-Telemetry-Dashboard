import streamlit as st
import pandas as pd
import plotly.express as px

@st.cache_data
def load_data():
    return pd.read_csv("telemetry_data.csv")

df = load_data()

st.set_page_config(layout="wide")
st.title("📊 Unified SAM Telemetry Dashboard")

# ---------------- Tabs ----------------
tab1, tab2, tab3, tab4 = st.tabs([
    "🔍 Operational View", 
    "💼 CXO View", 
    "🖥 Software Inventory & Security", 
    "💰 Optimization & Savings"
])

# ======================================================
# OPERATIONAL VIEW
# ======================================================
with tab1:
    st.subheader("Operational Telemetry Dashboard")
    col1, col2, col3, col4 = st.columns(4)
    with col1: st.selectbox("Impact", ["All","High","Medium","Low"])
    with col2: st.selectbox("Urgency", ["All","Critical","High","Low"])
    with col3: st.selectbox("Category", ["All","Software","Hardware","Database","Network"])
    with col4: st.selectbox("State", ["All","Active","Resolved","Closed"])

    kpi1, kpi2, kpi3, kpi4 = st.columns(4)
    kpi1.metric("Active Compliance Issues", int((df["EntitledLicenses"] - df["ActualUsage"]).sum()))
    kpi2.metric("High Impact Risks", int((df["ActualUsage"] > df["EntitledLicenses"]).sum()))
    kpi3.metric("Unused Licenses >90d", 340)
    kpi4.metric("Resolved Issues", 210)

    col1, col2 = st.columns(2)
    with col1:
        fig1 = px.pie(df, names="DeploymentType", title="Usage by Deployment Type")
        st.plotly_chart(fig1, use_container_width=True)
    with col2:
        fig2 = px.treemap(df, path=["Vendor","Product"], values="EntitledLicenses",
                          title="Entitlements by Vendor/Product")
        st.plotly_chart(fig2, use_container_width=True)

    st.subheader("License Lifecycle Funnel")
    funnel_df = pd.DataFrame({
        "Stage": ["Purchased","Assigned","Active Use","Expired"],
        "Count": [20000,18000,15000,3000]
    })
    fig3 = px.funnel(funnel_df, x="Count", y="Stage", title="License Lifecycle")
    st.plotly_chart(fig3, use_container_width=True)

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

    st.subheader("Detailed Telemetry Records")
    st.dataframe(df.sample(50))

# ======================================================
# CXO VIEW
# ======================================================
with tab2:
    st.subheader("CXO Strategic Dashboard")
    total_spend = (df["EntitledLicenses"].sum() * 50)
    actual_spend = (df["ActualUsage"].sum() * 50)
    savings_potential = total_spend - actual_spend
    compliance_rate = (df["ActualUsage"].sum() / df["EntitledLicenses"].sum()) * 100

    kpi1, kpi2, kpi3, kpi4 = st.columns(4)
    kpi1.metric("Total Spend ($)", f"{total_spend:,.0f}")
    kpi2.metric("Actual Usage Spend ($)", f"{actual_spend:,.0f}")
    kpi3.metric("Savings Opportunity ($)", f"{savings_potential:,.0f}")
    kpi4.metric("Compliance %", f"{compliance_rate:.2f}%")

    cost_map = {"Microsoft 365": 15, "Adobe CC": 25, "Oracle DB": 500,
                "SQL Server": 300, "Zoom": 12, "Salesforce": 120}
    df["CostPerLicense"] = df["Vendor"].map(cost_map)
    df["TotalCost"] = df["EntitledLicenses"] * df["CostPerLicense"]
    spend_summary = df.groupby("Vendor")[["TotalCost"]].sum().reset_index()

    col1, col2 = st.columns(2)
    with col1:
        fig6 = px.bar(spend_summary.sort_values("TotalCost", ascending=False),
                      x="Vendor", y="TotalCost", title="Top Vendors by Spend")
        st.plotly_chart(fig6, use_container_width=True)
    with col2:
        fig7 = px.pie(spend_summary, names="Vendor", values="TotalCost",
                      title="Spend Distribution by Vendor")
        st.plotly_chart(fig7, use_container_width=True)

    st.subheader("Compliance & Risk Exposure")
    compliance_df = df.groupby("Vendor")[["EntitledLicenses","ActualUsage"]].sum().reset_index()
    compliance_df["OverUsage"] = compliance_df["ActualUsage"] - compliance_df["EntitledLicenses"]
    compliance_df["PenaltyRisk($)"] = compliance_df["OverUsage"].apply(lambda x: x*200 if x>0 else 0)
    compliance_df["UnderUtilization"] = compliance_df["EntitledLicenses"] - compliance_df["ActualUsage"]
    compliance_df["WastedSpend($)"] = compliance_df["UnderUtilization"].apply(lambda x: x*50 if x>0 else 0)
    fig8 = px.bar(compliance_df, x="Vendor", y=["PenaltyRisk($)", "WastedSpend($)"],
                  barmode="group", title="Compliance Risks & Wasted Spend by Vendor")
    st.plotly_chart(fig8, use_container_width=True)

    st.subheader("License Renewal Forecast (Next 4 Quarters)")
    forecast_df = pd.DataFrame({
        "Quarter": ["Q1","Q2","Q3","Q4"],
        "RenewalValue": [120000, 95000, 150000, 175000]
    })
    fig9 = px.line(forecast_df, x="Quarter", y="RenewalValue", markers=True,
                   title="Upcoming Renewal Exposure")
    st.plotly_chart(fig9, use_container_width=True)

    st.subheader("Adoption by Function (Sample)")
    adoption_df = pd.DataFrame({
        "Department": ["IT","Finance","HR","Marketing","Engineering"],
        "AdoptionRate(%)": [92, 70, 65, 40, 85]
    })
    fig10 = px.bar(adoption_df, x="Department", y="AdoptionRate(%)", 
                   title="License Adoption by Department", color="AdoptionRate(%)")
    st.plotly_chart(fig10, use_container_width=True)

# ======================================================
# SOFTWARE INVENTORY & SECURITY
# ======================================================
with tab3:
    st.subheader("Software Inventory & Security")
    inventory_summary = df.groupby("Product")[["EntitledLicenses"]].count().reset_index()
    inventory_summary.columns = ["Product", "Installations"]
    fig11 = px.bar(inventory_summary.sort_values("Installations", ascending=False).head(10),
                   x="Product", y="Installations", title="Top 10 Installed Products")
    st.plotly_chart(fig11, use_container_width=True)

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
# OPTIMIZATION & SAVINGS
# ======================================================
with tab4:
    st.subheader("Optimization & Savings")
    optimization_df = df.groupby("Vendor")[["EntitledLicenses","ActualUsage"]].sum().reset_index()
    optimization_df["UnusedLicenses"] = optimization_df["EntitledLicenses"] - optimization_df["ActualUsage"]
    optimization_df["ShelfwareSavings($)"] = optimization_df["UnusedLicenses"] * 50

    total_shelfware = optimization_df["ShelfwareSavings($)"].sum()
    downgrade_savings = 65000
    consolidation_savings = 40000
    total_savings = total_shelfware + downgrade_savings + consolidation_savings

    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Total Savings Potential ($)", f"{total_savings:,.0f}")
    k2.metric("Shelfware Savings ($)", f"{total_shelfware:,.0f}")
    k3.metric("Downgrade Savings ($)", f"{downgrade_savings:,.0f}")
    k4.metric("Consolidation Savings ($)", f"{consolidation_savings:,.0f}")

    fig13 = px.bar(optimization_df, x="Vendor", y="ShelfwareSavings($)",
                   title="Shelfware Savings by Vendor")
    st.plotly_chart(fig13, use_container_width=True)

    forecast_savings = pd.DataFrame({
        "Category": ["Shelfware", "Downgrades", "Consolidation"],
        "Savings($)": [total_shelfware, downgrade_savings, consolidation_savings]
    })
    fig14 = px.bar(forecast_savings, x="Category", y="Savings($)", color="Category",
                   title="Forecasted Optimization Savings")
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
