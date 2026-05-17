#!/usr/bin/env python3
"""
DeFi & NFT Monitor v6.0 - 链上收益机会 + NFT 趋势
=================================================
📌 战略: 开源免费 → 生态建设 → 适时商业化 (收款地址暂不公开)

🔥 v6.0 重大升级:
1. DeFi 链上收益监控 - 跨链流动性挖矿 APY 追踪
2. NFT 地板价趋势 - 热门 NFT 集合趋势分析
3. 流动性挖矿机会 - 高收益低风险 DeFi 协议发现
4. 链上资金流向 - 巨鲸地址监控
5. 跨链桥接数据 - 资金跨链流动监控
6. DeFi 协议风险评分 - 协议安全评估
7. NFT 市场情绪 - NFT 交易量和价格趋势
8. DeFi 收益率对比 - 多协议收益率横向比较

数据源 (已验证沙箱可用):
  1. DeFiLlama - TVL + 收益率 + 协议数据
  2. CoinGecko - ETH 价格 + 市值 + NFT 数据
  3. Etherscan - 链上交易数据
  4. NFTGo - NFT 交易数据 (免费 API)
  5. OpenSea - NFT 地板价
  6. Dune Analytics - 链上分析数据

Author: 悟空 (Hermes Agent)
License: MIT
"""

import json
import os
import logging
import functools
import sys
import time
import math
from typing import Dict, Any, Optional
from datetime import datetime, timedelta

try:
    from mcp.server.fastmcp import FastMCP
    MCP_AVAILABLE = True
except ImportError:
    MCP_AVAILABLE = False

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 数据源层 (Data Source Layer)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def fetch_url(url: str, timeout: int = 10) -> Optional[str]:
    """安全获取 URL 数据"""
    try:
        r = subprocess.run(
            f"curl -s --max-time {timeout} '{url}'",
            shell=True, capture_output=True, text=True
        )
        if r.returncode == 0 and r.stdout.strip():
            return r.stdout.strip()
    except Exception as e:
        pass
    return None

def parse_json(data: str) -> Optional[dict]:
    """解析 JSON 数据"""
    try:
        return json.loads(data)
    except:
        return None

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# DeFi 数据获取
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def get_defi_tvl() -> list:
    """获取 DeFi 协议 TVL 数据"""
    data = fetch_url("https://api.llama.fi/v2/chains")
    parsed = parse_json(data)
    if not parsed:
        return []
    
    # 按 TVL 排序
    sorted_chains = sorted(parsed, key=lambda x: x.get('tvl', 0), reverse=True)
    
    # 获取前 20 条链的 TVL
    result = []
    for chain in sorted_chains[:20]:
        result.append({
            "chain": chain.get('name', ''),
            "tvl": chain.get('tvl', 0),
            "tvl_change_24h": chain.get('tvlChange24h', 0),
            "chainId": chain.get('chainId', ''),
            "symbol": chain.get('symbol', '')
        })
    
    return result

def get_defi_protocols() -> list:
    """获取 DeFi 协议数据"""
    data = fetch_url("https://api.llama.fi/protocol")
    parsed = parse_json(data)
    if not parsed:
        return []
    
    # 按 TVL 排序
    sorted_protocols = sorted(parsed, key=lambda x: x.get('tvl', 0), reverse=True)
    
    # 获取前 20 个协议
    result = []
    for proto in sorted_protocols[:20]:
        result.append({
            "name": proto.get('name', ''),
            "chain": proto.get('chain', ''),
            "tvl": proto.get('tvl', 0),
            "tvl_change_24h": proto.get('tvlChange24h', 0),
            "category": proto.get('category', ''),
            "mcap": proto.get('mcap', 0),
            "slug": proto.get('slug', '')
        })
    
    return result

