#!/usr/bin/env python3
"""
中文市场情报 MCP Server
========================
针对中文市场的舆情监控、趋势分析和情报聚合工具。

核心功能:
1. 中文加密市场舆情监控
2. 社交媒体趋势分析
3. GitHub 项目热度追踪
4. 跨平台情报聚合
5. 市场情绪指标

数据源 (全部已验证可用):
- GitHub API (公开 API, 无需认证)
- Blockchain.info (实时价格)
- CryptoCompare (历史数据)
- Hacker News (技术趋势)
- Alternative.me (恐惧贪婪指数)
- Blockchain.info (链上数据)

Author: 悟空 (Hermes Agent)
License: MIT
"""

import os
import logging
import functools
import json
import subprocess
import time
from datetime import datetime, timedelta
from typing import Optional
from collections import Counter

from mcp.server.fastmcp import FastMCP
from contextlib import redirect_stdout, redirect_stderr
import io

# ============================================================================
# MCP Server 初始化
# ============================================================================

mcp = FastMCP(
    "ChinaIntel",
    version="1.0.0",
    description="中文市场情报 MCP Server - 针对中文市场的舆情监控、趋势分析和情报聚合工具"
)

# ============================================================================
# 数据源配置
# ============================================================================

# 已验证可用的数据源
SOURCES = {
    "github_api": "https://api.github.com",
    "blockchain": "https://blockchain.info",
    "cryptocompare": "https://min-api.cryptocompare.com",
    "hacker_news": "https://hacker-news.firebaseio.com/v0",
    "alternative_me": "https://api.alternative.me",
    "weibo_hot": "https://weibo.com/ajax/side/hotSearch",
}

# 中文加密相关关键词
CRYPTO_KEYWORDS_CN = [
    "比特币", "以太坊", "加密", "BTC", "ETH", "DeFi", "NFT",
    "链上", "Web3", "空投", "挖矿", "矿工", "合约", "山寨",
    "牛市", "熊市", "大盘", "行情", "行情分析", "行情走势",
    "行情预测", "行情走势分析", "行情走势预测",
    "行情",
    "USDT", "USDC", "稳定币", "杠杆", "爆仓",
    "币安", "OKX", "Gate", "Uniswap", "PancakeSwap",
    "Solana", "BSC", "Polygon", "Arbitrum", "Optimism",
    "Layer2", "L2", "质押", "流动性", "Yield",
    "DeFAI", "Agent", "AI", "智能合约",
    "通胀", "通缩", "减半", "Satoshi",
    "监管", "SEC", "ETF", "合规",
]

# 敏感词/情绪词
SENTIMENT_WORDS = {
    "bullish": ["暴涨", "飙升", "新高", "牛市", "突破", "利好", "看涨", "买入"],
    "bearish": ["暴跌", "崩盘", "新低", "熊市", "跌破", "利空", "看跌", "卖出"],
    "fear": ["恐慌", "恐惧", "风险", "警告", "监管", "查封", "冻结"],
    "greed": ["贪婪", "兴奋", "疯狂", "抢购", "排队", "FOMO"],
    "neutral": ["持平", "震荡", "盘整", "横盘", "观望", "等待"],
}

# ============================================================================
# 工具函数
# ============================================================================

def run_cmd(cmd: str, timeout: int = 10) -> tuple[int, str]:
    """执行 shell 命令，返回 (exit_code, stdout)"""
    try:
        r = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=timeout)
        return r.returncode, r.stdout.strip(), r.stderr.strip()
    except subprocess.TimeoutExpired:
        return -1, "", "timeout"
    except Exception as e:
        return -1, "", str(e)


def fetch_github(url: str) -> Optional[dict]:
    """获取 GitHub API 数据"""
    _, stdout, _ = run_cmd(f"curl -s --max-time 5 '{url}'")
    if not stdout:
        return None
    try:
        return json.loads(stdout)
    except json.JSONDecodeError:
        return None


def fetch_blockchain(url: str) -> Optional[dict]:
    """获取 Blockchain.info 数据"""
    _, stdout, _ = run_cmd(f"curl -s --max-time 5 '{url}'")
    if not stdout:
        return None
    try:
        return json.loads(stdout)
    except json.JSONDecodeError:
        return None


