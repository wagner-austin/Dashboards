# Live (GitHub Pages, deployed on push to main): https://austinwagner.org/flock-investigation/
# No `make deploy` target needed — GitHub Pages serves this subfolder automatically,
# regardless of whether the parent index.html links to it.

SHELL := powershell.exe
.SHELLFLAGS := -NoProfile -ExecutionPolicy Bypass -Command

.PHONY: dev urls clean

# Dev - serve locally
dev:
	@netstat -ano 2>$$null | Select-String ":8080.*LISTENING" | ForEach-Object { Stop-Process -Id (($$_ -split '\s+')[-1]) -Force -ErrorAction SilentlyContinue }
	Write-Host "Starting server at http://localhost:8080" -ForegroundColor Green
	python -m http.server 8080 --bind 0.0.0.0

# Urls - print the live URL and confirm it's serving
urls:
	Write-Host "Live: https://austinwagner.org/flock-investigation/" -ForegroundColor Green
	curl.exe -sI https://austinwagner.org/flock-investigation/ | Select-Object -First 1
