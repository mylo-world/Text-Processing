import requests
import json
import time
from datetime import datetime

class OpenLibraryHTTPScraper:
    def __init__(self):
        self.base_url = "https://openlibrary.org"
        self.search_url = f"{self.base_url}/search.json"
        self.headers = {
            "User-Agent": "OpenLibraryHTTPScraper/1.0 (Educational Purpose)"
        }
        self.session = requests.Session()
        self.session.headers.update(self.headers)

    def search_books(self, query, limit=5):
        """Search books by query keyword"""
        params = {"q": query, "limit": limit}
        response = self.session.get(self.search_url, params=params)
        if response.status_code == 200:
            data = response.json()
            results = []
            for doc in data.get("docs", []):
                results.append({
                    "title": doc.get("title", "Unknown"),
                    "author": doc.get("author_name", ["Unknown"])[0] if doc.get("author_name") else "Unknown",
                    "first_publish_year": doc.get("first_publish_year", "Unknown"),
                    "edition_count": doc.get("edition_count", 0),
                    "key": doc.get("key", ""),
                    "url": f"{self.base_url}{doc.get('key', '')}"
                })
            return results
        else:
            print(f"Error searching books: {response.status_code}")
            return []

    def get_book_details(self, olid):
        """Fetch details of a book by OLID (Open Library ID)"""
        url = f"{self.base_url}{olid}.json"
        response = self.session.get(url)
        if response.status_code == 200:
            data = response.json()
            return {
                "title": data.get("title", "Unknown"),
                "description": data.get("description", {}).get("value", "") if isinstance(data.get("description"), dict) else data.get("description", ""),
                "subjects": data.get("subjects", []),
                "created": data.get("created", {}).get("value", ""),
                "last_modified": data.get("last_modified", {}).get("value", ""),
                "scraped_at": datetime.now().isoformat()
            }
        else:
            print(f"Error get_book_details: {response.status_code}")
            return None

    def scrape_topic_comprehensive(self, query, num_books=5):
        print(f"Scraping topic: {query}")
        search_results = self.search_books(query, limit=num_books)
        if not search_results:
            print("No books found!")
            return []

        scraped_books = []
        for i, book in enumerate(search_results, 1):
            print(f"Scraping book {i}/{len(search_results)}: {book['title']}")
            details = self.get_book_details(book["key"])
            if details:
                book.update(details)
                scraped_books.append(book)
            time.sleep(1)  # biar ga keblok rate-limit
        return scraped_books

    def save_to_file(self, data, filename):
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        print(f"Data saved to {filename}")


def main():
    scraper = OpenLibraryHTTPScraper()
    topics = ["Data Science", "Machine Learning", "Artificial Intelligence"]

    all_scraped_data = {}
    for topic in topics:
        print("="*60)
        print(f"SCRAPING TOPIC: {topic}")
        print("="*60)
        books = scraper.scrape_topic_comprehensive(topic, num_books=3)
        all_scraped_data[topic] = books
        print(f"Completed {topic}: {len(books)} books scraped")
        time.sleep(2)

    scraper.save_to_file(all_scraped_data, "openlibrary_http_data.json")
    print("SCRAPING COMPLETED!")


if __name__ == "__main__":
    main()
