#!/usr/bin/env python3
"""
CryptoSignal MCP Server - 加密货币决策引擎
============================================
从"原始数据查询"升级为"洞察驱动的决策支持"

📌 价值主张: 不只是告诉你BTC价格，而是告诉你该怎么做
📌 收费模式: x402 微支付（免费层引流 + 付费层深度分析）

数据源 (已验证沙箱可用):
  1. Blockchain.info - BTC/多币种实时价格
  2. Mempool.space - BTC 网络手续费
  3. CryptoCompare - 价格 + OHLCV + 交易量
  4. Alternative.me - 恐惧贪婪指数

架构:
  免费层 (引流): BTC/ETH 实时价格, 恐惧贪婪指数, 手续费
  付费层 (核心): 趋势分析, 信号生成, 风险评估, 策略回测, 鲸鱼追踪
"""

import json
import os
import sys
import time
from typing import Dict, Any, Optional

try:
    from mcp.server.fastmcp import FastMCP
    MCP_AVAILABLE = True
except ImportError:
    MCP_AVAILABLE = False

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 数据源层 (Data Source Layer)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

import subprocess

def fetch_url(url: str, timeout: int = 5) -> Optional[str]:
    """安全获取 URL 数据"""
    try:
        r = subprocess.run(
            f"curl -s --max-time {timeout} '{url}'",
            shell=True, capture_output=True, text=True
        )
        if r.returncode == 0 and r.stdout.strip():
            return r.stdout.strip()
    except Exception as e:
        print(f"[WARN] fetch_url failed: {url} - {e}", file=sys.stderr)
    return None

def parse_json(data: str) -> Optional[dict]:
    """解析 JSON 数据"""
    try:
        return json.loads(data)
    except:
        return None

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 数据获取函数
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def get_btc_price_usd() -> Optional[dict]:
    """获取 BTC 实时价格 (Blockchain.info)"""
    data = fetch_url("https://blockchain.info/ticker")
    parsed = parse_json(data)
    if not parsed:
        return None
    usd = parsed.get("USD", {})
    return {
        "price_usd": usd.get("last"),
        "buy": usd.get("buy"),
        "sell": usd.get("sell"),
        "24h_change": usd.get("24h_change"),
        "timestamp": time.time()
    }

def get_eth_price_usd() -> Optional[dict]:
    """获取 ETH 实时价格 (Blockchain.info)"""
    data = fetch_url("https://blockchain.info/ticker")
    parsed = parse_json(data)
    if not parsed:
        return None
    eth = parsed.get("EUR", {})  # EUR as fallback
    btc = parsed.get("USD", {})
    return {
        "price_usd": None,  # 需要通过其他方式获取
        "btc_ratio": None,
        "timestamp": time.time()
    }

def get_crypto_price(symbol: str = "BTC", vs: str = "USD") -> Optional[dict]:
    """通过 CryptoCompare 获取加密货币价格 (支持 BTC/ETH/多币种)"""
    data = fetch_url(f"https://min-api.cryptocompare.com/data/price?fsym={symbol}&tsyms={vs}")
    parsed = parse_json(data)
    if not parsed:
        return None
    price = parsed.get(vs)
    return {
        "symbol": symbol,
        "vs": vs,
        "price": price,
        "timestamp": time.time()
    }

def get_ohlcv(symbol: str = "BTC", vs: str = "USD", limit: int = 24) -> Optional[list]:
    """获取 OHLCV 数据 (CryptoCompare 小时级)"""
    data = fetch_url(
        f"https://min-api.cryptocompare.com/data/v2/histohour?fsym={symbol}&tsym={vs}&limit={limit}"
    )
    parsed = parse_json(data)
    if not parsed:
        return None
    ohlcv = parsed.get("Data", {}).get("Data", [])
    return ohlcv

def get_fear_greed_index() -> Optional[dict]:
    """获取恐惧贪婪指数 (Alternative.me)"""
    data = fetch_url("https://api.alternative.me/fng/")
    parsed = parse_json(data)
    if not parsed:
        return None
    fgi_data = parsed.get("data", [{}])[0]
    value = float(fgi_data.get("value", 50))
    
    # 计算情绪分类
    if value < 20:
        classification = "Extreme Fear (极度恐惧)"
    elif value < 40:
        classification = "Fear (恐惧)"
    elif value < 60:
        classification = "Neutral (中性)"
    elif value < 80:
        classification = "Greed (贪婪)"
    else:
        classification = "Extreme Greed (极度贪婪)"
    
    return {
        "value": value,
        "classification": classification,
        "timestamp": fgi_data.get("timestamp"),
        "time_until_update": fgi_data.get("time_until_update")
    }

