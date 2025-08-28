import streamlit as st
import pandas as pd
import plotly.express as px

@st.cache_data
def load_data():
    return pd.read_csv("telemetry_data.csv")

df = load_data()

st.set_page_config(layout="wide")
st.title("📊 SAM Telemetry Dashboard (ServiceNow Style)")

# ---------------- Filters ----------------
col1, col2, col3, col4 = st.columns(4)
with col1: impact = st.selectbox("Impact", ["All","High","Medium","Low"])
with col2: urgency = st.selectbox("Urgency", ["All","Critical","High","Low"])
with col3: category = st.selectbox("Category", ["All","Software","Hardware","Database","Network"])
with col4: state = st.selectbox("State", ["All","Active","Resolved","Closed"])

# ---------------- KPI Tiles ----------------
kpi1, kpi2, kpi3, kpi4 = st.columns(4)
kpi1.metric("Active Compliance Issues", int((df["EntitledLicenses"] - df["ActualUsage"]).sum()))
kpi2.metric("High Impact Risks", int((df["ActualUsage"] > df["EntitledLicenses"]).sum()))
kpi3.metric("Unused Licenses >90d", 340)  # Placeholder metric
kpi4.metric("Resolved Issues", 210)       # Placeholder metric

# ---------------- Charts Row 1 ----------------
col1, col2 = st.columns(2)
with col1:
    urgency_counts = df.groupby("Vendor")["ActualUsage"].sum().reset_index()
    fig1 = px.pie(df, names="DeploymentType", title="Usage by Deployment Type")
    st.plotly_chart(fig1, use_container_width=True)

with col2:
    fig2 = px.treemap(df, path=["Vendor","Product"], values="EntitledLicenses",
                      title="Entitlements by Vendor/Product")
    st.plotly_chart(fig2, use_container_width=True)

# ---------------- Funnel Chart ----------------
st.subheader("License Lifecycle Funnel")
funnel_df = pd.DataFrame({
    "Stage": ["Purchased","Assigned","Active Use","Expired"],
    "Count": [20000,18000,15000,3000]
})
fig3 = px.funnel(funnel_df, x="Count", y="Stage", title="License Lifecycle")
st.plotly_chart(fig3, use_container_width=True)

# ---------------- Charts Row 2 ----------------
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

# ---------------- Drill-down Table ----------------
st.subheader("Detailed Telemetry Records")
st.dataframe(df.sample(50))
