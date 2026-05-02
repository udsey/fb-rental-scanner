.PHONY: help add-apartments review-apartments

help:
	@echo "Available commands:"
	@echo "  make add-apartments    	- Manually add apartments to CSV"
	@echo "  make review-apartments 	- Review and remove apartments from CSV"
	@echo "  make generate-messages 	- Generate texts for all relevant apartments"
	@echo "  make filter-raw        	- Filter apartments from scraper's raw files"
	@echo "  make monitor-apartments    - Monitoring apartments"

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