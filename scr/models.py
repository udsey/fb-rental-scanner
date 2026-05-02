from datetime import datetime
from typing import Literal, Optional, List, Any
import math
from pydantic import BaseModel, Field, field_validator, model_validator
from selenium.webdriver.common.by import ByType


class FacebookGroupModel(BaseModel):
    idx: Optional[int] = None
    url: str
    last_visited: Optional[datetime] = None


class FacebookPostModel(BaseModel):
    author: str = ''
    text: str = ''
    created_at: Optional[datetime] = None
    url: str = ''
    raw_content: str = ''


class ApartmentModel(BaseModel):
    contact_number: Optional[str] = None
    location: Optional[str] = None
    price: Optional[float] = 0
    price_currency: Optional[str] = 'VND'
    url: Optional[str] = None
    comments: Optional[str] = None
    allows_foreigners: bool = True

    published_at: Optional[datetime] = None

    summary: Optional[str] = None

    move_in_from: Optional[str] = None
    minimum_lease_months: Optional[int] = None

    electricity_rate: Optional[float] = None
    water_rate: Optional[float] = None
    service_fee: Optional[float] = None
    deposit_months: Optional[int] = None
    property_type: Optional[str] = None
    original_text: Optional[str] = None

    @model_validator(mode="before")
    @classmethod
    def replace_nan_with_none(cls, data: Any) -> Any:
        if not isinstance(data, dict):
            return data
        return {
            k: None if (isinstance(v, float) and math.isnan(v)) else v
            for k, v in data.items()
        }
    
    @field_validator("price", "electricity_rate", "water_rate", "service_fee", mode="before")
    @classmethod
    def coerce_to_float(cls, v):
        if v is None:
            return v
        try:
            return float(v)
        except (ValueError, TypeError):
            return None

    def convert_nan_to_none(cls, value):
        if isinstance(value, float) and math.isnan(value):
            return None
        return value


class LLMResponseModel(BaseModel):
    property_type: Optional[str] = Field(default=None,
        description="Property type. Extract from keywords: 'studio'→'studio', '1BR/1-bedroom/1 bedroom'→'apartment', 'house/nhà'→'house', 'villa'→'villa'. If room count mentioned but no type, use 'apartment'.")

    location: Optional[str] = Field(default=None,
        description="Full address or area. Keep original Vietnamese names, do NOT translate. Include street, district if mentioned.")

    contact_number: Optional[str] = Field(default=None,
        description="Phone number in original format as written in the post.")

    price: Optional[float] = Field(default=None,
        description="Monthly rent in millions of VND. ALWAYS convert to millions: '13,500,000 VND'→13.5, '13.5 triệu'→13.5, '26M'→26.0. If USD+VND both given, use VND value. If price range given, use lowest.")

    price_currency: Optional[str] = Field(default="VND",
        description="Currency: 'VND' or 'USD'. Default VND unless price is USD-only.")

    electricity_rate: Optional[float] = Field(default=None,
        description="Electricity price in VND per kWh. E.g. '4,000đ/kWh'→4000.0.")

    water_rate: Optional[float] = Field(default=None,
        description="Water price in VND per cubic meter or per person per month.")

    service_fee: Optional[float] = Field(default=None,
        description="Monthly building service/maintenance fee in VND.")

    deposit_months: Optional[int] = Field(default=None,
        description="Number of months deposit required. E.g. 'deposit 2 months'→2.")

    move_in_from: Optional[str] = Field(default=None,
        description="Earliest move-in date in YYYY-MM-DD format. Look for: 'available from', 'from', 'ngày', 'từ ngày'. 'available now'/'free now' → use null. If no date mentioned → null.")

    minimum_lease_months: Optional[int] = Field(default=None,
        description="Minimum lease term in months. E.g. 'minimum 6 months'→6, '1 year minimum'→12.")

    allows_foreigners: Optional[bool] = Field(default=True,
        description="Whether foreigners are accepted. Default true unless explicitly stated otherwise (e.g. 'Vietnamese only', 'không cho người nước ngoài').")

    summary: Optional[str] = Field(default=None,
                                   description="2-3 sentence English summary covering property type, location, price, and key amenities. Only null if post does not contain apartment listing info.")

    confidence_score: Optional[float] = Field(default=None,
        description="How much real listing info was found (0-1). >0.7: clear listing with price+location. 0.3-0.7: partial info. <0.3: spam, comments, or no real listing data.",
        ge=0, le=1)
    

    @model_validator(mode="before")
    @classmethod
    def replace_null_with_defaults(cls, data: Any) -> Any:
        if not isinstance(data, dict):
            return data

        # Map field name → default to use when null is received
        null_safe_defaults = {
            "allows_foreigners": True,
            "move_in_from": "not specified",
            "price_currency": "VND",
        }

        for field, default in null_safe_defaults.items():
            if data.get(field) is None:
                data[field] = default

        return data

