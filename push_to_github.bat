@echo off
chcp 65001 >nul
echo ============================================================
echo   迅鲨加速器 - 一键推送到 GitHub
echo ============================================================
echo.

set /p GITHUB_USER="请输入 GitHub 用户名 (默认: Quansss): "
if "%GITHUB_USER%"=="" set GITHUB_USER=Quansss

set REPO_NAME=SharkVPNConnect

echo.
echo 配置信息：
echo   用户名: %GITHUB_USER%
echo   仓库名: %REPO_NAME%
echo   仓库URL: https://github.com/%GITHUB_USER%/%REPO_NAME%.git
echo.

cd /d "%~dp0"

REM 检查 git
where git >nul 2>&1
if errorlevel 1 (
    echo [错误] 未找到 git，请先安装 Git for Windows
    pause
    exit /b 1
)

REM 初始化仓库（如果还没有）
if not exist .git (
    echo [1/5] 初始化 Git 仓库...
    git init
    git branch -M main
) else (
    echo [1/5] Git 仓库已存在
)

REM 创建 .gitignore
echo [2/5] 创建 .gitignore...
(
echo # Python
echo __pycache__/
echo *.py[cod]
echo *$py.class
echo *.so
echo.
echo # 构建产物
echo build/
echo dist/
echo release/
echo *.spec
echo.
echo # EasyTier 资源（构建时重新下载）
echo easytier-extract/
echo easytier.zip
echo easytier-macos-*.zip
echo.
echo # 日志
echo *.log
echo build_err.txt
echo build_log.txt
echo.
echo # 测试/调试脚本
echo test_*.py
echo ssh_*.py
echo patch_*.py
echo.
echo # 系统
echo .DS_Store
echo Thumbs.db
echo.
echo # IDE
echo .vscode/
echo .idea/
echo *.swp
) > .gitignore

REM 添加文件
echo [3/5] 添加文件到 Git...
git add .

echo.
echo 将要提交的文件：
git status --short

echo.
set /p CONFIRM="确认提交并推送？ (y/n): "
if /i not "%CONFIRM%"=="y" (
    echo 已取消
    pause
    exit /b 0
)

REM 提交
echo [4/5] 提交代码...
git commit -m "Initial commit: SharkVPNConnect v1.0.0

- 迅鲨加速器客户端（暗色游戏风格 GUI）
- 授权注册工具（白底简洁风格）
- 授权码生成器（服务端用）
- PyInstaller 打包脚本（Windows）
- macOS 打包脚本（支持 arm64/x86_64）
- EasyTier 虚拟组网集成
- HMAC-SHA256 授权验证"

REM 添加远程仓库
echo [5/5] 推送到 GitHub...
git remote remove origin 2>nul
git remote add origin https://github.com/%GITHUB_USER%/%REPO_NAME%.git

echo.
echo ============================================================
echo 准备推送到: https://github.com/%GITHUB_USER%/%REPO_NAME%.git
echo ============================================================
echo.
echo 提示：推送时会要求输入 GitHub 凭据
echo   用户名: %GITHUB_USER%
echo   密码:   使用 Personal Access Token（不是登录密码！）
echo.
echo 如果没有 Token，请按以下步骤创建：
echo   1. 访问 https://github.com/settings/tokens
echo   2. Generate new token (classic)
echo   3. 勾选 repo 权限
echo   4. 复制生成的 token（只显示一次！）
echo.

git push -u origin main

if errorlevel 1 (
    echo.
    echo [失败] 推送失败，请检查：
    echo   1. GitHub 仓库已创建
    echo   2. 使用了 Personal Access Token 而不是密码
    echo   3. 网络连接正常
) else (
    echo.
    echo ============================================================
    echo  ✅ 推送成功！
    echo  仓库地址: https://github.com/%GITHUB_USER%/%REPO_NAME%
    echo ============================================================
)

pause
