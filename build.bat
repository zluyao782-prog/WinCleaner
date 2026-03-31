@echo off
echo ========================================
echo    WinCleaner Windows 系统清理工具
echo           构建脚本 v1.0
echo ========================================
echo.

REM 检查Python环境
echo [1/6] 检查Python环境...
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ 错误: 未找到Python环境
    echo 请确保已安装Python 3.10或更高版本
    pause
    exit /b 1
)
echo ✅ Python环境检查通过

REM 检查管理员权限
echo [2/6] 检查管理员权限...
net session >nul 2>&1
if errorlevel 1 (
    echo ⚠️  警告: 当前不是管理员权限
    echo 建议以管理员身份运行此脚本以避免权限问题
    echo.
    choice /C YN /M "是否继续构建"
    if errorlevel 2 exit /b 1
)

REM 安装依赖
echo [3/6] 安装依赖包...
pip install -r requirements.txt
if errorlevel 1 (
    echo ❌ 依赖安装失败
    pause
    exit /b 1
)
echo ✅ 依赖安装完成

REM 创建必要目录
echo [4/6] 创建目录结构...
if not exist "logs" mkdir logs
if not exist "dist" mkdir dist
if not exist "build" mkdir build
echo ✅ 目录创建完成

REM 清理旧的构建文件
echo [5/6] 清理旧构建文件...
if exist "dist\WinCleaner.exe" del "dist\WinCleaner.exe"
if exist "build" rmdir /s /q "build"
if exist "WinCleaner.spec" del "WinCleaner.spec"

REM 使用PyInstaller打包
echo [6/6] 开始打包...
pyinstaller --onefile --windowed --uac-admin ^
  --name WinCleaner ^
  --add-data "config;config" ^
  --distpath dist ^
  --workpath build ^
  --specpath . ^
  --version-file version_info.txt ^
  --clean ^
  main.py

if errorlevel 1 (
    echo ❌ 打包失败
    echo 请检查错误信息并重试
    pause
    exit /b 1
)

REM 验证打包结果
if not exist "dist\WinCleaner.exe" (
    echo ❌ 打包失败: 未找到输出文件
    pause
    exit /b 1
)

REM 显示文件信息
echo.
echo ========================================
echo           构建成功完成！
echo ========================================
echo.
echo 📁 输出文件: dist\WinCleaner.exe
for %%I in ("dist\WinCleaner.exe") do echo 📊 文件大小: %%~zI 字节
echo 🕒 构建时间: %date% %time%
echo.
echo 📋 使用说明:
echo   1. 将 WinCleaner.exe 复制到目标计算机
echo   2. 右键选择"以管理员身份运行"
echo   3. 在UAC提示中点击"是"
echo.
echo ⚠️  重要提示:
echo   - 程序需要管理员权限才能正常工作
echo   - 建议在使用前备份重要数据
echo   - 禁用Windows更新可能带来安全风险
echo.

REM 询问是否清理构建文件
choice /C YN /M "是否清理临时构建文件"
if errorlevel 1 (
    if exist "build" rmdir /s /q "build"
    if exist "WinCleaner.spec" del "WinCleaner.spec"
    echo ✅ 临时文件清理完成
)

echo 构建完成！按任意键退出...
pause >nul