"""
================================================================================
SEVERANCE & EXIT FINANCIAL ANALYSIS WEB APPLICATION
================================================================================

Web interface for comprehensive financial modeling of employment exit scenarios
in Germany. Built with Streamlit for easy hosting and sharing.

Author: Conti Exit Planning
Version: 2.0 Web
Last Updated: February 2026

Deploy: streamlit run app.py
================================================================================
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime
import math
from io import BytesIO
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak, Image
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
import os
import tempfile
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend for server environments

# ============================================================================
# PAGE CONFIGURATION
# ============================================================================

st.set_page_config(
    page_title="Severance & Exit Financial Calculator",
    page_icon="💼",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================================================
# CUSTOM CSS
# ============================================================================

st.markdown("""
    <style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 1rem;
    }
    .sub-header {
        font-size: 1.2rem;
        color: #666;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
    }
    .warning-box {
        background-color: #fff3cd;
        border-left: 4px solid #ffc107;
        padding: 1rem;
        margin: 1rem 0;
    }
    .info-box {
        background-color: #d1ecf1;
        border-left: 4px solid #17a2b8;
        padding: 1rem;
        margin: 1rem 0;
    }
    </style>
""", unsafe_allow_html=True)

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def get_state_from_plz(plz):
    """
    Maps German postal code (PLZ) to state (Bundesland).
    Returns tuple: (state_name, has_familiengeld, familiengeld_amount)
    """
    plz = int(plz)
    
    # Postal code ranges by state (ordered by specificity to avoid conflicts)
    # More specific ranges first, then broader ranges
    
    # Bayern (Bavaria) - multiple ranges including 89xxx
    if (80000 <= plz <= 87999 or 89000 <= plz <= 89999 or 91000 <= plz <= 94999):
        return ("Bayern (Bavaria)", True, 250)  # Bayerisches Familiengeld
    
    # Sachsen (Saxony)
    elif 1000 <= plz <= 1999 or 2600 <= plz <= 2999 or 4000 <= plz <= 4999:
        return ("Sachsen (Saxony)", True, 200)  # Landeserziehungsgeld
    
    # Thüringen (Thuringia)
    elif 96000 <= plz <= 99999 or 7000 <= plz <= 7999:
        return ("Thüringen (Thuringia)", True, 200)  # Thüringer Familiengeld
    
    # Berlin
    elif 10000 <= plz <= 14999:
        return ("Berlin", False, 0)
    
    # Brandenburg
    elif 3000 <= plz <= 3999 or 14400 <= plz <= 16999 or 19300 <= plz <= 19357:
        return ("Brandenburg", False, 0)
    
    # Mecklenburg-Vorpommern
    elif 17000 <= plz <= 19999 and not (19300 <= plz <= 19357):
        return ("Mecklenburg-Vorpommern", False, 0)
    
    # Hamburg
    elif 20000 <= plz <= 21999 or 22000 <= plz <= 22999 or 27000 <= plz <= 27999:
        return ("Hamburg", False, 0)
    
    # Schleswig-Holstein
    elif 24000 <= plz <= 25999 or 23000 <= plz <= 23999:
        return ("Schleswig-Holstein", False, 0)
    
    # Bremen
    elif 28000 <= plz <= 28999 or 26000 <= plz <= 27999 and not (27000 <= plz <= 27999):
        return ("Bremen", False, 0)
    
    # Niedersachsen (Lower Saxony)
    elif 26000 <= plz <= 27999 or 29000 <= plz <= 31999 or 37000 <= plz <= 38999 or 48000 <= plz <= 49999:
        return ("Niedersachsen (Lower Saxony)", False, 0)
    
    # Nordrhein-Westfalen (NRW)
    elif (32000 <= plz <= 33999 or 34000 <= plz <= 36999 or 40000 <= plz <= 47999 or 
          50000 <= plz <= 53999 or 57000 <= plz <= 59999):
        return ("Nordrhein-Westfalen (NRW)", False, 0)
    
    # Hessen (Hesse)
    elif 34000 <= plz <= 36999 or 60000 <= plz <= 64999 or 65000 <= plz <= 66999:
        return ("Hessen (Hesse)", False, 0)
    
    # Rheinland-Pfalz (Rhineland-Palatinate)
    elif 54000 <= plz <= 56999 or 66000 <= plz <= 67999:
        return ("Rheinland-Pfalz (Rhineland-Palatinate)", False, 0)
    
    # Saarland
    elif 66000 <= plz <= 66999:
        return ("Saarland", False, 0)
    
    # Baden-Württemberg (excluding 89xxx which is Bavaria)
    elif 68000 <= plz <= 69999 or 70000 <= plz <= 76999 or 77000 <= plz <= 79999 or 88000 <= plz <= 88999:
        return ("Baden-Württemberg", False, 0)
    
    # Sachsen-Anhalt (Saxony-Anhalt)
    elif 6000 <= plz <= 6999 or 38000 <= plz <= 39999:
        return ("Sachsen-Anhalt (Saxony-Anhalt)", False, 0)
    
    else:
        return ("Unknown", False, 0)

# ============================================================================
# CALCULATION FUNCTIONS
# ============================================================================

def calculate_fuenftelregelung_tax(annual_salary, severance_amount, net_rate_on_salary):
    """
    Calculates the tax on severance using the Fünftelregelung (five-year rule).
    
    Args:
        annual_salary: Gross annual salary (EUR)
        severance_amount: Gross severance payment (EUR)
        net_rate_on_salary: Net salary rate (e.g., 0.67 for Tax Class 3)
    
    Returns:
        tuple: (net_severance, tax_on_severance, effective_tax_rate)
    """
    tax_rate_salary = 1 - net_rate_on_salary
    tax_on_salary = annual_salary * tax_rate_salary
    
    fifth_of_severance = severance_amount / 5
    combined_income = annual_salary + fifth_of_severance
    
    tax_on_combined = combined_income * tax_rate_salary
    tax_per_fifth = tax_on_combined - tax_on_salary
    total_sev_tax = tax_per_fifth * 5
    
    net_severance = severance_amount - total_sev_tax
    effective_rate = total_sev_tax / severance_amount if severance_amount > 0 else 0
    
    return net_severance, total_sev_tax, effective_rate

def calculate_scenario(annual_salary, severance_months, tax_class, has_children, 
                       monthly_expenses, sperrzeit_months=3, num_children=0, state_name="", 
                       has_familiengeld=False, familiengeld_amount=0, child_ages=None, months_worked_2026=6):
    """
    Calculate complete financial scenario for given parameters.
    
    Returns:
        dict: Comprehensive financial breakdown
    """
    # Tax rates based on class
    if tax_class == "Tax Class 3 (Married)":
        net_rate_salary = 0.67
    else:  # Tax Class 1
        net_rate_salary = 0.60
    
    # ALG1 rate
    alg1_rate = 0.67 if has_children else 0.60
    
    # Kindergeld (child benefit) - €250 per child per month (2026 rates)
    kindergeld_monthly = 250 * num_children if has_children else 0
    
    # Familiengeld (state-specific benefit for children aged 1-3)
    # Count eligible children (ages 1-3)
    num_eligible_familiengeld = 0
    if has_children and has_familiengeld and child_ages:
        num_eligible_familiengeld = sum(1 for age in child_ages if 1 <= age <= 3)
    
    familiengeld_monthly = familiengeld_amount * num_eligible_familiengeld if has_familiengeld else 0
    
    # Calculate monthly values
    monthly_gross = annual_salary / 12
    monthly_net = monthly_gross * net_rate_salary
    
    # Severance calculation
    gross_severance = monthly_gross * severance_months
    net_severance, sev_tax, sev_tax_rate = calculate_fuenftelregelung_tax(
        annual_salary, gross_severance, net_rate_salary
    )
    
    # Salary for 2026 (based on months worked)
    salary_2026 = monthly_net * months_worked_2026
    
    # ALG1 calculation - Maximum 12 months total
    alg1_monthly = monthly_net * alg1_rate
    
    # 2026: No ALG1 during sperrzeit, then remaining months in year after work period
    months_remaining_2026 = 12 - months_worked_2026
    months_alg1_2026 = max(0, months_remaining_2026 - sperrzeit_months)  # Remaining months in 2026 after sperrzeit
    alg1_2026 = alg1_monthly * months_alg1_2026
    
    # Kindergeld for 2026 (full year regardless of employment)
    kindergeld_2026 = kindergeld_monthly * 12
    familiengeld_2026 = familiengeld_monthly * 12
    
    # 2027: ALG1 is capped at 12 months total, so subtract what was used in 2026
    months_alg1_2027 = max(0, 12 - months_alg1_2026)  # Remaining ALG1 months out of 12 total
    alg1_2027 = alg1_monthly * months_alg1_2027
    kindergeld_2027 = kindergeld_monthly * 12
    familiengeld_2027 = familiengeld_monthly * 12
    
    # Total ALG1 duration
    total_alg1_months = months_alg1_2026 + months_alg1_2027
    
    # Total calculations for reference (including salary)
    total_2026 = salary_2026 + net_severance + alg1_2026 + kindergeld_2026 + familiengeld_2026
    total_2027 = alg1_2027 + kindergeld_2027 + familiengeld_2027
    total_2_years = total_2026 + total_2027
    
    # Calculate income as percentage of annual salary
    income_percentage_2026 = (total_2026 / annual_salary * 100) if annual_salary > 0 else 0
    income_percentage_2027 = (total_2027 / annual_salary * 100) if annual_salary > 0 else 0
    
    # Runway calculation - ONLY count money available AFTER exit
    # Salary is consumed by expenses during working months, so DON'T include it
    # Only severance + benefits are available for runway after exit
    cash_after_exit = net_severance + alg1_2026 + alg1_2027 + kindergeld_2026 + kindergeld_2027 + familiengeld_2026 + familiengeld_2027
    
    # Split cash after exit by year
    cash_after_exit_2026 = net_severance + alg1_2026 + kindergeld_2026 + familiengeld_2026
    cash_after_exit_2027 = alg1_2027 + kindergeld_2027 + familiengeld_2027
    
    # Runway is how long this cash lasts from exit date onwards
    runway_months = cash_after_exit / monthly_expenses if monthly_expenses > 0 else 0
    
    # Calculate what portion of total income is actually available (excluding salary)
    total_income_after_exit = cash_after_exit
    
    return {
        'monthly_gross': monthly_gross,
        'monthly_net': monthly_net,
        'gross_severance': gross_severance,
        'sev_tax': sev_tax,
        'sev_tax_rate': sev_tax_rate,
        'net_severance': net_severance,
        'salary_2026': salary_2026,
        'months_worked_2026': months_worked_2026,
        'alg1_monthly': alg1_monthly,
        'alg1_2026': alg1_2026,
        'alg1_2027': alg1_2027,
        'months_alg1_2027': months_alg1_2027,
        'total_alg1_months': total_alg1_months,
        'kindergeld_monthly': kindergeld_monthly,
        'kindergeld_2026': kindergeld_2026,
        'kindergeld_2027': kindergeld_2027,
        'familiengeld_monthly': familiengeld_monthly,
        'familiengeld_2026': familiengeld_2026,
        'familiengeld_2027': familiengeld_2027,
        'total_2026': total_2026,
        'total_2027': total_2027,
        'income_percentage_2026': income_percentage_2026,
        'income_percentage_2027': income_percentage_2027,
        'total_2_years': total_2_years,
        'runway_months': runway_months,
        'cash_after_exit': cash_after_exit,
        'cash_after_exit_2026': cash_after_exit_2026,
        'cash_after_exit_2027': cash_after_exit_2027,
        'total_income_after_exit': total_income_after_exit,
        'sperrzeit_months': sperrzeit_months,
        'state_name': state_name,
        'has_familiengeld': has_familiengeld,
        'num_eligible_familiengeld': num_eligible_familiengeld,
        'months_remaining_2026': months_remaining_2026,
        'months_alg1_2026': months_alg1_2026
    }

# ============================================================================
# MAIN APPLICATION
# ============================================================================

def main():
    # Header
    st.markdown('<div class="main-header">💼 Severance & Exit Financial Calculator</div>', 
                unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Comprehensive Financial Planning for Employment Exit in Germany</div>', 
                unsafe_allow_html=True)
    
    # Sidebar - Quick Info
    st.sidebar.title("ℹ️ About This Calculator")
    st.sidebar.info(
        "This calculator uses the **Fünftelregelung** (5-year rule) for severance tax calculation, "
        "providing accurate estimates of your financial runway after employment exit."
    )
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 📚 Quick Reference")
    st.sidebar.markdown("""
    **Key Information:**
    - ALG1: 60-67% of net salary
    - Kindergeld: €250/child/month
    - Tax Class 3: ~67% net
    - Tax Class 1: ~60% net
    
    **👉 See full FAQ section below for:**
    - Where to apply for ALG1
    - Tax system details
    - Severance negotiation tips
    - Required documents
    - Health insurance options
    """)
    st.sidebar.markdown("---")
    st.sidebar.markdown("### ⚠️ Important")
    st.sidebar.warning(
        "Apply for unemployment benefits within **3 days** of receiving termination notice!"
    )
    
    # ========================================================================
    # INPUT PARAMETERS - MAIN AREA
    # ========================================================================
    
    st.header("📝 Input Your Financial Parameters")
    
    # Row 1: Employment & Exit Details
    with st.expander("💼 Employment & Exit Details", expanded=True):
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            annual_salary = st.number_input(
                "Annual Gross Salary (€)",
                min_value=30000,
                max_value=300000,
                value=90000,
                step=5000,
                help="Your current annual gross salary before taxes"
            )
        
        with col2:
            months_worked_2026 = st.slider(
                "Months of Salary in 2026",
                min_value=1,
                max_value=12,
                value=6,
                step=1,
                help="How many months of salary you will receive before exit"
            )
        
        with col3:
            severance_months = st.slider(
                "Severance Package (Months)",
                min_value=0,
                max_value=24,
                value=6,
                step=1,
                help="Number of months of gross salary as severance"
            )
        
        with col4:
            sperrzeit_months = st.slider(
                "Sperrzeit - Waiting Period (Months)",
                min_value=0,
                max_value=6,
                value=0,
                step=1,
                help="Months with no ALG1 (typically 3 for voluntary exits, 0 for company-initiated)"
            )
    
    # Row 2: Tax Class & Family
    with st.expander("🏠 Tax Class & Family Situation", expanded=True):
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            plz = st.text_input(
                "Postal Code (PLZ)",
                value="89231",
                max_chars=5,
                help="Enter your German postal code to determine state-specific benefits"
            )
        
        with col2:
            tax_class = st.radio(
                "Tax Class (Steuerklasse)",
                ["Tax Class 3 (Married)", "Tax Class 1 (Single)"],
                help="Tax Class 3: Married - more favorable\nTax Class 1: Single - higher tax"
            )
        
        with col3:
            has_children = st.checkbox(
                " I have dependent children",
                value=False,
                help="Increases ALG1 to 67% + adds Kindergeld + state benefits"
            )
        
        with col4:
            if has_children:
                num_children = st.select_slider(
                    "Number of Children",
                    options=[1, 2, 3, 4, 5],
                    value=1,
                    help="Each child adds €250/month Kindergeld"
                )
            else:
                num_children = 0
        
        # Ask for child ages when children are selected
        child_ages = []
        if has_children and num_children > 0:
            st.markdown("**👶 Children's Ages (for Familiengeld eligibility)**")
            age_cols = st.columns(min(num_children, 5))  # Max 5 columns
            for i in range(num_children):
                with age_cols[i % 5]:
                    age = st.number_input(
                        f"Child {i+1} Age",
                        min_value=0,
                        max_value=25,
                        value=2,
                        step=1,
                        help="Familiengeld available for ages 1-3",
                        key=f"child_age_{i}"
                    )
                    child_ages.append(age)
        
        # Determine state and Familiengeld eligibility
        if plz and len(plz) >= 4:
            try:
                state_name, has_familiengeld, familiengeld_amount = get_state_from_plz(plz)
                if has_familiengeld and has_children:
                    # Count eligible children (ages 1-3)
                    num_eligible = sum(1 for age in child_ages if 1 <= age <= 3) if child_ages else 0
                    if num_eligible > 0:
                        st.success(f"📍 **{state_name}** - Familiengeld: €{familiengeld_amount}/month × {num_eligible} child{'ren' if num_eligible > 1 else ''} (ages 1-3)")
                    else:
                        st.info(f"📍 **{state_name}** - Familiengeld available for children ages 1-3 only")
                elif not has_children:
                    st.info(f"📍 **{state_name}** - No additional state family benefits (select 'I have dependent children' to add benefits)")
                else:
                    st.info(f"📍 **{state_name}** - No additional state family benefits available")
            except:
                state_name, has_familiengeld, familiengeld_amount = "Unknown", False, 0
                st.warning("Invalid postal code")
        else:
            state_name, has_familiengeld, familiengeld_amount = "Unknown", False, 0
    
    # Row 3: Monthly Expenses
    with st.expander("💶 Monthly Expenses Breakdown", expanded=True):
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**🏠 Housing & Utilities**")
            rent = st.number_input(
                "Rent / Mortgage (€)",
                min_value=0,
                max_value=5000,
                value=1200,
                step=50,
                help="Monthly housing costs"
            )
            
            utilities = st.number_input(
                "Utilities (€)",
                min_value=0,
                max_value=1000,
                value=250,
                step=25,
                help="Electricity, internet, Rundfunkbeitrag"
            )
            
            st.markdown("**🛒 Food & Transport**")
            groceries = st.number_input(
                "Groceries (€)",
                min_value=0,
                max_value=2000,
                value=600,
                step=50,
                help="Monthly food and household items"
            )
        
        with col2:
            st.markdown("**🚗 Transportation**")
            transport = st.number_input(
                "Car / Transport (€)",
                min_value=0,
                max_value=1500,
                value=300,
                step=50,
                help="Car, fuel, insurance, or public transport"
            )
            
            st.markdown("**👶 Other Expenses**")
            kindergarten = st.number_input(
                "Kindergarten Fees (€)",
                min_value=0,
                max_value=1500,
                value=0 if not has_children else 300,
                step=50,
                help="Monthly childcare costs"
            )
            
            other_expenses = st.number_input(
                "Other Expenses (€)",
                min_value=0,
                max_value=2000,
                value=650,
                step=50,
                help="Insurance, phone, subscriptions, etc."
            )
    
    # Calculate total monthly expenses
    monthly_expenses = rent + groceries + transport + utilities + kindergarten + other_expenses
    
    # Show expense summary
    st.markdown(f"**Total Monthly Expenses: €{monthly_expenses:,.0f}**")
    
    st.markdown("---")
    
    # Calculate scenario
    results = calculate_scenario(
        annual_salary, severance_months, tax_class, has_children,
        monthly_expenses, sperrzeit_months, num_children,
        state_name, has_familiengeld, familiengeld_amount, child_ages, months_worked_2026
    )
    
    # ========================================================================
    # ANALYSIS SECTION - Financial Runway & Severance Recommendation
    # ========================================================================
    
    st.header("📊 Financial Analysis & Recommendations")
    
    # Financial Runway Information
    st.info(
        f"💡 **Financial Runway:** Your financial runway after exit is **{results['runway_months']:.1f} months**. "
        f"This is calculated from your exit date onwards using €{results['cash_after_exit']:,.0f} (severance + benefits) "
        f"divided by €{monthly_expenses:,.0f}/month expenses. "
        f"During your {months_worked_2026} working months, your salary covers those expenses. "
        f"ALG1 is capped at **12 months total** ({results['months_alg1_2026']} months in 2026 + {results['months_alg1_2027']} months in 2027)."
    )
    
    st.markdown("---")
    
    # Severance Package Recommendation
    with st.expander("💡 Severance Package Recommendation", expanded=True):
        
        # Calculate expenses
        months_after_exit_2026 = 12 - months_worked_2026
        expenses_2026 = monthly_expenses * months_after_exit_2026
        expenses_2027 = monthly_expenses * 12
        
        # Calculate total deficit/surplus
    total_income_after_exit = results['cash_after_exit']
    total_expenses_projected = expenses_2026 + expenses_2027
    surplus_deficit = total_income_after_exit - total_expenses_projected
    
    monthly_gross = results['monthly_gross']
    
    # Calculate net severance per additional month (using same tax rate)
    net_severance_rate = results['net_severance'] / results['gross_severance'] if results['gross_severance'] > 0 else 0.75
    net_per_severance_month = monthly_gross * net_severance_rate
    
    # Current severance months
    current_sev_months = severance_months
    
    # Calculate break-even severance months (exact)
    months_needed_for_breakeven = (total_expenses_projected - total_income_after_exit) / net_per_severance_month
    breakeven_months = current_sev_months + months_needed_for_breakeven
    
    # Create three options: deficit, break-even, surplus
    option_deficit = max(1, int(breakeven_months - 1))  # 1 month less than break-even
    option_breakeven = max(1, math.ceil(breakeven_months))  # Rounded up to break-even
    option_surplus = max(1, int(breakeven_months + 2))  # 2 months more than break-even
    
    recommended_options = [
        ("deficit", option_deficit),
        ("breakeven", option_breakeven),
        ("surplus", option_surplus)
    ]
    
    if surplus_deficit < 0:
        # Deficit scenario
        deficit_amount = -surplus_deficit
        
        # Calculate additional months needed
        additional_months_needed = deficit_amount / net_per_severance_month
        
        st.warning(
            f"⚠️ **You have a deficit of €{deficit_amount:,.0f}** to survive through 2027 with your current expenditure of €{monthly_expenses:,.0f}/month. "
            f"To cover your expenses without financial difficulties, consider negotiating a higher severance package."
        )
        
        col_rec1, col_rec2 = st.columns([2, 3])
        
        with col_rec1:
            st.markdown("**💼 Recommended Severance:**")
            for option_type, option in recommended_options:
                gross_option = monthly_gross * option
                net_option = gross_option * net_severance_rate
                projected_surplus = total_income_after_exit - total_expenses_projected + (net_option - results['net_severance'])
                
                if abs(projected_surplus) < net_per_severance_month * 0.1:  # Within 10% of a month = break-even
                    st.info(f"⚖️ **{option} months** → Break-even: €{projected_surplus:,.0f}")
                elif projected_surplus >= 0:
                    st.success(f"✅ **{option} months** → Surplus: €{projected_surplus:,.0f}")
                else:
                    st.warning(f"⚠️ **{option} months** → Deficit: €{-projected_surplus:,.0f}")
        
        with col_rec2:
            st.markdown("**📈 Why negotiate higher severance:**")
            st.markdown(
                f"- Each additional severance month adds ~€{net_per_severance_month:,.0f} to your runway\n"
                f"- You need ~{additional_months_needed:.1f} more months to break even\n"
                f"- Recommended: **{option_breakeven}+ months** to survive 2027 comfortably\n"
                f"- This ensures you can cover €{total_expenses_projected:,.0f} total expenses"
            )
    else:
        # Surplus scenario - still show options for better financial security
        surplus_amount = surplus_deficit
        
        st.success(
            f"**You have a surplus of €{surplus_amount:,.0f} for survival in 2026 and 2027** with your current {current_sev_months}-month severance package. "
            f"However, negotiating additional months can provide even more financial security."
        )
        
        col_rec1, col_rec2 = st.columns([2, 3])
        
        with col_rec1:
            st.markdown("**💼 Severance Options:**")
            for option_type, option in recommended_options:
                gross_option = monthly_gross * option
                net_option = gross_option * net_severance_rate
                projected_surplus = total_income_after_exit - total_expenses_projected + (net_option - results['net_severance'])
                
                if abs(projected_surplus) < net_per_severance_month * 0.1:  # Within 10% of a month = break-even
                    st.info(f"⚖️ **{option} months** → Break-even: €{projected_surplus:,.0f}")
                elif projected_surplus >= 0:
                    st.success(f"✅ **{option} months** → Surplus: €{projected_surplus:,.0f}")
                else:
                    st.warning(f"⚠️ **{option} months** → Deficit: €{-projected_surplus:,.0f}")
        
        with col_rec2:
            st.markdown("**📈 Benefits of higher severance:**")
            st.markdown(
                f"- Each additional severance month adds ~€{net_per_severance_month:,.0f} to your safety net\n"
                f"- Current surplus: €{surplus_amount:,.0f}\n"
                f"- More months = more time to find the right opportunity\n"
                f"- Additional buffer for unexpected expenses"
            )
    
    # ========================================================================
    # DETAILED BREAKDOWN
    # ========================================================================
    
    with st.expander("📋 Detailed Financial Breakdown", expanded=False):
        
        tab1, tab2 = st.tabs(["🥧 Income vs Expenses", "📊 Breakdown Table"])
    
    with tab1:
        # Income vs Expenses Pie Charts
        st.subheader("Income vs Expenses Analysis")
        
        # Calculate expenses
        months_after_exit_2026 = 12 - months_worked_2026
        expenses_2026 = monthly_expenses * months_after_exit_2026
        expenses_2027 = monthly_expenses * 12
        
        # Build 2026 data
        data_2026 = {
            'Category': [],
            'Amount': []
        }
        
        # Add 2026 income sources
        if results['net_severance'] > 0:
            data_2026['Category'].append('Severance')
            data_2026['Amount'].append(results['net_severance'])
        
        if results['alg1_2026'] > 0:
            data_2026['Category'].append(f'ALG1 ({results["months_alg1_2026"]}mo)')
            data_2026['Amount'].append(results['alg1_2026'])
        
        if has_children and results['kindergeld_2026'] > 0:
            data_2026['Category'].append('Kindergeld')
            data_2026['Amount'].append(results['kindergeld_2026'])
        
        if has_familiengeld and results['familiengeld_2026'] > 0:
            data_2026['Category'].append('Familiengeld')
            data_2026['Amount'].append(results['familiengeld_2026'])
        
        # Add 2026 expenses
        data_2026['Category'].append('Expenses')
        data_2026['Amount'].append(expenses_2026)
        
        df_2026 = pd.DataFrame(data_2026)
        
        # Build 2027 data
        data_2027 = {
            'Category': [],
            'Amount': []
        }
        
        # Add 2027 income sources
        if results['alg1_2027'] > 0:
            data_2027['Category'].append(f'ALG1 ({results["months_alg1_2027"]}mo)')
            data_2027['Amount'].append(results['alg1_2027'])
        
        if has_children and results['kindergeld_2027'] > 0:
            data_2027['Category'].append('Kindergeld')
            data_2027['Amount'].append(results['kindergeld_2027'])
        
        if has_familiengeld and results['familiengeld_2027'] > 0:
            data_2027['Category'].append('Familiengeld')
            data_2027['Amount'].append(results['familiengeld_2027'])
        
        # Add 2027 expenses
        data_2027['Category'].append('Expenses')
        data_2027['Amount'].append(expenses_2027)
        
        df_2027 = pd.DataFrame(data_2027)
        
        # Create side-by-side columns for both years
        col_2026, col_2027 = st.columns(2)
        
        # Color sequence for pie charts
        color_sequence = ['#27AE60', '#3498DB', '#9B59B6', '#F39C12', '#E74C3C']
        
        # 2026 Section
        with col_2026:
            st.markdown("#### 📅 2026 Income vs Expenses")
            
            # Create 2026 pie chart
            fig_2026_pie = px.pie(
                df_2026,
                values='Amount',
                names='Category',
                hole=0.4,
                color_discrete_sequence=color_sequence
            )
            
            fig_2026_pie.update_traces(
                textposition='auto',
                textinfo='percent+label',
                hovertemplate='<b>%{label}</b><br>€%{value:,.0f}<br>%{percent}<extra></extra>'
            )
            
            fig_2026_pie.update_layout(
                height=400,
                showlegend=True,
                margin=dict(l=20, r=20, t=30, b=20)
            )
            
            st.plotly_chart(fig_2026_pie, use_container_width=True)
            
            # 2026 metrics
            total_income_2026 = results['cash_after_exit_2026']
            surplus_2026 = total_income_2026 - expenses_2026
            
            st.metric("Total Income", f"€{total_income_2026:,.0f}", "After exit")
            st.metric("Expenses", f"€{expenses_2026:,.0f}", f"{months_after_exit_2026} months")
            
            if surplus_2026 >= 0:
                st.success(f"✅ Surplus: €{surplus_2026:,.0f}")
            else:
                st.error(f"⚠️ Deficit: €{-surplus_2026:,.0f}")
        
        # 2027 Section
        with col_2027:
            st.markdown("#### 📅 2027 Income vs Expenses")
            
            # Create 2027 pie chart
            fig_2027_pie = px.pie(
                df_2027,
                values='Amount',
                names='Category',
                hole=0.4,
                color_discrete_sequence=color_sequence
            )
            
            fig_2027_pie.update_traces(
                textposition='auto',
                textinfo='percent+label',
                hovertemplate='<b>%{label}</b><br>€%{value:,.0f}<br>%{percent}<extra></extra>'
            )
            
            fig_2027_pie.update_layout(
                height=400,
                showlegend=True,
                margin=dict(l=20, r=20, t=30, b=20)
            )
            
            st.plotly_chart(fig_2027_pie, use_container_width=True)
            
            # 2027 metrics
            total_income_2027 = results['cash_after_exit_2027']
            surplus_2027 = total_income_2027 - expenses_2027
            
            st.metric("Total Income", f"€{total_income_2027:,.0f}", "After exit")
            st.metric("Expenses", f"€{expenses_2027:,.0f}", "12 months")
            
            if surplus_2027 >= 0:
                st.success(f"✅ Surplus: €{surplus_2027:,.0f}")
            else:
                st.error(f"⚠️ Deficit: €{-surplus_2027:,.0f}")
    
    with tab2:
        # Detailed breakdown table
        st.subheader("Complete Financial Breakdown")
        
        categories = [
            'Monthly Gross Salary',
            'Monthly Net Salary',
            '',
            'Gross Severance',
            'Severance Tax (Fünftelregelung)',
            'Effective Tax Rate on Severance',
            'Net Severance',
            '',
            f'{months_worked_2026}-Month Salary (2026)',
            'Net Severance Payment',
            f'2026 ALG1 ({results["months_alg1_2026"]} months)'
        ]
        amounts = [
            f"€{results['monthly_gross']:,.2f}",
            f"€{results['monthly_net']:,.2f}",
            '',
            f"€{results['gross_severance']:,.2f}",
            f"€{results['sev_tax']:,.2f}",
            f"{results['sev_tax_rate']*100:.2f}%",
            f"€{results['net_severance']:,.2f}",
            '',
            f"€{results['salary_2026']:,.2f}",
            f"€{results['net_severance']:,.2f}",
            f"€{results['alg1_2026']:,.2f}"
        ]
        
        if has_children:
            categories.append('2026 Kindergeld (12 months)')
            amounts.append(f"€{results['kindergeld_2026']:,.2f}")
        
        if has_children and has_familiengeld:
            categories.append(f'2026 Familiengeld ({state_name})')
            amounts.append(f"€{results['familiengeld_2026']:,.2f}")
        
        categories.extend(['2026 Total Cash', '', 'Monthly ALG1 Benefit'])
        amounts.extend([f"€{results['total_2026']:,.2f}", '', f"€{results['alg1_monthly']:,.2f}"])
        
        if has_children:
            categories.append(f'Monthly Kindergeld (€250 × {num_children})')
            amounts.append(f"€{results['kindergeld_monthly']:,.2f}")
        
        if has_children and has_familiengeld:
            categories.append(f'Monthly Familiengeld (€{familiengeld_amount} × {results["num_eligible_familiengeld"]} eligible)')
            amounts.append(f"€{results['familiengeld_monthly']:,.2f}")
        
        categories.append('2027 ALG1 (12 months)')
        amounts.append(f"€{results['alg1_2027']:,.2f}")
        
        if has_children:
            categories.append('2027 Kindergeld (12 months)')
            amounts.append(f"€{results['kindergeld_2027']:,.2f}")
        
        if has_children and has_familiengeld:
            categories.append(f'2027 Familiengeld ({state_name})')
            amounts.append(f"€{results['familiengeld_2027']:,.2f}")
        
        categories.extend([
            '',
            '2-Year Total Cash Available',
            '',
            'MONTHLY EXPENSES BREAKDOWN:',
            '  Rent / Mortgage',
            '  Groceries',
            '  Car / Transport',
            '  Utilities',
            '  Kindergarten Fees',
            '  Other Expenses',
            'Total Monthly Expenses',
            '',
            'Financial Runway'
        ])
        amounts.extend([
            '',
            f"€{results['total_2_years']:,.2f}",
            '',
            '',
            f"€{rent:,.2f}",
            f"€{groceries:,.2f}",
            f"€{transport:,.2f}",
            f"€{utilities:,.2f}",
            f"€{kindergarten:,.2f}",
            f"€{other_expenses:,.2f}",
            f"€{monthly_expenses:,.2f}",
            '',
            f"{results['runway_months']:.1f} months"
        ])
        
        breakdown_data = {
            'Category': categories,
            'Amount': amounts
        }
        
        df_breakdown = pd.DataFrame(breakdown_data)
        
        # Style the dataframe
        st.dataframe(
            df_breakdown,
            hide_index=True,
            use_container_width=True,
            height=600
        )
    
    # ========================================================================
    # FAQ SECTION (Combined with Important Information)
    # ========================================================================
    
    with st.expander("ℹ️ Important Information & FAQ", expanded=False):
        
        faq_col1, faq_col2 = st.columns(2)
        
        with faq_col1:
            st.subheader("🇩🇪 German Tax & Benefits System")
            
            st.markdown("##### 🔹 What is Fünftelregelung (five-year rule)?")
            st.markdown("""
            **Fünftelregelung** is a tax benefit for severance payments:
            
            **How It Works:**
            - Severance is divided by 5
            - One-fifth is added to your annual income
            - Tax is calculated on this combined income
            - The tax difference × 5 = your severance tax
            - Formula: Tax = 5 × (Tax[Salary + Sev/5] - Tax[Salary])
            
            **Benefits:**
            - Lower tax rate than normal income tax
            - Prevents severance from pushing you into higher tax bracket
            - Can save thousands of euros in taxes
            
            **Eligibility:**
            - Must be extraordinary income (one-time payment)
            - Must result from employment termination
            - Automatically applied by employer or tax advisor
            
            **This Calculator:** Uses Fünftelregelung for all severance calculations
            """)
            
            st.markdown("##### 🔹 Understanding German Tax Classes")
            st.markdown("""
            **Tax Class 3 (Married/Partnership):**
            - Most favorable tax rate
            - Net ≈ 67% of gross salary
            - ~33% total deductions (tax + social insurance)
            - Recommended if spouse earns significantly less
            
            **Tax Class 1 (Single/Divorced):**
            - Standard tax rate
            - Net ≈ 60% of gross salary
            - ~40% total deductions (tax + social insurance)
            - Default for unmarried individuals
            
            **These are simplified estimates.** Actual net varies by:
            - Church tax (8-9% of income tax if applicable)
            - Solidarity surcharge (Solidaritätszuschlag)
            - Municipal tax rates
            - Personal deductions
            """)
            
            st.markdown("##### 🔹 What are Kindergeld benefits?")
            st.markdown("""
            **Kindergeld (Child Benefit):**
            - **€250** per child per month (2026 rates)
            - Paid regardless of employment status
            - Continues during unemployment
            - Tax-free income for families
            - For children up to age 18 (25 if in education)
            
            **How to Apply:**
            - 🌐 [Familienkasse Official Website](https://www.arbeitsagentur.de/familie-und-kinder/kindergeld)
            - 📄 [Kindergeld Application Form](https://www.arbeitsagentur.de/datei/kg1-hauptantrag_ba013134.pdf)
            - Submit once, continues automatically
            """)
            
            st.markdown("##### 🔹 What is Familiengeld and am I eligible?")
            st.markdown("""
            **Familiengeld** is a state-specific benefit (additional to Kindergeld):
            
            **Bavaria (Bayern):**
            - 💶 €250/month per child aged 1-3
            - 🌐 [Application: Bavarian Family Benefits](https://www.zbfs.bayern.de/familie/familiengeld/)
            
            **Saxony (Sachsen):**
            - 💶 €200/month per child
            - 🌐 [Landeserziehungsgeld Application](https://www.lsnq.de/)
            
            **Thuringia (Thüringen):**
            - 💶 €200/month per child
            - 🌐 [Thüringer Familiengeld](https://landesverwaltungsamt.thueringen.de/)
            
            **Other States:** May have different programs - check your state's website
            
            **Paid in addition to Kindergeld** - both benefits run simultaneously
            """)
            
            st.subheader("📝 Unemployment Benefits (ALG1)")
            
            st.markdown("##### 🔹 Where do I apply for Arbeitslosengeld (ALG1)?")
            st.markdown("""
            **Apply at your local Agentur für Arbeit (Federal Employment Agency):**
            
            **Online Application:**
            - 🌐 [Arbeitsagentur Official Portal](https://www.arbeitsagentur.de/)
            - 📱 [eServices Portal for Online Registration](https://www.arbeitsagentur.de/eservices)
            
            **Steps to Apply:**
            1. Register as unemployed **immediately** after receiving notice of termination
            2. Submit application online or visit local office in person
            3. Attend mandatory registration appointment
            4. Provide required documents (ID, employment contract, severance agreement)
            
            **Important:** Apply within 3 days of receiving termination notice to avoid benefit delays!
            
            **Find Your Local Office:**
            - 📍 [Office Finder](https://www.arbeitsagentur.de/dienststellen)
            """)
            
            st.markdown("##### 🔹 How much is ALG1 and how long does it last?")
            st.markdown("""
            **ALG1 Payment Rates:**
            - **60%** of net salary (no children)
            - **67%** of net salary (with children)
            - Based on last 12 months of employment
            
            **Standard Duration:** 12 months (maximum under age 50)
            
            **Factors Affecting Duration:**
            - **Age:** Longer benefits for 50+ (up to 24 months)
            - **Contribution History:** Must have paid into unemployment insurance for 12+ months in last 2 years
            - **Previous Work:** Longer work history = longer benefits
            
            **After ALG1 Expires:**
            - ALG2 (Bürgergeld) - means-tested welfare
            - Lower payments based on basic needs
            - Requires asset disclosure
            """)
            
            st.markdown(f"##### 🔹 What is Sperrzeit (blocking period)?")
            st.markdown(f"""
            **Sperrzeit** is a penalty period where you receive **NO unemployment benefits** if you:
            - Voluntarily quit your job
            - Sign a termination agreement (Aufhebungsvertrag)
            - Are fired due to your own misconduct
            
            **Duration:** Usually **3 months** (12 weeks)
            
            **Your Scenario:** {sperrzeit_months} month{'s' if sperrzeit_months != 1 else ''} Sperrzeit
            
            **How to Avoid:**
            - Have employer initiate termination
            - Have valid reason for signing termination agreement
            - Document business restructuring or position elimination
            - Consult employment lawyer before signing
            
            **During Sperrzeit:** Live on severance payment and savings - this is factored into your financial runway above
            """)
        
        with faq_col2:
            st.subheader("⏱️ Your Timeline & Cash Flow")
            
            # Generate dynamic timeline based on months worked
            month_names_full = ['January', 'February', 'March', 'April', 'May', 'June', 
                               'July', 'August', 'September', 'October', 'November', 'December']
            salary_period = f"Jan-{month_names_full[months_worked_2026-1][:3]}: Regular salary ({months_worked_2026} months)"
            exit_month = month_names_full[months_worked_2026-1]
            
            st.markdown("##### 🔹 What is my projected timeline?")
            st.markdown(f"""
            **Working Period:** {months_worked_2026} months in 2026
            
            **2026 Cash Flow:**
            - {salary_period}
            - **{exit_month}:** Severance payment received (€{results['net_severance']:,.0f})
            - **Sperrzeit:** {sperrzeit_months} month{'s' if sperrzeit_months != 1 else ''} - NO benefits
            - **ALG1:** {results['months_alg1_2026']} month{'s' if results['months_alg1_2026'] != 1 else ''} (remaining 2026)
            
            **2027 Cash Flow:**
            - **ALG1:** {results['months_alg1_2027']} month{'s' if results['months_alg1_2027'] != 1 else ''} (ALG1 capped at 12 months total)
            - **Kindergeld:** {'Continues all year' if has_children else 'N/A - no children'}
            - **Familiengeld:** {'Continues for eligible children' if has_familiengeld else 'N/A'}
            
            **Financial Runway:** {results['runway_months']:.1f} months from exit date
            """)
            
            st.subheader("💼 Severance & Taxation")
            
            st.markdown("##### 🔹 How much severance should I negotiate?")
            st.markdown("""
            **Common Formulas:**
            - **Standard:** 0.5 months gross salary per year of service
            - **Good:** 1.0 month per year of service
            - **Excellent:** 1.5+ months per year of service
            
            **Factors Affecting Amount:**
            - Length of service (longer = more)
            - Age (older = higher)
            - Position level (senior = more)
            - Company financial situation
            - Legal risks for employer
            - Your negotiation leverage
            
            **Tips:**
            - Calculate your financial runway (use this tool!)
            - Account for Sperrzeit period (3 months no benefits)
            - Consider job market conditions in your field
            - Aim for 12-18 months total runway minimum
            
            **This Calculator's Recommendation:** See "Severance Package Recommendation" section above for personalized guidance
            """)
            
            st.markdown("##### 🔹 Do I need a tax advisor (Steuerberater)?")
            st.markdown("""
            **Recommended If:**
            - ✅ Large severance payment (€50,000+)
            - ✅ Complex tax situation (multiple income sources)
            - ✅ Want to optimize Fünftelregelung application
            - ✅ Have investments or rental income
            - ✅ Need help with tax declaration
            
            **Services Provided:**
            - Calculate exact severance tax
            - File tax return with optimal deductions
            - Advise on payment timing (year-end vs. new year)
            - Handle negotiations with Finanzamt
            
            **Cost:** Usually €500-€1,500 (tax-deductible!)
            
            **Find an Advisor:**
            - 🌐 [Steuerberater Search](https://www.bstbk.de/de/)
            """)
            
            st.subheader("📋 Documentation & Process")
            
            st.markdown("##### 🔹 What documents do I need for exit process?")
            st.markdown("""
            **For ALG1 Application:**
            - ✅ Termination letter (Kündigungsschreiben)
            - ✅ Severance agreement (Aufhebungsvertrag)
            - ✅ Work certificate (Arbeitszeugnis)
            - ✅ Tax card (Lohnsteuerkarte/eID)
            - ✅ Social security card (Sozialversicherungsausweis)
            - ✅ Proof of identity (Personalausweis)
            - ✅ Bank details (IBAN)
            
            **For Tax Return:**
            - ✅ Severance payment confirmation
            - ✅ Income statements (Lohnsteuerbescheinigung)
            - ✅ Employment contract
            
            **Keep Copies:** Store all documents for 10+ years
            """)
            
            st.markdown("##### 🔹 What are my health insurance options?")
            st.markdown("""
            **During ALG1:**
            - Continue in gesetzliche Krankenversicherung (public health insurance)
            - Arbeitsagentur pays your premiums automatically
            - No change in coverage
            - Family members remain covered
            
            **If Privately Insured (PKV):**
            - Must stay in PKV or switch to public
            - Arbeitsagentur pays subsidy (up to public insurance rate)
            - You pay the difference if PKV is more expensive
            - Consider switching to reduce costs
            
            **Important:** Health insurance is **mandatory** - don't let coverage lapse!
            """)
    
    # ========================================================================
    # DISCLAIMERS
    # ========================================================================
    
    st.markdown("---")
    st.markdown(
        '<div class="warning-box">'
        '<strong>⚠️ Important Disclaimers:</strong><br>'
        '• This is a PLANNING TOOL, not professional tax or financial advice<br>'
        '• Tax calculations are simplified estimates based on average rates<br>'
        '• Actual taxes vary by church tax, solidarity surcharge, municipal rates, and deductions<br>'
        '• Consult a Steuerberater (tax advisor) for precise calculations<br>'
        '• ALG1 eligibility and duration depend on contribution history and age<br>'
        '• Employment law varies - seek legal counsel for severance negotiations'
        '</div>',
        unsafe_allow_html=True
    )
    
    # Developer Credit
    st.markdown("---")
    st.markdown(
        '<div style="text-align: center; padding: 1rem; color: #666;">'
        '<strong>Developed by:</strong><br>'
        'Vinod Kumar Neelakantam<br>'
        '<a href="https://www.linkedin.com/in/vinodneelakantam/" target="_blank" style="color: #0077b5;">'
        'https://www.linkedin.com/in/vinodneelakantam/</a>'
        '</div>',
        unsafe_allow_html=True
    )
    
    # ========================================================================
    # EXPORT OPTIONS
    # ========================================================================
    
    st.header("📥 Export Results")
    
    # Name input for personalized PDF
    col_name, col_btn = st.columns([3, 1])
    with col_name:
        user_name = st.text_input(
            "Your Name (for personalized PDF)",
            value="",
            placeholder="e.g., John Doe",
            help="Enter your name to personalize the PDF report"
        )
    
    # Create export data
    export_params = [
        'Annual Gross Salary',
        'Months Worked in 2026',
        'Severance Package (Months)',
        'Tax Class',
        'Postal Code (PLZ)',
        'State (Bundesland)',
        'Dependent Children',
        'Number of Children',
        '',
        'MONTHLY EXPENSES:',
        'Rent / Mortgage',
        'Groceries',
        'Car / Transport',
        'Utilities',
        'Kindergarten Fees',
        'Other Expenses',
        'Total Monthly Expenses',
        'Sperrzeit (Months)',
    ]
    
    export_values = [
        f"€{annual_salary:,}",
        f"{months_worked_2026}",
        f"{severance_months}",
        tax_class,
        f"{plz}",
        f"{state_name}",
        'Yes' if has_children else 'No',
        f"{num_children}" if has_children else 'N/A',
        '',
        '',
        f"€{rent:,}",
        f"€{groceries:,}",
        f"€{transport:,}",
        f"€{utilities:,}",
        f"€{kindergarten:,}",
        f"€{other_expenses:,}",
        f"€{monthly_expenses:,}",
        f"{sperrzeit_months}",
    ]
    
    export_params.extend([
        '',
        'CALCULATED RESULTS:',
        'Monthly Gross Salary',
        'Monthly Net Salary',
        'Gross Severance',
        'Severance Tax',
        'Effective Severance Tax Rate',
        'Net Severance',
        '',
        f'{months_worked_2026}-Month Salary (2026)',
        '2026 ALG1',
    ])
    
    export_values.extend([
        '',
        '',
        f"€{results['monthly_gross']:,.2f}",
        f"€{results['monthly_net']:,.2f}",
        f"€{results['gross_severance']:,.2f}",
        f"€{results['sev_tax']:,.2f}",
        f"{results['sev_tax_rate']*100:.2f}%",
        f"€{results['net_severance']:,.2f}",
        '',
        f"€{results['salary_2026']:,.2f}",
        f"€{results['alg1_2026']:,.2f}",
    ])
    
    if has_children:
        export_params.append('2026 Kindergeld')
        export_values.append(f"€{results['kindergeld_2026']:,.2f}")
    
    export_params.append('2026 Total')
    export_values.append(f"€{results['total_2026']:,.2f}")
    
    export_params.extend(['', 'Monthly ALG1'])
    export_values.extend(['', f"€{results['alg1_monthly']:,.2f}"])
    
    if has_children:
        export_params.append('Monthly Kindergeld')
        export_values.append(f"€{results['kindergeld_monthly']:,.2f}")
    
    if has_children and has_familiengeld:
        export_params.append(f'Monthly Familiengeld ({state_name})')
        export_values.append(f"€{results['familiengeld_monthly']:,.2f}")
    
    export_params.append('2027 ALG1 (12 months)')
    export_values.append(f"€{results['alg1_2027']:,.2f}")
    
    if has_children:
        export_params.append('2027 Kindergeld (12 months)')
        export_values.append(f"€{results['kindergeld_2027']:,.2f}")
    
    if has_children and has_familiengeld:
        export_params.append(f'2027 Familiengeld ({state_name})')
        export_values.append(f"€{results['familiengeld_2027']:,.2f}")
    
    export_params.extend([
        '',
        '2-Year Total Cash',
        'Financial Runway (months)'
    ])
    export_values.extend([
        '',
        f"€{results['total_2_years']:,.2f}",
        f"{results['runway_months']:.1f}"
    ])
    
    # Generate PDF with all GUI elements
    def create_pdf(name):
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=0.4*inch, bottomMargin=0.4*inch, leftMargin=0.5*inch, rightMargin=0.5*inch)
        
        # Container for PDF elements
        elements = []
        
        # Styles
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=20,
            textColor=colors.HexColor('#1f77b4'),
            spaceAfter=20,
            alignment=TA_CENTER,
            fontName='Helvetica-Bold'
        )
        
        heading_style = ParagraphStyle(
            'CustomHeading',
            parent=styles['Heading2'],
            fontSize=13,
            textColor=colors.HexColor('#1f77b4'),
            spaceAfter=10,
            spaceBefore=15,
            fontName='Helvetica-Bold'
        )
        
        subheading_style = ParagraphStyle(
            'SubHeading',
            parent=styles['Heading3'],
            fontSize=11,
            textColor=colors.HexColor('#555555'),
            spaceAfter=8,
            spaceBefore=10,
            fontName='Helvetica-Bold'
        )
        
        body_style = ParagraphStyle(
            'BodyText',
            parent=styles['Normal'],
            fontSize=9,
            leading=12,
            alignment=TA_JUSTIFY
        )
        
        # ===== PAGE 1: TITLE & INPUT PARAMETERS =====
        # Title
        if name:
            title_text = f"Severance & Exit Financial Analysis<br/>Prepared for: {name}"
        else:
            title_text = "Severance & Exit Financial Analysis"
        
        elements.append(Paragraph(title_text, title_style))
        elements.append(Paragraph(f"Generated: {datetime.now().strftime('%B %d, %Y at %H:%M')}", body_style))
        elements.append(Spacer(1, 0.2*inch))
        
        # Financial Runway Info Box
        runway_info = Paragraph(
            f"<b>Financial Runway:</b> Your financial runway after exit is <b>{results['runway_months']:.1f} months</b>. "
            f"This is calculated from your exit date onwards using €{results['cash_after_exit']:,.0f} (severance + benefits) "
            f"divided by €{monthly_expenses:,.0f}/month expenses. "
            f"During your {months_worked_2026} working months, your salary covers those expenses. "
            f"ALG1 is capped at 12 months total ({results['months_alg1_2026']} months in 2026 + {results['months_alg1_2027']} months in 2027).",
            body_style
        )
        
        runway_table = Table([[runway_info]], colWidths=[7*inch])
        runway_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#d1ecf1')),
            ('BOX', (0, 0), (-1, -1), 2, colors.HexColor('#17a2b8')),
            ('LEFTPADDING', (0, 0), (-1, -1), 10),
            ('RIGHTPADDING', (0, 0), (-1, -1), 10),
            ('TOPPADDING', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
        ]))
        elements.append(runway_table)
        elements.append(Spacer(1, 0.15*inch))
        
        # Input Parameters
        elements.append(Paragraph("📝 Input Parameters", heading_style))
        
        input_data = [
            ['Parameter', 'Value'],
            ['Annual Gross Salary', f"€{annual_salary:,}"],
            ['Months Worked in 2026', f"{months_worked_2026}"],
            ['Severance Package', f"{severance_months} months"],
            ['Tax Class', tax_class],
            ['Location', f"PLZ {plz} ({state_name})"],
            ['Children', f"{num_children} child(ren)" if has_children else 'No'],
            ['Sperrzeit', f"{sperrzeit_months} month(s)"],
        ]
        
        input_table = Table(input_data, colWidths=[3*inch, 4*inch])
        input_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1f77b4')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
            ('TOPPADDING', (0, 1), (-1, -1), 5),
            ('BOTTOMPADDING', (0, 1), (-1, -1), 5),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
        ]))
        elements.append(input_table)
        elements.append(Spacer(1, 0.15*inch))
        
        # Monthly Expenses
        elements.append(Paragraph("💶 Monthly Expenses", heading_style))
        
        expenses_data = [
            ['Category', 'Amount'],
            ['Rent / Mortgage', f"€{rent:,}"],
            ['Groceries', f"€{groceries:,}"],
            ['Car / Transport', f"€{transport:,}"],
            ['Utilities', f"€{utilities:,}"],
            ['Kindergarten', f"€{kindergarten:,}"],
            ['Other', f"€{other_expenses:,}"],
            ['Total Monthly', f"€{monthly_expenses:,}"],
        ]
        
        expenses_table = Table(expenses_data, colWidths=[3*inch, 4*inch])
        expenses_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1f77b4')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
            ('TOPPADDING', (0, 1), (-1, -1), 5),
            ('BOTTOMPADDING', (0, 1), (-1, -1), 5),
            ('BACKGROUND', (0, 1), (-1, -2), colors.beige),
            ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#d3d3d3')),
            ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
        ]))
        elements.append(expenses_table)
        
        # Page break before pie charts
        elements.append(PageBreak())
        
        # ===== PAGE 2: INCOME VS EXPENSES PIE CHARTS =====
        elements.append(Paragraph("📊 Income vs Expenses Analysis", heading_style))
        elements.append(Spacer(1, 0.1*inch))
        
        # Calculate values
        months_after_exit_2026 = 12 - months_worked_2026
        expenses_2026 = monthly_expenses * months_after_exit_2026
        total_income_2026 = results['cash_after_exit_2026']
        surplus_2026 = total_income_2026 - expenses_2026
        expenses_2027 = monthly_expenses * 12
        total_income_2027 = results['cash_after_exit_2027']
        surplus_2027 = total_income_2027 - expenses_2027
        
        # Generate pie charts using matplotlib (much faster than kaleido)
        chart_temp_file = None
        try:
            # Create figure with two subplots side by side
            fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10, 4))
            
            # 2026 Pie Chart Data
            labels_2026 = []
            values_2026 = []
            colors_2026 = ['#27AE60', '#3498DB', '#9B59B6', '#F39C12', '#E74C3C']
            
            if results['net_severance'] > 0:
                labels_2026.append('Severance')
                values_2026.append(results['net_severance'])
            if results['alg1_2026'] > 0:
                labels_2026.append(f'ALG1\n({results["months_alg1_2026"]}mo)')
                values_2026.append(results['alg1_2026'])
            if has_children and results['kindergeld_2026'] > 0:
                labels_2026.append('Kindergeld')
                values_2026.append(results['kindergeld_2026'])
            if has_familiengeld and results['familiengeld_2026'] > 0:
                labels_2026.append('Familiengeld')
                values_2026.append(results['familiengeld_2026'])
            labels_2026.append('Expenses')
            values_2026.append(expenses_2026)
            
            # 2027 Pie Chart Data
            labels_2027 = []
            values_2027 = []
            
            if results['alg1_2027'] > 0:
                labels_2027.append(f'ALG1\n({results["months_alg1_2027"]}mo)')
                values_2027.append(results['alg1_2027'])
            if has_children and results['kindergeld_2027'] > 0:
                labels_2027.append('Kindergeld')
                values_2027.append(results['kindergeld_2027'])
            if has_familiengeld and results['familiengeld_2027'] > 0:
                labels_2027.append('Familiengeld')
                values_2027.append(results['familiengeld_2027'])
            labels_2027.append('Expenses')
            values_2027.append(expenses_2027)
            
            # Create 2026 pie chart
            ax1.pie(values_2026, labels=labels_2026, autopct='%1.1f%%', 
                   colors=colors_2026[:len(values_2026)], startangle=90)
            ax1.set_title('2026 Income vs Expenses', fontsize=12, fontweight='bold')
            
            # Create 2027 pie chart
            ax2.pie(values_2027, labels=labels_2027, autopct='%1.1f%%', 
                   colors=colors_2026[:len(values_2027)], startangle=90)
            ax2.set_title('2027 Income vs Expenses', fontsize=12, fontweight='bold')
            
            # Save to BytesIO instead of temp file to avoid file locking issues
            img_buffer = BytesIO()
            plt.tight_layout()
            plt.savefig(img_buffer, format='png', dpi=150, bbox_inches='tight')
            plt.close()
            img_buffer.seek(0)
            
            # Add chart to PDF from BytesIO
            chart_img = Image(img_buffer, width=7*inch, height=2.8*inch)
            elements.append(chart_img)
            
        except Exception as e:
            # Fallback message if chart generation fails
            error_msg = Paragraph(
                f"<i>Note: Chart generation unavailable. {str(e)}</i>",
                body_style
            )
            elements.append(error_msg)
        
        elements.append(Spacer(1, 0.2*inch))
        
        metrics_data = [
            ['Metric', '2026', '2027'],
            ['Total Income', f"€{total_income_2026:,.0f}", f"€{total_income_2027:,.0f}"],
            ['Total Expenses', f"€{expenses_2026:,.0f}", f"€{expenses_2027:,.0f}"],
            ['Surplus/Deficit', 
             f"€{surplus_2026:,.0f}" if surplus_2026 >= 0 else f"-€{-surplus_2026:,.0f}",
             f"€{surplus_2027:,.0f}" if surplus_2027 >= 0 else f"-€{-surplus_2027:,.0f}"]
        ]
        
        metrics_table = Table(metrics_data, colWidths=[2.5*inch, 2*inch, 2*inch])
        metrics_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1f77b4')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('ALIGN', (1, 0), (-1, -1), 'RIGHT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
            ('TOPPADDING', (0, 1), (-1, -1), 5),
            ('BOTTOMPADDING', (0, 1), (-1, -1), 5),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
        ]))
        elements.append(metrics_table)
        elements.append(Spacer(1, 0.1*inch))
        
        # Page break before recommendations
        elements.append(PageBreak())
        
        # ===== PAGE 3: SEVERANCE RECOMMENDATION =====
        elements.append(Paragraph("💡 Severance Package Recommendation", heading_style))
        elements.append(Spacer(1, 0.1*inch))
        
        # Calculate total and recommendations
        months_after_exit_2026 = 12 - months_worked_2026
        expenses_2026 = monthly_expenses * months_after_exit_2026
        expenses_2027 = monthly_expenses * 12
        total_income_after_exit = results['cash_after_exit']
        total_expenses_projected = expenses_2026 + expenses_2027
        surplus_deficit = total_income_after_exit - total_expenses_projected
        
        monthly_gross = results['monthly_gross']
        net_severance_rate = results['net_severance'] / results['gross_severance'] if results['gross_severance'] > 0 else 0.75
        net_per_severance_month = monthly_gross * net_severance_rate
        
        months_needed_for_breakeven = (total_expenses_projected - total_income_after_exit) / net_per_severance_month
        breakeven_months = severance_months + months_needed_for_breakeven
        
        option_deficit = max(1, int(breakeven_months - 1))
        option_breakeven = max(1, math.ceil(breakeven_months))
        option_surplus = max(1, int(breakeven_months + 2))
        
        if surplus_deficit < 0:
            deficit_amount = -surplus_deficit
            rec_text = (
                f"<b>Warning:</b> You have a deficit of €{deficit_amount:,.0f} to survive through 2027 with your current "
                f"expenditure of €{monthly_expenses:,.0f}/month. To cover your expenses without financial difficulties, "
                f"consider negotiating a higher severance package."
            )
        else:
            surplus_amount = surplus_deficit
            rec_text = (
                f"<b>Good News:</b> You have a surplus of €{surplus_amount:,.0f} for survival in 2026 and 2027 with your "
                f"current {severance_months}-month severance package. However, negotiating additional months can provide "
                f"even more financial security."
            )
        
        elements.append(Paragraph(rec_text, body_style))
        elements.append(Spacer(1, 0.15*inch))
        
        # Recommendation options
        elements.append(Paragraph("Recommended Severance Options:", subheading_style))
        
        rec_options = [
            ['Severance Months', 'Projected Result'],
            [f"{option_deficit} months", ''],
            [f"{option_breakeven} months (Break-even)", ''],
            [f"{option_surplus} months", ''],
        ]
        
        for i, option in enumerate([option_deficit, option_breakeven, option_surplus]):
            gross_option = monthly_gross * option
            net_option = gross_option * net_severance_rate
            projected_surplus = total_income_after_exit - total_expenses_projected + (net_option - results['net_severance'])
            
            if abs(projected_surplus) < net_per_severance_month * 0.1:
                rec_options[i+1][1] = f"Break-even: €{projected_surplus:,.0f}"
            elif projected_surplus >= 0:
                rec_options[i+1][1] = f"Surplus: €{projected_surplus:,.0f}"
            else:
                rec_options[i+1][1] = f"Deficit: €{-projected_surplus:,.0f}"
        
        rec_table = Table(rec_options, colWidths=[2.5*inch, 4.5*inch])
        rec_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1f77b4')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
            ('TOPPADDING', (0, 1), (-1, -1), 5),
            ('BOTTOMPADDING', (0, 1), (-1, -1), 5),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('BACKGROUND', (0, 2), (-1, 2), colors.HexColor('#d1ecf1')),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
        ]))
        elements.append(rec_table)
        elements.append(Spacer(1, 0.15*inch))
        
        key_points = Paragraph(
            f"<b>Key Points:</b><br/>"
            f"• Each additional severance month adds ~€{net_per_severance_month:,.0f} to your runway<br/>"
            f"• Financial Runway: {results['runway_months']:.1f} months from exit date<br/>"
            f"• Total expenses to cover: €{total_expenses_projected:,.0f} ({months_after_exit_2026 + 12} months)<br/>"
            f"• More months = more time to find the right opportunity",
            body_style
        )
        elements.append(key_points)
        
        # Page break before detailed results
        elements.append(PageBreak())
        
        # ===== PAGE 4: DETAILED FINANCIAL BREAKDOWN =====
        elements.append(Paragraph("📋 Detailed Financial Breakdown", heading_style))
        elements.append(Spacer(1, 0.1*inch))
        
        detailed_data = [
            ['Item', 'Amount'],
            ['Severance Calculation', ''],
            ['Monthly Gross Salary', f"€{results['monthly_gross']:,.2f}"],
            ['Monthly Net Salary', f"€{results['monthly_net']:,.2f}"],
            ['Gross Severance', f"€{results['gross_severance']:,.2f}"],
            ['Severance Tax (Fünftelregelung)', f"€{results['sev_tax']:,.2f}"],
            ['Effective Tax Rate', f"{results['sev_tax_rate']*100:.2f}%"],
            ['Net Severance', f"€{results['net_severance']:,.2f}"],
            ['', ''],
            ['2026 Income', ''],
            [f'Salary ({months_worked_2026} months)', f"€{results['salary_2026']:,.2f}"],
            ['Net Severance Payment', f"€{results['net_severance']:,.2f}"],
            [f'ALG1 ({results["months_alg1_2026"]} months)', f"€{results['alg1_2026']:,.2f}"],
        ]
        
        if has_children:
            detailed_data.append(['Kindergeld (12 months)', f"€{results['kindergeld_2026']:,.2f}"])
        if has_familiengeld:
            detailed_data.append([f'Familiengeld ({state_name})', f"€{results['familiengeld_2026']:,.2f}"])
        
        detailed_data.extend([
            ['2026 Total', f"€{results['total_2026']:,.2f}"],
            ['', ''],
            ['2027 Income', ''],
            [f'ALG1 ({results["months_alg1_2027"]} months)', f"€{results['alg1_2027']:,.2f}"],
        ])
        
        if has_children:
            detailed_data.append(['Kindergeld (12 months)', f"€{results['kindergeld_2027']:,.2f}"])
        if has_familiengeld:
            detailed_data.append([f'Familiengeld ({state_name})', f"€{results['familiengeld_2027']:,.2f}"])
        
        detailed_data.extend([
            ['2027 Total', f"€{results['total_2027']:,.2f}"],
            ['', ''],
            ['Summary', ''],
            ['2-Year Total Income', f"€{results['total_2_years']:,.2f}"],
            ['Cash After Exit', f"€{results['cash_after_exit']:,.2f}"],
            ['Financial Runway', f"{results['runway_months']:.1f} months"],
        ])
        
        detailed_table = Table(detailed_data, colWidths=[3.5*inch, 3.5*inch])
        detailed_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('LINEBELOW', (0, 0), (-1, 0), 1, colors.black),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),  # Header row
            ('FONTNAME', (0, 1), (0, 1), 'Helvetica-Bold'),  # Severance Calculation
            ('FONTNAME', (0, 9), (0, 9), 'Helvetica-Bold'),  # 2026 Income (row varies based on children)
            ('GRID', (0, 0), (-1, -1), 0.25, colors.grey),
        ]))
        elements.append(detailed_table)
        
        # Disclaimer
        elements.append(Spacer(1, 0.3*inch))
        disclaimer_style = ParagraphStyle(
            'Disclaimer',
            parent=styles['Normal'],
            fontSize=7,
            textColor=colors.grey,
            alignment=TA_JUSTIFY,
            leading=9
        )
        
        disclaimer_text = (
            "<b>Disclaimer:</b> This is a planning tool, not professional financial or tax advice. "
            "Tax calculations are simplified estimates. Actual taxes vary by church tax, solidarity surcharge, "
            "municipal rates, and deductions. Consult a Steuerberater (tax advisor) for precise calculations. "
            "ALG1 eligibility and duration depend on contribution history and age. Employment law varies - "
            "seek legal counsel for severance negotiations."
        )
        elements.append(Paragraph(disclaimer_text, disclaimer_style))
        
        # Developer Credit
        elements.append(Spacer(1, 0.2*inch))
        credit_style = ParagraphStyle(
            'Credit',
            parent=styles['Normal'],
            fontSize=8,
            textColor=colors.HexColor('#666666'),
            alignment=TA_CENTER,
            leading=10
        )
        credit_text = (
            "<b>Developed by:</b><br/>"
            "Vinod Kumar Neelakantam<br/>"
            "https://www.linkedin.com/in/vinodneelakantam/"
        )
        elements.append(Paragraph(credit_text, credit_style))
        
        # Page break before FAQ
        elements.append(PageBreak())
        
        # ===== PAGE 5+: FAQ SECTION =====
        elements.append(Paragraph("❓ Frequently Asked Questions (FAQ)", heading_style))
        elements.append(Spacer(1, 0.1*inch))
        
        # FAQ items
        faq_items = [
            {
                'question': '1. What is Arbeitslosengeld I (ALG1)?',
                'answer': 'Unemployment benefit I (ALG1) is a social insurance benefit for people who have lost their job in Germany. '
                         'It is paid by the German Federal Employment Agency (Bundesagentur für Arbeit). To qualify, you must have worked '
                         'and paid social insurance contributions for at least 12 months in the last 30 months (qualifying period). '
                         'The benefit amount is 60% of your previous net salary (or 67% if you have dependent children). '
                         'The maximum duration depends on your age and contribution history, but is typically 12 months for most people. '
                         'Official resource: https://www.arbeitsagentur.de/en/unemployment-benefiti'
            },
            {
                'question': '2. Where do I apply for Arbeitslosengeld (ALG1)?',
                'answer': 'You must register as unemployed at your local Agentur für Arbeit (Employment Agency). You can do this: '
                         '• Online: https://www.arbeitsagentur.de/eservices • In person at your local office • By phone: 0800 4 5555 00 (free). '
                         'You must register at least 3 months before your contract ends (or within 3 days of learning about termination). '
                         'Late registration can result in benefit reductions. Bring your ID, termination letter (Kündigungsschreiben), '
                         'social security card, and employment contract.'
            },
            {
                'question': '3. What is Sperrzeit (blocking period)?',
                'answer': 'Sperrzeit is a waiting period during which you cannot receive ALG1. This typically occurs if you: '
                         '• Resign voluntarily (Eigenkündigung) without "important reason" • Sign a termination agreement (Aufhebungsvertrag) '
                         'without negotiation pressure • Are dismissed for misconduct (Verhaltensbedingte Kündigung). '
                         'Standard duration: 12 weeks (3 months). During Sperrzeit, you receive no benefits but the clock still ticks on your '
                         'total ALG1 entitlement. Important: If you negotiate a severance package as part of termination, consult with '
                         'the Agentur für Arbeit beforehand to avoid Sperrzeit. Documentation of economic necessity (Betriebsbedingte Kündigung) '
                         'can often prevent blocking periods.'
            },
            {
                'question': '4. How is severance taxed in Germany?',
                'answer': 'Severance pay (Abfindung) is subject to income tax but NOT social insurance contributions (no pension, health, '
                         'or unemployment insurance). The tax is calculated using the "Fünftelregelung" (one-fifth rule), a favorable method: '
                         '1. Calculate tax on your annual salary without severance 2. Calculate tax on annual salary + 1/5 of severance '
                         '3. The difference is multiplied by 5 to get total severance tax. This method reduces the tax burden by avoiding '
                         'full progression into higher tax brackets. The effective tax rate on severance is typically 25-45% depending on your '
                         'income level. Church tax (8-9%) and solidarity surcharge (5.5% on income tax) also apply. Important: Severance '
                         'received in January counts toward the previous year for tax purposes, which can optimize your liability.'
            },
            {
                'question': '5. What is Kindergeld and who qualifies?',
                'answer': 'Kindergeld (Child Benefit) is a monthly tax-free payment from the German government to support families with children. '
                         'Eligibility: • You live in Germany and pay taxes • Child is under 18 (or under 25 if in education/training). '
                         'Monthly amounts (2024): • €250 per child (all children). Application: Submit Kindergeldantrag to your local Familienkasse. '
                         'More info: https://www.arbeitsagentur.de/familie-und-kinder/kindergeld-kinderzuschlag-kindergeld'
            },
            {
                'question': '6. What is Familiengeld and who qualifies?',
                'answer': 'Familiengeld is a state-level (Bavaria & Saxony only) benefit for families with young children. '
                         'Bavaria (Bayerisches Familiengeld): • €250/month for 2nd child • €300/month for 3rd+ child • Paid from child\'s '
                         '13th-36th month of life • Income-independent (no income limit). Saxony (Sächsisches Familiengeld): • €100/month for 2nd+ '
                         'child • Paid from birth to age 3. Application: Submit to your local Familienkasse or state family office. '
                         'Bavaria info: https://www.zbfs.bayern.de/familie/familiengeld/ Saxony info: https://www.familie.sachsen.de/'
            },
            {
                'question': '7. How long can I receive ALG1?',
                'answer': 'ALG1 duration depends on your age and months of contributions: • Under 50 years: Max 12 months • 50-54 years: '
                         'Up to 15 months • 55-57 years: Up to 18 months • 58+ years: Up to 24 months. You must have paid contributions for '
                         'at least half the maximum duration (e.g., 24 months of work for 12 months of ALG1). If you have a Sperrzeit (blocking period), '
                         'it reduces your total entitlement duration. Important: ALG1 cannot extend beyond finding new employment.'
            },
            {
                'question': '8. Can I negotiate my severance package?',
                'answer': 'Yes! Severance is negotiable in most cases. There is no legal entitlement to severance in Germany unless: '
                         '• Specified in your employment contract • Part of a social plan (Sozialplan) during restructuring • Agreed in a '
                         'termination agreement (Aufhebungsvertrag). Typical severance: 0.5 months of gross salary per year of service. '
                         'Higher amounts (1-2 months per year) are possible for senior roles or long tenure. Negotiation tips: • Emphasize your '
                         'contributions and tenure • Request severance in exchange for waiving claims (Kündigungsschutzklage) • Consult an '
                         'employment lawyer (Fachanwalt für Arbeitsrecht) • Consider tax optimization (timing, splitting payments). '
                         'Legal advice: https://www.fachanwaltssuche.de/'
            },
            {
                'question': '9. What happens if I find a job during ALG1?',
                'answer': 'When you find new employment: • Your ALG1 stops immediately when you start working • Report the job to Agentur für '
                         'Arbeit within 3 days • Any unused ALG1 entitlement expires (it does not carry forward). Part-time work while receiving '
                         'ALG1: • You can work up to 15 hours/week and still receive reduced ALG1 • Income above €165/month reduces your benefit '
                         'proportionally. Self-employment: Notify the agency - special rules apply for Existenzgründung (startup) support.'
            },
            {
                'question': '10. What are my obligations while receiving ALG1?',
                'answer': 'To continue receiving ALG1, you must: • Actively search for work (apply to jobs regularly) • Attend all appointments '
                         'at Agentur für Arbeit • Accept suitable job offers (Zumutbare Arbeit) • Participate in job training programs if required '
                         '• Inform the agency of any changes (address, income, health status) within 3 days. Violations can result in benefit '
                         'reductions or sanctions. "Suitable work" generally means jobs within your qualifications, but after months of unemployment, '
                         'you may be required to accept positions below your previous level. You can take vacations, but must notify the agency '
                         'in advance (you remain reachable for job offers).'
            },
            {
                'question': '11. Important Resources & Links',
                'answer': ('• Bundesagentur für Arbeit (Federal Employment Agency):<br/>'
                         '&nbsp;&nbsp;https://www.arbeitsagentur.de/en<br/><br/>'
                         '• ALG1 Calculator:<br/>'
                         '&nbsp;&nbsp;https://www.pub.arbeitsagentur.de/selbst.html<br/><br/>'
                         '• Kindergeld Information:<br/>'
                         '&nbsp;&nbsp;https://www.arbeitsagentur.de/familie-und-kinder/kindergeld-kinderzuschlag-kindergeld<br/><br/>'
                         '• Familiengeld Bavaria:<br/>'
                         '&nbsp;&nbsp;https://www.zbfs.bayern.de/familie/familiengeld/<br/><br/>'
                         '• Find Employment Lawyer:<br/>'
                         '&nbsp;&nbsp;https://www.fachanwaltssuche.de/<br/><br/>'
                         '• Find Tax Advisor:<br/>'
                         '&nbsp;&nbsp;https://www.steuberater.de<br/><br/>'
                         '• Job Portal:<br/>'
                         '&nbsp;&nbsp;https://www.arbeitsagentur.de/jobsuche/<br/><br/>'
                         '• Tax Classes Explained:<br/>'
                         '&nbsp;&nbsp;https://www.bmf-steuerrechner.de/')
            },
        ]
        
        for faq in faq_items:
            elements.append(Paragraph(f"<b>{faq['question']}</b>", subheading_style))
            elements.append(Paragraph(faq['answer'], body_style))
            elements.append(Spacer(1, 0.1*inch))
        
        # Build PDF
        doc.build(elements)
        buffer.seek(0)
        return buffer
    
    # Download button
    with col_btn:
        st.write("")  # Spacing
        st.write("")  # Spacing
        if st.button("📄 Generate PDF", type="primary"):
            if not user_name:
                st.warning("💡 Add your name for a personalized PDF report!")
            
            with st.spinner("🔄 Generating PDF report..."):
                pdf_buffer = create_pdf(user_name)
            
            # Create filename
            if user_name:
                safe_name = "".join(c for c in user_name if c.isalnum() or c in (' ', '-', '_')).strip()
                filename = f"Severance_Analysis_{safe_name.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d')}.pdf"
            else:
                filename = f"Severance_Analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
            
            st.success("✅ PDF generated successfully!")
            st.download_button(
                label="📥 Download PDF Report",
                data=pdf_buffer,
                file_name=filename,
                mime="application/pdf"
            )

if __name__ == "__main__":
    main()
