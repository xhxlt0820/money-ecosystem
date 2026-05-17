"""
core_utils.py — Money Ecosystem 核心工具库

统一的日志、缓存、重试、数据验证等基础设施。
所有 MCP Server 共享此模块。
"""

import os
import sys
import json
import time
import hashlib
import logging
import functools
import urllib.request
import urllib.error
import ssl
from datetime import datetime, timezone
from typing import Any, Optional, Dict, List, Callable, Union
from collections import OrderedDict
from dataclasses import dataclass, field, asdict

# ============================================================
# 日志系统
# ============================================================

_log_initialized = False

def setup_logger(
    name: str = "money-ecosystem",
    level: str = "INFO",
    log_file: Optional[str] = None,
    max_bytes: int = 10_485_760,  # 10MB
    backup_count: int = 5,
) -> logging.Logger:
    """初始化统一日志系统"""
    global _log_initialized
    if _log_initialized:
        return logging.getLogger(name)

    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, level.upper(), logging.INFO))

    formatter = logging.Formatter(
        "%(asctime)s [%(levelname)s] %(name)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # 控制台输出
    console = logging.StreamHandler(sys.stdout)
    console.setFormatter(formatter)
    logger.addHandler(console)

    # 文件输出
    if log_file:
        os.makedirs(os.path.dirname(log_file), exist_ok=True)
        from logging.handlers import RotatingFileHandler
        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=max_bytes,
            backupCount=backup_count,
        )
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    _log_initialized = True
    return logger


# ============================================================
# 重试机制
# ============================================================

