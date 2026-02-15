# SEC Financial Statement Data Extractor

A Streamlit web application for extracting actual financial statement data from SEC Financial Statement Data Sets.

## Overview

This tool retrieves real financial data from public company filings with the U.S. Securities and Exchange Commission (SEC). The application downloads and parses SEC Financial Statement Data Sets - quarterly ZIP files containing pre-parsed XBRL data from all company filings.

## Features

- **Ticker-based search**: Enter any U.S. public company ticker symbol
- **Flexible data frequency**: Choose annual (10-K) or quarterly (10-Q) filings
- **Historical data**: Retrieve up to 5 years of financial statements
- **Real data extraction**: Uses actual SEC Financial Statement Data Sets (not sample data)
- **Multiple output formats**: Download as Excel (multi-sheet) or individual CSV files
- **Interactive preview**: Review data before downloading
- **Progress tracking**: Real-time status updates during data retrieval
- **Smart caching**: Datasets cached for 1 hour to improve performance

## Financial Statements Included

- Balance Sheet
- Income Statement
- Cash Flow Statement

## Data Source

**SEC Financial Statement Data Sets**
- Source: https://www.sec.gov/dera/data/financial-statement-data-sets.html
- Quarterly ZIP files (50-200 MB each) containing pre-parsed XBRL data
- Available from 2020 onwards
- Updated quarterly by the SEC
- Contains standardized US-GAAP taxonomy tags

Each dataset includes three main files:
- `sub.txt`: Submission metadata (company info, filing dates, periods)
- `num.txt`: Numeric financial data (actual reported values)
- `tag.txt`: Tag definitions (descriptions of financial line items)

## Installation

### Prerequisites

- Python 3.8 or higher
- pip (Python package installer)

### Local Setup

1. Clone this repository:
```bash
git clone https://github.com/YOUR_USERNAME/sec-financial-data-tool.git
cd sec-financial-data-tool
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Run the application:
```bash
streamlit run app.py
```

4. Open your browser to `http://localhost:8501`

## Deployment on Streamlit Community Cloud

