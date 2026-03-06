FROM node:22-bookworm
ENV NODE_ENV=production
RUN npm install -g pnpm@10.2.0

WORKDIR /app

# Install ALL deps (including devDeps so tsc is available)
COPY package.json pnpm-lock.yaml ./
RUN pnpm install --frozen-lockfile

COPY src/ ./src/
COPY tsconfig.json ./

# Compile TypeScript → dist/
RUN pnpm build

# Download LiveKit turn-detector model files into the image at build time
# so the container starts without needing network access for model downloads.
RUN node dist/index.js download-files

RUN addgroup --gid 1001 nodejs && adduser --uid 1001 --ingroup nodejs --disabled-password --gecos "" agent
RUN chown -R agent:nodejs /app
USER agent

EXPOSE 8019

CMD ["node", "dist/index.js", "start"]
