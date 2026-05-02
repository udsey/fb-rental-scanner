import os
from pydantic import BaseModel
import yaml
from dotenv import load_dotenv
from scr.models import ConfigModel, SystemConfigModel, UserConfigModel
import logging


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
    handlers=[
        logging.StreamHandler(),                          # console
    ]
)
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("WDM").setLevel(logging.WARNING)


def load_config_file(filename: str) -> dict:
    """Load config fime from name."""
    with open(os.path.join(BASE_DIR, filename), "r") as f:
        config = yaml.safe_load(f)
    return config


def save_config(config: BaseModel, filename: str):
    """Save config file."""
    with open(os.path.join(BASE_DIR, filename), 'w') as f:
        yaml.dump(config.model_dump(), f, default_flow_style=False)


def load_config() -> ConfigModel:
    """Load configurations."""
    user_config = load_config_file("user_config.yaml")
    user_config = UserConfigModel(**user_config)

    system_config = load_config_file("system_config.yaml")
    system_config = SystemConfigModel(**system_config)

    config = ConfigModel(
        user_config=user_config,
        system_config=system_config
    )

    return config


load_dotenv()

FACEBOOK_USERNAME = os.getenv("FACEBOOK_USERNAME")
FACEBOOK_PASSWORD = os.getenv("FACEBOOK_PASSWORD")
BASE_DIR = os.getcwd()
DATA_DIR = os.path.join(BASE_DIR, 'data')
RAW_DATA_DIR = os.path.join(DATA_DIR, 'raw_data')


config = load_config()

save_config(config.user_config, "user_config.yaml")
save_config(config.system_config, "system_config.yaml")