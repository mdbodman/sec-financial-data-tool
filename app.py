"""
SEC Financial Statement Data Extraction Tool
Retrieves and parses financial data from SEC Financial Statement Data Sets
"""

import streamlit as st
import pandas as pd
import requests
from datetime import datetime
from io import BytesIO
import time
from typing import List, Dict, Optional, Tuple
import zipfile
from urllib.parse import urljoin

# Page configuration
st.set_page_config(
    page_title="SEC Financial Data Extractor",
    page_icon="📊",
    layout="wide"
)

# Constants
SEC_EDGAR_BASE = "https://www.sec.gov"
SEC_API_BASE = "https://data.sec.gov"
SEC_DATASETS_BASE = "https://www.sec.gov/files/dera/data/financial-statement-data-sets/"
REQUEST_HEADERS = {
    'User-Agent': 'Financial Data Tool research@example.com',
    'Accept-Encoding': 'gzip, deflate',
}

# Initialize session state
if 'data_retrieved' not in st.session_state:
    st.session_state.data_retrieved = False
if 'financial_data' not in st.session_state:
    st.session_state.financial_data = None
if 'ticker' not in st.session_state:
    st.session_state.ticker = ""

@st.cache_data(ttl=3600)
def get_cik_from_ticker(ticker: str) -> Optional[str]:
    """Convert ticker symbol to CIK number"""
    try:
        ticker = ticker.strip().upper()
        # Use the correct SEC endpoint
        url = "https://www.sec.gov/files/company_tickers.json"
        headers = {
            'User-Agent': 'Financial Data Tool research@example.com',
            'Accept-Encoding': 'gzip, deflate',
        }
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        
        companies = response.json()
        
        for company in companies.values():
            if company['ticker'] == ticker:
                cik = str(company['cik_str']).zfill(10)
                return cik
        
        return None
    except Exception as e:
        st.error(f"Error retrieving CIK: {str(e)}")
        return None

def get_available_quarters() -> List[str]:
    """Get list of available quarterly dataset periods"""
    # SEC publishes datasets with a delay of 6-10 weeks after quarter end
    # Generate quarters from 2020 onwards, but exclude very recent quarters
    quarters = []
    current_year = datetime.now().year
    current_month = datetime.now().month
    
    # Calculate which quarter we're in
    current_quarter = (current_month - 1) // 3 + 1
    
    # SEC typically hasn't published the current quarter yet, and sometimes
    # the previous quarter is still being finalized. Go back 2 quarters to be safe.
    if current_quarter <= 2:
        last_available_year = current_year - 1
        last_available_quarter = 4 + (current_quarter - 2)
    else:
        last_available_year = current_year
        last_available_quarter = current_quarter - 2
    
    for year in range(2020, current_year + 1):
        for q in range(1, 5):
            # Don't include quarters that likely aren't published yet
            if year > last_available_year:
                break
            if year == last_available_year and q > last_available_quarter:
                break
            quarters.append(f"{year}q{q}")
    
    return sorted(quarters, reverse=True)

@st.cache_data(ttl=3600)
def download_dataset(quarter: str) -> Tuple[Optional[pd.DataFrame], Optional[pd.DataFrame], Optional[pd.DataFrame]]:
    """Download and parse SEC Financial Statement Data Set for a given quarter"""
    try:
        # Construct URL for the quarterly dataset
        zip_filename = f"{quarter}.zip"
        url = urljoin(SEC_DATASETS_BASE, zip_filename)
        
        # Download the ZIP file
        response = requests.get(url, headers=REQUEST_HEADERS, timeout=120)
        response.raise_for_status()
        
        # Extract files from ZIP
        with zipfile.ZipFile(BytesIO(response.content)) as z:
            # Read the three main files
            # SUB - submission data
            # NUM - numeric data
            # TAG - tag definitions
            
            with z.open('sub.txt') as f:
                sub_df = pd.read_csv(f, sep='\t', dtype=str, low_memory=False)
            
            with z.open('num.txt') as f:
                num_df = pd.read_csv(f, sep='\t', dtype=str, low_memory=False)
            
            with z.open('tag.txt') as f:
                tag_df = pd.read_csv(f, sep='\t', dtype=str, low_memory=False)
        
        return sub_df, num_df, tag_df
    
    except Exception as e:
        st.warning(f"Could not download dataset for {quarter}: {str(e)}")
        return None, None, None