1. Fork or upload this repository to your GitHub account
2. Go to [share.streamlit.io](https://share.streamlit.io)
3. Sign in with GitHub
4. Click "New app"
5. Select your repository and set:
   - Branch: `main`
   - Main file path: `app.py`
6. Click "Deploy"

Your app will be live at: `https://your-app-name.streamlit.app`

## Usage

1. **Enter Ticker Symbol**: Type the stock ticker in the sidebar (e.g., AAPL, MSFT)
2. **Select Data Frequency**: Choose Annual or Quarterly
3. **Choose Historical Period**: Select 1-5 years using the slider
4. **Select Output Format**: Check Excel, CSV, or both
5. **Click "Retrieve Data"**: Wait for the app to download SEC datasets and extract data (1-2 minutes for first download)
6. **Preview Results**: Review the data in the tabs
7. **Download**: Click download buttons to save files to your device

## Example Companies

Try these ticker symbols:
- AAPL (Apple Inc.)
- MSFT (Microsoft Corporation)
- GOOGL (Alphabet Inc.)
- AMZN (Amazon.com Inc.)
- TSLA (Tesla Inc.)
- JPM (JPMorgan Chase & Co.)
- JNJ (Johnson & Johnson)
- WMT (Walmart Inc.)

## Processing Time

- **First download**: 1-2 minutes per quarterly dataset
- **Cached queries**: Much faster (datasets cached for 1 hour)
- **Annual data (5 years)**: Downloads ~5 quarterly datasets
- **Quarterly data (5 years)**: Downloads up to 20 quarterly datasets (but stops early if enough data found)

## Data Structure

The tool extracts key financial line items using US-GAAP standard taxonomy tags:

### Balance Sheet Tags
- Assets, AssetsCurrent, AssetsNoncurrent
- Liabilities, LiabilitiesCurrent, LiabilitiesNoncurrent
- StockholdersEquity
- CashAndCashEquivalentsAtCarryingValue
- AccountsReceivableNetCurrent
- PropertyPlantAndEquipmentNet
- And more...

### Income Statement Tags
- Revenues
- CostOfRevenue
- GrossProfit
- OperatingExpenses, OperatingIncomeLoss
- NetIncomeLoss
- EarningsPerShareBasic, EarningsPerShareDiluted
- And more...

### Cash Flow Tags
- NetCashProvidedByUsedInOperatingActivities
- NetCashProvidedByUsedInInvestingActivities
- NetCashProvidedByUsedInFinancingActivities
- Depreciation
- And more...

## Output Format

Downloaded files include:

**Excel File** (if selected):
- Single file with three sheets: Balance Sheet, Income Statement, Cash Flow
- Filename: `{TICKER}_financials.xlsx`

**CSV Files** (if selected):
- Three separate files for each statement type
- Filenames: `{TICKER}_balance_sheet.csv`, `{TICKER}_income_statement.csv`, `{TICKER}_cash_flow.csv`

Each file contains columns:
- Tag: US-GAAP taxonomy tag identifier
- Metric: Human-readable description
- Value: Reported numeric value
- Date: Reporting date
- Unit: Unit of measurement (typically USD)
- Period: Filing period

## Rate Limiting

The application complies with SEC fair access guidelines:
- Datasets are cached to minimize downloads
- Built-in delays between dataset checks
- Proper User-Agent header identification

## Limitations

- **Data availability**: Limited to periods covered by SEC datasets (2020 onwards)
- **Coverage**: Only U.S. public companies filing with SEC
- **Line items**: Not all line items available for all companies (depends on what company reports)
- **Taxonomy variations**: Some companies use company-specific extensions to US-GAAP
- **Dataset size**: Each quarterly dataset is 50-200 MB (first download takes time)
- **Restatements**: Historical restatements may not be reflected in older datasets
- **Non-GAAP metrics**: Tool extracts only standardized US-GAAP tags

## Troubleshooting

**"Could not find CIK for ticker"**:
- Verify the ticker symbol is correct
- Ensure the company is publicly traded in the U.S.
- Try alternative ticker format (e.g., BRK.B vs BRK-B)

**"No filings found in available datasets"**:
- Company may have gone public after 2020
- Try reducing the historical period requested
- Company may not file regularly (check SEC EDGAR directly)

**"Could not download dataset"**:
- SEC datasets may be temporarily unavailable
- Check internet connection
- Try again later (datasets are published quarterly)

**Download is slow**:
- First download of each dataset takes 1-2 minutes (50-200 MB files)
- Subsequent queries use cached data (much faster)
- Consider requesting fewer years initially

**Missing financial data**:
- Not all companies report all line items
- Some companies use non-standard taxonomy tags
- Try a larger, more established company (e.g., AAPL, MSFT) to verify tool is working

## Technical Details

### How It Works

1. **CIK Lookup**: Converts ticker symbol to CIK (Central Index Key) using SEC's company tickers JSON
2. **Dataset Identification**: Determines which quarterly datasets to download based on requested period
3. **Download & Parse**: Downloads SEC quarterly ZIP files and extracts tab-delimited text files
4. **Filter & Extract**: Filters for specific company and filing type, extracts US-GAAP tagged data
5. **Aggregate**: Combines data across multiple periods
6. **Format**: Structures data into financial statements with proper labeling
7. **Download**: Generates Excel/CSV files for user download

### Caching Strategy

- CIK lookups cached for 1 hour
- Dataset downloads cached for 1 hour
- Reduces redundant downloads for same period
- Improves performance for multiple queries

## Contributing

Contributions welcome. To contribute:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

Potential improvements:
- Additional financial metrics and ratios
- Data visualization charts
- Year-over-year comparison features
- Support for more taxonomy extensions
- Historical trend analysis

## License

This project is provided as-is for educational and research purposes.

## Disclaimer

This tool is for informational purposes only. Always verify financial data against official SEC filings. The authors are not responsible for any decisions made based on data from this tool.

Financial data is extracted from SEC Financial Statement Data Sets using standardized US-GAAP taxonomy tags. Some companies may report using different or company-specific tags not captured by this tool.

## Resources

- **SEC Financial Statement Data Sets**: https://www.sec.gov/dera/data/financial-statement-data-sets.html
- **SEC EDGAR Database**: https://www.sec.gov/edgar/searchedgar/companysearch.html
- **US-GAAP Taxonomy**: https://www.sec.gov/info/edgar/edgartaxonomies.shtml
- **XBRL Information**: https://www.xbrl.org/

## Contact

For questions or issues, please open a GitHub issue in this repository.

## Acknowledgments

- Data provided by the U.S. Securities and Exchange Commission
- Built with Streamlit, Pandas, and Python
- Uses SEC Financial Statement Data Sets (public domain data)