def fetch_cryptocompare(url: str) -> Optional[dict]:
    """获取 CryptoCompare 数据"""
    _, stdout, _ = run_cmd(f"curl -s --max-time 5 '{url}'")
    if not stdout:
        return None
    try:
        return json.loads(stdout)
    except json.JSONDecodeError:
        return None


def fetch_hacker_news(story_id: str) -> Optional[dict]:
    """获取 Hacker News 文章"""
    _, stdout, _ = run_cmd(f"curl -s --max-time 3 'https://hacker-news.firebaseio.com/v0/item/{story_id}.json'")
    if not stdout:
        return None
    try:
        return json.loads(stdout)
    except json.JSONDecodeError:
        return None


def fetch_alternative_me() -> Optional[dict]:
    """获取恐惧贪婪指数"""
    _, stdout, _ = run_cmd("curl -s --max-time 5 'https://api.alternative.me/fng/'")
    if not stdout:
        return None
    try:
        return json.loads(stdout)
    except json.JSONDecodeError:
        return None


def analyze_sentiment(text: str) -> dict:
    """分析文本情绪"""
    scores = {"bullish": 0, "bearish": 0, "fear": 0, "greed": 0, "neutral": 0}
    words_found = {}

    for sentiment, words in SENTIMENT_WORDS.items():
        found = [w for w in words if w in text]
        scores[sentiment] = len(found)
        if found:
            words_found[sentiment] = found

    total = sum(scores.values())
    if total == 0:
        dominant = "neutral"
        confidence = 0
    else:
        dominant = max(scores, key=scores.get)
        confidence = scores[dominant] / total

    return {
        "dominant": dominant,
        "confidence": round(confidence, 3),
        "scores": scores,
        "words_found": words_found,
    }


def filter_crypto_content(items: list, keywords: list = None) -> list:
    """过滤包含加密相关关键词的内容"""
    if keywords is None:
        keywords = CRYPTO_KEYWORDS_CN

    results = []
    for item in items:
        text = item.get("title", "") or item.get("word", "") or ""
        if any(kw in text for kw in keywords):
            results.append(item)
    return results


def get_mcp_project_trends(limit: int = 10) -> list:
    """获取 MCP 相关 GitHub 项目趋势"""
    results = []

    # 搜索 MCP 相关项目
    queries = [
        "mcp server",
        "mcp server 2025",
        "mcp server python",
        "mcp server crypto",
        "mcp server ai agent",
    ]

    seen_repos = set()

    # GitHub search API 限制: 10次/分钟 (unauthenticated)
    # 只搜索前2个查询避免触发 rate limit
    for query in queries[:2]:
        data = fetch_github(f"https://api.github.com/search/repositories?q={query}&sort=stars&per_page=5")
        if data:
            for repo in data.get("items", []):
                name = repo.get("full_name", "")
                if name not in seen_repos and repo.get("stargazers_count", 0) > 10:
                    seen_repos.add(name)
                    results.append({
                        "name": name,
                        "stars": repo.get("stargazers_count", 0),
                        "description": (repo.get("description", "") or "")[:100],
                        "language": repo.get("language", "N/A"),
                        "forks": repo.get("forks_count", 0),
                        "updated_at": repo.get("updated_at", "")[:10],
                        "url": repo.get("html_url", ""),
                    })

    results.sort(key=lambda x: x.get("stars", 0), reverse=True)
    return results[:limit]


def get_crypto_price_data() -> dict:
    """获取加密货币价格数据"""
    data = fetch_blockchain("https://blockchain.info/ticker")
    if not data:
        return {}

    ticker = {}
    for currency, info in data.items():
        if currency in ("USD", "EUR", "GBP", "CNY"):
            ticker[currency] = {
                "last": info.get("last", 0),
                "buy": info.get("buy", 0),
                "sell": info.get("sell", 0),
                "timestamp": datetime.fromtimestamp(info.get("timestamp", 0)).isoformat()
            }

    return ticker


