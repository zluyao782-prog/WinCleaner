#!/bin/bash

echo "========================================"
echo "   WinCleaner Windows 系统清理工具"
echo "        构建脚本 v1.0 (Unix)"
echo "========================================"
echo

# 检查Python环境
echo "[1/5] 检查Python环境..."
if ! command -v python3 &> /dev/null; then
    echo "❌ 错误: 未找到Python3环境"
    echo "请确保已安装Python 3.10或更高版本"
    exit 1
fi
echo "✅ Python环境检查通过"

# 安装依赖
echo "[2/5] 安装依赖包..."
if [[ "$OSTYPE" == "darwin"* ]] || [[ "$OSTYPE" == "linux-gnu"* ]]; then
    # Unix系统使用跨平台依赖
    pip3 install -r requirements_unix.txt
else
    # Windows系统使用完整依赖
    pip3 install -r requirements.txt
fi
if [ $? -ne 0 ]; then
    echo "❌ 依赖安装失败"
    exit 1
fi
echo "✅ 依赖安装完成"

# 创建必要目录
echo "[3/5] 创建目录结构..."
mkdir -p logs dist build
echo "✅ 目录创建完成"

# 清理旧的构建文件
echo "[4/5] 清理旧构建文件..."
rm -f dist/WinCleaner
rm -rf build/*
rm -f WinCleaner.spec

# 使用PyInstaller打包
echo "[5/5] 开始打包..."
python3 -m PyInstaller --onefile --windowed \
  --name WinCleaner \
  --add-data "config:config" \
  --distpath dist \
  --workpath build \
  --specpath . \
  --clean \
  main.py

if [ $? -ne 0 ]; then
    echo "❌ 打包失败"
    echo "请检查错误信息并重试"
    exit 1
fi

# 验证打包结果
if [ ! -f "dist/WinCleaner" ]; then
    echo "❌ 打包失败: 未找到输出文件"
    exit 1
fi

# 显示文件信息
echo
echo "========================================"
echo "          构建成功完成！"
echo "========================================"
echo
echo "📁 输出文件: dist/WinCleaner"
echo "📊 文件大小: $(du -h dist/WinCleaner | cut -f1)"
echo "🕒 构建时间: $(date)"
echo
echo "⚠️  注意: 此版本在非Windows系统上功能受限"
echo "完整功能需要在Windows系统上运行"
echo

# 询问是否清理构建文件
read -p "是否清理临时构建文件? (y/n): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    rm -rf build
    rm -f WinCleaner.spec
    echo "✅ 临时文件清理完成"
fi

echo "构建完成！"