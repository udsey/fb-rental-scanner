from datetime import datetime
from typing import Optional, List

from pydantic import BaseModel, Field


class GroupModel(BaseModel):
    idx: int
    url: str
    last_visited: Optional[datetime] = None


class PostModel(BaseModel):
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

    author: Optional[str] = None

    summary: Optional[str] = None

    move_in_from: Optional[str] = None
    minimum_lease_months: Optional[int] = None



    electricity_rate: Optional[float] = None
    water_rate: Optional[float] = None
    service_fee: Optional[float] = None
    deposit_months: Optional[int] = None
    property_type: Optional[str] = None
    original_text: Optional[str] = None




class LLMResponseModel(BaseModel):
    property_type: Optional[str] = Field(default = None,
                                         description="Type: 'apartment', 'house', 'villa', etc.")
    location: Optional[str] = Field(default=None,
                                    description="Information about apartment location")
    contact_number: Optional[str] = Field(default=None,
                                          description="Contact number.")
    # Price
    price: Optional[float] = Field(default=0.0,
                                   description="Monthly rent price in millions (e.g., 26.0 = 26,000,000 VND)")
    price_currency: str = Field(default="VND",
                                description="Currency of price. (e.g. USD, VND, etc)")
    electricity_rate: Optional[float] = Field(default=None,
                                              description="Electricity price in VND/kWh")
    water_rate: Optional[float] = Field(default=None,
                                        description="Water price in VND/cubic meter or per person")
    service_fee: Optional[float] = Field(default=None,
                                         description="Monthly service/maintenance fee in VND")
    deposit_months: Optional[int] = Field(default=None,
                                          description="Number of months deposit required")
    # Availability
    move_in_from: str = Field(default="not specified",
                              description="Earliest move-in date...")
    minimum_lease_months: Optional[int] = Field(default=None,
                                                description="Minimum lease term in months")
    allows_foreigners: bool = Field(default=True,
                                    description="If apartment allows foreigners. If not mentioned set to true")

    summary: Optional[str] = Field(default=None,
                                    description="Quick English summary of the apartment/rental post (2-3 sentences covering key features: property type, location, price, and standout amenities)")
    confidence_score: Optional[float] = Field(default=None,
                                              description="Confidence score of extraction (0-1)",
                                              ge=0,
                                              le=1)


