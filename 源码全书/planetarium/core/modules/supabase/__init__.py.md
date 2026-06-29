# `planetarium/core/modules/supabase/__init__.py`

> 路径：`planetarium/core/modules/supabase/__init__.py` | 行数：45


---


```python
# -*- coding: utf-8 -*-
# Supabase 云端同步客户端 - 子模块聚合导出
from ._core import (
    SSL_VERIFY,
    SSL_CTX,
    _dns_reachable,
    _dns_precheck,
    _request,
    test_connection,
    check_user_cloud_status,
)
from .activation import CloudActivation, CloudLog
from .auth import CloudUser, CloudSession
from .business import CloudMembership, CloudOrder, CloudFinance, CloudCustomer, CloudProduct
from .wallet import CloudWallet, CloudWalletTxn
from .distribution import CloudDistribution, CloudCommission
from .member import CloudMember
from .admin_log import CloudAdminLog
from .updater import UpdateChecker

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
