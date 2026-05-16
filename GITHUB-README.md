# 🤖 Hermes Agent 中文 AI 技能市场 & MCP Server 生态

> **零成本启动的中文 AI Agent 数据变现生态**
> 
> 通过 OpenClaw/Hermes 技能系统和 MCP Server，将中文数据源 monetize。
> 所有服务通过 x402 微支付收款（加密货币）。

## 📦 项目概览

本生态包含两大模块：

### 模块一：MCP Servers (3个)
1. **Chinese News MCP Server** — 中文新闻实时数据 (微博热搜、头条热搜、澎湃新闻)
2. **Crypto Chain MCP Server** — 加密货币链上数据 (BTC价格、链上统计、恐慌贪婪指数)
3. **Public Data MCP Server** — 公共数据查询 (IP定位、PM2.5、汇率、天气、GitHub搜索)

### 模块二：Skills (3个)
1. **AI Data Analysis Report** — AI 数据分析报告工具
2. **Crypto Market Analysis** — 加密货币市场分析技能
3. **Crypto Alert Monitor** — 自动化数据监控与预警技能

## 🚀 快速开始

```bash
# 一键部署
bash scripts/deploy.sh

# 验证服务
curl http://localhost:8788/health
curl http://localhost:8789/health
curl http://localhost:8790/health
```

## 💰 收费模式

### MCP Server (按调用收费)
| Server | 价格 | 数据源 |
|--------|------|--------|
| Chinese News | $0.001/次 | 微博热搜、头条热搜 |
| Crypto Chain | $0.005/次 | BTC价格、恐慌贪婪指数、Mempool |
| Public Data | $0.002/次 | IP定位、PM2.5、汇率、天气 |

### Skills (订阅制)
| Skill | 价格 | 目标用户 |
|-------|------|---------|
| AI Data Analysis | $19-29/月 | 企业决策者、分析师 |
| Crypto Market Analysis | $9-19/月 | 加密货币交易者 |
| Crypto Alert Monitor | $29-49/月 | 高级交易者 |

## 🔧 技术栈

- **运行环境**: Python 3.8+
- **MCP 协议**: MCP Server (stdio/stdin)
- **收款方式**: x402 微支付 (USDC on Base)
- **推广渠道**: GitHub 开源
- **API 预算**: $0 (全部免费数据源)

## 📋 项目结构

```
money-ecosystem/
├── mcp-servers/
│   ├── chinese-news-server/    # 中文新闻 MCP Server
│   ├── crypto-chain-server/    # 加密货币 MCP Server
│   └── chinese-business-server/  # 公共数据 MCP Server
├── skills/
│   ├── crypto-market-analysis/  # 加密货币市场分析技能
│   ├── crypto-alert-monitor/    # 加密货币预警监控技能
│   └── data-analysis-tool/      # AI 数据分析报告技能
├── x402/
│   └── payment-config.yaml     # 收款配置
├── scripts/
│   ├── deploy.sh               # 一键部署脚本
│   └── monitor-income.sh       # 收入监控脚本
├── GITHUB-README.md            # GitHub 开源说明
└── README.md                   # 项目文档
```

## 📊 数据源清单

### MCP Server 1 (Chinese News)
- [x] 微博热搜 — ✅ 已验证
- [x] 头条热搜 — ✅ 已验证
- [x] Hacker News — ✅ 已验证
- [x] GitHub Trending — ✅ 已验证

### MCP Server 2 (Crypto Chain)
- [x] CryptoCompare BTC/ETH 价格 — ✅ 已验证
- [x] Blockchain.info BTC 链上数据 — ✅ 已验证
- [x] Alternative.me 恐慌贪婪指数 — ✅ 已验证
- [x] Mempool.space 链上统计 — ✅ 已验证
- [x] Satoshi 地址余额查询 — ✅ 已验证

### MCP Server 3 (Public Data)
- [x] IP 地理定位 — ✅ 已验证
- [x] PM2.5 空气质量 — ✅ 已验证
- [x] 汇率查询 — ✅ 已验证
- [x] 天气查询 — ✅ 已验证
- [x] Hacker News 热门 — ✅ 已验证
- [x] GitHub 仓库搜索 — ✅ 已验证

## 🎯 路线图

### Phase 1: 基础建设 ✅ (已完成)
- [x] 搭建基础目录结构
- [x] 开发 3 个 MCP Servers
- [x] 开发 3 个 Skills
- [x] 配置 x402 收款链路
- [x] 准备 GitHub 开源

### Phase 2: 部署上线 ⏳ (待主人确认后执行)
- [ ] 主人提供加密货币收款地址
- [ ] 配置 x402 收款
- [ ] 一键部署到主人服务器
- [ ] 开始收入监控

### Phase 3: 开源推广 ⏳ (待部署后执行)
- [ ] GitHub 开源发布
- [ ] ClawHub 技能市场发布
- [ ] 社区推广

## 🔑 需要主人提供的信息

1. **加密货币收款地址** (USDC on Base)
2. **推广渠道** (已确认: GitHub 开源)
3. **API 预算** (已确认: $0 零成本)
4. **项目方向** (已确认: 数据分析 + 免费开源)

## 📞 联系与支持

- 项目维护: Hermes Agent (悟空)
- 推广渠道: GitHub 开源
- API 预算: $0 零成本
- 预计月收入: $500-$10,000 (取决于使用量)

## 📜 License

MIT License

---

*由悟空 (Hermes Agent) 自动开发和维护 🤖*