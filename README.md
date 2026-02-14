# SEC Financial Statement Data Extractor

A Streamlit web application for extracting financial statement data from SEC EDGAR filings.

## Overview

This tool allows users to retrieve and download financial data from public company filings with the U.S. Securities and Exchange Commission (SEC). The application fetches data from the SEC EDGAR database and presents it in a user-friendly format with downloadable Excel and CSV outputs.

## Features

- **Ticker-based search**: Enter any U.S. public company ticker symbol
- **Flexible data frequency**: Choose annual (10-K) or quarterly (10-Q) filings
- **Historical data**: Retrieve up to 5 years of financial statements
- **Multiple output formats**: Download as Excel (multi-sheet) or individual CSV files
- **Interactive preview**: Review data before downloading
- **Progress tracking**: Real-time status updates during data retrieval

## Financial Statements Included

- Balance Sheet
- Income Statement
- Cash Flow Statement

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
5. **Click "Retrieve Data"**: Wait for the app to fetch SEC filings
6. **Preview Results**: Review the data in the tabs
7. **Download**: Click download buttons to save files to your device

## Example Companies

Try these ticker symbols:
- AAPL (Apple Inc.)
- MSFT (Microsoft Corporation)
- GOOGL (Alphabet Inc.)
- AMZN (Amazon.com Inc.)
- TSLA (Tesla Inc.)

## Important Notes

### Current Implementation Status

This is a **demonstration version** that shows the complete application structure and user interface. The current version:

- ✅ Retrieves company CIK numbers from SEC database
- ✅ Fetches filing metadata (dates, accession numbers)
- ✅ Provides full UI/UX with download capabilities
- ⚠️ Uses sample data for demonstration (actual XBRL parsing not yet implemented)

### Full Production Implementation Requirements

For a production version with actual XBRL data parsing, you would need to:

1. **Use SEC Financial Statement Data Sets**:
   - Download quarterly ZIP files from: https://www.sec.gov/dera/data/financial-statement-data-sets.html
   - Parse the tab-delimited text files containing pre-processed XBRL data

2. **Implement XBRL Parsing**:
   - Use libraries like `arelle`, `python-xbrl`, or `xbrlreader`
   - Map GAAP taxonomy elements to standardized labels
   - Handle company-specific taxonomy extensions

3. **Add Data Validation**:
   - Verify statement balancing (Assets = Liabilities + Equity)
   - Check for duplicate or conflicting values
   - Identify restatements

## Data Source

All data is retrieved from the SEC EDGAR database:
- Company information: https://data.sec.gov/submissions/
- Filings: https://www.sec.gov/cgi-bin/browse-edgar

## Rate Limiting

The application complies with SEC fair access guidelines:
- Maximum 10 requests per second
- Proper User-Agent header identification
- Built-in delays between requests

## Limitations

- Only works for U.S. public companies filing with the SEC
- Data availability depends on company filing history
- Some companies may have limited historical data
- Company-specific accounting policies may result in non-standard taxonomy
- Does not include amended filings or restatements automatically

## Supported Line Items

The tool extracts common financial statement items including:

**Balance Sheet**:
- Assets (Current, Non-Current, Total)
- Liabilities (Current, Non-Current, Total)
- Stockholders' Equity

**Income Statement**:
- Revenue
- Cost of Revenue
- Operating Expenses
- Net Income

**Cash Flow Statement**:
- Operating Activities
- Investing Activities
- Financing Activities

## Troubleshooting

**"Could not find CIK for ticker"**:
- Verify the ticker symbol is correct
- Ensure the company is publicly traded in the U.S.
- Try alternative ticker format (e.g., BRK.B vs BRK-B)

**"No filings found"**:
- Company may have recently gone public
- Reduce the historical period requested
- Check if company files regularly with SEC

**Download button not working**:
- Ensure data retrieval completed successfully
- Check browser download settings
- Try a different browser

## Contributing

Contributions welcome. To contribute:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## License

This project is provided as-is for educational and research purposes.

## Disclaimer

This tool is for informational purposes only. Always verify financial data against official SEC filings. The authors are not responsible for any decisions made based on data from this tool.

## Contact

For questions or issues, please open a GitHub issue in this repository.

## Acknowledgments

- Data provided by the U.S. Securities and Exchange Commission
- Built with Streamlit, Pandas, and Python
