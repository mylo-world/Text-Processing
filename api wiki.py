import requests
import json
import time
from datetime import datetime

class WikipediaAPI:
    def __init__(self):
        self.base_url = "https://en.wikipedia.org/api/rest_v1"
        self.wiki_api_url = "https://en.wikipedia.org/w/api.php"
        self.headers = {
            'User-Agent': 'WikipediaAPIScraper/1.0 (https://example.com/contact)'
        }
    
    def search_articles(self, query, limit=10):
        params = {
            'action': 'query',
            'format': 'json',
            'list': 'search',
            'srsearch': query,
            'srlimit': limit
        }
        
        response = requests.get(self.wiki_api_url, params=params, headers=self.headers)
        data = response.json()
        
        if 'query' in data and 'search' in data['query']:
            return data['query']['search']
        return []
    
    def get_page_content(self, title):
        clean_title = title.replace(' ', '_')
        url = f"{self.base_url}/page/summary/{clean_title}"
        
        try:
            response = requests.get(url, headers=self.headers)
            if response.status_code == 200:
                return response.json()
            else:
                print(f"Error getting {title}: {response.status_code}")
                return None
        except Exception as e:
            print(f"Exception getting {title}: {e}")
            return None
    
    def get_page_sections(self, title):
        params = {
            'action': 'parse',
            'format': 'json',
            'page': title,
            'prop': 'sections'
        }
        
        response = requests.get(self.wiki_api_url, params=params, headers=self.headers)
        data = response.json()
        
        if 'parse' in data and 'sections' in data['parse']:
            return data['parse']['sections']
        return []
    
    def get_page_images(self, title):
        params = {
            'action': 'query',
            'format': 'json',
            'titles': title,
            'prop': 'images',
            'imlimit': 10
        }
        
        response = requests.get(self.wiki_api_url, params=params, headers=self.headers)
        data = response.json()
        
        images = []
        if 'query' in data and 'pages' in data['query']:
            for page_id, page_data in data['query']['pages'].items():
                if 'images' in page_data:
                    images.extend([img['title'] for img in page_data['images']])
        
        return images
    
    def scrape_topic(self, query, num_articles=5):
        print(f"Searching for articles about: {query}")

        search_results = self.search_articles(query, num_articles)
        
        if not search_results:
            print("No articles found!")
            return []
        
        articles_data = []
        
        for i, result in enumerate(search_results[:num_articles], 1):
            title = result['title']
            print(f"\nProcessing article {i}/{num_articles}: {title}")

            content = self.get_page_content(title)
 
            sections = self.get_page_sections(title)

            images = self.get_page_images(title)
            
            article_data = {
                'title': title,
                'search_snippet': result.get('snippet', ''),
                'word_count': result.get('wordcount', 0),
                'timestamp': result.get('timestamp', ''),
                'summary': content.get('extract', '') if content else '',
                'description': content.get('description', '') if content else '',
                'url': f"https://en.wikipedia.org/wiki/{title.replace(' ', '_')}",
                'sections': [section['line'] for section in sections],
                'images_count': len(images),
                'scraped_at': datetime.now().isoformat()
            }
            
            articles_data.append(article_data)
            
            time.sleep(1)
        
        return articles_data
    
    def save_to_file(self, data, filename):
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        print(f"Data saved to {filename}")

def main():
    wiki_api = WikipediaAPI()

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

        articles = wiki_api.scrape_topic(topic, num_articles=3)
        all_data[topic] = articles
        
        print(f"Completed scraping {len(articles)} articles for '{topic}'")

        time.sleep(2)

    wiki_api.save_to_file(all_data, 'wikipedia_api_data.json')

    print(f"\n{'='*50}")
    print("SCRAPING SUMMARY")
    print(f"{'='*50}")
    
    total_articles = sum(len(articles) for articles in all_data.values())
    print(f"Total topics scraped: {len(topics)}")
    print(f"Total articles collected: {total_articles}")
    print(f"Data saved to: wikipedia_api_data.json")
    
    if all_data:
        first_topic = list(all_data.keys())[0]
        first_article = all_data[first_topic][0]
        print(f"\nSample article data structure:")
        print(f"Title: {first_article['title']}")
        print(f"Summary length: {len(first_article['summary'])} characters")
        print(f"Sections: {len(first_article['sections'])}")
        print(f"Images: {first_article['images_count']}")

if __name__ == "__main__":
    main()