@echo off
rem SpotiParty on Windows: double-click to open it in the browser.
python "%~dp0serve.py" %*
if errorlevel 1 py "%~dp0serve.py" %*
