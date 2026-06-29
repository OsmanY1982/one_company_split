# `iqra/core/process_manager.py`

> 路径：`iqra/core/process_manager.py` | 行数：285


---


```python
"""
Iqra Process Manager - 后台进程管理

提供:
- 启动/停止后台进程
- 实时日志查看
- 标准输入发送
- 进度监控
"""

import os
import time
import json
import subprocess
from typing import Dict, List, Any, Optional


class ProcessManager:
    """后台进程管理器"""
    
    def __init__(self, log_dir: str = None):
        self.processes: Dict[str, Dict] = {}
        if log_dir:
            self.log_dir = log_dir
        else:
            self.log_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "process_logs")
        os.makedirs(self.log_dir, exist_ok=True)
    
    def start(self, command: str, workdir: str = None, name: str = None, 
              timeout: int = None, notify_on_complete: bool = False) -> str:
        """
        启动后台进程
        
        Returns:
            process_id (唯一标识符)
        """
        import uuid
        
        process_id = f"proc_{uuid.uuid4().hex[:8]}"
        
        # 准备环境变量
        env = os.environ.copy()
        if workdir:
            env["IQRA_WORKDIR"] = workdir
        
        # 启动进程
        try:
            proc = subprocess.Popen(
                command,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=False,
                cwd=workdir or ".",
                env=env
            )
            
            self.processes[process_id] = {
                "id": process_id,
                "name": name or command[:50],
                "command": command,
                "workdir": workdir,
                "proc": proc,
                "pid": proc.pid,
                "status": "running",
                "started_at": time.time(),
                "notify_on_complete": notify_on_complete
            }
            
        except Exception as e:
            return {"error": f"启动失败：{e}"}
        
        return process_id
    
    def list_processes(self) -> List[Dict]:
        """列出所有进程"""
        results = []
        for pid, info in self.processes.items():
            results.append({
                "id": info["id"],
                "name": info["name"],
                "status": info["status"],
                "pid": info.get("pid"),
                "started_at": info["started_at"],
                "command": info["command"][:100]
            })
        return results
    
    def poll(self, process_id: str, limit: int = 200) -> Dict:
        """
        检查进程状态并获取新输出
        
        Returns:
            {
                "status": "running|completed|failed|not_found",
                "output": "最新输出片段",
                "return_code": int
            }
        """
        proc_info = self.processes.get(process_id)
        if not proc_info:
            return {"status": "not_found", "output": ""}
        
        status = proc_info["status"]
        
        if status != "running":
            return {
                "status": status,
                "output": "",
                "return_code": proc_info.get("return_code")
            }
        
        # 获取新输出（从 subprocess.Popen.stdout 管道直接读取）
        try:
            output_bytes = b""
            proc = proc_info.get("proc")
            if proc and proc.stdout:
                try:
                    # 非阻塞读取管道中可用的数据
                    import select
                    while select.select([proc.stdout], [], [], 0)[0]:
                        chunk = proc.stdout.read(4096)
                        if not chunk:
                            break
                        output_bytes += chunk
                except Exception:
                    # select 在某些平台不可用，回退到 read1
                    try:
                        while True:
                            chunk = proc.stdout.read1(4096)
                            if not chunk:
                                break
                            output_bytes += chunk
                    except Exception:
                        pass
            
            output = output_bytes.decode('utf-8', errors='replace')
            
            # 检查是否完成
            exit_code = proc_info["proc"].poll()
            if exit_code is not None:
                proc_info["status"] = "completed" if exit_code == 0 else "failed"
                proc_info["return_code"] = exit_code
                proc_info["finished_at"] = time.time()
                
                # 保存完整日志
                self._save_log(process_id, output_bytes)
                
                if proc_info.get("notify_on_complete"):
                    self._send_notification(process_id, exit_code)
            
            return {
                "status": "running",
                "output": output[-10000:],  # 最后 10KB
                "exit_code": exit_code
            }
            
        except Exception as e:
            return {"error": str(e)}
    
    def log(self, process_id: str, offset: int = 0, limit: int = 200) -> Dict:
        """查看完整日志"""
        log_file = os.path.join(self.log_dir, f"{process_id}.log")
        
        if not os.path.exists(log_file):
            return {"log": "", "total_lines": 0}
        
        with open(log_file, 'r', encoding='utf-8') as f:
            all_lines = f.readlines()
        
        total = len(all_lines)
        start = offset * limit
        end = start + limit
        
        return {
            "log": "".join(all_lines[start:end]),
            "total_lines": total,
            "offset": offset,
            "limit": limit
        }
    
    def wait(self, process_id: str, timeout: int = None) -> Dict:
        """等待进程完成"""
        proc_info = self.processes.get(process_id)
        if not proc_info:
            return {"error": "进程不存在"}
        
        if proc_info["status"] != "running":
            return {"status": proc_info["status"]}
        
        try:
            proc_info["proc"].wait(timeout=timeout)
            exit_code = proc_info["proc"].returncode
            
            proc_info["status"] = "completed" if exit_code == 0 else "failed"
            proc_info["return_code"] = exit_code
            proc_info["finished_at"] = time.time()
            
            self._save_log(process_id)
            
            return {
                "status": "completed",
                "return_code": exit_code
            }
            
        except subprocess.TimeoutExpired:
            proc_info["status"] = "timeout"
            return {"error": "超时"}
        except Exception as e:
            return {"error": str(e)}
    
    def kill(self, process_id: str) -> bool:
        """终止进程"""
        proc_info = self.processes.get(process_id)
        if not proc_info:
            return False
        
        try:
            proc_info["proc"].terminate()
            proc_info["status"] = "terminated"
            del self.processes[process_id]
            return True
        except Exception:
            return False
    
    def write(self, process_id: str, data: str):
        """向进程发送 stdin 数据"""
        proc_info = self.processes.get(process_id)
        if not proc_info or proc_info["status"] != "running":
            return
        
        try:
            if hasattr(proc_info["proc"], "stdin") and proc_info["proc"].stdin:
                proc_info["proc"].stdin.write(data.encode() + b'\n')
                proc_info["proc"].stdin.flush()
        except Exception as e:
            return {"error": str(e)}
    
    def submit(self, process_id: str, data: str):
        """发送数据并回车（交互式命令）"""
        self.write(process_id, data)
    
    def close(self, process_id: str):
        """关闭 stdin（发送 EOF）"""
        proc_info = self.processes.get(process_id)
        if not proc_info:
            return
        
        try:
            if hasattr(proc_info["proc"], "stdin") and proc_info["proc"].stdin:
                proc_info["proc"].stdin.close()
        except Exception:
            pass
    
    def _save_log(self, process_id: str, extra_output: bytes = None):
        """保存进程日志"""
        log_file = os.path.join(self.log_dir, f"{process_id}.log")
        
        content = b""
        if extra_output:
            content += extra_output
        
        if os.path.exists(log_file):
            with open(log_file, 'rb') as f:
                content += f.read()
        
        with open(log_file, 'wb') as f:
            f.write(content)
    
    def _send_notification(self, process_id: str, exit_code: int):
        """发送完成通知（预留接口）"""
        pass  # 待与 GUI/Web 集成


# ═══════════════════════════════════════════
# 全局实例
# ═══════════════════════════════════════════

_process_manager = None

def get_process_manager() -> ProcessManager:
    global _process_manager
    if _process_manager is None:
        _process_manager = ProcessManager()
    return _process_manager

```
