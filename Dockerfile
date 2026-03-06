FROM node:22-bookworm
ENV NODE_ENV=production
# The livekit plugin resolves its cache via Node's os.homedir(), NOT HF_HOME.
# Setting HOME=/app means homedir() returns /app in both the build step (root)
# and at runtime (agent user), so download-files and the running worker both
# use /app/.cache/huggingface/hub/ — which is covered by the chown below.
ENV HOME=/app
RUN npm install -g pnpm@10.2.0
RUN corepack enable

WORKDIR /app

# Install ALL deps (including devDeps so tsc is available)
COPY package.json pnpm-lock.yaml ./
RUN pnpm install --frozen-lockfile

COPY src/ ./src/
COPY tsconfig.json ./
COPY . .

# Compile TypeScript → dist/
RUN pnpm build

# Download LiveKit turn-detector model files into /app/.cache (inside HF_HOME)
# so the chown below makes them readable by the agent user at runtime.
RUN node dist/index.js download-files

RUN addgroup --gid 1001 nodejs && adduser --uid 1001 --ingroup nodejs --disabled-password --gecos "" agent
RUN chown -R agent:nodejs /app
USER agent

EXPOSE 8019

CMD ["node", "dist/index.js", "start"]
