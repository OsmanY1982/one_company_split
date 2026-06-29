# -*- coding: utf-8 -*-
import sys as _sys, os as _os
_dir = _os.path.dirname(_os.path.abspath(__file__))
for _ in range(10):
    if _os.path.exists(_os.path.join(_dir, 'dark_theme.py')):
        _parent = _os.path.dirname(_dir)
        if _parent not in _sys.path:
            _sys.path.insert(0, _parent)
        break
    _dir = _os.path.dirname(_dir)

"""
钱包服务模块

提供：钱包管理、充值、提现、转账、交易记录、云端同步
数据库：data/wallet.db (wallet + wallet_transactions)
"""

from ._db import (
    DB_PATH,
    init_db,
    _connect,
    init_address_book_db,
    init_withdrawal_queue,
)

from ._cloud import (
    _cloud_safe,
    _sync_wallet_cloud,
    _sync_txn_cloud,
    reconcile,
    force_sync_all_to_cloud,
)

from ._address import (
    add_address,
    get_addresses,
    update_address,
    delete_address,
)

from ._wallet_crud import (
    get_wallet,
    get_or_create_wallet,
    get_all_wallets,
    get_wallet_stats,
    get_wallet_detail,
    get_top_wallets,
    get_balance,
    update_wallet_status,
    delete_wallet,
)

from ._transactions import (
    recharge,
    withdraw,
    transfer,
    add_commission,
    get_transactions,
    export_transactions_to_csv,
    delete_transaction,
    get_income_expense_report,
    get_balance_trend,
)

from ._withdrawal_queue import (
    submit_withdrawal_request,
    get_pending_withdrawals,
    get_all_withdrawal_requests,
    approve_withdrawal,
    reject_withdrawal,
    cancel_withdrawal_request,
    delete_withdrawal_request,
    clear_withdrawal_queue,
    freeze_amount,
    unfreeze_amount,
)
