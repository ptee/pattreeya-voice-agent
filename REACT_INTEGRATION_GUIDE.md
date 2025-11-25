# React Frontend Integration Guide

This document explains how the React frontend has been integrated with the Python LiveKit agent backend.

## Architecture Overview

The integration consists of three main components:

1. **React Frontend (Next.js)** - Running on port 3000
   - Provides the web UI for voice agent interaction
   - Makes API calls to the Python backend for token generation
   - Built with Next.js 15, TypeScript, and Tailwind CSS

2. **Flask API Server** - Running on port 8019
   - Serves the `/api/connection-details` endpoint
   - Generates LiveKit access tokens for the frontend
   - Handles CORS for cross-origin requests

3. **LiveKit Agent Server** - Running on the agent's designated port
   - Handles the voice agent logic and RTC sessions
   - Processes user interactions via LiveKit rooms

```
┌──────────────────┐
│  React Frontend  │
│   (port 3000)    │
└────────┬─────────┘
         │
    POST /api/connection-details
         │
         ↓
┌──────────────────────────┐
│  Flask API Server        │
│  (port 8019)             │
│  - Token Generation      │
│  - CORS Handling         │
└────────┬─────────────────┘
         │
         ↓
┌──────────────────────────┐
│  LiveKit Servers         │
│  (wss://...)             │
│  - Room Management       │
│  - RTC Session Handling  │
└──────────────────────────┘
         │
         ↓
┌──────────────────────────┐
│  Python Agent Server     │
│  - Voice Agent Logic     │
│  - LLM Integration       │
└──────────────────────────┘
```

## Files Changed/Added

### 1. `/web` Directory
- **Location**: `agent-starter-python/web/`
- **Content**: Complete React/Next.js frontend application
- **Built**: `pnpm build` has been executed, creating `.next/` build output
- **Configuration**: `.env.local` updated to point to Python API server

### 2. `src/web_server.py` (NEW)
- **Purpose**: Flask web server for API endpoints
- **Functionality**:
  - Serves `/api/connection-details` POST endpoint
  - Generates LiveKit access tokens
  - Handles CORS for cross-origin requests
  - Can optionally serve static frontend files

### 3. `src/agent.py` (MODIFIED)
- **Changes**:
  - Added import: `from web_server import run_web_server`
  - Added Flask API server startup (port 8019)
  - Added Next.js frontend server startup (port 3000)
  - Both run as background processes while LiveKit agent server runs

### 4. `pyproject.toml` (MODIFIED)
- **Dependencies Added**:
  - `flask>=3.0`
  - `flask-cors>=4.0`
  - `livekit-server-sdk>=0.11`

### 5. `web/.env.local` (MODIFIED)
- **Configuration**:
  - `NEXT_PUBLIC_CONN_DETAILS_ENDPOINT="http://localhost:8019/api/connection-details"`
  - Points React frontend to Python backend API

## Running the Integrated System

### Step 1: Install Python Dependencies

```bash
cd /home/pt/Projects/LLMs/voice-agents/agent-starter-python
uv sync
```

This installs all Python dependencies including Flask, Flask-CORS, and LiveKit SDK.

### Step 2: Run the Agent with Integrated Frontend

```bash
uv run python src/agent.py dev
```

This command will start:
1. **Flask API Server** on port 8019 (token generation)
2. **Next.js Frontend** on port 3000 (web UI)
3. **LiveKit Agent Server** (voice agent logic)

You should see output like:
```
✓ API server started on http://0.0.0.0:8019
✓ Next.js server started on http://0.0.0.0:3000
```

### Step 3: Access the Frontend

Open your browser and navigate to:
```
http://localhost:3000
```

You should see the Pattreeya voice agent interface.

## How It Works

### Frontend to Backend Communication Flow

1. **User clicks "Start call"** on the React frontend
2. **Frontend requests token**:
   ```javascript
   POST http://localhost:8019/api/connection-details
   Body: { "room_config": { "agents": [...] } }
   ```
3. **Flask API generates token**:
   - Creates LiveKit access token with video grants
   - Generates unique room and participant names
   - Returns connection details to frontend
4. **Frontend receives response**:
   ```json
   {
     "serverUrl": "wss://voiceagent-46wqrz65.livekit.cloud",
     "roomName": "voice_assistant_room_XXXX",
     "participantToken": "eyJ0eXAi...",
     "participantName": "user"
   }
   ```
