import requests
from bs4 import BeautifulSoup
import json
import time
import re
from datetime import datetime
from urllib.parse import urljoin, quote

class WikipediaHTTPScraper:
    def __init__(self):
        self.base_url = "https://en.wikipedia.org"
        self.search_url = "https://en.wikipedia.org/w/index.php"
        self.headers = {
            'User-Agent': 'WikipediaHTTPScraper/1.0 (Educational Purpose)'
        }
        self.session = requests.Session()
        self.session.headers.update(self.headers)
    
    def search_articles(self, query, limit=10):
        params = {
            'search': query,
            'title': 'Special:Search',
            'profile': 'advanced',
            'fulltext': '1',
            'ns0': '1'
        }
        
        response = self.session.get(self.search_url, params=params)
        soup = BeautifulSoup(response.content, 'html.parser')
        
        results = []
        
        search_results = soup.find_all('div', class_='mw-search-result-heading')
        
        for i, result in enumerate(search_results[:limit]):
            link_elem = result.find('a')
            if link_elem:
                title = link_elem.get('title', '')
                href = link_elem.get('href', '')

                result_data = result.find_parent('div', class_='mw-search-result')
                snippet_elem = result_data.find('div', class_='searchresult') if result_data else None
                snippet = snippet_elem.get_text().strip() if snippet_elem else ''
                
                results.append({
                    'title': title,
                    'url': urljoin(self.base_url, href),
                    'snippet': snippet
                })
        
        return results
    
    def scrape_page_content(self, url):
        try:
            response = self.session.get(url)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')

            title_elem = soup.find('h1', id='firstHeading')
            title = title_elem.get_text().strip() if title_elem else ''

            content_div = soup.find('div', id='mw-content-text')

            intro_paragraphs = content_div.find_all('p')[:3] if content_div else []
            introduction = ' '.join([p.get_text().strip() for p in intro_paragraphs if p.get_text().strip()])
 
            sections = []
            if content_div:
                section_headers = content_div.find_all(['h2', 'h3', 'h4'], class_='mw-headline')
                for header in section_headers:
                    sections.append({
                        'level': header.parent.name,
                        'title': header.get_text().strip(),
                        'id': header.get('id', '')
                    })

            infobox = {}
            infobox_elem = soup.find('table', class_='infobox')
            if infobox_elem:
                rows = infobox_elem.find_all('tr')
                for row in rows:
                    header = row.find('th')
                    data = row.find('td')
                    if header and data:
                        key = header.get_text().strip()
                        value = data.get_text().strip()
                        infobox[key] = value

            images = []
            img_tags = soup.find_all('img', src=True)
            for img in img_tags:
                src = img.get('src')
                alt = img.get('alt', '')
                if src and src.startswith('//'):
                    src = 'https:' + src
                if 'upload.wikimedia.org' in src:
                    images.append({
                        'src': src,
                        'alt': alt,
                        'width': img.get('width', ''),
                        'height': img.get('height', '')
                    })

            references_section = soup.find('div', class_='reflist')
            ref_count = 0
            if references_section:
                ref_links = references_section.find_all('a')
                ref_count = len(ref_links)

            categories = []
            cat_links = soup.find_all('a', href=re.compile(r'/wiki/Category:'))
            for cat_link in cat_links:
                cat_name = cat_link.get_text().strip()
                if cat_name:
                    categories.append(cat_name)

            main_content = content_div.get_text() if content_div else ''
            word_count = len(main_content.split())
            
            return {
                'title': title,
                'url': url,
                'introduction': introduction,
                'sections': sections,
                'infobox': infobox,
                'images': images[:10],  
                'references_count': ref_count,
                'categories': categories[:10],  
                'word_count': word_count,
                'scraped_at': datetime.now().isoformat()
            }
            
        except requests.RequestException as e:
            print(f"Error scraping {url}: {e}")
            return None
    
    def get_random_articles(self, count=5):
        articles = []
        
        for i in range(count):
            random_url = "https://en.wikipedia.org/wiki/Special:Random"
            response = self.session.get(random_url, allow_redirects=True)
            
            if response.status_code == 200:
                article_data = self.scrape_page_content(response.url)
                if article_data:
                    articles.append(article_data)
                    print(f"Scraped random article {i+1}/{count}: {article_data['title']}")
            
            time.sleep(1)
        
        return articles
    
    def scrape_topic_comprehensive(self, query, num_articles=5):
        print(f"Scraping topic: {query}")

        search_results = self.search_articles(query, num_articles)
        
        if not search_results:
            print("No search results found!")
            return []
        
        scraped_articles = []
        
        for i, result in enumerate(search_results, 1):
            print(f"Scraping article {i}/{len(search_results)}: {result['title']}")

            article_data = self.scrape_page_content(result['url'])
            
            if article_data:
                article_data['search_snippet'] = result['snippet']
                article_data['search_rank'] = i
                scraped_articles.append(article_data)

            time.sleep(2)
        
        return scraped_articles
    
    def save_to_file(self, data, filename):
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        print(f"Data saved to {filename}")
    
    def generate_report(self, data):
        total_articles = sum(len(articles) for articles in data.values())
        total_words = sum(
            sum(article['word_count'] for article in articles)
            for articles in data.values()
        )
        
        report = {
            'scraping_summary': {
                'total_topics': len(data),
                'total_articles': total_articles,
                'total_words': total_words,
                'scraping_date': datetime.now().isoformat()
            },
            'topic_breakdown': {}
        }
        
        for topic, articles in data.items():
            topic_word_count = sum(article['word_count'] for article in articles)
            avg_sections = sum(len(article['sections']) for article in articles) / len(articles) if articles else 0
            
            report['topic_breakdown'][topic] = {
                'articles_count': len(articles),
                'total_words': topic_word_count,
                'average_sections': round(avg_sections, 2),
                'top_articles': [article['title'] for article in articles[:3]]
            }
        
        return report

