# Python Web Crawler Service

A comprehensive web crawling service built with Python Flask that provides detailed website analysis, SEO metrics, performance insights, and accessibility checks. The service features a modern web interface with dark/light theme support and stores results in Redis for fast retrieval.

## 🚀 Features

- **Advanced Web Crawling**: Multi-threaded crawling with retry logic and rate limiting
- **Comprehensive Analysis**: 
  - SEO metrics and meta tag analysis
  - Performance metrics and load time analysis
  - Accessibility checks
  - Security header analysis
  - Technology detection
  - Social media link extraction
- **Modern Web Interface**: Responsive design with dark/light theme toggle
- **Redis Storage**: Fast data persistence and retrieval
- **Docker Support**: Containerized deployment with Docker Compose
- **Health Monitoring**: URL health checks and status monitoring
- **Scalable Architecture**: Load balancer ready with Traefik

## 📋 Project Structure

```
Python-Crawler-Service/
├── main.py                 # Advanced crawler implementation
├── app.py                  # Flask web application
├── redis_storage.py        # Redis data storage handler
├── requirements.txt        # Python dependencies
├── Dockerfile             # Container configuration
├── docker-compose.yml     # Multi-service deployment
├── entrypoint.sh          # Container startup script
├── templates/             # HTML templates
│   ├── base.html          # Base template with navigation
│   ├── index.html         # Crawler form interface
│   ├── results.html       # Results display page
│   └── history.html       # Crawl history page
├── static/
│   └── css/
│       └── main.css       # Styling and theme support
└── docs/                  # Documentation and examples
    ├── src/crawler/       # Example crawler implementations
    └── not_so_simple_python_crawler.py
```

## 🛠️ Installation

### Prerequisites

- Python 3.12+
- Redis server
- Docker and Docker Compose (for containerized deployment)

### Local Development Setup

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd Python-Crawler-Service
   ```

2. **Install Python dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Start Redis server:**
   ```bash
   redis-server
   ```

4. **Run the application:**
   ```bash
   python app.py
   ```

5. **Access the web interface:**
   Open http://localhost:5000 in your browser

### Docker Deployment

1. **Build the Docker image:**
   ```bash
   docker-compose build
   ```

2. **Start all services:**
   ```bash
   docker-compose up -d
   ```

   Or combine both steps:
   ```bash
   docker-compose build && docker-compose up -d
   ```

3. **Access the application:**
   - Web interface: http://localhost:81
   - Traefik dashboard: http://localhost:8080

## 🎯 Usage

### Web Interface

1. **Navigate to the crawler interface**
2. **Enter a URL** to crawl (e.g., https://example.com)
3. **Configure crawling parameters:**
   - Maximum pages to crawl (1-50)
   - Maximum retries (1-5)
   - Maximum workers (1-10)
   - Delay between requests (1-10 seconds)
   - Force refresh option
4. **Click "Crawl"** to start the analysis
5. **View detailed results** including:
   - Page information and metadata
   - SEO analysis
   - Performance metrics
   - Accessibility checks
   - Security headers
   - Technology detection

### API Endpoints

- `GET /` - Main crawler interface
- `POST /crawl` - Start crawling process
- `GET /results/<crawl_id>` - View crawl results
- `GET /history` - View crawl history
- `GET /api/crawl/<crawl_id>` - JSON API for results

### Programmatic Usage

```python
from main import AdvancedWebCrawler

# Initialize crawler
crawler = AdvancedWebCrawler(
    start_url="https://example.com",
    max_retries=3,
    delay=1,
    max_workers=5
)

# Start crawling
crawler.crawl(max_pages=5)

# Results are automatically saved to Redis
```

## 📊 Analysis Features

### SEO Metrics
- Meta description presence
- Canonical URL detection
- Robots meta tags
- Sitemap links
- Schema markup detection

### Performance Analysis
- Page load times
- Resource counts (scripts, CSS, images)
- Resource hints detection
- Content optimization metrics

### Accessibility Checks
- Image alt text analysis
- ARIA landmarks detection
- Form label validation
- Skip links detection
- Language specification

### Security Analysis
- Security headers evaluation
- Content Security Policy
- X-Frame-Options
- XSS Protection headers

### Technology Detection
- Framework identification (React, Angular, WordPress)
- Library detection (jQuery, Bootstrap)
- CMS detection
- Server technology analysis

## 🔧 Configuration

### Environment Variables

```bash
# Redis Configuration
REDIS_URL=redis://localhost:6379
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=
REDIS_DB=0
REDIS_RETRY_COUNT=3
REDIS_RETRY_DELAY=1

# Application Configuration
FLASK_ENV=production
FLASK_DEBUG=False
```

### Crawler Parameters

- `max_pages`: Maximum number of pages to crawl (default: 5)
- `max_retries`: Number of retry attempts for failed requests (default: 3)
- `max_workers`: Concurrent worker threads (default: 5)
- `delay`: Delay between requests in seconds (default: 1)

## 🐳 Docker Services

The application uses Docker Compose with the following services:

- **Traefik**: Load balancer and reverse proxy
- **Crawler**: Python Flask application (3 replicas)
- **Redis Master**: Primary Redis instance
- **Redis Slave**: Redis read replicas (2 instances)

## 🔍 Monitoring and Logging

- Application logs are written to `crawler.log`
- Health checks monitor URL availability
- Redis stores crawl results with timestamps
- Performance metrics track response times

## 🚨 Troubleshooting

### Common Issues

1. **Redis Connection Error:**
   ```bash
   # Check Redis status
   redis-cli ping
   
   # Restart Redis service
   sudo systemctl restart redis
   ```

2. **Docker Build Issues:**
   ```bash
   # Rebuild containers
   docker-compose down
   docker-compose build --no-cache
   docker-compose up -d
   ```

3. **Permission Errors:**
   ```bash
   # Fix entrypoint permissions
   chmod +x entrypoint.sh
   ```

### Performance Optimization

- Adjust `max_workers` based on server capacity
- Increase `delay` for rate-limited websites
- Use `force_refresh` sparingly to avoid cache misses
- Monitor Redis memory usage for large crawl jobs

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License.

## 🔗 Related Projects

- Simple Python Crawler: `/docs/src/crawler/simple_python_crawler.py`
- Advanced Examples: `/docs/src/crawler/not_so_simple_python_crawler.py`

## 📞 Support

For issues and questions:
1. Check the troubleshooting section
2. Review the logs in `crawler.log`
3. Open an issue in the repository

---

**Built with ❤️ using Python Flask, Redis, and Docker**