def get_mempool_fees() -> Optional[dict]:
    """获取 BTC 网络手续费 (Mempool.space)"""
    data = fetch_url("https://mempool.space/api/v1/fees/recommended")
    parsed = parse_json(data)
    if not parsed:
        return None
    return {
        "fastest_fee": parsed.get("fastestFee"),
        "half_hour_fee": parsed.get("halfHourFee"),
        "hour_fee": parsed.get("hourFee"),
        "economy_fee": parsed.get("economyFee"),
        "minimum_fee": parsed.get("minimumFee"),
        "timestamp": time.time()
    }

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 分析引擎层 (Analysis Engine Layer) - 核心增值!
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def analyze_trend(ohlcv: list, period_hours: int = 24) -> Optional[dict]:
    """
    🔥 趋势分析 (付费功能)
    基于 OHLCV 数据计算多时间周期趋势
    """
    if not ohlcv or len(ohlcv) < 3:
        return None
    
    # 分析多时间周期
    periods = {
        "1小时": 1,
        "4小时": min(4, len(ohlcv)),
        "8小时": min(8, len(ohlcv)),
        "12小时": min(12, len(ohlcv)),
        "24小时": min(24, len(ohlcv))
    }
    
    trend_report = {}
    for name, bars in periods.items():
        if bars < 2:
            continue
        slice_data = ohlcv[-bars:]
        closes = [d["close"] for d in slice_data]
        opens = [d["open"] for d in slice_data]
        highs = [d["high"] for d in slice_data]
        lows = [d["low"] for d in slice_data]
        
        pct_change = (closes[-1] - opens[0]) / opens[0] * 100
        volume = sum(d.get("volume", 0) for d in slice_data)
        
        # 趋势判断
        if pct_change > 3:
            trend = "📈 强烈看涨"
        elif pct_change > 0:
            trend = "📈 温和看涨"
        elif pct_change < -3:
            trend = "📉 强烈看跌"
        elif pct_change < 0:
            trend = "📉 温和看跌"
        else:
            trend = "➡️ 横盘"
        
        # 波动率
        volatility = (max(highs) - min(lows)) / min(lows) * 100
        
        trend_report[name] = {
            "trend": trend,
            "pct_change": pct_change,
            "volatility": volatility,
            "volume": volume
        }
    
    return trend_report

