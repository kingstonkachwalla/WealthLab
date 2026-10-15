
import math
import pandas as pd
import plotly.express as px
import streamlit as st


# ============================================================
# WEALTHLAB V0.3 — INVESTMENT ANALYSIS + FINANCIAL HEALTH
# ============================================================

st.set_page_config(
    page_title="WealthLab | Financial Platform",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ============================================================
# SHARED UTILITIES
# ============================================================

def money(value, decimals=0):
    return f"${value:,.{decimals}f}"


def build_projection(starting, monthly, annual_return, years):
    """Monthly compounding with month-end contributions."""
    if starting < 0 or monthly < 0:
        raise ValueError("Amounts cannot be negative.")
    if annual_return <= -100:
        raise ValueError("Annual return must be greater than -100%.")
    if years < 1:
        raise ValueError("Years must be at least one.")

    monthly_rate = annual_return / 100 / 12
    balance = float(starting)
    contributed = float(starting)

    rows = [{
        "Year": 0,
        "Portfolio Value": balance,
        "Total Contributions": contributed,
        "Investment Growth": 0.0,
    }]

    for month in range(1, years * 12 + 1):
        balance *= 1 + monthly_rate
        balance += monthly
        contributed += monthly

        if month % 12 == 0:
            rows.append({
                "Year": month // 12,
                "Portfolio Value": balance,
                "Total Contributions": contributed,
                "Investment Growth": balance - contributed,
            })

    return pd.DataFrame(rows)


def required_monthly_contribution(starting, target, annual_return, years):
    """Binary search for a monthly payment that reaches a target."""
    if starting < 0 or target < 0:
        raise ValueError("Amounts cannot be negative.")
    if annual_return <= -100:
        raise ValueError("Annual return must be greater than -100%.")
    if years < 1:
        raise ValueError("Years must be at least one.")
    if starting >= target:
        return 0.0

    rate = annual_return / 100 / 12
    months = years * 12

    def ending_balance(payment):
        balance = float(starting)
        for _ in range(months):
            balance *= 1 + rate
            balance += payment
        return balance

    if ending_balance(0) >= target:
        return 0.0

    low, high = 0.0, max(target, 1.0)

    while ending_balance(high) < target:
        high *= 2
        if high > 1e15:
            raise ValueError("Target is too large.")

    for _ in range(100):
        mid = (low + high) / 2
        if ending_balance(mid) >= target:
            high = mid
        else:
            low = mid

    return high


def calculate_debt_payoff(balance, annual_rate, payment):
    """Estimate debt payoff using monthly interest and payments."""
    if balance < 0 or annual_rate < 0 or payment < 0:
        raise ValueError("Debt inputs cannot be negative.")

    if balance == 0:
        return {
            "months": 0,
            "total_paid": 0.0,
            "interest": 0.0,
        }

    monthly_rate = annual_rate / 100 / 12

    if payment <= 0:
        return None

    if monthly_rate > 0 and payment <= balance * monthly_rate:
        return None

    remaining = float(balance)
    total_paid = 0.0
    months = 0

    while remaining > 0.005 and months < 1200:
        interest = remaining * monthly_rate
        actual_payment = min(payment, remaining + interest)
        remaining = remaining + interest - actual_payment
        total_paid += actual_payment
        months += 1

    if remaining > 0.005:
        return None

    return {
        "months": months,
        "total_paid": total_paid,
        "interest": total_paid - balance,
    }


# ============================================================
# HEADER
# ============================================================

st.title("📈 WealthLab")
st.caption(
    "PERSONAL WEALTH • INVESTMENT ANALYSIS • FINANCIAL PLANNING"
)
st.write(
    "An educational financial platform to explore investments, "
    "cash flow, savings, net worth, and debt management."
)


# ============================================================
# INVESTMENT INPUTS
# ============================================================

with st.sidebar:
    st.header("Investment assumptions")

    starting = st.number_input(
        "Starting investment ($)",
        min_value=0.0,
        max_value=1_000_000_000.0,
        value=5000.0,
        step=500.0,
        key="v03_starting",
    )

    monthly = st.number_input(
        "Monthly investment contribution ($)",
        min_value=0.0,
        max_value=10_000_000.0,
        value=200.0,
        step=50.0,
        key="v03_monthly",
    )

    annual_return = st.number_input(
        "Expected annual return (%)",
        min_value=-99.0,
        max_value=100.0,
        value=7.0,
        step=0.5,
        key="v03_return",
    )

    years = st.slider(
        "Investment horizon (years)",
        min_value=1,
        max_value=50,
        value=10,
        key="v03_years",
    )

    st.divider()
    st.subheader("Additional assumptions")

    inflation = st.number_input(
        "Annual inflation (%)",
        min_value=0.0,
        max_value=30.0,
        value=2.5,
        step=0.5,
        key="v03_inflation",
    )

    spread = st.number_input(
        "Scenario spread (percentage points)",
        min_value=0.5,
        max_value=10.0,
        value=2.0,
        step=0.5,
        key="v03_spread",
    )


# ============================================================
# INVESTMENT CALCULATIONS
# ============================================================

projection = build_projection(starting, monthly, annual_return, years)

final_value = float(projection.iloc[-1]["Portfolio Value"])
contributed = float(projection.iloc[-1]["Total Contributions"])
investment_growth = final_value - contributed
real_value = final_value / ((1 + inflation / 100) ** years)

conservative_return = max(-99.0, annual_return - spread)
optimistic_return = min(100.0, annual_return + spread)

scenario_definitions = [
    ("Conservative", conservative_return),
    ("Base case", annual_return),
    ("Optimistic", optimistic_return),
]

scenario_frames = []

for scenario_name, scenario_rate in scenario_definitions:
    frame = build_projection(
        starting, monthly, scenario_rate, years
    )
    frame["Scenario"] = scenario_name
    scenario_frames.append(frame)

all_scenarios = pd.concat(scenario_frames, ignore_index=True)


# ============================================================
# MAIN NAVIGATION
# ============================================================

investment_tab, health_tab, debt_tab = st.tabs([
    "📈 Investment Analysis",
    "💰 Financial Health",
    "💳 Debt Management",
])


# ============================================================
# TAB 1 — INVESTMENT ANALYSIS
# ============================================================

with investment_tab:
    st.header("Investment dashboard")

    col1, col2, col3, col4 = st.columns(4)

    col1.metric("Projected balance", money(final_value))
    col2.metric("Total contributed", money(contributed))
    col3.metric("Investment growth", money(investment_growth))
    col4.metric("Value in today's dollars", money(real_value))

    st.caption(
        f"At {inflation:.1f}% assumed annual inflation, "
        f"{money(final_value)} in {years} years has estimated "
        f"purchasing power of {money(real_value)} today."
    )

    growth_tab, scenario_tab, goal_tab, data_tab = st.tabs([
        "Growth projection",
        "Scenario analysis",
        "Goal planner",
        "Year-by-year data",
    ])

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
            hovermode="x unified",
        )

        st.plotly_chart(growth_chart, use_container_width=True)

        composition = pd.DataFrame({
            "Category": ["Contributions", "Investment growth"],
            "Amount": [contributed, investment_growth],
        })

        composition_chart = px.bar(
            composition,
            x="Category",
            y="Amount",
            title="Contributions versus investment growth",
        )

        composition_chart.update_layout(
            template="plotly_white",
            yaxis_title="Amount ($)",
            yaxis_tickprefix="$",
            yaxis_tickformat=",.0f",
        )

        st.plotly_chart(composition_chart, use_container_width=True)

    with scenario_tab:
        st.subheader("Compare hypothetical outcomes")

        scenario_rows = []

        for scenario_name, scenario_rate in scenario_definitions:
            result = build_projection(
                starting, monthly, scenario_rate, years
            )

            ending = float(result.iloc[-1]["Portfolio Value"])
            total = float(result.iloc[-1]["Total Contributions"])

            scenario_rows.append({
                "Scenario": scenario_name,
                "Annual return": f"{scenario_rate:.1f}%",
                "Projected balance": money(ending, 2),
                "Total contributions": money(total, 2),
                "Investment growth": money(ending - total, 2),
            })

        st.dataframe(
            pd.DataFrame(scenario_rows),
            hide_index=True,
            use_container_width=True,
        )

        scenario_chart = px.line(
            all_scenarios,
            x="Year",
            y="Portfolio Value",
            color="Scenario",
            markers=True,
            title="Projected balance by scenario",
        )

        scenario_chart.update_layout(
            template="plotly_white",
            yaxis_title="Portfolio value ($)",
            yaxis_tickprefix="$",
            yaxis_tickformat=",.0f",
            hovermode="x unified",
        )

        st.plotly_chart(scenario_chart, use_container_width=True)

        st.caption(
            "Scenario assumptions are illustrative, not predictions."
        )

    with goal_tab:
        st.subheader("Financial goal planner")

        target = st.number_input(
            "Target portfolio value ($)",
            min_value=1.0,
            max_value=1_000_000_000.0,
            value=100000.0,
            step=5000.0,
            key="v03_goal_target",
        )

        goal_years = st.slider(
            "Years to reach target",
            min_value=1,
            max_value=50,
            value=min(10, years),
            key="v03_goal_years",
        )

        without_contributions = build_projection(
            starting, 0, annual_return, goal_years
        )

        if starting >= target:
            st.success("Your starting investment already meets the target.")
            st.metric("Required monthly contribution", "$0/month")

        elif without_contributions.iloc[-1]["Portfolio Value"] >= target:
            st.success(
                "The starting investment alone could reach this target "
                "under the selected assumptions."
            )
            st.metric("Required monthly contribution", "$0/month")

        else:
            required = required_monthly_contribution(
                starting, target, annual_return, goal_years
            )

            payment = math.ceil(required)

            st.metric(
                "Estimated required monthly contribution",
                f"{money(payment)}/month",
            )

            goal_projection = build_projection(
                starting, payment, annual_return, goal_years
            )

            goal_chart = px.line(
                goal_projection,
                x="Year",
                y="Portfolio Value",
                markers=True,
                title="Progress toward your target",
            )

            goal_chart.add_hline(
                y=target,
                line_dash="dash",
                annotation_text="Target",
            )

            goal_chart.update_layout(
                template="plotly_white",
                yaxis_tickprefix="$",
                yaxis_tickformat=",.0f",
            )

            st.plotly_chart(goal_chart, use_container_width=True)

    with data_tab:
        st.subheader("Year-by-year breakdown")

        display = projection.copy()

        for column in [
            "Portfolio Value",
            "Total Contributions",
            "Investment Growth",
        ]:
            display[column] = display[column].map(
                lambda value: money(value, 2)
            )

        st.dataframe(
            display,
            hide_index=True,
            use_container_width=True,
        )

        st.download_button(
            "Download investment projection as CSV",
            data=projection.to_csv(index=False).encode("utf-8"),
            file_name="wealthlab_projection.csv",
            mime="text/csv",
            key="v03_investment_csv",
        )