class LocationModel(BaseModel):
    pass


class CriteriaModel(BaseModel):
    min_price: Optional[float] = 0.0
    max_price: Optional[float] = float("inf")

    allows_foreigners: Optional[bool] = None
    property_type: Optional[str] = None

    location: Optional[LocationModel] = None
    minimum_lease_months: Optional[int] = None


class UserConfigModel(BaseModel):
    facebook_groups: List[FacebookGroupModel]
    message_template: str
    criteria: CriteriaModel


class LLMConfigModel(BaseModel):
    model_type: Literal["local", "groq"] = "groq"
    temperature: Optional[float] = 0.0
    model_name: Optional[str] = "meta-llama/llama-4-scout-17b-16e-instruct"
    extract_data_prompt: Optional[str] = "Extract data"


class LocatorModel(BaseModel):
    by: ByType  # "id", "xpath", "link text", "partial link text", "name", "tag name", "class name", "css selector"
    value: str

    def as_tuple(self):
        return (self.by, self.value)


class ScraperConfigModel(BaseModel):
    cooldown_min: Optional[int] = 2
    cooldown_max: Optional[int] = 3
    wait_timeout: Optional[int] = 1000
    cycle_limit: Optional[int] = 300
    scroll_y: Optional[int] = 5000
    max_timedelta_mins: Optional[int] = 60

    facebook_url: Optional[str] = "https://facebook.com"

    # Find elements by values
    username_input: Optional[LocatorModel] = LocatorModel(
        by='name',
        value='email'
    )
    password_input: Optional[LocatorModel] = LocatorModel(
        by='name', 
        value="pass"
    )
    login_button: Optional[LocatorModel] = LocatorModel(
        by="css selector", 
        value="div[role='button'][aria-label='Log in']"
    )
    search_facebook: Optional[LocatorModel] = LocatorModel(
        by="css selector",
        value="input[placeholder='Search Facebook']"
    )
    shared_with: Optional[LocatorModel] = LocatorModel(
        by='css selector',
        value="[title*='Shared with']"
    )
    panel: Optional[LocatorModel] = LocatorModel(
        by="xpath",
        value="../../../.."
    )
    share: Optional[LocatorModel] = LocatorModel(
        by="xpath",
        value="./*"
    )
    created_at: Optional[LocatorModel] = LocatorModel(
        by="css selector",
        value="[role='tooltip']"
    )
    feed: Optional[LocatorModel] = LocatorModel(
        by="css selector",
        value="div[role='feed'] > div"
    )
    post_container: Optional[LocatorModel] = LocatorModel(
        by="xpath",
        value="../../../../../../.."
    )
    see_more: Optional[LocatorModel] = LocatorModel(
        by="xpath",
        value=".//*[contains(text(), 'See more')]"
    )
    post_url: Optional[LocatorModel] = LocatorModel(
        by="css selector",
        value="a[href*='/posts/']"
    )

    


class SystemConfigModel(BaseModel):
    llm_config: LLMConfigModel
    scraper_config: ScraperConfigModel


class ConfigModel(BaseModel):
    user_config: UserConfigModel
    system_config: Optional[SystemConfigModel]