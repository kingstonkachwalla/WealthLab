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

import math

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

st.set_page_config(
    page_title="WealthLab",
    page_icon="📈",
    layout="wide",
)

st.title("WealthLab")
st.caption("PERSONAL WEALTH & INVESTMENT ANALYSIS")
st.write(
    "Model long-term investment growth, compare return scenarios, "
    "account for inflation, and plan financial goals."
)

with st.sidebar:
    st.header("Investment assumptions")

    starting = st.number_input(
        "Starting investment ($)",
        min_value=0.0,
        value=5000.0,
        step=500.0,
    )
    monthly = st.number_input(
        "Monthly contribution ($)",
        min_value=0.0,
        value=200.0,
        step=50.0,
    )
    annual_return = st.number_input(
        "Base annual return (%)",
        min_value=-99.0,
        max_value=100.0,
        value=7.0,
        step=0.5,
    )
    years = st.slider(
        "Investment horizon (years)",
        min_value=1,
        max_value=50,
        value=10,
    )
    inflation = st.number_input(
        "Assumed annual inflation (%)",
        min_value=0.0,
        max_value=30.0,
        value=2.5,
        step=0.5,
    )
    scenario_gap = st.number_input(
        "Scenario difference (+/- percentage points)",
        min_value=0.5,
        max_value=10.0,
        value=2.0,
        step=0.5,
    )

def project(start, contribution, annual_pct, duration):
    rate = annual_pct / 100 / 12
    balance = start
    contributed = start
    rows = [{
        "Month": 0,
        "Year": 0,
        "Portfolio Value": balance,
        "Total Contributions": contributed,
        "Investment Growth": 0.0,
    }]

    for month in range(1, duration * 12 + 1):
        balance *= 1 + rate
        balance += contribution
        contributed += contribution

        if month % 12 == 0:
            rows.append({
                "Month": month,
                "Year": month // 12,
                "Portfolio Value": balance,
                "Total Contributions": contributed,
                "Investment Growth": balance - contributed,
            })

    return pd.DataFrame(rows)

def required_monthly(start, target, annual_pct, duration):
    if target <= start:
        return 0.0

    rate = annual_pct / 100 / 12
    months = duration * 12

    def ending_balance(payment):
        balance = start
        for _ in range(months):
            balance *= 1 + rate
            balance += payment
        return balance

    if ending_balance(0) >= target:
        return 0.0

    low, high = 0.0, target
    for _ in range(80):
        mid = (low + high) / 2
        if ending_balance(mid) >= target:
            high = mid
        else:
            low = mid

    return high

conservative_rate = max(-99.0, annual_return - scenario_gap)
optimistic_rate = min(100.0, annual_return + scenario_gap)

scenario_rates = {
    "Conservative": conservative_rate,
    "Base case": annual_return,
    "Optimistic": optimistic_rate,
}

scenario_frames = []
for name, rate in scenario_rates.items():
    frame = project(starting, monthly, rate, years)
    frame["Scenario"] = name
    frame["Assumed Return (%)"] = rate
    scenario_frames.append(frame)

all_scenarios = pd.concat(scenario_frames, ignore_index=True)
base = project(starting, monthly, annual_return, years)
final_value = base.iloc[-1]["Portfolio Value"]
total_contributed = base.iloc[-1]["Total Contributions"]
growth = final_value - total_contributed
real_value = final_value / (
    (1 + inflation / 100) ** years
)

st.divider()
st.header("1. Portfolio overview")

c1, c2, c3, c4 = st.columns(4)
c1.metric("Projected balance", f"${final_value:,.0f}")
c2.metric("Total contributions", f"${total_contributed:,.0f}")
c3.metric("Investment growth", f"${growth:,.0f}")
c4.metric("Value in today's dollars", f"${real_value:,.0f}")

st.caption(
    f"Your projected ${final_value:,.0f} balance in {years} years "
    f"would have purchasing power equivalent to about "
    f"${real_value:,.0f} today, assuming {inflation:.1f}% annual inflation."
)

