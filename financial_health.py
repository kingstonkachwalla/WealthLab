
import math
import pandas as pd
import plotly.express as px
import streamlit as st


def calculate_financial_health(
    monthly_income,
    monthly_expenses,
    cash_savings,
    assets,
    liabilities,
):
    """Calculate core personal financial health metrics."""

    monthly_surplus = monthly_income - monthly_expenses

    savings_rate = (
        monthly_surplus / monthly_income * 100
        if monthly_income > 0
        else 0.0
    )

    net_worth = assets + cash_savings - liabilities

    emergency_fund_months = (
        cash_savings / monthly_expenses
        if monthly_expenses > 0
        else 0.0
    )

    return {
        "monthly_surplus": monthly_surplus,
        "savings_rate": savings_rate,
        "net_worth": net_worth,
        "emergency_fund_months": emergency_fund_months,
    }


def calculate_debt_payoff(
    balance,
    annual_interest_rate,
    monthly_payment,
):
    """Estimate months and interest required to pay off a debt."""

    if balance <= 0:
        return {
            "months": 0,
            "total_paid": 0.0,
            "total_interest": 0.0,
        }

    if monthly_payment <= 0:
        return None

    if annual_interest_rate < 0:
        raise ValueError("Interest rate cannot be negative.")

    monthly_rate = annual_interest_rate / 100 / 12

    if monthly_rate > 0 and monthly_payment <= balance * monthly_rate:
        return None

    remaining = float(balance)
    total_paid = 0.0
    months = 0

    while remaining > 0.005 and months < 1200:
        interest = remaining * monthly_rate
        payment = min(monthly_payment, remaining + interest)

        remaining = remaining + interest - payment
        total_paid += payment
        months += 1

    if remaining > 0.005:
        return None

    return {
        "months": months,
        "total_paid": total_paid,
        "total_interest": total_paid - balance,
    }


def render_financial_health():
    """Render the WealthLab financial health dashboard."""

    st.title("Personal Financial Health")
    st.write(
        "Understand your cash flow, savings habits, net worth, "
        "emergency reserves, and debt payoff options."
    )

    st.subheader("1. Monthly income and expenses")

    col1, col2 = st.columns(2)

    with col1:
        monthly_income = st.number_input(
            "Monthly take-home income ($)",
            min_value=0.0,
            value=4000.0,
            step=100.0,
            key="fh_income",
        )

        monthly_expenses = st.number_input(
            "Monthly expenses ($)",
            min_value=0.0,
            value=2800.0,
            step=100.0,
            key="fh_expenses",
        )

    with col2:
        cash_savings = st.number_input(
            "Available cash savings ($)",
            min_value=0.0,
            value=6000.0,
            step=500.0,
            key="fh_cash",
        )

        emergency_target = st.slider(
            "Emergency fund target (months)",
            min_value=1,
            max_value=12,
            value=6,
            key="fh_emergency_target",
        )

    surplus = monthly_income - monthly_expenses

    savings_rate = (
        surplus / monthly_income * 100
        if monthly_income > 0
        else 0.0
    )

    emergency_months = (
        cash_savings / monthly_expenses
        if monthly_expenses > 0
        else 0.0
    )

    emergency_target_amount = (
        monthly_expenses * emergency_target
    )

    emergency_gap = max(
        0.0,
        emergency_target_amount - cash_savings,
    )

    st.subheader("Your monthly snapshot")

    m1, m2, m3 = st.columns(3)

    m1.metric(
        "Monthly surplus / deficit",
        f"${surplus:,.2f}",
    )

    m2.metric(
        "Savings rate",
        f"{savings_rate:.1f}%",
    )

    m3.metric(
        "Emergency fund coverage",
        f"{emergency_months:.1f} months",
    )

    if surplus < 0:
        st.warning(
            "Your modeled expenses exceed your take-home income. "
            "Review your budget before increasing investment contributions."
        )

    st.subheader("2. Emergency fund planner")

    st.write(
        f"Your selected target is "
        f"${emergency_target_amount:,.2f}."
    )

    st.progress(
        min(
            cash_savings / emergency_target_amount,
            1.0,
        )
        if emergency_target_amount > 0
        else 0.0
    )

    if emergency_gap == 0:
        st.success("Your cash savings meet the selected target.")
    else:
        st.info(
            f"You need another ${emergency_gap:,.2f} "
            "to reach your selected target."
        )

        if surplus > 0:
            months_to_target = math.ceil(
                emergency_gap / surplus
            )

            st.write(
                f"If you saved your entire modeled monthly surplus, "
                f"you could reach the target in approximately "
                f"{months_to_target} months."
            )
        else:
            st.write(
                "A positive monthly surplus is needed to estimate "
                "a savings timeline using this method."
            )

    st.subheader("3. Net worth calculator")

    col3, col4 = st.columns(2)

    with col3:
        other_assets = st.number_input(
            "Other assets ($)",
            min_value=0.0,
            value=15000.0,
            step=500.0,
            key="fh_assets",
            help="For example, investments or property. Do not include cash savings again.",
        )

    with col4:
        liabilities = st.number_input(
            "Total debts and liabilities ($)",
            min_value=0.0,
            value=8000.0,
            step=500.0,
            key="fh_liabilities",
        )

    net_worth = cash_savings + other_assets - liabilities

    st.metric(
        "Estimated net worth",
        f"${net_worth:,.2f}",
    )

    net_worth_chart = px.bar(
        pd.DataFrame({
            "Category": [
                "Cash savings",
                "Other assets",
                "Liabilities",
            ],
            "Amount": [
                cash_savings,
                other_assets,
                -liabilities,
            ],
        }),
        x="Category",
        y="Amount",
        title="Assets and liabilities",
    )

    net_worth_chart.update_layout(
        template="plotly_white",
        yaxis_title="Amount ($)",
        yaxis_tickprefix="$",
        yaxis_tickformat=",.0f",
    )

    st.plotly_chart(
        net_worth_chart,
        use_container_width=True,
    )

    st.subheader("4. Debt payoff calculator")

    debt_col1, debt_col2 = st.columns(2)

    with debt_col1:
        debt_balance = st.number_input(
            "Debt balance ($)",
            min_value=0.0,
            value=5000.0,
            step=250.0,
            key="fh_debt_balance",
        )

        debt_rate = st.number_input(
            "Annual interest rate (%)",
            min_value=0.0,
            max_value=100.0,
            value=18.0,
            step=0.5,
            key="fh_debt_rate",
        )

    with debt_col2:
        debt_payment = st.number_input(
            "Monthly debt payment ($)",
            min_value=0.0,
            value=250.0,
            step=25.0,
            key="fh_debt_payment",
        )

    payoff = calculate_debt_payoff(
        debt_balance,
        debt_rate,
        debt_payment,
    )

    if payoff is None:
        st.error(
            "This payment is too low to pay off the debt under "
            "the selected interest rate, or the timeline is too long. "
            "Increase the monthly payment and recalculate."
        )
    elif payoff["months"] == 0:
        st.success("There is no debt balance to pay off.")
    else:
        months = payoff["months"]

        st.metric(
            "Estimated payoff time",
            f"{months // 12} years, {months % 12} months",
        )

        result_col1, result_col2 = st.columns(2)

        result_col1.metric(
            "Total interest",
            f"${payoff['total_interest']:,.2f}",
        )

        result_col2.metric(
            "Total paid",
            f"${payoff['total_paid']:,.2f}",
        )

    st.caption(
        "Educational estimates only. Results exclude changes in income, "
        "unexpected expenses, fees, and changes to interest rates. "
        "This module does not provide personalized financial advice."
    )
