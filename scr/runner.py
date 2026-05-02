import os
import sys
import select
import time
import logging
import pandas as pd
from scr.setup import config, RAW_DATA_DIR, DATA_DIR
from scr.parser import select_relevant_apartments
from scr.scraper import login_facebook, configure_chrome, read_new_posts_from_all_groups
from scr.manual_operations import review_apartments, generate_messages

logger = logging.getLogger(__name__)

def check_relevant() -> bool:
    filepath = os.path.join(DATA_DIR, 'relevant_apartments.csv')
    if os.path.isfile(filepath):
        df = pd.read_csv(filepath)
    n_relevant = df.shape[0]
    return n_relevant


def wait_for_input(n_relevant, timeout: int = 30) -> bool:
    """Wait for user input."""
    logger.info(f"There are {n_relevant} unreviewed relevant apartments. Press 'y' to review, 'n' to skip (auto-skip in {timeout}mins).")    
    ready, _, _ = select.select([sys.stdin], [], [], timeout)
    if ready:
        answer = sys.stdin.readline().strip().lower()
        return answer == 'y'
    return False


if __name__ == "__main__":

    driver, wait = configure_chrome()
    scraper_config = config.system_config.scraper_config

    login_facebook(driver=driver, 
                scraper_config=scraper_config,
                wait=wait)

    # Block images and videos
    driver.execute_cdp_cmd("Network.setBlockedURLs", {"urls": [
        "*.jpg", "*.jpeg", "*.png", "*.gif", "*.webp",
        "*.mp4", "*.webm", "*.ogg", "*.mov", "*.avi", "*.m3u8", "*.ts"
    ]})
    driver.execute_cdp_cmd("Network.enable", {})




    while True:
        try:
            logger.info("-"*100)
            logger.info("New iteration started.")
            logger.info("-"*100)
            read_new_posts_from_all_groups(driver=driver)
            
            new_files = os.listdir(RAW_DATA_DIR)
            if len(new_files) == 0:
                continue

            logger.info("Parsing new posts.")
            select_relevant_apartments()
            n_relevant = check_relevant()
            if n_relevant:
                decision = wait_for_input(n_relevant=n_relevant)
                if decision:
                    review_apartments()
                    generate_messages()
                    
            time.sleep(config.system_config.runner_config.interval_mins * 60)
        except Exception as e:
            logger.exception(e)



