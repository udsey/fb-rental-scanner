"""Functions for scraping data from Facebook's groups."""
import os
import random
import time
from datetime import datetime, timedelta
from typing import List, Optional
from selenium.webdriver import Chrome
from tqdm import tqdm
import logging

import pandas as pd


from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.wait import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.remote.webelement import WebElement

from scr.models import FacebookPostModel, FacebookGroupModel, ScraperConfigModel
from scr.setup import config, RAW_DATA_DIR, FACEBOOK_PASSWORD, FACEBOOK_USERNAME, save_config

logger = logging.getLogger(__name__)
#logger.setLevel(logging.DEBUG)

facebook_groups = config.user_config.facebook_groups



def save_raw_posts(raw_posts: list):
    if len(raw_posts) == 0:
        logger.info("Nothing to save.")
        return
    filename = f"raw_posts_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    full_path = os.path.join(RAW_DATA_DIR, filename)
    df = pd.DataFrame([post.model_dump() for post in raw_posts])
    os.makedirs(RAW_DATA_DIR, exist_ok=True)
    df.to_csv(full_path, index=False)
    logger.info(f"{df.shape[0]} posts was saved in {full_path}")


def text_to_datetime(created_at: str) -> Optional[datetime]:
    try:
        return datetime.strptime(created_at.replace('\u202f', ' ')
                             , '%A, %B %d, %Y at %I:%M %p')
    except Exception as e:
        logger.debug(e, exc_info=True)


def cooldown() -> None:
    a = config.system_config.scraper_config.cooldown_min
    b = config.system_config.scraper_config.cooldown_max
    time.sleep(random.uniform(a, b))


def configure_chrome() -> tuple[WebDriver, WebDriverWait]:
    """Configure chromedriver"""

    wait_timeout = config.system_config.scraper_config.wait_timeout

    options = Options()
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)
    # Mask webdriver property
    options.add_argument("--disable-blink-features=AutomationControlled")
    # Set a real user agent
    options.add_argument(
        "user-agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36")
    options.add_experimental_option("prefs", {
        "profile.default_content_setting_values.notifications": 2
    })

    driver = Chrome(service=Service(ChromeDriverManager().install()), options=options)
    driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
        "source": "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
    })
    wait = WebDriverWait(driver, wait_timeout)
    return driver, wait


def login_facebook(driver: WebDriver, 
                   wait: WebDriverWait, 
                   scraper_config: ScraperConfigModel):
    """Login to Facebook."""

    logger.info("Logging into Facebook accout.")

    driver.get(scraper_config.facebook_url)
    if not FACEBOOK_PASSWORD or not FACEBOOK_USERNAME:
        logger.info("Please log in.")

    else:
        username_input = wait.until(EC.presence_of_element_located(scraper_config.username_input.as_tuple()))
        username_input.send_keys(FACEBOOK_USERNAME)
        password_input = driver.find_element(*scraper_config.password_input.as_tuple())
        password_input.send_keys(FACEBOOK_PASSWORD)

        login_button = driver.find_element(*scraper_config.login_button.as_tuple())
        login_button.click()

    # TODO: add capcha detector
    capcha_detected = True
    if capcha_detected:
        logger.info("Please solve the CAPCHA")
        wait.until(EC.presence_of_element_located((scraper_config.search_facebook.as_tuple())))

    logger.info("Done!")


def scroll(driver, x: int = 0, y: int = 1000):
    driver.execute_script(f"window.scrollBy({x}, {y});")


def last_idx(driver: WebDriver, 
             scraper_config: ScraperConfigModel, 
             post_elements, 
             last_update: datetime):
    """Find last seen post."""
    n = len(post_elements)
    
    for i, post_element in enumerate(reversed(post_elements)):
        text = post_element.text
        if not text or "New posts" in text:
            continue

        globs = post_element.find_elements(*scraper_config.shared_with.as_tuple())
        if len(globs) == 0:
            continue

        panel = globs[0].find_element(*scraper_config.panel.as_tuple())
        share = panel.find_elements(*scraper_config.share.as_tuple())[-3]
        ActionChains(driver).move_to_element(share).perform()
        cooldown()

        created_at_el = driver.find_elements(*scraper_config.created_at.as_tuple())
        if len(created_at_el) == 0:
            continue

        created_at = text_to_datetime(created_at_el[0].text)
        if not created_at:
            continue

        idx = n - i - 1
        if created_at < last_update:
            return idx, created_at
        return None, None
    return None, None


def scroll_till_last(driver: WebDriver, 
                     scraper_config: ScraperConfigModel,
                     last_update: datetime):
    """Scroll down till last update."""
    limit = scraper_config.cycle_limit

    for i in range(limit):
        post_elements = driver.find_elements(*scraper_config.feed.as_tuple())
        idx, created_at = last_idx(
            driver=driver,
            scraper_config=scraper_config,
            post_elements=post_elements,
            last_update=last_update
        )
        if idx is None:
            scroll(driver=driver, y=scraper_config.scroll_y)
        elif created_at > last_update:
            scroll(driver=driver, y=scraper_config.scroll_y)
        else:
            break
        cooldown()
    scroll_into_element(driver, post_elements[idx])


