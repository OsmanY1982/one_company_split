# -*- coding: utf-8 -*-
"""
云端接口预留：用于后续对接云端API
"""

class CloudAPI:
    def send_verification_code(self, account, method='email'):
        # TODO: 发送验证码到邮箱/手机
        return False, "暂未接入云端验证码服务"

    def verify_code(self, account, code):
        # TODO: 校验验证码
        return False, "暂未接入云端验证码服务"

    def login(self, account, password):
        # TODO: 对接云端登录API
        return False, "暂未接入云端服务"

    def register(self, account, password):
        # TODO: 对接云端注册API
        return False, "暂未接入云端服务"

    def sync_data(self, user_id, data):
        # TODO: 对接云端数据同步API
        return False, "暂未接入云端服务"