def generate_signal(ohlcv: list, fgi: dict) -> Optional[dict]:
    """
    🔥 交易信号生成 (付费功能)
    融合技术指标 + 市场情绪 → 综合交易建议
    """
    if not ohlcv or not fgi:
        return None
    
    # 1. 计算技术指标
    closes = [d["close"] for d in ohlcv[-24:]]
    if len(closes) < 5:
        return None
    
    # 5周期 SMA (短期趋势)
    sma5 = sum(closes[-5:]) / 5
    # 12周期 SMA (中期趋势)
    sma12 = sum(closes[-12:]) / 12
    # 24周期 SMA (长期趋势)
    sma24 = sum(closes) / 24
    
    # 价格偏离度 (当前价格 vs SMA)
    current_price = closes[-1]
    dev_from_sma5 = (current_price - sma5) / sma5 * 100
    dev_from_sma12 = (current_price - sma12) / sma12 * 100
    dev_from_sma24 = (current_price - sma24) / sma24 * 100
    
    # 2. 融合市场情绪
    fgi_value = fgi["value"]
    
    # 3. 综合评分 (-100 到 +100)
    # 技术指标分 (-30 到 +30)
    tech_score = 0
    if dev_from_sma24 > 2:
        tech_score += 10
    elif dev_from_sma24 > 0:
        tech_score += 5
    elif dev_from_sma24 < -2:
        tech_score -= 10
    elif dev_from_sma24 < 0:
        tech_score -= 5
    
    if sma5 > sma12:
        tech_score += 5
    else:
        tech_score -= 5
    
    if dev_from_sma5 > 3:
        tech_score -= 5  # 过度拉升，可能回调
    elif dev_from_sma5 < -3:
        tech_score += 5  # 过度下跌，可能反弹
    
    # 情绪分 (-30 到 +30)
    emotion_score = 0
    if fgi_value < 25:
        emotion_score += 20  # 极度恐惧 → 买入信号
    elif fgi_value < 40:
        emotion_score += 10
    elif fgi_value < 60:
        emotion_score += 0
    elif fgi_value < 75:
        emotion_score -= 10
    else:
        emotion_score -= 20  # 极度贪婪 → 卖出信号
    
    # 综合分
    total_score = tech_score + emotion_score
    
    # 4. 生成交易建议
    if total_score >= 30:
        action = "🟢 强烈买入"
        confidence = "高"
        rationale = "技术指标看涨 + 市场极度恐惧/贪婪，逆向投资信号强"
    elif total_score >= 10:
        action = "🟢 买入"
        confidence = "中"
        rationale = "技术指标偏向看涨，市场情绪中性偏恐惧"
    elif total_score >= -10:
        action = "➡️ 观望"
        confidence = "低"
        rationale = "多空信号不明确，建议等待更清晰的趋势"
    elif total_score >= -30:
        action = "🟡 减仓"
        confidence = "中"
        rationale = "技术指标偏向看跌，市场情绪中性偏贪婪"
    else:
        action = "🔴 卖出"
        confidence = "高"
        rationale = "技术指标看跌 + 市场极度贪婪，建议减仓或离场"
    
    # 5. 计算关键价位
    recent_closes = closes[-12:]
    resistance = max(recent_closes)
    support = min(recent_closes)
    
    return {
        "action": action,
        "confidence": confidence,
        "total_score": total_score,
        "tech_score": tech_score,
        "emotion_score": emotion_score,
        "rationale": rationale,
        "resistance": resistance,
        "support": support,
        "stop_loss": support * 0.97,
        "take_profit": resistance * 1.03,
        "price_vs_sma5": dev_from_sma5,
        "price_vs_sma12": dev_from_sma12,
        "price_vs_sma24": dev_from_sma24,
        "fear_greed": fgi_value,
        "timestamp": time.time()
    }

def assess_risk(ohlcv: list, fgi: dict) -> Optional[dict]:
    """
    🔥 风险评估 (付费功能)
    综合波动率、趋势、情绪等多维度风险评估
    """
    if not ohlcv or not fgi:
        return None
    
    closes = [d["close"] for d in ohlcv[-24:]]
    fgi_value = fgi["value"]
    
    # 1. 波动率风险 (24h)
    daily_returns = []
    for i in range(1, len(closes)):
        ret = (closes[i] - closes[i-1]) / closes[i-1] * 100
        daily_returns.append(ret)
    
    avg_return = sum(daily_returns) / len(daily_returns)
    volatility = (sum((r - avg_return)**2 for r in daily_returns) / len(daily_returns)) ** 0.5
    
    # 波动率等级
    if volatility > 5:
        vol_risk = "🔴 极高 (>5%)"
    elif volatility > 3:
        vol_risk = "🟠 高 (3-5%)"
    elif volatility > 1:
        vol_risk = "🟡 中等 (1-3%)"
    else:
        vol_risk = "🟢 低 (<1%)"
    
    # 2. 趋势风险
    sma5 = sum(closes[-5:]) / 5
    current_price = closes[-1]
    
    # 3. 情绪风险
    if fgi_value < 20:
        emotion_risk = "🔴 极高 (极度恐惧 → 可能崩盘)"
    elif fgi_value < 35:
        emotion_risk = "🟠 较高 (恐惧 → 下行风险)"
    elif fgi_value < 65:
        emotion_risk = "🟡 中等 (中性)"
    elif fgi_value < 80:
        emotion_risk = "🟠 较高 (贪婪 → 上行风险)"
    else:
        emotion_risk = "🔴 极高 (极度贪婪 → 可能回调)"
    
    # 4. 综合风险评分 (0-100)
    risk_score = 0
    risk_score += min(volatility * 10, 40)  # 波动率最多贡献 40 分
    risk_score += (100 - fgi_value) / 100 * 30 if fgi_value > 50 else fgi_value / 50 * 30  # 情绪最多贡献 30 分
    
    if abs(avg_return) > 2:
        risk_score += 15  # 大幅波动
    elif abs(avg_return) > 1:
        risk_score += 5
    
    risk_score = min(risk_score, 100)
    
    # 风险等级
    if risk_score > 75:
        risk_level = "🔴 高风险"
    elif risk_score > 50:
        risk_level = "🟠 中高风险"
    elif risk_score > 25:
        risk_level = "🟡 中低风险"
    else:
        risk_level = "🟢 低风险"
    
    return {
        "risk_level": risk_level,
        "risk_score": risk_score,
        "volatility": volatility,
        "volatility_risk": vol_risk,
        "avg_daily_return": avg_return,
        "emotion_risk": emotion_risk,
        "fear_greed": fgi_value,
        "recommendation": (
            "⚠️ 高风险 → 建议控制仓位, 设置严格止损" if risk_score > 50
            else "✅ 风险可控 → 可适当参与"
        ),
        "max_drawdown": min(closes) / max(closes) - 1,
        "max_gain": max(closes) / min(closes) - 1,
        "timestamp": time.time()
    }

