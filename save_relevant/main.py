from prompt_toolkit import prompt
import csv

if __name__ == '__main__':
    relevant_posts = []
    seen_urls = set()
    try:
        while True:
            print("-" * 100)
            url = prompt('Enter URL: ')
            if not url:
                continue
            if url in seen_urls:
                print('URL already added')
                continue

            price = prompt('Enter price: ')
            location = prompt('Enter location: ')
            comment = prompt('Enter comment: ')
            relevant_posts.append({
                'url': url,
                'price': price,
                'location': location,
                'comment': comment
            })
            seen_urls.add(url)

    except (KeyboardInterrupt, EOFError):
        pass

    if relevant_posts:
        with open('relevant_posts.csv', 'a', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=['url', 'price', 'location'])
            if f.tell() == 0:
                writer.writeheader()  # only write header if file is empty
            writer.writerows(relevant_posts)
        print(f'\nSaved {len(relevant_posts)} entries.')
    else:
        print('\nNothing to save.')





