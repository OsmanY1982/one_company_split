"""
AgentBridge v2 — iqra 自主 Agent 引擎（对标 Codex / Claude Code）

双模式：
  chat(message)       → 对话模式（单轮工具调用，ChatEngine）
  run_task(message)   → 自主执行模式（多步 Think-Plan-Act-Observe-Reflect，AgentLoop）

工具套件（12 个专业工具）：
  文件:   read_file / write_file / edit_file / list_directory / search_files
  代码:   search_code / run_tests
  系统:   execute_shell / desktop_control
  Git:    git_operation
  网络:   web_search / web_fetch_page
"""

import os
import sys
import json
import re
import subprocess
import fnmatch
import traceback
import time
from pathlib import Path
from typing import Optional, Callable, Dict, Any, List

from core.modules.intelligence.session_context import session_ctx

# ── iqra 引擎路径（必须在子模块 import 之前注入，否则 core.agent_loop 等找不到）──
_project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
_iqra_pkg = os.path.join(_project_root, "iqra")
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)
if _iqra_pkg not in sys.path:
    sys.path.insert(0, _iqra_pkg)

from core.modules.intelligence.agent_bridge_workers import _TaskWorker, _StreamWorker
from core.modules.intelligence.agent_bridge_models import AgentBridgeModelMixin
from core.modules.intelligence.agent_bridge_tools import AgentBridgeToolsMixin

from core.chat_engine import ChatEngine
from core.tool_registry import ToolRegistry
from core.llm_backend import BaseLLMBackend
from core.agent_loop import AgentLoop, AgentEvent, AgentEventType, AgentResult
from core.smart_memory_adapter import SmartMemoryStore
# 注：iqra 包不存在，Iqra/IqraConfig 为死导入（重构残留），已移除
from PyQt5.QtCore import QObject, pyqtSignal, QThread

# ── 引擎模块（try/except，缺失不阻塞启动）──
try:
    from core.code_executor import CodeExecutor, SecureSandbox, CodeValidator, ExecutionResult
    _HAVE_CODE_EXECUTOR = True
except ImportError:
    _HAVE_CODE_EXECUTOR = False
    SecureSandbox = None
    CodeValidator = None
    ExecutionResult = None
try:
    from core.code_intel import SymbolExtractor
    _HAVE_CODE_INTEL = True
except ImportError:
    _HAVE_CODE_INTEL = False
try:
    from core.workspace_indexer import WorkspaceIndexer
    _HAVE_INDEXER = True
except ImportError:
    _HAVE_INDEXER = False
try:
    from core.patch_engine import PatchEngine
    _HAVE_PATCH_ENGINE = True
except ImportError:
    _HAVE_PATCH_ENGINE = False
try:
    from core.task_scheduler import TaskScheduler
    _HAVE_TASK_SCHEDULER = True
except ImportError:
    _HAVE_TASK_SCHEDULER = False
try:
    from core.todo_system import TodoSystem
    _HAVE_TODO_SYSTEM = True
except ImportError:
    _HAVE_TODO_SYSTEM = False
try:
    from core.session_search import SessionSearch
    _HAVE_SESSION_SEARCH = True
except ImportError:
    _HAVE_SESSION_SEARCH = False
try:
    from core.semantic_search import SemanticSearcher, HybridRetriever
    _HAVE_SEMANTIC_SEARCH = True
except ImportError:
    _HAVE_SEMANTIC_SEARCH = False
try:
    from core.super_intelligence import SuperIntelligence
    _HAVE_SUPER_INTEL = True
except ImportError:
    _HAVE_SUPER_INTEL = False
try:
    from core.rag_context import RAGContextInjector
    _HAVE_RAG = True
except ImportError:
    _HAVE_RAG = False
try:
    from core.token_optimizer import TokenOptimizer
    _HAVE_TOKEN_OPT = True
except ImportError:
    _HAVE_TOKEN_OPT = False
try:
    from core.clarify_system import ClarifySystem
    _HAVE_CLARIFY = True
except ImportError:
    _HAVE_CLARIFY = False
try:
    from core.model_status import ModelStatus
    _HAVE_MODEL_STATUS = True
except ImportError:
    _HAVE_MODEL_STATUS = False
try:
    from core.model_status_manager import ModelStatusManager
    _HAVE_MODEL_MGR = True