5. **Frontend connects to LiveKit** using the token
6. **LiveKit Agent** joins the room and handles conversation

## Ports and Services

| Service | Port | Purpose |
|---------|------|---------|
| React Frontend | 3000 | Web UI for voice agent |
| Flask API Server | 8019 | Token generation endpoint |
| LiveKit Agent | Agent Default | Voice agent RTC sessions |
| LiveKit Cloud | wss:// | Real-time communication |

## Troubleshooting

### Issue: "Cannot GET /" on port 3000

**Cause**: Next.js server hasn't started or failed to start.

**Solution**:
```bash
cd web
pnpm install
pnpm start
```

Or check the agent.py logs for Next.js startup errors.

### Issue: "Failed to fetch connection details"

**Cause**: Flask API server not running or CORS error.

**Solution**:
1. Check that port 8019 is available: `lsof -i :8019`
2. Verify Flask server is running: `curl http://localhost:8019/health`
3. Check browser console for CORS errors
4. Ensure `NEXT_PUBLIC_CONN_DETAILS_ENDPOINT` is set correctly in `web/.env.local`

### Issue: "WebSocket connection failed"

**Cause**: Invalid LiveKit credentials or URL.

**Solution**:
1. Verify `.env.local` has correct `LIVEKIT_URL` and credentials
2. Test connection: `curl -v wss://your-livekit-url/health`

## Environment Variables

### In `agent-starter-python/.env.local`
```env
LIVEKIT_URL=wss://voiceagent-46wqrz65.livekit.cloud
LIVEKIT_API_KEY=your_api_key
LIVEKIT_API_SECRET=your_api_secret
```

### In `agent-starter-python/web/.env.local`
```env
NEXT_PUBLIC_LIVEKIT_URL=wss://voiceagent-46wqrz65.livekit.cloud
NEXT_PUBLIC_CONN_DETAILS_ENDPOINT=http://localhost:8019/api/connection-details
```

## Development Notes

### Rebuilding the Frontend

If you modify React files in `web/`, rebuild:
```bash
cd web
pnpm build
```

Then restart the agent:
```bash
uv run python src/agent.py dev
```

### API Endpoint Reference

**POST `/api/connection-details`**

Request:
```json
{
  "room_config": {
    "agents": [
      {
        "agent_name": "optional-agent-name"
      }
    ]
  }
}
```

Response (200):
```json
{
  "serverUrl": "wss://livekit.cloud",
  "roomName": "voice_assistant_room_XXXX",
  "participantToken": "jwt-token-here",
  "participantName": "user"
}
```

Error Response (500):
```json
{
  "error": "Error message here"
}
```

### Testing the API with curl

```bash
curl -X POST http://localhost:8019/api/connection-details \
  -H "Content-Type: application/json" \
  -d '{"room_config": {"agents": []}}'
```

## Next Steps

1. **Test the Integration**:
   - Navigate to http://localhost:3000
   - Click "Start call"
   - Verify WebRTC connection is established
   - Test voice interaction with the agent

2. **Customize the Frontend**:
   - Edit files in `web/components/`
   - Update branding in `web/app-config.ts`
   - Modify styling with Tailwind CSS

3. **Enhance the Backend**:
   - Add more API endpoints to `web_server.py`
   - Integrate additional features with the agent
   - Add logging and monitoring

## Known Limitations

1. The Flask API server runs in a background thread alongside the LiveKit agent
2. Frontend requires explicit port configuration for development
3. CORS is enabled for all origins on API endpoints (should be restricted in production)

## Production Deployment

For production deployment:

1. Use a reverse proxy (nginx, Apache) to:
   - Serve Next.js frontend on port 80/443
   - Forward `/api/*` requests to Flask on port 8019
   - Configure proper CORS headers

2. Run Flask with a production WSGI server (Gunicorn, uWSGI)

3. Use environment-based configuration for ports and origins

4. Enable HTTPS/WSS for all connections

Example nginx config:
```nginx
server {
    listen 80;
    server_name yourdomain.com;

    location / {
        proxy_pass http://localhost:3000;
    }

    location /api/ {
        proxy_pass http://localhost:8019;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

## Support

For issues with:
- **React Frontend**: See `web/CLAUDE.md`
- **Python Agent**: See `AGENTS.md`
- **LiveKit**: Visit https://docs.livekit.io