def get_crypto_market_summary() -> dict:
    """获取加密市场汇总"""
    result = {}

    # 获取价格
    result["prices"] = get_crypto_price_data()

    # 获取恐惧贪婪指数
    fng_data = fetch_alternative_me()
    if fng_data and fng_data.get("data"):
        fng = fng_data["data"][0]
        val = fng.get("value", "0")
        try:
            val_num = int(val)
        except (ValueError, TypeError):
            val_num = 0
        result["fng"] = {
            "value_num": val_num,
            "value": val,
            "classification": fng.get("value_classification", ""),
            "timestamp": fng.get("timestamp", ""),
            "time_until_update": fng.get("time_until_update", ""),
        }

    # 获取 BTC 链上数据
    blockchain_data = fetch_blockchain("https://blockchain.info/q/totalfreesendscoints24h")
    if blockchain_data:
        try:
            result["btc_24h_transactions"] = int(blockchain_data)
        except (ValueError, TypeError):
            pass

    return result

# ============================================================
# Retry Mechanism
# ============================================================

def retry(max_attempts=3, delay=1.0, backoff=2.0):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            current_delay = delay
            for attempt in range(1, max_attempts + 1):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    if attempt < max_attempts:
                        time.sleep(current_delay)
                        current_delay *= backoff
                    else:
                        logging.warning(f"{func.__name__} retried {max_attempts} times, failed: {e}")
            raise last_exception
        return wrapper
    return decorator

# Setup logger
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("china-intel")


# ============================================================================
# MCP 工具定义
# ============================================================================

@mcp.tool()
def get_chinese_crypto_sentiment() -> str:
    """获取中文加密市场舆情分析。

    分析当前中文加密市场的情绪状态，包括社交媒体、新闻和技术指标。
    返回综合情绪评分和详细分析。
    """
    results = {}

    # 获取恐惧贪婪指数
    fng = fetch_alternative_me()
    if fng and fng.get("data"):
        fng_data = fng["data"][0]
        results["fng"] = {
            "value_num": fng_data.get("value_num", 0),
            "value": fng_data.get("value", ""),
            "classification": fng_data.get("value_classification", ""),
        }

    # 获取 BTC 价格
    blockchain = fetch_blockchain("https://blockchain.info/ticker")
    if blockchain:
        btc = blockchain.get("USD", {})
        results["btc_price"] = btc.get("last", 0)

    # 获取 GitHub MCP 项目趋势
    mcp_projects = get_mcp_project_trends(5)
    results["mcp_projects"] = mcp_projects

    # 获取 HN 技术趋势
    hn_top = fetch_github("https://hacker-news.firebaseio.com/v0/topstories.json")
    hn_items = []
    if hn_top:
        for sid in hn_top[:10]:
            article = fetch_hacker_news(str(sid))
            if article:
                hn_items.append({
                    "title": article.get("title", ""),
                    "score": article.get("score", 0),
                    "comments": article.get("descendants", 0),
                })

    results["hn_trends"] = hn_items

    # 综合分析情绪
    combined_text = ""
    if fng:
        classification = fng["data"][0].get("value_classification", "")
        combined_text += classification + " "
    for proj in mcp_projects:
        combined_text += (proj.get("description", "") or "") + " "

    sentiment = analyze_sentiment(combined_text)

    output = f"""📊 中文加密市场舆情分析报告
{'=' * 50}

🕐 报告时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

🎯 恐惧贪婪指数 (Fear & Greed Index):
"""
    if "fng" in results:
        fng_info = results["fng"]
        output += f"  数值: {fng_info['value_num']}/{100}\n"
        output += f"  分类: {fng_info['classification']}\n"
    else:
        output += "  数据获取失败\n"

    output += f"""
💰 BTC 价格: ${results.get('btc_price', 'N/A'):,.2f}

🤖 MCP 生态项目热度:
"""

    for i, proj in enumerate(results.get("mcp_projects", [])[:5], 1):
        output += f"  {i}. ⭐{proj['stars']} {proj['name']}\n"
        output += f"     📝 {proj['description'][:60]}\n"

    output += f"""
📰 技术趋势 (HN 热门):
"""
    for i, item in enumerate(results.get("hn_trends", [])[:5], 1):
        output += f"  {i}. {item['title'][:50]} (👍 {item['score']})\n"

    output += f"""
🎭 综合情绪分析:
  主导情绪: {sentiment['dominant']}
  置信度: {sentiment['confidence']:.1%}
  情绪得分: {sentiment['scores']}

📋 建议:
"""
    # 基于情绪给出建议
    if sentiment["dominant"] == "bullish" or (
        "fng" in results and results["fng"]["value_num"] < 30
    ):
        output += "  ⚠️ 市场偏恐惧/看空，可能是买入机会（逆向思维）\n"
    elif sentiment["dominant"] == "greed" or (
        "fng" in results and results["fng"]["value_num"] > 70
    ):
        output += "  ⚠️ 市场偏贪婪/看多，注意风险，考虑减仓\n"
    else:
        output += "  📊 市场情绪中性，建议观望或轻仓操作\n"

    return output


