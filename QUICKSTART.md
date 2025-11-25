# Quick Start Guide

Fast reference for running the voice agent application in development and production modes.

## TL;DR - Quick Start

### Development Mode (5 minutes)

```bash
# 1. Install dependencies
uv sync

# 2. Build React frontend (one-time)
cd web && pnpm build && cd ..

# 3. Run everything
uv run python src/agent.py dev

# 4. Open browser
# http://localhost:3000
```

### Production Mode

```bash
# 1. Prepare
uv sync --no-dev
cd web && pnpm install --prod && pnpm build && cd ..

# 2. Run
uv run python src/agent.py start

# 3. Set up reverse proxy (nginx)
# See AGENTS.md for nginx config
```

---

## Development Mode - Step by Step

### Prerequisites

- Python 3.9+
- Node.js 16+
- `uv` package manager
- `pnpm` package manager
- LiveKit Cloud account with credentials

### Step 1: Configure Environment

Create `.env.local`:

```bash
LIVEKIT_URL=wss://your-project.livekit.cloud
LIVEKIT_API_KEY=your_api_key
LIVEKIT_API_SECRET=your_api_secret

# Optional: Database configuration
POSTGRESQL_URL=postgresql://user:pass@host:5432/db
QDRANT_URL=https://your-qdrant:6333
QDRANT_API_KEY=your_key
```

### Step 2: Install Dependencies

```bash
# Python dependencies
uv sync

# Frontend dependencies
cd web
pnpm install
cd ..
```

### Step 3: Build Frontend (First Time Only)

```bash
cd web
pnpm build
cd ..
```

### Step 4: Start Application

```bash
uv run python src/agent.py dev
```

**Expected Output:**
```
✓ API server started on http://0.0.0.0:8019
✓ Next.js server started on http://0.0.0.0:3000
```

### Step 5: Access Application

1. Open browser: `http://localhost:3000`
2. Click "Start call"
3. Speak to the agent

### Development: React Changes Only

For faster frontend development:

```bash
# Terminal 1: Backend
uv run python src/agent.py start

# Terminal 2: Frontend (with hot reload)
cd web
pnpm dev
```

Then update `web/.env.local`:
```
NEXT_PUBLIC_CONN_DETAILS_ENDPOINT=http://localhost:8019/api/connection-details
```

---

## Production Mode - Step by Step

### Step 1: Prepare Environment

```bash
# Install production dependencies only
uv sync --no-dev

# Set environment variable
export ENVIRONMENT=production
```

### Step 2: Build Application

```bash
# Build frontend with production optimizations
cd web
pnpm install --prod
pnpm build
cd ..
```

### Step 3: Start Application

```bash
# Run in production mode
uv run python src/agent.py start
```

### Step 4: Set Up Reverse Proxy (Recommended)

Use nginx, Apache, or your preferred reverse proxy.

**Nginx example** (see AGENTS.md for full config):

```nginx
upstream flask_api {
    server localhost:8019;
}

upstream next_frontend {
    server localhost:3000;
}

server {
    listen 443 ssl http2;
    server_name yourdomain.com;

    location / {
        proxy_pass http://next_frontend;
    }

    location /api/ {
        proxy_pass http://flask_api;
    }
}
```

### Step 5: Use Process Manager (Recommended)

**Docker:**
```bash
docker build -t voice-agent .
docker run -p 80:3000 -p 8019:8019 \
  -e LIVEKIT_URL=wss://your-url.livekit.cloud \
  -e LIVEKIT_API_KEY=your_key \
  -e LIVEKIT_API_SECRET=your_secret \
  voice-agent
```

**Systemd:**
```ini
[Unit]
Description=Voice Agent
After=network.target

[Service]
Type=simple
User=agent
WorkingDirectory=/opt/agent-starter-python
ExecStart=/usr/local/bin/uv run python src/agent.py start
Restart=on-failure
RestartSec=10

[Install]
WantedBy=multi-user.target
```

---

## Ports & Services

| Service | Port | Purpose |
|---------|------|---------|
| React Frontend | 3000 | Web UI |
| Flask API | 8019 | Token generation |
| LiveKit Agent | N/A | Voice logic |

---

## Testing

### Test API Endpoint

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

### Test Frontend

1. Navigate to `http://localhost:3000`
2. Click "Start call"
3. Verify connection and test voice

---

## Common Issues

### Port Already in Use

```bash
# Find process
lsof -i :8019  # or :3000

# Kill process
kill -9 <PID>
```

### Frontend Not Building

```bash
cd web
rm -rf .next node_modules
pnpm install
pnpm build
cd ..
```

### API Connection Failed

```bash
# Check if API is running
curl http://localhost:8019/health

# Check frontend config
cat web/.env.local | grep NEXT_PUBLIC_CONN_DETAILS_ENDPOINT
```

### LiveKit Connection Failed

- Verify credentials in `.env.local`
- Check LiveKit URL is valid
- Test: `curl -v wss://your-url.livekit.cloud/health`

---

## Useful Commands

```bash
# Format code
uv run ruff format src/

# Check code quality
uv run ruff check src/

# Run tests
uv run pytest

# Download models
uv run python src/agent.py download-files

# Interactive console
uv run python src/agent.py console
```

---

## Architecture

```
┌─────────────────┐
│  Browser        │
│ localhost:3000  │
└────────┬────────┘
         │
    ┌────▼─────────────────────┐
    │  React Frontend           │
    │  (Next.js on port 3000)   │
    └────┬──────────────────────┘
         │ POST /api/connection-details
    ┌────▼──────────────────────┐
    │  Flask API Server         │
    │  (Port 8019)              │
    │  Generates LiveKit tokens │
    └────┬──────────────────────┘
         │
    ┌────▼──────────────────────┐
    │  LiveKit Cloud            │
    │  (wss://your-url)         │
    └────┬──────────────────────┘
         │
    ┌────▼──────────────────────┐
    │  Python Voice Agent       │
    │  (RTC, LLM, STT, TTS)     │
    └──────────────────────────┘
```

---

## Documentation

- **AGENTS.md** - Complete development guide
- **REACT_INTEGRATION_GUIDE.md** - React integration details
- **README.md** - Project overview

---

## Getting Help

- Check logs in console output
- Review AGENTS.md troubleshooting section
- Check browser developer console for frontend errors
- Verify `.env.local` configuration
- Test API endpoint with curl

---

**For detailed instructions, see AGENTS.md**