def main():
    scraper = WikipediaHTTPScraper()

    topics = [
        "Climate Change",
        "Quantum Computing", 
        "Renewable Energy",
        "Space Exploration",
        "Biotechnology"
    ]
    
    all_scraped_data = {}

    for topic in topics:
        print(f"\n{'='*60}")
        print(f"SCRAPING TOPIC: {topic}")
        print(f"{'='*60}")
        
        articles = scraper.scrape_topic_comprehensive(topic, num_articles=3)
        all_scraped_data[topic] = articles
        
        print(f"Completed {topic}: {len(articles)} articles scraped")

        time.sleep(3)

    print(f"\n{'='*60}")
    print("SCRAPING RANDOM ARTICLES")
    print(f"{'='*60}")
    
    random_articles = scraper.get_random_articles(5)
    all_scraped_data['Random Articles'] = random_articles

    scraper.save_to_file(all_scraped_data, 'wikipedia_http_data.json')

    report = scraper.generate_report(all_scraped_data)
    scraper.save_to_file(report, 'wikipedia_scraping_report.json')

    print(f"\n{'='*60}")
    print("SCRAPING COMPLETED!")
    print(f"{'='*60}")
    print(f"Topics scraped: {len(topics) + 1}")
    print(f"Total articles: {report['scraping_summary']['total_articles']}")
    print(f"Total words: {report['scraping_summary']['total_words']:,}")
    print(f"Main data: wikipedia_http_data.json")
    print(f"Report: wikipedia_scraping_report.json")

    if all_scraped_data:
        first_topic = list(all_scraped_data.keys())[0]
        if all_scraped_data[first_topic]:
            sample_article = all_scraped_data[first_topic][0]
            print(f"\nSample article: {sample_article['title']}")
            print(f"Word count: {sample_article['word_count']}")
            print(f"Sections: {len(sample_article['sections'])}")
            print(f"Images: {len(sample_article['images'])}")
            print(f"Categories: {len(sample_article['categories'])}")

if __name__ == "__main__":
    main()