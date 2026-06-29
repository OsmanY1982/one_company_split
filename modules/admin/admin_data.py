# -*- coding: utf-8 -*-
"""
后台管理 - 数据管理（云端同步、缓存清理、数据清空）
"""
import sys
import os
import shutil

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QMessageBox, QGroupBox
)

# 动态获取项目根目录
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)

from core.paths import BASE_DIR as CORE_BASE_DIR, DATA_DIR, CONFIG_DIR


class AdminDataWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)

        # ═══ 云端数据同步 ═══
        cloud_sync_group = QGroupBox("云端数据同步")
        cs_layout = QVBoxLayout(cloud_sync_group)
        cs_layout.addWidget(QLabel("将 Supabase 云端所有数据拉取到本地，实现管理员后台 = 云端镜像"))
        cs_layout.addWidget(QLabel("同步内容: 用户、激活码、产品、订单、会员记录"))
        cs_layout.addWidget(QLabel("⚠️ 现有本地数据将被云端数据覆盖 (admin 账号保留)"))

        btn_cloud_pull = QPushButton("从云端拉取全部数据")
        btn_cloud_pull.setStyleSheet("background-color: #6f42c1; color: white; padding: 10px 30px; font-weight: bold;")
        btn_cloud_pull.clicked.connect(self._pull_from_cloud)
        cs_layout.addWidget(btn_cloud_pull)
        layout.addWidget(cloud_sync_group)

        # ═══ 数据备份 ═══
        backup_group = QGroupBox("数据备份")
        b_layout = QVBoxLayout(backup_group)
        b_layout.addWidget(QLabel("备份内容:所有数据库(.db) + 代码(.py) + 配置(.json)"))
        b_layout.addWidget(QLabel("🔐 备份文件加密保存,外部无法直接打开,只能通过本系统恢复"))

        btn_backup = QPushButton("立即加密备份")
        btn_backup.setStyleSheet("background-color: #007bff; color: white; padding: 10px 30px; font-weight: bold;")
        btn_backup.clicked.connect(self._create_backup)
        b_layout.addWidget(btn_backup)
        b_layout.addWidget(QLabel(f"保存位置: {os.path.join(CORE_BASE_DIR, 'backup')}/  格式: .opcbak(加密)"))
        layout.addWidget(backup_group)

        # ═══ 数据清理 ═══
        clean_group = QGroupBox("数据清理")
        c_layout = QVBoxLayout(clean_group)
        c_layout.addWidget(QLabel("清理缓存文件:"))
        btn_cache = QPushButton("清理缓存")
        btn_cache.setStyleSheet("background-color: #FF9800; color: white; padding: 8px 20px;")
        btn_cache.clicked.connect(self._clean_cache)
        c_layout.addWidget(btn_cache)
        c_layout.addWidget(QLabel("清空所有数据(不可恢复!):"))
        btn_all = QPushButton("清空所有数据")
        btn_all.setStyleSheet("background-color: #dc3545; color: white; padding: 8px 20px;")
        btn_all.clicked.connect(self._clean_all)
        c_layout.addWidget(btn_all)
        layout.addWidget(clean_group)
        layout.addStretch()

    def _pull_from_cloud(self):
        """从云端拉取全部数据到本地"""
        reply = QMessageBox.question(self, "确认同步",
            "将从 Supabase 云端拉取全部数据到本地:\n\n"
            "📋  用户数据\n"
            "🔑  激活码\n"
            "📦  产品\n"
            "📋  订单\n"
            "👤  会员记录\n\n"
            "现有本地数据将被云端数据覆盖 (admin 账号保留)。\n确认继续?",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply != QMessageBox.Yes:
            return

        try:
            from core.cloud_pull import pull_all_from_cloud
            info = pull_all_from_cloud()

            if info.get('errors'):
                err_msgs = '\n'.join([f"  {k}: {e}" for k, e in info['errors']])
                QMessageBox.warning(self, "部分失败",
                    f"⚠️ 拉取完成，但有错误:\n总计 {info['total']} 条\n\n{info['summary']}\n\n错误:\n{err_msgs}")
            else:
                QMessageBox.information(self, "同步成功",
                    f"✅ 数据拉取完成!\n总计 {info['total']} 条\n\n{info['summary']}")
        except Exception as e:
            QMessageBox.critical(self, "同步失败", f"❌ 拉取失败: {str(e)[:200]}")

    def _create_backup(self):
        from core.backup import auto_backup
        ok, msg, _ = auto_backup("后台手动备份")
        if ok:
            QMessageBox.information(self, "备份成功", msg)
        else:
            QMessageBox.warning(self, "备份失败", msg)

    def _clean_cache(self):
        try:
            cache_dirs = [
                os.path.join(CORE_BASE_DIR, "__pycache__"),
                os.path.join(CORE_BASE_DIR, "modules", "__pycache__")
            ]
            count = 0
            for d in cache_dirs:
                if os.path.exists(d):
                    shutil.rmtree(d)
                    count += 1
            QMessageBox.information(self, "成功", f"已清理 {count} 个缓存目录")
        except Exception as e:
            QMessageBox.warning(self, "失败", str(e))

    def _clean_all(self):
        reply = QMessageBox.question(self, "警告", "确定要清空所有数据吗?此操作不可恢复!",
                                    QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            if QMessageBox.Yes == QMessageBox.question(self, "再次确认", "最后一次确认,数据删除后无法恢复!"):
                # 询问是否清除登录记忆
                clear_login = QMessageBox.Yes == QMessageBox.question(
                    self, "清除登录记忆", "是否同时清除登录记忆?\n\n是:删除保存的账号密码,下次需重新登录\n否:保留登录记忆",
                    QMessageBox.Yes | QMessageBox.No)
                if clear_login:
                    remember_file = os.path.join(CONFIG_DIR, "remember.json")
                    if os.path.exists(remember_file):
                        os.remove(remember_file)

                data_dir = os.path.join(CORE_BASE_DIR, "data")
                if os.path.exists(data_dir):
                    for f in os.listdir(data_dir):
                        os.remove(os.path.join(data_dir, f))
                QMessageBox.information(self, "成功", "数据已清空!")
