@echo off
chcp 65001 > nul
setlocal
set VIDEO_PATH=%~1

if "%VIDEO_PATH%"=="" (
    echo [ERROR] 動画の絶対パスを指定してください。
    echo 使用法: run_antigravity.bat "C:\path\to\video.mp4"
    pause
    exit /b 1
)

echo ================================================================================
echo  Antigravity Ver.1.0 - Full Pipeline
echo ================================================================================

echo.
echo [Step 0] Video Downloader (UTAGE → yt-dlp)
python video_downloader.py
if %ERRORLEVEL% neq 0 (
    echo [ERROR] Step 0 failed. Aborting.
    pause
    exit /b 1
)

echo.
echo [Step 1-4] Master Batch Refiner
python master_batch_refiner.py "%VIDEO_PATH%"
if %ERRORLEVEL% neq 0 (
    echo [ERROR] Step 1-4 failed. Aborting.
    pause
    exit /b 1
)

echo.
echo [Step 5] Grand Master Integrator
python grand_master_integrator.py
if %ERRORLEVEL% neq 0 (
    echo [ERROR] Step 5 failed. Aborting.
    pause
    exit /b 1
)

echo.
echo [Step 6] Total Evidence Integrator
python total_evidence_integrator.py
if %ERRORLEVEL% neq 0 (
    echo [ERROR] Step 6 failed. Aborting.
    pause
    exit /b 1
)

echo.
echo ================================================================================
echo  All Steps Completed Successfully!
echo ================================================================================
pause