def get_created_at(driver: WebDriver,
                   wait: WebDriverWait,
                   scraper_config: ScraperConfigModel,
                   share: WebElement) -> Optional[datetime]:
    """Get post creation time."""
    ActionChains(driver).move_to_element(share).perform()
    try:
        tooltip = wait.until(EC.presence_of_element_located(scraper_config.created_at.as_tuple()))
        return text_to_datetime(tooltip.text)
    except:
        return None


def read_post(driver: WebDriver,
              wait: WebDriverWait, 
              scraper_config: ScraperConfigModel,
              post_element: WebElement) -> FacebookPostModel:
    """Extract facebook post."""
    post = FacebookPostModel()
    try:
        globe = post_element.find_element(*scraper_config.shared_with.as_tuple())
        panel = globe.find_element(*scraper_config.panel.as_tuple())
        share = panel.find_elements(*scraper_config.share.as_tuple())[-3]

        post.created_at = get_created_at(driver=driver,
                                         wait=wait,
                                         scraper_config=scraper_config,
                                         share=share)

        post_container = panel.find_element(*scraper_config.post_container.as_tuple())
        see_more = post_element.find_elements(*scraper_config.see_more.as_tuple())
        if see_more:
            see_more[0].click()

        post.raw_content = post_container.text
        post_content = post_container.text.split('·')
        post.author = post_content[0].split('\n')[0].strip()
        post.text = post_content[-1].split("See translation")[0].strip()

        post.url = share.find_element(*scraper_config.post_url.as_tuple()).get_attribute("href").split("?")[0]

    except Exception as e:
        logger.debug(e, exc_info=True)
    return post


def read_visible_posts(driver: WebDriver,
                       wait: WebDriverWait,
                       scraper_config: ScraperConfigModel,
                       last_update: datetime) -> List[FacebookPostModel]:
    """Read visible posts."""
    posts = []
    seen_urls = set()

    post_elements = driver.find_elements(*scraper_config.feed.as_tuple())
    try:
        for post_element in tqdm(reversed(post_elements), 
                                 total=len(post_elements), 
                                 desc="Reading new posts:", 
                                 bar_format='{percentage:3.0f}%|{bar}|'):
            text = post_element.text
            if not text or "New posts" in text:
                continue
            scroll_into_element(driver=driver, 
                                element=post_element)
            cooldown()
            post = read_post(driver=driver, 
                             wait=wait,
                             scraper_config=scraper_config,
                             post_element=post_element)
            #cooldown()
            if not post.url or post.url in seen_urls:
                continue

            if post.created_at and post.created_at <= last_update:
                continue

            seen_urls.add(post.url)
            posts.append(post)
    except Exception as e:
        logger.debug(e, exc_info=True)
    return posts


def scroll_into_element(driver: WebDriver, 
                        element: WebElement, 
                        offset: int =-100):
    """Scroll view into the top of element."""
    driver.execute_script(f"arguments[0].scrollIntoView(true); window.scrollBy(0, {offset});", element)


def read_group_new_posts(driver: WebDriver,
                         wait: WebDriverWait, 
                         scraper_config: ScraperConfigModel,
                         group_info: FacebookGroupModel) -> List[FacebookPostModel]:
    """Read new messages in group."""
    url = group_info.url
    last_update = group_info.last_visited
    max_update_time = datetime.now() - timedelta(minutes=scraper_config.max_timedelta_mins)

    if not last_update or last_update < max_update_time:
        last_update = max_update_time
    logger.info(f"Entering group: {url}")
    driver.get(url)
    cooldown()
    logger.info(f"Scrolling down till {last_update}")
    scroll_till_last(driver=driver,
                     scraper_config=scraper_config,
                     last_update=last_update)
    #cooldown()
    logger.info(f"Reading new posts since {last_update}")
    posts = read_visible_posts(driver=driver,
                               wait=wait,
                               scraper_config=scraper_config,
                               last_update=last_update)
    return posts



def read_new_posts_from_all_groups(driver: WebDriver, wait: WebDriverWait):
    """Read new posts across all groups."""
    group_info = config.user_config.facebook_groups
    scraper_config = config.system_config.scraper_config
    raw_posts = []
    for group_info in facebook_groups:
        try:
            current_time = datetime.now()
            group_posts = read_group_new_posts(driver=driver, 
                                               wait=wait,
                                               scraper_config=scraper_config,
                                               group_info=group_info)
            raw_posts += group_posts
            group_info.last_visited = current_time
        except Exception as e:
            logger.debug(e, exc_info=True)
    save_raw_posts(raw_posts=raw_posts)
    save_config(config=config.user_config, filename="user_config.yaml")
    logger.info("Done!")


