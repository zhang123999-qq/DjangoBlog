@echo off
cd /d "%~dp0.."
docker compose -f deploy/docker-compose.yml up -d
