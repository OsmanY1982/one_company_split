# `core/modules/personnel/distribution_window/_dashboard.py`

> 路径：`core/modules/personnel/distribution_window/_dashboard.py` | 行数：21


---


```python
"""
_DashboardMixin — 统计面板数据加载
"""
from core.modules.personnel.distribution_service import get_distribution_stats


class _DashboardMixin:
    """统计与全量加载 Mixin"""

    def _load_all(self):
        self._load_links()
        self._search_commissions()
        self._load_team()

    def _update_stats(self):
        s = get_distribution_stats()
        self.stats_label.setText(
            f"链接: {s['links']} | 总点击: {s['clicks']} | "
            f"佣金: {s['commissions_count']}笔 ¥{s['commissions_amount']:.2f} | "
            f"团队: {s['team_size']}人"
        )

```
