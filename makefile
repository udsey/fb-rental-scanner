.PHONY: help add-apartments review-apartments

help:
	@echo "Available commands:"
	@echo "  make add-apartments    - Manually add apartments to CSV"
	@echo "  make review-apartments - Review and remove apartments from CSV"
	@echo "  make filter-raw        - Filter apartments from scraper's raw files"

add-apartments:
	@uv run python -c "from manual_operations.functions import manually_add_relevant_apartments; manually_add_relevant_apartments()"

review-apartments:
	@uv run python -c "from manual_operations.functions import review_apartments; review_apartments()"

filter-raw:
	@uv run python -c "from parser.functions import select_relevant_apartments; select_relevant_apartments()"