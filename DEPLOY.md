# 🚀 Deployment Guide for HIVE

This guide ensures you can host HIVE easily using Docker containers. This is the production-ready way to host the application.

## ✅ Prerequisites

1. **Docker Desktop**: Install from [docker.com](https://www.docker.com/products/docker-desktop/)
2. **Git**: (Optional) if you are cloning the repo

---

## 🛠️ Step-by-Step Deployment

### 1. Build and Run

Navigate to the `deploy` folder and run Docker Compose:

```powershell
# Open PowerShell in the project root
cd deploy
docker-compose up --build -d
```

That's it! 

### 2. Access the Application

- **Frontend**: http://localhost:8080
- **Status Check**: The app is now running in isolated containers.
  - `nginx` container: manages routing
  - `backend` container: runs API
  - `frontend` container: serves UI

### 3. Stop the Application

```powershell
docker-compose down
```

---

## ☁️ Cloud Hosting (AWS, DigitalOcean, etc.)

To host publicly on a server:

1. **Copy project** to your server.
2. **Install Docker** on the server.
3. **Run the same command**: `docker-compose up --build -d` inside the deploy folder.

The application will be available on the server's IP address on port 8080.

---

## 🔧 Configuration details

- **Nginx Reverse Proxy**: Handles routing so `/api` goes to backend and `/` goes to frontend.
- **Data Persistence**: The knowledge base files in `data/` are mounted into the container.
- **Environment**: Ensure `.env` is present in `hive-backend/` before building.

---

## ❓ Troubleshooting

**"Ports are occupied"**
- If localhost:8080 is used, change the port in `deploy/docker-compose.yml`:
  ```yaml
  ports:
    - "9090:80"  # Change outer port to 9090
  ```

**"Changes not showing"**
- Run `docker-compose up --build -d` to force rebuild containers after code changes.
