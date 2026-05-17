from typing import Optional

from nonebot import on_message
from nonebot.adapters import Event
from nonebot.adapters.onebot.v11 import GroupMessageEvent
from nonebot.rule import Rule

from .config import plugin_config
from .utils import should_skip_group_message

last_text_by_group: dict[int, tuple[int, str]] = {}


# 判断事件是否是群消息事件。
async def is_group_message(event: Event) -> bool:
    return isinstance(event, GroupMessageEvent)


# 提取纯文本消息；如果包含图片、表情等非文本段，则返回 None。
def extract_pure_text(event: GroupMessageEvent) -> Optional[str]:
    message = event.get_message()
    if not message:
        return None
    if any(segment.type != "text" for segment in message):
        return None

    text = message.extract_plain_text()
    if not text.strip():
        return None
    return text


# 记录当前群最后一条纯文本消息。
def remember_last_text(event: GroupMessageEvent, text: str) -> None:
    last_text_by_group[event.group_id] = (event.user_id, text)


# 清理当前群的上一条文本记录，用于打断连续复读判断。
def clear_last_text(group_id: int) -> None:
    last_text_by_group.pop(group_id, None)


repeat_matcher = on_message(rule=Rule(is_group_message), priority=20, block=False)


@repeat_matcher.handle()
async def handle_repeat(event: GroupMessageEvent) -> None:
    """处理群消息事件，连续两条纯文本完全相同时发送提醒。"""
    if should_skip_group_message(event):
        clear_last_text(event.group_id)
        return

    text = extract_pure_text(event)
    if text is None:
        clear_last_text(event.group_id)
        return

    last_text = last_text_by_group.get(event.group_id)
    remember_last_text(event, text)

    if last_text is not None and last_text[1] == text:
        await repeat_matcher.send(plugin_config.anti_recall_repeat_repeat_tip)