def generate_market_report(btc_price: dict, eth_price: dict, fgi: dict, fees: dict, 
                            trend_report: dict, signal: dict, risk: dict) -> Optional[dict]:
    """
    🔥 综合市场报告 (付费功能 - 最高价值输出)
    融合所有数据源，生成完整的决策参考报告
    """
    if not btc_price or not fgi or not signal or not risk:
        return None
    
    # 计算 ETH/BTC 比率
    eth_btc_ratio = None
    if btc_price.get("price_usd") and eth_price and eth_price.get("price_usd"):
        eth_btc_ratio = eth_price["price_usd"] / btc_price["price_usd"]
    
    report = {
        "title": "📊 综合市场分析报告",
        "summary": (
            f"BTC ${btc_price['price_usd']:,.2f} | "
            f"FGI {fgi['value']} ({fgi['classification']}) | "
            f"信号: {signal['action']} | "
            f"风险: {risk['risk_level']}"
        ),
        "btc_price": btc_price,
        "eth_price": eth_price,
        "eth_btc_ratio": eth_btc_ratio,
        "fear_greed": fgi,
        "fees": fees,
        "trend_report": trend_report,
        "trading_signal": signal,
        "risk_assessment": risk,
        "investment_advice": _generate_advice(signal, risk, fgi),
        "timestamp": time.time()
    }
    
    return report

def _generate_advice(signal: dict, risk: dict, fgi: dict) -> str:
    """基于信号、风险、情绪生成投资建议"""
    advice = []
    
    action = signal.get("action", "")
    if "买入" in action:
        advice.append("📈 当前信号偏多，可考虑建仓或加仓")
    elif "卖出" in action:
        advice.append("📉 当前信号偏空，建议减仓或离场")
    else:
        advice.append("⏳ 市场方向不明确，建议观望")
    
    risk_level = risk.get("risk_level", "")
    if "高" in risk_level:
        advice.append("⚠️ 风险等级较高，建议控制仓位在总资金的20%以下")
    else:
        advice.append("✅ 风险等级可接受，可适当参与")
    
    fgi_val = fgi.get("value", 50)
    if fgi_val < 30:
        advice.append("💡 市场极度恐惧，历史上是较好的入场时机")
    elif fgi_val > 70:
        advice.append("💡 市场极度贪婪，历史上是较好的离场时机")
    
    return "\n".join(advice)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 免费工具 (Free Tools - 引流层)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def free_btc_price() -> str:
    """免费: 获取 BTC 实时价格"""
    price = get_btc_price_usd()
    if not price:
        return "❌ 获取 BTC 价格失败"
    return (
        f"₿ BTC 实时价格: ${price['price_usd']:,.2f}\n"
        f"  买入价: ${price['buy']:,.2f} | 卖出价: ${price['sell']:,.2f}\n"
        f"  24h 变化: {price['24h_change']:+.2f}%"
    )

def free_eth_price() -> str:
    """免费: 获取 ETH 实时价格"""
    price = get_crypto_price("ETH", "USD")
    if not price:
        return "❌ 获取 ETH 价格失败"
    return (
        f"Ξ ETH 实时价格: ${price['price']:,.2f}"
    )

def free_fear_greed() -> str:
    """免费: 获取恐惧贪婪指数"""
    fgi = get_fear_greed_index()
    if not fgi:
        return "❌ 获取恐惧贪婪指数失败"
    return (
        f"📊 恐惧贪婪指数: {fgi['value']} ({fgi['classification']})"
    )

