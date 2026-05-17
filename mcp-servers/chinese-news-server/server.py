#!/usr/bin/env python3
"""
Chinese News MCP Server — 中文新闻实时数据 MCP Server
数据源：纯免费，无需 API Key
- 微博热搜 (通过访客 Cookie 获取)
- 知乎热榜 (通过 API)
- Hacker News (免费 JSON API)
- GitHub Trending (公开页面)
- 澎湃新闻 RSS

收款：x402 微支付 (USDC on Base)
推广：GitHub 开源

零成本启动 — 所有数据源均可免费获取。
"""

import json
import time
import hashlib
from datetime import datetime, timezone
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.request import urlopen, Request
from urllib.parse import urlparse, parse_qs
import ssl
import re
from html.parser import HTMLParser
import os
import logging
import functools


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("chinese-news")
# ============================================================
# 免费数据源 — 零成本
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
                        logger.warning(f"{func.__name__} retried {max_attempts} times, failed: {e}")
            raise last_exception
        return wrapper
    return decorator

@retry(max_attempts=3, delay=1.0, backoff=2.0)
def fetch(url, headers=None, timeout=10):
    if not news_rate_limiter.acquire(1.0):
        logger.warning(f"Rate limit reached for {url[:50]}...")
        time.sleep(0.5)

    """通用 HTTP 获取，自动处理 SSL 和中文编码"""
    if headers is None:
        headers = {}
    headers.setdefault("User-Agent", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    headers.setdefault("Accept", "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8")
    headers.setdefault("Accept-Language", "zh-CN,zh;q=0.9,en;q=0.8")
    ctx = ssl.create_default_context()
    req = Request(url, headers=headers)
    try:
        with urlopen(req, timeout=timeout, context=ctx) as resp:
            data = resp.read()
        # 自动检测编码
    logger.info(f"fetch success: {url[:50]}... (charset: charset)")
    charset = "utf-8"
    ct = resp.headers.get("Content-Type", "")
    if "charset=" in ct:
        charset = ct.split("charset=")[-1].split(";")[0].strip()
    try:
        result = data.decode(charset)
        logger.debug(f"fetch result length: {len(result)} chars")
        return result
    except UnicodeDecodeError:
        result = data.decode("utf-8", errors="replace")
        logger.warning(f"UTF-8 decode error for {url[:50]}...")
        return result
    except urllib.error.HTTPError as e:
        logger.error(f"HTTP {e.code} error for {url[:50]}...")
        return None
    except urllib.error.URLError as e:
        logger.error(f"URL error for {url[:50]}... {e.reason}")
        return None
    except Exception as e:
        logger.error(f"Fetch error for {url[:50]}... {e}")
        return None


def strip_html(text):
    """去除 HTML 标签"""
    return re.sub(r'<[^>]+>', '', text).strip()


def fetch_weibo_hot():
    """微博热搜 — 通过微博移动端 API"""
    try:
        # 微博移动端热搜 API（无需登录）
        resp = fetch("https://weibo.com/ajax/side/hotSearch", timeout=10, headers={
            "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X)",
            "Referer": "https://weibo.com/hot/search",
            "X-Requested-With": "XMLHttpRequest",
        })
        data = json.loads(resp)
        items = []
        for item in data.get("data", {}).get("realtime", [])[:30]:
            items.append({
                "title": item.get("word", "")[:100],
                "hot": item.get("num", 0),
                "label": item.get("label", {}).get("text", ""),
                "mid": item.get("mid", ""),
                "status_type": item.get("status_type", 0),
            })
        return {"source": "weibo", "fetched_at": datetime.now(timezone.utc).isoformat(), "items": items}
    except Exception as e:
        return {"source": "weibo", "error": str(e), "items": []}


def fetch_zhihu_hot():
    """知乎热榜 — 通过移动端 API（备用数据源）"""
    try:
        resp = fetch("https://api.zhihu.com/toplist/hot", timeout=10, headers={
            "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X)",
            "Referer": "https://www.zhihu.com/hot",
        })
        data = json.loads(resp)
        items = []
        for item in data.get("data", [])[:30]:
            title = ""
            if "target" in item and "title" in item["target"]:
                title = item["target"]["title"][:120]
            elif "title" in item:
                title = item["title"][:120]
            if title:
                items.append({
                    "title": title,
                    "rank": item.get("rank", 0),
                    "hot": item.get("hot_value", 0),
                    "link": f"https://www.zhihu.com/search?q={title}",
                })
        return {"source": "zhihu", "fetched_at": datetime.now(timezone.utc).isoformat(), "items": items}
    except Exception as e:
        return {"source": "zhihu", "error": str(e), "items": []}


def fetch_toutiao_hot():
    """头条热搜 — 免费公开 API ✅ 已验证可用"""
    try:
        resp = fetch("https://www.toutiao.com/hot-event/hot-board/?origin=toutiao_pc&type=trending", timeout=10, headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept": "application/json",
        })
        data = json.loads(resp)
        items = []
        for item in data.get("data", [])[:30]:
            title = item.get("Title", "")
            if title:
                items.append({
                    "title": title[:120],
                    "hot": item.get("HotValue", 0),
                    "cluster_id": item.get("ClusterIdStr", ""),
                    "category": item.get("InterestCategory", ["unknown"]),
                    "image": item.get("Image", {}).get("url", ""),
                    "url": item.get("Url", ""),
                })
        return {"source": "toutiao", "fetched_at": datetime.now(timezone.utc).isoformat(), "items": items}
    except Exception as e:
        return {"source": "toutiao", "error": str(e), "items": []}


