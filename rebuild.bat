@echo off
chcp 65001 >nul
cd /d C:\Users\15062\.qclaw\workspace\palworld-client-app

echo === [1/4] 关闭旧 EXE ===
powershell -NoProfile -Command "Get-WmiObject -Class Win32_Process -Filter \"Name='迅鲨加速器.exe' or Name='PalworldClient.exe' or Name='LicenseGenerator.exe' or Name='RegisterTool.exe'\" | ForEach-Object { $_.Terminate() | Out-Null }"
timeout /t 1 /nobreak >nul

echo === [2/4] 检查依赖 ===
python -m pip install --upgrade pyinstaller pillow --quiet

echo === [3/4] 主构建 (build_exe.py) ===
python build_exe.py
if errorlevel 1 goto :err

echo === [4/4] 构建注册机 + 重打 zip ===
pyinstaller --onefile --windowed --name RegisterTool register_tool.py
if errorlevel 1 goto :err

if exist "dist\RegisterTool.exe" (
    copy /Y "dist\RegisterTool.exe" "release\迅鲨加速器-v1.0.0\RegisterTool.exe" >nul
    powershell -NoProfile -Command "Remove-Item 'release\迅鲨加速器-v1.0.0.zip' -ErrorAction SilentlyContinue; Add-Type -AssemblyName System.IO.Compression.FileSystem; [System.IO.Compression.ZipFile]::CreateFromDirectory('release\迅鲨加速器-v1.0.0', 'release\迅鲨加速器-v1.0.0.zip')"
)

echo.
echo === 构建完成 ===
echo 发布包: %CD%\release\迅鲨加速器-v1.0.0.zip
powershell -NoProfile -Command "Get-Item 'release\迅鲨加速器-v1.0.0.zip' | Select-Object Name, @{N='Size_MB';E={[math]::Round($_.Length/1MB,2)}} | Format-Table -AutoSize"
echo.
echo 文件列表:
powershell -NoProfile -Command "Get-ChildItem 'release\迅鲨加速器-v1.0.0\' | Format-Table Name, @{N='Size_KB';E={[int]($_.Length/1024)}} -AutoSize"
pause
exit /b 0

:err
echo.
echo === 出错，请查看上面的日志 ===
pause
exit /b 1
