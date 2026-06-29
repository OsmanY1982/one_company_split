# -*- coding: utf-8 -*-
"""AgentBridge 引擎模块 Mixin — try/except 导入 + _init_engine_modules"""

import os
import sys

# ── 项目根路径 ──
_project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

# ═══════════════════════════════════════════
# 引擎模块（try/except，缺失不阻塞启动）
# ═══════════════════════════════════════════

try:
    from iqra.core.code_executor import CodeExecutor
    _HAVE_CODE_EXECUTOR = True
except ImportError:
    _HAVE_CODE_EXECUTOR = False
try:
    from iqra.core.code_intel import SymbolExtractor
    _HAVE_CODE_INTEL = True
except ImportError:
    _HAVE_CODE_INTEL = False
try:
    from iqra.core.workspace_indexer import WorkspaceIndexer
    _HAVE_INDEXER = True
except ImportError:
    _HAVE_INDEXER = False
try:
    from iqra.core.patch_engine import PatchEngine
    _HAVE_PATCH_ENGINE = True
except ImportError:
    _HAVE_PATCH_ENGINE = False
try:
    from iqra.core.task_scheduler import TaskScheduler
    _HAVE_TASK_SCHEDULER = True
except ImportError:
    _HAVE_TASK_SCHEDULER = False
try:
    from iqra.core.todo_system import TodoSystem
    _HAVE_TODO_SYSTEM = True
except ImportError:
    _HAVE_TODO_SYSTEM = False
try:
    from iqra.core.session_search import SessionSearch
    _HAVE_SESSION_SEARCH = True
except ImportError:
    _HAVE_SESSION_SEARCH = False
try:
    from iqra.core.semantic_search import SemanticSearcher, HybridRetriever
    _HAVE_SEMANTIC_SEARCH = True
except ImportError:
    _HAVE_SEMANTIC_SEARCH = False
try:
    from iqra.core.super_intelligence import SuperIntelligence
    _HAVE_SUPER_INTEL = True
except ImportError:
    _HAVE_SUPER_INTEL = False
try:
    from iqra.core.rag_context import RAGContextInjector
    _HAVE_RAG = True
except ImportError:
    _HAVE_RAG = False
try:
    from iqra.core.token_optimizer import TokenOptimizer
    _HAVE_TOKEN_OPT = True
except ImportError:
    _HAVE_TOKEN_OPT = False
try:
    from iqra.core.clarify_system import ClarifySystem
    _HAVE_CLARIFY = True
except ImportError:
    _HAVE_CLARIFY = False
try:
    from iqra.core.model_status import ModelStatus
    _HAVE_MODEL_STATUS = True
except ImportError:
    _HAVE_MODEL_STATUS = False
try:
    from iqra.core.model_status_manager import ModelStatusManager
    _HAVE_MODEL_MGR = True
except ImportError:
    _HAVE_MODEL_MGR = False
try:
    from iqra.core.multi_model import MultiModelRouter
    _HAVE_MULTI_MODEL = True
except ImportError:
    _HAVE_MULTI_MODEL = False
try:
    from iqra.core.skill_loader import SkillLoader
    _HAVE_SKILL_LOADER = True
except ImportError:
    _HAVE_SKILL_LOADER = False
try:
    from iqra.core.skill_system import SkillSystem
    _HAVE_SKILL_SYSTEM = True
except ImportError:
    _HAVE_SKILL_SYSTEM = False
try:
    from iqra.core.agent_delegate import AgentDelegate
    _HAVE_DELEGATE = True
except ImportError:
    _HAVE_DELEGATE = False
try:
    from iqra.core.cloud_sync import CloudSyncService
    _HAVE_CLOUD_SYNC = True
except ImportError:
    _HAVE_CLOUD_SYNC = False
try:
    from iqra.core.performance_monitor import PerformanceMonitor
    _HAVE_PERF_MON = True
except ImportError:
    _HAVE_PERF_MON = False
try:
    from iqra.core.process_manager import ProcessManager
    _HAVE_PROC_MGR = True
except ImportError:
    _HAVE_PROC_MGR = False
try:
    from iqra.core.secure_storage import SecureStorage
    _HAVE_SECURE = True
except ImportError:
    _HAVE_SECURE = False
try:
    from iqra.core.token_saver import TokenOptimizer as TokenSaverOptimizer, TokenStats
    _HAVE_TOKEN_SAVER = True
except ImportError:
    _HAVE_TOKEN_SAVER = False
try:
    from iqra.core.iqra_logging import get_logger, install as install_logging
    _HAVE_LOGGING = True
except ImportError:
    _HAVE_LOGGING = False
try:
    from iqra.core.provider_registry import ModelConfig
    _HAVE_PROVIDER_REG = True
except ImportError:
    _HAVE_PROVIDER_REG = False
try:
    from iqra.core.config_validator import ConfigValidator
    _HAVE_CONFIG_VALID = True
except ImportError:
    _HAVE_CONFIG_VALID = False
try:
    from iqra.core.sync_bridge import SyncBridge
    _HAVE_SYNC_BRIDGE = True
except ImportError:
    _HAVE_SYNC_BRIDGE = False
try:
    from iqra.core.observability import ObservableBridge
    _HAVE_OBSERVABILITY = True
except ImportError:
    _HAVE_OBSERVABILITY = False
try:
    from iqra.core.collaboration_client import IqraHermesClient
    _HAVE_COLLAB = True
except ImportError:
    _HAVE_COLLAB = False
try:
    from iqra.core.supabase_client import SupabaseClient
    _HAVE_SUPABASE = True
except ImportError:
    _HAVE_SUPABASE = False


class AgentBridgeEngineMixin:
    """引擎模块初始化 Mixin"""

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
                    os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))),
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
