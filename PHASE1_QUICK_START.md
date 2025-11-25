# Phase 1 Quick Start Guide

## 5-Minute Setup

### 1. Copy Environment Template
```bash
cp .env.example .env.local
```

### 2. Fill Environment Variables
Edit `.env.local` with your actual credentials:
```
LIVEKIT_URL=wss://your-livekit.cloud
LIVEKIT_API_KEY=your-api-key
LIVEKIT_API_SECRET=your-api-secret
OPENAI_API_KEY=your-openai-key
POSTGRESQL_URL=postgresql://user:pass@localhost/cv_db
QDRANT_URL=http://localhost:6333
QDRANT_API_KEY=your-qdrant-key
```

### 3. Install Dependencies
```bash
uv sync
```

### 4. Download Models
```bash
uv run python src/agent.py download-files
```

### 5. Test Configuration
```bash
uv run python src/config.py
```

Expected output:
```
✓ Configuration loaded successfully
  - LiveKit URL: wss://your-livekit...
  - LLM Model: openai/gpt-4.1-mini
  - Qdrant Collection: cv_documents
```

## Run Tests

```bash
# Run all tests
uv run pytest

# Run specific module
uv run pytest tests/test_mcp_server.py -v

# Run with coverage
uv run pytest --cov=src
```

## Module Quick Reference

### Configuration (`src/config.py`)
```python
from config import get_config

config = get_config()
api_key = config.get_openai_api_key()
pg_url = config.get_postgresql_url()
```

### MCP Server (`src/mcp_server.py`)
```python
from mcp_server import create_mcp_server

server = create_mcp_server()
result = server.get_cv_summary()
results = server.search_company_experience("TechCorp")
```

### MCP Client (`src/mcp_client.py`)
```python
from mcp_client import get_mcp_client

client = get_mcp_client()
summary = client.get_cv_summary()
tools = client.get_available_tools()
```

### Voice Agent (`src/agent.py`)
```python
from agent import Assistant
from mcp_client import get_mcp_client

mcp_client = get_mcp_client()
agent = Assistant(mcp_client=mcp_client)
```

## Verify Each Module

### 1. Test Config
```bash
uv run python src/config.py
# Should print: ✓ Configuration loaded successfully
```

### 2. Test MCP Server
```bash
uv run python src/mcp_server.py
# Should print: ✓ MCP Server is working correctly
```

### 3. Test MCP Client
```bash
uv run python src/mcp_client.py
# Should print: ✓ MCP Client initialized successfully
```

### 4. Test Agent
```bash
uv run python -c "from agent import Assistant; print('✓ Agent initialized')"
# Should print: ✓ Agent initialized
```

## Run Agent

### Console Mode (for testing)
```bash
uv run python src/agent.py console
```

Type your questions and the agent will respond using tools.

### Development Server
```bash
uv run python src/agent.py dev
```

Starts server ready for frontend connections.

## Common Tools

### Get CV Summary
- **Tool**: `get_cv_summary()`
- **Input**: None
- **Output**: Name, current role, years of experience, total jobs, degrees, publications

### Search by Company
- **Tool**: `search_company_experience(company_name)`
- **Example**: `search_company_experience("TechCorp")`
- **Output**: Role, location, dates, technologies, skills

### Search by Technology
- **Tool**: `search_technology_experience(technology)`
- **Example**: `search_technology_experience("Python")`
- **Output**: Jobs using that technology

### Search Education
- **Tool**: `search_education(degree="PhD")` or `search_education()`
- **Output**: Institution, degree, field, graduation date, thesis

### Search Publications
- **Tool**: `search_publications(year=2023)` or `search_publications()`
- **Output**: Title, conference, DOI, year, keywords

### Search Skills
- **Tool**: `search_skills(category)` where category is "AI", "ML", "programming", "Tools", "Cloud", "Data_tools"
- **Output**: List of skills in that category

### Semantic Search
- **Tool**: `semantic_search(query)` or `semantic_search(query, section="work_experience")`
- **Example**: `semantic_search("machine learning expertise")`
- **Output**: Semantically matching content with similarity scores

## File Structure

```
src/
  ├── agent.py           # Voice agent with MCP tool integration
  ├── config.py          # Configuration management
  ├── mcp_client.py      # MCP client wrapper
  ├── mcp_server.py      # MCP server with database tools
  ├── prompts.py         # System prompts and instructions
  └── __init__.py

tests/
  ├── test_agent.py      # LiveKit agent tests
  ├── test_agent_integration.py  # Agent + MCP integration tests
  ├── test_mcp_client.py # MCP client tests
  ├── test_mcp_server.py # MCP server tests
  └── __init__.py

.env.example            # Template for environment variables
.env.local              # Your actual environment (DO NOT COMMIT)
```

## Troubleshooting

| Problem | Solution |
|---------|----------|
| `ValueError: Missing required env vars` | Run `cp .env.example .env.local` and fill in values |
| `ModuleNotFoundError: No module named X` | Run `uv sync` to install dependencies |
| `Database connection error` | Verify PostgreSQL is running and URL is correct |
| `Qdrant connection refused` | Verify Qdrant server is running at QDRANT_URL |
| `VAD model not found` | Run `uv run python src/agent.py download-files` |
| Tests fail with imports | Make sure tests/ directory has `__init__.py` |

## Next Steps

1. ✅ Phase 1 Backend (you are here)
2. → Phase 2 Frontend (React)
3. → Phase 3 Quality Assurance

See [PHASE1_IMPLEMENTATION.md](./PHASE1_IMPLEMENTATION.md) for detailed documentation.
