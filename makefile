.PHONY: help add-apartments review-apartments

help:
	@echo "Available commands:"
	@echo "  make add-apartments    	- Manually add apartments to CSV"
	@echo "  make review-apartments 	- Review and remove apartments from CSV"
	@echo "  make generate-messages 	- Generate texts for all relevant apartments"
	@echo "  make filter-raw        	- Filter apartments from scraper's raw files"
	@echo "  make monitor-apartments    	- Monitoring apartments"
	@echo "  make scrap-facebook        	- Scrap facebook groups"

add-apartments:
	@uv run python -c "from scr.manual_operations import manually_add_relevant_apartments; manually_add_relevant_apartments()"

review-apartments:
	@uv run python -c "from scr.manual_operations import review_apartments; review_apartments()"

generate-messages:
	@uv run python -c "from scr.manual_operations import generate_messages; generate_messages()"

filter-raw:
	@uv run python -c "from scr.parser import select_relevant_apartments; select_relevant_apartments()"

monitor-apartments:
	@uv run python -m scr.runner

scrap-facebook:
	@uv run python -c 'from scr.setup import config, RAW_DATA_DIR, DATA_DIR; \
		from scr.scraper import login_facebook, configure_chrome, read_new_posts_from_all_groups; \
		driver, wait = configure_chrome(); \
		scraper_config = config.system_config.scraper_config; \
		login_facebook(driver=driver, scraper_config=scraper_config, wait=wait); \
		read_new_posts_from_all_groups(driver=driver, wait=wait)'