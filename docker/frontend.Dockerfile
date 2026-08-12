# syntax=docker/dockerfile:1
# Multi-stage: build the SPA with pnpm, then serve the static bundle with nginx, which also
# reverse-proxies the API routes to the app container so everything is one origin (no CORS).
#
# Build context is the REPO ROOT (see docker/docker-compose.prod.yml) so this one Dockerfile can reach
# both the frontend source (frontend/) and the shared nginx config (docker/nginx.conf). Paths below are
# therefore repo-root-relative; the root .dockerignore keeps node_modules/dist out of the context.

# --- build stage ---------------------------------------------------------------------------
FROM node:22-alpine AS build
WORKDIR /app

# Pin pnpm via corepack for reproducible installs.
RUN corepack enable && corepack prepare pnpm@11 --activate

# Install deps first (cached while the lockfile is unchanged). pnpm-workspace.yaml carries the install
# policy (minimum-release-age excludes + onlyBuiltDependencies for esbuild/oxide/biome native binaries),
# so it must be present for the install to resolve exactly as it does locally.
COPY frontend/package.json frontend/pnpm-lock.yaml frontend/pnpm-workspace.yaml ./
RUN pnpm install --frozen-lockfile

# Build the production bundle (tsc + vite → dist/).
COPY frontend/ .
RUN pnpm build

# --- serve stage ---------------------------------------------------------------------------
FROM nginx:alpine AS serve
# Static SPA bundle.
COPY --from=build /app/dist /usr/share/nginx/html
# Our server config (SPA fallback + SSE-safe API proxy).
COPY docker/nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
