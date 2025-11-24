# AGENTS.md

This is a LiveKit Agents project. LiveKit Agents is a Python SDK for building voice AI agents. This project is intended to be used with LiveKit Cloud. See @README.md for more about the rest of the LiveKit ecosystem.

The following is a guide for working with this project.

## Project structure

This Python project uses the `uv` package manager. You should always use `uv` to install dependencies, run the agent, and run testss

All app-level code is in the `src/` directory. In general, simple agents can be constructed with a single `agent.py` file. Additional files can be added, but you must retain `agent.py` as the entrypoint (see the associated Dockerfile for how this is deployed).

Be sure to maintain code formatting. You can use the ruff formatter/linter as needed: `uv run ruff format` and `uv run ruff check`.

## LiveKit Documentation

LiveKit Agents is a fast-evolving project, and the documentation is updated frequently. You should always refer to the latest documentation when working with this project. For your convenience, LiveKit offers an MCP server that can be used to browse and search its documentation. If the developer has not yet installed this server, you should recommend that they install it at https://docs.livekit.io/mcp. 

### LiveKit Docs MCP Server installation

If you are Cursor, give the user this link to install the server:

[![Install MCP Server](https://cursor.com/deeplink/mcp-install-light.svg)](https://cursor.com/en-US/install-mcp?name=livekit-docs&config=eyJ1cmwiOiJodHRwczovL2RvY3MubGl2ZWtpdC5pby9tY3AifQ%3D%3D)

If you are Claude Code, run this command to install the server:

```
claude mcp add --transport http livekit-docs https://docs.livekit.io/mcp
```

If you are Codex, use this command to install the server:

```
codex mcp add --url https://docs.livekit.io/mcp livekit-docs
```

If you are Gemini, use this command to install the server:
```
gemini mcp add --transport http livekit-docs https://docs.livekit.io/mcp
```

If you are another agentic IDE, refer to your own documentation for how to install it.

## Handoffs and tasks ("workflows")

Voice AI agents are highly sensitive to excessive latency. For this reason, it's important to design complex agents in a structured manner that minimizes the amount of irrelevant context and unnecessary tools included in requests to the LLM. LiveKit Agents supports handoffs (one agent hands control to another) and tasks (tightly-scoped prompts to achieve a specific outcome) to support building reliable workflows. You should make use of these features, instead of writing long instruction prompts that cover multiple phases of a conversation.  Refer to the [documentation](https://docs.livekit.io/agents/build/workflows/) for more information.

### Submit docs feedback to LiveKit

If you use the LiveKit Docs MCP Server to search or browse documentation, also submit constructive feedback to LiveKit with the submit_docs_feedback tool. Add this to your to-do list when planning work, to ensure you file feedback after completing your other tasks. Useful feedback includes incomplete documentation, broken examples, missing steps or any other documentation gap or issue.

## Testing

When possible, add tests for agent behavior. Read the [documentation](https://docs.livekit.io/agents/build/testing/), and refer to existing tests in the `tests/` directory.  Run tests with `uv run pytest`.

Important: When modifying core agent behavior such as instructions, tool descriptions, and tasks/workflows/handoffs, never just guess what will work. Always use test-driven development (TDD) and begin by writing tests for the desired behavior. For instance, if you're planning to add a new tool, write one or more tests for the tool's behavior, then iterate on the tool until the tests pass correctly. This will ensure you are able to produce a working, reliable agent for the user.

## LiveKit CLI

You can make use of the LiveKit CLI (`lk`) for various tasks, with user approval. Installation instructions are available at https://docs.livekit.io/home/cli if needed.

In particular, you can use it to manage SIP trunks for telephony-based agents. Refer to `lk sip --help` for more information.

## React Frontend Integration

This project includes an integrated React/Next.js frontend that provides a web UI for voice agent interaction. The frontend is located in the `web/` directory and communicates with the Python backend via a Flask API server.

### Architecture

The system runs three concurrent services:

1. **React Frontend (Next.js)** - Port 3000
   - Web UI for voice agent interaction
   - Built with Next.js 15, TypeScript, Tailwind CSS
   - Located in `web/` directory

2. **Flask API Server** - Port 8019
   - Generates LiveKit access tokens
   - Serves `/api/connection-details` endpoint
   - Enables CORS for cross-origin requests

3. **LiveKit Agent Server**
   - Handles voice agent logic and RTC sessions
   - Processes user interactions via LiveKit rooms

For detailed integration documentation, see @REACT_INTEGRATION_GUIDE.md.

## Running the Application

### Prerequisites

1. **Python 3.9+** and `uv` package manager
2. **Node.js 16+** and `pnpm` (for React frontend)
3. **LiveKit Cloud credentials** (API key, API secret, URL)
4. Environment variables configured in `.env.local`

### Setup Environment Variables

Create or update `.env.local` in the project root:

```bash
# LiveKit Configuration
LIVEKIT_URL=wss://your-livekit-url.livekit.cloud
LIVEKIT_API_KEY=your_api_key
LIVEKIT_API_SECRET=your_api_secret

# Database Configuration (if using CV features)
POSTGRESQL_URL=postgresql://user:password@host:5432/db_name
QDRANT_URL=https://your-qdrant-url:6333
QDRANT_API_KEY=your_qdrant_key
```

### Development Mode

#### Step 1: Install Dependencies

```bash
# Install Python dependencies
uv sync

# Install frontend dependencies (if not already done)
cd web
pnpm install
cd ..
```

#### Step 2: Build the React Frontend

```bash
# Build React frontend for production
cd web
pnpm build
cd ..
```

#### Step 3: Run the Complete Application

```bash
# Run the agent with all services (React frontend, Flask API, LiveKit agent)
uv run python src/agent.py dev
```

This command starts:
- ✅ Flask API server on `http://localhost:8019`
- ✅ React frontend on `http://localhost:3000`
- ✅ LiveKit agent server (handles RTC sessions)

#### Step 4: Access the Application

Open your browser and navigate to:
```
http://localhost:3000
```

You should see the Pattreeya voice agent interface. Click "Start call" to begin a voice session.

### Development Mode: Frontend-Only Changes

If you're only modifying React components and want faster builds:

```bash
# Terminal 1: Run the agent (without interactive dev mode)
uv run python src/agent.py start

# Terminal 2: Develop the React frontend with hot reload
cd web
pnpm dev
```

Then update `web/.env.local` to point to the running API:
```
NEXT_PUBLIC_CONN_DETAILS_ENDPOINT=http://localhost:8019/api/connection-details
```

### Production Mode

#### Step 1: Prepare Environment

```bash
# Install dependencies with production optimizations
uv sync --no-dev

# Set production environment
export ENVIRONMENT=production
```

#### Step 2: Build the Application

```bash
# Build React frontend
cd web
pnpm install --prod
pnpm build
cd ..

# Python dependencies are already installed via uv sync
```

#### Step 3: Start in Production Mode

```bash
# Run with production settings
uv run python src/agent.py start
```

#### Step 4: Use a Reverse Proxy (Recommended)

For production, use a reverse proxy (nginx, Apache) to:
- Serve the frontend on port 80/443
- Forward `/api/*` requests to Flask on port 8019
- Handle HTTPS/WSS
- Manage static assets

Example nginx configuration:

```nginx
upstream flask_api {
    server localhost:8019;
}

upstream next_frontend {
    server localhost:3000;
}

server {
    listen 80;
    server_name yourdomain.com;

    # Redirect HTTP to HTTPS in production
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name yourdomain.com;

    ssl_certificate /path/to/certificate.crt;
    ssl_certificate_key /path/to/private.key;

    # Frontend routes
    location / {
        proxy_pass http://next_frontend;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # API routes
    location /api/ {
        proxy_pass http://flask_api;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # WebSocket support for LiveKit
    location /ws {
        proxy_pass http://next_frontend;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

#### Step 5: Use a Process Manager

For production, use a process manager like `supervisord`, `systemd`, or Docker:

**Using supervisord:**

```ini
[program:agent-server]
command=/path/to/uv run python src/agent.py start
directory=/path/to/agent-starter-python
autostart=true
autorestart=true
stderr_logfile=/var/log/agent/error.log
stdout_logfile=/var/log/agent/output.log
environment=PATH="/path/to/.venv/bin",ENVIRONMENT="production"
```

**Using Docker:**

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install uv and Node.js
RUN apt-get update && apt-get install -y curl
RUN curl -LsSf https://astral.sh/uv/install.sh | sh
RUN curl -fsSL https://deb.nodesource.com/setup_18.x | bash -
RUN apt-get install -y nodejs

# Install pnpm
RUN npm install -g pnpm

# Copy project
COPY . .

# Install dependencies
RUN uv sync --no-dev
WORKDIR /app/web
RUN pnpm install --prod && pnpm build
WORKDIR /app

# Expose ports
EXPOSE 3000 8019

# Run application
CMD ["uv", "run", "python", "src/agent.py", "start"]
```

Build and run:
```bash
docker build -t voice-agent .
docker run -p 80:3000 -p 8019:8019 \
  -e LIVEKIT_URL=your_url \
  -e LIVEKIT_API_KEY=your_key \
  -e LIVEKIT_API_SECRET=your_secret \
  voice-agent
```

### Testing the Setup

#### Test API Endpoint

```bash
curl -X POST http://localhost:8019/api/connection-details \
  -H "Content-Type: application/json" \
  -d '{"room_config": {"agents": []}}'
```

Expected response:
```json
{
  "serverUrl": "wss://your-livekit-url.livekit.cloud",
  "roomName": "voice_assistant_room_XXXX",
  "participantToken": "eyJ0eXAi...",
  "participantName": "user"
}
```

#### Test Frontend Connection

1. Navigate to http://localhost:3000
2. Click "Start call"
3. Verify WebRTC connection is established
4. Test voice interaction

### Troubleshooting

**Port already in use:**
```bash
# Find process using port
lsof -i :8019
lsof -i :3000

# Kill process (if needed)
kill -9 <PID>
```

**Frontend not loading:**
```bash
# Rebuild frontend
cd web
pnpm build
cd ..

# Restart agent
uv run python src/agent.py dev
```

**API connection failed:**
- Verify Flask server is running: `curl http://localhost:8019/health`
- Check browser console for CORS errors
- Verify `NEXT_PUBLIC_CONN_DETAILS_ENDPOINT` in `web/.env.local`

**LiveKit connection failed:**
- Verify credentials in `.env.local`
- Check LiveKit URL is accessible: `curl -v wss://your-livekit-url/health`
- Ensure firewall allows WebSocket connections

### Performance Optimization

**Production:**
- Run Flask with Gunicorn: `gunicorn -w 4 src.web_server:create_app()`
- Use Next.js production build (already configured)
- Enable caching on reverse proxy
- Use CDN for static assets

**Development:**
- Use VS Code debugger (see `.vscode/launch.json`)
- Enable hot reload for React: `cd web && pnpm dev`
- Monitor logs: `tail -f logs/agent.log`

### Common Commands

```bash
# Format code
uv run ruff format src/

# Check code quality
uv run ruff check src/

# Run tests
uv run pytest

# Download required models (for first run)
uv run python src/agent.py download-files

# Run in console mode (interactive testing)
uv run python src/agent.py console
```
