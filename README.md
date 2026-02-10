# 💼 Severance & Exit Financial Calculator - Web Application

A comprehensive web-based financial planning tool for employment exit scenarios in Germany. This interactive application helps you understand your financial position when negotiating severance packages and planning for unemployment.

## 📋 Purpose

This calculator is designed for employees in Germany facing potential job termination or considering voluntary exit packages. It helps you:

- **Understand your financial position** after severance and during unemployment
- **Calculate net severance** after taxes using the German Fünftelregelung (five-year tax rule)
- **Project unemployment benefits** (ALG1) based on your situation
- **Plan your financial runway** to see how long your money will last
- **Compare scenarios** to make informed decisions about severance negotiations
- **Generate professional PDF reports** for your records or to share with advisors

Whether you're negotiating a severance package, planning for unemployment, or evaluating your options, this tool provides clear visibility into your financial future.

## 🌟 Features

- **Interactive Calculator**: Real-time calculations as you adjust parameters
- **Fünftelregelung Implementation**: Accurate German 5-year severance tax rule
- **Postal Code Integration**: Automatic state detection for Familiengeld eligibility (Bavaria)
- **Visual Analytics**: Beautiful pie charts showing income vs expenses breakdown
- **ALG1 Calculations**: Unemployment benefit projections with proper month-by-month tracking
- **Kindergeld & Familiengeld**: Automatic calculation of child benefits
- **Financial Runway**: See exactly how long your money will last
- **Comprehensive PDF Reports**: Download detailed analysis with charts, tables, and recommendations
- **Smart Recommendations**: Get personalized advice based on your financial situation
- **Collapsible Sections**: Clean, organized UI with expandable detailed breakdowns
- **Complete FAQ Section**: 11 detailed questions covering all aspects of German unemployment

## 🚀 Quick Start

### Local Deployment

1. **Install Python** (3.12 or higher recommended)

2. **Clone or download** this repository

3. **Create a virtual environment** (recommended):
   ```bash
   python -m venv .venv
   .venv\Scripts\activate  # Windows
   # or
   source .venv/bin/activate  # Mac/Linux
   ```

4. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

5. **Run the application**:
   ```bash
   streamlit run app.py
   ```

6. **Open your browser** to `http://localhost:8502`

## 🌐 Cloud Deployment Options

### Option 1: Streamlit Community Cloud (FREE & Easiest)

1. **Create a GitHub account** if you don't have one
2. **Create a new repository** and upload these files:
   - `app.py`
   - `requirements.txt`
   - `README.md`

