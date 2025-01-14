import redis
import json
from datetime import datetime
import os
from dotenv import load_dotenv
from redis.sentinel import Sentinel
from redis.exceptions import ConnectionError

class RedisStorage:
    def __init__(self):
        load_dotenv()
        self.redis_client = self._get_redis_connection()

    def _get_redis_connection(self):
        """Get Redis connection with retry and fallback logic"""
        redis_hosts = [
            {'host': 'redis-master', 'port': 6379},  
            {'host': 'redis-slave', 'port': 6379}
        ]
        password = os.getenv('REDIS_PASSWORD', 'redispassword')

        for redis_config in redis_hosts:
            try:
                client = redis.Redis(
                    host=redis_config['host'],
                    port=redis_config['port'],
                    password=password,
                    db=int(os.getenv('REDIS_DB', 0)),
                    decode_responses=True,
                    socket_timeout=1,
                    retry_on_timeout=True,
                    health_check_interval=5
                )
                # Test connection
                client.ping()
                print(f"Connected to Redis at {redis_config['host']}:{redis_config['port']}")
                return client
            except (ConnectionError, redis.exceptions.TimeoutError):
                continue

        raise ConnectionError("Could not connect to any Redis instance")
        
    def _ensure_connection(self):
        """Ensure Redis connection is alive, reconnect if needed"""
        try:
            self.redis_client.ping()
        except (ConnectionError, redis.exceptions.TimeoutError):
            self.redis_client = self._get_redis_connection()
            
    def store_crawl_data(self, start_url, visited_pages):
        """Store crawling results in Redis with connection check"""
        self._ensure_connection()
        
        timestamp = int(datetime.now().timestamp())
        crawl_id = f"crawl:{start_url}:{timestamp}"
        
        if not visited_pages or not isinstance(visited_pages, list):
            return None

        # Use pipeline for atomic operations
        with self.redis_client.pipeline() as pipe:
            try:
                # Store summary
                summary = {
                    'pages_visited': len(visited_pages),
                    'start_url': start_url,
                    'crawl_time': datetime.now().isoformat(),
                    'total_words': sum(page.get('word_count', 0) for page in visited_pages),
                    'total_images': sum(page.get('images_found', 0) for page in visited_pages),
                }
                
                pipe.hset(f"{crawl_id}:summary", mapping=summary)
                
                # Store each page data
                for index, page in enumerate(visited_pages):
                    if not isinstance(page, dict):
                        continue
                    
                    page_key = f"{crawl_id}:page:{index}"
                    page_data = {
                        'url': page.get('url', ''),
                        'title': page.get('title', 'No title'),
                        'status_code': str(page.get('status_code', 0)),
                        'load_time': str(page.get('load_time', 0)),
                        'content_length': str(page.get('content_length', 0)),
                        'internal_links': json.dumps(page.get('internal_links', [])),
                        'external_links': json.dumps(page.get('external_links', [])),
                        'images_found': str(page.get('images_found', 0)),
                        'word_count': str(page.get('word_count', 0)),
                        'top_words': json.dumps(page.get('top_words', {})),
                        'meta_tags': json.dumps(page.get('meta_tags', {})),
                        'headers': json.dumps(page.get('headers', {})),
                        'timestamp': page.get('timestamp', datetime.now().isoformat()),
                        'health_check': json.dumps(page.get('health_check', {})),
                        'seo_metrics': json.dumps(page.get('seo_metrics', {})),
                        'social_links': json.dumps(page.get('social_links', {})),
                        'performance_metrics': json.dumps(page.get('performance_metrics', {})),
                        'accessibility': json.dumps(page.get('accessibility', {})),
                        'technologies': json.dumps(page.get('technologies', {}))
                    }
                    
                    pipe.hset(page_key, mapping=page_data)
                    pipe.rpush(f"{crawl_id}:pages", page_key)
                
                pipe.rpush("all_crawls", crawl_id)
                pipe.execute()
                
                return crawl_id
            except (ConnectionError, redis.exceptions.TimeoutError):
                self.redis_client = self._get_redis_connection()
                raise
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
            for field in ['internal_links', 'external_links', 'top_words', 'meta_tags', 
                         'headers', 'health_check', 'seo_metrics', 'social_links', 
                         'performance_metrics', 'accessibility', 'technologies', 'security_headers']:
                try:
                    page_data[field] = json.loads(page_data.get(field, '{}'))
                except (json.JSONDecodeError, TypeError):
                    page_data[field] = {}
            
            # Convert numeric fields
            for field in ['status_code', 'load_time', 'content_length', 'images_found', 
                         'word_count', 'scripts', 'stylesheets', 'forms', 'h1_count']:
                try:
                    page_data[field] = int(page_data.get(field, 0))
                except (ValueError, TypeError):
                    page_data[field] = 0
            
            # Convert float fields
            page_data['text_to_html_ratio'] = float(page_data.get('text_to_html_ratio', 0))
            
            # Convert boolean fields
            page_data['responsive_meta'] = page_data.get('responsive_meta', 'False') == 'True'
            
            # Convert list fields
            try:
                page_data['languages'] = json.loads(page_data.get('languages', '[]'))
            except (json.JSONDecodeError, TypeError):
                page_data['languages'] = []
            
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
