FROM nginx:alpine

# Copy frontend files with proper structure
COPY index.html /usr/share/nginx/html/
COPY admin-enhanced.html /usr/share/nginx/html/
COPY assets/ /usr/share/nginx/html/assets/
COPY css/ /usr/share/nginx/html/css/
COPY js/ /usr/share/nginx/html/js/

# Health check for container monitoring
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD wget --quiet --tries=1 --spider http://localhost:80/ || exit 1

# Nginx runs as non-root by default in Alpine
EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
