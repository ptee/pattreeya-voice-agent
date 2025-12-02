# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository Overview

This is a **React + Next.js** starter template for building real-time voice agent interfaces using [LiveKit Agents](https://docs.livekit.io/agents). It provides a web-based UI for voice interaction with AI agents, featuring camera streaming, screen sharing, and avatar integration.

The project uses:

- **Framework**: Next.js 15 (App Router) with TypeScript
- **UI Components**: LiveKit React Components, Radix UI primitives
- **Styling**: Tailwind CSS v4 with PostCSS
- **Package Manager**: pnpm 9.15.9
- **Code Quality**: ESLint, Prettier with import sorting

## Architecture and Data Flow

### High-Level Architecture

```
┌─────────────────────────────────────────┐
│        Next.js Frontend (React)          │
│                                         │
│  ┌───────────────────────────────────┐ │
│  │     App Component Tree             │ │
│  │  (app-config.ts configuration)    │ │
│  └───────────────────────────────────┘ │
│            ↓                            │
│  ┌───────────────────────────────────┐ │
│  │  ConnectionProvider (useConnection)│ │
│  │  - Manages LiveKit session state   │ │
│  │  - Token generation & refresh      │ │
│  └───────────────────────────────────┘ │
│            ↓                            │
│  ┌───────────────────────────────────┐ │
│  │  LiveKit SessionProvider          │ │
│  │  (from @livekit/components-react) │ │
│  └───────────────────────────────────┘ │
└──────────────────────┬──────────────────┘
                       │
         POST to /api/connection-details
                       ↓
┌─────────────────────────────────────────┐
│    Next.js API Route (Node.js Backend)   │
│    app/api/connection-details/route.ts  │
│                                         │
│  - Creates JWT access token            │
│  - Generates room & participant IDs     │
│  - Returns LiveKit credentials          │
└──────────────────────┬──────────────────┘
                       │
                       ↓
        ┌──────────────────────────┐
        │   LiveKit Server (WSS)    │
        │  Manages rooms & sessions │
        └──────────────────────────┘
                       │
                       ↓
        ┌──────────────────────────┐
        │  Agent (Python/Node.js)   │
        │  AI voice interaction     │
        └──────────────────────────┘
```

### Key Component Flow

1. **User Interaction**: User clicks "Start call" on welcome page (WelcomeView)
2. **Connection**: `useConnection()` hook calls `/api/connection-details` API route
3. **Token Generation**: API creates JWT with LiveKit credentials and room configuration
4. **Session Start**: React receives token, connects to LiveKit room via WebSocket
5. **Media Setup**: Camera/microphone streams initialized via LiveKit SDK
6. **Agent Communication**: Messages flow between user client and agent via LiveKit protocol
7. **Disconnection**: Session end triggers UI state reset and cleanup

## Core Modules and Patterns

### App Configuration (`app-config.ts`)

Centralized configuration interface for branding and feature toggles:

```typescript
export interface AppConfig {
  pageTitle: string; // HTML page title
  pageDescription: string; // Meta description
  companyName: string; // Branding text
  supportsChatInput: boolean; // Enable text input feature
  supportsVideoInput: boolean; // Enable camera feature
  supportsScreenShare: boolean; // Enable screen sharing
  isPreConnectBufferEnabled: boolean; // Show preconnect animations
  logo: string; // Light theme logo path
  logoDark?: string; // Dark theme logo path
  accent: string; // Primary color (light)
  accentDark?: string; // Primary color (dark)
  startButtonText: string; // CTA button label
  sandboxId?: string; // LiveKit Cloud Sandbox ID
  agentName?: string; // Agent identifier
}
```

Update `APP_CONFIG_DEFAULTS` to customize the UI without code changes.

### Connection Management (`hooks/useConnection.tsx`)

Custom context-based hook managing LiveKit session lifecycle:

- **TokenSource**: Resolves JWT by calling `/api/connection-details` endpoint
- **Session State**: `isConnectionActive` tracks user connection status
- **Disconnect Transition**: Smooth animation state before cleanup
- **Error Handling**: Captured via `useAgentErrors()` hook

```typescript
// Usage in components
const { isConnectionActive, connect, startDisconnectTransition } = useConnection();
```

### LiveKit API Integration (`app/api/connection-details/route.ts`)

Server-side endpoint generating secure JWT tokens:

**Request Body**:

```json
{
  "room_config": {
    "agents": [{ "agent_name": "your-agent" }]
  }
}
```

**Response**:

```json
{
  "serverUrl": "wss://livekit.example.com",
  "roomName": "voice_assistant_room_XXXX",
  "participantToken": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "participantName": "user"
}
```

**Key Details**:

- Token TTL set to 15 minutes
- Grants: publish, subscribe, publish data
- Room/participant names auto-generated with random suffixes
- Requires environment variables: `LIVEKIT_API_KEY`, `LIVEKIT_API_SECRET`, `LIVEKIT_URL`

### Component Organization

```
components/
├── app/                          # Application-specific views
│   ├── app.tsx                  # Root app wrapper
│   ├── welcome-view.tsx         # Pre-connection landing page
│   ├── session-view.tsx         # Main voice interface
│   ├── view-controller.tsx      # View state transitions
│   ├── chat-transcript.tsx      # Message history display
│   ├── tile-layout.tsx          # Video grid layout
│   ├── theme-toggle.tsx         # Dark/light mode toggle
│   └── preconnect-message.tsx   # Loading animation
└── livekit/                      # UI primitives & LiveKit-specific
    ├── agent-control-bar/       # Audio/video controls
    ├── button.tsx               # Styled button component
    ├── toggle.tsx               # Radio/toggle controls
    ├── select.tsx               # Dropdown selector
    ├── alert.tsx                # Alert dialogs
    ├── toaster.tsx              # Toast notifications
    ├── chat-entry.tsx           # Single message component
    └── scroll-area/             # Custom scroll behavior
```

### Styling System

- **Tailwind CSS v4**: Utility-first styling with `@tailwindcss/postcss` plugin
- **Theme Variables**: Light/dark theme via CSS custom properties
- **Motion Effects**: Framer Motion for animations (fade, slide transitions)
- **UI Library**: Radix UI primitives under `components/livekit/` (select, toggle)

## Environment Configuration

### Required Environment Variables (`.env.local`)

```env
# LiveKit Server Credentials
LIVEKIT_API_KEY=<your_livekit_api_key>
LIVEKIT_API_SECRET=<your_livekit_api_secret>
LIVEKIT_URL=wss://<project-subdomain>.livekit.cloud

# Optional: Custom endpoints
NEXT_PUBLIC_CONN_DETAILS_ENDPOINT=  # Override token endpoint
NEXT_PUBLIC_APP_CONFIG_ENDPOINT=    # Override config endpoint
SANDBOX_ID=                         # LiveKit Cloud Sandbox ID
```

Copy `.env.example` and fill in values. The API route uses server-side environment variables (not prefixed with `NEXT_PUBLIC_`).

## Common Commands

### Development

```bash
# Install dependencies (uses pnpm)
pnpm install

# Start dev server with Turbopack (port 3000)
pnpm dev

# Build for production
pnpm build

# Start production server
pnpm start
```

### Code Quality

```bash
# Lint TypeScript and JSX
pnpm lint

# Check formatting without changes
pnpm format:check

# Apply formatting and import sorting
pnpm format

# Fix linting issues (when possible)
pnpm lint --fix
```

### Single Feature Testing

To test a specific component or hook:

1. **Component isolation**: Use Next.js UI routes (`app/ui/page.tsx`) for standalone testing
2. **Hook testing**: Call from a test component and verify state changes via React DevTools
3. **API testing**: Use `curl` or Postman to POST to `/api/connection-details`
   ```bash
   curl -X POST http://localhost:3000/api/connection-details \
     -H "Content-Type: application/json" \
     -d '{"room_config":{"agents":[{"agent_name":"test-agent"}]}}'
   ```

## Key Patterns and Conventions

### React Hooks & Context

- **`'use client'` directive**: All interactive components use client-side rendering
- **Context for state**: `ConnectionProvider` wraps app with `SessionProvider`
- **Custom hooks**: `useConnection()`, `useAgentErrors()`, `useDebug()` abstract LiveKit logic
- **Session data**: Accessed via `useSessionContext()` and `useSessionMessages()` from `@livekit/components-react`

### TypeScript Patterns

- **Type safety**: `AppConfig` interface defines all configuration
- **Strict mode enabled**: `tsconfig.json` enforces full type checking
- **Path aliases**: `@/*` maps to root directory for cleaner imports

### Error Handling

- **Agent failures**: `useAgentErrors()` watches `agent.state === 'failed'`
- **Connection errors**: Caught in `ConnectionProvider.tokenSource` and shown via toast
- **User feedback**: Failures display via `toastAlert()` with guidance links

### Styling Conventions

- **Tailwind utility classes**: Primary styling method (no custom CSS files)
- **Dark mode**: System preference auto-detected via `next-themes`
- **Animation**: Motion component wrapping for complex transitions
- **Responsive design**: Mobile-first, tested at 375px+ widths

## Build and Deployment

### Development Workflow

1. **Code changes**: Edit files in `components/`, `app/`, `hooks/`, `lib/`
2. **Type checking**: TypeScript automatically validates on save
3. **Lint on commit**: ESLint rules enforce consistency
4. **Hot reload**: `pnpm dev` rebuilds instantly on file changes

### Production Build

```bash
pnpm build
pnpm start
```

The build:

- Compiles TypeScript → JavaScript
- Bundles dependencies
- Optimizes CSS and images
- Generates static exports where applicable

### Docker Deployment

The frontend includes a production-ready Dockerfile with multi-stage build optimization.

**Files:**

- `Dockerfile`: Multi-stage build (builder + runtime)
- `.dockerignore`: Excludes unnecessary files from build context
- `docker-compose.yml`: Complete compose setup with environment configuration
- `DOCKER.md`: Comprehensive Docker documentation

**Quick Start:**

```bash
# Build image
docker build -t ptee-voice-agent-frontend:latest .

# Run with docker-compose (uses port 3001 by default)
docker-compose up -d

# Or run standalone on port 3001
docker run -p 3001:3000 \
  -e NEXT_PUBLIC_LIVEKIT_URL=wss://voiceagent-46wqrz65.livekit.cloud \
  -e NEXT_PUBLIC_CONN_DETAILS_ENDPOINT=http://localhost:8019/api/connection-details \
  ptee-voice-agent-frontend:latest

# Access at: http://localhost:3001
```

**Key Features:**

- Multi-stage build reduces final image size (~150MB)
- Alpine Linux base for minimal footprint
- Health check configured for production monitoring
- Environment variables for LiveKit and backend configuration
- Supports local development and cloud deployment

**Environment Variables for Docker:**

| Variable                            | Required | Description                                                    |
| ----------------------------------- | -------- | -------------------------------------------------------------- |
| `NEXT_PUBLIC_LIVEKIT_URL`           | Yes      | LiveKit WebSocket server URL                                   |
| `NEXT_PUBLIC_CONN_DETAILS_ENDPOINT` | No       | Backend token endpoint (defaults to `/api/connection-details`) |
| `OPENAI_API_KEY`                    | No       | OpenAI API key (if needed by frontend)                         |

**Docker Compose with Backend:**

To run frontend and backend together, uncomment the `backend` service in `docker-compose.yml`:

```yaml
services:
  frontend:
    # Frontend configuration
    environment:
      NEXT_PUBLIC_CONN_DETAILS_ENDPOINT: http://backend:8019/api/connection-details

  backend:
    build:
      context: ../
      dockerfile: Dockerfile
    # Backend will run on port 8019
```

Then run: `docker-compose up -d`

**See `DOCKER.md` for:**

- Detailed setup and troubleshooting
- Network configuration (local, Docker, production)
- Health check configuration
- Performance optimization
- Kubernetes integration

### Deployment Targets

#### Vercel (Recommended)

- Automatic deploys on git push
- Zero-configuration for Next.js
- See `../vercel.json` if custom config needed

#### Render.com

- Uses `render.yaml` in the web/ directory for configuration
- Automatically enables pnpm via corepack
- Build command: `pnpm install && pnpm build`
- Start command: `pnpm start`
- Requires environment variables in `render.yaml`:
  ```yaml
  envVars:
    - key: NEXT_PUBLIC_LIVEKIT_URL
      value: wss://voiceagent-46wqrz65.livekit.cloud
    - key: NEXT_PUBLIC_CONN_DETAILS_ENDPOINT
      value: https://your-backend-url.com/api/connection-details
  ```

**Setup:**

1. In Render.com dashboard, create a new "Web Service"
2. Connect your GitHub repository
3. Set the root directory to `web`
4. Render will automatically detect `web/render.yaml` and use it for configuration
5. Push to main branch to auto-deploy

#### Docker

- Use included `Dockerfile` and `docker-compose.yml` (see Docker Deployment section above)
- Multi-stage build optimized for production
- Run: `docker build -t ptee-voice-agent-frontend:latest web/`

#### Docker Compose

- Multi-service setup with backend (`docker-compose.yml`)
- Run: `docker-compose up -d`

#### Kubernetes

- Container-ready with health checks configured
- Use Docker image built from Dockerfile

#### LiveKit Cloud Sandbox

- Direct deployment via `lk app create --template agent-starter-react`

## Important File Locations

- **Config**: `app-config.ts` (branding, features)
- **API routes**: `app/api/*/route.ts` (token generation, config)
- **Main UI**: `components/app/*.tsx` (views, layouts)
- **Hooks**: `hooks/*.tsx` (connection, errors, debug)
- **Utilities**: `lib/utils.ts` (cn() class merger)
- **Styles**: `app/globals.css` (Tailwind directives)
- **Type definitions**: `app-config.ts`, inline `interface` definitions

## Testing Locally with Mock Agent

To test without a real agent:

1. Start dev server: `pnpm dev`
2. Set dummy environment variables in `.env.local`:
   ```env
   LIVEKIT_API_KEY=test
   LIVEKIT_API_SECRET=test
   LIVEKIT_URL=ws://localhost:5432
   ```
3. Use LiveKit CLI to start a local server:
   ```bash
   livekit-cli start-room localhost:5432
   ```
4. Connect via UI at `http://localhost:3000`

For detailed agent setup, see [LiveKit Agents documentation](https://docs.livekit.io/agents/start/voice-ai/).