except ImportError:
    _HAVE_MODEL_MGR = False
try:
    from core.multi_model import MultiModelRouter
    _HAVE_MULTI_MODEL = True
except ImportError:
    _HAVE_MULTI_MODEL = False
try:
    from core.skill_loader import SkillLoader
    _HAVE_SKILL_LOADER = True
except ImportError:
    _HAVE_SKILL_LOADER = False
try:
    from core.skill_system import SkillSystem
    _HAVE_SKILL_SYSTEM = True
except ImportError:
    _HAVE_SKILL_SYSTEM = False
try:
    from core.agent_delegate import AgentDelegate
    _HAVE_DELEGATE = True
except ImportError:
    _HAVE_DELEGATE = False
try:
    from core.cloud_sync import CloudSyncService
    _HAVE_CLOUD_SYNC = True
except ImportError:
    _HAVE_CLOUD_SYNC = False
try:
    from core.performance_monitor import PerformanceMonitor
    _HAVE_PERF_MON = True
except ImportError:
    _HAVE_PERF_MON = False
try:
    from core.process_manager import ProcessManager
    _HAVE_PROC_MGR = True
except ImportError:
    _HAVE_PROC_MGR = False
try:
    from core.secure_storage import SecureStorage
    _HAVE_SECURE = True
except ImportError:
    _HAVE_SECURE = False
try:
    from core.token_saver import TokenOptimizer as TokenSaverOptimizer, TokenStats
    _HAVE_TOKEN_SAVER = True
except ImportError:
    _HAVE_TOKEN_SAVER = False
try:
    from core.iqra_logging import get_logger, install as install_logging
    _HAVE_LOGGING = True
except ImportError:
    _HAVE_LOGGING = False
try:
    from core.provider_registry import ModelConfig
    _HAVE_PROVIDER_REG = True
except ImportError:
    _HAVE_PROVIDER_REG = False
try:
    from core.config_validator import ConfigValidator
    _HAVE_CONFIG_VALID = True
except ImportError:
    _HAVE_CONFIG_VALID = False
try:
    from core.sync_bridge import SyncBridge
    _HAVE_SYNC_BRIDGE = True
except ImportError:
    _HAVE_SYNC_BRIDGE = False
try:
    from core.observability import ObservableBridge
    _HAVE_OBSERVABILITY = True
except ImportError:
    _HAVE_OBSERVABILITY = False
try:
    from core.collaboration_client import IqraHermesClient
    _HAVE_COLLAB = True
except ImportError:
    _HAVE_COLLAB = False
try:
    from core.supabase_client import SupabaseClient
    _HAVE_SUPABASE = True
except ImportError:
    _HAVE_SUPABASE = False


# ═══════════════════════════════════════════
# AgentBridge 主类
# ═══════════════════════════════════════════

