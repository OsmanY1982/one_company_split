# `config/supabase_config.py`

> 路径：`config/supabase_config.py` | 行数：7


---


```python
# Supabase 云端同步配置
# 与 iqra/core/supabase_client.py 共用同一 Supabase 项目

SUPABASE_URL = "https://zkpymaioolnxxbqsapnj.supabase.co"
SUPABASE_ANON_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InprcHltYWlvb2xueHhicXNhcG5qIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzcxNTI2NzIsImV4cCI6MjA5MjcyODY3Mn0.c7IO7Cf2u4EgwMwB-zF7KGO38XkAg19guwmfEUGEJk8"
SUPABASE_SERVICE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InprcHltYWlvb2xueHhicXNhcG5qIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc3NzE1MjY3MiwiZXhwIjoyMDkyNzI4NjcyfQ.a9wsDspX9zytWNQXReS6ytsFQP2Zw_YdiAlNUV0XQps"
SUPABASE_PROJECT_ID = SUPABASE_URL.split("//")[-1].split(".")[0]

```
