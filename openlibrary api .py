import requests
import json
import time
from datetime import datetime

class OpenLibraryAPI:
    def __init__(self):
        self.base_url = "https://openlibrary.org"
        self.headers = {
            'User-Agent': 'OpenLibraryScraper/1.0 (https://example.com/contact)'
        }

    def search_books(self, query, limit=5):
        url = f"{self.base_url}/search.json"
        params = {
            "q": query,
            "limit": limit
        }
        response = requests.get(url, params=params, headers=self.headers)
        if response.status_code == 200:
            return response.json().get("docs", [])
        else:
            print(f"Error search_books: {response.status_code}")
            return []

    def get_book_details(self, olid):
        url = f"{self.base_url}/works/{olid}.json"
        response = requests.get(url, headers=self.headers)
        if response.status_code == 200:
            return response.json()
        else:
            print(f"Error get_book_details: {response.status_code}")
            return None

    def scrape_topic(self, query, num_books=5):
        print(f"Searching for books about: {query}")
        search_results = self.search_books(query, num_books)

        if not search_results:
            print("No books found!")
            return []

        books_data = []
        for i, book in enumerate(search_results[:num_books], 1):
            title = book.get("title", "Unknown Title")
            olid = book.get("key", "").replace("/works/", "")
            print(f"\nProcessing book {i}/{num_books}: {title}")

            details = self.get_book_details(olid) if olid else {}

            book_data = {
                "title": title,
                "author": book.get("author_name", ["Unknown"])[0],
                "first_publish_year": book.get("first_publish_year", "Unknown"),           
                "edition_count": book.get("edition_count", 0),
                "key": olid,
                "url": f"{self.base_url}/works/{olid}" if olid else "",
                "scraped_at": datetime.now().isoformat()
            }

            books_data.append(book_data)
            time.sleep(1)

        return books_data

    def save_to_file(self, data, filename):
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        print(f"Data saved to {filename}") 


def main():
    ol_api = OpenLibraryAPI()

    topics = [
        "Python programming",
        "Artificial Intelligence",
        "Machine Learning",
        "Web Scraping",
        "Data Science"
    ]

    all_data = {}

    for topic in topics:
        print(f"\n{'='*50}")
        print(f"SCRAPING TOPIC: {topic}")
        print(f"{'='*50}")

        books = ol_api.scrape_topic(topic, num_books=3)
        all_data[topic] = books

        print(f"Completed scraping {len(books)} books for '{topic}'")
        time.sleep(2)

    ol_api.save_to_file(all_data, 'openlibrary_api_data.json')

    print(f"\n{'='*50}")
    print("SCRAPING SUMMARY")
    print(f"{'='*50}")

    total_books = sum(len(books) for books in all_data.values())
    print(f"Total topics scraped: {len(topics)}")
    print(f"Total books collected: {total_books}")
    print(f"Data saved to: openlibrary_api_data.json")

    if all_data:
        first_topic = list(all_data.keys())[0]
        first_book = all_data[first_topic][0]
        print(f"\nSample book data structure:")
        print(f"Title: {first_book['title']}")
        print(f"Author: {first_book['author']}")
        print(f"Year: {first_book['first_publish_year']}")


if __name__ == "__main__":
    main()
