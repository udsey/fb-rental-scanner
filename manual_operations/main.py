import os
from prompt_toolkit import prompt
import pandas as pd

if __name__ == '__main__':
    relevant_posts = []
    seen_urls = set()
    try:
        while True:
            print("-" * 50)
            location = prompt('Enter location: ')
            url = prompt('Enter URL: ')
            if not url:
                continue
            if url in seen_urls:
                print('URL already added')
                continue
            contact = prompt('Enter contact info: ')
            price = prompt('Enter price: ')
            comment = prompt('Enter comment: ')
            relevant_posts.append({
                'url': url,
                'price': price,
                'location': location,
                'comment': comment,
                'contact': contact
            })
            seen_urls.add(url)

    except (KeyboardInterrupt, EOFError):
        pass

    if not relevant_posts:
        print('\nNothing to save.')

    if os.path.exists('relevant_posts.csv'):
        df = pd.read_csv('relevant_posts.csv')
        df = pd.concat([df, pd.DataFrame(relevant_posts)], ignore_index=True)
        df.drop_duplicates(subset='url', keep='last', inplace=True)
        df.to_csv('relevant_posts.csv', index=False)
    else:
        df = pd.DataFrame(relevant_posts)
    df.to_csv('relevant_posts.csv', index=False)
    print('\nSaved relevant_posts.csv')




