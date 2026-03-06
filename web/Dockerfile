# Multi-stage build for Next.js frontend
# Stage 1: Builder
FROM node:22-alpine AS builder

WORKDIR /app

# Install pnpm
RUN npm install -g pnpm@10.2.0

# Copy package files
COPY package.json pnpm-lock.yaml ./

# Install dependencies
RUN pnpm install --frozen-lockfile

# Copy ALL source files (including tsconfig.json, config, etc)
COPY . .

# Build the Next.js application
RUN pnpm build

# Stage 2: Runtime
FROM node:22-alpine

WORKDIR /app

ENV NODE_ENV=production

# Install pnpm for running next start
RUN npm install -g pnpm@10.2.0

# Copy package files
COPY package.json pnpm-lock.yaml ./

# Copy built application and dependencies from builder
COPY --from=builder /app/.next ./.next
COPY --from=builder /app/node_modules ./node_modules
COPY --from=builder /app/public ./public

# Create non-root user for security
RUN addgroup -g 1001 -S nodejs && \
    adduser -S nextjs -u 1001 && \
    chown -R nextjs:nodejs /app

USER nextjs

# Expose port 3002 (matches package.json "start": "next start -p 3002")
EXPOSE 3002

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
  CMD curl -f http://localhost:3002/ || exit 1

# Start the Next.js application on port 3002
CMD ["node_modules/.bin/next", "start", "-p", "3002"]