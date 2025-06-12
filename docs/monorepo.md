# Monorepo Strategy

## Structure

```
hypexbt/
├── api/                 # FastAPI echo server
│   ├── main.py
│   ├── pyproject.toml
│   └── .tool-versions
├── agent/               # Twitter bot
│   ├── src/
│   ├── pyproject.toml
│   └── .tool-versions
├── build/               # Docker configs
│   └── Dockerfile.api
├── Makefile             # Development commands
└── docs/                # Documentation
```

## Why This Setup

- **Separate Dependencies**: Each service has its own `pyproject.toml`
- **Isolated Environments**: Different Python versions via `.tool-versions`
- **Easy Development**: Makefile commands for common tasks
- **Scalable**: Ready for Next.js frontend, more microservices

## Key Files

- `pyproject.toml` - Dependencies per service
- `.tool-versions` - Python version per service
- `Makefile` - Build/run/test commands
- `build/` - Docker configurations

## Development Workflow

```bash
# Build and run API
make dev-api

# Test API endpoints
make test-api

# See all commands
make help
```

## Adding New Services

1. Create new directory (e.g., `frontend/`)
2. Add `pyproject.toml` and `.tool-versions`
3. Create `build/Dockerfile.{service}`
4. Add Makefile targets
5. Update this documentation
