@echo off
setlocal
set VIDEO_PATH=%~1

if "%VIDEO_PATH%"=="" (
    echo [ERROR] 動画の絶対パスを指定してください。
    echo 使用法: run_antigravity.bat "C:\path\to\video.mp4"
    pause
    exit /b 1
)

echo [Antigravity] 執行を開始します...
python master_batch_refiner.py "%VIDEO_PATH%"

echo [DONE] 処理が完了しました。
pause