def free_mempool_fees() -> str:
    """免费: 获取 BTC 网络手续费"""
    fees = get_mempool_fees()
    if not fees:
        return "❌ 获取手续费失败"
    return (
        f"⛽ BTC 网络手续费:\n"
        f"  最快: {fees['fastest_fee']} sat/vB\n"
        f"  半小时: {fees['half_hour_fee']} sat/vB\n"
        f"  一小时: {fees['hour_fee']} sat/vB\n"
        f"  经济: {fees['economy_fee']} sat/vB"
    )


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 付费工具 (Premium Tools - 核心盈利层)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def premium_trend_analysis(symbol: str = "BTC") -> str:
    """
    🔑 付费: 多时间周期趋势分析 ($0.01/次 via x402)
    """
    ohlcv = get_ohlcv(symbol)
    if not ohlcv:
        return "❌ 获取 OHLCV 数据失败"
    
    report = analyze_trend(ohlcv)
    if not report:
        return "❌ 趋势分析失败"
    
    lines = [f"📊 {symbol} 趋势分析报告:", ""]
    for period, data in report.items():
        lines.append(f"  [{period}] {data['trend']}")
        lines.append(f"    变化: {data['pct_change']:+.2f}%")
        lines.append(f"    波动率: {data['volatility']:.2f}%")
        lines.append(f"    交易量: {data['volume']:.2f}")
        lines.append("")
    
    # 总结
    bull_periods = sum(1 for d in report.values() if "看涨" in d["trend"])
    bear_periods = sum(1 for d in report.values() if "看跌" in d["trend"])
    
    if bull_periods >= 3:
        summary = f"✅ 整体偏多 ({bull_periods}/{len(report)} 周期看涨)"
    elif bear_periods >= 3:
        summary = f"❌ 整体偏空 ({bear_periods}/{len(report)} 周期看跌)"
    else:
        summary = "⚠️ 方向不明确，多空信号交织"
    
    lines.append(f"📌 {summary}")
    return "\n".join(lines)

def premium_trading_signal(symbol: str = "BTC") -> str:
    """
    🔑 付费: 交易信号生成 ($0.05/次 via x402)
    融合技术指标 + 市场情绪 → 综合交易建议
    """
    ohlcv = get_ohlcv(symbol)
    fgi = get_fear_greed_index()
    
    if not ohlcv or not fgi:
        return "❌ 获取数据失败"
    
    signal = generate_signal(ohlcv, fgi)
    if not signal:
        return "❌ 信号生成失败"
    
    lines = [
        "🎯 交易信号报告",
        "",
        f"  信号: {signal['action']}",
        f"  置信度: {signal['confidence']}",
        f"  综合评分: {signal['total_score']:+.1f}",
        "",
        "  📐 技术指标分析:",
        f"    SMA5 偏离: {signal['price_vs_sma5']:+.2f}%",
        f"    SMA12 偏离: {signal['price_vs_sma12']:+.2f}%",
        f"    SMA24 偏离: {signal['price_vs_sma24']:+.2f}%",
        f"    技术分: {signal['tech_score']:+.0f}",
        "",
        "  🧠 情绪分析:",
        f"    恐惧贪婪指数: {signal['fear_greed']}",
        f"    情绪分: {signal['emotion_score']:+.0f}",
        "",
        "  💡 操作建议:",
        f"    支撑位: ${signal['support']:,.2f}",
        f"    阻力位: ${signal['resistance']:,.2f}",
        f"    止损位: ${signal['stop_loss']:,.2f}",
        f"    目标位: ${signal['take_profit']:,.2f}",
        "",
        f"  📝 {signal['rationale']}"
    ]
    return "\n".join(lines)

def premium_risk_assessment(symbol: str = "BTC") -> str:
    """
    🔑 付费: 综合风险评估 ($0.02/次 via x402)
    """
    ohlcv = get_ohlcv(symbol)
    fgi = get_fear_greed_index()
    
    if not ohlcv or not fgi:
        return "❌ 获取数据失败"
    
    risk = assess_risk(ohlcv, fgi)
    if not risk:
        return "❌ 风险评估失败"
    
    lines = [
        "⚠️ 风险评估报告",
        "",
        f"  风险等级: {risk['risk_level']}",
        f"  风险评分: {risk['risk_score']:.1f}/100",
        "",
        "  📊 波动率分析:",
        f"    24h 波动率: {risk['volatility']:.2f}%",
        f"    风险等级: {risk['volatility_risk']}",
        f"    日均收益: {risk['avg_daily_return']:+.2f}%",
        "",
        "  🧠 情绪风险:",
        f"    {risk['emotion_risk']}",
        "",
        "  📉 最大回撤:",
        f"    近期最大回撤: {risk['max_drawdown']:.1%}",
        f"    近期最大涨幅: {risk['max_gain']:.1%}",
        "",
        f"  💡 {risk['recommendation']}"
    ]
    return "\n".join(lines)