# ============================================================
# TAB 2 — PERSONAL FINANCIAL HEALTH
# ============================================================

with health_tab:
    st.header("Personal Financial Health")

    st.write(
        "Analyze your monthly cash flow, savings rate, emergency reserves, "
        "assets, liabilities, and overall net worth."
    )

    st.subheader("Monthly income and expenses")

    income_col1, income_col2 = st.columns(2)

    with income_col1:
        monthly_income = st.number_input(
            "Monthly take-home income ($)",
            min_value=0.0,
            max_value=100_000_000.0,
            value=4000.0,
            step=100.0,
            key="health_income",
        )

        monthly_expenses = st.number_input(
            "Monthly living expenses ($)",
            min_value=0.0,
            max_value=100_000_000.0,
            value=2800.0,
            step=100.0,
            key="health_expenses",
        )

    with income_col2:
        cash_savings = st.number_input(
            "Available cash savings ($)",
            min_value=0.0,
            max_value=1_000_000_000.0,
            value=6000.0,
            step=500.0,
            key="health_cash",
            help="Cash available for emergencies, excluding invested assets.",
        )

        emergency_target_months = st.slider(
            "Emergency fund target (months)",
            min_value=1,
            max_value=12,
            value=6,
            key="health_emergency_months",
        )

    monthly_surplus = monthly_income - monthly_expenses

    savings_rate = (
        monthly_surplus / monthly_income * 100
        if monthly_income > 0
        else 0.0
    )

    emergency_coverage = (
        cash_savings / monthly_expenses
        if monthly_expenses > 0
        else 0.0
    )

    emergency_target = monthly_expenses * emergency_target_months
    emergency_gap = max(0.0, emergency_target - cash_savings)

    st.subheader("Monthly financial snapshot")

    h1, h2, h3 = st.columns(3)

    h1.metric(
        "Monthly surplus / deficit",
        money(monthly_surplus, 2),
    )

    h2.metric(
        "Savings rate",
        f"{savings_rate:.1f}%",
    )

    h3.metric(
        "Emergency fund coverage",
        f"{emergency_coverage:.1f} months",
    )

    if monthly_income == 0:
        st.info(
            "Enter monthly take-home income to calculate a meaningful savings rate."
        )
    elif monthly_surplus < 0:
        st.warning(
            "Your expenses exceed your take-home income. "
            "Review your budget before increasing investments."
        )
    else:
        st.success(
            f"You have a modeled monthly surplus of "
            f"{money(monthly_surplus, 2)}."
        )

    st.subheader("Emergency fund planner")

    st.write(
        f"Your {emergency_target_months}-month target is "
        f"{money(emergency_target, 2)}."
    )

    progress = (
        min(cash_savings / emergency_target, 1.0)
        if emergency_target > 0
        else 0.0
    )

    st.progress(progress)

    if emergency_gap == 0:
        st.success("Your cash savings meet the selected emergency-fund target.")
    else:
        st.info(
            f"You need another {money(emergency_gap, 2)} "
            "to reach your target."
        )

        if monthly_surplus > 0:
            months_needed = math.ceil(emergency_gap / monthly_surplus)
            st.write(
                f"If you saved the entire modeled monthly surplus, "
                f"you could reach the target in about {months_needed} months."
            )
        else:
            st.write(
                "A positive monthly surplus is needed to estimate a savings timeline."
            )

    st.subheader("Income versus expenses")

    cash_flow = pd.DataFrame({
        "Category": ["Take-home income", "Living expenses", "Monthly surplus"],
        "Amount": [monthly_income, monthly_expenses, monthly_surplus],
    })

    cash_flow_chart = px.bar(
        cash_flow,
        x="Category",
        y="Amount",
        title="Monthly cash flow",
        text="Amount",
    )

    cash_flow_chart.update_traces(
        texttemplate="$%{text:,.0f}",
        textposition="outside",
    )

    cash_flow_chart.update_layout(
        template="plotly_white",
        yaxis_title="Monthly amount ($)",
        yaxis_tickprefix="$",
        yaxis_tickformat=",.0f",
    )

    st.plotly_chart(cash_flow_chart, use_container_width=True)

    st.subheader("Net worth calculator")

    st.write(
        "Enter assets and debts below. Cash savings are included separately "
        "to avoid counting them twice."
    )

    assets_col1, assets_col2 = st.columns(2)

    with assets_col1:
        investment_assets = st.number_input(
            "Investments and retirement accounts ($)",
            min_value=0.0,
            max_value=1_000_000_000.0,
            value=15000.0,
            step=500.0,
            key="health_investment_assets",
        )

        property_assets = st.number_input(
            "Property and other assets ($)",
            min_value=0.0,
            max_value=1_000_000_000.0,
            value=0.0,
            step=1000.0,
            key="health_property_assets",
        )

    with assets_col2:
        credit_card_debt = st.number_input(
            "Credit card debt ($)",
            min_value=0.0,
            max_value=1_000_000_000.0,
            value=1000.0,
            step=100.0,
            key="health_credit_debt",
        )

        other_debt = st.number_input(
            "Other loans and liabilities ($)",
            min_value=0.0,
            max_value=1_000_000_000.0,
            value=7000.0,
            step=500.0,
            key="health_other_debt",
        )

    total_assets = cash_savings + investment_assets + property_assets
    total_liabilities = credit_card_debt + other_debt
    net_worth = total_assets - total_liabilities

    n1, n2, n3 = st.columns(3)

    n1.metric("Total assets", money(total_assets, 2))
    n2.metric("Total liabilities", money(total_liabilities, 2))
    n3.metric("Estimated net worth", money(net_worth, 2))

    asset_breakdown = pd.DataFrame({
        "Category": ["Cash savings", "Investments", "Property / other assets"],
        "Amount": [cash_savings, investment_assets, property_assets],
    })

    asset_chart = px.pie(
        asset_breakdown,
        names="Category",
        values="Amount",
        hole=0.5,
        title="Asset composition",
    )

    st.plotly_chart(asset_chart, use_container_width=True)

    with st.expander("How Financial Health metrics are calculated"):
        st.markdown(
            """
            - **Monthly surplus:** take-home income minus living expenses.
            - **Savings rate:** monthly surplus divided by take-home income.
            - **Emergency fund coverage:** cash savings divided by monthly expenses.
            - **Emergency target:** monthly expenses multiplied by target months.
            - **Net worth:** cash savings plus other assets minus all liabilities.
            """
        )