def fetch_sanews():
    """澎湃新闻 RSS"""
    try:
        # 澎湃新闻 RSS 可能返回大响应，限制超时
        rss = fetch("https://www.thepaper.cn/rssList_23808.rss", timeout=15)
        items = []
        # 简单 XML 解析
        for match in re.finditer(r'<item>(.*?)</item>', rss, re.DOTALL):
            block = match.group(1)
            title_m = re.search(r'<title>([^<]+)</title>', block)
            link_m = re.search(r'<link>([^<]+)</link>', block)
            if title_m:
                title = title_m.group(1)[:120]
                link = link_m.group(1) if link_m else ""
                items.append({"title": title, "link": link})
            if len(items) >= 15:
                break
        return {"source": "sanews", "fetched_at": datetime.now(timezone.utc).isoformat(), "items": items}
    except Exception as e:
        return {"source": "sanews", "error": str(e), "items": []}


def fetch_hackernews():
    """Hacker News Top Stories — 免费 JSON API"""
    try:
        data = fetch("https://hacker-news.firebaseio.com/v0/topstories.json")
        ids = json.loads(data)[:30]
        items = []
        for eid in ids:
            item = fetch(f"https://hacker-news.firebaseio.com/v0/item/{eid}.json")
            d = json.loads(item)
            title = (d.get("title") or "").strip()[:150]
            if title and title != "[]":
                items.append({
                    "title": title,
                    "url": d.get("url", f"https://news.ycombinator.com/item?id={eid}"),
                    "score": d.get("score", 0),
                    "comments": d.get("descendants", 0),
                })
            if len(items) >= 30:
                break
        return {"source": "hackernews", "fetched_at": datetime.now(timezone.utc).isoformat(), "items": items}
    except Exception as e:
        return {"source": "hackernews", "error": str(e), "items": []}


