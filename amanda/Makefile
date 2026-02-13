SHELL := powershell.exe
.SHELLFLAGS := -NoProfile -ExecutionPolicy Bypass -Command

.PHONY: build clean dev

build:
	npm install
	npx tsc

clean:
	if (Test-Path "dist") { Remove-Item -Recurse -Force "dist" }
	if (Test-Path "node_modules") { Remove-Item -Recurse -Force "node_modules" }

dev:
	npm install
	npx tsc
	@netstat -ano 2>$$null | Select-String ":5174.*LISTENING" | ForEach-Object { Stop-Process -Id (($$_ -split '\s+')[-1]) -Force -ErrorAction SilentlyContinue }
	Write-Host "Starting server at http://localhost:5174" -ForegroundColor Green
	python -m http.server 5174 --bind 0.0.0.0
