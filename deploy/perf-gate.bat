@echo off
setlocal enabledelayedexpansion

REM Performance gate with k6
REM Usage:
REM   deploy\perf-gate.bat
REM   deploy\perf-gate.bat --stress

set MODE=%1
if "%MODE%"=="" set MODE=--smoke

set BASE_URL=%BASE_URL%
if "%BASE_URL%"=="" set BASE_URL=http://127.0.0.1:8000

where k6 >nul 2>nul
if errorlevel 1 (
  echo [perf] k6 not found. Please install k6 first.
  echo [perf] Windows winget: winget install k6.k6
  exit /b 1
)

echo [perf] BASE_URL=%BASE_URL%

if /I "%MODE%"=="--stress" (
  echo [perf] running stress profile...
  k6 run tests\perf\k6_stress.js -e BASE_URL=%BASE_URL%
  if errorlevel 1 goto :fail
) else (
  echo [perf] running smoke profile...
  k6 run deploy\perf\k6_smoke.js -e BASE_URL=%BASE_URL%
  if errorlevel 1 goto :fail
)

echo [perf] PASS
goto :eof

:fail
echo [perf] FAIL
exit /b 1
