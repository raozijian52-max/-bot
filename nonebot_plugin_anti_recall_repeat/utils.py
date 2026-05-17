from nonebot import get_driver, logger
from nonebot.adapters.onebot.v11 import Bot, GroupMessageEvent

from .config import plugin_config


# 判断插件总开关是否启用。
def is_plugin_enabled() -> bool:
    return plugin_config.anti_recall_repeat_enabled


# 判断当前群是否在启用范围内，空配置表示所有群启用。
def is_group_enabled(group_id: int) -> bool:
    enabled_groups = plugin_config.anti_recall_repeat_enabled_groups
    return not enabled_groups or group_id in enabled_groups


# 判断用户是否是超级用户或白名单用户。
def is_superuser_or_whitelist(user_id: int) -> bool:
    superusers = {str(user) for user in get_driver().config.superusers}
    return str(user_id) in superusers or user_id in plugin_config.anti_recall_repeat_whitelist_users


# 判断群消息发送者是否需要跳过处理。
def should_skip_group_message(event: GroupMessageEvent) -> bool:
    if not is_plugin_enabled():
        return True
    if not is_group_enabled(event.group_id):
        return True
    if is_superuser_or_whitelist(event.user_id):
        return True
    return event.sender.role in {"admin", "owner"}


# 查询群成员是否是管理员或群主，失败时不阻断后续流程。
async def is_group_admin_or_owner(bot: Bot, group_id: int, user_id: int) -> bool:
    try:
        member = await bot.get_group_member_info(
            group_id=group_id,
            user_id=user_id,
            no_cache=True,
        )
    except Exception as exc:
        logger.debug("查询群成员身份失败: group_id={}, user_id={}, error={}", group_id, user_id, exc)
        return False

    return member.get("role") in {"admin", "owner"}