def fetch_github_trending():
    """GitHub Trending Repositories — 公开页面"""
    try:
        html = fetch("https://github.com/trending", timeout=10, headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept": "text/html,application/xhtml+xml",
        })
        items = []
        # 解析 <h2 class="h3 lh-condensed">...</h2> 中的仓库名
        repo_matches = re.finditer(
            r'<h2[^>]*class="[^"]*h3[^"]*lh-condensed[^"]*"[^>]*>\s*'
            r'<a[^>]*href="(/[^"]+)"[^>]*>\s*'
            r'<span[^>]*class="[^"]*"[^>]*>([^<]+)</span>'
            r'(?:<span[^>]*class="[^"]*"[^>]*>/</span>\s*)?'
            r'<span[^>]*class="[^"]*"[^>]*>([^<]+)</span>',
            html, re.DOTALL
        )
        for m in repo_matches:
            path = m.group(1)
            name = f"{m.group(2).strip()}/{m.group(3).strip()}"
            if name and name.count("/") == 1:
                items.append({
                    "name": name,
                    "url": f"https://github.com{path}" if path.startswith("/") else path,
                })
        # fallback
        if not items:
            for m in re.finditer(r'<a\s+href="/([^/]+/[^"]+)"\s+class="[^"]*lh-condensed', html):
                path = m.group(1)
                name = path.split("/")[0] + "/" + path.split("/")[1]
                if name:
                    items.append({"name": name, "url": f"https://github.com/{path}"})
                if len(items) >= 25:
                    break
        return {"source": "github_trending", "fetched_at": datetime.now(timezone.utc).isoformat(), "items": items}
    except Exception as e:
        return {"source": "github_trending", "error": str(e), "items": []}


# ============================================================
# 缓存层
# ============================================================
_cache = {}
_CACHE_TTL = 300  # 5 分钟

def get_cached(key, fetcher):
    if key in _cache and time.time() - _cache[key]["ts"] < _CACHE_TTL:
        return _cache[key]["data"]
    data = fetcher()
    _cache[key] = {"data": data, "ts": time.time()}
    return data


# ============================================================
# MCP Tools 定义
# ============================================================
TOOLS = [
    {
        "name": "get_chinese_news",
        "description": "获取中文新闻热榜（微博热搜、头条热搜、澎湃新闻）",
        "inputSchema": {
            "type": "object",
            "properties": {
                "sources": {"type": "array", "items": {"type": "string"}, "description": "数据源: weibo, toutiao, sanews. 默认全部"},
                "limit": {"type": "integer", "description": "返回数量限制，默认20", "default": 20},
            },
            "required": []
        }
    },
    {
        "name": "get_tech_news",
        "description": "获取技术新闻（Hacker News + GitHub Trending）",
        "inputSchema": {
            "type": "object",
            "properties": {
                "sources": {"type": "array", "items": {"type": "string"}, "description": "数据源: hackernews, github_trending. 默认全部"},
                "limit": {"type": "integer", "description": "返回数量限制，默认20", "default": 20},
            },
            "required": []
        }
    },
    {
        "name": "get_all_news",
        "description": "获取所有可用新闻数据（中文+英文技术），一次性聚合",
        "inputSchema": {
            "type": "object",
            "properties": {
                "limit": {"type": "integer", "description": "每个源返回数量", "default": 15},
            },
            "required": []
        }
    },
    {
        "name": "search_news",
        "description": "在已获取的新闻中搜索关键词",
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "搜索关键词"},
                "source": {"type": "string", "description": "限制数据源，可选"},
            },
            "required": ["query"]
        }
    },
]

# 数据源映射
FETCHERS = {
    "weibo": fetch_weibo_hot,
    "toutiao": fetch_toutiao_hot,
    "sanews": fetch_sanews,
    "hackernews": fetch_hackernews,
    "github_trending": fetch_github_trending,
}

def call_tool(name, arguments):
    """MCP tool call 分发"""
    limit = arguments.get("limit", 20)

    if name == "get_chinese_news":
        sources = arguments.get("sources", ["weibo", "zhihu", "sanews"])
        results = {}
        for s in sources:
            results[s] = get_cached(s, FETCHERS[s])
        return {"results": results, "query_time": datetime.now(timezone.utc).isoformat()}

    elif name == "get_tech_news":
        sources = arguments.get("sources", ["hackernews", "github_trending"])
        results = {}
        for s in sources:
            results[s] = get_cached(s, FETCHERS[s])
        return {"results": results, "query_time": datetime.now(timezone.utc).isoformat()}

    elif name == "get_all_news":
        results = {}
        for s in FETCHERS:
            results[s] = get_cached(s, FETCHERS[s])
        return {"results": results, "query_time": datetime.now(timezone.utc).isoformat()}

    elif name == "search_news":
        query = arguments["query"]
        source = arguments.get("source")
        all_data = get_all_news_impl(limit)
        matches = []
        for src, data in all_data.items():
            for item in data.get("items", [])[:limit]:
                text = json.dumps(item, ensure_ascii=False)
                if query.lower() in text.lower():
                    matches.append({"source": src, "item": item})
        return {"results": matches, "query_time": datetime.now(timezone.utc).isoformat()}

    return {"error": f"Unknown tool: {name}"}


