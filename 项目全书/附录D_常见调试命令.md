## 启动与测试

```bash
# 开发模式启动（不打包）
python3 main.py

# 只验证模块导入
python3 -c "from modules.dashboard.dashboard_window import DashboardWindow; print('OK')"

# 验证所有核心模块
python3 -c "
from core.cosmic import CosmicBackground
from core.agent import AgentCore
from core.llm_client import LLMClient
from core.data import init_all_dbs
print('All core OK')
"

# 检查数据库完整性
python3 -c "
import sqlite3
for db in ['member.db','staff.db','wallet.db','order.db']:
    conn = sqlite3.connect(f'data/{db}')
    print(db, conn.execute('PRAGMA integrity_check').fetchone()[0])
"
```


## 重置与清理

```bash
# 删除所有数据（危险！）
rm -rf data/*.db data/*.db-wal data/*.db-shm

# 清理 Python 缓存
find . -type d -name '__pycache__' -exec rm -rf {} +

# 重新生成源码全书
python3 gen_book.py
```

---

*一人公司 · 宇宙版 · 项目全书*
*「一个人 + 一台电脑 = 能运转的最小企业」*
*最后更新：2026-06-11*
*（内容由AI生成，仅供参考）*
*（内容由AI生成，仅供参考）*