class AgentBridge(AgentBridgeModelMixin, AgentBridgeToolsMixin):
    """
    iqra 自主 Agent 引擎

    用法:
        bridge = AgentBridge(backend)
        reply = bridge.chat("今天天气如何")          # 对话模式
        bridge.run_task("重构 src/ 下的 import")     # 自主执行模式
    """

    DEFAULT_SYSTEM_PROMPT = (
        "你是 iqra，一人公司的全能 AI 助理。\n"
        "\n"
        "核心能力：\n"
        "1. 文件系统：read_file/write_file/edit_file/list_directory/search_files\n"
        "2. 代码：search_code/run_tests\n"
        "3. 系统：execute_shell/execute_python/desktop_control\n"
        "4. Git：git_operation\n"
        "5. 网络：web_search/web_fetch_page\n"
        "\n"
        "=== 工具选择铁律（违反将导致低效/错误） ===\n"
        "1. 读取文件 → 只用 read_file，严禁用 execute_shell 执行 cat/more/osascript\n"
        "2. 搜索文件 → 只用 search_files（或 list_directory+匹配），严禁用 find/grep/mdfind/ls\n"
        "3. 读写文件 → 只用 read_file/write_file/edit_file，严禁通过 pipe/重定向操作\n"
        "4. 执行命令 → 只用 execute_shell，严禁用 osascript/open/xdg-open\n"
        "5. 每个目的只用一个工具一次完成，不要用多个工具接力做同一件事\n"
        "\n"
        "=== 执行原则 ===\n"
        "- 永远用工具完成任务，不要只给建议\n"
        "- 多个独立操作必须并行调用（如同一轮读多个文件），不要串行等待\n"
        "- 只读操作（读文件/列目录/搜索）直接执行，不废话\n"
        "- 出错后分析原因，尝试替代方案，同一错误不重试超过2次\n"
        "- 关键操作（删除/覆盖）前确认安全性\n"
        "\n"
        "=== 文件定位策略 ===\n"
        "当用户提到某个文件名或配置文档（如「设计规范」「规范」「AI规范」等）：\n"
        "1. 先在工作目录下搜索该文件名\n"
        "2. 搜索 /Volumes/D盘工作区/ 根目录（同名文件）\n"
        "3. 搜索 ~/ 用户主目录\n"
        "优先级：用户说的路径 > find/search_files 搜索结果 > 推断\n"
        "\n"
        "=== 能力质疑处理 ===\n"
        "- 如果用户质疑你的能力，不要用文字解释\n"
        "- 直接调用工具现场演示，用行动证明\n"
    )

    def __init__(
        self,
        backend: BaseLLMBackend,
        system_prompt: str = "",
        session_id: str = None,
        persistence_dir: str = "",
    ):
        self._backend = backend
        if session_id is None:
            session_id = session_ctx.current_session_id
        self.session_id = session_id

        # ── 对话持久化存储 ──
        if not persistence_dir:
            persistence_dir = os.path.join(
                os.path.expanduser("~"), ".iqra", "sessions"
            )
        os.makedirs(persistence_dir, exist_ok=True)
        self._memory = SmartMemoryStore(
            base_dir=persistence_dir,
        )

        # ── 项目上下文感知 ──
        self._project_context: Dict[str, Any] = {}
        self._detect_project_context()

        # ── 增强版 System Prompt（含项目上下文）──
        full_prompt = self._build_system_prompt(system_prompt)

        # ── 工具注册表 ──
        self.registry = ToolRegistry(enable_metrics=False)
        self._register_tools()

        # ── ChatEngine（对话模式，开启 auto_save）──
        self._engine = ChatEngine(
            backend=backend,
            registry=self.registry,
            system_prompt=full_prompt,
            memory_store=self._memory,
            auto_save=True,
            session_id=session_id,
        )

        # ── 可观测性（Token/调用链/成本，缺失不阻塞引擎）──
        self.obs = None
        if _HAVE_OBSERVABILITY:
            try:
                self.obs = ObservableBridge(memory_store=self._memory)
                self.obs.attach_to(backend)
                self._engine.obs = self.obs
            except Exception:
                self.obs = None

        # ── AgentLoop（自主执行模式）──
        self._agent_loop = AgentLoop(
            engine=self._engine,
            max_iterations=50,
            max_retries=3,
            timeout_seconds=900,  # 15 分钟（35b+ 大模型需要更长推理时间）
            verbose=True,
        )

        # ── 引擎模块初始化 ──
        self._init_engine_modules()

        # ── 后台线程 ──
        self._task_thread: Optional[QThread] = None
        self._task_worker: Optional[_TaskWorker] = None
        self._stream_cancelled: bool = False
        self._stream_aborted: bool = False

    def _init_engine_modules(self):
        """初始化所有 iqra 引擎模块（try/except 包裹，逐个失败不影响启动）"""
        # ── SuperIntelligence ──
        if _HAVE_SUPER_INTEL:
            try:
                self._super_intel = SuperIntelligence()
            except Exception:
                self._super_intel = None
        else:
            self._super_intel = None

        # ── RAG 上下文注入 ──
        if _HAVE_RAG:
            try:
                self._rag = RAGContextInjector()
                project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
                self._rag.set_project(project_root, build=False)
            except Exception:
                self._rag = None
        else:
            self._rag = None

        # ── Token 优化 ──
        if _HAVE_TOKEN_OPT:
            try:
                self._token_opt = TokenOptimizer(mode="balanced")
            except Exception:
                self._token_opt = None
        else:
            self._token_opt = None

        # ── 高风险确认 ──
        if _HAVE_CLARIFY:
            try:
                self._clarify = ClarifySystem()
            except Exception:
                self._clarify = None
        else:
            self._clarify = None

        # ── 模型健康监控 + 故障切换 ──
        self._model_status = None
        if _HAVE_MODEL_STATUS:
            try:
                self._model_status = ModelStatus()
            except Exception:
                pass
        self._model_mgr = None
        if _HAVE_MODEL_MGR:
            try:
                self._model_mgr = ModelStatusManager()
            except Exception:
                pass

        # ── 多模型路由 ──
        if _HAVE_MULTI_MODEL:
            try:
                self._multi_model = MultiModelRouter()
            except Exception:
                self._multi_model = None
        else:
            self._multi_model = None

        # ── 技能系统 ──
        if _HAVE_SKILL_LOADER:
            try:
                self._skill_loader = SkillLoader()
            except Exception:
                self._skill_loader = None
        else:
            self._skill_loader = None
        if _HAVE_SKILL_SYSTEM:
            try:
                skills_dir = os.path.join(_project_root, "iqra", "skills")
                self._skill_system = SkillSystem(skills_dir) if os.path.isdir(skills_dir) else None
            except Exception:
                self._skill_system = None
        else:
            self._skill_system = None

        # ── 子代理分派 ──
        if _HAVE_DELEGATE:
            try:
                self._delegate = AgentDelegate()
            except Exception:
                self._delegate = None
        else:
            self._delegate = None

        # ── 工作效率工具 ──
        self._code_executor = CodeExecutor(default_timeout=30) if _HAVE_CODE_EXECUTOR else None
        self._patch_engine = PatchEngine() if _HAVE_PATCH_ENGINE else None
        if _HAVE_TASK_SCHEDULER:
            try:
                self._task_scheduler = TaskScheduler()
            except Exception:
                self._task_scheduler = None
        else:
            self._task_scheduler = None
        if _HAVE_TODO_SYSTEM:
            try:
                self._todo = TodoSystem()
            except Exception:
                self._todo = None
        else:
            self._todo = None
        self._session_search = SessionSearch() if _HAVE_SESSION_SEARCH else None

        # ── 后台服务 ──
        self._cloud_sync = None
        if _HAVE_CLOUD_SYNC:
            try:
                self._cloud_sync = CloudSyncService()
            except Exception:
                pass
        self._perf_mon = None
        if _HAVE_PERF_MON:
            try:
                self._perf_mon = PerformanceMonitor()
            except Exception:
                pass
        self._proc_mgr = ProcessManager() if _HAVE_PROC_MGR else None
        self._secure_store = SecureStorage() if _HAVE_SECURE else None

        # ── 结构化日志 ──
        self._logger = None
        if _HAVE_LOGGING:
            try:
                install_logging()
                self._logger = get_logger("agent_bridge")
            except Exception:
                pass

        # ── 配置校验 ──
        self._config_validator = None
        if _HAVE_CONFIG_VALID:
            try:
                config_path = os.path.join(
                    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
                    "iqra", "data", "iqra_config.json"
                )
                self._config_validator = ConfigValidator(config_path)
            except Exception:
                pass

        # ── 模型配置注册 ──
        self._provider_registry = ModelConfig() if _HAVE_PROVIDER_REG else None

        # ── Token 统计与节省 ──
        self._token_stats = None
        self._token_saver = None
        if _HAVE_TOKEN_SAVER:
            try:
                self._token_stats = TokenStats()
                self._token_saver = TokenSaverOptimizer(self._token_stats)
            except Exception:
                pass

        # ── 云端同步 ──
        self._sync_bridge = SyncBridge() if _HAVE_SYNC_BRIDGE else None

        # ── Supabase 远程后端 ──
        self._supabase = SupabaseClient() if _HAVE_SUPABASE else None

        # ── 多人协作 ──
        self._collab_client = IqraHermesClient() if _HAVE_COLLAB else None

    # ═══════════════════════════════════════════
    # 模式 1: 对话模式（chat / chat_stream）
    # ═══════════════════════════════════════════

    # ── 任务检测关键词 ──
    TASK_KEYWORDS = [
        "帮我", "重构", "写一个", "生成", "修改", "创建", "修复", "优化",
        "部署", "安装", "配置", "搜索文件", "查找", "整理", "编译",
        "测试", "运行", "迁移", "打包", "发布", "调试", "分析代码",
        "把", "请把", "找出", "提取", "转换", "合并", "拆分", "检查",
        "执行", "启动", "关闭", "重启", "清理", "格式化", "添加",
        "删除", "移除", "替换", "升级", "降级", "回滚", "备份",
    ]

    def chat_stream(
        self,
        message: str,
        on_chunk: Callable[[str], None] = None,
        on_done: Callable[[str], None] = None,
        on_tool: Callable[[str, str], None] = None,
        on_error: Callable[[str], None] = None,
    ):
        """
        流式对话（逐字输出，打字机效果）。在后台线程执行，回调运行在主线程。

        Args:
            message: 用户输入
            on_chunk: 每收到一个文本块时回调 on_chunk(chunk_str)
            on_done: 流式完成后回调 on_done(full_text)
            on_tool: 工具调用时回调 on_tool(tool_name, status)
            on_error: 流式出错时回调 on_error(error_message)
        """
        # 终止前一次流式（如果还在运行），防止旧 finished 信号误杀新线程
        self._abort_stream()

        # 管线预处理（RAG / Token 压缩 / SuperIntelligence / 多模型路由）
        self._preprocess_stream(message)

        self._stream_thread = QThread()
        self._stream_worker = _StreamWorker(self._engine, message, bridge=self)
        self._stream_worker.moveToThread(self._stream_thread)

        # 连接信号到回调（跨线程安全，回调在主线程执行）
        from PyQt5.QtCore import Qt
        if on_chunk:
            self._stream_worker.chunk_ready.connect(on_chunk, Qt.QueuedConnection)
        if on_tool:
            self._stream_worker.tool_event.connect(on_tool, Qt.QueuedConnection)
        if on_done:
            self._stream_worker.stream_done.connect(on_done, Qt.QueuedConnection)
        if on_error:
            self._stream_worker.stream_error.connect(on_error, Qt.QueuedConnection)

        self._stream_thread.started.connect(self._stream_worker.run)
        self._stream_worker.finished.connect(self._stream_thread.quit)
        self._stream_worker.finished.connect(self._stream_worker.deleteLater)
        self._stream_thread.finished.connect(self._stream_thread.deleteLater)
        self._stream_thread.start()

    def _abort_stream(self):
        """安全终止当前正在运行的流式线程（清除旧引用防止信号串扰）"""
        if hasattr(self, '_stream_worker') and self._stream_worker:
            try:
                self._stream_worker.finished.disconnect()
            except Exception:
                pass
        if hasattr(self, '_stream_thread') and self._stream_thread:
            try:
                self._stream_thread.quit()
                self._stream_thread.wait(200)
            except Exception:
                pass
        self._stream_worker = None
        self._stream_thread = None

    def cancel(self):
        """取消正在执行的流式或自主任务"""
        self._stream_cancelled = True
        if hasattr(self, '_agent_loop') and self._agent_loop:
            try:
                self._agent_loop.cancel()
            except Exception:
                pass

    def cancel_task(self):
        """取消正在执行的自主任务"""
        if self._agent_loop:
            self._agent_loop.cancel()

    # ── 模型管理接口 ──

    def get_model(self) -> str:
        """返回当前使用的模型名"""
        if hasattr(self._backend, 'get_model'):
            return self._backend.get_model()
        if hasattr(self._backend, 'config') and hasattr(self._backend.config, 'model'):
            return self._backend.config.model
        return ""

    def get_provider_info(self) -> dict:
        """返回当前供应商信息"""
        if hasattr(self._backend, 'config'):
            cfg = self._backend.config
            return {
                "provider_id": cfg.name if hasattr(cfg, 'name') else "",
                "provider_type": cfg.provider_type if hasattr(cfg, 'provider_type') else "",
                "model": self.get_model(),
                "base_url": cfg.base_url if hasattr(cfg, 'base_url') else "",
            }
        return {}

    def list_all_models(self) -> list:
        """列出所有可用模型（供应商预设 + Ollama 动态发现）"""
        models = []
        if hasattr(self._backend, 'list_models'):
            try:
                models = self._backend.list_models()
            except Exception:
                pass

        # Ollama 动态发现（本地服务，通过后端配置的 base_url 探测）
        if not models and hasattr(self._backend, 'config'):
            try:
                import json, urllib.request
                base = self._backend.config.base_url.rstrip("/")
                req = urllib.request.Request(f"{base}/models", method="GET")
                with urllib.request.urlopen(req, timeout=5) as resp:
                    data = json.loads(resp.read().decode("utf-8"))
                    raw_models = data.get("data", [])
                    models = [{"name": m.get("id", ""), "size": 0} for m in raw_models]
            except Exception:
                pass

        # 最后兜底：从配置取模型名
        if not models and hasattr(self._backend, 'config') and hasattr(self._backend.config, 'model'):
            models = [{"name": self._backend.config.model}]

        # 归一化：确保每项是 dict 且有 "name" 键
        result = []
        for m in models:
            if isinstance(m, str):
                result.append({"name": m})
            elif isinstance(m, dict):
                if "name" not in m:
                    d = dict(m)
                    d["name"] = d.get("model") or d.get("id") or str(d)
                    result.append(d)
                else:
                    result.append(m)
        return result

    def switch_model(self, provider_id: str, model: str) -> bool:
        """切换模型"""
        try:
            if hasattr(self._backend, 'switch_model'):
                return self._backend.switch_model(provider_id, model)
            if hasattr(self._backend, 'config'):
                self._backend.config.model = model
                return True
            return False
        except Exception:
            return False

    def run_task_sync(self, message: str):
        """同步执行 Agent 任务（AgentLoop.run 的薄包装）

        Args:
            message: 任务描述字符串，如 "重构 src/ 下的 import"

        Returns:
            AgentResult — 含 success / summary / steps_taken / tools_called 等字段
        """
        return self._agent_loop.run(message)

    def chat(self, message: str) -> str:
        """
        智能入口：自动判定路由到对话模式或自主执行模式。

        规则：
        - 包含任务动词 → run_task_sync（AgentLoop 自主执行）
        - 否则 → 单轮对话（ChatEngine）
        - AgentLoop 失败时自动回退到 ChatEngine
        """
        is_task = any(kw in message for kw in self.TASK_KEYWORDS)

        if is_task:
            try:
                result = self.run_task_sync(message)
                if result.success:
                    return result.summary
                else:
                    return (
                        f"[任务未完成] {result.summary}\n\n"
                        f"已执行 {result.steps_taken} 步，"
                        f"调用工具: {', '.join(result.tools_called) if result.tools_called else '无'}"
                    )
            except Exception as e:
                traceback.print_exc()
                try:
                    return self._engine.chat(message)
                except Exception:
                    return f"[AgentBridge 错误] {e}"

        try:
            return self._apply_engine_pipeline(message)
        except Exception as e:
            traceback.print_exc()
            return f"[AgentBridge 错误] {e}"

    def _clear_pipeline_blocks(self, engine):
        """移除 system message 中旧的管线注入块，防止重复追加导致膨胀"""
        if not engine.messages or engine.messages[0]['role'] != 'system':
            return
        content = engine.messages[0]['content']
        content = re.sub(
            r'\n<pipeline_rag>.*?</pipeline_rag>\n',
            '', content, flags=re.DOTALL
        )
        content = re.sub(
            r'\n<pipeline_si>.*?</pipeline_si>\n',
            '', content, flags=re.DOTALL
        )
        engine.messages[0]['content'] = content

    def _apply_engine_pipeline(self, message: str) -> str:
        """
        引擎管线：对 ChatEngine 调用前注入上下文压缩、RAG、SuperIntelligence。
        管线顺序：RAG 注入 → Token 压缩 → SuperIntelligence 提示词 → 路由判断 → LLM 调用
        """
        # 清理旧的管线注入块，防止 system prompt 无限增长
        self._clear_pipeline_blocks(self._engine)

        # 1. RAG 上下文注入
        if self._rag:
            try:
                rag_ctx = self._rag.inject_context(message)
                if rag_ctx:
                    self._engine.inject_context(
                        f'<pipeline_rag>\n[项目上下文]\n{rag_ctx}\n</pipeline_rag>'
                    )
            except Exception:
                pass

        # 2. Token 压缩
        if self._token_opt:
            try:
                self._engine.messages = self._token_opt.optimize_messages(self._engine.messages)
            except Exception:
                pass

        # 3. SuperIntelligence 推理链注入
        if self._super_intel:
            try:
                si_prompt = self._super_intel.inject_prompt(message)
                if si_prompt:
                    self._engine.inject_context(
                        f'<pipeline_si>\n{si_prompt}\n</pipeline_si>'
                    )
            except Exception:
                pass

        # 4. 多模型路由
        if self._multi_model:
            try:
                route = self._multi_model.route(message)
                if route and route.get("model"):
                    self.switch_model(route.get("provider_id", ""), route["model"])
            except Exception:
                pass

        # 5. 调用 ChatEngine
        try:
            return self._engine.chat(message)
        except Exception as e:
            # 故障切换：如果当前模型失败且 model_mgr 可用，尝试备用模型
            if self._model_mgr:
                try:
                    fallback = self._model_mgr.get_fallback()
                    if fallback:
                        self.switch_model(fallback.provider_id, fallback.model)
                        return self._engine.chat(message)
                except Exception:
                    pass
            raise e

    def _preprocess_stream(self, message: str):
        """
        流式管线预处理（对标 _apply_engine_pipeline），
        在 ChatEngine.chat_stream() 被 _StreamWorker 调用前执行。
        """
        self._clear_pipeline_blocks(self._engine)

        # 1. RAG 上下文注入
        if self._rag:
            try:
                rag_ctx = self._rag.inject_context(message)
                if rag_ctx:
                    self._engine.inject_context(
                        f'<pipeline_rag>\n[项目上下文]\n{rag_ctx}\n</pipeline_rag>'
                    )
            except Exception:
                pass

        # 2. Token 压缩
        if self._token_opt:
            try:
                self._engine.messages = self._token_opt.optimize_messages(self._engine.messages)
            except Exception:
                pass

        # 3. SuperIntelligence 推理链注入
        if self._super_intel:
            try:
                si_prompt = self._super_intel.inject_prompt(message)
                if si_prompt:
                    self._engine.inject_context(
                        f'<pipeline_si>\n{si_prompt}\n</pipeline_si>'
                    )
            except Exception:
                pass

        # 4. 多模型路由
        if self._multi_model:
            try:
                route = self._multi_model.route(message)
                if route and route.get("model"):
                    self.switch_model(route.get("provider_id", ""), route["model"])
            except Exception:
                pass

    def reset(self):
        """重置对话历史"""
        self._engine.messages = []
        self._engine.initialize_session()

    # ── 信号转发 ──
    @property
    def on_tool_start(self): return self._engine.on_tool_start
    @property
    def on_tool_result(self): return self._engine.on_tool_result
    @property
    def on_agent_event(self): return self._agent_loop.on_event
    @property
    def on_agent_progress(self): return self._agent_loop.on_progress

    # ═══════════════════════════════════════════
    # 项目上下文感知
    # ═══════════════════════════════════════════

    def _detect_project_context(self) -> None:
        """自动检测当前工作区项目结构，注入系统提示"""
        cwd = os.getcwd()
        ctx: Dict[str, Any] = {
            "cwd": cwd,
            "has_git": os.path.isdir(os.path.join(cwd, ".git")),
            "top_files": [],
            "package_managers": [],
            "design_specs": [],  # AI 设计规范等关键文档
        }

        # 检测顶层文件（.py, .json, .md, .txt）
        try:
            for f in sorted(os.listdir(cwd))[:30]:
                fp = os.path.join(cwd, f)
                if os.path.isfile(fp) and not f.startswith("."):
                    ctx["top_files"].append(f)
        except Exception as e:
            print(f"[agent_bridge] 扫描工作目录文件失败: {e}")

        # 检测 D 盘根目录关键文档（AI设计规范等）
        drive_roots = ["/Volumes/D盘工作区", "/Volumes/C盘工作区"]
        for root in drive_roots:
            if os.path.isdir(root):
                spec_file = os.path.join(root, "AI设计规范.txt")
                if os.path.isfile(spec_file):
                    ctx["design_specs"].append(spec_file)

        # 检测包管理器
        pm_indicators = {
            "Python/pip": ["requirements.txt", "setup.py", "setup.cfg", "pyproject.toml", "Pipfile"],
            "Node.js": ["package.json", "yarn.lock", "pnpm-lock.yaml"],
            "Git": [".git"],
            "Docker": ["Dockerfile", "docker-compose.yml", "docker-compose.yaml"],
        }
        for pm, indicators in pm_indicators.items():
            if any(os.path.exists(os.path.join(cwd, i)) for i in indicators):
                ctx["package_managers"].append(pm)

        self._project_context = ctx

    def _build_system_prompt(self, base_prompt: str) -> str:
        """将项目上下文注入 System Prompt"""
        base = base_prompt or self.DEFAULT_SYSTEM_PROMPT
        ctx = self._project_context

        if not ctx or not ctx.get("cwd"):
            return base

        lines = [base, "", "## 当前项目环境"]
        lines.append(f"- 工作目录: `{ctx['cwd']}`")

        if ctx.get("has_git"):
            lines.append("- Git 仓库: 是")
        if ctx.get("package_managers"):
            lines.append(f"- 技术栈: {', '.join(ctx['package_managers'])}")
        if ctx.get("top_files"):
            top = ctx["top_files"][:15]
            lines.append(f"- 顶层文件: {', '.join(top)}")

        # 注入关键文档路径（AI设计规范等）
        if ctx.get("design_specs"):
            lines.append("\n## 关键参考文档（做任何重大决策前务必先查阅）")
            for spec in ctx["design_specs"]:
                lines.append(f"- `{spec}`")

        lines.append(
            "\n所有文件操作默认基于以上工作目录。"
            "如需访问其他目录，请使用绝对路径。"
        )

        # ── 持久化记忆注入（跨会话 AI 自律规则）──
        memory_md = Path.home() / ".hermes" / "memories" / "MEMORY.md"
        if memory_md.exists():
            try:
                raw = memory_md.read_text(encoding="utf-8")
                entries = [e.strip() for e in raw.split("\n§\n") if e.strip()]
                if entries:
                    lines.append("\n## 持久化记忆（跨会话 AI 自律）")
                    for i, entry in enumerate(entries, 1):
                        lines.append(f"\n### 记忆 {i}\n{entry}")
            except Exception:
                pass

        return "\n".join(lines)

    # ═══════════════════════════════════════════
    # 对话持久化
    # ═══════════════════════════════════════════

    def save_session(self, messages: list = None, session_id: str = None) -> bool:
        """手动保存当前会话到磁盘。
        
        Args:
            messages: 消息列表，若为 None 则使用 engine 内的消息
            session_id: 会话ID，若为 None 则使用当前 session_id
        """
        try:
            msgs = messages if messages is not None else self._engine.messages
            sid = session_id if session_id is not None else self.session_id
            self._memory.save_session(msgs, sid)
            return True
        except Exception as e:
            traceback.print_exc()
            return False

    def load_session(self, session_id: str = None) -> list:
        """从磁盘恢复会话历史，返回消息列表。
        
        Args:
            session_id: 会话ID，若为 None 则使用当前 session_id
        """
        try:
            sid = session_id if session_id is not None else self.session_id
            msgs = self._memory.load_session(sid)
            return msgs
        except Exception:
            return []

    def append_message(self, role: str, content: str, session_id: str = "default") -> str:
        """实时追加单条消息到会话（增量保存，防止崩溃丢失）"""
        existing = self._memory.load_session(session_id)
        if existing is None:
            existing = []
        existing.append({"role": role, "content": content})
        # 记录最后一条消息，供 notify_message_added 使用
        self._last_message_info = (session_id, role, content)
        return self._memory.save_session(existing, session_id)

    def notify_message_added(self):
        """通知 session_ctx 的消息监听器（悬浮球等）有新消息"""
        if hasattr(self, '_last_message_info'):
            sid, role, content = self._last_message_info
            session_ctx.notify_message_added(sid, role, content)

    def list_sessions(self) -> List[Dict[str, Any]]:
        """列出所有已保存的会话"""
        try:
            return self._memory.list_sessions()
        except Exception:
            return []

    def rename_session(self, session_id: str, new_title: str) -> bool:
        """重命名会话"""
        try:
            return self._memory.rename_session(session_id, new_title)
        except Exception:
            return False

    def toggle_pin_session(self, session_id: str) -> bool:
        """置顶/取消置顶会话。返回 True=已置顶, False=已取消"""
        try:
            return self._memory.toggle_pin_session(session_id)
        except Exception:
            return False

    def delete_session(self, session_id: str) -> bool:
        """删除会话"""
        try:
            return self._memory.delete_session(session_id)
        except Exception:
            return False

    def get_sessions_dir(self) -> str:
        """返回会话文件的存储目录路径"""
        return self._memory.get_sessions_dir()