def retry(
    max_attempts: int = 3,
    delay: float = 1.0,
    backoff: float = 2.0,
    exceptions: tuple = (Exception,),
):
    """装饰器：自动重试失败的操作"""
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            current_delay = delay
            for attempt in range(1, max_attempts + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt < max_attempts:
                        time.sleep(current_delay)
                        current_delay *= backoff
                    else:
                        logger = logging.getLogger("money-ecosystem.retry")
                        logger.warning(
                            f"{func.__name__} 重试 {max_attempts} 次后失败: {e}"
                        )
            raise last_exception
        return wrapper
    return decorator


# ============================================================
# 缓存系统（内存 + 磁盘混合缓存）
# ============================================================

@dataclass
class CacheEntry:
    data: Any
    created_at: float
    ttl: int  # seconds

    def is_expired(self) -> bool:
        return time.time() - self.created_at > self.ttl


class CacheManager:
    """内存 + 磁盘混合缓存管理器"""

    def __init__(
        self,
        memory_max_size: int = 1000,
        disk_cache_dir: Optional[str] = None,
    ):
        self._memory: OrderedDict[str, CacheEntry] = OrderedDict()
        self._memory_max = memory_max_size
        self._disk_dir = disk_cache_dir or os.path.join(
            os.path.expanduser("~"), ".money-ecosystem-cache"
        )
        os.makedirs(self._disk_dir, exist_ok=True)
        self._logger = logging.getLogger("money-ecosystem.cache")

    def _disk_key(self, key: str) -> str:
        return os.path.join(self._disk_dir, hashlib.md5(key.encode()).hexdigest() + ".json")

    def get(self, key: str, default: Any = None) -> Optional[Any]:
        # 优先读内存
        if key in self._memory:
            entry = self._memory[key]
            if entry.is_expired():
                del self._memory[key]
                return default
            self._memory.move_to_end(key)
            return entry.data

        # 读磁盘
        disk_path = self._disk_key(key)
        if os.path.exists(disk_path):
            try:
                with open(disk_path, "r") as f:
                    entry_data = json.load(f)
                entry = CacheEntry(**entry_data)
                if entry.is_expired():
                    os.remove(disk_path)
                    return default
                # 加载到内存
                if len(self._memory) >= self._memory_max:
                    self._memory.popitem(last=False)
                self._memory[key] = entry
                return entry.data
            except (json.JSONDecodeError, KeyError):
                return default
        return default

    def put(self, key: str, data: Any, ttl: int = 300):
        entry = CacheEntry(data=data, created_at=time.time(), ttl=ttl)
        self._memory[key] = entry

        # 写入磁盘
        try:
            disk_path = self._disk_key(key)
            entry_dict = {
                "data": data,
                "created_at": entry.created_at,
                "ttl": entry.ttl,
            }
            with open(disk_path, "w") as f:
                json.dump(entry_dict, f)
        except Exception as e:
            self._logger.debug(f"磁盘缓存写入失败: {e}")

    def invalidate(self, key: str):
        self._memory.pop(key, None)
        disk_path = self._disk_key(key)
        if os.path.exists(disk_path):
            os.remove(disk_path)

    def clear(self):
        self._memory.clear()
        for f in os.listdir(self._disk_dir):
            if f.endswith(".json"):
                os.remove(os.path.join(self._disk_dir, f))

    def stats(self) -> Dict:
        return {
            "memory_entries": len(self._memory),
            "disk_entries": len([f for f in os.listdir(self._disk_dir) if f.endswith(".json")]),
            "max_memory": self._memory_max,
        }


# ============================================================
# 数据质量验证
# ============================================================

@dataclass
class ValidationResult:
    valid: bool
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict:
        return asdict(self)


def validate_price_data(
    price: float,
    symbol: str = "",
) -> ValidationResult:
    """验证价格数据的合理性"""
    errors = []
    warnings = []

    if price <= 0:
        errors.append(f"{symbol}: 价格为非正数: {price}")
    if price > 1e12:
        warnings.append(f"{symbol}: 价格异常高: {price}")
    if price < 1e-10:
        warnings.append(f"{symbol}: 价格异常低: {price}")

    return ValidationResult(valid=len(errors) == 0, errors=errors, warnings=warnings)


def validate_json_response(
    data: Any,
    required_keys: Optional[List[str]] = None,
) -> ValidationResult:
    """验证 JSON 响应数据的完整性"""
    errors = []
    warnings = []

    if data is None:
        errors.append("数据为空")
        return ValidationResult(valid=False, errors=errors)

    if required_keys:
        if isinstance(data, dict):
            for key in required_keys:
                if key not in data:
                    errors.append(f"缺少必需键: {key}")
        else:
            errors.append(f"期望字典类型，实际: {type(data).__name__}")

    if not errors and isinstance(data, dict):
        for key, value in data.items():
            if isinstance(value, str) and len(value) > 10000:
                warnings.append(f"键 '{key}' 的值过长: {len(value)} 字符")

    return ValidationResult(valid=len(errors) == 0, errors=errors, warnings=warnings)


def validate_list_data(
    data: Any,
    min_length: int = 0,
    expected_type: Optional[type] = None,
) -> ValidationResult:
    """验证列表数据的合理性"""
    errors = []
    warnings = []

    if not isinstance(data, (list, tuple)):
        errors.append(f"期望列表类型，实际: {type(data).__name__}")
        return ValidationResult(valid=False, errors=errors)

    if len(data) < min_length:
        errors.append(f"列表长度不足: {len(data)} < {min_length}")

    if expected_type and data:
        for item in data:
            if not isinstance(item, expected_type):
                errors.append(
                    f"列表元素类型不匹配: {type(item).__name__} != {expected_type.__name__}"
                )

    return ValidationResult(valid=len(errors) == 0, errors=errors, warnings=warnings)


# ============================================================
# HTTP 请求封装
# ============================================================

def fetch_url(
    url: str,
    timeout: int = 10,
    headers: Optional[Dict[str, str]] = None,
    use_cache: bool = True,
    cache_key: Optional[str] = None,
    cache: Optional[CacheManager] = None,
) -> Optional[Any]:
    """封装 HTTP GET 请求，支持缓存"""

    if use_cache and cache:
        ck = cache_key or url
        cached = cache.get(ck)
        if cached is not None:
            logger = logging.getLogger("money-ecosystem.cache")
            logger.debug(f"缓存命中: {url[:60]}...")
            return cached

    if headers is None:
        headers = {
            "User-Agent": "MoneyEcosystem/1.0 (MCP Server)",
            "Accept": "application/json",
        }

    ctx = ssl.create_default_context()
    req = urllib.request.Request(url, headers=headers)

    try:
        with urllib.request.urlopen(req, timeout=timeout, context=ctx) as resp:
            body = resp.read().decode("utf-8")
            return json.loads(body)
    except urllib.error.HTTPError as e:
        logger = logging.getLogger("money-ecosystem.http")
        logger.error(f"HTTP {e.code} 错误: {url}")
        return None
    except urllib.error.URLError as e:
        logger = logging.getLogger("money-ecosystem.http")
        logger.error(f"URL 错误: {url} - {e.reason}")
        return None
    except Exception as e:
        logger = logging.getLogger("money-ecosystem.http")
        logger.error(f"请求失败: {url} - {e}")
        return None


def fetch_with_retry(
    url: str,
    max_retries: int = 3,
    timeout: int = 10,
    **kwargs,
) -> Optional[Any]:
    """带重试的 HTTP GET"""
    last_err = None
    for attempt in range(max_retries):
        result = fetch_url(url, timeout=timeout, **kwargs)
        if result is not None:
            return result
        last_err = f"Attempt {attempt+1}/{max_retries} failed"
        if attempt < max_retries - 1:
            time.sleep(2 ** attempt)
    logger = logging.getLogger("money-ecosystem.http")
    logger.warning(f"{url} 所有 {max_retries} 次重试均失败")
    return None


# ============================================================
# 速率限制器
# ============================================================

class RateLimiter:
    """令牌桶速率限制器"""

    def __init__(self, max_tokens: float, refill_rate: float):
        self._tokens = max_tokens
        self._max = max_tokens
        self._refill_rate = refill_rate  # tokens per second
        self._last_refill = time.time()
        self._lock = False  # 简化：无锁实现

    def acquire(self, tokens: float = 1.0) -> bool:
        now = time.time()
        elapsed = now - self._last_refill
        self._tokens = min(self._max, self._tokens + elapsed * self._refill_rate)
        self._last_refill = now

        if self._tokens >= tokens:
            self._tokens -= tokens
            return True
        return False

    def wait_and_acquire(self, tokens: float = 1.0, max_wait: float = 10.0) -> bool:
        start = time.time()
        while time.time() - start < max_wait:
            if self.acquire(tokens):
                return True
            time.sleep(0.1)
        return False


# ============================================================
# 数据格式化工具
# ============================================================

class DataFormatter:
    """统一的数据格式化输出"""

    @staticmethod
    def format_price(price: float, symbol: str = "") -> str:
        prefix = f"{symbol}: " if symbol else ""
        if price >= 1e6:
            return f"{prefix}${price/1e6:.4f}M"
        elif price >= 1e3:
            return f"{prefix}${price/1e3:.3f}K"
        else:
            return f"{prefix}${price:,.6f}"

    @staticmethod
    def format_percentage(value: float) -> str:
        return f"{value:+.2f}%"

    @staticmethod
    def format_timestamp(dt: datetime) -> str:
        return dt.strftime("%Y-%m-%d %H:%M:%S UTC")

    @staticmethod
    def format_bytes(size: int) -> str:
        for unit in ["B", "KB", "MB", "GB"]:
            if size < 1024:
                return f"{size:.2f} {unit}"
            size /= 1024
        return f"{size:.2f} TB"

    @staticmethod
    def format_signal(score: float) -> str:
        """将信号分数转换为可读信号"""
        if score >= 75:
            return "🟢 STRONG_BUY"
        elif score >= 60:
            return "🟡 BUY"
        elif score >= 40:
            return "🟠 HOLD"
        elif score >= 25:
            return "🟠 SELL"
        else:
            return "🔴 STRONG_SELL"


# ============================================================
# 健康检查
# ============================================================

@dataclass
class HealthStatus:
    status: str  # "healthy", "degraded", "unhealthy"
    checks: Dict[str, str] = field(default_factory=dict)
    uptime_seconds: float = 0.0

    def to_dict(self) -> Dict:
        return asdict(self)


class HealthChecker:
    """服务健康检查器"""

    def __init__(self, service_name: str):
        self._service_name = service_name
        self._start_time = time.time()
        self._checks: Dict[str, str] = {}
        self._logger = logging.getLogger(f"money-ecosystem.health.{service_name}")

    def add_check(self, name: str, status: str):
        self._checks[name] = status

    def check(self) -> HealthStatus:
        if not self._checks:
            self._checks["service"] = "running"

        statuses = set(self._checks.values())

        if "healthy" in statuses and "unhealthy" not in statuses:
            status = "healthy"
        elif "unhealthy" in statuses:
            status = "unhealthy"
        else:
            status = "degraded"

        return HealthStatus(
            status=status,
            checks=self._checks,
            uptime_seconds=time.time() - self._start_time,
        )


# ============================================================
# 导出工具
# ============================================================

class DataExporter:
    """数据导出工具（CSV/JSON）"""

    @staticmethod
    def export_csv(data: List[Dict], filename: str) -> str:
        """导出为 CSV 文件"""
        if not data:
            return ""

        os.makedirs(os.path.dirname(filename) or ".", exist_ok=True)

        headers = list(data[0].keys())
        with open(filename, "w", encoding="utf-8") as f:
            f.write(",".join(headers) + "\n")
            for row in data:
                values = []
                for h in headers:
                    val = str(row.get(h, "")).replace(",", ";")
                    values.append(val)
                f.write(",".join(values) + "\n")

        return filename

    @staticmethod
    def export_json(data: Any, filename: str) -> str:
        """导出为 JSON 文件"""
        os.makedirs(os.path.dirname(filename) or ".", exist_ok=True)
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2, default=str)
        return filename

    @staticmethod
    def export_report(report: Dict, filename: str) -> str:
        """导出分析报告（Markdown 格式）"""
        os.makedirs(os.path.dirname(filename) or ".", exist_ok=True)
        with open(filename, "w", encoding="utf-8") as f:
            f.write("# 数据分析报告\n\n")
            f.write(f"**生成时间**: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}\n\n")

            for key, value in report.items():
                f.write(f"## {key}\n\n")
                if isinstance(value, dict):
                    for k, v in value.items():
                        f.write(f"- **{k}**: {v}\n")
                elif isinstance(value, list):
                    for item in value:
                        f.write(f"- {item}\n")
                else:
                    f.write(f"{value}\n")
                f.write("\n")

        return filename


# ============================================================
# 时间戳工具
# ============================================================

def current_timestamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def current_timestamp_human() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")


def ts_to_datetime(ts: str) -> Optional[datetime]:
    """ISO 时间戳转 datetime"""
    try:
        return datetime.fromisoformat(ts.replace("Z", "+00:00"))
    except (ValueError, AttributeError):
        return None
