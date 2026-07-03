FROM nginx:1.27-alpine

# Static sites — nothing to build, just copy them in.
COPY frontend/ /usr/share/nginx/html/frontend/
COPY admin/    /usr/share/nginx/html/admin/
COPY nginx/nginx.conf /etc/nginx/nginx.conf

EXPOSE 80
