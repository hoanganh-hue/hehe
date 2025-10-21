# Simple frontend nginx container for static HTML files
FROM nginx:1.24-alpine

# Install wget for health checks
RUN apk add --no-cache wget

# Create necessary directories
RUN mkdir -p /usr/share/nginx/html /var/cache/nginx /var/log/nginx

# Copy static HTML files and assets
COPY admin /usr/share/nginx/html/admin
COPY merchant /usr/share/nginx/html/merchant
COPY css /usr/share/nginx/html/css
COPY js /usr/share/nginx/html/js

# Copy nginx configuration
COPY nginx.conf /etc/nginx/nginx.conf
COPY conf.d/default.conf /etc/nginx/conf.d/default.conf

# Create cache directories with proper permissions
RUN mkdir -p /var/cache/nginx/client_temp \
    /var/cache/nginx/proxy_temp \
    /var/cache/nginx/fastcgi_temp \
    /var/cache/nginx/uwsgi_temp \
    /var/cache/nginx/scgi_temp && \
    chown -R nginx:nginx /var/cache/nginx && \
    chown -R nginx:nginx /usr/share/nginx/html && \
    chmod -R 755 /usr/share/nginx/html

# Create health check page
RUN echo "healthy" > /usr/share/nginx/html/health

# Expose port
EXPOSE 80

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD wget --quiet --tries=1 --spider http://localhost/health || exit 1

# Start nginx
CMD ["nginx", "-g", "daemon off;"]
