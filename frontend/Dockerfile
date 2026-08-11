# syntax=docker/dockerfile:1
# Multi-stage: build the SPA with pnpm, then serve the static bundle with nginx, which also
# reverse-proxies the API routes to the app container so everything is one origin (no CORS).

# --- build stage ---------------------------------------------------------------------------
FROM node:22-alpine AS build
WORKDIR /app

# Pin pnpm via corepack for reproducible installs.
RUN corepack enable && corepack prepare pnpm@11 --activate

# Install deps first (cached while the lockfile is unchanged). pnpm-workspace.yaml carries the install
# policy (minimum-release-age excludes + onlyBuiltDependencies for esbuild/oxide/biome native binaries),
# so it must be present for the install to resolve exactly as it does locally.
COPY package.json pnpm-lock.yaml pnpm-workspace.yaml ./
RUN pnpm install --frozen-lockfile

# Build the production bundle (tsc + vite → dist/).
COPY . .
RUN pnpm build

# --- serve stage ---------------------------------------------------------------------------
FROM nginx:alpine AS serve
# Static SPA bundle.
COPY --from=build /app/dist /usr/share/nginx/html
# Our server config (SPA fallback + SSE-safe API proxy).
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
