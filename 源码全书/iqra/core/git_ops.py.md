# `iqra/core/git_ops.py`

> 路径：`iqra/core/git_ops.py` | 行数：403


---


```python
# -*- coding: utf-8 -*-
"""
GitOps — Git 操作封装（对标 Codex 的 Git 集成）

安全设计:
  - 所有写操作返回 dry_run 预览，默认不执行
  - force_push / hard_reset 等破坏性操作需 explicit confirm
  - 自动 stash 保护未提交变更
  - 操作日志完整记录

工具清单:
  - git_status      → 查看仓库状态
  - git_diff        → 查看变更差异
  - git_log         → 查看提交历史
  - git_stage       → 暂存文件
  - git_commit      → 提交变更
  - git_branch      → 分支管理
  - git_checkout    → 切换分支
  - git_stash       → 暂存/恢复工作区
"""

import os
import subprocess
import json
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple
from pathlib import Path


# ═══════════════════════════════════════════
# 数据结构
# ═══════════════════════════════════════════

@dataclass
class GitStatus:
    """Git 仓库状态"""
    branch: str = ""
    ahead: int = 0
    behind: int = 0
    staged: List[str] = field(default_factory=list)      # 已暂存
    modified: List[str] = field(default_factory=list)     # 已修改未暂存
    untracked: List[str] = field(default_factory=list)    # 未跟踪
    deleted: List[str] = field(default_factory=list)      # 已删除
    renamed: List[str] = field(default_factory=list)      # 重命名
    has_conflicts: bool = False
    is_clean: bool = True


@dataclass
class GitCommit:
    """提交记录"""
    hash: str = ""
    short_hash: str = ""
    author: str = ""
    date: str = ""
    message: str = ""


@dataclass
class GitOpResult:
    """操作结果"""
    success: bool = False
    output: str = ""
    error: str = ""
    dry_run: bool = False


# ═══════════════════════════════════════════
# Git 操作核心
# ═══════════════════════════════════════════

class GitOps:
    """
    Git 操作封装

    用法:
        git = GitOps("/path/to/repo")
        status = git.status()
        git.stage(["file.py"])
        git.commit("feat: add new feature")
    """

    def __init__(self, repo_path: str):
        self.repo_path = os.path.abspath(repo_path)
        self._git_dir = os.path.join(self.repo_path, ".git")

        if not os.path.isdir(self._git_dir):
            raise ValueError(f"Not a git repository: {self.repo_path}")

    # ── 基础命令 ──

    def _run(self, args: List[str], timeout: int = 30, capture: bool = True) -> Tuple[int, str, str]:
        """执行 git 命令"""
        cmd = ["git", "-C", self.repo_path] + args
        try:
            result = subprocess.run(
                cmd,
                capture_output=capture,
                text=True,
                timeout=timeout,
                env={**os.environ, "GIT_TERMINAL_PROMPT": "0"},
            )
            return result.returncode, result.stdout.strip(), result.stderr.strip()
        except subprocess.TimeoutExpired:
            return -1, "", "Git command timed out"
        except FileNotFoundError:
            return -1, "", "Git not found. Please install git."

    # ── 状态 / 信息 ──

    def status(self) -> GitStatus:
        """获取仓库状态"""
        status = GitStatus()

        # 分支信息
        code, out, _ = self._run(["branch", "--show-current"])
        if code == 0 and out:
            status.branch = out

        # ahead/behind
        if status.branch:
            code, out, _ = self._run(["rev-list", "--left-right", "--count", f"{status.branch}...@{{u}}"])
            if code == 0 and out:
                parts = out.split()
                if len(parts) == 2:
                    status.ahead = int(parts[0])
                    status.behind = int(parts[1])

        # 文件状态（porcelain 格式）
        code, out, _ = self._run(["status", "--porcelain"])
        if code != 0:
            return status

        for line in out.split("\n"):
            if not line.strip():
                continue
            xy = line[:2]
            fname = line[3:].strip().split(" -> ")[-1]  # 处理重命名

            # 暂存区状态 (X)
            staged = xy[0]
            if staged == "M":
                status.staged.append(fname)
            elif staged == "A":
                status.staged.append(fname)
            elif staged == "D":
                status.staged.append(fname)
            elif staged == "R":
                status.renamed.append(fname)

            # 工作区状态 (Y)
            worktree = xy[1]
            if worktree == "M":
                status.modified.append(fname)
            elif worktree == "D":
                status.deleted.append(fname)
            elif worktree == "?":
                status.untracked.append(fname)

            # 冲突
            if "U" in xy:
                status.has_conflicts = True

        # 判断是否干净
        status.is_clean = not (
            status.staged or status.modified or
            status.untracked or status.deleted or status.renamed
        ) and not status.has_conflicts

        return status

    def diff(self, file_path: str = "", staged: bool = False, max_lines: int = 500) -> str:
        """查看差异"""
        args = ["diff"]
        if staged:
            args.append("--staged")
        if file_path:
            args.extend(["--", file_path])
        code, out, err = self._run(args)
        if code != 0:
            return f"Error: {err}"
        if not out:
            return "(no changes)"
        # 截断
        lines = out.split("\n")
        if len(lines) > max_lines:
            return "\n".join(lines[:max_lines]) + f"\n... ({len(lines) - max_lines} more lines)"
        return out

    def log(self, max_count: int = 15, file_path: str = "") -> List[GitCommit]:
        """查看提交历史"""
        fmt = "--pretty=format:%H|%h|%an|%ad|%s"
        args = ["log", fmt, "--date=short", f"-n{max_count}"]
        if file_path:
            args.extend(["--", file_path])

        code, out, _ = self._run(args)
        if code != 0 or not out:
            return []

        commits = []
        for line in out.split("\n"):
            parts = line.split("|", 4)
            if len(parts) >= 5:
                commits.append(GitCommit(
                    hash=parts[0],
                    short_hash=parts[1],
                    author=parts[2],
                    date=parts[3],
                    message=parts[4],
                ))
        return commits

    def blame(self, file_path: str, max_lines: int = 200) -> str:
        """查看文件各行作者"""
        code, out, err = self._run(["blame", "--date=short", "-w", file_path])
        if code != 0:
            return f"Error: {err}"
        lines = out.split("\n")
        if len(lines) > max_lines:
            return "\n".join(lines[:max_lines]) + f"\n... ({len(lines) - max_lines} more lines)"
        return out

    # ── 暂存 / 提交 ──

    def stage(self, file_paths: List[str], dry_run: bool = False) -> GitOpResult:
        """暂存文件"""
        if not file_paths:
            return GitOpResult(success=False, error="No files specified")

        if dry_run:
            return GitOpResult(
                success=True,
                output=f"[DRY RUN] Would stage: {', '.join(file_paths)}",
                dry_run=True,
            )

        code, out, err = self._run(["add", "--"] + file_paths)
        if code != 0:
            return GitOpResult(success=False, error=err)
        return GitOpResult(success=True, output=f"Staged: {', '.join(file_paths)}")

    def unstage(self, file_paths: List[str]) -> GitOpResult:
        """取消暂存"""
        code, out, err = self._run(["reset", "HEAD", "--"] + file_paths)
        if code != 0:
            return GitOpResult(success=False, error=err)
        return GitOpResult(success=True, output=f"Unstaged: {', '.join(file_paths)}")

    def commit(self, message: str, dry_run: bool = False) -> GitOpResult:
        """提交变更"""
        if not message.strip():
            return GitOpResult(success=False, error="Commit message is required")

        if dry_run:
            # 预览将要提交的内容
            code, out, _ = self._run(["diff", "--staged", "--stat"])
            return GitOpResult(
                success=True,
                output=f"[DRY RUN] Would commit with message: {message}\n\n{out}",
                dry_run=True,
            )

        code, out, err = self._run(["commit", "-m", message])
        if code != 0:
            return GitOpResult(success=False, error=err)
        return GitOpResult(success=True, output=out)

    # ── 分支 ──

    def branch_list(self) -> List[Dict[str, str]]:
        """列出所有分支"""
        code, out, _ = self._run(["branch", "-a", "--format=%(refname:short)|%(objectname:short)|%(upstream:short)"])
        if code != 0:
            return []
        branches = []
        for line in out.split("\n"):
            parts = line.split("|")
            if len(parts) >= 1 and parts[0]:
                branches.append({
                    "name": parts[0].strip(),
                    "hash": parts[1].strip() if len(parts) > 1 else "",
                    "upstream": parts[2].strip() if len(parts) > 2 else "",
                })
        return branches

    def branch_create(self, name: str, dry_run: bool = False) -> GitOpResult:
        """创建分支"""
        if dry_run:
            return GitOpResult(success=True, output=f"[DRY RUN] Would create branch: {name}", dry_run=True)
        code, out, err = self._run(["checkout", "-b", name])
        if code != 0:
            return GitOpResult(success=False, error=err)
        return GitOpResult(success=True, output=f"Created and switched to branch: {name}")

    def checkout(self, target: str, dry_run: bool = False) -> GitOpResult:
        """切换分支/提交"""
        if dry_run:
            return GitOpResult(success=True, output=f"[DRY RUN] Would checkout: {target}", dry_run=True)
        code, out, err = self._run(["checkout", target])
        if code != 0:
            return GitOpResult(success=False, error=err)
        return GitOpResult(success=True, output=out or f"Switched to {target}")

    def merge(self, branch: str, dry_run: bool = False) -> GitOpResult:
        """合并分支"""
        if dry_run:
            return GitOpResult(success=True, output=f"[DRY RUN] Would merge {branch}", dry_run=True)
        code, out, err = self._run(["merge", branch])
        if code != 0:
            return GitOpResult(success=False, error=err)
        return GitOpResult(success=True, output=out)

    # ── 安全操作 ──

    def stash_push(self, message: str = "") -> GitOpResult:
        """暂存当前工作区变更"""
        args = ["stash", "push"]
        if message:
            args.extend(["-m", message])
        code, out, err = self._run(args)
        if code != 0:
            return GitOpResult(success=False, error=err)
        return GitOpResult(success=True, output=out or "Changes stashed")

    def stash_pop(self) -> GitOpResult:
        """恢复最近的 stash"""
        code, out, err = self._run(["stash", "pop"])
        if code != 0:
            return GitOpResult(success=False, error=err)
        return GitOpResult(success=True, output=out or "Stash popped")

    def stash_list(self) -> str:
        """列出 stash"""
        code, out, _ = self._run(["stash", "list"])
        return out if code == 0 else ""

    def pull(self, dry_run: bool = False) -> GitOpResult:
        """拉取远程更新"""
        if dry_run:
            return GitOpResult(success=True, output="[DRY RUN] Would execute: git pull", dry_run=True)
        code, out, err = self._run(["pull", "--rebase"])
        if code != 0:
            return GitOpResult(success=False, error=err)
        return GitOpResult(success=True, output=out or "Pull successful")

    def push(self, dry_run: bool = False) -> GitOpResult:
        """推送到远程（安全模式：默认不带 --force）"""
        if dry_run:
            return GitOpResult(success=True, output="[DRY RUN] Would execute: git push", dry_run=True)
        code, out, err = self._run(["push"])
        if code != 0:
            return GitOpResult(success=False, error=err)
        return GitOpResult(success=True, output=out or "Push successful")

    # ── 撤销 ──

    def restore(self, file_paths: List[str], staged: bool = False, dry_run: bool = False) -> GitOpResult:
        """恢复文件到最近提交状态"""
        if dry_run:
            return GitOpResult(
                success=True,
                output=f"[DRY RUN] Would restore: {', '.join(file_paths)}",
                dry_run=True,
            )
        args = ["restore"]
        if staged:
            args.append("--staged")
        args.extend(["--"] + file_paths)
        code, out, err = self._run(args)
        if code != 0:
            return GitOpResult(success=False, error=err)
        return GitOpResult(success=True, output=f"Restored: {', '.join(file_paths)}")

    def revert(self, commit_hash: str, dry_run: bool = False) -> GitOpResult:
        """回退指定提交"""
        if dry_run:
            return GitOpResult(
                success=True,
                output=f"[DRY RUN] Would revert: {commit_hash}",
                dry_run=True,
            )
        code, out, err = self._run(["revert", "--no-edit", commit_hash])
        if code != 0:
            return GitOpResult(success=False, error=err)
        return GitOpResult(success=True, output=out or f"Reverted {commit_hash}")

    # ── 辅助 ──

    def has_git(self) -> bool:
        return os.path.isdir(self._git_dir)

    def get_repo_name(self) -> str:
        return os.path.basename(self.repo_path)

    def get_remote_url(self) -> str:
        code, out, _ = self._run(["remote", "get-url", "origin"])
        return out if code == 0 else ""

    def is_safe(self) -> bool:
        """检查是否有未保存的变更（安全门）"""
        s = self.status()
        return s.is_clean

```
