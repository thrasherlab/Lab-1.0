# PE Deal Tracker

A Python tool that automatically reads your Gmail inbox for private equity newsletters and extracts deal announcements into a structured database.

## Features

- **Automated Email Fetching**: Connects to Gmail API to fetch PE newsletters
- **Intelligent Extraction**: Uses Claude API to extract structured deal information
- **Comprehensive Data**: Captures target company, acquirer, PE firms (buy-side and sell-side), deal value, and more
- **SQLite Database**: Stores all deals in a local database for easy querying
- **CSV Export**: Export deals to CSV for analysis in Excel or other tools
- **Flexible Filtering**: Filter by date range, news outlet, or Gmail labels

## Supported Newsletters

Pre-configured for common PE newsletters:
- PitchBook
- Axios Pro Rata
- PE Hub
- DealBook
- Bloomberg
- WSJ Pro PE
- Financial Times
- And more...

You can also configure custom sender domains or use Gmail labels.

## Installation

### Prerequisites

- Python 3.8 or higher
- Gmail account
- Anthropic API key
- Google Cloud project with Gmail API enabled

### 1. Clone or Download Repository

```bash
cd Lab-1.0
```

### 2. Create Virtual Environment

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Set Up Gmail API

Follow the detailed instructions in [config_templates/GMAIL_SETUP.md](config_templates/GMAIL_SETUP.md)

Quick summary:
1. Create a Google Cloud project
2. Enable Gmail API
3. Create OAuth 2.0 credentials (Desktop app)
4. Download credentials and save as `credentials.json` in project root

### 5. Set Up Anthropic API

1. Get your API key from [Anthropic Console](https://console.anthropic.com/)
2. Copy `.env.example` to `.env`:
   ```bash
   cp .env.example .env
   ```
3. Edit `.env` and add your API key:
   ```
   ANTHROPIC_API_KEY=your_actual_api_key_here
   ```

## Usage

### Fetch and Extract Deals

Fetch emails from the last 30 days and extract deals:

```bash
python src/main.py fetch
```

Fetch emails from the last 7 days:

```bash
python src/main.py fetch --days 7
```

Fetch emails from a specific date range:

```bash
python src/main.py fetch --start-date 2024-01-01 --end-date 2024-01-31
```

Fetch more emails (default is 100):

```bash
python src/main.py fetch --max-emails 500
```

Fetch emails with a specific Gmail label:

```bash
python src/main.py fetch --label "PE Newsletters"
```

### View Statistics

See summary statistics about your deal database:

```bash
python src/main.py stats
```

### List Deals

View deals in the terminal:

```bash
python src/main.py list-deals
```

List deals from a specific date range:

```bash
python src/main.py list-deals --start-date 2024-01-01 --end-date 2024-01-31
```

List deals from a specific news outlet:

```bash
python src/main.py list-deals --outlet "PitchBook"
```

Show more deals (default is 20):

```bash
python src/main.py list-deals --limit 50
```

### Export to CSV

Export all deals to CSV:

```bash
python src/main.py export
```

Export to a custom location:

```bash
python src/main.py export --output exports/q1_2024_deals.csv
```

Export with filters:

```bash
python src/main.py export --start-date 2024-01-01 --end-date 2024-03-31 --outlet "PitchBook"
```

## Data Schema

Each deal record includes:

| Field | Description |
|-------|-------------|
| `deal_name` | Concise name for the deal |
| `date_announced` | Date the deal was announced |
| `target_company` | Company being acquired/sold |
| `selling_pe_firm` | PE firm selling (if sponsor exit) |
| `acquiring_company` | Entity acquiring the target |
| `acquiring_pe_firm` | PE firm behind the acquirer |
| `deal_type` | Type (buyout, growth equity, exit, merger, add-on) |
| `deal_value` | Deal value if disclosed |
| `news_outlet` | Newsletter source |
| `email_subject` | Subject line of source email |
| `email_date` | Date email was sent |
| `confidence_score` | Extraction confidence (high/medium/low) |

## Project Structure

```
Lab-1.0/
├── src/
│   ├── main.py              # CLI interface and orchestration
│   ├── gmail_client.py      # Gmail API integration
│   ├── deal_extractor.py    # Claude API integration
│   └── database.py          # SQLite database management
├── config_templates/
│   └── GMAIL_SETUP.md       # Gmail setup instructions
├── exports/                 # CSV exports (created automatically)
├── .env.example             # Environment variable template
├── requirements.txt         # Python dependencies
└── README.md               # This file
```

## How It Works

1. **Gmail Fetching**: Connects to Gmail API and fetches emails from specified newsletters based on date range and filters
2. **Content Extraction**: Each email is sent to Claude API with a structured prompt
3. **Deal Parsing**: Claude extracts deal information and returns structured JSON
4. **Database Storage**: Deals are stored in SQLite database with deduplication (by email ID)
5. **Export**: Query and export deals to CSV for analysis

## Tips

- **First Run**: The first time you run `fetch`, a browser will open for Gmail authentication
- **Token Storage**: After first auth, a `token.json` file is created for future runs
- **Deduplication**: Emails are tracked by ID, so re-running won't create duplicates
- **Newsletter Labels**: Consider creating a Gmail label for PE newsletters and using `--label` flag
- **API Costs**: Claude API charges per token. Expect ~$0.01-0.05 per email depending on length

## Troubleshooting

**Gmail authentication fails**
- Check that you've set up OAuth credentials correctly
- Make sure you added yourself as a test user
- See [config_templates/GMAIL_SETUP.md](config_templates/GMAIL_SETUP.md)

**No deals found**
- Check that you're fetching emails from the right date range
- Verify that the newsletters actually contain deal announcements
- Try `--max-emails 500` to fetch more emails

**Claude API errors**
- Verify your `ANTHROPIC_API_KEY` in `.env` file
- Check your API key is valid at [Anthropic Console](https://console.anthropic.com/)

**Database errors**
- The database file `pe_deals.db` is created automatically
- Delete it to start fresh if needed

## Security

- `credentials.json` and `token.json` contain sensitive Gmail credentials
- `.env` contains your Anthropic API key
- All are in `.gitignore` and will not be committed to git
- Never share these files publicly

## License

This project is provided as-is for personal use.

## Contributing

Feel free to submit issues or pull requests for improvements.
