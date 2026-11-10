@echo off
rem Usage: assess.bat "path\to\file.sql" [report_name]
setlocal
set "HERE=%~dp0"
if "%~1"=="" (
  echo Usage: assess "path\to\file.sql" [report_name]
  exit /b 2
)
set "NAME=%~2"
if "%NAME%"=="" set "NAME=my_report"
"%HERE%.venv\Scripts\python.exe" -m dbintel assess "%~1" --out "%HERE%reports\%NAME%"
if errorlevel 2 exit /b %errorlevel%
if not defined DBINTEL_NO_OPEN if exist "%HERE%reports\%NAME%\report.html" start "" "%HERE%reports\%NAME%\report.html"
