# `iqra/core/iqra_logging.py`

> 路径：`iqra/core/iqra_logging.py` | 行数：281


---


```python
"""
Iqra 日志模块 - Enhanced Edition

统一的日志输出，支持：
- 控制台彩色输出（DEBUG/INFO/WARNING/ERROR/CRITICAL）
- 文件轮转（每天一个日志文件，自动清理）
- 分级控制（环境变量 LOG_LEVEL）
- JSON 结构化日志（可选，用于机器分析）
- 性能日志集成
- 模块级 logger 工厂
"""

import os
import sys
import json
import logging
import traceback
from datetime import datetime
from logging.handlers import RotatingFileHandler, TimedRotatingFileHandler
from typing import Optional, Dict, Any

# ── 配置 ────────────────────────────────────────────────────

LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO").upper()
LOG_DIR = os.path.join(os.path.dirname(__file__), "..", "logs")
JSON_LOG = os.environ.get("JSON_LOG", "0") == "1"  # 环境变量启用 JSON 日志
MAX_LOG_SIZE = 5 * 1024 * 1024  # 5MB
BACKUP_COUNT = 7  # 保留 7 天


# ── ANSI 颜色 ──────────────────────────────────────────────

class ColorFormatter(logging.Formatter):
    """彩色控制台输出格式器"""
    
    COLORS = {
        "DEBUG": "\033[36m",      # Cyan
        "INFO": "\033[32m",       # Green
        "WARNING": "\033[33m",    # Yellow
        "ERROR": "\033[31m",      # Red
        "CRITICAL": "\033[1;31m", # Bold Red
        "RESET": "\033[0m",
        "BOLD": "\033[1m",
        "DIM": "\033[2m",
    }

    EMOJI_MAP = {
        "DEBUG": "🔍",
        "INFO": "ℹ️",
        "WARNING": "⚠️",
        "ERROR": "❌",
        "CRITICAL": "💥",
    }

    def __init__(self, use_emoji: bool = True):
        super().__init__()
        self.use_emoji = use_emoji

    def format(self, record: logging.LogRecord) -> str:
        color = self.COLORS.get(record.levelname, self.COLORS["RESET"])
        reset = self.COLORS["RESET"]
        dim = self.COLORS["DIM"]

        time_str = datetime.fromtimestamp(record.created).strftime("%H:%M:%S")
        level = record.levelname
        
        emoji = self.EMOJI_MAP.get(level, "") if self.use_emoji else ""
        prefix = f"{emoji} " if emoji else ""

        # Module name (dim)
        module = f"{dim}[{record.name}]{reset}"

        # Message
        msg = record.getMessage()

        # Exception info
        exc_text = ""
        if record.exc_info and record.exc_info[0] is not None:
            exc_text = f"\n{dim}{self.formatException(record.exc_info)}{reset}"

        return f"{dim}{time_str}{reset} {color}{prefix}{level:<7}{reset} {module} {msg}{exc_text}"


class JsonFormatter(logging.Formatter):
    """JSON 结构化日志格式器（用于文件日志或机器消费）"""
    
    def format(self, record: logging.LogRecord) -> str:
        log_data = {
            "timestamp": datetime.fromtimestamp(record.created).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        
        if record.exc_info and record.exc_info[0] is not None:
            log_data["exception"] = self.formatException(record.exc_info)
        
        # Add extra fields if present
        for key in ("tool_name", "duration_ms", "provider", "session_id", "event_type"):
            if hasattr(record, key):
                log_data[key] = getattr(record, key)
        
        return json.dumps(log_data, ensure_ascii=False)


# ── Logger 工厂 ─────────────────────────────────────────────

def _ensure_log_dir():
    """确保日志目录存在"""
    if not os.path.exists(LOG_DIR):
        os.makedirs(LOG_DIR, exist_ok=True)


def _create_logger(name: str) -> logging.Logger:
    """创建带彩色控制台和文件输出的 logger"""
    _ensure_log_dir()

    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, LOG_LEVEL, logging.INFO))

    if logger.handlers:
        return logger

    # ── 文件 handler：按大小轮转 ──
    today = datetime.now().strftime("%Y-%m-%d")
    file_handler = RotatingFileHandler(
        os.path.join(LOG_DIR, f"iqra_{today}.log"),
        maxBytes=MAX_LOG_SIZE,
        backupCount=BACKUP_COUNT,
        encoding="utf-8",
    )
    file_handler.setLevel(logging.DEBUG)
    
    if JSON_LOG:
        file_handler.setFormatter(JsonFormatter())
    else:
        file_formatter = logging.Formatter(
            "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        file_handler.setFormatter(file_formatter)
    logger.addHandler(file_handler)

    # ── JSON 文件 handler（始终输出 JSON 格式到单独文件）──
    json_handler = RotatingFileHandler(
        os.path.join(LOG_DIR, f"iqra_{today}.jsonl"),
        maxBytes=MAX_LOG_SIZE,
        backupCount=3,
        encoding="utf-8",
    )
    json_handler.setLevel(logging.INFO)
    json_handler.setFormatter(JsonFormatter())
    logger.addHandler(json_handler)

    # ── 控制台 handler：彩色输出 ──
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(getattr(logging, LOG_LEVEL, logging.INFO))
    
    # Windows 下检查是否支持 ANSI
    use_color = True
    if sys.platform == "win32":
        try:
            import ctypes
            kernel32 = ctypes.windll.kernel32
            kernel32.SetConsoleMode(kernel32.GetStdHandle(-11), 7)
        except Exception:
            use_color = False
    
    if use_color:
        console_handler.setFormatter(ColorFormatter())
    else:
        console_formatter = logging.Formatter(
            "%(asctime)s [%(levelname)s] %(message)s",
            datefmt="%H:%M:%S",
        )
        console_handler.setFormatter(console_formatter)
    
    logger.addHandler(console_handler)

    return logger


# ── 模块级 logger ──────────────────────────────────────────

logger = _create_logger("iqra")


def get_logger(name: str) -> logging.Logger:
    """获取子模块 logger"""
    return _create_logger(f"iqra.{name}")


# ── 结构化日志辅助 ─────────────────────────────────────────

def log_tool_call(logger_instance: logging.Logger, tool_name: str,
                  success: bool, duration_ms: float, error: str = ""):
    """记录工具调用的结构化日志"""
    extra = {
        "tool_name": tool_name,
        "duration_ms": duration_ms,
        "event_type": "tool_call",
    }
    msg = f"Tool '{tool_name}' {'succeeded' if success else 'failed'} in {duration_ms:.1f}ms"
    if error:
        msg += f" | Error: {error}"
    
    if success:
        logger_instance.info(msg, extra=extra)
    else:
        logger_instance.error(msg, extra=extra)


def log_llm_request(logger_instance: logging.Logger, provider: str,
                    success: bool, duration_ms: float,
                    tokens_in: int = 0, tokens_out: int = 0):
    """记录 LLM 请求的结构化日志"""
    extra = {
        "provider": provider,
        "duration_ms": duration_ms,
        "event_type": "llm_request",
    }
    msg = f"LLM '{provider}' {'OK' if success else 'FAIL'} {duration_ms:.0f}ms tokens:{tokens_in}→{tokens_out}"
    
    if success:
        logger_instance.info(msg, extra=extra)
    else:
        logger_instance.error(msg, extra=extra)


# ── 全局异常处理器 ─────────────────────────────────────────

def exception_handler(exc_type, exc_value, exc_traceback):
    """全局异常捕获器 - 避免崩溃时打印普通 traceback"""
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return
    logger.critical("未捕获的异常", exc_info=(exc_type, exc_value, exc_traceback))


def install():
    """安装全局异常处理器"""
    sys.excepthook = exception_handler
    logger.info("Iqra 日志系统已启动 (level=%s, json=%s)", LOG_LEVEL, JSON_LOG)
    # 启动时清理 14 天前的旧日志
    try:
        cleaned = cleanup_old_logs(days=14)
        if cleaned > 0:
            logger.info("日志清理完成: 已删除 %d 个过期文件", cleaned)
    except Exception:
        pass


# ── 日志清理 ───────────────────────────────────────────────

def cleanup_old_logs(days: int = 14) -> int:
    """清理超过 N 天的日志文件"""
    from datetime import timedelta
    cutoff = datetime.now() - timedelta(days=days)
    removed = 0
    
    if not os.path.exists(LOG_DIR):
        return 0
    
    for fname in os.listdir(LOG_DIR):
        fpath = os.path.join(LOG_DIR, fname)
        if not os.path.isfile(fpath):
            continue
        try:
            mtime = datetime.fromtimestamp(os.path.getmtime(fpath))
            if mtime < cutoff:
                os.remove(fpath)
                removed += 1
        except Exception:
            pass
    
    if removed > 0:
        logger.info(f"已清理 {removed} 个过期日志文件 (>{days}天)")
    return removed

```
