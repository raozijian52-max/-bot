from nonebot.plugin import PluginMetadata

from .config import Config

__plugin_meta__ = PluginMetadata(
    name="防撤回与防复读",
    description="基于 OneBot v11 的 QQ 群管插件，提供防撤回缓存和简单防复读提醒。",
    usage="安装插件后在 NoneBot2 中加载；通过 .env 配置启用群、白名单和提醒文案。",
    type="application",
    config=Config,
    supported_adapters={"~onebot.v11"},
)

from . import anti_recall as anti_recall
from . import anti_repeat as anti_repeat
from . import ai_chat as ai_chat
