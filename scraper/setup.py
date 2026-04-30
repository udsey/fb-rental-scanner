"""Configurable settings."""
import yaml
from dotenv import load_dotenv
import os

from scraper.models import GroupModel

root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


load_dotenv()

FACEBOOK_USERNAME = os.getenv("FACEBOOK_USERNAME")
FACEBOOK_PASSWORD = os.getenv("FACEBOOK_PASSWORD")

with open(os.path.join(root, "config.yaml"), "r") as f:
    config = yaml.safe_load(f)

facebook_groups = [GroupModel(**g) for g in config['groups']]