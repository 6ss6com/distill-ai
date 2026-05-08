@echo off
chcp 65001 >nul 2>&1
title DistillAI 一键启动

echo ========================================
echo   DistillAI v2.5 一键启动器
echo ========================================
echo.

cd /d "%~dp0"

REM 检查Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [错误] 未找到 Python，请先安装 Python 3.10+
    echo 下载地址: https://www.python.org/downloads/
    pause
    exit /b 1
)

REM 检查依赖
python -c "import flask" >nul 2>&1
if errorlevel 1 (
    echo [安装] 正在安装依赖...
    pip install flask flask-cors requests -q
    echo [OK] 依赖安装完成
)

REM 安装本体
echo [安装] 正在安装 DistillAI...
pip install -e . -q
if errorlevel 1 (
    REM 如果失败，用简单方式
    echo [备用] pip install 失败，尝试 PYTHONPATH 模式...
)

echo.
echo ========================================
echo   启动中...
echo ========================================
echo.

REM 启动服务（无auth模式，方便测试）
python distill\api\server.py --no-auth

pause