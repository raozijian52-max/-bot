# nonebot_plugin_anti_recall_repeat

一个基于 NoneBot2 + OneBot v11 的 QQ 群管插件最小版本，当前提供：

- 防撤回：监听群消息和群撤回事件，缓存群消息；撤回时随机禁言并复述撤回内容，超级用户除外。
- 防复读：连续两条纯文本完全相同时，随机禁言并发送提醒。
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

OneBot v11 端需要连接到 NoneBot2 暴露的反向 WebSocket 地址：

```text
ws://127.0.0.1:8080/onebot/v11/ws
```

## 配置项

```dotenv
SUPERUSERS=["123456789"]

ANTI_RECALL_REPEAT_ENABLED=true
ANTI_RECALL_REPEAT_ENABLED_GROUPS=[]
ANTI_RECALL_REPEAT_WHITELIST_USERS=[]
ANTI_RECALL_REPEAT_CACHE_SIZE=500
ANTI_RECALL_REPEAT_BAN_MIN_SECONDS=60
ANTI_RECALL_REPEAT_BAN_MAX_SECONDS=600
ANTI_RECALL_REPEAT_RECALL_TIP="检测到撤回，已禁言 {user_id} {duration} 秒。撤回内容：{message}"
ANTI_RECALL_REPEAT_REPEAT_TIP="检测到复读，已禁言 {user_id} {duration} 秒。"
```

说明：

- `ANTI_RECALL_REPEAT_ENABLED`：插件总开关。
- `ANTI_RECALL_REPEAT_ENABLED_GROUPS`：启用群列表，空列表表示所有群启用。
- `ANTI_RECALL_REPEAT_WHITELIST_USERS`：白名单 QQ 用户列表。
- `ANTI_RECALL_REPEAT_CACHE_SIZE`：防撤回消息缓存条数。
- `ANTI_RECALL_REPEAT_BAN_MIN_SECONDS`：随机禁言最短秒数，默认 `60`。
- `ANTI_RECALL_REPEAT_BAN_MAX_SECONDS`：随机禁言最长秒数，默认 `600`。
- `ANTI_RECALL_REPEAT_RECALL_TIP`：复述撤回内容的提示模板，可使用 `{group_id}`、`{user_id}`、`{operator_id}`、`{duration}`、`{message}`、`{raw_message}`。
- `ANTI_RECALL_REPEAT_REPEAT_TIP`：检测到连续复读时发送的提醒，可使用 `{group_id}`、`{user_id}`、`{duration}`。

## 当前行为

### 防撤回

插件会缓存群消息。收到群撤回事件时，如果命中缓存，会先随机禁言撤回消息的用户 1 到 10 分钟，然后在群里发送提示并复述撤回内容。

如果机器人不是群管理员，禁言会失败，但仍会复述撤回内容。

撤回逻辑不会因为管理员、群主或白名单身份跳过复述；只有超级用户撤回或操作撤回时会跳过。

### 防复读

插件只处理纯文本消息。如果同一个群里连续两条纯文本内容完全相同，会随机禁言当前复读用户 1 到 10 分钟，并发送一次提醒。
