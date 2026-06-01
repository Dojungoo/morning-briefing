FROM node:22-alpine AS deps
RUN corepack enable
WORKDIR /app
COPY package.json pnpm-lock.yaml ./
RUN pnpm install --frozen-lockfile

FROM node:22-alpine AS builder
RUN corepack enable
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY . .
# `output: "export"` in next.config.ts → static site in ./out
RUN pnpm build

FROM nginx:1.27-alpine AS runner
# Limit envsubst to BACKEND_URL so $host / $proxy_add_x_forwarded_for
# in the nginx config aren't expanded against env vars.
ENV NGINX_ENVSUBST_FILTER="BACKEND_URL"
COPY nginx.conf.template /etc/nginx/templates/default.conf.template
COPY --from=builder /app/out /usr/share/nginx/html
EXPOSE 80
