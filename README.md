# nonebot_plugin_anti_recall_repeat

一个基于 NoneBot2 + OneBot v11 的 QQ 群管插件最小版本，当前只保留基础框架和简单逻辑：

- 防撤回：监听群消息和群撤回事件，先缓存群消息，不主动复读撤回内容。
- 防复读：连续两条纯文本完全相同时发送提醒，不禁言。
- 管理员、群主、超级用户、白名单用户会跳过处理。
- 不写死群号和 QQ 号，全部通过 `.env` / NoneBot 配置管理。

## 项目结构

```text
.
├── bot.py
├── pyproject.toml
├── README.md
├── .env.example
└── nonebot_plugin_anti_recall_repeat
    ├── __init__.py
    ├── config.py
    ├── utils.py
    ├── anti_recall.py
    └── anti_repeat.py
```

## 安装依赖

```bash
pip install -e .
```

## 最小启动

复制 `.env.example` 为 `.env`，按需修改配置，然后运行：

```bash
python bot.py
```

OneBot v11 端需要连接到 NoneBot2 暴露的驱动地址，具体连接方式取决于你使用的 OneBot 实现。

## 配置项

```dotenv
SUPERUSERS=["123456789"]

ANTI_RECALL_REPEAT_ENABLED=true
ANTI_RECALL_REPEAT_ENABLED_GROUPS=[]
ANTI_RECALL_REPEAT_WHITELIST_USERS=[]
ANTI_RECALL_REPEAT_CACHE_SIZE=500
ANTI_RECALL_REPEAT_REPEAT_TIP="检测到复读啦，先打断一下～"
```

说明：

- `ANTI_RECALL_REPEAT_ENABLED`：插件总开关。
- `ANTI_RECALL_REPEAT_ENABLED_GROUPS`：启用群列表，空列表表示所有群启用。
- `ANTI_RECALL_REPEAT_WHITELIST_USERS`：白名单 QQ 用户列表。
- `ANTI_RECALL_REPEAT_CACHE_SIZE`：防撤回消息缓存条数。
- `ANTI_RECALL_REPEAT_REPEAT_TIP`：检测到连续复读时发送的提醒。

## 当前行为

### 防撤回

插件会缓存普通群成员发送的群消息。收到群撤回事件时，如果命中缓存，只记录日志，后续可以在 `anti_recall.py` 中扩展为通知管理员、复读撤回内容或写入数据库。

### 防复读

插件只处理纯文本消息。如果同一个群里连续两条纯文本内容完全相同，会发送一次提醒。当前不会禁言，也不会执行更复杂的处罚逻辑。
