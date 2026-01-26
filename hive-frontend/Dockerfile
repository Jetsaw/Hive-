FROM nginx:alpine

# Copy only necessary static files (not all files)
COPY index.html /usr/share/nginx/html/
COPY admin-enhanced.html /usr/share/nginx/html/
COPY *.css /usr/share/nginx/html/
COPY *.js /usr/share/nginx/html/
COPY logo.png /usr/share/nginx/html/

# Health check for container monitoring
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD wget --quiet --tries=1 --spider http://localhost:80/ || exit 1

# Nginx runs as non-root by default in Alpine
EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
