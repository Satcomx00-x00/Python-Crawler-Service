# simple_python_crawler.py
import requests
from bs4 import BeautifulSoup
import time
import json

class SimpleWebCrawler:
    def __init__(self, start_url):
        self.start_url = start_url
        self.visited_pages = []
        
    def get_page_info(self, url):
        """Get basic information about a webpage"""
        try:
            # Make a request to the page
            response = requests.get(url)
            
            # Parse the HTML content
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Get all links from the page
            links = []
            for link in soup.find_all('a'):
                href = link.get('href')
                if href:
                    links.append(href)
            
            # Count images
            image_count = len(soup.find_all('img'))
            
            # Get page title
            title = soup.title.string if soup.title else "No title"
            
            # Store page information
            page_info = {
                'url': url,
                'title': title,
                'status_code': response.status_code,
                'links_found': len(links),
                'images_found': image_count
            }
            
            return page_info
            
        except Exception as e:
            print(f"Error processing {url}: {str(e)}")
            return None
    
    def crawl(self, max_pages=5):
        """Crawl websites starting from the initial URL"""
        print(f"Starting to crawl from: {self.start_url}")
        print(f"Will visit up to {max_pages} pages")
        
        pages_visited = 0
        
        try:
            # Visit the start URL
            page_info = self.get_page_info(self.start_url)
            if page_info:
                self.visited_pages.append(page_info)
                pages_visited += 1
                print(f"Visited page {pages_visited}: {self.start_url}")
                
            # Try to find and visit more pages
            soup = BeautifulSoup(requests.get(self.start_url).text, 'html.parser')
            
            # Find all links on the page
            for link in soup.find_all('a'):
                if pages_visited >= max_pages:
                    break
                    
                href = link.get('href')
                if href and href.startswith('http'):
                    page_info = self.get_page_info(href)
                    if page_info:
                        self.visited_pages.append(page_info)
                        pages_visited += 1
                        print(f"Visited page {pages_visited}: {href}")
                        
                        # Add a small delay to be nice to the servers
                        time.sleep(1)
        
        except Exception as e:
            print(f"An error occurred while crawling: {str(e)}")
        
        # Save results to a file
        self.save_results()
        
    def save_results(self):
        """Save the crawling results to a JSON file"""
        results = {
            'pages_visited': len(self.visited_pages),
            'start_url': self.start_url,
            'page_data': self.visited_pages
        }
        
        with open('crawler_results.json', 'w') as f:
            json.dump(results, f, indent=2)
        
        print("\nCrawling completed!")
        print(f"Visited {len(self.visited_pages)} pages")
        print("Results saved to crawler_results.json")

# Example usage
def main():
    # Create a crawler starting from a website
    crawler = SimpleWebCrawler('https://example.com')
    
    # Start crawling - will visit up to 5 pages
    crawler.crawl(max_pages=5)

if __name__ == "__main__":
    main()