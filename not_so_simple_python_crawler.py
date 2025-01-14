import requests
from bs4 import BeautifulSoup
import time
import json
import logging
from concurrent.futures import ThreadPoolExecutor
from urllib.parse import urljoin, urlparse
import asyncio
from collections import Counter
from datetime import datetime

class AdvancedWebCrawler:
    def __init__(self, start_url, max_retries=3, delay=1, max_workers=5):
        self.start_url = start_url
        self.visited_pages = []
        self.max_retries = max_retries
        self.delay = delay
        self.max_workers = max_workers
        self.session = requests.Session()
        self._setup_logging()

    def _setup_logging(self):
        """Configure logging for the crawler"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            filename='crawler.log'
        )
        self.logger = logging.getLogger(__name__)

    def _get_meta_tags(self, soup):
        """Extract meta tags from the page"""
        meta_tags = {}
        for tag in soup.find_all('meta'):
            name = tag.get('name') or tag.get('property')
            content = tag.get('content')
            if name and content:
                meta_tags[name] = content
        return meta_tags

    def _count_words(self, soup):
        """Count words in the page content"""
        text = soup.get_text()
        words = text.lower().split()
        return len(words), Counter(words)

    def _categorize_links(self, base_url, links):
        """Separate internal and external links"""
        internal_links = set()
        external_links = set()
        base_domain = urlparse(base_url).netloc

        for link in links:
            try:
                absolute_url = urljoin(base_url, link)
                if urlparse(absolute_url).netloc == base_domain:
                    internal_links.add(absolute_url)
                else:
                    external_links.add(absolute_url)
            except Exception:
                continue

        return list(internal_links), list(external_links)

    async def check_url_health(self, url):
        """Asynchronously check URL health"""
        try:
            response = await asyncio.get_event_loop().run_in_executor(
                None, 
                lambda: requests.head(url, timeout=5)
            )
            return {
                'url': url,
                'status': response.status_code,
                'response_time': response.elapsed.total_seconds()
            }
        except Exception as e:
            return {
                'url': url,
                'status': 'error',
                'error': str(e)
            }

    def get_page_info(self, url):
        """Get detailed information about a webpage with retry logic"""
        for attempt in range(self.max_retries):
            try:
                start_time = time.time()
                response = self.session.get(url, timeout=10)
                load_time = time.time() - start_time

                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Extract all links
                links = [link.get('href') for link in soup.find_all('a') if link.get('href')] # <a>
                internal_links, external_links = self._categorize_links(url, links)
                
                # Count words
                word_count, word_freq = self._count_words(soup)
                
                # Get meta tags
                meta_tags = self._get_meta_tags(soup)
                
                page_info = {
                    'url': url,
                    'title': soup.title.string if soup.title else "No title",
                    'status_code': response.status_code,
                    'load_time': round(load_time, 2),
                    'content_length': len(response.content),
                    'internal_links': internal_links,
                    'external_links': external_links,
                    'images_found': len(soup.find_all('img')),
                    'word_count': word_count,
                    'top_words': dict(word_freq.most_common(10)),
                    'meta_tags': meta_tags,
                    'headers': dict(response.headers),
                    'timestamp': datetime.now().isoformat()
                }
                
                self.logger.info(f"Successfully processed {url}")
                time.sleep(self.delay)  # Respect robots.txt
                return page_info

            except Exception as e:
                self.logger.error(f"Attempt {attempt + 1} failed for {url}: {str(e)}")
                if attempt == self.max_retries - 1:
                    return None
                time.sleep(self.delay * (attempt + 1))  # Exponential backoff

    def crawl(self, max_pages=5):
        """Crawl websites using ThreadPoolExecutor"""
        self.logger.info(f"Starting crawl from: {self.start_url}")
        
        urls_to_visit = [self.start_url]
        visited = set()
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            while urls_to_visit and len(visited) < max_pages:
                future_to_url = {
                    executor.submit(self.get_page_info, url): url 
                    for url in urls_to_visit[:max_pages - len(visited)]
                    if url not in visited
                }
                
                urls_to_visit = urls_to_visit[max_pages - len(visited):]
                
                for future in future_to_url:
                    url = future_to_url[future]
                    try:
                        page_info = future.result()
                        if page_info:
                            self.visited_pages.append(page_info)
                            visited.add(url)
                            
                            # Add new internal links to visit
                            urls_to_visit.extend([
                                link for link in page_info['internal_links']
                                if link not in visited
                            ])
                    except Exception as e:
                        self.logger.error(f"Error processing {url}: {str(e)}")

        # Perform health check on all visited URLs
        asyncio.run(self._check_all_urls_health())
        self.save_results()

    async def _check_all_urls_health(self):
        """Check health of all visited URLs"""
        urls = [page['url'] for page in self.visited_pages]
        tasks = [self.check_url_health(url) for url in urls]
        health_results = await asyncio.gather(*tasks)
        
        # Add health check results to visited pages
        for page, health in zip(self.visited_pages, health_results):
            page['health_check'] = health

    def save_results(self):
        """Save detailed crawling results to a JSON file"""
        results = {
            'summary': {
                'pages_visited': len(self.visited_pages),
                'start_url': self.start_url,
                'crawl_time': datetime.now().isoformat(),
                'total_words': sum(page['word_count'] for page in self.visited_pages),
                'total_images': sum(page['images_found'] for page in self.visited_pages),
            },
            'page_data': self.visited_pages
        }
        
        filename = f'crawler_results_{int(time.time())}.json'
        with open(filename, 'w') as f:
            json.dump(results, f, indent=4)
        
        self.logger.info(f"Results saved to {filename}")
        return filename

def process_url(url):
    try:
        print(f"\nCrawling: {url}")
        crawler = AdvancedWebCrawler(
            url,
            max_retries=3,
            delay=1,
            max_workers=5
        )
        crawler.crawl(max_pages=5)
    except Exception as e:
        print(f"Error crawling {url}: {str(e)}")

def main():
    # Read URLs from file
    try:
        with open('urls.txt', 'r') as f:
            urls = [url.strip() for url in f.readlines() if url.strip()]
    except FileNotFoundError:
        print("Error: urls.txt not found")
        return
    except Exception as e:
        print(f"Error reading file: {str(e)}")
        return

    if not urls:
        print("No URLs found in file")
        return

    # Process URLs concurrently using ThreadPoolExecutor
    with ThreadPoolExecutor(max_workers=3) as executor:
        executor.map(process_url, urls)

if __name__ == "__main__":
    main()