3. **Go to** [share.streamlit.io](https://share.streamlit.io)
4. **Sign in** with GitHub
5. **Click** "New app"
6. **Select** your repository, branch (main), and file (`app.py`)
7. **Click** "Deploy"

Your app will be live at: `https://[your-app-name].streamlit.app`

**Pros**: 
- 100% free
- Zero configuration
- Automatic updates when you push to GitHub
- HTTPS included

### Option 2: Heroku

1. **Create** a `Procfile`:
   ```
   web: sh setup.sh && streamlit run app.py
   ```

2. **Create** `setup.sh`:
   ```bash
   mkdir -p ~/.streamlit/
   echo "\
   [server]\n\
   headless = true\n\
   port = $PORT\n\
   enableCORS = false\n\
   \n\
   " > ~/.streamlit/config.toml
   ```

3. **Deploy to Heroku**:
   ```bash
   heroku create your-app-name
   git push heroku main
   ```

### Option 3: Azure App Service

1. **Create** an Azure App Service (Python runtime)
2. **Configure** deployment from GitHub or local Git
3. **Set** startup command: `python -m streamlit run app.py --server.port 8000`
4. **Deploy** your code

### Option 4: AWS (EC2 or Elastic Beanstalk)

1. **Launch** an EC2 instance or create Elastic Beanstalk app
2. **Install** Python and dependencies
3. **Run** Streamlit with:
   ```bash
   streamlit run app.py --server.port 80 --server.address 0.0.0.0
   ```

## 📊 How to Use

### Step 1: Enter Your Employment Details

**Exit Date & Working Months**:
- Select your **exit date** (when you leave the company)
- Specify **months worked in 2026** (this affects your salary income)
- Enter your **annual gross salary**

**Tax & Family Information**:
- Choose your **tax class** (Class 1 for single, Class 3 for married)
- Enter your **postal code (PLZ)** - automatically detects Bavaria for Familiengeld eligibility
- Specify **number of children** - affects ALG1 rate (67% vs 60%) and Kindergeld

### Step 2: Severance Package Details

- **Severance package** in months of salary (0-36 months)
- The calculator automatically applies the **Fünftelregelung** tax benefit
- See your net severance after taxes instantly

### Step 3: Monthly Expenses Breakdown

Enter your actual monthly costs:
- Rent/Mortgage
- Groceries
- Car/Transport
- Utilities
- Kindergarten
- Other expenses

The calculator shows your **total monthly burn rate** and uses this for runway calculations.

### Step 4: Review Your Financial Analysis

**Key Metrics Displayed**:
- 💰 **Net Severance After Tax**: What you actually receive
- 📅 **Financial Runway**: How many months your money lasts (shown prominently in an info box)
- 💶 **Monthly ALG1**: Your unemployment benefit amount
- 📊 **2026 Total Income**: Complete income for remaining months in 2026
- 📊 **2027 Total Income**: Projected income for 2027
- 💰 **2-Year Total Cash**: Your complete financial cushion

**Visual Analysis**:
- **Pie Charts**: See 2026 and 2027 income vs expenses breakdown
- **Income Tables**: Month-by-month tracking of ALG1, Kindergeld, Familiengeld
- **Detailed Financial Breakdown**: Tabs showing 2026, 2027, and summary

### Step 5: Get Personalized Recommendations

The calculator provides **smart recommendations** based on your situation:
- **Deficit Scenario**: If expenses exceed income, get specific advice
- **Break-Even Scenario**: If you're barely covering costs, see optimization tips
- **Surplus Scenario**: If you have excess income, get savings strategies

### Step 6: Generate Professional PDF Report

1. Enter your **name** in the text field (optional, for personalization)
2. Click **"📄 Generate PDF"** button
3. Download your comprehensive report

**PDF Report Includes**:
- ✅ Personalized title with your name
- ✅ Financial runway explanation
- ✅ All input parameters
- ✅ Monthly expenses breakdown
- ✅ Pie charts (2026 & 2027 income vs expenses)
- ✅ Severance recommendations for your scenario
- ✅ Complete detailed financial breakdown
- ✅ Full FAQ section (11 questions with detailed answers)
- ✅ Important resources with clickable links
- ✅ Professional disclaimers

### Understanding the Results

**Collapsible Sections** (click to expand/collapse):
- 📊 **Financial Analysis & Recommendations**: Always expanded by default
- 💡 **Severance Package Recommendation**: Personalized advice for your situation
- 📋 **Detailed Financial Breakdown**: Year-by-year income and expense tables
- ❓ **Important Information & FAQ**: Complete guide to German unemployment system

## 🇩🇪 German Tax & Benefits Explained

### Fünftelregelung (Five-Year Rule)
German tax benefit that reduces tax on severance by spreading calculation over 5 years:
```
Tax = 5 × (Tax[Salary + Severance/5] - Tax[Salary])
```
This results in lower effective tax rate (typically 25-35% vs 40%+).

### Tax Classes
- **Tax Class 3**: Married/partnership - Net ≈ 67% of gross salary
- **Tax Class 1**: Single/divorced - Net ≈ 60% of gross salary
- These rates are used for both salary and ALG1 calculations

### ALG1 (Arbeitslosengeld I)
- **Without children**: 60% of net salary
- **With children**: 67% of net salary
- **Duration**: 12 months maximum (calculated from exit date, split across 2026/2027)
- Month-by-month tracking ensures accurate projections

### Kindergeld (Child Benefit)
- **€250/month per child** (2026 rate)
- Available for all children (no income limits in most cases)
- Automatically calculated based on number of children

### Familiengeld (Family Money - Bavaria Only)
- **€250-€300/month per child** for second and third year of life
- **Only available in Bavaria** (detected via postal code)
- Requires no employment or only mini-job (≤32.5 hours/week)
- Stacks with Kindergeld

### Financial Runway Calculation
```
Runway = (Total Cash After Exit) / Monthly Expenses
Total Cash = Net Severance + ALG1 (2026) + ALG1 (2027) + Kindergeld + Familiengeld
```
Note: During working months in 2026, your salary covers expenses - only post-exit period counts.

## 📁 Project Structure

```
jeevitham/
├── app.py              # Main Streamlit application (1950+ lines)
├── requirements.txt    # Python dependencies
├── README.md          # This file
└── .venv/             # Virtual environment (not committed)
```

## 🔧 Technical Details

### Dependencies
- **streamlit==1.31.0**: Web framework for interactive UI
- **pandas==2.2.0**: Data manipulation and tables
- **plotly==5.18.0**: Interactive charts in the GUI
- **matplotlib==3.10.8**: Pie chart generation for PDF reports
- **reportlab==4.0.7**: PDF generation engine
- **openpyxl==3.1.2**: Excel file support (if needed)

### Key Technologies
- **Python 3.12.6**: Core language
- **ReportLab**: Professional PDF generation with tables, charts, and styling
- **Matplotlib**: Fast pie chart rendering (replaced kaleido for performance)
- **Streamlit**: Modern web framework with real-time updates

### PDF Generation
- Uses **BytesIO** for in-memory chart generation (no temporary files)
- Professional formatting with custom fonts, colors, and spacing
- Multi-page reports with automatic page breaks
- Charts embedded directly from matplotlib (2-3 second generation time)

### Performance
- Instant calculations (client-side rendering)
- PDF generation: 2-3 seconds (includes pie chart creation)
- No database required - all calculations in real-time
- Responsive design works on mobile and desktop

### Browser Compatibility
- Chrome, Firefox, Safari, Edge (latest versions)
- Mobile responsive design
- Works offline after initial load

## ⚠️ Important Disclaimers

- This is a **PLANNING TOOL**, not professional tax or financial advice
- Tax calculations are **simplified estimates** based on average rates
- Actual taxes vary by:
  - Church tax (Kirchensteuer)
  - Solidarity surcharge (Solidaritätszuschlag)
  - Municipal rates
  - Individual deductions
- **Consult a Steuerberater** (tax advisor) for precise calculations
- ALG1 eligibility and duration depend on contribution history and age
- **Seek legal counsel** for severance negotiations
- Familiengeld rules and amounts may change - verify with ZBFS Bayern
- Always verify benefits eligibility with Bundesagentur für Arbeit

## 📞 Resources & Support

### Official German Government Links
- **Bundesagentur für Arbeit**: https://www.arbeitsagentur.de/en
- **ALG1 Calculator**: https://www.pub.arbeitsagentur.de/selbst.html
- **Kindergeld Information**: https://www.arbeitsagentur.de/familie-und-kinder/kindergeld
- **Familiengeld Bavaria**: https://www.zbfs.bayern.de/familie/familiengeld/

### Professional Help
- **Find Employment Lawyer**: https://www.fachanwaltssuche.de/
- **Find Tax Advisor**: https://www.steuerberater.de

### Job Search
- **Job Portal**: https://www.arbeitsagentur.de/jobsuche/

## 👨‍💻 Developer

**Developed by:** Vinod Kumar Neelakantam  
**LinkedIn:** https://www.linkedin.com/in/vinodneelakantam/

## 📝 Version History

- **v2.1** (Feb 2026): 
  - Added comprehensive PDF export with pie charts
  - Implemented Familiengeld for Bavaria
  - Added postal code integration
  - Smart recommendations system
  - Complete FAQ section
  - Collapsible UI sections
  
- **v2.0** (Feb 2026): Web application with Streamlit

## 📄 License

Free to use for personal financial planning.

---

**Built with ❤️ for better financial planning during career transitions**