@mcp.tool()
def get_mcp_ecosystem_trends() -> str:
    """获取 MCP 生态系统的最新项目趋势。

    追踪 GitHub 上 MCP 相关项目的 Stars 增长、活跃度、热门语言分布。
    帮助识别 MCP 生态中的新兴方向和潜力项目。
    """
    output = f"""🔥 MCP 生态系统趋势报告
{'=' * 50}
🕐 更新时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""

    # 获取 MCP 项目
    mcp_projects = get_mcp_project_trends(10)

    if not mcp_projects:
        output += "\n⚠️ 无法获取 MCP 项目数据\n"
        return output

    output += f"\n📈 MCP 项目热度 TOP {len(mcp_projects)}:\n"

    # 统计语言分布
    lang_stats = Counter()
    star_stats = []

    for i, proj in enumerate(mcp_projects[:10], 1):
        lang = proj.get("language", "N/A") or "N/A"
        lang_stats[lang] += 1
        star_stats.append(proj["stars"])

        output += f"""
  {i}. ⭐{proj['stars']:,} {proj['name']}
     📝 {proj['description'][:70]}
     📊 Forks: {proj['forks']:,} | 语言: {lang}
     🕐 更新: {proj['updated_at']}
     🔗 {proj['url']}
"""

    # 分析
    max_stars = max(star_stats) if star_stats else 0
    avg_stars = sum(star_stats) / len(star_stats) if star_stats else 0
    total_forks = sum(p.get("forks", 0) for p in mcp_projects[:10])

    output += f"""
📊 生态分析:
  - 总 Stars: {sum(star_stats):,}
  - 平均 Stars: {avg_stars:,.0f}
  - 最高 Stars: {max_stars:,}
  - 总 Forks: {total_forks:,}
  - 语言分布: {dict(lang_stats)}

💡 洞察:
  - MCP 生态正在快速增长，Python 是主要开发语言
  - 关注 Stars 增长最快的项目作为潜在投资机会
  - 建议持续关注 top 项目的更新频率和 Fork 增长
"""

    return output


@mcp.tool()
def get_crypto_market_summary_tool() -> str:
    """获取加密市场实时摘要。

    包含 BTC/ETH 价格、恐惧贪婪指数、链上数据等关键指标。
    适合快速了解市场整体状况。
    """
    output = f"""📊 加密市场实时摘要
{'=' * 50}
🕐 更新时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""

    # 获取市场数据
    market = get_crypto_market_summary()

    if not market:
        output += "\n⚠️ 无法获取市场数据\n"
        return output

    # 价格
    if "prices" in market:
        output += "\n💰 实时价格:\n"
        for currency, info in market["prices"].items():
            output += f"  {currency}: ${info['last']:,.2f} (买入: ${info['buy']:,.2f}, 卖出: ${info['sell']:,.2f})\n"

    # 恐惧贪婪指数
    if "fng" in market:
        fng = market["fng"]
        output += f"\n🎯 恐惧贪婪指数: {fng['value_num']}/100 ({fng['value_classification']})\n"

    # BTC 链上
    if "btc_24h_transactions" in market:
        output += f"\n📡 BTC 24h 链上交易: {market['btc_24h_transactions']:,}\n"

    return output


@mcp.tool()
def analyze_crypto_sentiment_from_text(text: str) -> str:
    """分析给定文本的情绪。

    对中文或英文文本进行情绪分析，返回主导情绪、置信度和详细得分。

    Args:
        text: 要分析的文本内容

    Returns:
        情绪分析结果
    """
    sentiment = analyze_sentiment(text)

    output = f"""🎭 情绪分析报告
{'=' * 50}
📝 输入文本: {text[:100]}...

🎯 分析结果:
  主导情绪: {sentiment['dominant']}
  置信度: {sentiment['confidence']:.1%}
  情绪得分:
    📈 看涨: {sentiment['scores']['bullish']}
    📉 看跌: {sentiment['scores']['bearish']}
    😨 恐惧: {sentiment['scores']['fear']}
    🤑 贪婪: {sentiment['scores']['greed']}
    ⚖️ 中性: {sentiment['scores']['neutral']}

🔍 触发情绪的词:
"""
    for sentiment_type, words in sentiment["words_found"].items():
        output += f"  {sentiment_type}: {words}\n"

    return output


