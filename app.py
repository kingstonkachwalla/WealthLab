
import math

import pandas as pd
import plotly.express as px
import streamlit as st


# ============================================================
# WEALTHLAB — PERSONAL WEALTH & INVESTMENT ANALYSIS
# ============================================================

st.set_page_config(
    page_title="WealthLab | Investment Analysis",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ============================================================
# CALCULATION FUNCTIONS
# ============================================================

def build_projection(starting_investment, monthly_contribution,
                     annual_return_pct, years):
    """Project investment growth using monthly compounding."""

    if starting_investment < 0 or monthly_contribution < 0:
        raise ValueError("Investment amounts cannot be negative.")

    if annual_return_pct <= -100:
        raise ValueError("Annual return must be greater than -100%.")

    if years < 1:
        raise ValueError("Investment horizon must be at least one year.")

    monthly_rate = (annual_return_pct / 100) / 12

    balance = float(starting_investment)
    contributions = float(starting_investment)

    rows = [{
        "Year": 0,
        "Portfolio Value": balance,
        "Total Contributions": contributions,
        "Investment Growth": balance - contributions,
    }]

    for month in range(1, years * 12 + 1):
        balance *= 1 + monthly_rate
        balance += monthly_contribution
        contributions += monthly_contribution

        if month % 12 == 0:
            rows.append({
                "Year": month // 12,
                "Portfolio Value": balance,
                "Total Contributions": contributions,
                "Investment Growth": balance - contributions,
            })

    return pd.DataFrame(rows)


def required_monthly_contribution(
    starting_investment, target_value, annual_return_pct, years
):
    """Estimate the monthly deposit needed to reach a target."""

    if starting_investment < 0 or target_value < 0:
        raise ValueError("Amounts cannot be negative.")

    if annual_return_pct <= -100:
        raise ValueError("Annual return must be greater than -100%.")

    if years < 1:
        raise ValueError("Timeline must be at least one year.")

    if starting_investment >= target_value:
        return 0.0

    monthly_rate = (annual_return_pct / 100) / 12
    months = years * 12

    def ending_balance(payment):
        balance = float(starting_investment)

        for _ in range(months):
            balance *= 1 + monthly_rate
            balance += payment

        return balance

    if ending_balance(0) >= target_value:
        return 0.0

    low = 0.0
    high = max(target_value, 1.0)

    while ending_balance(high) < target_value:
        high *= 2

        if high > 1e15:
            raise ValueError("Target is too large to calculate.")

    for _ in range(100):
        midpoint = (low + high) / 2

        if ending_balance(midpoint) >= target_value:
            high = midpoint
        else:
            low = midpoint

    return high


def money(value, decimals=0):
    return f"${value:,.{decimals}f}"


# ============================================================
# SIDEBAR — USER INPUTS
# ============================================================

st.title("📈 WealthLab")

st.caption(
    "PERSONAL WEALTH  •  INVESTMENT ANALYSIS  •  FINANCIAL PLANNING"
)

st.write(
    "Explore how starting capital, recurring contributions, "
    "and hypothetical investment returns can affect long-term wealth."
)

with st.sidebar:
    st.header("Investment assumptions")

    starting = st.number_input(
        "Starting investment ($)",
        min_value=0.0,
        max_value=1_000_000_000.0,
        value=5000.0,
        step=500.0,
        key="wl_starting",
    )

    monthly = st.number_input(
        "Monthly contribution ($)",
        min_value=0.0,
        max_value=10_000_000.0,
        value=200.0,
        step=50.0,
        key="wl_monthly",
    )

    annual_return = st.number_input(
        "Expected annual return (%)",
        min_value=-99.0,
        max_value=100.0,
        value=7.0,
        step=0.5,
        key="wl_return",
    )

    years = st.slider(
        "Investment horizon (years)",
        min_value=1,
        max_value=50,
        value=10,
        key="wl_horizon",
    )

    st.divider()

    inflation = st.number_input(
        "Assumed annual inflation (%)",
        min_value=0.0,
        max_value=30.0,
        value=2.5,
        step=0.5,
        key="wl_inflation",
    )

    scenario_spread = st.number_input(
        "Scenario spread (percentage points)",
        min_value=0.5,
        max_value=10.0,
        value=2.0,
        step=0.5,
        key="wl_spread",
    )


# ============================================================
# MAIN CALCULATIONS
# ============================================================

projection = build_projection(
    starting, monthly, annual_return, years
)

final_value = float(projection.iloc[-1]["Portfolio Value"])
total_contributions = float(
    projection.iloc[-1]["Total Contributions"]
)
investment_growth = final_value - total_contributions

inflation_adjusted_value = final_value / (
    (1 + inflation / 100) ** years
)

conservative_return = max(
    -99.0, annual_return - scenario_spread
)

optimistic_return = min(
    100.0, annual_return + scenario_spread
)

scenario_definitions = [
    ("Conservative", conservative_return),
    ("Base case", annual_return),
    ("Optimistic", optimistic_return),
]

scenario_frames = []

for scenario_name, scenario_return in scenario_definitions:
    scenario_df = build_projection(
        starting, monthly, scenario_return, years
    )

    scenario_df["Scenario"] = scenario_name
    scenario_frames.append(scenario_df)

all_scenarios = pd.concat(
    scenario_frames,
    ignore_index=True,
)


# ============================================================
# PORTFOLIO OVERVIEW
# ============================================================

st.divider()
st.header("Portfolio overview")

col1, col2, col3, col4 = st.columns(4)

col1.metric(
    "Projected balance",
    money(final_value),
)

col2.metric(
    "Total contributed",
    money(total_contributions),
)

col3.metric(
    "Investment growth",
    money(investment_growth),
)

col4.metric(
    "Value in today's dollars",
    money(inflation_adjusted_value),
)

st.caption(
    f"Assuming {inflation:.1f}% annual inflation, "
    f"{money(final_value)} in {years} years could have "
    f"purchasing power similar to {money(inflation_adjusted_value)} today."
)


# ============================================================
# NAVIGATION TABS
# ============================================================

growth_tab, scenarios_tab, goal_tab, data_tab = st.tabs([
    "📊 Growth projection",
    "⚖️ Scenario analysis",
    "🎯 Goal planner",
    "📋 Year-by-year data",
])


# ============================================================
# TAB 1 — GROWTH PROJECTION
# ============================================================

with growth_tab:
    st.subheader("Projected portfolio growth")

    growth_chart = px.area(
        projection,
        x="Year",
        y="Portfolio Value",
        title="Portfolio value over time",
    )

    growth_chart.add_scatter(
        x=projection["Year"],
        y=projection["Total Contributions"],
        mode="lines",
        name="Total contributions",
        line={"dash": "dash"},
    )

    growth_chart.update_layout(
        template="plotly_white",
        xaxis_title="Investment year",
        yaxis_title="Portfolio value ($)",
        yaxis_tickprefix="$",
        yaxis_tickformat=",.0f",
        legend_title_text="",
        hovermode="x unified",
    )

    st.plotly_chart(
        growth_chart,
        use_container_width=True,
    )

    st.subheader("Contributions versus investment growth")

    composition = pd.DataFrame({
        "Category": [
            "Total contributions",
            "Investment growth",
        ],
        "Amount": [
            total_contributions,
            investment_growth,
        ],
    })

    composition_chart = px.bar(
        composition,
        x="Category",
        y="Amount",
        text="Amount",
        title="What makes up your projected balance?",
    )

    composition_chart.update_traces(
        texttemplate="$%{text:,.0f}",
        textposition="outside",
    )

    composition_chart.update_layout(
        template="plotly_white",
        yaxis_title="Amount ($)",
        yaxis_tickprefix="$",
        yaxis_tickformat=",.0f",
    )

    st.plotly_chart(
        composition_chart,
        use_container_width=True,
    )

    with st.expander("View your model assumptions"):
        st.write(f"Starting investment: {money(starting, 2)}")
        st.write(f"Monthly contribution: {money(monthly, 2)}")
        st.write(f"Annual return assumption: {annual_return:.2f}%")
        st.write(f"Investment horizon: {years} years")
        st.write("Contributions are added at the end of each month.")
        st.write("The annual return assumption is divided by 12.")


# ============================================================
# TAB 2 — SCENARIO ANALYSIS
# ============================================================

with scenarios_tab:
    st.subheader("Compare hypothetical outcomes")

    st.write(
        "See how different return assumptions affect your "
        "projected balance over the same investment horizon."
    )

    summary_rows = []

    for scenario_name, scenario_return in scenario_definitions:
        result = build_projection(
            starting,
            monthly,
            scenario_return,
            years,
        )

        summary_rows.append({
            "Scenario": scenario_name,
            "Annual return": f"{scenario_return:.1f}%",
            "Projected balance": result.iloc[-1]["Portfolio Value"],
            "Total contributions": result.iloc[-1]["Total Contributions"],
            "Investment growth": (
                result.iloc[-1]["Portfolio Value"]
                - result.iloc[-1]["Total Contributions"]
            ),
        })

    summary_df = pd.DataFrame(summary_rows)

    display_summary = summary_df.copy()

    for column in [
        "Projected balance",
        "Total contributions",
        "Investment growth",
    ]:
        display_summary[column] = display_summary[column].map(
            lambda value: money(value, 2)
        )

    st.dataframe(
        display_summary,
        hide_index=True,
        use_container_width=True,
    )

    scenario_chart = px.line(
        all_scenarios,
        x="Year",
        y="Portfolio Value",
        color="Scenario",
        markers=True,
        title="Projected balances by scenario",
    )

    scenario_chart.update_layout(
        template="plotly_white",
        xaxis_title="Investment year",
        yaxis_title="Portfolio value ($)",
        yaxis_tickprefix="$",
        yaxis_tickformat=",.0f",
        legend_title_text="",
        hovermode="x unified",
    )

    st.plotly_chart(
        scenario_chart,
        use_container_width=True,
    )

    st.caption(
        "These scenarios are illustrative assumptions, not predictions "
        "or estimates of the probability of a particular outcome."
    )


# ============================================================
# TAB 3 — FINANCIAL GOAL PLANNER
# ============================================================

with goal_tab:
    st.subheader("Plan toward a financial target")

    goal_col1, goal_col2 = st.columns(2)

    with goal_col1:
        target = st.number_input(
            "Target portfolio value ($)",
            min_value=1.0,
            max_value=1_000_000_000.0,
            value=100000.0,
            step=5000.0,
            key="wl_goal_target",
        )

    with goal_col2:
        goal_years = st.slider(
            "Time to reach target (years)",
            min_value=1,
            max_value=50,
            value=min(10, years),
            key="wl_goal_years",
        )

    no_contribution_projection = build_projection(
        starting,
        0.0,
        annual_return,
        goal_years,
    )

    required_payment = required_monthly_contribution(
        starting,
        target,
        annual_return,
        goal_years,
    )

    if starting >= target:
        st.success(
            "Your starting investment already meets this target."
        )

        st.metric(
            "Required monthly contribution",
            "$0/month",
        )

    elif no_contribution_projection.iloc[-1]["Portfolio Value"] >= target:
        st.success(
            "Under these assumptions, your starting investment alone "
            "could reach the target within this timeline."
        )

        st.metric(
            "Required monthly contribution",
            "$0/month",
        )

    else:
        rounded_payment = math.ceil(required_payment)

        st.metric(
            "Estimated monthly contribution needed",
            f"{money(rounded_payment)}/month",
        )

        goal_projection = build_projection(
            starting,
            rounded_payment,
            annual_return,
            goal_years,
        )

        goal_final_value = float(
            goal_projection.iloc[-1]["Portfolio Value"]
        )

        st.write(
            f"At {money(rounded_payment)} per month, "
            f"the model projects approximately "
            f"{money(goal_final_value)} after {goal_years} years."
        )

        goal_chart = px.line(
            goal_projection,
            x="Year",
            y="Portfolio Value",
            markers=True,
            title="Progress toward your financial goal",
        )

        goal_chart.add_hline(
            y=target,
            line_dash="dash",
            annotation_text="Target",
        )

        goal_chart.update_layout(
            template="plotly_white",
            xaxis_title="Year",
            yaxis_title="Portfolio value ($)",
            yaxis_tickprefix="$",
            yaxis_tickformat=",.0f",
        )

        st.plotly_chart(
            goal_chart,
            use_container_width=True,
        )

    st.caption(
        "This estimate assumes a constant monthly return and "
        "month-end contributions. Actual investment results vary."
    )


# ============================================================
# TAB 4 — YEAR-BY-YEAR DATA
# ============================================================

with data_tab:
    st.subheader("Year-by-year breakdown")

    display_df = projection.copy()

    for column in [
        "Portfolio Value",
        "Total Contributions",
        "Investment Growth",
    ]:
        display_df[column] = display_df[column].map(
            lambda value: money(value, 2)
        )

    st.dataframe(
        display_df,
        hide_index=True,
        use_container_width=True,
    )

    csv_data = projection.to_csv(index=False).encode("utf-8")

    st.download_button(
        label="Download projection as CSV",
        data=csv_data,
        file_name="wealthlab_projection.csv",
        mime="text/csv",
        key="wl_download_csv",
    )


# ============================================================
# METHODOLOGY AND DISCLAIMER
# ============================================================

st.divider()

with st.expander("Methodology and limitations"):
    st.markdown(
        """
        **How the model works**

        - Monthly return = stated annual return divided by 12.
        - The starting investment is present at the beginning.
        - Each month, the balance earns the assumed monthly return.
        - The monthly contribution is then added at month-end.
        - Investment growth = ending balance minus total contributions.
        - Inflation-adjusted value = future balance divided by
          `(1 + inflation rate) ** years`.

        **What the model excludes**

        Taxes, fees, changing returns, and market volatility are excluded.
        Scenario outcomes are hypothetical and are not guaranteed.
        """
    )

st.caption(
    "WealthLab is an educational financial modeling project. "
    "Projections are hypothetical, not guaranteed, and are not "
    "personalized financial, tax, or investment advice."
)
