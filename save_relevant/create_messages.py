import pandas as pd
import yaml
import os


with open(os.path.join("../config.yaml"), "r") as f:
    config = yaml.safe_load(f)

message_text = config['message_text']
df = pd.read_csv('relevant_posts.csv')


messages = [f"{message_text}\n{url}" for url in df["url"]]
contacts = df['contact'].tolist()

with open("messages.txt", "w") as f:
    spacer = "_" * 50 + '\n\n'
    for contact, message in zip(contacts, messages):
        f.write(f"{contact}\n\n{message}\n\n")
        f.write(spacer)