# ============================================================
# TAB 3 — DEBT MANAGEMENT
# ============================================================

with debt_tab:
    st.header("Debt Management")

    st.write(
        "Estimate payoff time and interest costs for one debt using "
        "a fixed monthly payment."
    )

    debt_col1, debt_col2 = st.columns(2)

    with debt_col1:
        debt_balance = st.number_input(
            "Debt balance ($)",
            min_value=0.0,
            max_value=1_000_000_000.0,
            value=5000.0,
            step=250.0,
            key="debt_balance",
        )

        debt_interest = st.number_input(
            "Annual interest rate (%)",
            min_value=0.0,
            max_value=100.0,
            value=18.0,
            step=0.5,
            key="debt_interest",
        )

    with debt_col2:
        debt_payment = st.number_input(
            "Monthly payment ($)",
            min_value=0.0,
            max_value=100_000_000.0,
            value=250.0,
            step=25.0,
            key="debt_payment",
        )

    payoff = calculate_debt_payoff(
        debt_balance,
        debt_interest,
        debt_payment,
    )

    if payoff is None:
        st.error(
            "This payment may not cover the interest accruing each month, "
            "or the payoff timeline is too long. Increase the payment "
            "or check the debt assumptions."
        )

    elif payoff["months"] == 0:
        st.success("There is no debt balance to pay off.")

    else:
        months = payoff["months"]

        p1, p2, p3 = st.columns(3)

        p1.metric(
            "Estimated payoff time",
            f"{months // 12} years, {months % 12} months",
        )

        p2.metric(
            "Total interest",
            money(payoff["interest"], 2),
        )

        p3.metric(
            "Total payments",
            money(payoff["total_paid"], 2),
        )

        st.caption(
            "This is an estimate assuming a constant interest rate "
            "and the same payment every month."
        )


# ============================================================
# FOOTER
# ============================================================

st.divider()

st.caption(
    "WealthLab is an educational financial modeling project. "
    "Projections are hypothetical and not guaranteed. The app excludes "
    "taxes, fees, changing market returns, and many real-world financial "
    "factors. It does not provide personalized financial, tax, or "
    "investment advice."
)
