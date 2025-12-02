# Docker Setup for Frontend

This guide explains how to build and run the Next.js frontend in Docker.

## Quick Start

### Build the Docker Image

```bash
# From the web/ directory
docker build -t ptee-voice-agent-frontend:latest .

# Or with a specific tag
docker build -t ptee-voice-agent-frontend:v0.1.0 .
```

### Run the Container

```bash
# Basic run on port 3001 (default from docker-compose.yml)
docker run -p 3001:3000 ptee-voice-agent-frontend:latest

# Or use port 3000 if available
docker run -p 3000:3000 ptee-voice-agent-frontend:latest

# With custom environment variables
docker run -p 3001:3000 \
  -e NEXT_PUBLIC_LIVEKIT_URL=wss://your-livekit-server.cloud \
  -e NEXT_PUBLIC_CONN_DETAILS_ENDPOINT=http://your-backend:8019/api/connection-details \
  ptee-voice-agent-frontend:latest

# Run in detached mode with a name
docker run -d \
  --name ptee-frontend \
  -p 3001:3000 \
  -e NEXT_PUBLIC_LIVEKIT_URL=wss://voiceagent-46wqrz65.livekit.cloud \
  -e NEXT_PUBLIC_CONN_DETAILS_ENDPOINT=http://localhost:8019/api/connection-details \
  ptee-voice-agent-frontend:latest
```

## Using Docker Compose

### Basic Usage

```bash
# Build and run frontend only
docker-compose up -d

# View logs
docker-compose logs -f frontend

# Stop and remove containers
docker-compose down
```

### With Custom Environment Variables

Create a `.env` file in the web/ directory:

```env
NEXT_PUBLIC_LIVEKIT_URL=wss://voiceagent-46wqrz65.livekit.cloud
NEXT_PUBLIC_CONN_DETAILS_ENDPOINT=http://localhost:8019/api/connection-details
OPENAI_API_KEY=sk-...
```

Then run:

```bash
docker-compose up -d
```

The `.env` file will be automatically loaded.

### Running Backend and Frontend Together

Uncomment the `backend` service in `docker-compose.yml`:

```yaml
services:
  frontend:
    # ... existing config

  backend:
    build:
      context: ../
      dockerfile: Dockerfile
    # ... rest of config
```

Then run:

```bash
docker-compose up -d
```

This will start both services and they can communicate via service names:

- Frontend calls `http://backend:8019/api/connection-details`

## Environment Variables

### Required for Frontend

| Variable                            | Description                               | Example                                        |
| ----------------------------------- | ----------------------------------------- | ---------------------------------------------- |
| `NEXT_PUBLIC_LIVEKIT_URL`           | LiveKit WebSocket URL                     | `wss://voiceagent-46wqrz65.livekit.cloud`      |
| `NEXT_PUBLIC_CONN_DETAILS_ENDPOINT` | Backend API endpoint for token generation | `http://localhost:8019/api/connection-details` |

### Optional

| Variable         | Description                                   | Default |
| ---------------- | --------------------------------------------- | ------- |
| `OPENAI_API_KEY` | OpenAI API key (if frontend uses it directly) | Empty   |

## Network Configuration

### Running Locally

When running frontend and backend on the same machine:

```
Frontend (3000) → Backend (8019)
```

Use this endpoint:

```
NEXT_PUBLIC_CONN_DETAILS_ENDPOINT=http://localhost:8019/api/connection-details
```

### Docker Network

When using Docker Compose, containers can communicate via service names:

```yaml
services:
  frontend:
    # Calls http://backend:8019/...
  backend:
    # Exposed on port 8019
```

Update `docker-compose.yml` backend service and set:

```
NEXT_PUBLIC_CONN_DETAILS_ENDPOINT=http://backend:8019/api/connection-details
```

### Production Deployment

Use the actual deployed URL:

```
NEXT_PUBLIC_CONN_DETAILS_ENDPOINT=https://api.yourdomain.com/api/connection-details
```

## Health Check

The container includes a health check that:

- Runs every 30 seconds
- Waits 40 seconds before first check (start-period)
- Times out after 3 seconds
- Retries up to 3 times before marking unhealthy

Check container health:

```bash
docker ps --format="{{.Names}}\t{{.Status}}"
```

## Troubleshooting

### Port Already in Use

```bash
# Find what's using port 3000
lsof -i :3000

# Use a different port
docker run -p 3001:3000 ptee-voice-agent-frontend:latest
```

### Container Won't Start

```bash
# Check logs
docker logs ptee-frontend

# Run with interactive terminal to debug
docker run -it ptee-voice-agent-frontend:latest /bin/sh
```

### Can't Reach Backend

If running backend separately, ensure:

1. Backend is running on the correct port (8019)
2. Firewall allows connections
3. Environment variable uses correct URL:
   ```
   NEXT_PUBLIC_CONN_DETAILS_ENDPOINT=http://your-backend-ip:8019/api/connection-details
   ```

### Environment Variables Not Working

Ensure variables are prefixed with `NEXT_PUBLIC_` for them to be visible to the frontend:

```bash
# This will be available in the browser
NEXT_PUBLIC_LIVEKIT_URL=...

# This will NOT be available (backend only)
SECRET_KEY=...
```

## Performance Optimization

### Reduce Image Size

The multi-stage build produces a smaller image by:

- Using `node:22-alpine` (lightweight base image)
- Only copying build artifacts to runtime stage
- Not including node_modules in final image

Current approximate sizes:

- Builder stage: ~800MB (temporary)
- Final image: ~150MB

### Layer Caching

To speed up rebuilds:

```bash
# Docker caches layers, so changing source code only rebuilds necessary layers
# Dependencies are cached as long as package.json and pnpm-lock.yaml don't change
docker build -t ptee-voice-agent-frontend:latest .
```

## Production Checklist

- [ ] Environment variables set correctly
- [ ] LiveKit URL points to production server
- [ ] Backend endpoint is correct and accessible
- [ ] Container health check is passing
- [ ] Logs are monitored
- [ ] Image is scanned for vulnerabilities
- [ ] Resource limits are set (CPU, memory)
- [ ] Restart policy is configured

## Advanced Configuration

### Custom Node Arguments

Modify the Dockerfile's CMD to pass Node.js arguments:

```dockerfile
CMD ["node", "--max-old-space-size=1024", "server.js"]
```

### Custom Next.js Configuration

Update `next.config.ts` for Docker-specific settings:

```typescript
export default {
  output: 'standalone', // Already configured for docker
  // Add other Next.js config here
};
```

### Multi-Architecture Build

Build for multiple architectures:

```bash
docker buildx build --platform linux/amd64,linux/arm64 -t ptee-voice-agent-frontend:latest .
```

## Integration with Kubernetes

For Kubernetes deployment, see the main project README for K8s manifests.

Basic service example:

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: ptee-frontend
spec:
  containers:
    - name: frontend
      image: ptee-voice-agent-frontend:latest
      ports:
        - containerPort: 3000
      env:
        - name: NEXT_PUBLIC_LIVEKIT_URL
          value: 'wss://voiceagent-46wqrz65.livekit.cloud'
        - name: NEXT_PUBLIC_CONN_DETAILS_ENDPOINT
          value: 'http://backend:8019/api/connection-details'
```
