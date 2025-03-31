# Chrome History Extractor

A command-line tool for extracting and analyzing your Chrome browser history. 
It can generate reports of your most visited domains, mail-to links, and top 
100 URLs, with options to either display results in the terminal or send them via email.

## Installation

```bash
uv pip install git@github.com:arrrlo/chrome_history_extractor.git
```

## Features

- Extracts Chrome browsing history for the last 7 days
- Generates reports for:
  - Most visited domains with visit counts
  - Mail-to domains
  - Top 100 visited URLs
- Output options:
  - Terminal display using ASCII tables
  - Email reports with CSV attachments
- Automated reporting via cron job setup

## Usage

### Basic Command Structure

```bash
chrome_history_extractor [COMMAND] [OPTIONS]
```

### Commands

#### 1. Extract History

```bash
chrome_history_extractor extract-history [OPTIONS]
```

**Options:**
- `-h, --smtp_host`: SMTP host server
- `-p, --smtp_port`: SMTP port number
- `-u, --username`: SMTP username
- `-k, --api_key`: SMTP API key/password
- `-s, --sender_email`: Sender's email address
- `-r, --recipient_email`: Recipient's email address

If email options are not provided, results will be displayed in the terminal.

#### 2. Set up Cron Job

```bash
chrome_history_extractor set-cron-job [OPTIONS]
```

Sets up a cron job to automatically send history reports every Monday at 15:00.

**Options:**
- Same as extract-history command

### Examples

1. Display history in terminal:
```bash
chrome_history_extractor extract-history
```

2. Send history report via email:
```bash
chrome_history_extractor extract-history \
    -h smtp.example.com \
    -p 587 \
    -u your_username \
    -k your_api_key \
    -s sender@example.com \
    -r recipient@example.com
```

3. Set up weekly email reports:
```bash
chrome_history_extractor set-cron-job \
    -h smtp.example.com \
    -p 587 \
    -u your_username \
    -k your_api_key \
    -s sender@example.com \
    -r recipient@example.com
```

## Output Format

### Terminal Output
Results are displayed in ASCII tables showing:
- Domain/URL
- Visit count
- Last visited timestamp

### Email Output
When using email options, three CSV files are attached:
- `domains.csv`: Most visited domains
- `mail_to_domains.csv`: Mail-to domain statistics
- `top_100_urls.csv`: Top 100 most visited URLs

## Requirements

- Python 3.x
- Google Chrome
- Required Python packages:
  - click
  - terminaltables
  - pytest (for development)
  - pytest-mock (for development)

## Notes

- The tool only processes history from the last 7 days
- Chrome must be installed in the default location
- URLs are truncated to 150 characters in terminal display
- Email functionality requires valid SMTP credentials

## License

MIT License