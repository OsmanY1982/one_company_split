"""
全局广告启动器
任何模块需要激励广告时，调用 launch_ad(parent_window) 即可。
播放器自动选择：有视频则播视频，无视频降级为内置倒计时广告。
"""
import os
import sys
from PyQt5.QtWidgets import QMessageBox


PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)


def check_and_prompt_ad(parent_window=None):
    """
    检查授权状态，过期则自动弹窗询问是否观看广告延长时间。
    适合放在主窗口 showEvent 中调用。

    管理员（admin/super_admin）不触发广告弹窗。
    """
    # ── 角色检查：管理员跳过广告 ──
    role = _get_window_role(parent_window)
    if role in ("admin", "super_admin"):
        return

    from services.license_service import LicenseService
    try:
        lic = LicenseService().check_license()
        if lic.get("valid"):
            return  # 授权有效，无需提示
    except Exception:
        return  # 无法检查，静默跳过

    from services.ad_service import AdService
    ad_svc = AdService()
    status = ad_svc.can_watch_ad()
    if not status["can_watch"]:
        return  # 今日已达上限，不打扰

    # 弹窗询问
    from PyQt5.QtWidgets import QMessageBox
    msg = QMessageBox(parent_window)
    msg.setWindowTitle("授权已过期")
    msg.setText("您的授权时长已到期。\n观看 15-30 秒赞助广告，可延长 1 小时使用时间。")
    msg.setIcon(QMessageBox.Information)
    watch_btn = msg.addButton("观看广告", QMessageBox.AcceptRole)
    later_btn = msg.addButton("稍后再说", QMessageBox.RejectRole)
    msg.setDefaultButton(watch_btn)
    msg.exec_()

    if msg.clickedButton() == watch_btn:
        launch_ad(parent_window)


def _get_window_role(parent_window) -> str:
    """从父窗口获取当前用户角色，同时查 PermissionService 数据库做双重校验。"""
    # 1. 从窗口对象直接获取 _role 属性
    if parent_window is not None and hasattr(parent_window, "_role"):
        win_role = parent_window._role
        if win_role:
            return win_role

    # 2. 兜底：查询权限数据库中是否有 admin/super_admin 角色分配
    try:
        from services.permission_service import PermissionService
        from core.database import get_conn, close_conn
        db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                               "data", "permissions.db")
        if os.path.exists(db_path):
            conn = get_conn("permissions.db")
            cursor = conn.cursor()
            cursor.execute("""
                SELECT r.code FROM user_roles ur
                JOIN roles r ON ur.role_id = r.id
                WHERE r.code IN ('admin', 'super_admin')
                AND (ur.expires_at IS NULL OR ur.expires_at > datetime('now'))
                LIMIT 1
            """)
            row = cursor.fetchone()
            close_conn("permissions.db")
            if row:
                return row[0]
    except Exception:
        pass

    return ""  # 无法确定角色，按普通用户处理


def launch_ad(parent_window=None):
    """
    直接启动广告播放器，返回是否成功启动。
    看完后自动调用 AdService 延长授权。
    """
    from services.ad_service import AdService
    from modules.ad_player import AdPlayerWidget

    ad_svc = AdService()
    status = ad_svc.can_watch_ad()
    if not status["can_watch"]:
        if parent_window:
            QMessageBox.information(parent_window, "提示", status["message"])
        return False

    player = AdPlayerWidget(None)
    player.resize(640, 420)

    if parent_window and hasattr(parent_window, 'screen'):
        screen_geo = parent_window.screen().availableGeometry()
    else:
        from PyQt5.QtWidgets import QApplication
        app = QApplication.instance()
        screen_geo = app.primaryScreen().availableGeometry()

    player.move(
        screen_geo.center().x() - 320,
        screen_geo.center().y() - 210,
    )

    def on_completed(extend_seconds):
        hours = extend_seconds / 3600
        QMessageBox.information(
            player, "领取成功",
            f"已延长 {hours:.0f} 小时使用时间！\n\n感谢您的支持。",
        )

    def on_dismissed():
        pass  # 未领奖关闭，静默处理

    player.ad_completed.connect(on_completed)
    player.ad_dismissed.connect(on_dismissed)

    if not player.auto_play():
        QMessageBox.warning(player, "播放失败", "无法启动广告")
        return False

    player.show()
    return True
