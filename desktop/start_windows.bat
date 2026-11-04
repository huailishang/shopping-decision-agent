@echo off
setlocal
cd /d "%~dp0.."
where javac >nul 2>nul
if errorlevel 1 (echo JDK 17+ is required; javac not found.& pause & exit /b 1)
if not exist .h08-build mkdir .h08-build
javac -encoding UTF-8 -d .h08-build desktop\DesktopBridgeClient.java desktop\ShoppingDecisionDesktop.java
if errorlevel 1 (pause & exit /b 1)
java -cp .h08-build ShoppingDecisionDesktop python
