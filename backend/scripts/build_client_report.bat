@echo off
setlocal

set "ROOT=%~dp0.."
set "RESULTS_DIR=%ROOT%\reports\allure-results"
set "OUTPUT_HTML=%ROOT%\reports\client-report\index.html"

python "%ROOT%\scripts\generate_client_html_report.py" --results-dir "%RESULTS_DIR%" --output "%OUTPUT_HTML%"
if errorlevel 1 (
  exit /b %errorlevel%
)

echo.
echo Client report generated:
echo %OUTPUT_HTML%

endlocal
