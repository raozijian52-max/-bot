from collections import OrderedDict
from typing import Any, Optional

from nonebot import logger, on_message, on_notice
from nonebot.adapters import Event
from nonebot.adapters.onebot.v11 import Bot, GroupMessageEvent, GroupRecallNoticeEvent
from nonebot.rule import Rule

from .config import plugin_config
from .utils import (
    get_random_ban_duration,
    is_group_enabled,
    is_plugin_enabled,
    is_superuser,
)

message_cache: OrderedDict[int, dict[str, Any]] = OrderedDict()


# 判断事件是否是群消息事件。
async def is_group_message(event: Event) -> bool:
    return isinstance(event, GroupMessageEvent)


# 判断事件是否是群撤回通知事件。
async def is_group_recall(event: Event) -> bool:
    return isinstance(event, GroupRecallNoticeEvent)


# 缓存群消息，超过配置上限时淘汰最早的一条。
def cache_group_message(event: GroupMessageEvent) -> None:
    cache_size = plugin_config.anti_recall_repeat_cache_size
    if cache_size <= 0:
        return

    message_cache[event.message_id] = {
        "group_id": event.group_id,
        "user_id": event.user_id,
        "message": event.get_message(),
        "raw_message": event.raw_message,
        "time": event.time,
    }
    message_cache.move_to_end(event.message_id)

    while len(message_cache) > cache_size:
        message_cache.popitem(last=False)

    logger.debug("已缓存群消息: group_id={}, message_id={}", event.group_id, event.message_id)


# 根据消息 ID 从缓存中读取消息。
def get_cached_message(message_id: int) -> Optional[dict[str, Any]]:
    return message_cache.get(message_id)


# 禁言撤回消息的用户，机器人没有管理员权限时只记录失败日志。
async def ban_recall_user(bot: Bot, group_id: int, user_id: int, duration: int) -> None:
    if duration <= 0:
        return

    try:
        await bot.set_group_ban(group_id=group_id, user_id=user_id, duration=duration)
    except Exception as exc:
        logger.warning(
            "禁言撤回用户失败: group_id={}, user_id={}, duration={}, error={}",
            group_id,
            user_id,
            duration,
            exc,
        )


# 生成复述撤回内容的群消息。
def build_recall_tip(
    event: GroupRecallNoticeEvent,
    cached_message: dict[str, Any],
    duration: int,
) -> str:
    return plugin_config.anti_recall_repeat_recall_tip.format(
        group_id=event.group_id,
        user_id=event.user_id,
        operator_id=event.operator_id,
        duration=duration,
        message=cached_message["message"],
        raw_message=cached_message["raw_message"],
    )


group_message_matcher = on_message(rule=Rule(is_group_message), priority=10, block=False)
group_recall_matcher = on_notice(rule=Rule(is_group_recall), priority=10, block=False)


@group_message_matcher.handle()
async def handle_group_message(event: GroupMessageEvent) -> None:
    """处理群消息事件，当前只负责写入撤回缓存。"""
    if not is_plugin_enabled():
        return
    if not is_group_enabled(event.group_id):
        return
    if str(event.user_id) == str(event.self_id):
        return
    if is_superuser(event.user_id):
        return

    cache_group_message(event)


@group_recall_matcher.handle()
async def handle_group_recall(bot: Bot, event: GroupRecallNoticeEvent) -> None:
    """处理群撤回事件，命中缓存后禁言并复述撤回内容。"""
    if not is_plugin_enabled():
        return
    if not is_group_enabled(event.group_id):
        return
    if str(event.user_id) == str(bot.self_id) or str(event.operator_id) == str(bot.self_id):
        return
    if is_superuser(event.user_id) or is_superuser(event.operator_id):
        return

    cached_message = get_cached_message(event.message_id)
    if cached_message is None:
        logger.info(
            "收到群撤回事件，但未命中缓存: group_id={}, message_id={}",
            event.group_id,
            event.message_id,
        )
        return

    logger.info(
        "收到群撤回事件，已命中缓存: group_id={}, user_id={}, operator_id={}, message={}",
        event.group_id,
        event.user_id,
        event.operator_id,
        cached_message["message"],
    )

    duration = get_random_ban_duration()
    await ban_recall_user(bot, event.group_id, event.user_id, duration)
    await bot.send_group_msg(
        group_id=event.group_id,
        message=build_recall_tip(event, cached_message, duration),
    )