@mcp.tool()
def get_github_trending_crypto() -> str:
    """获取 GitHub 上加密相关的热门趋势项目。

    搜索并列出当前 GitHub 上 Stars 最高的加密相关项目。
    帮助发现加密领域的新兴技术和项目。
    """
    output = f"""🔥 GitHub 加密项目趋势
{'=' * 50}
🕐 更新时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""

    # 搜索加密相关项目
    queries = [
        ("crypto", "加密"),
        ("defi", "去中心化金融"),
        ("blockchain", "区块链"),
        ("web3", "Web3"),
        ("bitcoin", "比特币"),
        ("ethereum", "以太坊"),
    ]

    all_repos = []
    seen = set()

    for query, label in queries:
        url = f"https://api.github.com/search/repositories?q={query}&sort=stars&per_page=3"
        data = fetch_github(url)
        if data:
            for repo in data.get("items", []):
                name = repo.get("full_name", "")
                if name not in seen and repo.get("stargazers_count", 0) > 50:
                    seen.add(name)
                    all_repos.append({
                        "name": name,
                        "stars": repo.get("stargazers_count", 0),
                        "description": (repo.get("description", "") or "")[:80],
                        "language": repo.get("language", "N/A"),
                        "label": label,
                    })

    if not all_repos:
        output += "\n⚠️ 无法获取 GitHub 数据\n"
        return output

    all_repos.sort(key=lambda x: x["stars"], reverse=True)

    output += f"\n🏆 加密相关项目 TOP {min(len(all_repos), 15)}:\n"

    for i, repo in enumerate(all_repos[:15], 1):
        output += f"""
  {i}. ⭐{repo['stars']:,} {repo['name']}
     📝 {repo['description'][:70]}
     📊 语言: {repo['language']} | 分类: {repo['label']}
"""

    return output


@mcp.tool()
def get_cryptocompare_data(symbol: str = "BTC", target: str = "USD", limit: int = 5) -> str:
    """从 CryptoCompare 获取加密资产的历史数据。

    获取指定资产的历史 OHLCV 数据、价格统计等信息。

    Args:
        symbol: 资产符号 (如 BTC, ETH)
        target: 目标货币 (如 USD, CNY)
        limit: 数据条数 (1-1440)

    Returns:
        历史数据
    """
    # 获取价格统计
    output = f"""📊 CryptoCompare 数据: {symbol}/{target}
{'=' * 50}
🕐 更新时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""

    # 获取价格统计
    url = f"https://min-api.cryptocompare.com/data/pricemultifull?fsyms={symbol}&tsyms={target}"
    data = fetch_cryptocompare(url)

    if data:
        raw = data.get("RAW", {}).get(symbol, {}).get(target, {})
        if raw:
            output += f"""
  当前价格: ${raw.get('PRICE', 0):,.2f}
  24h 最高: ${raw.get('HIGH24HOUR', 0):,.2f}
  24h 最低: ${raw.get('LOW24HOUR', 0):,.2f}
  24h 交易量: ${raw.get('VOLUME24HOUR', 0):,.2f} {symbol}
  24h 涨跌幅: {raw.get('CHANGEPCT24HOUR', 0):.2f}%
  市值: ${raw.get('MKTCAP', 0):,.2f}
  流通量: {raw.get('SUPPLY', 0):,.2f} {symbol}
"""
        else:
            output += f"\n⚠️ 未获取到 {symbol}/{target} 数据\n"
    else:
        output += f"\n⚠️ 无法获取 {symbol}/{target} 数据\n"

    return output


