# 🇨🇳 ChinaIntel MCP Server

中文市场情报 MCP Server - 针对中文市场的舆情监控、趋势分析和情报聚合工具。

## 🎯 核心功能

| 工具 | 描述 |
|------|------|
| `get_chinese_crypto_sentiment` | 获取中文加密市场舆情分析 |
| `get_mcp_ecosystem_trends` | 获取 MCP 生态系统趋势 |
| `get_crypto_market_summary_tool` | 获取加密市场实时摘要 |
| `analyze_crypto_sentiment_from_text` | 分析给定文本的情绪 |
| `get_github_trending_crypto` | 获取 GitHub 加密相关热门项目 |
| `get_cryptocompare_data` | 从 CryptoCompare 获取加密数据 |
| `generate_market_intelligence_report` | 生成综合市场情报报告 |

## 📡 数据源

- **GitHub API**: MCP 项目趋势、项目热度
- **Blockchain.info**: 实时价格
- **CryptoCompare**: 详细市场数据
- **Hacker News**: 技术趋势
- **Alternative.me**: 恐惧贪婪指数

## 🚀 安装

```bash
pip install mcp fastmcp
cd mcp-servers/china-intel-server
python server.py
```

## 📊 市场优势分析

### 竞品对比

| 竞品 | Stars | 定位 | 不足 |
|------|-------|------|------|
| kukapay/crypto-sentiment-mcp | 47 | 英文情绪分析 | 仅限英文 |
| kukapay/cryptopanic-mcp-server | 71 | 英文新闻聚合 | 仅限英文 |
| kukapay/crypto-indicators-mcp | 122 | 技术指标 | 无中文支持 |
| armorwallet/armor-crypto-mcp | 182 | 钱包工具 | 非情报类 |
| **ChinaIntel (本工具)** | N/A | **中文市场情报** | **填补中文空白** |

### 市场机会

1. **中文市场空白**: 现有 MCP 生态工具几乎全部面向英文市场，中文市场情报工具严重缺失
2. **加密市场中文用户**: 全球最大加密交易群体之一（中国、台湾、香港、东南亚）
3. **差异化优势**: 结合 GitHub 项目热度 + 恐惧贪婪指数 + 情绪分析的多维度情报
4. **变现潜力**: 通过 x402 微支付提供高级情报订阅服务

## 💰 商业模式

- **免费层**: 基础市场摘要、恐惧贪婪指数
- **订阅层**: 综合情报报告、实时舆情监控
- **企业层**: 定制情报推送、API 接入

## 📝 License

MIT
