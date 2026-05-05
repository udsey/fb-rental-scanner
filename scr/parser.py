import os
import sys
import time
from typing import List, Optional
from send2trash import send2trash

from langchain_groq import ChatGroq
from langchain_ollama import ChatOllama
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.language_models import BaseChatModel
from langchain_core.runnables import Runnable
from dotenv import load_dotenv
import pandas as pd
from pydantic import BaseModel
import logging
from tqdm import tqdm

from scr.models import CriteriaModel, LLMResponseModel, ApartmentModel, LocationModel
from scr.setup import DATA_DIR, RAW_DATA_DIR, config

logger = logging.getLogger(__name__)


def get_llm() -> BaseChatModel:
    """Get llm with params."""
    model_type = config.system_config.llm_config.model_type

    logger.info(f"Loading {model_type} LLM: {config.system_config.llm_config.model_name}")

    if model_type == "groq":
        return ChatGroq(
            model=config.system_config.llm_config.model_name, 
            temperature=config.system_config.llm_config.temperature
        )
    
    elif model_type == "local":
        return ChatOllama(
            model=config.system_config.llm_config.model_name,
            temperature=config.system_config.llm_config.temperature
        )
    
    else:
        logger.error(f"Unknown model type: '{model_type}'. Expected 'groq' or 'local'.")
        raise


def get_structured_llm(prompt_text: str, output_model: BaseModel) -> Runnable:
    """Return structured llm."""
    llm = get_llm()
    prompt = ChatPromptTemplate.from_messages([
    ("system", prompt_text),
    ("human", "{content}")
    ])

    structured_llm = prompt | llm.with_structured_output(output_model)

    return structured_llm


structured_llm = get_structured_llm(prompt_text=config.system_config.llm_config.extract_data_prompt, 
                                    output_model=LLMResponseModel)


def extract_data(text: str) -> LLMResponseModel:
    """Extrac data from raw text."""
    return structured_llm.invoke({"content": text})


def get_apartments_table(df: pd.DataFrame) -> List[pd.DataFrame]:
    """Get enriched apartment table with data extracted."""

    apartments = []
    unprocessed = []

    for idx, row in tqdm(df.iterrows(), 
                         total=len(df), 
                         desc="Extracting apartments",
                         file=sys.stdout):
        try:
            llm_result = extract_data(row["raw_content"])
            apt = ApartmentModel(
                    **llm_result.model_dump(),
                    url=row["url"],
                    published_at=row["created_at"],
                    original_text=row["raw_content"],
                )
            apartments.append(apt.model_dump())
        except Exception as e:
            logger.error(f"Failed to process row {idx}: {e}")
            unprocessed.append(row)
        if config.system_config.llm_config.model_type != "local":
            time.sleep(1)

    if len(unprocessed) != 0:
        logger.info(f"Processed {len(apartments)} apartments successfully, {len(unprocessed)} failed.")
    apartments = pd.DataFrame(apartments)
    unprocessed = pd.DataFrame(unprocessed)
    return apartments, unprocessed


def check_location(col: pd.Series, location_criteria: LocationModel) -> pd.Series:
    # TODO: implement location filtering
    logger.warning("Location filtering not implemented yet, skipping.")
    return pd.Series([True] * len(col), index=col.index)


def filter_apartments(df: pd.DataFrame, criteria: CriteriaModel):
    """Filter apartments with user criteria."""

    mask = pd.Series([True] * len(df), index=df.index)

    if criteria.min_price is not None:
        mask &= df["price"] >= criteria.min_price

    if criteria.max_price is not None and criteria.max_price != float("inf"):
        mask &= df["price"] <= criteria.max_price

    if criteria.allows_foreigners is not None:
        mask &= df['allows_foreigners'] == criteria.allows_foreigners

    if criteria.property_type is not None:
        mask &= df['property_type'].str.contains(criteria.property_type, case=False, na=False)

    if criteria.location is not None:
        mask &= check_location(df['location'], criteria.location)
        
    if criteria.minimum_lease_months is not None:
        mask &= df['minimum_lease_months'] <= criteria.minimum_lease_months

    return df[mask].copy()


def preprocess_df(df: pd.DataFrame, filepath: str = None) -> Optional[pd.DataFrame]:
    """Preprocess df and save is filepath provided."""
    try:
        df = df.copy()
        df_cols = set(df.columns.to_list())

        filter_cols = df_cols & {'url', 'original_text', 'raw_content'}
        df.drop_duplicates(subset=list(filter_cols), keep='last', inplace=True)

        filter_cols = df_cols & {'price', 'published_at'}
        df.sort_values(by=list(filter_cols), inplace=True)

        df.reset_index(drop=True, inplace=True)
        if filepath and not df.empty:
            df.to_csv(
                os.path.join(filepath), 
                index=False)
        return df
    except Exception as e:
        logger.exception(f"Failed to preprocess df: {e}")
        return None


def load_df(filepath: str) -> Optional[pd.DataFrame]:
    """Try load df, if empry return None."""
    if os.path.isfile(filepath):
        try:
            df = pd.read_csv(filepath, dtype=str)
            if not df.empty:
                return df
        except pd.errors.EmptyDataError:
            pass
    return None



def select_relevant_apartments() -> None:
    """Parse raw apartments data and select relevant."""

    apartments_list = []
    unsorted_list = []

    filepath = os.path.join(DATA_DIR, 'relevant_apartments.csv')
    df = load_df(filepath)
    if df is not None:
        apartments_list.append(df)

    filepath = os.path.join(DATA_DIR, 'unsorted_apartments.csv')
    unsorted = load_df(filepath)

    filepath = os.path.join(DATA_DIR, 'relevant_apartments.csv')
    previous_relevant = load_df(filepath)

    for filename in os.listdir(RAW_DATA_DIR):
        filepath = os.path.join(RAW_DATA_DIR, filename)
        df = load_df(filepath)
        if df is not None:
            apartments_list.append(df)
            send2trash(os.path.join(RAW_DATA_DIR, filename))

    if len(apartments_list) == 0:
        logger.info('No apartments available for selection.')
        return

    apartments = pd.concat(apartments_list, ignore_index=True)
    apartments = preprocess_df(apartments)
    if apartments is None:
        logger.info('No apartments available for selection.')
        return
    try:
        logger.info(f"Found {len(apartments)} rows to process.")
        unsorted_apartments, unprocessed = get_apartments_table(apartments)
        criteria = config.user_config.criteria
        apartments = filter_apartments(unsorted_apartments, criteria)
        logger.info(f"Filtered down to {len(apartments)} relevant apartments.")

        if previous_relevant is not None:
            apartments = pd.concat([previous_relevant, apartments])
        preprocess_df(
            df=apartments,
            filepath=os.path.join(DATA_DIR, 'relevant_apartments.csv'))
        
        preprocess_df(
            df=unprocessed,
            filepath=os.path.join(RAW_DATA_DIR, 'unprocessed.csv'))

        if unsorted is not None:
            unsorted_apartments = pd.concat([unsorted, unsorted_apartments])

        preprocess_df(
                df=unsorted_apartments,
                filepath=os.path.join(DATA_DIR, 'unsorted_apartments.csv'))
            
        logger.info(f"Saved results to {DATA_DIR}")
        logger.info('Done!')

    except Exception as e:
        logger.exception(f"Pipeline failed: {e}")
        unprocessed = pd.concat([unprocessed, apartments])
        preprocess_df(
            df=unprocessed,
            filepath=os.path.join(RAW_DATA_DIR, 'unprocessed.csv'))