def get_company_data(cik: str, num_df: pd.DataFrame, sub_df: pd.DataFrame, tag_df: pd.DataFrame, filing_type: str = '10-K') -> List[Dict]:
    """Extract company filings from dataset"""
    try:
        # Filter submissions for this CIK and filing type
        company_subs = sub_df[
            (sub_df['cik'] == cik) & 
            (sub_df['form'] == filing_type)
        ].copy()
        
        if company_subs.empty:
            return []
        
        # Get unique adsh (accession numbers)
        filings = []
        for _, row in company_subs.iterrows():
            filings.append({
                'adsh': row['adsh'],
                'cik': row['cik'],
                'name': row['name'],
                'form': row['form'],
                'filed': row['filed'],
                'period': row['period'],
                'fy': row['fy'],
                'fp': row['fp']
            })
        
        return filings
    
    except Exception as e:
        st.error(f"Error extracting company data: {str(e)}")
        return []

def extract_financial_statements(adsh: str, num_df: pd.DataFrame, tag_df: pd.DataFrame) -> Dict[str, pd.DataFrame]:
    """Extract financial statement data for a specific filing"""
    try:
        # Filter numeric data for this filing
        filing_data = num_df[num_df['adsh'] == adsh].copy()
        
        if filing_data.empty:
            return {}
        
        # Merge with tag descriptions
        filing_data = filing_data.merge(
            tag_df[['tag', 'tlabel', 'version']], 
            on='tag', 
            how='left'
        )
        
        # Filter for US GAAP tags only
        filing_data = filing_data[filing_data['version'].str.contains('us-gaap', na=False)]
        
        # Define key line items for each statement
        balance_sheet_tags = [
            'Assets', 'AssetsCurrent', 'AssetsNoncurrent',
            'Liabilities', 'LiabilitiesCurrent', 'LiabilitiesNoncurrent',
            'StockholdersEquity', 'LiabilitiesAndStockholdersEquity',
            'CashAndCashEquivalentsAtCarryingValue',
            'AccountsReceivableNetCurrent',
            'InventoryNet',
            'PropertyPlantAndEquipmentNet',
            'AccountsPayableCurrent',
            'LongTermDebtNoncurrent'
        ]
        
        income_statement_tags = [
            'Revenues', 'RevenueFromContractWithCustomerExcludingAssessedTax',
            'CostOfRevenue', 'CostOfGoodsAndServicesSold',
            'GrossProfit',
            'OperatingExpenses', 'OperatingIncomeLoss',
            'IncomeLossFromContinuingOperationsBeforeIncomeTaxesExtraordinaryItemsNoncontrollingInterest',
            'IncomeTaxExpenseBenefit',
            'NetIncomeLoss', 'ProfitLoss',
            'EarningsPerShareBasic', 'EarningsPerShareDiluted'
        ]
        
        cash_flow_tags = [
            'NetCashProvidedByUsedInOperatingActivities',
            'NetCashProvidedByUsedInInvestingActivities',
            'NetCashProvidedByUsedInFinancingActivities',
            'CashCashEquivalentsRestrictedCashAndRestrictedCashEquivalentsPeriodIncreaseDecreaseIncludingExchangeRateEffect',
            'PaymentsToAcquirePropertyPlantAndEquipment',
            'Depreciation', 'DepreciationDepletionAndAmortization'
        ]
        
        # Extract each statement type
        statements = {}
        
        # Balance Sheet
        bs_data = filing_data[filing_data['tag'].isin(balance_sheet_tags)].copy()
        if not bs_data.empty:
            # Get most recent instant values
            bs_data = bs_data[bs_data['ddate'].notna()]
            bs_data = bs_data.sort_values('ddate', ascending=False)
            bs_data = bs_data.drop_duplicates(subset=['tag'], keep='first')
            statements['balance_sheet'] = bs_data[['tag', 'tlabel', 'value', 'ddate', 'uom']].copy()
            statements['balance_sheet'].columns = ['Tag', 'Metric', 'Value', 'Date', 'Unit']
        
        # Income Statement
        is_data = filing_data[filing_data['tag'].isin(income_statement_tags)].copy()
        if not is_data.empty:
            # Get duration values (typically qtrs=1 for quarterly, qtrs=4 for annual)
            is_data = is_data[is_data['qtrs'].notna()]
            is_data = is_data.sort_values(['tag', 'ddate'], ascending=[True, False])
            is_data = is_data.drop_duplicates(subset=['tag'], keep='first')
            statements['income_statement'] = is_data[['tag', 'tlabel', 'value', 'ddate', 'uom', 'qtrs']].copy()
            statements['income_statement'].columns = ['Tag', 'Metric', 'Value', 'Date', 'Unit', 'Quarters']
        
        # Cash Flow Statement
        cf_data = filing_data[filing_data['tag'].isin(cash_flow_tags)].copy()
        if not cf_data.empty:
            # Get duration values
            cf_data = cf_data[cf_data['qtrs'].notna()]
            cf_data = cf_data.sort_values(['tag', 'ddate'], ascending=[True, False])
            cf_data = cf_data.drop_duplicates(subset=['tag'], keep='first')
            statements['cash_flow'] = cf_data[['tag', 'tlabel', 'value', 'ddate', 'uom', 'qtrs']].copy()
            statements['cash_flow'].columns = ['Tag', 'Metric', 'Value', 'Date', 'Unit', 'Quarters']
        
        return statements
    
    except Exception as e:
        st.warning(f"Error extracting statements: {str(e)}")
        return {}