st.header("2. Compare investment scenarios")

scenario_summary = (
    all_scenarios.groupby("Scenario", sort=False)
    .tail(1)[["Scenario", "Assumed Return (%)",
              "Portfolio Value", "Total Contributions",
              "Investment Growth"]]
    .reset_index(drop=True)
)

summary_display = scenario_summary.copy()
for col in ["Portfolio Value", "Total Contributions", "Investment Growth"]:
    summary_display[col] = summary_display[col].map(
        lambda x: f"${x:,.2f}"
    )
summary_display["Assumed Return (%)"] = (
    summary_display["Assumed Return (%)"].map(lambda x: f"{x:.1f}%")
)
st.dataframe(summary_display, hide_index=True, use_container_width=True)

scenario_chart = px.line(
    all_scenarios,
    x="Year",
    y="Portfolio Value",
    color="Scenario",
    markers=True,
    title="Projected balance by return scenario",
)
scenario_chart.update_layout(
    xaxis_title="Year",
    yaxis_title="Portfolio value ($)",
    yaxis_tickprefix="$",
    yaxis_tickformat=",.0f",
    template="plotly_white",
)
st.plotly_chart(scenario_chart, use_container_width=True)

st.header("3. Contributions versus growth")

breakdown = pd.DataFrame({
    "Category": ["Your contributions", "Investment growth"],
    "Amount": [total_contributed, growth],
})
breakdown_chart = px.bar(
    breakdown,
    x="Category",
    y="Amount",
    title="Where your projected balance comes from",
    text="Amount",
)
breakdown_chart.update_traces(
    texttemplate="$%{text:,.0f}",
    textposition="outside",
)
breakdown_chart.update_layout(
    yaxis_title="Amount ($)",
    yaxis_tickprefix="$",
    yaxis_tickformat=",.0f",
    template="plotly_white",
)
st.plotly_chart(breakdown_chart, use_container_width=True)

st.header("4. Financial goal planner")

g1, g2 = st.columns(2)
with g1:
    target = st.number_input(
        "Target portfolio balance ($)",
        min_value=1.0,
        value=100000.0,
        step=5000.0,
    )
with g2:
    goal_years = st.slider(
        "Years to reach your goal",
        min_value=1,
        max_value=50,
        value=10,
    )

needed = required_monthly(
    starting, target, annual_return, goal_years
)
goal_projection = project(
    starting, needed, annual_return, goal_years
)
goal_final = goal_projection.iloc[-1]["Portfolio Value"]

if starting >= target:
    st.success("Your starting investment already meets this target.")
elif project(starting, 0, annual_return, goal_years).iloc[-1][
    "Portfolio Value"
] >= target:
    st.success(
        "Your starting investment may reach this target without "
        "additional monthly contributions under these assumptions."
    )
else:
    st.metric(
        "Estimated monthly contribution needed",
        f"${math.ceil(needed):,.0f}/month",
    )
    st.caption(
        f"Calculated using the base return of {annual_return:.1f}% "
        f"and a {goal_years}-year timeline. The unrounded model "
        f"estimates approximately ${goal_final:,.0f} at the end."
    )

st.header("5. Year-by-year breakdown")

display = base[
    ["Year", "Portfolio Value", "Total Contributions", "Investment Growth"]
].copy()
for col in ["Portfolio Value", "Total Contributions", "Investment Growth"]:
    display[col] = display[col].map(lambda x: f"${x:,.2f}")
st.dataframe(display, hide_index=True, use_container_width=True)

st.caption(
    "EDUCATIONAL MODEL — not personalized financial advice. "
    "Returns are hypothetical, not forecasts or guarantees. "
    "The model uses a constant monthly rate equal to the stated "
    "annual rate divided by 12, with contributions added at month-end. "
    "Inflation is applied annually to estimate purchasing power. "
    "Taxes, fees, changing returns, and market volatility are excluded. "
    "Scenario labels describe assumptions, not probabilities."
)
