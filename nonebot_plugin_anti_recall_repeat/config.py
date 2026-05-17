from pydantic import BaseModel, Field
from nonebot import get_plugin_config


class Config(BaseModel):
    """插件配置，字段会从 NoneBot 配置或 .env 中读取。"""

    anti_recall_repeat_enabled: bool = Field(default=True)
    anti_recall_repeat_enabled_groups: set[int] = Field(default_factory=set)
    anti_recall_repeat_whitelist_users: set[int] = Field(default_factory=set)
    anti_recall_repeat_cache_size: int = Field(default=500)
    anti_recall_repeat_ban_min_seconds: int = Field(default=60)
    anti_recall_repeat_ban_max_seconds: int = Field(default=600)
    anti_recall_repeat_recall_tip: str = Field(
        default="检测到撤回，已禁言 {user_id} {duration} 秒。撤回内容：{message}"
    )
    anti_recall_repeat_repeat_tip: str = Field(
        default="检测到复读，已禁言 {user_id} {duration} 秒。"
    )


plugin_config = get_plugin_config(Config)
