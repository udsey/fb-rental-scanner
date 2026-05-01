# fb-rental-scanner
<p align="center">
  <img src="https://img.shields.io/badge/Python-3776AB?logo=python&logoColor=fff" alt="Python">
  <img src="https://img.shields.io/badge/LangChain-1c3c3c?logo=langchain&logoColor=white" alt="LangChain">
  <img src="https://img.shields.io/badge/Pandas-150458?logo=pandas&logoColor=fff" alt="Pandas">
  <img src="https://img.shields.io/badge/Pydantic-E92063?logo=pydantic&logoColor=white" alt="Pydantic">
  <img src="https://img.shields.io/badge/Selenium-43B02A?logo=selenium&logoColor=fff" alt="Selenium">
</p>

Automates apartment hunting by scraping Facebook groups, extracting structured data with an LLM, and generating ready-to-send messages to landlords.
> Because scrolling Facebook groups for hours is boring.

## How it works

1. **Scrape** — opens Facebook groups in Chrome, scrolls to the last unseen post, and collects new posts (author, text, timestamp, URL)
2. **Parse** — sends each post to an LLM to extract structured data: price, location, property type, utilities, move-in date, etc.
3. **Filter** — applies your criteria from `config.yaml` (max price, location, property type, etc.)
4. **Review** — manually go through filtered apartments and keep/remove them
5. **Message** — generates ready-to-send messages for each remaining apartment

---
## Usage

Open `demo.ipynb` in Jupyter and run cells step by step:

1. **Login** — opens Chrome, auto-fills credentials if provided, waits for CAPTCHA to be solved manually
2. **Scrape** — collects new posts from all configured groups
3. **Parse** — extracts structured data and filters by criteria
4. **Manual operations** — review, add, or generate messages
---
## Quick setup

```bash
cp .env.example .env
cp config.example.yaml config.yaml
```
1. Add FB credentials + Groq API key in `.env`
2. Edit `config.yaml` with your groups, message template and criteria

---

## CLI commands

```bash
make add-apartments      # manually add apartments
make review-apartments   # review and remove apartments
make generate-messages   # generate messages for all relevant apartments
make filter-raw          # reprocess raw scraped files
```
---
## Project structure

```
fb-rental-scanner/
├── demo.ipynb                      # Open [`demo.ipynb`](demo.ipynb) in Jupyter...
├── config.yaml                     # groups, criteria, message template
├── .env                            # secrets
├── scr/
│   ├── scraper.py                  # selenium scraping logic
│   ├── parser.py                   # LLM extraction and filtering
│   ├── models.py                   # pydantic models
│   └── manual_operations.py        # manual review, add, and message generation
├── data/
│   ├── raw_data/                   # raw scraped CSVs (auto-deleted after parsing)
│   ├── relevant_apartments.csv     # filtered apartments
│   └── messages.txt                # generated messages ready to send
└── makefile
```
---
## Notes

- Facebook requires manual CAPTCHA solving on first login
- Images are blocked after login to speed up scraping
- `last_visited` per group is updated automatically in `config.yaml` after each run
- LLM extraction uses structured output — works with any OpenAI-compatible API (tested with Groq)

---
## Disclaimer

This project was built for personal and educational purposes only. Scraping Facebook may violate their [Terms of Service](https://www.facebook.com/terms). The author is not responsible for any misuse or consequences of using this tool. Use at your own risk.