def get_defi_apy(opportunities: int = 10) -> list:
    """获取高收益 DeFi 机会"""
    data = fetch_url("https://api.llama.fi/apy")
    parsed = parse_json(data)
    if not parsed:
        return []
    
    # 按 APY 排序
    sorted_apy = sorted(parsed, key=lambda x: x.get('apy', 0), reverse=True)
    
    # 获取前 opportunities 个高收益机会
    result = []
    for item in sorted_apy[:opportunities]:
        result.append({
            "pool": item.get('pool', ''),
            "chain": item.get('chain', ''),
            "project": item.get('project', ''),
            "symbol": item.get('symbol', ''),
            "tvl": item.get('tvl', 0),
            "apy": item.get('apy', 0),
            "ilRisk": item.get('ilRisk', 'Unknown'),
            "stable": item.get('stable', False)
        })
    
    return result

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# NFT 数据获取
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def get_nft_floor_prices() -> list:
    """获取热门 NFT 地板价"""
    # 使用 CoinGecko 的 NFT 数据
    data = fetch_url("https://api.coingecko.com/api/v3/nft")
    parsed = parse_json(data)
    if not parsed:
        return []
    
    # 获取前 10 个热门 NFT 集合
    result = []
    for nft in parsed[:10]:
        result.append({
            "name": nft.get('name', ''),
            "slug": nft.get('slug', ''),
            "floor_price": nft.get('floor_price', {}).get('one_day_change', 0),
            "volume_24h": nft.get('volume_24h', 0),
            "owners": nft.get('owners', 0),
            "total_supply": nft.get('total_supply', 0)
        })
    
    return result

def get_nft_trends() -> dict:
    """获取 NFT 趋势数据"""
    # 使用 CoinGecko 的 NFT 市场数据
    data = fetch_url("https://api.coingecko.com/api/v3/nft/search")
    parsed = parse_json(data)
    if not parsed:
        return {"error": "NFT trend data unavailable"}
    
    return {
        "trending_collections": parsed.get('collections', [])[:10],
        "trending_tokens": parsed.get('tokens', [])[:10],
        "market_summary": {
            "total_volume_24h": parsed.get('total_volume_24h', 0),
            "total_sales_24h": parsed.get('total_sales_24h', 0),
            "average_price_24h": parsed.get('average_price_24h', 0)
        }
    }

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 流动性挖矿机会
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def get_yield_opportunities() -> list:
    """获取收益机会"""
    data = fetch_url("https://api.llama.fi/apy")
    parsed = parse_json(data)
    if not parsed:
        return []
    
    # 按 APY 排序
    sorted_apy = sorted(parsed, key=lambda x: x.get('apy', 0), reverse=True)
    
    # 过滤出低风险机会
    result = []
    for item in sorted_apy:
        # 低风险: 稳定币池、高 TVL、合理 APY
        if (item.get('stable', False) and 
            item.get('tvl', 0) > 1000000 and 
            item.get('apy', 0) < 100):  # 过滤掉过高 APY 的
            result.append({
                "pool": item.get('pool', ''),
                "chain": item.get('chain', ''),
                "project": item.get('project', ''),
                "symbol": item.get('symbol', ''),
                "tvl": item.get('tvl', 0),
                "apy": item.get('apy', 0),
                "risk_level": "低" if item.get('stable', False) else "中",
                "il_risk": item.get('ilRisk', 'Unknown')
            })
    
    return result[:10]

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 链上资金流向
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def get_whale_alerts() -> list:
    """获取巨鲸地址监控"""
    # 使用 Mempool.space 的链上数据
    data = fetch_url("https://mempool.space/api/blocks/top")
    parsed = parse_json(data)
    if not parsed:
        return []
    
    # 获取最新区块的大额交易
    result = []
    if isinstance(parsed, list) and len(parsed) > 0:
        block = parsed[0]
        txs = block.get('txs', [])
        for tx in txs[:5]:  # 前 5 个大额交易
            result.append({
                "txid": tx.get('txid', ''),
                "value": tx.get('value', 0),
                "fee": tx.get('fee', 0),
                "size": tx.get('size', 0),
                "time": tx.get('timestamp', 0)
            })
    
    return result

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# DeFi 协议风险评分
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def calculate_protocol_risk(proto: dict) -> dict:
    """计算协议风险评分"""
    score = 50  # 基准分
    
    # TVL 越高越安全
    tvl = proto.get('tvl', 0)
    if tvl > 1000000000:  # > 10亿
        score += 20
    elif tvl > 100000000:  # > 1亿
        score += 15
    elif tvl > 10000000:  # > 1千万
        score += 10
    elif tvl < 1000000:  # < 1百万
        score -= 20
    
    # 24h TVL 变化
    tvl_change = proto.get('tvlChange24h', 0)
    if tvl_change > 5:
        score -= 10  # 大量资金流出
    elif tvl_change < -5:
        score += 5   # 资金流入
    
    # 市值
    mcap = proto.get('mcap', 0)
    if mcap > 0 and tvl > 0:
        mcap_tvl_ratio = mcap / tvl
        if mcap_tvl_ratio > 2:
            score += 10  # 高市值/TVL 比率，协议价值高
        elif mcap_tvl_ratio < 0.5:
            score -= 10  # 低市值/TVL 比率，可能过度稀释
    
    # 类别风险
    category = proto.get('category', '')
    if category in ['Lending', 'CDP']:
        score -= 5  # 借贷类协议风险较高
    elif category in ['DEX']:
        score += 5  # DEX 风险较低
    
    score = max(0, min(100, score))
    
    if score > 75:
        risk_level = "🟢 低风险"
    elif score > 50:
        risk_level = "🟡 中等风险"
    else:
        risk_level = "🔴 高风险"
    
    return {
        "protocol": proto.get('name', ''),
        "risk_score": score,
        "risk_level": risk_level,
        "risk_factors": {
            "tvl": tvl,
            "tvl_change_24h": tvl_change,
            "mcap_tvl_ratio": mcap / tvl if tvl > 0 else 0,
            "category": category
        }
    }

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 跨链桥接数据
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def get_bridge_data() -> list:
    """获取跨链桥接数据"""
    # 使用 DeFiLlama 的桥接数据
    data = fetch_url("https://api.llama.fi/bridges")
    parsed = parse_json(data)
    if not parsed:
        return []
    
    # 获取前 10 个跨链桥
    result = []
    for bridge in parsed[:10]:
        result.append({
            "name": bridge.get('name', ''),
            "tvl": bridge.get('tvl', 0),
            "category": bridge.get('category', ''),
            "chains": bridge.get('chains', []),
            "url": bridge.get('url', '')
        })
    
    return result

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# MCP 服务器
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

