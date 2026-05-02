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
3. **Filter** — applies your criteria from `user_config.yaml` (max price, location, property type, etc.)
4. **Review** — manually go through filtered apartments and keep/remove them
5. **Message** — generates ready-to-send messages for each remaining apartment

---

## Usage

### Automated mode
```bash
make monitor-apartments
```
Runs scraper and parser in a loop every N minutes (configurable in `system_config.yaml`). Prompts for manual review after each cycle if new relevant apartments are found.

### Step-by-step (Jupyter)
Open `demo.ipynb` and run cells one by one:
1. **Login** — opens Chrome, auto-fills credentials if provided, waits for CAPTCHA
2. **Scrape** — collects new posts from all configured groups
3. **Parse** — extracts structured data and filters by criteria
4. **Manual operations** — review, add, or generate messages

---

## Quick setup

```bash
cp .env.example .env
cp user_config.example.yaml user_config.yaml
```
1. Add FB credentials + Groq API key (or use local Ollama) in `.env`
2. Edit `user_config.yaml` with your groups, message template and criteria
3. Optionally edit `system_config.yaml` to change LLM, scrape interval, and timing

---

## CLI commands

```bash
make monitor-apartments  # run scraper + parser in a loop
make filter-raw          # reprocess raw scraped files
make add-apartments      # manually add apartments
make review-apartments   # review and remove apartments
make generate-messages   # generate messages for all relevant apartments
```

---

## Project structure
```
fb-rental-scanner/
├── demo.ipynb                     # step-by-step Jupyter walkthrough
├── user_config.yaml                # groups, criteria, message template
├── system_config.yaml              # LLM, scraper, and runner settings
├── .env                            # secrets
├── scr/
│   ├── runner.py                   # main loop: scrape → parse → review
│   ├── scraper.py                  # selenium scraping logic
│   ├── parser.py                   # LLM extraction and filtering
│   ├── models.py                   # pydantic models
│   ├── setup.py                    # config loading and logging setup
│   └── manual_operations.py        # manual review, add, and message generation
├── data/
│   ├── raw_data/                   # raw scraped CSVs (auto-deleted after parsing)
│   ├── unsorted_apartments.csv     # all extracted apartments before filtering
│   ├── relevant_apartments.csv     # filtered apartments
│   └── messages_<timestamp>.txt    # generated messages ready to send
└── makefile
```
---

## Configuration

**`user_config.yaml`** — things you change often:
- `facebook_groups` — list of group URLs to scrape
- `criteria` — price range, property type, location, etc.
- `message_template` — message sent to landlords

**`system_config.yaml`** — infrastructure settings:
- `llm_config` — model type (`groq` or `local`), model name, prompt
- `scraper_config` — cooldown, scroll speed, CSS/XPath selectors
- `runner_config` — scrape interval in minutes

---

## LLM support

Supports any model via LangChain. Tested with:
- **Groq** (`meta-llama/llama-4-scout-17b-16e-instruct`) — fast, free tier available
- **Ollama** (`llama3`) — fully local, no API key needed

Change `model_type` in `system_config.yaml` to switch.

---

## Notes

- Facebook requires manual CAPTCHA solving on first login
- Images and videos are blocked after login to speed up scraping
- `last_visited` per group is saved automatically in `user_config.yaml` after each run
- LLM uses structured output — null values and type coercion are handled automatically

---

## Disclaimer

This project was built for personal and educational purposes only. Scraping Facebook may violate their [Terms of Service](https://www.facebook.com/terms). The author is not responsible for any misuse or consequences of using this tool. Use at your own risk.