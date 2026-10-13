import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(
    page_title="WealthLab",
    page_icon="📈",
    layout="wide"
)

st.title("WealthLab")
st.subheader("Personal Wealth & Investment Analysis")
st.write(
    "Explore how starting capital, recurring contributions, "
    "and assumed investment returns affect long-term growth."
)

st.sidebar.header("Investment assumptions")

starting_investment = st.sidebar.number_input(
    "Starting investment ($)",
    min_value=0.0,
    value=5000.0,
    step=500.0
)

monthly_contribution = st.sidebar.number_input(
    "Monthly contribution ($)",
    min_value=0.0,
    value=200.0,
    step=50.0
)

annual_return_pct = st.sidebar.number_input(
    "Expected annual return (%)",
    min_value=-99.0,
    max_value=100.0,
    value=7.0,
    step=0.5
)

years = st.sidebar.slider(
    "Investment horizon (years)",
    min_value=1,
    max_value=50,
    value=10
)

monthly_return = (annual_return_pct / 100) / 12
portfolio = starting_investment
total_contributed = starting_investment

results = [{
    "Year": 0,
    "Portfolio Value": portfolio,
    "Total Contributions": total_contributed,
    "Investment Growth": 0.0
}]

for month in range(1, years * 12 + 1):
    portfolio *= (1 + monthly_return)
    portfolio += monthly_contribution
    total_contributed += monthly_contribution

    if month % 12 == 0:
        results.append({
            "Year": month // 12,
            "Portfolio Value": portfolio,
            "Total Contributions": total_contributed,
            "Investment Growth": portfolio - total_contributed
        })

df = pd.DataFrame(results)

final_value = portfolio
investment_growth = final_value - total_contributed

st.divider()
st.subheader("Your projection")

col1, col2, col3 = st.columns(3)

col1.metric("Projected portfolio value", f"${final_value:,.2f}")
col2.metric("Total contributed", f"${total_contributed:,.2f}")
col3.metric("Investment growth", f"${investment_growth:,.2f}")

fig = px.line(
    df,
    x="Year",
    y="Portfolio Value",
    markers=True,
    title="Projected Portfolio Growth"
)

fig.update_layout(
    xaxis_title="Investment year",
    yaxis_title="Portfolio value ($)",
    yaxis_tickprefix="$",
    yaxis_tickformat=",.0f",
    template="plotly_white"
)

st.plotly_chart(fig, use_container_width=True)

st.subheader("Year-by-year breakdown")

display_df = df.copy()

for column in [
    "Portfolio Value",
    "Total Contributions",
    "Investment Growth"
]:
    display_df[column] = display_df[column].map(
        lambda value: f"${value:,.2f}"
    )

st.dataframe(display_df, hide_index=True, use_container_width=True)

st.caption(
    "Educational projection only, not personalized financial advice. "
    "Returns are assumptions, not predictions. This model assumes a "
    "constant monthly return and end-of-month contributions. It excludes "
    "taxes, fees, inflation, and market volatility."
)
