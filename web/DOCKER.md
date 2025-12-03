# Docker Setup for Voice Agent Frontend

This guide explains how to build and run the Next.js voice agent frontend in Docker. The frontend uses a multi-stage build process for optimal image size and production readiness.

## Overview

The Dockerfile uses a **multi-stage build**:
1. **Builder stage** (node:22-alpine): Compiles TypeScript and bundles Next.js
2. **Runtime stage** (node:22-alpine): Runs the optimized application with minimal dependencies

**Key features:**
- Node.js 22 Alpine (lightweight, ~150MB final image)
- Non-root user (`nextjs`) for security
- Health check for monitoring
- Optimized for LiveKit integration

## Quick Start

### Build the Docker Image

```bash
# From the web/ directory
docker build -t ptee-voice-agent-frontend:latest .

# Or with a specific semantic tag
docker build -t ptee-voice-agent-frontend:v0.1.0 .

# Build with BuildKit for faster builds (optional)
DOCKER_BUILDKIT=1 docker build -t ptee-voice-agent-frontend:latest .
```

### Run the Container

```bash
# Basic run on port 3001
docker run -p 3001:3000 ptee-voice-agent-frontend:latest

# Run with minimal required environment variables
docker run -p 3001:3000 \
  -e NEXT_PUBLIC_LIVEKIT_URL=wss://your-livekit-server.cloud \
  ptee-voice-agent-frontend:latest

# Run with full configuration (backend integration)
docker run -p 3001:3000 \
  -e NEXT_PUBLIC_LIVEKIT_URL=wss://voiceagent-46wqrz65.livekit.cloud \
  -e NEXT_PUBLIC_CONN_DETAILS_ENDPOINT=http://your-backend:8019/api/connection-details \
  ptee-voice-agent-frontend:latest

# Run in detached mode with health monitoring
docker run -d \
  --name ptee-frontend \
  -p 3001:3000 \
  -e NEXT_PUBLIC_LIVEKIT_URL=wss://voiceagent-46wqrz65.livekit.cloud \
  -e NEXT_PUBLIC_CONN_DETAILS_ENDPOINT=http://localhost:8019/api/connection-details \
  --restart unless-stopped \
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

To enable container health monitoring, add a health check to the Dockerfile:

```dockerfile
HEALTHCHECK --interval=30s --timeout=3s --start-period=40s --retries=3 \
    CMD node -e "require('http').get('http://localhost:3000', (r) => {if (r.statusCode !== 200) throw new Error(r.statusCode)})"
```

Check container health status:

```bash
# View health status in ps output
docker ps --format="{{.Names}}\t{{.Status}}"

# Example output:
# ptee-frontend  Up 2 minutes (healthy)
```

The health check:
- Runs every 30 seconds
- Waits 40 seconds before first check (allows startup time)
- Times out after 3 seconds
- Marks unhealthy after 3 consecutive failures

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

### Dockerfile Build Process

The build uses a multi-stage approach optimized for production:

**Builder Stage:**
- Uses `node:22-alpine` for minimal footprint
- Installs pnpm 10.2.0 globally
- Uses `pnpm install --frozen-lockfile` for reproducible builds
- Runs `pnpm build` to compile TypeScript and bundle Next.js

**Runtime Stage:**
- Copies only necessary files (`.next`, `node_modules`, `public`)
- Creates non-root `nextjs` user for security
- Runs as PID 1 with `node_modules/.bin/next start`
- Minimal attack surface with only runtime dependencies

### Custom Node Arguments

To modify memory or other Node.js settings, update the Dockerfile's CMD:

```dockerfile
# For increased heap size
CMD ["node", "--max-old-space-size=1024", "node_modules/.bin/next", "start"]

# For debugging (not recommended in production)
CMD ["node", "--inspect=0.0.0.0:9229", "node_modules/.bin/next", "start"]
```

### Custom Next.js Configuration

The `next.config.ts` is minimal but can be extended:

```typescript
import type { NextConfig } from 'next';

const nextConfig: NextConfig = {
  eslint: {
    ignoreDuringBuilds: true,
  },
  // Add custom config for specific needs:
  // output: 'export', // For static export (incompatible with API routes)
  // productionBrowserSourceMaps: false, // Reduce bundle size
  // compress: true, // Already default in production
  // swcMinify: true, // Already default in production
};

export default nextConfig;
```

### Multi-Architecture Build

Build for multiple architectures:

```bash
docker buildx build --platform linux/amd64,linux/arm64 -t ptee-voice-agent-frontend:latest .
```

### Dependency Management

The project uses **pnpm 10.2.0** with a locked dependency file:

```bash
# Lock file must be present for reproducible builds
# Committed to git: pnpm-lock.yaml

# To update dependencies (be cautious in production):
pnpm update --latest
pnpm install --frozen-lockfile  # Rebuild with lock

# Rebuild Docker image after dependency updates
docker build -t ptee-voice-agent-frontend:latest .
```

Key dependencies in production:
- `next` 15.5.2 - React framework
- `react` 19.0.0 - UI library
- `@livekit/components-react` 2.9.15 - LiveKit UI components
- `livekit-server-sdk` 2.13.2 - Token generation
- `tailwindcss` 4.x - CSS framework

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
      livenessProbe:
        httpGet:
          path: /
          port: 3000
        initialDelaySeconds: 40
        periodSeconds: 30
      resources:
        requests:
          cpu: 100m
          memory: 256Mi
        limits:
          cpu: 500m
          memory: 512Mi
```

## Summary

| Task                        | Command                                                               |
| --------------------------- | --------------------------------------------------------------------- |
| Build image                 | `docker build -t ptee-voice-agent-frontend:latest .`                 |
| Run container               | `docker run -p 3001:3000 ptee-voice-agent-frontend:latest`            |
| Use docker-compose          | `docker-compose up -d`                                                |
| View logs                   | `docker logs ptee-frontend` or `docker-compose logs -f frontend`      |
| Stop container              | `docker stop ptee-frontend`                                           |
| Remove container            | `docker rm ptee-frontend`                                             |
| Check health                | `docker ps --format="{{.Names}}\t{{.Status}}"`                        |
| Debug interactive shell     | `docker run -it ptee-voice-agent-frontend:latest /bin/sh`            |
| Clean up unused resources   | `docker system prune`                                                 |

For production deployments, refer to the **Production Checklist** section above and ensure all environment variables are properly configured.
