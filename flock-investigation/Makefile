SHELL := powershell.exe
.SHELLFLAGS := -NoProfile -ExecutionPolicy Bypass -Command

.PHONY: dev clean

# Dev - serve locally
dev:
	@netstat -ano 2>$$null | Select-String ":8080.*LISTENING" | ForEach-Object { Stop-Process -Id (($$_ -split '\s+')[-1]) -Force -ErrorAction SilentlyContinue }
	Write-Host "Starting server at http://localhost:8080" -ForegroundColor Green
	python -m http.server 8080 --bind 0.0.0.0
