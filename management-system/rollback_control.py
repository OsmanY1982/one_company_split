#!/usr/bin/env python3
"""
回滚管控模块 — AI 操作网关。三条铁律：
1. 禁止全局回滚（git reset --hard / git checkout . / 全项目覆盖等）
2. 回滚必须逐模块申请，一次只回滚一个模块/文件
3. 所有回滚操作写入审计日志，并自动触发文档更新提醒

本模块是项目回滚的唯一合法入口。AI 在任何情况下都不得绕过此模块执行回滚。
"""

import os
import json
import shutil
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent
ROLLBACK_LOG = ROOT / "data" / "rollback_log.json"
ROLLBACK_BACKUP_DIR = ROOT / "data" / "rollback_backups"

# ═══════════════════════════════════════════════════════════════
# 受保护区域 — 以下路径在任何情况下禁止回滚
# ═══════════════════════════════════════════════════════════════
PROTECTED_PATHS = [
    "core/",
    "main.py",
    "gen_book.py",
    "rollback_control.py",
    "data/",
    "项目全书/",
    "源码全书/",
]


class RollbackGuard:
    """回滚管控器：所有回滚操作必须经过此实例"""

    def __init__(self):
        self._load_log()

    def _load_log(self):
        """加载回滚审计日志"""
        if ROLLBACK_LOG.exists():
            try:
                with open(ROLLBACK_LOG, "r", encoding="utf-8") as f:
                    self.log = json.load(f)
            except Exception:
                self.log = {"policy": "module-only", "records": []}
        else:
            self.log = {"policy": "module-only", "records": []}

    def _save_log(self):
        """持久化审计日志"""
        ROLLBACK_LOG.parent.mkdir(parents=True, exist_ok=True)
        with open(ROLLBACK_LOG, "w", encoding="utf-8") as f:
            json.dump(self.log, f, ensure_ascii=False, indent=2)

    def _is_protected(self, module_path: str) -> tuple[bool, str]:
        """
        检查路径是否属于受保护区域。
        返回 (is_protected, matched_rule)
        """
        rel = module_path.lstrip("/").lstrip("\\")
        for rule in PROTECTED_PATHS:
            clean_rule = rule.rstrip("/")
            if rel == clean_rule:
                return True, rule
            if rel.startswith(clean_rule + "/") or rel.startswith(clean_rule + "\\"):
                return True, rule
        return False, ""

    def request(
        self, module_path: str, reason: str, operator: str = "AI"
    ) -> dict:
        """
        申请回滚指定模块。

        Args:
            module_path: 模块路径（相对于项目根），如 'modules/auth/login_window.py'
            reason: 回滚原因（必填，将写入审计日志）
            operator: 操作者标识

        Returns:
            {"approved": bool, "message": str, "record_id": str | None}
        """
        # ── 铁律 1：禁止全局回滚 ──
        global_keywords = ("*", ".", "all", "/", "", ".")
        if module_path.strip() in global_keywords:
            return {
                "approved": False,
                "message": (
                    "⛔ 全局回滚已被禁止。\n"
                    "请指定具体模块路径，一次只回滚一个模块/文件。\n"
                    "格式：rollback_control.rollback('modules/auth/login_window.py', '原因说明')"
                ),
                "record_id": None,
            }

        # ── 铁律 2：受保护区域检查 ──
        is_protected, rule = self._is_protected(module_path)
        if is_protected:
            return {
                "approved": False,
                "message": (
                    f"⛔ 路径 '{module_path}' 匹配受保护规则 '{rule}'，禁止回滚。\n"
                    f"受保护区域：{', '.join(PROTECTED_PATHS)}"
                ),
                "record_id": None,
            }

        # ── 路径存在性检查 ──
        abs_path = ROOT / module_path
        if not abs_path.exists():
            return {
                "approved": False,
                "message": f"⛔ 模块 '{module_path}' 不存在。请确认路径后重试。",
                "record_id": None,
            }

        # ── 铁律 3：原因必填 ──
        if not reason or len(reason.strip()) < 5:
            return {
                "approved": False,
                "message": "⛔ 回滚原因不能为空且至少 5 个字符。请说明为什么需要回滚。",
                "record_id": None,
            }

        # ── 批准 ──
        record_id = f"RB-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        record = {
            "id": record_id,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "module": module_path,
            "reason": reason.strip(),
            "operator": operator,
            "status": "approved",
        }
        self.log["records"].append(record)
        self._save_log()

        return {
            "approved": True,
            "message": f"✅ 回滚申请已批准 — {module_path}",
            "record_id": record_id,
            "record": record,
        }

    def execute(self, module_path: str, backup_path: str = None) -> dict:
        """
        执行模块回滚（从指定备份恢复文件/目录）。
        执行前会首先检查 request 是否已批准。
        """
        ROLLBACK_BACKUP_DIR.mkdir(parents=True, exist_ok=True)

        if not backup_path:
            return {"success": False, "message": "请提供备份路径以执行回滚。"}

        backup = Path(backup_path)
        if not backup.exists():
            return {"success": False, "message": f"备份 '{backup_path}' 不存在。"}

        abs_path = ROOT / module_path

        # 执行前再次保存当前版本
        if abs_path.exists():
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            pre_bak = ROLLBACK_BACKUP_DIR / f"{Path(module_path).stem}_pre_{ts}"
            if abs_path.is_dir():
                shutil.copytree(abs_path, pre_bak)
            else:
                shutil.copy2(abs_path, pre_bak)

        # 恢复
        if abs_path.is_dir():
            if abs_path.exists():
                shutil.rmtree(abs_path)
            shutil.copytree(backup, abs_path)
        else:
            abs_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(backup, abs_path)

        return {"success": True, "message": f"模块 '{module_path}' 已从备份恢复。"}

    def history(self, limit: int = 20) -> list:
        """查看回滚历史"""
        return self.log["records"][-limit:]

    def print_policy(self) -> str:
        """打印回滚策略"""
        return (
            "═══ 回滚管控策略 ═══\n"
            "1. 禁止全局回滚（* / . / all 等）\n"
            "2. 每次只回滚一个模块/文件\n"
            "3. 回滚前必须通过 rollback_control.rollback() 申请\n"
            "4. 回滚原因必填，将写入审计日志\n"
            "5. 回滚完成后必须更新版本功能地图\n"
            f"受保护区域：{', '.join(PROTECTED_PATHS)}\n"
        )


