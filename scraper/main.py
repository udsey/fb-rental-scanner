"""Scrape data from Facebook Groups."""
from scraper.functions import configure_chrome, login, read_group, save_raw_posts
from scraper.setup import FACEBOOK_PASSWORD, FACEBOOK_USERNAME, facebook_groups

if __name__ == "__main__":

    driver, wait = configure_chrome()
    login(driver=driver,
          wait=wait,
          username=FACEBOOK_USERNAME,
          password=FACEBOOK_PASSWORD)

    raw_posts = []

    for group_info in facebook_groups:
        group_posts = read_group(driver=driver,
                                 group_info=group_info)
        raw_posts.append(group_posts)
    save_raw_posts(raw_posts=raw_posts)

    driver.close()







