import streamlit as st
import pandas as pd
import plotly.express as px

# Load telemetry data
@st.cache_data
def load_data():
    return pd.read_csv("telemetry_data.csv")

df = load_data()

# Sidebar navigation
st.sidebar.title("📌 Navigation")
menu = st.sidebar.radio(
    "Go to",
    [
        "Dashboard Summary",
        "Budgeting & Forecasting",
        "Supplier Management",
        "Procure-to-Pay",
        "Analytics & Optimization",
        "Governance & Compliance"
    ]
)

st.title("📊 SAM Telemetry Dashboard")

# ============= DASHBOARD SUMMARY =============
if menu == "Dashboard Summary":
    st.subheader("📌 Telemetry Overview")

    # Filters
    vendor_filter = st.multiselect("Filter by Vendor", df["Vendor"].unique())
    location_filter = st.multiselect("Filter by Location", df["Location"].unique())

    filtered_df = df.copy()
    if vendor_filter:
        filtered_df = filtered_df[filtered_df["Vendor"].isin(vendor_filter)]
    if location_filter:
        filtered_df = filtered_df[filtered_df["Location"].isin(location_filter)]

    # KPIs
    total_entitled = filtered_df["EntitledLicenses"].sum()
    total_usage = filtered_df["ActualUsage"].sum()
    compliance_rate = (total_usage / total_entitled) * 100 if total_entitled > 0 else 0
    unused = total_entitled - total_usage

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Entitled", total_entitled)
    col2.metric("Total Usage", total_usage)
    col3.metric("Compliance (%)", f"{compliance_rate:.2f}")
    col4.metric("Unused Licenses", unused)

    # Charts
    col1, col2 = st.columns(2)
    with col1:
        fig1 = px.bar(filtered_df.groupby("Vendor")[["EntitledLicenses","ActualUsage"]].sum().reset_index(),
                    x="Vendor", y=["EntitledLicenses","ActualUsage"], barmode="group",
                    title="Usage vs Entitlement (by Vendor)")
        st.plotly_chart(fig1, use_container_width=True)

    with col2:
        fig2 = px.pie(filtered_df, names="DeploymentType", title="On-Prem vs Cloud Usage")
        st.plotly_chart(fig2, use_container_width=True)

    fig3 = px.bar(filtered_df.groupby("Location")[["ActualUsage"]].sum().reset_index(),
                x="Location", y="ActualUsage", title="Usage by Location")
    st.plotly_chart(fig3, use_container_width=True)

    st.dataframe(filtered_df.head(50))


# ============= BUDGETING & FORECASTING =============
elif menu == "Budgeting & Forecasting":
    st.subheader("📊 Budgeting & Forecasting Insights")

    forecast_df = df.groupby("Vendor")[["EntitledLicenses","ActualUsage"]].sum().reset_index()
    forecast_df["Forecast_Next_Quarter"] = forecast_df["ActualUsage"] * 1.1  # simple growth factor
    st.dataframe(forecast_df)

    fig = px.line(forecast_df, x="Vendor", y=["ActualUsage","Forecast_Next_Quarter"],
                  title="Usage Forecast by Vendor")
    st.plotly_chart(fig)


# ============= SUPPLIER MANAGEMENT =============
elif menu == "Supplier Management":
    st.subheader("🏢 Supplier Management Insights")

    supplier_df = df.groupby("Vendor")[["EntitledLicenses","ActualUsage"]].sum().reset_index()
    supplier_df["Utilization %"] = (supplier_df["ActualUsage"] / supplier_df["EntitledLicenses"]) * 100
    st.dataframe(supplier_df)

    fig = px.bar(supplier_df, x="Vendor", y="Utilization %", title="Supplier License Utilization (%)")
    st.plotly_chart(fig)


# ============= PROCURE-TO-PAY =============
elif menu == "Procure-to-Pay":
    st.subheader("💳 Procure-to-Pay Insights")

    # Simulate procurement costs
    cost_map = {
        "Microsoft 365": 15,
        "Adobe CC": 25,
        "Oracle DB": 500,
        "SQL Server": 300,
        "Zoom": 12,
        "Salesforce": 120
    }

    df["CostPerLicense"] = df["Vendor"].map(cost_map)
    df["TotalCost"] = df["EntitledLicenses"] * df["CostPerLicense"]

    cost_summary = df.groupby("Vendor")[["TotalCost"]].sum().reset_index()
    st.dataframe(cost_summary)

    fig = px.pie(cost_summary, names="Vendor", values="TotalCost", title="Procurement Spend by Vendor")
    st.plotly_chart(fig)


# ============= ANALYTICS & OPTIMIZATION =============
elif menu == "Analytics & Optimization":
    st.subheader("📈 Optimization Insights")

    optimization_df = df.groupby("Vendor")[["EntitledLicenses","ActualUsage"]].sum().reset_index()
    optimization_df["Unused"] = optimization_df["EntitledLicenses"] - optimization_df["ActualUsage"]

    st.dataframe(optimization_df)

    fig = px.bar(optimization_df, x="Vendor", y="Unused", title="Unused Licenses (Optimization Opportunity)")
    st.plotly_chart(fig)


# ============= GOVERNANCE & COMPLIANCE =============
elif menu == "Governance & Compliance":
    st.subheader("⚖ Governance & Compliance Risks")

    compliance_df = df.groupby("Vendor")[["EntitledLicenses","ActualUsage"]].sum().reset_index()
    compliance_df["OverUsage"] = compliance_df["ActualUsage"] - compliance_df["EntitledLicenses"]
    compliance_df = compliance_df[compliance_df["OverUsage"] > 0]

    st.dataframe(compliance_df)

    fig = px.bar(compliance_df, x="Vendor", y="OverUsage", title="Over-Usage Risks (Non-Compliance)")
    st.plotly_chart(fig)

