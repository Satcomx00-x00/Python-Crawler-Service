from flask import Flask, render_template, request, redirect, url_for
import re
from main import AdvancedWebCrawler
from functools import wraps
import asyncio

app = Flask(__name__)

URL_PATTERN = re.compile(
    r'^https?://'
    r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'
    r'localhost|'
    r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'
    r'(?::\d+)?'
    r'(?:/?|[/?]\S+)$', re.IGNORECASE)

def validate_url(url):
    return bool(URL_PATTERN.match(url))

def async_route(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        return asyncio.run(f(*args, **kwargs))
    return wrapper

@app.route('/', methods=['GET'])
def index():
    return render_template('index.html')

@app.route('/crawl', methods=['POST'])
@async_route
async def crawl():
    url = request.form.get('url', '').strip()
    
    if not url or not validate_url(url):
        return render_template('index.html', error="Invalid URL format")
    
    try:
        crawler = AdvancedWebCrawler(url, max_retries=2, delay=1, max_workers=3)
        crawler.crawl(max_pages=3)
        return render_template('results.html', results=crawler.visited_pages[0])
    except Exception as e:
        return render_template('index.html', error=f"Error crawling URL: {str(e)}")

if __name__ == '__main__':
    app.run(debug=True)