def aggregate_multi_period_data(all_filings_data: List[Tuple[str, Dict]]) -> Dict[str, pd.DataFrame]:
    """Combine data from multiple periods"""
    balance_sheets = []
    income_statements = []
    cash_flows = []
    
    for period, statements in all_filings_data:
        if 'balance_sheet' in statements and not statements['balance_sheet'].empty:
            df = statements['balance_sheet'].copy()
            df['Period'] = period
            balance_sheets.append(df)
        
        if 'income_statement' in statements and not statements['income_statement'].empty:
            df = statements['income_statement'].copy()
            df['Period'] = period
            income_statements.append(df)
        
        if 'cash_flow' in statements and not statements['cash_flow'].empty:
            df = statements['cash_flow'].copy()
            df['Period'] = period
            cash_flows.append(df)
    
    combined = {}
    
    if balance_sheets:
        combined['balance_sheet'] = pd.concat(balance_sheets, ignore_index=True)
        # Convert value to numeric
        combined['balance_sheet']['Value'] = pd.to_numeric(combined['balance_sheet']['Value'], errors='coerce')
    else:
        combined['balance_sheet'] = pd.DataFrame()
    
    if income_statements:
        combined['income_statement'] = pd.concat(income_statements, ignore_index=True)
        combined['income_statement']['Value'] = pd.to_numeric(combined['income_statement']['Value'], errors='coerce')
    else:
        combined['income_statement'] = pd.DataFrame()
    
    if cash_flows:
        combined['cash_flow'] = pd.concat(cash_flows, ignore_index=True)
        combined['cash_flow']['Value'] = pd.to_numeric(combined['cash_flow']['Value'], errors='coerce')
    else:
        combined['cash_flow'] = pd.DataFrame()
    
    return combined

def create_excel_download(data: Dict[str, pd.DataFrame], ticker: str) -> BytesIO:
    """Create Excel file with multiple sheets in memory"""
    buffer = BytesIO()
    
    with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
        if not data['balance_sheet'].empty:
            data['balance_sheet'].to_excel(writer, sheet_name='Balance Sheet', index=False)
        
        if not data['income_statement'].empty:
            data['income_statement'].to_excel(writer, sheet_name='Income Statement', index=False)
        
        if not data['cash_flow'].empty:
            data['cash_flow'].to_excel(writer, sheet_name='Cash Flow', index=False)
    
    buffer.seek(0)
    return buffer

def create_csv_download(df: pd.DataFrame) -> BytesIO:
    """Create CSV file in memory"""
    buffer = BytesIO()
    df.to_csv(buffer, index=False)
    buffer.seek(0)
    return buffer

