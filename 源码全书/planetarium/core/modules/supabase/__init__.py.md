# `planetarium/core/modules/supabase/__init__.py`

> 路径：`planetarium/core/modules/supabase/__init__.py` | 行数：45


---


```python
# -*- coding: utf-8 -*-
# Supabase 云端同步客户端 — 桥接存根（主源：iqra/core/modules/supabase/）
from iqra.core.modules.supabase._core import (
    SSL_VERIFY,
    SSL_CTX,
    _dns_reachable,
    _dns_precheck,
    _request,
    test_connection,
    check_user_cloud_status,
)
from iqra.core.modules.supabase.activation import CloudActivation, CloudLog
from iqra.core.modules.supabase.auth import CloudUser, CloudSession
from iqra.core.modules.supabase.business import CloudMembership, CloudOrder, CloudFinance, CloudCustomer, CloudProduct
from iqra.core.modules.supabase.wallet import CloudWallet, CloudWalletTxn
from iqra.core.modules.supabase.distribution import CloudDistribution, CloudCommission
from iqra.core.modules.supabase.member import CloudMember
from iqra.core.modules.supabase.admin_log import CloudAdminLog
from iqra.core.modules.supabase.updater import UpdateChecker

__all__ = [
    "SSL_VERIFY",
    "SSL_CTX",
    "_dns_reachable",
    "_dns_precheck",
    "_request",
    "test_connection",
    "check_user_cloud_status",
    "CloudActivation",
    "CloudLog",
    "CloudUser",
    "CloudSession",
    "CloudMembership",
    "CloudOrder",
    "CloudFinance",
    "CloudCustomer",
    "CloudProduct",
    "CloudWallet",
    "CloudWalletTxn",
    "CloudDistribution",
    "CloudCommission",
    "CloudMember",
    "CloudAdminLog",
    "UpdateChecker",
]

```
