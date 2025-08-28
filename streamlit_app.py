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
tab1, tab2 = st.tabs(["🔍 Operational View", "💼 CXO View"])

# ======================================================
# OPERATIONAL VIEW
# ======================================================
with tab1:
    st.subheader("Operational Telemetry Dashboard")

    # Filters
    col1, col2, col3, col4 = st.columns(4)
    with col1: impact = st.selectbox("Impact", ["All","High","Medium","Low"])
    with col2: urgency = st.selectbox("Urgency", ["All","Critical","High","Low"])
    with col3: category = st.selectbox("Category", ["All","Software","Hardware","Database","Network"])
    with col4: state = st.selectbox("State", ["All","Active","Resolved","Closed"])

    # KPI Tiles
    kpi1, kpi2, kpi3, kpi4 = st.columns(4)
    kpi1.metric("Active Compliance Issues", int((df["EntitledLicenses"] - df["ActualUsage"]).sum()))
    kpi2.metric("High Impact Risks", int((df["ActualUsage"] > df["EntitledLicenses"]).sum()))
    kpi3.metric("Unused Licenses >90d", 340)  # placeholder
    kpi4.metric("Resolved Issues", 210)       # placeholder

    # Charts
    col1, col2 = st.columns(2)
    with col1:
        fig1 = px.pie(df, names="DeploymentType", title="Usage by Deployment Type")
        st.plotly_chart(fig1, use_container_width=True)

    with col2:
        fig2 = px.treemap(df, path=["Vendor","Product"], values="EntitledLicenses",
                          title="Entitlements by Vendor/Product")
        st.plotly_chart(fig2, use_container_width=True)

    # Funnel Chart
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

    # Drill-down
    st.subheader("Detailed Telemetry Records")
    st.dataframe(df.sample(50))

# ======================================================
# CXO VIEW
# ======================================================
with tab2:
    st.subheader("CXO Strategic Dashboard")

    # KPI Tiles
    total_spend = (df["EntitledLicenses"].sum() * 50)  # assume avg $50/license
    actual_spend = (df["ActualUsage"].sum() * 50)
    savings_potential = total_spend - actual_spend
    compliance_rate = (df["ActualUsage"].sum() / df["EntitledLicenses"].sum()) * 100

    kpi1, kpi2, kpi3, kpi4 = st.columns(4)
    kpi1.metric("Total Spend ($)", f"{total_spend:,.0f}")
    kpi2.metric("Actual Usage Spend ($)", f"{actual_spend:,.0f}")
    kpi3.metric("Savings Opportunity ($)", f"{savings_potential:,.0f}")
    kpi4.metric("Compliance %", f"{compliance_rate:.2f}%")

    # Spend Optimization (Pareto)
    st.subheader("Vendor Spend Analysis")
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

    # Risk & Compliance
    st.subheader("Compliance & Risk Exposure")
    compliance_df = df.groupby("Vendor")[["EntitledLicenses","ActualUsage"]].sum().reset_index()
    compliance_df["OverUsage"] = compliance_df["ActualUsage"] - compliance_df["EntitledLicenses"]
    compliance_df["PenaltyRisk($)"] = compliance_df["OverUsage"].apply(lambda x: x*200 if x>0 else 0)

    fig8 = px.bar(compliance_df, x="Vendor", y="PenaltyRisk($)",
                  title="Potential Penalty Risk by Vendor")
    st.plotly_chart(fig8, use_container_width=True)

    # Forecast
    st.subheader("License Renewal Forecast (Next 4 Quarters)")
    forecast_df = pd.DataFrame({
        "Quarter": ["Q1","Q2","Q3","Q4"],
        "RenewalValue": [120000, 95000, 150000, 175000]
    })
    fig9 = px.line(forecast_df, x="Quarter", y="RenewalValue", markers=True,
                   title="Upcoming Renewal Exposure")
    st.plotly_chart(fig9, use_container_width=True)

    # Business Adoption
    st.subheader("Adoption by Function (Sample)")
    adoption_df = pd.DataFrame({
        "Department": ["IT","Finance","HR","Marketing","Engineering"],
        "AdoptionRate(%)": [92, 70, 65, 40, 85]
    })
    fig10 = px.bar(adoption_df, x="Department", y="AdoptionRate(%)", 
                   title="License Adoption by Department", color="AdoptionRate(%)")
    st.plotly_chart(fig10, use_container_width=True)