def main():
    st.title("📊 SEC Financial Statement Data Extractor")
    st.markdown("Extract financial data from SEC Financial Statement Data Sets")
    
    # Sidebar for inputs
    with st.sidebar:
        st.header("Input Parameters")
        
        ticker = st.text_input(
            "Ticker Symbol",
            value=st.session_state.ticker,
            placeholder="e.g., AAPL",
            help="Enter the stock ticker symbol"
        ).upper()
        
        data_frequency = st.radio(
            "Data Frequency",
            options=["Annual", "Quarterly"],
            help="Select annual (10-K) or quarterly (10-Q) filings"
        )
        
        years = st.select_slider(
            "Historical Period",
            options=[1, 2, 3, 4, 5],
            value=2,
            help="Number of years of historical data to retrieve"
        )
        
        st.markdown("---")
        
        output_format = st.multiselect(
            "Output Format",
            options=["Excel", "CSV"],
            default=["Excel"],
            help="Select one or both output formats"
        )
        
        st.markdown("---")
        
        col1, col2 = st.columns(2)
        
        with col1:
            retrieve_button = st.button(
                "🔍 Retrieve Data",
                type="primary",
                use_container_width=True
            )
        
        with col2:
            clear_button = st.button(
                "🗑️ Clear",
                use_container_width=True
            )
        
        if clear_button:
            st.session_state.data_retrieved = False
            st.session_state.financial_data = None
            st.session_state.ticker = ""
            st.rerun()
    
    # Main content area
    if retrieve_button:
        if not ticker:
            st.error("Please enter a ticker symbol")
            return
        
        if not output_format:
            st.error("Please select at least one output format")
            return
        
        st.session_state.ticker = ticker
        
        # Progress tracking
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        try:
            # Step 1: Get CIK
            status_text.text("Step 1/5: Looking up company CIK...")
            progress_bar.progress(0.1)
            
            cik = get_cik_from_ticker(ticker)
            if not cik:
                st.error(f"Could not find CIK for ticker: {ticker}")
                return
            
            # Remove leading zeros for display
            cik_display = str(int(cik))
            st.success(f"Found company (CIK: {cik_display})")
            
            # Step 2: Determine which quarters to download
            status_text.text("Step 2/5: Identifying required datasets...")
            progress_bar.progress(0.2)
            
            available_quarters = get_available_quarters()
            # Determine how many quarters to fetch
            num_periods = years * (4 if data_frequency == "Quarterly" else 1)
            quarters_to_fetch = available_quarters[:min(num_periods * 2, len(available_quarters))]  # Fetch extra to ensure coverage
            
            st.info(f"Will search {len(quarters_to_fetch)} quarterly datasets")
            
            # Step 3: Download datasets
            status_text.text("Step 3/5: Downloading SEC datasets (this may take 1-2 minutes)...")
            progress_bar.progress(0.3)
            
            filing_type = "10-K" if data_frequency == "Annual" else "10-Q"
            all_filings = []
            datasets_checked = 0
            
            for quarter in quarters_to_fetch:
                datasets_checked += 1
                progress = 0.3 + (0.3 * datasets_checked / len(quarters_to_fetch))
                progress_bar.progress(progress)
                status_text.text(f"Step 3/5: Checking dataset {quarter}... ({datasets_checked}/{len(quarters_to_fetch)})")
                
                sub_df, num_df, tag_df = download_dataset(quarter)
                
                if sub_df is None or num_df is None or tag_df is None:
                    continue
                
                # Look for company filings in this dataset
                filings = get_company_data(cik, num_df, sub_df, tag_df, filing_type)
                
                for filing in filings:
                    all_filings.append((filing, num_df, tag_df))
                
                # Stop if we have enough filings
                if len(all_filings) >= num_periods:
                    break
                
                time.sleep(0.2)  # Rate limiting
            
            if not all_filings:
                st.error(f"No {filing_type} filings found in available datasets")
                return
            
            # Limit to requested number of periods
            all_filings = all_filings[:num_periods]
            st.success(f"Found {len(all_filings)} {filing_type} filings")
            
            # Step 4: Extract financial data
            status_text.text("Step 4/5: Extracting financial statements...")
            progress_bar.progress(0.7)
            
            filings_data = []
            for i, (filing, num_df, tag_df) in enumerate(all_filings):
                progress = 0.7 + (0.2 * (i + 1) / len(all_filings))
                progress_bar.progress(progress)
                
                statements = extract_financial_statements(filing['adsh'], num_df, tag_df)
                if statements:
                    filings_data.append((filing['period'], statements))
            
            if not filings_data:
                st.error("Could not extract financial data from filings")
                return
            
            # Step 5: Aggregate data
            status_text.text("Step 5/5: Aggregating data across periods...")
            progress_bar.progress(0.9)
            
            combined_data = aggregate_multi_period_data(filings_data)
            
            st.session_state.financial_data = combined_data
            st.session_state.data_retrieved = True
            
            # Complete
            status_text.text("Complete!")
            progress_bar.progress(1.0)
            
            st.success(f"✅ Retrieved financial data for {ticker}")
            
        except Exception as e:
            st.error(f"Error during data retrieval: {str(e)}")
            import traceback
            st.error(traceback.format_exc())
            return
    
    # Display results and download options
    if st.session_state.data_retrieved and st.session_state.financial_data:
        data = st.session_state.financial_data
        
        st.markdown("---")
        st.header("📈 Results Summary")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric(
                "Balance Sheet Records",
                len(data['balance_sheet'])
            )
        
        with col2:
            st.metric(
                "Income Statement Records",
                len(data['income_statement'])
            )
        
        with col3:
            st.metric(
                "Cash Flow Records",
                len(data['cash_flow'])
            )
        
        # Data preview
        st.markdown("---")
        st.header("📋 Data Preview")
        
        tab1, tab2, tab3 = st.tabs(["Balance Sheet", "Income Statement", "Cash Flow"])
        
        with tab1:
            if not data['balance_sheet'].empty:
                st.dataframe(data['balance_sheet'], use_container_width=True)
            else:
                st.info("No balance sheet data available")
        
        with tab2:
            if not data['income_statement'].empty:
                st.dataframe(data['income_statement'], use_container_width=True)
            else:
                st.info("No income statement data available")
        
        with tab3:
            if not data['cash_flow'].empty:
                st.dataframe(data['cash_flow'], use_container_width=True)
            else:
                st.info("No cash flow data available")
        
        # Download section
        st.markdown("---")
        st.header("💾 Download Data")
        
        download_col1, download_col2 = st.columns(2)
        
        if "Excel" in output_format:
            with download_col1:
                excel_buffer = create_excel_download(data, st.session_state.ticker)
                file_size = len(excel_buffer.getvalue()) / 1024  # KB
                
                st.download_button(
                    label=f"📥 Download Excel File ({file_size:.1f} KB)",
                    data=excel_buffer,
                    file_name=f"{st.session_state.ticker}_financials.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True
                )
        
        if "CSV" in output_format:
            with download_col2:
                st.markdown("**CSV Files:**")
                
                if not data['balance_sheet'].empty:
                    csv_buffer = create_csv_download(data['balance_sheet'])
                    st.download_button(
                        label="Balance Sheet CSV",
                        data=csv_buffer,
                        file_name=f"{st.session_state.ticker}_balance_sheet.csv",
                        mime="text/csv",
                        use_container_width=True
                    )
                
                if not data['income_statement'].empty:
                    csv_buffer = create_csv_download(data['income_statement'])
                    st.download_button(
                        label="Income Statement CSV",
                        data=csv_buffer,
                        file_name=f"{st.session_state.ticker}_income_statement.csv",
                        mime="text/csv",
                        use_container_width=True
                    )
                
                if not data['cash_flow'].empty:
                    csv_buffer = create_csv_download(data['cash_flow'])
                    st.download_button(
                        label="Cash Flow CSV",
                        data=csv_buffer,
                        file_name=f"{st.session_state.ticker}_cash_flow.csv",
                        mime="text/csv",
                        use_container_width=True
                    )
    
    # Help section
    with st.expander("ℹ️ How to Use This Tool"):
        st.markdown("""
        ### Instructions:
        
        1. **Enter Ticker Symbol**: Type the stock ticker (e.g., AAPL, MSFT, GOOGL)
        2. **Select Frequency**: Choose Annual (10-K) or Quarterly (10-Q) filings
        3. **Choose Period**: Select how many years of historical data (1-5 years)
        4. **Select Format**: Choose Excel, CSV, or both
        5. **Click Retrieve Data**: The app will download SEC datasets and extract data
        6. **Review Data**: Preview the extracted financial statements
        7. **Download**: Click download buttons to save files to your device
        
        ### Data Source:
        
        This tool uses **SEC Financial Statement Data Sets** - quarterly ZIP files published by the SEC containing pre-parsed XBRL data from all company filings.
        
        - Source: https://www.sec.gov/dera/data/financial-statement-data-sets.html
        - Data from 2020 onwards
        - Updated quarterly by the SEC
        - Contains standardized US-GAAP taxonomy tags
        
        ### Processing Time:
        
        - Each quarterly dataset is 50-200 MB
        - First download takes 1-2 minutes (cached for 1 hour)
        - Subsequent queries for same period are faster
        
        ### Important Notes:
        
        - Only works for U.S. public companies filing with the SEC
        - Data availability depends on SEC dataset publication schedule
        - Values are in the units reported by the company (typically USD)
        - Some line items may not be present for all companies
        - Data extracted uses US-GAAP standard taxonomy tags
        
        ### Limitations:
        
        - Company-specific accounting policies may vary
        - Not all line items available for all companies
        - Historical restatements may not be reflected
        - Data limited to periods covered by SEC datasets (2020+)
        """)

if __name__ == "__main__":
    main()
