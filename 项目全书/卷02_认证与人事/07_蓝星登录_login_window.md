## 第七章 · 蓝星登录（login_window.py）

### 地球仪设计

登录窗口不是普通的表单。中间是一颗缓慢旋转的蓝色地球（`EarthGlobe` 类），用 QPainter 手绘——经纬线、大陆轮廓的抽象简化、大气层辉光。

设计意图：这是「一人公司」的世界观入口。你登录的不是一个软件，而是进入你的宇宙。

### 管理员 vs 会员双通道

底部的登录表单有一个不易察觉的设计：管理员入口是隐藏的。在密码框下方有一个极小的「管理员」链接，点击弹出独立的管理员登录对话框（`admin_login_dialog.py`）。

为什么不做成 Tab 切换？因为：
- 普通用户（会员）不应该看到管理员入口
- 管理员知道入口在哪就行
- 减少了界面的视觉噪音

### 登录流程

```
LoginWindow
  → 验证账号密码（bcrypt 哈希比对，调用 auth_service.py）
  → 读取 membership_info（角色、权限、企业名）
  → 判断角色：
      admin → ConnectWindow(role='admin', ...)
      member → ConnectWindow(role='member', ...)
```

### auth_service.py — 身份认证核心

这是整个认证体系的后端服务，纯 Python 逻辑，不依赖 PyQt：

- `register(username, password, **kwargs)` — bcrypt 加盐哈希注册
- `login(username, password)` — 验证 + 返回用户信息
- `change_password(username, old_pw, new_pw)` — 验证旧密码 + 更新哈希
- `get_membership(username)` — 读取会员等级和到期时间

### 修改密码（change_password_dialog.py）

独立的 QDialog，输入旧密码 + 两次新密码，调用 `auth_service.change_password()`。bcrypt 哈希在服务端完成，UI 层不接触密码哈希逻辑。

### 升级会员（upgrade_window.py）

三档会员方案展示 + 支付流程（当前为模拟支付）。设计方案卡片的布局参考了 App Store 的订阅页面。会员等级：trial（体验）/ vip（VIP）/ permanent（永久）。

### 翻车：登录后直接跳舰桥，跳过了引擎舱

`login_window.py` 的 `_open_dashboard` 最初直接创建了 `DashboardWindow`。`connect_window.py` 虽然早就写好了（模型选择、API Key 配置、点火测试），但从未被调用。

修复只改了一行：`_open_dashboard` → 改为打开 `ConnectWindow`。引擎舱成了必经之路。

---