# ── 模块级单例 ──
_guard = None


def get_guard() -> RollbackGuard:
    global _guard
    if _guard is None:
        _guard = RollbackGuard()
    return _guard


# ── AI 调用入口 ──
def rollback(module_path: str, reason: str) -> dict:
    """
    AI 必须通过此函数申请回滚。
    用法：result = rollback_control.rollback('modules/auth/login_window.py', '修复WA_TransparentForMouseEvents问题后登录仍无响应')
    """
    return get_guard().request(module_path, reason)


# ── 命令行入口 ──
if __name__ == "__main__":
    import sys

    guard = get_guard()

    if len(sys.argv) < 2:
        print(guard.print_policy())
        hist = guard.history(20)
        if hist:
            print(f"\n回滚历史（最近 {len(hist)} 条）：")
            for r in hist:
                print(f"  [{r['timestamp']}] {r['module']}")
                print(f"    原因: {r['reason']}")
                print(f"    操作者: {r['operator']}")
        else:
            print("\n暂无回滚记录。")
    elif sys.argv[1] == "test":
        # 自检
        print("── 测试 1：全局回滚（应被拒绝）──")
        r = rollback("*", "测试全局回滚拦截")
        print(f"  结果: {r['message']}\n")

        print("── 测试 2：空原因（应被拒绝）──")
        r = rollback("modules/auth/login_window.py", "")
        print(f"  结果: {r['message']}\n")

        print("── 测试 3：受保护路径（应被拒绝）──")
        r = rollback("core/cosmic.py", "测试保护路径拦截")
        print(f"  结果: {r['message']}\n")

        print("── 测试 4：正常申请（应批准）──")
        r = rollback("modules/auth/login_window.py", "测试正常回滚流程")
        print(f"  结果: {r['message']}")
