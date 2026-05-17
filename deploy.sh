#!/bin/bash
# Money Ecosystem - 一键部署脚本
# 自动安装依赖并启动服务

set -e

echo "🚀 开始部署 Money Ecosystem..."

# 创建虚拟环境
if [ ! -d "venv" ]; then
    echo "📦 创建 Python 虚拟环境..."
    python3 -m venv venv
fi

# 激活虚拟环境
source venv/bin/activate

# 安装依赖
echo "📦 安装依赖..."
pip install -r requirements.txt

# 创建缓存目录
mkdir -p ~/.money-ecosystem-cache
mkdir -p ~/.money-ecosystem/logs

# 启动服务
case "$1" in
    cryptosignal)
        echo "🔴 启动 CryptoSignal Server..."
        python3 mcp-servers/cryptosignal-server/server.py
        ;;
    chinese-news)
        echo "📰 启动 Chinese News Server..."
        python3 mcp-servers/chinese-news-server/server.py
        ;;
    china-intel)
        echo "🇨🇳 启动 China Intel Server..."
        python3 mcp-servers/china-intel-server/server.py
        ;;
    defi-nft)
        echo "🏦 启动 DeFi/NFT Monitor Server..."
        python3 mcp-servers/defi-nft-monitor/server.py
        ;;
    skill-market)
        echo "🎮 启动 Skill Market Server..."
        python3 mcp-servers/skill-market/server.py
        ;;
    *)
        echo "🚀 启动所有服务..."
        for server in cryptosignal-server chinese-news-server china-intel-server defi-nft-monitor skill-market; do
            echo "📡 启动 $server..."
            python3 mcp-servers/$server/server.py &
        done
        wait
        ;;
esac
