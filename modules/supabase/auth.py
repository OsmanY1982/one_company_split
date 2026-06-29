# -*- coding: utf-8 -*-
"""
modules.supabase.auth — Re-export bridge to core.modules.supabase.auth

The canonical implementation lives at core/modules/supabase/auth.py.
This file enables `from modules.supabase.auth import ...` to work
without modifying existing import chains.
"""
from core.modules.supabase.auth import *  # noqa: F401, F403
