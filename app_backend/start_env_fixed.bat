@echo off
title Forest Management System - Environment Fixed
color 0A

echo.
echo  ███████╗ ██████╗ ██████╗ ███████╗███████╗████████╗    ███╗   ███╗ █████╗ ███╗   ██╗ █████╗  ██████╗ ███████╗███╗   ███╗███████╗███╗   ██╗████████╗
echo  ██╔════╝██╔═══██╗██╔══██╗██╔════╝██╔════╝╚══██╔══╝    ████╗ ████║██╔══██╗████╗  ██║██╔══██╗██╔════╝ ██╔════╝████╗ ████║██╔════╝████╗  ██║╚══██╔══╝
echo  █████╗  ██║   ██║██████╔╝█████╗  ███████╗   ██║       ██╔████╔██║███████║██╔██╗ ██║███████║██║  ███╗█████╗  ██╔████╔██║█████╗  ██╔██╗ ██║   ██║   
echo  ██╔══╝  ██║   ██║██╔══██╗██╔══╝  ╚════██║   ██║       ██║╚██╔╝██║██╔══██║██║╚██╗██║██╔══██║██║   ██║██╔══╝  ██║╚██╔╝██║██╔══╝  ██║╚██╗██║   ██║   
echo  ██║     ╚██████╔╝██║  ██║███████╗███████║   ██║       ██║ ╚═╝ ██║██║  ██║██║ ╚████║██║  ██║╚██████╔╝███████╗██║ ╚═╝ ██║███████╗██║ ╚████║   ██║   
echo  ╚═╝      ╚═════╝ ╚═╝  ╚═╝╚══════╝╚══════╝   ╚═╝       ╚═╝     ╚═╝╚═╝  ╚═╝╚═╝  ╚═══╝╚═╝  ╚═╝ ╚═════╝ ╚══════╝╚═╝     ╚═╝╚══════╝╚═╝  ╚═══╝   ╚═╝   
echo.
echo ========================================
echo 🌲 Forest Management System - Environment Fixed
echo ========================================
echo.

REM Check prerequisites using the correct commands
echo 🔍 Checking prerequisites...
py --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python is not installed or not in PATH
    echo Please install Python and try again
    pause
    exit /b 1
) else (
    echo ✅ Python is installed
)

node --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Node.js is not installed or not in PATH
    echo Please install Node.js and try again
    pause
    exit /b 1
) else (
    echo ✅ Node.js is installed
)

npm --version >nul 2>&1
if errorlevel 1 (
    echo ❌ npm is not installed or not in PATH
    echo Please install npm and try again
    pause
    exit /b 1
) else (
    echo ✅ npm is installed
)

echo.

REM Check directories
if not exist "C:\ForestProject\app_backend" (
    echo ❌ Backend directory not found: C:\ForestProject\app_backend
    pause
    exit /b 1
) else (
    echo ✅ Backend directory found
)

if not exist "C:\ForestProject\app_frontend" (
    echo ❌ Frontend directory not found: C:\ForestProject\app_frontend
    pause
    exit /b 1
) else (
    echo ✅ Frontend directory found
)

echo.

REM Clean up existing processes
echo 🧹 Cleaning up existing processes...
for /f "tokens=5" %%a in ('netstat -aon ^| findstr :8000') do taskkill /f /pid %%a >nul 2>&1
for /f "tokens=5" %%a in ('netstat -aon ^| findstr :3000') do taskkill /f /pid %%a >nul 2>&1
for /f "tokens=5" %%a in ('netstat -aon ^| findstr :3001') do taskkill /f /pid %%a >nul 2>&1
echo ✅ Cleanup completed
echo.

REM Start Backend Server
echo 🚀 Starting Backend Server...
echo ========================================
start "Backend Server" cmd /k "cd /d C:\ForestProject\app_backend && echo Starting Backend Server... && py run.py"

REM Wait for backend
echo ⏳ Waiting for backend to start...
ping 127.0.0.1 -n 6 >nul

REM Check if backend is running
netstat -an | findstr :8000 >nul
if errorlevel 1 (
    echo ❌ Backend server failed to start
    echo Please check the backend logs
    pause
    exit /b 1
) else (
    echo ✅ Backend server is running on port 8000
)

echo.

REM Start Frontend Server
echo 🌐 Starting Frontend Development Server...
echo ========================================
start "Frontend Server" cmd /k "cd /d C:\ForestProject\app_frontend && echo Starting Frontend Server... && npm run dev"

REM Wait for frontend
echo ⏳ Waiting for frontend to start...
ping 127.0.0.1 -n 11 >nul

REM Check which port frontend is using
set FRONTEND_PORT=3000
netstat -an | findstr :3000 >nul
if errorlevel 1 (
    set FRONTEND_PORT=3001
    netstat -an | findstr :3001 >nul
    if errorlevel 1 (
        echo ⚠️  Frontend server may still be starting...
        set FRONTEND_PORT=3000
    ) else (
        echo ✅ Frontend server is running on port 3001
    )
) else (
    echo ✅ Frontend server is running on port 3000
)

echo.

REM Start Electron App
echo 🖥️  Starting Electron App...
echo ========================================
start "Electron App" cmd /k "cd /d C:\ForestProject\app_frontend && echo Starting Electron App... && npm run electron:preview"

echo.
echo ========================================
echo 🎉 All services started successfully!
echo ========================================
echo.
echo 📱 Services:
echo    Backend API: http://localhost:8000
echo    Frontend Web: http://localhost:%FRONTEND_PORT%
echo    Electron App: Desktop Application
echo.
echo 🔐 Login Credentials:
echo    Admin: avitbulnir@gmail.com / admin123
echo    Users: [username] / password123
echo.
echo 📊 Quick Links:
echo    Dashboard: http://localhost:%FRONTEND_PORT%/dashboard
echo    API Docs: http://localhost:8000/docs
echo    Health Check: http://localhost:8000/health
echo.
echo 💡 Tips:
echo    - Each service runs in its own terminal window
echo    - Use Ctrl+C in each terminal to stop individual services
echo    - Check terminal windows for detailed logs
echo.

REM Open browser
echo 🌐 Opening application in browser...
start "" "http://localhost:%FRONTEND_PORT%"
start "" "http://localhost:8000/docs"

echo.
echo 🌲 Forest Management System is ready!
echo Press any key to exit...
pause >nul

