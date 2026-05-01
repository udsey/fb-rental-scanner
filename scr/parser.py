import ast
from fileinput import filename

import yaml
from langchain_openai import ChatOpenAI
from models import LLMResponseModel, PostModel, ApartmentModel
from langchain_core.prompts import ChatPromptTemplate
from dotenv import load_dotenv
import os
import pandas as pd
from scr.models import LLMResponseModel
load_dotenv()

BASE_DIR = os.getenv("BASE_DIR")

system_prompt = """You are a real estate information extractor. Extract apartment/rental information from Vietnamese real estate posts.

Rules:
1. Extract ONLY information explicitly mentioned in the text
2. If price is mentioned in millions (e.g., "26 triệu"), convert to 26.0
4. If information is not found, use default values (None for Optional fields)
5. For location, keep original Vietnamese names, do NOT translate names
6. Always consider Vietnamese currency (VND) as default currency
7. Set allows_foreigners to true unless explicitly stated otherwise
8. For move_in_from: Look for phrases like "Move-in from", "Available from", "From", "Move-in date". If a date is mentioned (e.g., "May 5th", "05/05", "ngày 5/5"), always extract and convert to YYYY-MM-DD format. Never leave as "not specified" when dates are clearly present.
9. Return confidence_score based on how much information was found (0-1)

Post text to analyze:
{content}
"""
prompt = ChatPromptTemplate.from_messages([
    ("system", system_prompt),
    ("human", "{content}")
])

llm = ChatOpenAI(model="openai/gpt-oss-20b",
                 base_url="https://api.groq.com/openai/v1",
                 temperature=0.1
                 )

structured_llm = prompt | llm.with_structured_output(LLMResponseModel)

def extract_data(post) -> LLMResponseModel:
    return structured_llm.invoke({"content": post})


def extract_criteria():
    with open(os.path.join(BASE_DIR, 'config.yaml'), 'r') as f:
        config = yaml.safe_load(f)

    criteria = config.get('criteria', {})
    criteria = {k: v for k, v in criteria.items() if v is not None}


def get_apartments_table(df):
    apartments = []

    for idx, row in df.iterrows():
        llm_result = extract_data(row["text"])
        # Create ApartmentModel with row data + LLM results
        apt = ApartmentModel(
            author=row["author"],
            published_at=row["created_at"],
            url=row["url"],
            original_text=row["text"],
            # LLM extracted fields
            property_type=llm_result.property_type,
            location=llm_result.location,
            price=llm_result.price or 0.0,
            price_currency=llm_result.price_currency,
            electricity_rate=llm_result.electricity_rate,
            water_rate=llm_result.water_rate,
            service_fee=llm_result.service_fee,
            deposit_months=llm_result.deposit_months,
            move_in_from=llm_result.move_in_from,
            minimum_lease_months=llm_result.minimum_lease_months,
            allows_foreigners=llm_result.allows_foreigners,
            summary=llm_result.summary
        )
        apartments.append(apt.model_dump())

    apartments = pd.DataFrame(apartments)
    return apartments


def filter_apartments(df, criteria):
    # Start with all True mask
    mask = pd.Series([True] * len(df), index=df.index)

    # Apply each non-None criterion
    if criteria.get('price') is not None:
        mask &= df['price'] <= criteria['price']

    if criteria.get('allows_foreigners') is not None:
        mask &= df['allows_foreigners'] == criteria['allows_foreigners']

    if criteria.get('property_type') is not None:
        mask &= df['property_type'].str.contains(criteria['property_type'], case=False, na=False)

    if criteria.get('location') is not None:
        mask &= df['location'].str.contains(criteria['location'], case=False, na=False)

    if criteria.get('minimum_lease_months') is not None:
        mask &= df['minimum_lease_months'] <= criteria['minimum_lease_months']

    if criteria.get('deposit_months') is not None:
        mask &= df['deposit_months'] <= criteria['deposit_months']

    if criteria.get('price_currency') is not None:
        mask &= df['price_currency'] == criteria['price_currency']

    # Date filter (published after given date)
    if criteria.get('published_at') is not None:
        mask &= df['published_at'] >= criteria['published_at']

    return df[mask].copy()



def load_criteria():
    with open(os.path.join(BASE_DIR, "config.yaml"), "r") as f:
        config = yaml.safe_load(f)

    criteria = config.get('criteria', {})
    criteria = {k: v for k, v in criteria.items() if v is not None}
    return criteria


def select_relevant_apartments():
    criteria = load_criteria()
    apartments_list = []
    filename = os.path.join(BASE_DIR, 'data/relevant_apartments.csv')
    if os.path.isfile(filename):
        apartments_list.append(pd.read_csv(filename))

    dirname = os.path.join(BASE_DIR, 'data/raw_data')
    for filename in os.listdir(dirname):
        filepath = os.path.join(dirname, filename)
        df = pd.read_csv(filepath)
        apartments_list.append(df)
        os.remove(os.path.join(dirname, filename))

    apartments = pd.concat(apartments_list, ignore_index=True)
    apartments.dropna(subset=['url', 'text'], inplace=True)
    apartments.drop_duplicates(subset=['url'], keep='last', inplace=True)

    try:

        apartments = get_apartments_table(apartments)
        apartments = filter_apartments(apartments, criteria)
        apartments.sort_values(by=['price', 'published_at'], inplace=True)
        apartments.reset_index(drop=True, inplace=True)
        apartments['comments'] = apartments['comments'].apply(lambda x: ast.literal_eval(x))
        filename = os.path.join(BASE_DIR, 'data/relevant_apartments.csv')
        apartments.to_csv(filename, index=False)

    except Exception as e:
        print(e)
        apartments.to_csv(os.path.join(BASE_DIR, 'data/raw_data', 'unprocessed.csv'), index=False)
