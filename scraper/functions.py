"""Functions for scraping data from Facebook's groups."""
import os
import random
import time
from datetime import datetime, timedelta
import yaml
from dotenv import load_dotenv

import pandas as pd

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.wait import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC

from models import PostModel, GroupModel

load_dotenv()

FACEBOOK_USERNAME = os.getenv("FACEBOOK_USERNAME")
FACEBOOK_PASSWORD = os.getenv("FACEBOOK_PASSWORD")

with open(os.path.join("../config.yaml"), "r") as f:
    config = yaml.safe_load(f)

facebook_groups = [GroupModel(idx=i, **g) for i, g in enumerate(config['groups'])]


def save_raw_posts(raw_posts: list, path: str = '../raw_data') -> None:
    if len(raw_posts) == 0:
        print("Nothing to save.")
        return
    filename = f"raw_posts_{str(datetime.now())}.csv"
    full_path = os.path.join(path, filename)
    df = pd.DataFrame([post.model_dump() for post in raw_posts])
    df.to_csv(full_path, index=False)
    print("Done!")


def text_to_datetime(created_at: str):
    try:
        return datetime.strptime(created_at.replace('\u202f', ' ')
                             , '%A, %B %d, %Y at %I:%M %p')
    except:
        print(created_at)


def cooldown(a=2, b=3):
    time.sleep(random.uniform(a, b))


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


def login(driver, wait):
    """Login to Facebook."""
    driver.get("https://facebook.com")
    time.sleep(2)

    if not FACEBOOK_PASSWORD or not FACEBOOK_USERNAME:
        print("Please log in.")

    else:
        # Log-in
        username_input = driver.find_element(by=By.NAME, value="email")
        username_input.send_keys(FACEBOOK_USERNAME)

        password_input = driver.find_element(by=By.NAME, value="pass")
        password_input.send_keys(FACEBOOK_PASSWORD)

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

    print("Done!")


def scroll(driver, x: int = 0, y: int = 1000):
    driver.execute_script(f"window.scrollBy({x}, {y});")


def last_idx(driver, post_elements, last_update):
    n = len(post_elements)
    for i, post_element in enumerate(reversed(post_elements)):
        text = post_element.text
        if not text or "New posts" in text:
            continue
        globs = post_element.find_elements(By.CSS_SELECTOR, "[title*='Shared with']")
        if len(globs) == 0:
            continue

        panel = globs[0].find_element(By.XPATH, "../../../..")
        share = panel.find_elements(By.XPATH, "./*")[-3]
        ActionChains(driver).move_to_element(share).perform()
        cooldown()
        created_at_el = driver.find_elements(By.CSS_SELECTOR, "[role='tooltip']")
        if len(created_at_el) == 0:
            continue

        created_at = text_to_datetime(created_at_el[0].text)
        if not created_at:
            continue

        idx = n - i - 1
        if created_at < last_update:
            return idx, created_at  # return the next one (last new post)
        return None, None  # all posts are new
    return None, None


def scroll_till_last(driver, last_update, limit=300):
    for i in range(limit):
        post_elements = driver.find_elements(By.CSS_SELECTOR, "div[role='feed'] > div")
        idx, created_at = last_idx(driver, post_elements, last_update)
        if idx is None:
            scroll(driver=driver, y=5000)  # all new, need more posts
        elif created_at > last_update:
            scroll(driver=driver, y=5000)
        else:
            break
        time.sleep(5)
    scroll_into_element(driver, post_elements[idx])


def get_created_at(driver, share):
    ActionChains(driver).move_to_element(share).perform()
    cooldown()
    created_at = driver.find_elements(By.CSS_SELECTOR, "[role='tooltip']")
    if created_at:
        return text_to_datetime(created_at[0].text)
    return None


def read_post(driver, post_element) -> PostModel:
    post = PostModel()
    try:
        globe = post_element.find_element(By.CSS_SELECTOR, "[title*='Shared with']")
        panel = globe.find_element(By.XPATH, "../../../..")
        share = panel.find_elements(By.XPATH, "./*")[-3]

        post.created_at = get_created_at(driver, share)

        post_container = panel.find_element(By.XPATH, "../../../../../../..")
        see_more = post_element.find_elements(By.XPATH, ".//*[contains(text(), 'See more')]")
        if see_more:
            see_more[0].click()

        post.raw_content = post_container.text
        post_content = post_container.text.split('·')
        post.author = post_content[0].split('\n')[0].strip()
        post.text = post_content[-1].split("See translation")[0].strip()

        post.url = share.find_element(By.CSS_SELECTOR, "a[href*='/posts/']").get_attribute("href").split("?")[0]

    except:
        pass

    return post


def read_visible_posts(driver, last_update: datetime):
    posts = []
    seen_urls = set()

    post_elements = driver.find_elements(By.CSS_SELECTOR, "div[role='feed'] > div")
    try:

        for post_element in reversed(post_elements):
            text = post_element.text
            if not text or "New posts" in text:
                continue
            scroll_into_element(driver, post_element)
            cooldown()
            post = read_post(driver, post_element)
            cooldown()
            if not post.url or post.url in seen_urls:
                continue

            if post.created_at and post.created_at <= last_update:
                continue

            seen_urls.add(post.url)
            posts.append(post)
    except:
        pass
    return posts


def highlight_element(driver, element, duration=5000):
    driver.execute_script(f"""
        arguments[0].style.border = '3px solid red';
        setTimeout(() => arguments[0].style.border = '', {duration});
    """, element)


def scroll_into_element(driver, post_element, offset=-100):
    driver.execute_script(f"arguments[0].scrollIntoView(true); window.scrollBy(0, {offset});", post_element)


def read_group_new_posts(driver, group_info: GroupModel):
    url = group_info.url
    last_update = group_info.last_visited
    max_update_time = datetime.now() - timedelta(hours=1)
    if not last_update or last_update < max_update_time:
        last_update = max_update_time
    driver.get(url)
    cooldown()
    scroll_till_last(driver, last_update)
    cooldown()
    posts = read_visible_posts(driver, last_update)
    return posts



def read_new_posts_from_all_groups(driver, facebook_groups):
    raw_posts = []
    for group_info in facebook_groups:
        try:
            current_time = datetime.now()
            group_posts = read_group_new_posts(driver=driver, group_info=group_info)
            raw_posts += group_posts
            config['groups'][group_info.idx]['last_visited'] = current_time.isoformat()
        except Exception as e:
            print(e)

    save_raw_posts(raw_posts=raw_posts)
    update_configs()


def update_configs():
    with open('../config.yaml', 'w') as f:
        yaml.dump(config, f, default_flow_style=False)


