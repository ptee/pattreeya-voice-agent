# Phase 1: Backend Implementation - Complete Guide

This document describes the Phase 1 (Backend) implementation for the Voice Agent application.

## Overview

Phase 1 consists of building a backend voice AI agent with the following components:
- **Voice Agent**: Python-based agent using LiveKit for real-time communication
- **RAG System**: Retrieval-Augmented Generation system for personal assistant context
- **Database Integration**: PostgreSQL (via MCP) and Qdrant Vector DB for data retrieval
- **Configuration Management**: Centralized environment variable handling
- **Comprehensive Testing**: Unit and integration tests

## Architecture Components

### 1. Configuration Management (`src/config.py`)

**Purpose**: Centralized configuration loader for environment variables

**Features**:
- Singleton pattern for global configuration access
- Loads all secrets from `.env.local`
- Validates required environment variables at startup
- Supports defaults for optional variables

**Key Classes**:
```python
ConfigManager:
  - get_livekit_url() -> str
  - get_livekit_api_key() -> str
  - get_livekit_api_secret() -> str
  - get_openai_api_key() -> str
  - get_llm_model() -> str
  - get_embedding_model() -> str
  - get_postgresql_url() -> str
  - get_qdrant_url() -> str
  - get_qdrant_api_key() -> str
  - get_qdrant_collection() -> str
  - get_instance() -> ConfigManager (singleton)

def get_config() -> ConfigManager
```

**Environment Variables**:
```
# LiveKit
LIVEKIT_URL=
LIVEKIT_API_KEY=
LIVEKIT_API_SECRET=

# OpenAI/LLM
OPENAI_API_KEY=
LLM_MODEL=openai/gpt-4.1-mini
EMBEDDING_MODEL=text-embedding-3-small

# PostgreSQL
POSTGRESQL_URL=postgresql://user:password@localhost:5432/cv_database

# Qdrant Vector Database
QDRANT_URL=http://localhost:6333
QDRANT_API_KEY=
QDRANT_VECTOR_COLLECTION=cv_documents
```

### 2. MCP Server (`src/mcp_server.py`)

**Purpose**: Provides standardized tools for querying PostgreSQL and Qdrant databases

**Key Class**: `DatabaseTools`

**Available Tools** (9 total):

1. **get_cv_summary()** - Get high-level CV overview
   - Returns: name, current_role, total_years_experience, total_jobs, etc.

2. **search_company_experience(company_name)** - Find jobs at specific company
   - Args: company_name (string)
   - Returns: List of work records with company, role, technologies, etc.

3. **search_technology_experience(technology)** - Find jobs using specific tech
   - Args: technology (e.g., 'Python', 'TensorFlow')
   - Returns: Work records using that technology

4. **search_work_by_date(start_year, end_year)** - Filter by date range
   - Args: start_year (int), end_year (int)
   - Returns: Work records within date range

5. **search_education(institution, degree)** - Find education records
   - Args: institution (optional), degree (optional)
   - Returns: Education records with thesis, graduation_date, etc.

6. **search_publications(year)** - Find research publications
   - Args: year (optional)
   - Returns: Publications with title, conference, DOI, content

7. **search_skills(category)** - Find skills by category
   - Args: category ('AI', 'ML', 'programming', 'Tools', 'Cloud', 'Data_tools')
   - Returns: List of skills in category

8. **search_awards_certifications(award_type)** - Find awards/certifications
   - Args: award_type (optional)
   - Returns: Awards and certifications with dates and organizations

9. **semantic_search(query, section, top_k)** - Vector similarity search
   - Args: query (natural language), section (optional), top_k (default: 5)
   - Returns: Semantically similar content with similarity scores

### 3. MCP Client (`src/mcp_client.py`)

**Purpose**: Client wrapper for MCP server tools, used by LLM agents

**Key Class**: `MCPClient`

