# API Documentation

## Quick Start

```bash
# Build and run
make dev-api

# Test endpoints
make test-api
```

## Endpoints

### `GET /`

Welcome message with timestamp and version.

```bash
curl http://localhost:8000/
```

### `GET /health`

Health check for monitoring.

```bash
curl http://localhost:8000/health
```

### `GET /api/echo/{message}`

Echo endpoint - returns your message with metadata.

```bash
curl http://localhost:8000/api/echo/hello-world
```

**Response:**

```json
{
  "echo": "hello-world",
  "timestamp": "2025-06-12T04:44:46.944014",
  "length": 11
}
```

## Development

### Local Setup

```bash
cd api/
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -e .
python main.py
```

### Docker

```bash
# Manual build
docker build -f docker/Dockerfile.api -t hypexbt-api .
docker run -p 8000:8000 hypexbt-api

# Or use Makefile
make dev-api
```

### Adding Endpoints

Edit `api/main.py`:

```python
@app.get("/new-endpoint")
async def new_endpoint():
    return {"message": "New endpoint"}
```

## Environment

- **Port**: 8000
- **Python**: 3.13
- **Dependencies**: FastAPI, Uvicorn
