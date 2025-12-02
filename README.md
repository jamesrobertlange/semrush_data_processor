# SEMrush Data Processor

A simple Flask web application for processing SEMrush CSV exports.

## Features

- Process multiple SEMrush CSV files simultaneously
- Remove duplicates across files
- Filter by position
- Identify branded keywords
- Export combined results as CSV

## Quick Start

```bash
# Install UV (if not already installed)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install dependencies
uv sync

# Run the application
./run.sh
```

Open your browser to: **http://127.0.0.1:5000**

## Required CSV Columns

Your SEMrush CSV files must contain:
- `Keyword`
- `Position`
- `Search Volume`
- `URL`
- `Traffic`
- `Timestamp`

## Usage

1. Upload one or more SEMrush CSV files
2. Set the maximum position filter (default: 11)
3. Optionally enter branded terms (comma-separated)
4. Click "Process Data"
5. Download the processed CSV

## Project Structure

```
semrush-data-processor/
├── app.py                  # Main Flask application
├── pyproject.toml          # Dependencies
├── run.sh                  # Run script
├── Makefile               
├── config/
│   └── settings.py         # Configuration
├── modules/
│   └── data_processor.py   # Data processing logic
└── templates/              # HTML templates
```

## Commands

```bash
make install  # Install dependencies
make run      # Run development server
make prod     # Run production server
make clean    # Clean cache files
```

## License

MIT
