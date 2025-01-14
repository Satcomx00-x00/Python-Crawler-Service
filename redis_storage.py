import redis
import json
from datetime import datetime
import os
from dotenv import load_dotenv

class RedisStorage:
    def __init__(self):
        load_dotenv()
        self.redis_client = redis.Redis(
            host=os.getenv('REDIS_HOST', 'localhost'),
            port=int(os.getenv('REDIS_PORT', 6379)),
            password=os.getenv('REDIS_PASSWORD', ''),
            db=int(os.getenv('REDIS_DB', 0)),
            decode_responses=True
        )

    def store_crawl_data(self, start_url, visited_pages):
        """Store crawling results in Redis"""
        timestamp = int(datetime.now().timestamp())
        crawl_id = f"crawl:{start_url}:{timestamp}"
        
        # Store summary
        summary = {
            'pages_visited': len(visited_pages),
            'start_url': start_url,
            'crawl_time': datetime.now().isoformat(),
            'total_words': sum(page['word_count'] for page in visited_pages),
            'total_images': sum(page['images_found'] for page in visited_pages),
        }
        
        # Store summary in Redis
        self.redis_client.hset(f"{crawl_id}:summary", mapping=summary)
        
        # Store each page data
        for index, page in enumerate(visited_pages):
            page_key = f"{crawl_id}:page:{index}"
            
            # Convert complex data types to strings
            page_data = {
                'url': page['url'],
                'title': page['title'],
                'status_code': str(page['status_code']),
                'load_time': str(page['load_time']),
                'content_length': str(page['content_length']),
                'internal_links': json.dumps(page['internal_links']),
                'external_links': json.dumps(page['external_links']),
                'images_found': str(page['images_found']),
                'word_count': str(page['word_count']),
                'top_words': json.dumps(page['top_words']),
                'meta_tags': json.dumps(page['meta_tags']),
                'headers': json.dumps(page['headers']),
                'timestamp': page['timestamp'],
                'health_check': json.dumps(page['health_check']),
                'seo_metrics': json.dumps(page.get('seo_metrics', {})),
                'social_links': json.dumps(page.get('social_links', {})),
                'performance_metrics': json.dumps(page.get('performance_metrics', {})),
                'accessibility': json.dumps(page.get('accessibility', {})),
                'technologies': json.dumps(page.get('technologies', {}))
            }
            
            # Store page data in Redis
            self.redis_client.hset(page_key, mapping=page_data)
            
            # Add to the list of pages for this crawl
            self.redis_client.rpush(f"{crawl_id}:pages", page_key)
        
        # Store crawl ID in the list of all crawls
        self.redis_client.rpush("all_crawls", crawl_id)
        
        return crawl_id

    def get_crawl_data(self, crawl_id):
        """Retrieve crawling results from Redis"""
        if not self.redis_client.exists(f"{crawl_id}:summary"):
            return None
        
        # Get summary
        summary = self.redis_client.hgetall(f"{crawl_id}:summary")
        
        # Get all pages
        pages = []
        page_keys = self.redis_client.lrange(f"{crawl_id}:pages", 0, -1)
        
        for page_key in page_keys:
            page_data = self.redis_client.hgetall(page_key)
            
            # Convert stored strings back to original data types
            page_data['internal_links'] = json.loads(page_data.get('internal_links', '[]'))
            page_data['external_links'] = json.loads(page_data.get('external_links', '[]'))
            page_data['top_words'] = json.loads(page_data.get('top_words', '{}'))
            page_data['meta_tags'] = json.loads(page_data.get('meta_tags', '{}'))
            page_data['headers'] = json.loads(page_data.get('headers', '{}'))
            page_data['health_check'] = json.loads(page_data.get('health_check', '{}'))
            page_data['seo_metrics'] = json.loads(page_data.get('seo_metrics', '{}'))
            page_data['social_links'] = json.loads(page_data.get('social_links', '{}'))
            page_data['performance_metrics'] = json.loads(page_data.get('performance_metrics', '{}'))
            page_data['accessibility'] = json.loads(page_data.get('accessibility', '{}'))
            page_data['technologies'] = json.loads(page_data.get('technologies', '{}'))
            page_data['security_headers'] = json.loads(page_data.get('security_headers', '{}'))
            
            # Ensure all required fields exist with default values
            page_data.setdefault('url', '')
            page_data.setdefault('title', 'No title')
            page_data.setdefault('status_code', 0)
            page_data.setdefault('load_time', 0)
            page_data.setdefault('content_length', 0)
            page_data.setdefault('images_found', 0)
            page_data.setdefault('word_count', 0)
            page_data.setdefault('scripts', 0)
            page_data.setdefault('stylesheets', 0)
            page_data.setdefault('forms', 0)
            page_data.setdefault('responsive_meta', False)
            page_data.setdefault('h1_count', 0)
            page_data.setdefault('text_to_html_ratio', 0)
            page_data.setdefault('languages', [])
            
            pages.append(page_data)
        
        return {
            'summary': summary,
            'page_data': pages
        }

    def delete_crawl_data(self, crawl_id):
        """Delete crawl data from Redis"""
        # Remove all pages
        page_keys = self.redis_client.lrange(f"{crawl_id}:pages", 0, -1)
        for page_key in page_keys:
            self.redis_client.delete(page_key)
        
        # Remove pages list
        self.redis_client.delete(f"{crawl_id}:pages")
        
        # Remove summary
        self.redis_client.delete(f"{crawl_id}:summary")
        
        # Remove from all_crawls list
        self.redis_client.lrem("all_crawls", 0, crawl_id)