def get_all_news_impl(limit):
    results = {}
    for s in FETCHERS:
        results[s] = get_cached(s, FETCHERS[s])
    return results


# ============================================================
# HTTP 接口
# ============================================================
SERVER_PORT = 8787
PAYMENT_WALLET = None
PAYMENT_ENABLED = False

class RateLimiter:
    def __init__(self, max_tokens=10, refill_rate=1.0):
        self._tokens = max_tokens
        self._max = max_tokens
        self._refill_rate = refill_rate
        self._last_refill = time.time()
    def acquire(self, tokens=1.0):
        now = time.time()
        elapsed = now - self._last_refill
        self._tokens = min(self._max, self._tokens + elapsed * self._refill_rate)
        self._last_refill = now
        if self._tokens >= tokens:
            self._tokens -= tokens
            return True
        return False

news_rate_limiter = RateLimiter(max_tokens=30, refill_rate=10.0)

def validate_news_items(items):
    errors = []
    warnings = []
    if not isinstance(items, list):
        errors.append("Expected list")
        return False, errors, warnings
    if len(items) == 0:
        warnings.append("Empty news list")
    for item in items[:5]:
        if not isinstance(item, dict):
            errors.append(f"Invalid item format: {type(item).__name__}")
            return False, errors, warnings
        if "title" not in item:
            warnings.append("Missing title in item")
    if not errors:
        logger.info(f"News validation passed: {len(items)} items")
    return len(errors) == 0, errors, warnings

class MCPHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        pass

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path

        if PAYMENT_ENABLED:
            auth = self.headers.get("Authorization", "")
            if not auth.startswith("Bearer x402:"):
                self.send_response(402)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"error": "Payment required"}).encode())
                return

        if path == "/health":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"status": "ok", "uptime": time.time()}).encode())

        elif path == "/mcp/tools/list":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"tools": TOOLS}).encode())

        elif path == "/mcp/tools/call":
            content_len = int(self.headers.get("Content-Length", 0))
            body = json.loads(self.rfile.read(content_len))
            tool_name = body.get("tool", "")
            arguments = body.get("arguments", {})
            result = call_tool(tool_name, arguments)
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(result, ensure_ascii=False).encode())

        elif path == "/metrics":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({
                "cache_keys": list(_cache.keys()),
                "cache_sizes": {k: len(v.get("data", "")) for k, v in _cache.items()},
            }).encode())

        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        self.do_GET()


def start_server(port=SERVER_PORT):
    server = HTTPServer(("0.0.0.0", port), MCPHandler)
    print(f"📡 Chinese News MCP Server running on port {port}")
    print(f"  /health — 健康检查")
    print(f"  /mcp/tools/list — MCP 工具列表")
    print(f"  /mcp/tools/call — MCP 工具调用")
    print(f"  /metrics — 指标监控")
    server.serve_forever()


if __name__ == "__main__":
    import sys
    if "--test" in sys.argv:
        print("🧪 测试模式...")
        for name, fetcher in FETCHERS.items():
            print(f"\n=== {name} ===")
            result = fetcher()
            if "error" in result:
                print(f"❌ 错误: {result['error']}")
            else:
                count = len(result.get("items", []))
                print(f"✅ 成功获取 {count} 条数据")
                if count > 0:
                    print(json.dumps(result["items"][:3], ensure_ascii=False, indent=2))
        print("\n✅ 所有数据源测试完成!")
    else:
        start_server()
