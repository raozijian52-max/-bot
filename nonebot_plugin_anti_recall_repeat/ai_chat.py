from typing import Optional

import httpx
from nonebot import logger, on_message
from nonebot.adapters import Event
from nonebot.adapters.onebot.v11 import Bot, GroupMessageEvent
from nonebot.rule import Rule

from .config import plugin_config
from .utils import is_group_enabled

SYSTEM_PROMPT = "你是一个 QQ 群里的 AI 助手。回答要简洁、友好、不要太长。"


# 判断 AI 聊天功能是否启用。
def is_ai_enabled() -> bool:
    return plugin_config.anti_recall_repeat_ai_enabled


# 从原始消息中提取 /ai 后面的提问内容。
def extract_question(raw_message: str) -> Optional[str]:
    trigger = plugin_config.anti_recall_repeat_ai_trigger
    if not trigger:
        return None
    if not raw_message.startswith(trigger):
        return None

    question = raw_message[len(trigger):].strip()
    return question or None


# 判断事件是否是需要处理的群 AI 命令。
async def is_ai_group_message(event: Event) -> bool:
    if not isinstance(event, GroupMessageEvent):
        return False
    if not is_ai_enabled():
        return False
    if not is_group_enabled(event.group_id):
        return False
    return extract_question(event.raw_message) is not None or event.raw_message.startswith(
        plugin_config.anti_recall_repeat_ai_trigger
    )


# 调用 OpenAI-compatible Chat Completions API 获取回答。
async def call_ai(question: str) -> str:
    api_key = plugin_config.anti_recall_repeat_ai_api_key.strip()
    if not api_key:
        return "AI API Key 还没有配置。"

    api_base = plugin_config.anti_recall_repeat_ai_api_base.rstrip("/")
    url = f"{api_base}/chat/completions"
    payload = {
        "model": plugin_config.anti_recall_repeat_ai_model,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": question},
        ],
        "max_tokens": plugin_config.anti_recall_repeat_ai_max_tokens,
    }
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    try:
        async with httpx.AsyncClient(timeout=plugin_config.anti_recall_repeat_ai_timeout) as client:
            response = await client.post(url, headers=headers, json=payload)
            response.raise_for_status()
            data = response.json()

        answer = data["choices"][0]["message"]["content"].strip()
        return answer or "AI 没有返回内容。"
    except Exception:
        logger.exception("AI 接口调用失败")
        return "AI 接口调用失败了，可以看一下后台日志。"


ai_chat_matcher = on_message(rule=Rule(is_ai_group_message), priority=5, block=False)


@ai_chat_matcher.handle()
async def handle_ai_chat(bot: Bot, event: GroupMessageEvent) -> None:
    """处理群里的 /ai 命令，调用大模型并发送回答。"""
    question = extract_question(event.raw_message)
    if question is None:
        await bot.send_group_msg(group_id=event.group_id, message="请在 /ai 后面输入问题。")
        return

    if plugin_config.anti_recall_repeat_ai_api_key.strip():
        await bot.send_group_msg(group_id=event.group_id, message="正在思考中……")

    answer = await call_ai(question)
    await bot.send_group_msg(group_id=event.group_id, message=answer)