**Features**:
- Wraps all DatabaseTools functions
- Global singleton instance via `get_mcp_client()`
- Tool registry with descriptions and parameter specs
- Dynamic tool execution via `execute_tool(tool_name, **kwargs)`

### 4. Voice Agent (`src/agent.py`)

**Purpose**: Main voice AI agent using LiveKit for real-time communication

**Key Class**: `Assistant(Agent)`

**Features**:
- Extends LiveKit `Agent` class
- Integrates MCP Client for data retrieval
- Implements 9 function tools via `@function_tool` decorator
- Uses system prompt from `prompts.py`
- Handles errors gracefully with informative messages

**System Prompt**: Defines agent personality and instructions for tool usage
- Located in `src/prompts.py`
- Instructs agent to use tools for every question
- Includes tool descriptions and usage examples

**Tool Integration**:
Each MCP tool is wrapped as an async function tool:
```python
@function_tool
async def search_company_experience(self, context: RunContext, company_name: str) -> str:
    """Find all work experience at a specific company."""
    # Calls self.mcp_client and returns formatted result
```

## Setup Instructions

### 1. Environment Configuration

Copy `.env.example` to `.env.local` and fill in required values:

```bash
cp .env.example .env.local
```

Then edit `.env.local` with:
- LiveKit credentials (from https://cloud.livekit.io/)
- OpenAI API key
- PostgreSQL connection URL
- Qdrant server details

### 2. Virtual Environment

```bash
# Using uv (recommended)
uv sync

# Or using pip with venv
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Download Model Files

```bash
uv run python src/agent.py download-files
```

This downloads Silero VAD and LiveKit turn detector models.

### 4. Run Tests

```bash
# Run all tests
uv run pytest

# Run specific test file
uv run pytest tests/test_config.py -v

# Run with coverage
uv run pytest --cov=src tests/
```

### 5. Test Individual Modules

```bash
# Test configuration
uv run python src/config.py

# Test MCP Server
uv run python src/mcp_server.py

# Test MCP Client
uv run python src/mcp_client.py

# Test Agent initialization
uv run python src/agent.py
```

## Testing

### Test Suite Organization

**tests/test_agent_integration.py** (60+ tests)
- Assistant initialization
- Tool existence and callable checks
- Async tool invocations
- Error handling
- Integration workflows

**tests/test_mcp_client.py** (40+ tests)
- MCPClient initialization
- Tool methods
- Tool registry
- execute_tool dynamic invocation
- Singleton pattern validation
- Integration workflows

**tests/test_mcp_server.py** (50+ tests)
- DatabaseTools initialization
- Each MCP tool function
- CV summary retrieval
- Company/technology searches
- Education/publications searches
- Skills and awards searches
- Row-to-dict conversions
- Error conditions

### Running Tests

```bash
# Run all tests
uv run pytest -v

# Run specific test class
uv run pytest tests/test_mcp_server.py::TestDatabaseToolsInit -v

# Run with coverage report
uv run pytest --cov=src --cov-report=html

# Run async tests specifically
uv run pytest tests/test_agent_integration.py -v -k "asyncio"
```

## Module Interactions

```
┌─────────────────────────────────────────────────────────┐
│                    User Input (Voice)                    │
└────────────────────────┬────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────┐
│                  Agent (LiveKit Session)                 │
│  ┌──────────────────────────────────────────────────┐  │
│  │  STT → LLM → TTS (via LiveKit Inference)        │  │
│  │  Function Tools: @function_tool decorators      │  │
│  └──────────────────────────────────────────────────┘  │
└────────────────────────┬────────────────────────────────┘
                         │
                         ▼
         ┌───────────────────────────────┐
         │  MCP Client (get_mcp_client)  │
         │  - 9 tool wrappers            │
         │  - Tool registry              │
         │  - execute_tool()             │
         └───────────────────────────────┘
                         │
           ┌─────────────┴─────────────┐
           ▼                           ▼
      ┌─────────────┐          ┌──────────────┐
      │ MCP Server  │          │  Config      │
      │ DatabaseTools
│          │ Manager    │
      │ - 9 DB tools  │          │ - Secrets    │
      │ - Queries     │          │ - Validation │
      └─────────────┘          └──────────────┘
           │
      ┌────┴─────────────────────┐
      ▼                          ▼
  ┌──────────────┐        ┌────────────┐
  │  PostgreSQL  │        │  Qdrant    │
  │  (structured)│        │  (semantic)│
  └──────────────┘        └────────────┘
```

## Code Quality

### Type Hints
- 95%+ type hint coverage across all modules
- Full type hints on function signatures and returns

### Error Handling
- Custom exception hierarchy (planned for Phase 1 extension)
- Graceful error messages to user
- Detailed logging for debugging

### Logging
- Configured in each module
- Structured format: `%(asctime)s - %(name)s - %(levelname)s - %(message)s`
- Uses Python's standard `logging` module

### Code Style
- Follows PEP 8 guidelines
- Uses `ruff` for formatting and linting:
```bash
uv run ruff format src/
uv run ruff check src/
```

## Running the Agent

### Development Mode (Terminal)

```bash
uv run python src/agent.py console
```

This starts the agent in console mode for local testing.

### Development Server (for frontend integration)

```bash
uv run python src/agent.py dev
```

This runs the agent server ready for connections from a frontend.

### Production

```bash
uv run python src/agent.py start
```

This runs the agent in production mode.

## Deployment

### Docker

```bash
# Build Docker image
docker build -t voice-agent .

# Run Docker container
docker run -e LIVEKIT_URL="..." \
           -e LIVEKIT_API_KEY="..." \
           -e LIVEKIT_API_SECRET="..." \
           -e OPENAI_API_KEY="..." \
           voice-agent
```

### Environment Variables for Deployment

All configuration comes from environment variables. Set these in your deployment platform:

- `LIVEKIT_URL`
- `LIVEKIT_API_KEY`
- `LIVEKIT_API_SECRET`
- `OPENAI_API_KEY`
- `LLM_MODEL` (optional, default: openai/gpt-4.1-mini)
- `EMBEDDING_MODEL` (optional, default: text-embedding-3-small)
- `POSTGRESQL_URL`
- `QDRANT_URL`
- `QDRANT_API_KEY`
- `QDRANT_VECTOR_COLLECTION` (optional, default: cv_documents)

## Troubleshooting

### Configuration Issues

**Error**: `Missing required environment variables`

**Solution**: Ensure all required variables are in `.env.local`:
```bash
cp .env.example .env.local
# Edit .env.local with actual values
```

### Database Connection

**Error**: `Database connection error`

**Solution**:
1. Verify PostgreSQL is running
2. Check `POSTGRESQL_URL` is correct format: `postgresql://user:password@host:port/database`
3. Verify Qdrant server is running and accessible at `QDRANT_URL`

### Missing Models

**Error**: `VAD model not found`

**Solution**:
```bash
uv run python src/agent.py download-files
```

### Import Errors

**Error**: `ModuleNotFoundError: No module named 'livekit'`

**Solution**:
```bash
uv sync  # Reinstall dependencies
```

## Next Steps

### Phase 2: Frontend

After Phase 1 is complete, proceed to Phase 2 to build a React-based frontend:
- Clone from `agent-starter-react-pt`
- Integrate with this backend
- Add voice UI components

### Phase 3: Quality Assurance

- Enhanced logging
- Performance monitoring
- Deployment testing
- Production hardening

## References

- [LiveKit Agents Documentation](https://docs.livekit.io/agents/)
- [LiveKit Python SDK](https://github.com/livekit/python-sdks)
- [Plan.md](./Plan.md) - Original project plan
- [AGENTS.md](./AGENTS.md) - Agent development guide
