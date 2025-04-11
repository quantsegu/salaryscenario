import streamlit as st
import pandas as pd
import plotly.graph_objects as go

st.set_page_config(page_title="Income Scenario Calculator", layout="wide")

st.title("Income Scenario Calculator")
st.write("Adjust income and parameters for different scenarios in the Netherlands")

# Define the scenarios with their respective tax rates
base_scenarios = [
    {
        "scenario": "Regular Salary",
        "income_tax_rate": 0.3961,
        "social_security_rate": 0.0669,
        "needs_hourly": False
    },
    {
        "scenario": "ZZP (Self-employed)",
        "income_tax_rate": 0.3961,
        "self_employment_deduction": 2470,
        "needs_hourly": True
    },
    {
        "scenario": "BV with Full Salary",
        "income_tax_rate": 0.3961,
        "social_security_rate": 0.0669,
        "needs_hourly": True
    },
    {
        "scenario": "BV with €60k Salary",
        "income_tax_rate": 0.3961,
        "corporate_tax_rate": 0.25,
        "retained_income_ratio": 0.6,
        "social_security_rate": 0.0669,
        "needs_hourly": True
    },
    {
        "scenario": "BV with €60k + Dividend",
        "income_tax_rate": 0.3961,
        "corporate_tax_rate": 0.25,
        "dividend_tax_rate": 0.25,
        "retained_income_ratio": 0.6,
        "social_security_rate": 0.0669,
        "needs_hourly": True
    },
    {
        "scenario": "Payrolling[No BV]",
        "income_tax_rate": 0.4665,
        "social_security_rate": 0.0669,
        "needs_hourly": True
    }
]

# Create sections for income and expense inputs
st.subheader("Income Parameters")
income_cols = st.columns(len(base_scenarios))
scenarios = []

for idx, (col, base_scenario) in enumerate(zip(income_cols, base_scenarios)):
    with col:
        st.markdown(f"**{base_scenario['scenario']}**")
        
        if base_scenario["needs_hourly"]:
            hourly_rate = st.number_input(
                "Hourly Rate (€)",
                min_value=20,
                max_value=500,
                value=100,
                step=5,
                key=f"rate_{idx}"
            )
            hours_per_week = st.number_input(
                "Hours per Week",
                min_value=1,
                max_value=60,
                value=36,
                step=1,
                key=f"hours_{idx}"
            )
            # Calculate annual gross income (48 weeks per year)
            gross_income = hourly_rate * hours_per_week * 48
            st.write(f"Annual: €{gross_income:,.2f}")
        else:
            gross_income = st.number_input(
                "Annual Gross Income (€)",
                min_value=50000,
                max_value=500000,
                value=150000,
                step=5000,
                key=f"income_{idx}"
            )

st.subheader("Company Expenses")
expense_cols = st.columns(len(base_scenarios))
for idx, (col, base_scenario) in enumerate(zip(expense_cols, base_scenarios)):
    with col:
        company_expenses = st.number_input(
            "Additional Expenses (€)",
            min_value=0,
            max_value=100000,
            value=0,
            step=1000,
            key=f"expense_{idx}"
        )
        
        # Create complete scenario with all parameters
        scenario = base_scenario.copy()
        scenario["gross_income"] = gross_income
        scenario["company_expenses"] = company_expenses
        scenarios.append(scenario)

