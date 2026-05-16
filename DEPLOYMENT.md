# 🚀 部署文档 - 悟空 AI 技能市场 & MCP Server 生态

## 已完成 ✅
- [x] 3 个 MCP Server 开发完成
- [x] 2 个 Skills 开发完成
- [x] x402 收款配置完成 (USDC on Base: `暂不公开（x402协议内部配置）`)
- [x] 所有数据源沙箱验证通过
- [x] Git 仓库初始化

## 下一步
1. 主人确认部署
2. 悟空部署到主人服务器
3. 启动 cron 监控
4. GitHub 开源发布

## 部署命令 (主人服务器)
```bash
# 1. 安装依赖
pip install aiohttp mcp

# 2. 配置 Hermes Agent
# 在 config.yaml 中添加:
mcp_servers:
  - name: crypto-chain-server
    command: python3
    args: [/root/workspace/money-ecosystem/mcp-servers/crypto-chain-server/server.py]
    
# 3. 注册 Skills
# 在 config.yaml 中添加:
skills:
  - name: crypto-market-analysis
    path: /root/workspace/money-ecosystem/skills/crypto-market-analysis/SKILL.md
  - name: crypto-alert-monitor
    path: /root/workspace/money-ecosystem/skills/crypto-alert-monitor/SKILL.md

# 4. 启动服务
python3 /root/workspace/money-ecosystem/mcp-servers/crypto-chain-server/server.py

# 5. 测试
curl http://localhost:8789/health
curl -X POST http://localhost:8789/mcp/tools/call -H 'Content-Type: application/json' -d '{"tool":"get_btc_price","arguments":{"currency":"USD"}}'
```
