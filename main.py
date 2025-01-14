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
from redis_storage import RedisStorage
import re

class AdvancedWebCrawler:
    def __init__(self, start_url, max_retries=3, delay=1, max_workers=5):
        self.start_url = start_url
        self.visited_pages = []
        self.max_retries = max_retries
        self.delay = delay
        self.max_workers = max_workers
        self.session = requests.Session()
        self._setup_logging()
        self.redis_storage = RedisStorage()
        self.tech_patterns = {
            'wordpress': r'wp-content|wp-includes',
            'react': r'react\.production\.min\.js',
            'angular': r'angular\.min\.js',
            'bootstrap': r'bootstrap\.min\.css',
            'jquery': r'jquery\.min\.js'
        }

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

    def check_url_health(self, url):
        """Synchronously check URL health"""
        try:
            response = requests.head(url, timeout=5)
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
                links = [link.get('href') for link in soup.find_all('a') if link.get('href')]
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
                    'timestamp': datetime.now().isoformat(),
                    # New information
                    'scripts': len(soup.find_all('script')),
                    'stylesheets': len(soup.find_all('link', rel='stylesheet')),
                    'forms': len(soup.find_all('form')),
                    'social_links': self._get_social_links(soup),
                    'responsive_meta': bool(soup.find('meta', {'name': 'viewport'})),
                    'h1_count': len(soup.find_all('h1')),
                    'text_to_html_ratio': self._calculate_text_ratio(soup),
                    'languages': [lang.get('lang', 'unknown') for lang in soup.find_all('html', lang=True)],
                    'seo_metrics': self._analyze_seo(soup, url),
                    'security_headers': self._check_security_headers(response.headers),
                    'performance_metrics': self._analyze_performance(soup, load_time),
                    'accessibility': self._check_accessibility(soup),
                    'technologies': self._detect_technologies(soup, response.text)
                }
                
                self.logger.info(f"Successfully processed {url}")
                time.sleep(self.delay)  # Respect robots.txt
                return page_info

            except Exception as e:
                self.logger.error(f"Attempt {attempt + 1} failed for {url}: {str(e)}")
                if attempt == self.max_retries - 1:
                    return None
                time.sleep(self.delay * (attempt + 1))  # Exponential backoff

    def _get_social_links(self, soup):
        """Extract social media links from the page"""
        social_patterns = {
            'facebook': r'facebook.com',
            'twitter': r'twitter.com|x.com',
            'linkedin': r'linkedin.com',
            'instagram': r'instagram.com',
            'youtube': r'youtube.com'
        }
        
        social_links = {}
        for link in soup.find_all('a', href=True):
            href = link['href']
            for platform, pattern in social_patterns.items():
                if re.search(pattern, href, re.I):
                    social_links[platform] = href
        return social_links

    def _calculate_text_ratio(self, soup):
        """Calculate the ratio of text content to HTML"""
        text_content = len(soup.get_text())
        html_content = len(str(soup))
        return round((text_content / html_content) * 100, 2) if html_content > 0 else 0

    def _analyze_seo(self, soup, url):
        """Analyze SEO elements"""
        return {
            'meta_description': bool(soup.find('meta', {'name': 'description'})),
            'canonical_url': bool(soup.find('link', {'rel': 'canonical'})),
            'robots_meta': bool(soup.find('meta', {'name': 'robots'})),
            'sitemap_links': bool(soup.find('a', href=re.compile(r'sitemap\.xml'))),
            'has_schema': bool(soup.find(attrs={"type": "application/ld+json"}))
        }

    def _check_security_headers(self, headers):
        """Analyze security headers"""
        security_headers = {
            'X-Content-Type-Options': headers.get('X-Content-Type-Options', 'Not Set'),
            'X-Frame-Options': headers.get('X-Frame-Options', 'Not Set'),
            'X-XSS-Protection': headers.get('X-XSS-Protection', 'Not Set'),
            'Content-Security-Policy': headers.get('Content-Security-Policy', 'Not Set'),
            'Strict-Transport-Security': headers.get('Strict-Transport-Security', 'Not Set')
        }
        return security_headers

    def _analyze_performance(self, soup, load_time):
        """Analyze performance metrics"""
        return {
            'total_load_time': load_time,
            'script_count': len(soup.find_all('script')),
            'css_count': len(soup.find_all('link', rel='stylesheet')),
            'image_size': sum(len(str(img)) for img in soup.find_all('img')),
            'total_links': len(soup.find_all('a')),
            'resource_hints': len(soup.find_all('link', rel=re.compile(r'preload|prefetch|preconnect')))
        }

    def _check_accessibility(self, soup):
        """Check basic accessibility features"""
        return {
            'images_with_alt': len([img for img in soup.find_all('img') if img.get('alt')]),
            'aria_landmarks': len(soup.find_all(attrs={"role": True})),
            'form_labels': len(soup.find_all('label')),
            'skip_links': bool(soup.find('a', href='#main-content')),
            'language_specified': bool(soup.find('html', lang=True))
        }

    def _detect_technologies(self, soup, response_text):
        """Detect technologies used on the website"""
        technologies = {}
        for tech, pattern in self.tech_patterns.items():
            if re.search(pattern, response_text, re.I):
                technologies[tech] = True
        
        # Additional framework detection
        if soup.find('meta', {'name': 'generator'}):
            technologies['cms'] = soup.find('meta', {'name': 'generator'})['content']
        
        return technologies

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
        self._check_all_urls_health()
        self.save_results()

    def _check_all_urls_health(self):
        """Check health of all visited URLs synchronously"""
        urls = [page['url'] for page in self.visited_pages]
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            health_results = list(executor.map(self.check_url_health, urls))
        
        # Add health check results to visited pages
        for page, health in zip(self.visited_pages, health_results):
            page['health_check'] = health

    def save_results(self):
        """Save detailed crawling results to Redis"""
        crawl_id = self.redis_storage.store_crawl_data(self.start_url, self.visited_pages)
        self.logger.info(f"Results saved to Redis with crawl ID: {crawl_id}")
        return crawl_id