# Calculate net retention and its percentage for each scenario
results = []
for scenario in scenarios:
    scenario_type = scenario["scenario"]
    gross_income = scenario["gross_income"]
    company_expenses = scenario["company_expenses"]
    
    # Initialize tax components
    personal_tax = 0
    corporate_tax = 0
    dividend_tax = 0
    social_security = 0
    
    if "ZZP" in scenario_type:
        # Apply self-employment deduction before tax
        taxable_income = gross_income - scenario["self_employment_deduction"] - company_expenses
        personal_tax = taxable_income * scenario["income_tax_rate"]
        net_income = taxable_income - personal_tax
    
    elif "BV" in scenario_type:
        # Calculate salary portion (40% of gross for BV with €60k scenarios)
        if "€60k" in scenario_type:
            salary = min(60000, gross_income * 0.4)
        else:
            salary = gross_income
            
        personal_tax = salary * scenario["income_tax_rate"]
        
        # Calculate corporate portion
        corporate_income = gross_income - salary - company_expenses
        if corporate_income > 0:
            corporate_tax = corporate_income * scenario["corporate_tax_rate"]
            
            if "Dividend" in scenario_type:
                # Apply dividend tax on retained income after corporate tax
                dividend_amount = corporate_income - corporate_tax
                dividend_tax = dividend_amount * scenario["dividend_tax_rate"]
                net_income = (salary - personal_tax) + (dividend_amount - dividend_tax)
            else:
                net_income = (salary - personal_tax) + (corporate_income - corporate_tax)
        else:
            net_income = salary - personal_tax
        
        social_security = salary * scenario.get("social_security_rate", 0)
        net_income -= social_security
    
    else:
        # Regular salary scenarios
        taxable_income = gross_income - company_expenses
        personal_tax = taxable_income * scenario["income_tax_rate"]
        social_security = taxable_income * scenario.get("social_security_rate", 0)
        net_income = taxable_income - personal_tax - social_security
    
    # Store results with tax breakdown
    results.append({
        "Scenario": scenario_type,
        "Gross Income": gross_income,
        "Company Expenses": company_expenses,
        "Net Income": net_income,
        "Personal Tax": personal_tax,
        "Corporate Tax": corporate_tax,
        "Dividend Tax": dividend_tax,
        "Social Security": social_security,
        "Retention %": (net_income / gross_income) * 100
    })

# Convert results to DataFrame
df = pd.DataFrame(results)

# Create two columns for displaying results
col1, col2 = st.columns([2, 3])

with col1:
    st.subheader("Results Table")
    # Format the display DataFrame
    display_df = df.copy()
    for col in ["Gross Income", "Company Expenses", "Net Income", "Personal Tax", "Corporate Tax", "Dividend Tax", "Social Security"]:
        display_df[col] = display_df[col].apply(lambda x: f"€{x:,.2f}")
    display_df["Retention %"] = display_df["Retention %"].apply(lambda x: f"{x:.1f}%")
    st.table(display_df)

with col2:
    st.subheader("Income Breakdown")
    
    # Create stacked bar chart using plotly
    fig = go.Figure()
    
    # Add bars for each component
    components = [
        ("Net Income", "rgb(53, 167, 137)"),
        ("Personal Tax", "rgb(251, 133, 0)"),
        ("Corporate Tax", "rgb(255, 65, 54)"),
        ("Dividend Tax", "rgb(128, 0, 128)"),
        ("Social Security", "rgb(55, 83, 109)"),
        ("Company Expenses", "rgb(169, 169, 169)")
    ]
    
    for component, color in components:
        fig.add_trace(go.Bar(
            name=component,
            x=df["Scenario"],
            y=df[component],
            marker_color=color
        ))
    
    fig.update_layout(
        barmode='stack',
        height=500,
        yaxis_title="Amount in Euros",
        xaxis_title="Scenario",
        legend_title="Components",
        font=dict(size=12),
        xaxis_tickangle=-75
    )
    
    st.plotly_chart(fig, use_container_width=True)

# Add explanatory notes
st.markdown("""
### Notes:
- All calculations are simplified approximations
- Tax rates and deductions are based on 2023 Dutch tax system
- BV scenarios assume a 40/60 split between salary and retained earnings
- ZZP (self-employed) scenario includes self-employment deduction
- Annual income for hourly scenarios assumes 48 working weeks
- Colors in the chart represent:
  - 🟢 Green: Net Income (what you keep)
  - 🟠 Orange: Personal Income Tax
  - 🔴 Red: Corporate Tax
  - 🟣 Purple: Dividend Tax
  - 🔵 Blue: Social Security Contributions
  - ⚫ Gray: Company Expenses
""")
