# build.ps1
# Build script for Student Performance System deployment

Write-Host "Starting full system build processes..." -ForegroundColor Cyan

# 1. Install frontend dependencies and build
Write-Host "`n[1/3] Building React Frontend..." -ForegroundColor Yellow
cd frontend
npm install
if ($LASTEXITCODE -ne 0) { throw "npm install failed" }
npm run build
if ($LASTEXITCODE -ne 0) { throw "npm run build failed" }
cd ..
Write-Host "Frontend build complete!" -ForegroundColor Green

# 2. Install backend python dependencies
Write-Host "`n[2/3] Installing Backend Dependencies..." -ForegroundColor Yellow
python -m pip install -r requirements.txt
if ($LASTEXITCODE -ne 0) { throw "pip install failed" }
Write-Host "Backend dependencies installed!" -ForegroundColor Green

Write-Host "`n[3/3] Build finished successfully." -ForegroundColor Cyan
Write-Host "`nTo start the unified production server, execute:"
Write-Host '$env:FLASK_DEBUG="false"'
Write-Host '$env:DB_PASSWORD="<mysql-password>"'
Write-Host "python run.py"
