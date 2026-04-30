"""Functions for scraping data from Facebook's groups."""
import os
import random
import time
from datetime import datetime
import yaml

import pandas as pd

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.wait import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC

from scraper.models import PostModel, GroupModel

def save_raw_posts(raw_posts: list, path: str = './raw_posts') -> None:
    filename = f"raw_posts_{str(datetime.now())}.csv"
    full_path = os.path.join(path, filename)
    df = pd.DataFrame([post.model_dump() for post in raw_posts])
    df.to_csv(full_path, index=False)


def to_datetime(created_at: str):
    if created_at:
        return datetime.strptime(created_at.replace('\u202f', ' ')
                             , '%A, %B %d, %Y at %I:%M %p')


def rest():
    time.sleep(random.uniform(1, 5))


def configure_chrome(wait_timeout=100):
    """Configure chromedriver"""
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
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
        "source": "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
    })
    wait = WebDriverWait(driver, wait_timeout)
    return driver, wait


def login(driver, wait, username: str, password: str):
    """Login to Facebook."""
    driver.get("https://facebook.com")
    time.sleep(2)

    if not username or not password:
        print("Please log in.")

    else:
        # Log-in
        username_input = driver.find_element(by=By.NAME, value="email")
        username_input.send_keys(username)

        password_input = driver.find_element(by=By.NAME, value="pass")
        password_input.send_keys(password)

        login_button = driver.find_element(by=By.CSS_SELECTOR, value="div[role='button'][aria-label='Log in']")
        login_button.click()

    # TODO and capcha detector
    capcha_detected = True
    if capcha_detected:
        print("Please solve the CAPCHA")
        # Wait until user solves CAPCHA
        expected_element = wait.until(
        EC.presence_of_element_located((By.CSS_SELECTOR,
                                        "input[placeholder='Search Facebook']")))


def scroll(driver, x: int = 0, y: int = 1000):
    driver.execute_script(f"window.scrollBy({x}, {y});")


def read_post(driver, post_element) -> PostModel:
    post = PostModel()
    try:
        globe = post_element.find_element(By.CSS_SELECTOR, "[title*='Shared with']")
        panel = globe.find_element(By.XPATH, "../../../..")
        share = panel.find_elements(By.XPATH, "./*")[-3]
        ActionChains(driver).move_to_element(share).perform()
        rest()
        created_at = driver.find_element(By.CSS_SELECTOR, "[role='tooltip']").text
        post.created_at = to_datetime(created_at)
        share.click()
        rest()
        post_url = (share.find_element(By.CSS_SELECTOR, "a[href*='/posts/']")
                    .get_attribute("href")
                    .split("?")[0])
        post.url = post_url
        message = driver.find_elements(By.CSS_SELECTOR, "[role='dialog']")[1].text
        post.message = message.split('·')[-1].split('Like')[0].strip()
        close_btn = driver.find_element(By.CSS_SELECTOR, "[aria-label='Close']")
        close_btn.click()
    except:
        pass

    return post

def read_visible_posts(driver,
                       post_elements: list,
                       last_update: datetime,
                       seen_locations: set,
                       last_y: int,
                       seen_urls: set):
    posts = []
    for post_element in post_elements:
        rest()
        try:
            location = tuple(post_element.location.values())
            location_error = None
        except Exception as e:
            location = None
            location_error = e
        if not location or location[1] <= last_y or location in seen_locations:
            continue

        post = read_post(driver=driver,
                         post_element=post_element)

        if not post.url or post.url in seen_urls:
            continue

        posts.append(post)
        seen_urls.add(post.url)
        seen_locations.add(location)
        last_y = location[1]

        if post.created_at and post.created_at <= last_update:
            return posts
    return posts, last_y


def read_group(driver, group_info: GroupModel, limit: int = 3):
    url = group_info.url
    last_update = group_info.last_visited

    posts_data = []
    seen_locations = set()
    last_y = 0
    seen_urls = set()

    driver.get(url)
    rest()
    scroll(driver, y=1000)

    for i in range(limit):
        post_elements = driver.find_elements(By.CSS_SELECTOR, "div[role='feed'] > div")
        posts, last_y = read_visible_posts(driver=driver,
                                           post_elements=post_elements,
                                           last_update=last_update,
                                           seen_locations=seen_locations,
                                           last_y=last_y,
                                           seen_urls=seen_urls)
        posts_data += posts
        scroll(driver, y=1000)
        rest()

    return posts_data


