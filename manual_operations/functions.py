import pandas as pd
import yaml
import os
from models import ApartmentModel

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

with open(os.path.join(BASE_DIR, "config.yaml"), "r") as f:
    config = yaml.safe_load(f)


def generate_messages():
    message_text = config['message_text']
    filename = os.path.join(BASE_DIR, 'relevant_apartments.csv')
    df = pd.read_csv(filename)
    messages = [f"{message_text}\n{url}" for url in df["url"]]
    contacts = df['contact'].tolist()

    with open("messages.txt", "w") as f:
        spacer = "_" * 50 + '\n\n'
        for contact, message in zip(contacts, messages):
            f.write(f"{contact}\n\n{message}\n\n")
            f.write(spacer)

def manually_add_relevant_apartments():
    filename = os.path.join(BASE_DIR, 'relevant_apartments.csv')
    relevant_posts = []
    seen_urls = set()

    try:
        while True:
            print("-" * 50)
            apartment = ApartmentModel()
            apartment.location = input('Enter location: ')
            apartment.url = input('Enter URL: ')
            if not apartment.url:
                continue
            if apartment.url in seen_urls:
                print('URL already added')
                continue
            apartment.contact_number = input('Enter contact info: ')
            while True:
                price_input = input('Enter price: ').strip()
                try:
                    price = float(price_input)
                    break
                except ValueError:
                    print("Please enter a valid price. Only numbers are allowed.")
                    continue


            apartment.price = float(price_input)
            apartment.comments = input('Enter comment: ')
            relevant_posts.append(apartment)
            seen_urls.add(apartment.url)

    except (KeyboardInterrupt, EOFError):
        pass

    if not relevant_posts:
        print('\nNothing to save.')
        return

    new_df = pd.DataFrame([r.model_dump() for r in relevant_posts])  # fix

    if os.path.exists(filename):
        df = pd.read_csv(filename)
        df = pd.concat([df, new_df], ignore_index=True)  # fix
        df['_count'] = df.notna().sum(axis=1)
        df = (df.sort_values('_count', ascending=False)
                .drop_duplicates(subset='url', keep='first')
                .drop('_count', axis=1))
    else:
        df = new_df

    df.to_csv(filename, index=False)
    print('\nSaved!')


def ask_yes_no(question: str) -> bool:
    while True:
        answer = input(f"{question} (y/n): ").strip().lower()
        if answer in ('y', 'yes'): return True
        if answer in ('n', 'no'): return False
        print("Please enter y or n.")

def review_apartments():
    filename = os.path.join(BASE_DIR, 'relevant_apartments.csv')
    if not os.path.exists(filename):
        print("\nNothing to review.")
        return
    df = pd.read_csv(filename)
    to_remove = []

    for i, row in df.iterrows():
        row_dict = {k: (None if pd.isna(v) else v) for k, v in row.to_dict().items()}
        apartment = ApartmentModel(**row_dict)
        print(f"\n{'-'*50}")
        print(f"URL: {apartment.url}")
        if not ask_yes_no("Keep this apartment?"):
            to_remove.append(i)

    df.drop(to_remove, inplace=True)
    df.to_csv(filename, index=False)
    print(f"\nDone. Removed {len(to_remove)} apartments.")

