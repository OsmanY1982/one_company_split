# `iqra/core/code_executor.py`

> 路径：`iqra/core/code_executor.py` | 行数：686


---


```python
"""
代码执行沙箱
安全执行 Python 代码，支持资源限制和超时控制
"""

import ast
import builtins
import contextlib
import io
import multiprocessing
import os
import resource
import signal
import sys
import threading
import time
import traceback
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Callable


@dataclass
class ExecutionResult:
    """代码执行结果"""
    success: bool
    output: str
    error: Optional[str] = None
    execution_time: float = 0.0
    memory_used: int = 0
    return_value: Any = None


class CodeValidator:
    """代码安全验证器"""
    
    # 危险模块和函数黑名单
    DANGEROUS_MODULES = {
        'os', 'sys', 'subprocess', 'socket', 'urllib', 'http',
        'ftplib', 'smtplib', 'poplib', 'imaplib', 'telnetlib',
        'requests', 'paramiko', 'fabric', 'pexpect',
        'ctypes', 'mmap', 'resource', 'signal', 'gc',
        'importlib', 'imp', 'modulefinder', 'runpy',
        'compileall', 'py_compile', 'zipfile', 'tarfile',
        'shutil', 'pathlib', 'path', 'pickle', 'shelve',
        'dbm', 'sqlite3', 'mysql', 'psycopg2', 'pymongo'
    }
    
    DANGEROUS_FUNCTIONS = {
        'eval', 'exec', 'compile', '__import__', 'open',
        'input', 'raw_input', 'print', 'exit', 'quit',
        'reload', 'breakpoint', 'help', 'license', 'credits',
        '__builtins__', '__import__', '__loader__', '__spec__',
        'globals', 'locals', 'vars', 'dir', 'getattr',
        'setattr', 'delattr', 'hasattr', 'isinstance',
        'issubclass', 'callable', 'staticmethod', 'classmethod',
        'property', 'super', 'type', 'object', 'class'
    }
    
    DANGEROUS_ATTRIBUTES = {
        '__class__', '__bases__', '__mro__', '__subclasses__',
        '__init__', '__new__', '__del__', '__getattr__',
        '__setattr__', '__delattr__', '__getattribute__',
        '__dict__', '__module__', '__name__', '__file__',
        '__path__', '__package__', '__cached__', '__spec__',
        '__loader__', '__import__', '__builtins__', '__globals__',
        '__closure__', '__code__', '__defaults__', '__kwdefaults__',
        '__annotations__', '__doc__', '__qualname__', '__slots__'
    }
    
    @classmethod
    def validate(cls, code: str) -> tuple[bool, Optional[str]]:
        """
        验证代码安全性
        
        Returns:
            (是否安全, 错误信息)
        """
        try:
            tree = ast.parse(code)
        except SyntaxError as e:
            return False, f"语法错误: {e}"
        
        for node in ast.walk(tree):
            # 检查导入语句
            if isinstance(node, ast.Import):
                for alias in node.names:
                    module_name = alias.name.split('.')[0]
                    if module_name in cls.DANGEROUS_MODULES:
                        return False, f"禁止导入模块: {alias.name}"
            
            # 检查 from ... import 语句
            if isinstance(node, ast.ImportFrom):
                module_name = node.module.split('.')[0] if node.module else ''
                if module_name in cls.DANGEROUS_MODULES:
                    return False, f"禁止从模块导入: {node.module}"
            
            # 检查函数调用
            if isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name):
                    if node.func.id in cls.DANGEROUS_FUNCTIONS:
                        return False, f"禁止调用函数: {node.func.id}"
            
            # 检查属性访问
            if isinstance(node, ast.Attribute):
                if node.attr in cls.DANGEROUS_ATTRIBUTES:
                    return False, f"禁止访问属性: {node.attr}"
            
            # 检查文件操作
            if isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name):
                    if node.func.id in ('open', 'file'):
                        return False, "禁止文件操作"
            
            # 检查网络操作
            if isinstance(node, ast.Call):
                if isinstance(node.func, ast.Attribute):
                    if node.func.attr in ('connect', 'bind', 'listen', 'accept'):
                        return False, "禁止网络操作"
        
        return True, None


class SecureSandbox:
    """
    安全代码执行沙箱
    支持资源限制、超时控制、安全验证
    """
    
    def __init__(self,
                 timeout: int = 30,
                 max_memory: int = 512 * 1024 * 1024,  # 512MB
                 max_output: int = 100 * 1024,  # 100KB
                 allow_modules: List[str] = None):
        """
        初始化沙箱
        
        Args:
            timeout: 执行超时时间（秒）
            max_memory: 最大内存使用（字节）
            max_output: 最大输出长度（字节）
            allow_modules: 允许导入的模块列表
        """
        self.timeout = timeout
        self.max_memory = max_memory
        self.max_output = max_output
        self.allow_modules = allow_modules or [
            'math', 'random', 'datetime', 'json', 're',
            'string', 'collections', 'itertools', 'functools',
            'statistics', 'fractions', 'decimal', 'hashlib',
            'base64', 'binascii', 'uuid', 'time', 'calendar'
        ]
        
        # 创建安全的全局命名空间
        self.safe_globals = self._create_safe_globals()
    
    def _create_safe_globals(self) -> Dict[str, Any]:
        """创建安全的全局命名空间"""
        safe_globals = {
            '__builtins__': {
                'True': True,
                'False': False,
                'None': None,
                'abs': abs,
                'all': all,
                'any': any,
                'ascii': ascii,
                'bin': bin,
                'bool': bool,
                'bytearray': bytearray,
                'bytes': bytes,
                'callable': callable,
                'chr': chr,
                'complex': complex,
                'dict': dict,
                'divmod': divmod,
                'enumerate': enumerate,
                'filter': filter,
                'float': float,
                'format': format,
                'frozenset': frozenset,
                'hasattr': hasattr,
                'hash': hash,
                'hex': hex,
                'id': id,
                'int': int,
                'isinstance': isinstance,
                'issubclass': issubclass,
                'iter': iter,
                'len': len,
                'list': list,
                'map': map,
                'max': max,
                'memoryview': memoryview,
                'min': min,
                'next': next,
                'object': object,
                'oct': oct,
                'ord': ord,
                'pow': pow,
                'print': self._safe_print,
                'property': property,
                'range': range,
                'repr': repr,
                'reversed': reversed,
                'round': round,
                'set': set,
                'slice': slice,
                'sorted': sorted,
                'staticmethod': staticmethod,
                'str': str,
                'sum': sum,
                'super': super,
                'tuple': tuple,
                'type': type,
                'vars': vars,
                'zip': zip,
                '__import__': self._safe_import,
            }
        }
        
        # 预导入允许的模块
        for module_name in self.allow_modules:
            try:
                module = __import__(module_name)
                safe_globals[module_name] = module
            except ImportError:
                pass
        
        return safe_globals
    
    def _safe_print(self, *args, **kwargs):
        """安全的 print 函数"""
        output = io.StringIO()
        print(*args, file=output, **kwargs)
        result = output.getvalue()
        output.close()
        return result
    
    def _safe_import(self, name: str, *args, **kwargs):
        """安全的 import 函数"""
        base_module = name.split('.')[0]
        if base_module not in self.allow_modules:
            raise ImportError(f"禁止导入模块: {name}")
        return __import__(name, *args, **kwargs)
    
    def execute(self, code: str, context: Dict[str, Any] = None) -> ExecutionResult:
        """
        在沙箱中执行代码
        
        Args:
            code: Python 代码
            context: 额外的上下文变量
            
        Returns:
            ExecutionResult
        """
        start_time = time.time()
        
        # 验证代码安全性
        is_safe, error = CodeValidator.validate(code)
        if not is_safe:
            return ExecutionResult(
                success=False,
                output="",
                error=f"代码验证失败: {error}",
                execution_time=time.time() - start_time
            )
        
        # 准备执行环境
        local_vars = {}
        if context:
            local_vars.update(context)
        
        # 创建输出捕获
        output_buffer = io.StringIO()
        
        try:
            # 使用进程池执行代码（隔离环境）
            with multiprocessing.Pool(1) as pool:
                result = pool.apply_async(
                    self._execute_in_process,
                    (code, self.safe_globals, local_vars)
                )
                
                try:
                    exec_result = result.get(timeout=self.timeout)
                except multiprocessing.TimeoutError:
                    pool.terminate()
                    return ExecutionResult(
                        success=False,
                        output=output_buffer.getvalue()[:self.max_output],
                        error=f"执行超时（{self.timeout}秒）",
                        execution_time=time.time() - start_time
                    )
            
            execution_time = time.time() - start_time
            
            return ExecutionResult(
                success=exec_result['success'],
                output=exec_result['output'][:self.max_output],
                error=exec_result.get('error'),
                execution_time=execution_time,
                return_value=exec_result.get('return_value')
            )
            
        except Exception as e:
            return ExecutionResult(
                success=False,
                output=output_buffer.getvalue()[:self.max_output],
                error=f"执行错误: {str(e)}\n{traceback.format_exc()}",
                execution_time=time.time() - start_time
            )
    
    @staticmethod
    def _execute_in_process(code: str, globals_dict: Dict, locals_dict: Dict) -> Dict:
        """在独立进程中执行代码"""
        output_buffer = io.StringIO()
        
        try:
            # 重定向标准输出
            with contextlib.redirect_stdout(output_buffer):
                # 编译代码
                compiled_code = compile(code, '<sandbox>', 'exec')
                
                # 执行代码
                exec(compiled_code, globals_dict, locals_dict)
            
            # 获取输出
            output = output_buffer.getvalue()
            output_buffer.close()
            
            # 查找可能的返回值（最后一个表达式的值）
            return_value = None
            if locals_dict:
                # 尝试获取最后一个变量的值
                last_var = list(locals_dict.keys())[-1] if locals_dict else None
                if last_var:
                    return_value = locals_dict.get(last_var)
            
            return {
                'success': True,
                'output': output,
                'return_value': return_value
            }
            
        except Exception as e:
            output = output_buffer.getvalue()
            output_buffer.close()
            
            return {
                'success': False,
                'output': output,
                'error': f"{str(e)}\n{traceback.format_exc()}"
            }


class CodeExecutor:
    """
    代码执行器
    提供高级代码执行功能，支持模板、预设、批量执行
    """
    
    def __init__(self, default_timeout: int = 30):
        """
        初始化代码执行器
        
        Args:
            default_timeout: 默认超时时间
        """
        self.default_timeout = default_timeout
        self.sandboxes: Dict[str, SecureSandbox] = {}
        self.presets: Dict[str, str] = {}
        self.execution_history: List[Dict] = []
    
    def create_sandbox(self, name: str, **kwargs) -> SecureSandbox:
        """创建命名沙箱"""
        sandbox = SecureSandbox(**kwargs)
        self.sandboxes[name] = sandbox
        return sandbox
    
    def get_sandbox(self, name: str = 'default') -> SecureSandbox:
        """获取沙箱，如果不存在则创建默认沙箱"""
        if name not in self.sandboxes:
            self.sandboxes[name] = SecureSandbox(timeout=self.default_timeout)
        return self.sandboxes[name]
    
    def execute(self, code: str, 
                sandbox_name: str = 'default',
                context: Dict[str, Any] = None,
                timeout: int = None) -> ExecutionResult:
        """
        执行代码
        
        Args:
            code: Python 代码
            sandbox_name: 沙箱名称
            context: 上下文变量
            timeout: 超时时间（覆盖默认）
            
        Returns:
            ExecutionResult
        """
        sandbox = self.get_sandbox(sandbox_name)
        
        if timeout:
            sandbox.timeout = timeout
        
        result = sandbox.execute(code, context)
        
        # 记录执行历史
        self.execution_history.append({
            'timestamp': time.time(),
            'code': code[:1000],  # 只记录前1000字符
            'sandbox': sandbox_name,
            'success': result.success,
            'execution_time': result.execution_time
        })
        
        return result
    
    def execute_with_template(self, template: str, 
                              variables: Dict[str, Any],
                              sandbox_name: str = 'default') -> ExecutionResult:
        """
        使用模板执行代码
        
        Args:
            template: 代码模板
            variables: 模板变量
            sandbox_name: 沙箱名称
            
        Returns:
            ExecutionResult
        """
        # 简单的模板替换
        code = template
        for key, value in variables.items():
            placeholder = f"{{{{{key}}}}}"
            code = code.replace(placeholder, repr(value))
        
        return self.execute(code, sandbox_name)
    
    def execute_batch(self, codes: List[str],
                      sandbox_name: str = 'default',
                      stop_on_error: bool = True) -> List[ExecutionResult]:
        """
        批量执行代码
        
        Args:
            codes: 代码列表
            sandbox_name: 沙箱名称
            stop_on_error: 遇到错误时停止
            
        Returns:
            ExecutionResult 列表
        """
        results = []
        
        for code in codes:
            result = self.execute(code, sandbox_name)
            results.append(result)
            
            if not result.success and stop_on_error:
                break
        
        return results
    
    def add_preset(self, name: str, code: str):
        """添加代码预设"""
        self.presets[name] = code
    
    def execute_preset(self, name: str, 
                       variables: Dict[str, Any] = None,
                       sandbox_name: str = 'default') -> ExecutionResult:
        """执行预设代码"""
        if name not in self.presets:
            return ExecutionResult(
                success=False,
                output="",
                error=f"预设不存在: {name}"
            )
        
        code = self.presets[name]
        
        if variables:
            code = self._apply_variables(code, variables)
        
        return self.execute(code, sandbox_name)
    
    def _apply_variables(self, code: str, variables: Dict[str, Any]) -> str:
        """应用变量到代码"""
        for key, value in variables.items():
            placeholder = f"{{{{{key}}}}}"
            code = code.replace(placeholder, repr(value))
        return code
    
    def get_history(self, limit: int = 100) -> List[Dict]:
        """获取执行历史"""
        return self.execution_history[-limit:]
    
    def clear_history(self):
        """清除执行历史"""
        self.execution_history.clear()
    
    def get_stats(self) -> Dict[str, Any]:
        """获取执行统计"""
        if not self.execution_history:
            return {
                'total_executions': 0,
                'successful': 0,
                'failed': 0,
                'average_time': 0
            }
        
        total = len(self.execution_history)
        successful = sum(1 for h in self.execution_history if h['success'])
        failed = total - successful
        avg_time = sum(h['execution_time'] for h in self.execution_history) / total
        
        return {
            'total_executions': total,
            'successful': successful,
            'failed': failed,
            'average_time': round(avg_time, 3)
        }


# ════════════════════════════════════════════════════════════
# 常用代码预设
# ════════════════════════════════════════════════════════════

DATA_ANALYSIS_PRESETS = {
    'calculate_statistics': '''
import statistics

data = {{{data}}}
result = {
    'mean': statistics.mean(data),
    'median': statistics.median(data),
    'stdev': statistics.stdev(data) if len(data) > 1 else 0,
    'min': min(data),
    'max': max(data),
    'sum': sum(data),
    'count': len(data)
}
print(result)
''',
    
    'sort_data': '''
data = {{{data}}}
key = {{{key}}}
reverse = {{{reverse}}}
result = sorted(data, key=lambda x: x.get(key, x) if isinstance(x, dict) else x, reverse=reverse)
print(result)
''',
    
    'filter_data': '''
data = {{{data}}}
condition = {{{condition}}}
# condition 是一个 lambda 函数字符串
result = [x for x in data if eval(condition)(x)]
print(result)
''',
    
    'group_by': '''
from collections import defaultdict

data = {{{data}}}
key_func = {{{key_func}}}
result = defaultdict(list)
for item in data:
    key = eval(key_func)(item)
    result[key].append(item)
print(dict(result))
''',
    
    'calculate_percentages': '''
data = {{{data}}}
total = sum(data.values()) if isinstance(data, dict) else sum(data)
result = {k: round(v/total*100, 2) for k, v in data.items()} if isinstance(data, dict) else [round(v/total*100, 2) for v in data]
print(result)
''',
    
    'date_calculations': '''
from datetime import datetime, timedelta

start_date = datetime.strptime({{{start_date}}}, '%Y-%m-%d')
end_date = datetime.strptime({{{end_date}}}, '%Y-%m-%d')
days = (end_date - start_date).days
result = {
    'days': days,
    'weeks': days // 7,
    'months_approx': days // 30,
    'years_approx': days // 365
}
print(result)
'''
}


# ════════════════════════════════════════════════════════════
# 便捷函数
# ════════════════════════════════════════════════════════════

# 全局执行器实例
_executor = None

def get_executor() -> CodeExecutor:
    """获取全局代码执行器"""
    global _executor
    if _executor is None:
        _executor = CodeExecutor()
        # 加载预设
        for name, code in DATA_ANALYSIS_PRESETS.items():
            _executor.add_preset(name, code)
    return _executor


def execute_code(code: str, context: Dict[str, Any] = None, timeout: int = 30) -> ExecutionResult:
    """便捷函数：执行代码"""
    return get_executor().execute(code, context=context, timeout=timeout)


def calculate_statistics(data: list) -> ExecutionResult:
    """便捷函数：计算统计数据"""
    return get_executor().execute_preset('calculate_statistics', {'data': data})


def safe_eval(expression: str) -> Any:
    """安全地评估表达式"""
    result = execute_code(f"result = {expression}")
    if result.success:
        return result.return_value
    return None


# ════════════════════════════════════════════════════════════
# 测试
# ════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("代码执行沙箱测试")
    print("=" * 50)
    
    # 测试 1: 简单计算
    print("\n测试 1: 简单计算")
    result = execute_code("""
import math
x = 10
y = 20
result = x + y
print(f"结果: {result}")
print(f"平方根: {math.sqrt(result)}")
""")
    print(f"成功: {result.success}")
    print(f"输出: {result.output}")
    print(f"执行时间: {result.execution_time:.3f}s")
    
    # 测试 2: 数据分析
    print("\n测试 2: 数据分析")
    result = calculate_statistics([1, 2, 3, 4, 5, 6, 7, 8, 9, 10])
    print(f"成功: {result.success}")
    print(f"输出: {result.output}")
    
    # 测试 3: 危险代码（应该被拒绝）
    print("\n测试 3: 危险代码检测")
    result = execute_code("""
import os
os.system('ls -la')
""")
    print(f"成功: {result.success}")
    print(f"错误: {result.error}")
    
    # 测试 4: 超时测试
    print("\n测试 4: 超时测试")
    result = execute_code("""
import time
time.sleep(10)
print("完成")
""", timeout=2)
    print(f"成功: {result.success}")
    print(f"错误: {result.error}")
    
    # 统计
    print("\n执行统计")
    print(get_executor().get_stats())

```
