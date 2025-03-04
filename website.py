# website.py
from flask import Flask, render_template, request, redirect, url_for
import re
from main import AdvancedWebCrawler
from redis_storage import RedisStorage
from urllib.parse import quote, unquote
from redis.exceptions import ConnectionError

app = Flask(__name__)
redis_storage = None

def init_redis():
    try:
        return RedisStorage()
    except ConnectionError as e:
        print(f"Failed to connect to Redis: {e}")
        print("Make sure Redis is running and accessible")
        return None

@app.before_request
def check_redis():
    global redis_storage
    if redis_storage is None:
        redis_storage = init_redis()
    if redis_storage is None:
        return "Redis connection is not available", 503

URL_PATTERN = re.compile(
    r'^https?://'
    r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'
    r'localhost|'
    r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'
    r'(?::\d+)?'
    r'(?:/?|[/?]\S+)$', re.IGNORECASE)

def validate_url(url):
    return bool(URL_PATTERN.match(url))

@app.route('/', methods=['GET'])
def index():
    return render_template('index.html')

@app.route('/crawl', methods=['POST'])
def crawl():
    url = request.form.get('url', '').strip()
    force_refresh = request.form.get('force_refresh') == 'true'
    
    if not url or not validate_url(url):
        return render_template('index.html', error="Invalid URL format")
    
    try:
        max_pages = int(request.form.get('max_pages', 5))
        max_retries = int(request.form.get('max_retries', 2))
        max_workers = int(request.form.get('max_workers', 3))
        delay = int(request.form.get('delay', 1))
        
        # Check for existing recent crawl if not forcing refresh
        if not force_refresh:
            normalized_url = url.rstrip('/')
            existing_crawls = redis_storage.redis_client.lrange("all_crawls", 0, -1)
            for crawl_id in existing_crawls:
                if normalized_url in crawl_id:
                    data = redis_storage.get_crawl_data(crawl_id)
                    if data and data['page_data']:
                        return render_template('results.html', results=data['page_data'][0])
        
        # Continue with new crawl if no existing data or force refresh
        crawler = AdvancedWebCrawler(url, 
                                   max_retries=max_retries, 
                                   delay=delay, 
                                   max_workers=max_workers)
        crawler.crawl(max_pages=max_pages)
        
        if not crawler.visited_pages or not isinstance(crawler.visited_pages, list):
            return render_template('index.html', error="No data could be retrieved from the URL")
        
        # Store results in Redis
        crawl_id = crawler.save_results()
        
        # Get the stored data back from Redis to ensure consistent format
        data = redis_storage.get_crawl_data(crawl_id)
        if not data or not data['page_data']:
            return render_template('index.html', error="Error storing crawl results")
            
        return render_template('results.html', results=data['page_data'][0])
    except Exception as e:
        return render_template('index.html', error=f"Error crawling URL: {str(e)}")

@app.route('/history')
def history():
    crawl_ids = redis_storage.redis_client.lrange("all_crawls", 0, -1)
    crawls = []
    for crawl_id in crawl_ids:
        summary = redis_storage.redis_client.hgetall(f"{crawl_id}:summary")
        if summary:
            crawls.append({
                'id': quote(crawl_id, safe=''),  # URL-safe encoding
                'url': summary['start_url'],
                'time': summary['crawl_time'],
                'pages': summary['pages_visited']
            })
    return render_template('history.html', crawls=crawls)

@app.route('/history/<path:crawl_id>')
def history_detail(crawl_id):
    decoded_id = unquote(crawl_id)  # URL-safe decoding
    data = redis_storage.get_crawl_data(decoded_id)
    if not data:
        return redirect(url_for('history'))
    return render_template('results.html', results=data['page_data'][0], history=True)

@app.route('/delete/<path:crawl_id>')
def delete_crawl(crawl_id):
    decoded_id = unquote(crawl_id)
    redis_storage.delete_crawl_data(decoded_id)
    return redirect(url_for('history'))

@app.route('/delete-multiple')
def delete_multiple():
    ids = request.args.get('ids', '').split(',')
    for crawl_id in ids:
        if crawl_id:
            decoded_id = unquote(crawl_id)
            redis_storage.delete_crawl_data(decoded_id)
    return redirect(url_for('history'))

if __name__ == '__main__':
    redis_storage = init_redis()  # Initial connection attempt
    if redis_storage is None:
        print("Warning: Redis connection is not available. Some features may not work.")
    app.run(debug=True, port=5000, host='0.0.0.0')