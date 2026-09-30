# infra/frontend.Dockerfile
# Packages the static frontend (landing, dashboard, outreach — already
# fully built HTML files, no build step needed since Phase 5-7 produced
# self-contained files directly) behind Nginx.
FROM nginx:1.27-alpine

COPY frontend/index.html /usr/share/nginx/html/index.html
COPY frontend/dashboard.html /usr/share/nginx/html/dashboard.html
COPY frontend/outreach.html /usr/share/nginx/html/outreach.html
COPY infra/nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD wget -q -O- http://localhost/ || exit 1
