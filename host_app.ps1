# Check if Docker is running
docker info > $null 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Docker is not running. Please start Docker Desktop first." -ForegroundColor Red
    exit
}

Write-Host "🐝 Building and Starting HIVE Containers..." -ForegroundColor Cyan

# Navigate to deploy directory
Set-Location -Path "deploy"

# Build and Start
docker-compose up --build -d

if ($LASTEXITCODE -eq 0) {
    Write-Host "`n✅ HIVE is hosted successfully!" -ForegroundColor Green
    Write-Host "👉 Access App: http://localhost:8080" -ForegroundColor Yellow
} else {
    Write-Host "`n❌ Deployment failed. Check error messages above." -ForegroundColor Red
}

# Wait for 2 seconds
Start-Sleep -Seconds 2
