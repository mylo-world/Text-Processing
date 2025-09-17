import requests
from bs4 import BeautifulSoup
import json
import time
import os
from urllib.parse import urljoin, urlparse
import re
from datetime import datetime

class NASAImageScraper:
    def __init__(self, output_dir="nasa_images"):
        self.base_url = "https://www.nasa.gov"
        self.archive_url = "https://www.nasa.gov/image-of-the-day/?page={}"
        self.output_dir = output_dir
        self.session = requests.Session()
        self.session.headers.update({'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'})
        
        os.makedirs(self.output_dir, exist_ok=True)
        os.makedirs(f"{self.output_dir}/images", exist_ok=True)
    
    def sanitize_filename(self, filename):
        return re.sub(r'[<>:"/\\|?*]', '', filename).strip()
    
    def download_image(self, img_url, title, index):
        try:
            response = self.session.get(img_url, timeout=30)
            response.raise_for_status()
            
            parsed_url = urlparse(img_url)
            ext = os.path.splitext(parsed_url.path)[1] or '.jpg'

            safe_title = self.sanitize_filename(title)[:50]  
            filename = f"{index:03d}_{safe_title}{ext}"
            filepath = os.path.join(self.output_dir, "images", filename)

            with open(filepath, 'wb') as f:
                f.write(response.content)
            
            print(f"Downloaded: {filename}")
            return filename
            
        except Exception as e:
            print(f"Error downloading image {img_url}: {e}")
            return None
    
    def scrape_article_data(self, article_url):
        try:
            response = self.session.get(article_url, timeout=30)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')
            
            title = None
            for selector in ['h1', '.entry-title', '.article-title', 'h1.wp-block-heading']:
                title_elem = soup.find(selector)
                if title_elem:
                    title = title_elem.get_text().strip()
                    break

            date = None
            for selector in ['.date', '.entry-date', 'time', '.published']:
                date_elem = soup.find(selector)
                if date_elem:
                    date = date_elem.get_text().strip()
                    break

            description = None
            for selector in ['.description', '.entry-content p', '.article-content p', '.wp-block-paragraph']:
                desc_elem = soup.find(selector)
                if desc_elem:
                    description = desc_elem.get_text().strip()
                    break

            img_url = None
            for selector in ['.image img', '.entry-content img', '.article-image img', 'img']:
                img_elem = soup.find(selector)
                if img_elem and img_elem.get('src'):
                    img_src = img_elem['src']
                    img_url = urljoin(self.base_url, img_src)
                    if any(skip in img_src.lower() for skip in ['thumb', 'icon', 'logo', 'avatar']):
                        continue
                    break

            metadata = {
                'scraped_at': datetime.now().isoformat(),
                'article_url': article_url,
                'title': title or 'No title found',
                'date': date or 'No date found',
                'description': description or 'No description found',
                'image_url': img_url,
            }

            content_elem = soup.find('div', class_='entry-content') or soup.find('div', class_='article-content')
            if content_elem:
                paragraphs = content_elem.find_all('p')
                full_content = '\n'.join([p.get_text().strip() for p in paragraphs if p.get_text().strip()])
                metadata['full_content'] = full_content[:1000]  
            
            return metadata
            
        except Exception as e:
            print(f"Error scraping article {article_url}: {e}")
            return None
    
    def is_moon_related(self, text):
        if not text:
            return False
        
        text_lower = text.lower()
        moon_keywords = [
            'moon', 'lunar', 'artemis', 'apollo', 'crater', 'mare', 'moonrise', 
            'moonset', 'full moon', 'new moon', 'crescent', 'gibbous',
            'lunar eclipse', 'lunar mission', 'lunar surface', 'lunar rover',
            'selenian', 'lunar orbit', 'lunar landing', 'moonlight',
            'lunar phase', 'lunar cycle', 'earth moon', 'moon earth'
        ]
        
        return any(keyword in text_lower for keyword in moon_keywords)

    def scrape_archive_pages(self, num_pages=10):
        data_list = []
        moon_articles_found = 0
        total_articles_checked = 0
        
        for page_num in range(1, num_pages + 1):
            print(f"Scraping page {page_num}...")
            url = self.archive_url.format(page_num)
            
            try:
                response = self.session.get(url, timeout=30)
                response.raise_for_status()
                soup = BeautifulSoup(response.content, 'html.parser')

                article_links = []
                for selector in ['a.article-link', '.entry-title a', '.post-title a', 'h2 a', 'h3 a']:
                    links = soup.find_all('a', href=True)
                    for link in links:
                        if '/image-of-the-day/' in link.get('href', ''):
                            article_links.append(link)
                    if article_links:
                        break
                
                print(f"Found {len(article_links)} articles on page {page_num}")
                
                for i, link in enumerate(article_links):
                    total_articles_checked += 1
                    article_url = urljoin(self.base_url, link['href'])
    
                    link_text = link.get_text().strip()
                    if not self.is_moon_related(link_text):
                        article_data = self.scrape_article_data(article_url)
                        if not article_data or not (
                            self.is_moon_related(article_data.get('title', '')) or 
                            self.is_moon_related(article_data.get('description', '')) or
                            self.is_moon_related(article_data.get('full_content', ''))
                        ):
                            print(f"Skipping non-moon article: {link_text[:50]}...")
                            continue
                    else:
                        article_data = self.scrape_article_data(article_url)
                    
                    if article_data:
                        moon_articles_found += 1
                        print(f"🌙 Found moon-related article #{moon_articles_found}: {article_data['title'][:50]}...")

                        if article_data['image_url']:
                            filename = self.download_image(
                                article_data['image_url'], 
                                article_data['title'], 
                                moon_articles_found
                            )
                            article_data['local_image_filename'] = filename

                        title_score = 1 if self.is_moon_related(article_data.get('title', '')) else 0
                        desc_score = 1 if self.is_moon_related(article_data.get('description', '')) else 0
                        content_score = 1 if self.is_moon_related(article_data.get('full_content', '')) else 0
                        article_data['moon_relevance_score'] = title_score + desc_score + content_score
                        
                        data_list.append(article_data)

                        if len(data_list) % 3 == 0:
                            self.save_data(data_list, f"moon_articles_progress_{len(data_list)}.json")

                    time.sleep(2)
                
            except Exception as e:
                print(f"Error scraping page {page_num}: {e}")
                continue
            
            time.sleep(3)
        
        print(f"\n⋆˖⁺‧₊☽Moon filtering summary☾₊‧⁺˖⋆")
        print(f"- ⋆Total articles checked: {total_articles_checked}")
        print(f"- ⋆Moon-related articles found: {moon_articles_found}")
        print(f"- ⋆Filter efficiency: {(moon_articles_found/total_articles_checked*100):.1f}%")
        
        return data_list
    
    def save_data(self, data_list, filename="moon_articles_archive.json"):
        filepath = os.path.join(self.output_dir, filename)
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data_list, f, indent=4, ensure_ascii=False)
        print(f"Saved {len(data_list)} moon-related items to {filepath}")
    
    def create_summary_report(self, data_list):
        report = {
            'total_articles': len(data_list),
            'successful_downloads': len([item for item in data_list if item.get('local_image_filename')]),
            'date_range': {
                'earliest': min([item['date'] for item in data_list if item['date'] != 'No date found'], default='N/A'),
                'latest': max([item['date'] for item in data_list if item['date'] != 'No date found'], default='N/A')
            },
            'scraped_at': datetime.now().isoformat()
        }
        
        report_path = os.path.join(self.output_dir, 'scraping_report.json')
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=4)
        
        print(f"\n⋆✴︎˚Scraping summary｡⋆:")
        print(f"⋆Total articles: {report['total_articles']}")
        print(f"⋆Successful downloads: {report['successful_downloads']}")
        print(f"⋆Date range: {report['date_range']['earliest']} to {report['date_range']['latest']}")
    
    def run_full_scrape(self, num_pages=10):
        print(f"Starting NASA Image of the Day scraper...")
        print(f"Will scrape {num_pages} pages")
        
        start_time = datetime.now()
        
        data_list = self.scrape_archive_pages(num_pages)
        
        if data_list:
            self.save_data(data_list)
            self.create_summary_report(data_list)
        
        end_time = datetime.now()
        print(f"\nScraping completed in {end_time - start_time}")
        
        return data_list

def analyze_scraped_data(json_file="nasa_images/nasa_iotd_archive.json"):
    try:
        with open(json_file, 'r') as f:
            data = json.load(f)
        
        print(f"Analysis of {len(data)} articles:")
        
        years = {}
        for item in data:
            if item.get('date') and item['date'] != 'No date found':
                try:
                    year_match = re.search(r'\b(20\d{2})\b', item['date'])
                    if year_match:
                        year = year_match.group(1)
                        years[year] = years.get(year, 0) + 1
                except:
                    pass
        
        if years:
            print("Articles by year:")
            for year in sorted(years.keys()):
                print(f"  {year}: {years[year]} articles")

        downloaded = len([item for item in data if item.get('local_image_filename')])
        print(f"Successfully downloaded images: {downloaded}/{len(data)}")
        
    except Exception as e:
        print(f"Error analyzing data: {e}")

if __name__ == "__main__":
    scraper = NASAImageScraper()

    data = scraper.run_full_scrape(num_pages=5)  
    
    analyze_scraped_data()
    
    print("\n☽Files created☾:")
    print("⋆nasa_images/nasa_iotd_archive.json (main data)")
    print("⋆nasa_images/images/ (downloaded images)")
    print("⋆nasa_images/scraping_report.json (summary report)")