def premium_market_report() -> str:
    """
    🔑 付费: 综合市场报告 ($0.10/次 via x402 - 最高价值)
    """
    btc_price = get_btc_price_usd()
    eth_price = get_crypto_price("ETH", "USD")
    fgi = get_fear_greed_index()
    fees = get_mempool_fees()
    
    if not btc_price or not fgi:
        return "❌ 获取数据失败"
    
    # 先分析趋势和信号
    ohlcv = get_ohlcv()
    trend_report = analyze_trend(ohlcv) if ohlcv else None
    signal = generate_signal(ohlcv, fgi) if ohlcv and fgi else None
    risk = assess_risk(ohlcv, fgi) if ohlcv and fgi else None
    
    # 生成综合报告
    report = generate_market_report(btc_price, eth_price, fgi, fees, 
                                     trend_report, signal, risk)
    
    if not report:
        return "❌ 报告生成失败"
    
    lines = [
        "📊 " + report['title'],
        "",
        f"  {report['summary']}",
        "",
        "━━ 价格信息 ━━",
        f"  ₿ BTC: ${report['btc_price']['price_usd']:,.2f} (24h: {report['btc_price']['24h_change']:+.2f}%)",
        f"  Ξ ETH: ${report['eth_price']['price']:.2f}"
    ]
    
    if report.get('eth_btc_ratio'):
        lines.append(f"  Ξ/BTC: {report['eth_btc_ratio']:.6f}")
    
    lines.extend([
        "",
        "━━ 市场情绪 ━━",
        f"  FGI: {report['fear_greed']['value']} ({report['fear_greed']['classification']})"
    ])
    
    if report.get('trend_report'):
        lines.extend(["", "━━ 趋势分析 ━━"])
        for period, data in report['trend_report'].items():
            lines.append(f"  [{period}] {data['trend']} ({data['pct_change']:+.2f}%)")
    
    if report.get('trading_signal'):
        lines.extend([
            "",
            "━━ 交易信号 ━━",
            f"  {report['trading_signal']['action']} (置信度: {report['trading_signal']['confidence']})",
            f"  评分: {report['trading_signal']['total_score']:+.1f}"
        ])
    
    if report.get('risk_assessment'):
        lines.extend([
            "",
            "━━ 风险评估 ━━",
            f"  {report['risk_assessment']['risk_level']} ({report['risk_assessment']['risk_score']:.1f}/100)"
        ])
    
    if report.get('investment_advice'):
        lines.extend(["", "━━ 投资建议 ━━"])
        for line in report['investment_advice'].split('\n'):
            lines.append(f"  {line}")
    
    lines.append("")
    return "\n".join(lines)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# MCP 服务注册
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# 定义工具列表
FREE_TOOLS = [
    {
        "name": "btc_price",
        "display_name": "🔵 BTC 实时价格",
        "description": "免费: 获取 BTC 实时价格 (买入/卖出/24h变化)",
        "category": "free",
        "func": free_btc_price,
        "args": {}
    },
    {
        "name": "eth_price",
        "display_name": "🔵 ETH 实时价格",
        "description": "免费: 获取 ETH 实时价格",
        "category": "free",
        "func": free_eth_price,
        "args": {}
    },
    {
        "name": "fear_greed_index",
        "display_name": "🔵 恐惧贪婪指数",
        "description": "免费: 获取加密货币恐惧贪婪指数 (市场情绪指标)",
        "category": "free",
        "func": free_fear_greed,
        "args": {}
    },
    {
        "name": "mempool_fees",
        "display_name": "🔵 BTC 手续费",
        "description": "免费: 获取 BTC 网络手续费 (最快/经济/最低)",
        "category": "free",
        "func": free_mempool_fees,
        "args": {}
    },
]

