"""超时执行脚本 — 接受命令行参数"""
import subprocess, sys

target = sys.argv[1] if len(sys.argv) > 1 else '/Volumes/D盘工作区/一人公司拆分版/one_company_split/intelligence/tests/debug_mcp4.py'

proc = subprocess.Popen(
    [sys.executable, target],
    stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
)
try:
    stdout, stderr = proc.communicate(timeout=10)
    print(stdout)
    if stderr: print("STDERR:", stderr)
except subprocess.TimeoutExpired:
    proc.kill()
    stdout, stderr = proc.communicate()
    print("TIMEOUT!")
    if stdout: print("stdout:", stdout[:500])
    if stderr: print("stderr:", stderr[:500])
