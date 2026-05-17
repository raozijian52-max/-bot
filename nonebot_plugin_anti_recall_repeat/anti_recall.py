from collections import OrderedDict
from typing import Any, Optional

from nonebot import logger, on_message, on_notice
from nonebot.adapters import Event
from nonebot.adapters.onebot.v11 import Bot, GroupMessageEvent, GroupRecallNoticeEvent
from nonebot.rule import Rule

from .config import plugin_config
from .utils import (
    is_group_admin_or_owner,
    is_group_enabled,
    is_plugin_enabled,
    is_superuser_or_whitelist,
    should_skip_group_message,
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


group_message_matcher = on_message(rule=Rule(is_group_message), priority=10, block=False)
group_recall_matcher = on_notice(rule=Rule(is_group_recall), priority=10, block=False)


@group_message_matcher.handle()
async def handle_group_message(event: GroupMessageEvent) -> None:
    """处理群消息事件，当前只负责写入撤回缓存。"""
    if should_skip_group_message(event):
        return

    cache_group_message(event)


@group_recall_matcher.handle()
async def handle_group_recall(bot: Bot, event: GroupRecallNoticeEvent) -> None:
    """处理群撤回事件，当前只尝试读取缓存并记录日志。"""
    if not is_plugin_enabled():
        return
    if not is_group_enabled(event.group_id):
        return
    if is_superuser_or_whitelist(event.user_id) or is_superuser_or_whitelist(event.operator_id):
        return
    if await is_group_admin_or_owner(bot, event.group_id, event.operator_id):
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