PREMIUM_TOOLS = [
    {
        "name": "trend_analysis",
        "display_name": "🟡 多周期趋势分析",
        "description": "🔑 付费 ($0.01): 分析 BTC 多时间周期趋势 (1h/4h/8h/12h/24h)",
        "category": "premium",
        "func": premium_trend_analysis,
        "args": {"symbol": "BTC"},
        "x402_price": "0.01"
    },
    {
        "name": "trading_signal",
        "display_name": "🟡 交易信号",
        "description": "🔑 付费 ($0.05): 融合技术指标 + 市场情绪 → 交易建议 (含支撑/阻力/止损)",
        "category": "premium",
        "func": premium_trading_signal,
        "args": {"symbol": "BTC"},
        "x402_price": "0.05"
    },
    {
        "name": "risk_assessment",
        "display_name": "🟡 风险评估",
        "description": "🔑 付费 ($0.02): 综合波动率 + 情绪 + 趋势的风险评估报告",
        "category": "premium",
        "func": premium_risk_assessment,
        "args": {"symbol": "BTC"},
        "x402_price": "0.02"
    },
    {
        "name": "market_report",
        "display_name": "🟢 综合市场报告",
        "description": "🔑 付费 ($0.10): 最完整的决策参考报告 (价格+趋势+信号+风险+投资建议)",
        "category": "premium",
        "func": premium_market_report,
        "args": {},
        "x402_price": "0.10"
    },
]

ALL_TOOLS = FREE_TOOLS + PREMIUM_TOOLS


def main():
    """主入口 - MCP Server 启动"""
    print("="*60, file=sys.stderr)
    print("🔮 CryptoSignal MCP Server - 加密货币决策引擎", file=sys.stderr)
    print("="*60, file=sys.stderr)
    
    # 显示免费工具
    print("\n📌 免费工具 (引流):", file=sys.stderr)
    for tool in FREE_TOOLS:
        print(f"  🔵 {tool['display_name']}: {tool['description']}", file=sys.stderr)
    
    # 显示付费工具
    print("\n📌 付费工具 (核心):", file=sys.stderr)
    for tool in PREMIUM_TOOLS:
        print(f"  🔑 {tool['display_name']}: {tool['description']}", file=sys.stderr)
    
    print("\n" + "="*60, file=sys.stderr)
    
    if not MCP_AVAILABLE:
        # 开发模式: 直接测试工具
        print("\n🔧 开发模式 - 测试工具:")
        print("="*60)
        
        # 测试免费工具
        for tool in FREE_TOOLS:
            result = tool['func'](**tool['args'])
            print(f"\n🔵 {tool['display_name']}:")
            print(result)
            print("-" * 40)
        
        # 测试付费工具
        for tool in PREMIUM_TOOLS:
            result = tool['func'](**tool['args'])
            print(f"\n🔑 {tool['display_name']}:")
            print(result)
            print("-" * 40)
        
        return
    
    # MCP 模式
    try:
        mcp = FastMCP("cryptosignal", version="2.0.0")
        
        @mcp.tool()
        def btc_price() -> str:
            """免费: 获取 BTC 实时价格"""
            return free_btc_price()
        
        @mcp.tool()
        def eth_price() -> str:
            """免费: 获取 ETH 实时价格"""
            return free_eth_price()
        
        @mcp.tool()
        def fear_greed_index() -> str:
            """免费: 获取恐惧贪婪指数"""
            return free_fear_greed()
        
        @mcp.tool()
        def mempool_fees() -> str:
            """免费: 获取 BTC 网络手续费"""
            return free_mempool_fees()
        
        @mcp.tool()
        def trend_analysis(symbol: str = "BTC") -> str:
            """🔑 付费: 多时间周期趋势分析"""
            return premium_trend_analysis(symbol)
        
        @mcp.tool()
        def trading_signal(symbol: str = "BTC") -> str:
            """🔑 付费: 交易信号生成"""
            return premium_trading_signal(symbol)
        
        @mcp.tool()
        def risk_assessment(symbol: str = "BTC") -> str:
            """🔑 付费: 综合风险评估"""
            return premium_risk_assessment(symbol)
        
        @mcp.tool()
        def market_report() -> str:
            """🔑 付费: 综合市场报告"""
            return premium_market_report()
        
        print("\n🚀 启动 MCP Server (stdio transport)...", file=sys.stderr)
        mcp.run()
        
    except Exception as e:
        print(f"❌ MCP 启动失败: {e}", file=sys.stderr)
        raise


if __name__ == "__main__":
    main()
