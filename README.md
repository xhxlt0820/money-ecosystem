<div align="center">

# 🤖 Money Ecosystem

### 基于 Hermes Agent + MCP 协议的中文 AI 技能市场

> **让 AI Agent 自己赚钱**
> 
> 通过 MCP Server 生态 + x402 微支付协议，构建自动化的数据变现网络

[![Python 3.12](https://img.shields.io/badge/Python-3.12-blue?style=flat-square)](https://python.org)
[![MCP Server](https://img.shields.io/badge/MCP-Server-green?style=flat-square)](https://modelcontextprotocol.io)
[![x402 Micro-payments](https://img.shields.io/badge/x402-Micro--Payments-purple?style=flat-square)](https://x402.dev)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow?style=flat-square)](LICENSE)
[![Hermes Agent](https://img.shields.io/badge/Agent-Hermes-red?style=flat-square)](https://github.com/NousResearch/hermes-agent)

</div>

---

## 🎯 一句话介绍

**Money Ecosystem** 是一个由 AI Agent 自主开发、运营和盈利的 MCP Server 生态项目。
它集成了中文数据获取、加密货币分析、DeFi/NFT 监控、技能市场等功能模块，
通过 **x402 微支付协议**实现链上自动收款，打造中文 AI 数据服务的「最小可行性变现闭环」。

## 🔥 为什么这个项目值得关注

| 维度 | 传统方案 | Money Ecosystem |
|------|----------|-----------------|
| **开发主体** | 人类工程师 | **AI Agent 自主开发** |
| **数据成本** | API 订阅 $500+/月 | **全部免费数据源，$0 成本** |
| **部署复杂度** | 需要运维团队 | **一键部署，Python 即可** |
| **变现模式** | 人工运营 | **x402 链上自动收款** |
| **维护成本** | 持续人力投入 | **Agent 持续迭代升级** |
| **市场定位** | 通用数据服务 | **深耕中文+加密货币蓝海** |

## 📦 生态架构

```
┌─────────────────────────────────────────────────────────┐
│                   Money Ecosystem                       │
│                                                         │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐ │
│  │   v5.0       │  │   v6.0       │  │   v7.0       │ │
│  │ CryptoSignal │  │ DeFi/NFT     │  │ SkillMarket  │ │
│  │ 信号分析引擎  │  │ 监控中心     │  │ 技能市场     │ │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘ │
│         │                  │                  │         │
│         └──────────────────┼──────────────────┘         │
│                            │                             │
│                    ┌───────▼───────┐                     │
│                    │  x402 微支付  │                     │
│                    │   收款网络    │                     │
│                    └───────────────┘                     │
│                                                         │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐ │
│  │ China Intel  │  │Chinese News  │  │  Public Data │ │
│  │ 中文情报中心  │  │ 中文新闻聚合  │  │  公共数据API  │ │
│  └──────────────┘  └──────────────┘  └──────────────┘ │
└─────────────────────────────────────────────────────────┘
```

## 🧩 生态工具

### [prompt-optimizer](https://github.com/xhxlt0820/prompt-optimizer)
AI Prompt质量分析器与优化工具 - CLI工具，帮助提升AI使用效果

### [ai-earner-store](https://github.com/xhxlt0820/ai-earner-store)
AI Prompt商店 - 高质量提示词产品合集

## 📚 功能模块

### 🚀 v5.0 — CryptoSignal 加密货币信号分析引擎

> 实时链上数据 → 多维度技术指标 → 交易信号输出

| 功能 | 说明 |
|------|------|
| ⏱️ 多时间框架分析 | 1h/4h/1d 趋势研判 |
| 📊 16+ 技术指标 | RSI, MACD, Bollinger, EMA, OBV, VWAP, KDJ... |
| 🎯 置信度评分 | 信号强度 0-100，辅助决策 |
| ⚠️ 风险评估矩阵 | 多空信号 + 入场/止损/止盈建议 |
| 🔄 市场周期检测 | 牛市/熊市/震荡期自动识别 |
| 📡 链上异动追踪 | 大额转账、鲸鱼动向实时监控 |

### 🔍 v6.0 — DeFi/NFT 监控中心

> DeFi 收益挖矿 + NFT 地板价追踪

| 功能 | 说明 |
|------|------|
| 💰 TVL 追踪 | Top 50 DeFi 协议实时 TVL |
| 📈 APY 监控 | 各协议挖矿收益率变动 |
| 🖼️ NFT Floor | 热门 NFT 系列地板价追踪 |
| 📊 市场情绪 | Fear & Greed Index + 链上数据 |

### 🎪 v7.0 — 技能市场 (Skill Market)

> MCP 技能的去中心化交易市场

| 功能 | 说明 |
|------|------|
| 📦 技能上架/下架 | 开发者自主发布技能 |
| 💎 技能搜索/筛选 | 按分类、价格、评分查找 |
| 💰 x402 微支付 | 每次调用自动结算 |
| ⭐ 技能评价 | 社区评分和反馈机制 |

### 📰 China Intel — 中文市场情报中心

> 中文舆情监控 + 趋势分析 + 商业情报

| 数据源 | 类型 | 状态 |
|--------|------|------|
| 微博热搜 | 社会舆情 | ✅ |
| 今日头条 | 财经/科技 | ✅ |
| 澎湃新闻 | 深度报道 | ✅ |
| 百度热搜 | 趋势监控 | ✅ |
| Hacker News | 全球科技 | ✅ |
| GitHub Trending | 开源趋势 | ✅ |

## 🏗️ 项目结构

```
money-ecosystem/
├── 📡 mcp-servers/
│   ├── cryptosignal-server/       # v5.0 — 加密货币信号分析引擎
│   ├── defi-nft-monitor/          # v6.0 — DeFi/NFT 监控中心
│   ├── skill-market/              # v7.0 — 技能市场平台
│   ├── chinese-news-server/       # 中文新闻聚合 MCP Server
│   ├── china-intel-server/        # 中文市场情报 MCP Server
│   └── crypto-chain-server/       # 加密货币链上数据 MCP Server
├── 🛠️ skills/
│   ├── crypto-market-analysis/    # 加密货币市场分析技能
│   ├── crypto-alert-monitor/      # 自动化数据监控与预警技能
│   └── ai-data-analysis-report/   # AI 数据分析报告生成技能
├── 💰 x402/
│   └── payment-config.yaml        # x402 微支付配置
├── 📊 scripts/
│   ├── deploy.sh                  # 一键部署脚本
│   ├── github-monitor.py          # GitHub 仓库监控
│   └── monitor-income.py          # 链上收入监控
├── 📄 赚钱计划.md                  # 三阶段变现路线图
├── 📄 智能体赚钱模式总结与执行计划.md  # 悟空深度研究报告
├── 📄 DEPLOYMENT.md               # 部署指南
└── 📄 README.md                   # 本文件
```

## ⚡ 快速开始

### 1. 环境要求

- Python 3.12+
- pip 或 uv
- 基础网络访问能力

### 2. 一键部署

```bash
# 克隆仓库
git clone https://github.com/xhxlt0820/money-ecosystem.git
cd money-ecosystem

# 安装依赖
pip install -r requirements.txt

# 启动 MCP Server
python mcp-servers/cryptosignal-server/server.py
python mcp-servers/chinese-news-server/server.py
python mcp-servers/china-intel-server/server.py
```

### 3. 使用 MCP 客户端连接

```json
{
  "mcpServers": {
    "cryptosignal": {
      "command": "python",
      "args": ["mcp-servers/cryptosignal-server/server.py"]
    },
    "chinese-news": {
      "command": "python",
      "args": ["mcp-servers/chinese-news-server/server.py"]
    },
    "china-intel": {
      "command": "python",
      "args": ["mcp-servers/china-intel-server/server.py"]
    }
  }
}
```

## 📊 技术亮点

- **🤖 Agent 驱动开发** — 所有 MCP Server 均由 Hermes Agent（悟空）自主开发，展示 AI 自主编码能力
- **💰 x402 微支付** — 基于 Base 链的链上微支付，每次 MCP 调用自动结算
- **🔗 多协议支持** — stdio / SSE / HTTP 协议，兼容主流 MCP 客户端
- **📊 零成本数据源** — 全部使用免费公开 API，无需付费订阅
- **🔐 安全设计** — 收款地址默认隐藏，通过 x402 协议内部配置
- **🌐 模块化架构** — 每个 MCP Server 独立部署、独立扩展
- **📱 中文优先** — 深耕中文数据获取，填补市场空白

## 🗺️ 路线图

### ✅ Phase 1 — 基础建设 (已完成)
- [x] 6 个 MCP Server 开发完成
- [x] v5.0 加密货币信号分析引擎
- [x] v6.0 DeFi/NFT 监控中心
- [x] 3 个 Hermes Agent Skills 开发完成
- [x] x402 微支付链路配置
- [x] 所有数据源沙箱验证通过

### 🔜 Phase 2 — 部署上线 (待执行)
- [ ] MCP Server 部署到生产环境
- [ ] x402 收款链路正式运行
- [ ] 收入监控系统启动
- [ ] GitHub 社区建设

### 🎯 Phase 3 — 开源推广 (规划中)
- [ ] ClawHub 技能市场上架
- [ ] MCP Registry 注册
- [ ] 社区贡献者招募
- [ ] 多语言支持扩展

## 💡 差异化优势

### 为什么不是其他 MCP Server？

1. **中文数据深度** — 微博、头条、百度等中文数据源的 MCP Server 几乎空白
2. **加密货币专精** — 从基础价格到链上分析的完整覆盖
3. **Agent 自主开发** — 整个项目由 AI Agent 开发，本身就是最佳 Demo
4. **x402 原生支持** — 不只是"可以收费"，而是原生微支付架构
5. **开源免费策略** — 先通过开源建立社区，再通过增值服务变现
6. **模块化设计** — 每个 Server 可独立运行、独立商业化

## 🤝 参与方式

### 贡献代码
```bash
git clone https://github.com/xhxlt0820/money-ecosystem.git
cd money-ecosystem
# 提交 PR
```

### 使用 MCP Server
在你的 AI 客户端中配置 MCP Server，享受免费数据服务。

### 分享项目
⭐ Star 这个仓库 | 📢 分享给需要的开发者

## 📈 当前状态

| 指标 | 值 |
|------|------|
| MCP Servers | 6 (全部功能完整) |
| Skills | 3 (全部功能完整) |
| 数据源 | 20+ 免费 API |
| 技术栈 | Python 3.12 |
| 开源协议 | MIT |
| 收款网络 | Base (USDC) |

## 📜 License

[MIT License](LICENSE) — 欢迎使用、修改、分发

---

<div align="center">

**由 Hermes Agent（悟空）自主开发、维护和进化** 🤖

*Money Ecosystem — 让 AI 自己赚钱*

📊 详细研究: [智能体赚钱模式总结与执行计划](智能体赚钱模式总结与执行计划.md) | [赚钱计划](赚钱计划.md)

</div>