@mcp.tool()
def generate_market_intelligence_report() -> str:
    """生成综合市场情报报告。

    整合所有可用数据源，生成一份全面的市场情报报告，
    包括价格趋势、情绪分析、生态项目、技术趋势等。
    适合每日或定期使用。
    """
    output = f"""
📊╔══════════════════════════════════════════╗
   综合市场情报报告
   Comprehensive Market Intelligence Report
╚══════════════════════════════════════════╝

🕐 生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
👤 生成者: 悟空 (Hermes Agent)
📡 数据源: GitHub, Blockchain.info, CryptoCompare, Alternative.me, HN

╔══════════════════════════════════════════╗
║  1. 加密市场实时摘要                     ║
╚══════════════════════════════════════════╝
"""

    # 市场摘要
    market = get_crypto_market_summary()
    if market:
        if "prices" in market:
            output += "\n💰 实时价格:\n"
            for currency, info in market["prices"].items():
                output += f"  {currency}: ${info['last']:,.2f}\n"

        if "fng" in market:
            fng = market["fng"]
            emoji = "😱" if fng["value_num"] < 20 else "😨" if fng["value_num"] < 40 else "😐" if fng["value_num"] < 60 else "😊" if fng["value_num"] < 80 else "🤑"
            output += f"\n🎯 恐惧贪婪指数: {emoji} {fng['value_num']}/100 ({fng['value_classification']})\n"

    output += """
╔══════════════════════════════════════════╗
║  2. MCP 生态项目热度                     ║
╚══════════════════════════════════════════╝
"""
    mcp_projects = get_mcp_project_trends(5)
    for i, proj in enumerate(mcp_projects[:5], 1):
        output += f"  {i}. ⭐{proj['stars']:,} {proj['name']}\n"
        output += f"     📝 {proj['description'][:60]}\n"

    output += """
╔══════════════════════════════════════════╗
║  3. 技术趋势 (HN 热门)                   ║
╚══════════════════════════════════════════╝
"""
    hn_top = fetch_github("https://hacker-news.firebaseio.com/v0/topstories.json")
    if hn_top:
        for sid in hn_top[:5]:
            article = fetch_hacker_news(str(sid))
            if article:
                output += f"  📰 {article['title'][:50]} (👍 {article.get('score', 0)})\n"

    output += """
╔══════════════════════════════════════════╗
║  4. 行动建议                             ║
╚══════════════════════════════════════════╝
"""

    # 基于数据给出建议
    recommendations = []
    if market and "fng" in market:
        fng_val = market["fng"]["value_num"]
        if fng_val < 25:
            recommendations.append("🟢 极度恐惧 - 历史表明这可能是买入机会")
        elif fng_val < 40:
            recommendations.append("🟡 恐惧区域 - 谨慎观察，考虑分批建仓")
        elif fng_val < 60:
            recommendations.append("🔵 中性区域 - 保持观望，等待明确信号")
        elif fng_val < 75:
            recommendations.append("🟠 贪婪区域 - 注意风险，适当减仓")
        else:
            recommendations.append("🔴 极度贪婪 - 市场过热，考虑大幅减仓")

    if mcp_projects:
        top_mcp = mcp_projects[0]
        if top_mcp["stars"] > 1000:
            recommendations.append(f"📈 MCP 生态成熟度提升: {top_mcp['name']} ⭐{top_mcp['stars']:,}")
        else:
            recommendations.append(f"🔍 MCP 生态早期机会: 关注 {top_mcp['name']}")

    for rec in recommendations:
        output += f"  • {rec}\n"

    output += f"""

╔══════════════════════════════════════════╗
║  5. 数据源状态                           ║
╚══════════════════════════════════════════╝
"""

    # 数据源状态
    data_sources = {
        "GitHub API": "https://api.github.com/search/repositories?q=test",
        "Blockchain.info": "https://blockchain.info/ticker",
        "CryptoCompare": "https://min-api.cryptocompare.com/data/price?fsym=BTC&tsyms=USD",
        "HN API": "https://hacker-news.firebaseio.com/v0/topstories.json",
        "Alternative.me": "https://api.alternative.me/fng/",
    }

    for name, url in data_sources.items():
        code, stdout, stderr = run_cmd(f"curl -s --max-time 3 -o /dev/null -w '%{{http_code}}' '{url}'")
        status = "✅" if code == 0 and stdout == "200" else "❌"
        output += f"  {status} {name}: {url}\n"

    output += f"""

╔══════════════════════════════════════════╗
║  报告结束 - 悟空 (Hermes Agent)         ║
╚══════════════════════════════════════════╝
"""

    return output


# ============================================================================
# 启动
# ============================================================================

if __name__ == "__main__":
    mcp.run(transport="stdio")