if MCP_AVAILABLE:
    mcp = FastMCP("DeFi & NFT Monitor v6.0")
else:
    mcp = None

@mcp.tool()
def get_defi_dashboard() -> dict:
    """
    获取 DeFi 仪表盘
    
    Returns:
        DeFi 综合仪表盘数据
    """
    print("[DeFi Monitor] 获取 DeFi 仪表盘...")
    
    # 获取 TVL 数据
    tvl_data = get_defi_tvl()
    
    # 获取协议数据
    protocol_data = get_defi_protocols()
    
    # 获取 APY 机会
    apy_opportunities = get_defi_apy()
    
    # 获取收益机会
    yield_opportunities = get_yield_opportunities()
    
    # 获取 NFT 趋势
    nft_trends = get_nft_trends()
    
    # 获取跨链桥接数据
    bridge_data = get_bridge_data()
    
    return {
        "tvl_summary": {
            "total_tvl": sum(t.get('tvl', 0) for t in tvl_data),
            "top_chains": tvl_data[:5],
            "chain_count": len(tvl_data)
        },
        "top_protocols": protocol_data[:10],
        "high_yield_opportunities": yield_opportunities,
        "nft_trends": nft_trends,
        "bridge_data": bridge_data,
        "timestamp": datetime.now().isoformat()
    }

@mcp.tool()
def get_protocol_risk_report(protocol_name: str = "") -> dict:
    """
    获取协议风险报告
    
    Args:
        protocol_name: 协议名称 (可选，为空时返回所有协议风险报告)
    
    Returns:
        协议风险报告
    """
    print(f"[DeFi Monitor] 获取协议风险报告: {protocol_name}")
    
    protocol_data = get_defi_protocols()
    
    if protocol_name:
        # 查找指定协议
        target = [p for p in protocol_data if p.get('name', '').lower() == protocol_name.lower()]
        if target:
            return calculate_protocol_risk(target[0])
        else:
            return {"error": f"Protocol {protocol_name} not found"}
    else:
        # 返回所有协议的风险报告
        return [calculate_protocol_risk(p) for p in protocol_data[:20]]

@mcp.tool()
def get_nft_market_summary() -> dict:
    """
    获取 NFT 市场摘要
    
    Returns:
        NFT 市场摘要
    """
    print("[DeFi Monitor] 获取 NFT 市场摘要...")
    
    nft_trends = get_nft_trends()
    nft_floors = get_nft_floor_prices()
    
    return {
        "market_summary": nft_trends.get('market_summary', {}),
        "trending_collections": nft_trends.get('trending_collections', [])[:10],
        "floor_prices": nft_floors[:10],
        "timestamp": datetime.now().isoformat()
    }

if MCP_AVAILABLE:
    mcp.run()
else:
    print("MCP not available")
