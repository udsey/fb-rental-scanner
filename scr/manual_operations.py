from datetime import datetime
import os
import pandas as pd
import logging
from scr.models import ApartmentModel
from scr.setup import DATA_DIR, config

logger = logging.getLogger(__name__)



def generate_messages():
    """Shaping messages for relevant apartments."""
    message_text = config.user_config.message_template
    df_filepath = os.path.join(DATA_DIR, 'relevant_apartments.csv')
    if not os.path.isfile(df_filepath):
        return
    df = pd.read_csv(df_filepath, dtype=str)
    n_relevant = df.shape[0]
    if n_relevant == 0:
        return
    
    messages = [f"{message_text}\n{url}" for url in df["url"]]
    contacts = df['contact_number'].tolist()
    filepath = os.path.join(DATA_DIR, f'messages_{datetime.now().strftime("%Y%m%d_%H%M%S")}.txt')
    with open(filepath, "w") as f:
        spacer = "_" * 50 + '\n\n'
        for contact, message in zip(contacts, messages):
            f.write(f"{contact}\n\n{message}\n\n")
            f.write(spacer)

    os.remove(df_filepath)
    logger.info(f"Done! Messages for short-listed apartments saved in {filepath}")


def manually_add_relevant_apartments():
    filepath = os.path.join(DATA_DIR, 'relevant_apartments.csv')
    relevant_posts = []
    seen_urls = set()

    try:
        while True:
            logger.info("-" * 50)
            apartment = ApartmentModel()
            apartment.location = input('Enter location: ')
            apartment.url = input('Enter URL: ')
            if not apartment.url:
                continue
            if apartment.url in seen_urls:
                logger.info('URL already added')
                continue
            apartment.contact_number = input('Enter contact info: ')
            while True:
                price_input = input('Enter price: ').strip()
                if price_input == '':
                    price_input = 0
                try:
                    price = float(price_input)
                    break
                except ValueError:
                    logger.info("Please enter a valid price. Only numbers are allowed.")
                    continue


            apartment.price = float(price_input)
            apartment.comments = input('Enter comment: ')
            relevant_posts.append(apartment)
            seen_urls.add(apartment.url)

    except (KeyboardInterrupt, EOFError):
        pass

    if not relevant_posts:
        logger.info('Nothing to save.')
        return

    new_df = pd.DataFrame([r.model_dump() for r in relevant_posts])

    if os.path.exists(filepath):
        df = pd.read_csv(filepath)
        df = pd.concat([df, new_df], ignore_index=True)
        df['_count'] = df.notna().sum(axis=1)
        df = (df.sort_values('_count', ascending=False)
                .drop_duplicates(subset='url', keep='first')
                .drop('_count', axis=1))
    else:
        df = new_df

    df.to_csv(filepath, index=False)
    logger.info('Saved!')


def ask_yes_no(question: str) -> bool:
    while True:
        answer = input(f"{question} (y/n): ").strip().lower()
        if answer in ('y', 'yes'): return True
        if answer in ('n', 'no'): return False
        logger.info("Please enter y or n.")


def review_apartments():
    filepath = os.path.join(DATA_DIR, 'relevant_apartments.csv')
    if not os.path.exists(filepath):
        logger.info("Nothing to review.")
        return
    df = pd.read_csv(filepath, dtype=str)
    to_remove = []

    for i, row in df.iterrows():
        row_dict = {k: (None if pd.isna(v) else v) for k, v in row.to_dict().items()}
        apartment = ApartmentModel(**row_dict)
        logger.info(f"\n{'-'*50}")
        logger.info(f"URL: {apartment.url}")
        if not ask_yes_no("Keep this apartment?"):
            to_remove.append(i)

    df.drop(to_remove, inplace=True)
    df.to_csv(filepath, index=False)
    logger.info(f"\nDone. Removed {len(to_remove)} apartments.")

