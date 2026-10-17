"""配置读取：本地用 config.ini，云端用环境变量覆盖。

不依赖 PyYAML / pydantic，只用标准库，方便在 PyCharm 里直接运行。
GitHub Actions 里没有 config.ini（也不该把密钥写进仓库），
密钥通过仓库的 Secrets 注入成环境变量，这里自动优先采用。
"""

from __future__ import annotations

import configparser
import os
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CONFIG_PATH = ROOT / "config.ini"

# 环境变量优先级高于 config.ini，用于 GitHub Actions 等无配置文件的环境
ENV_MAP = {
    ("app", "channel"): "ENGLISH_DAILY_CHANNEL",
    ("serverchan", "sendkey"): "SERVERCHAN_SENDKEY",
    ("pushplus", "token"): "PUSHPLUS_TOKEN",
    ("wxpusher", "apptoken"): "WXPUSHER_TOKEN",
    ("wxpusher", "uid"): "WXPUSHER_UID",
    ("wecom", "webhook"): "WECOM_WEBHOOK",
}

DEFAULT_INI = """\
# 英语每日一句 —— 配置文件
# 改完保存即可，不需要重启任何服务。

[app]
# 推送渠道，可选：console（只在终端/本地显示）、serverchan、pushplus、wecom
channel = console
# 本地输出目录（每天一个子文件夹，含 html 和 mp3）
output_dir = output
# 每天推送时间，仅写在页面上做提示，真正的定时由 Windows 计划任务负责
push_time = 07:30

[audio]
# edge = 用 edge-tts 生成英音 mp3（推荐，需要 pip install edge-tts）
# none = 不生成文件，只在推送里给一个在线英音播放链接
engine = edge
# 英音发音人：男声 en-GB-RyanNeural，女声 en-GB-SoniaNeural
voice = en-GB-RyanNeural
# 慢速版语速（跟读用），-25% 表示比正常慢四分之一
slow_rate = -25%
# 常速版语速
normal_rate = +0%

[serverchan]
# 方式一（推荐）：只填 SendKey，形如 sctp12345tXXXXXXXXXXXXXXXXXX
sendkey =
# 方式二：直接填 SendKey 页面复制来的完整推送地址
url =

[pushplus]
# pushplus 的 token
token =

[wxpusher]
# WxPusher：appToken（AT_ 开头）和你的 UID（UID_ 开头）
apptoken =
uid =

[wecom]
# 企业微信群机器人的 webhook 地址
webhook =

[study]
# 是否把朗读要点一起推送
tips = true
"""


class Config:
    def __init__(self, path: Path | None = None) -> None:
        self.path = Path(path) if path else CONFIG_PATH
        if not self.path.exists():
            self.path.write_text(DEFAULT_INI, encoding="utf-8")
        self._cp = configparser.ConfigParser(interpolation=None)
        # utf-8-sig：用记事本另存过也带着 BOM 的文件同样能读
        self._cp.read(self.path, encoding="utf-8-sig")

    def get(self, section: str, key: str, fallback: str = "") -> str:
        env_name = ENV_MAP.get((section, key))
        if env_name:
            value = os.environ.get(env_name, "").strip()
            if value:
                return value
        return self._cp.get(section, key, fallback=fallback).strip()

    # ---- 常用项，写成语义化属性，避免到处写字符串 ----
    @property
    def channel(self) -> str:
        return self.get("app", "channel", "console").lower()

    @property
    def output_dir(self) -> Path:
        raw = Path(self.get("app", "output_dir", "output"))
        return raw if raw.is_absolute() else ROOT / raw

    @property
    def push_time(self) -> str:
        return self.get("app", "push_time", "07:30")

    @property
    def audio_engine(self) -> str:
        return self.get("audio", "engine", "edge").lower()

    @property
    def voice(self) -> str:
        return self.get("audio", "voice", "en-GB-RyanNeural")

    @property
    def slow_rate(self) -> str:
        return self.get("audio", "slow_rate", "-25%")

    @property
    def normal_rate(self) -> str:
        return self.get("audio", "normal_rate", "+0%")

    @property
    def serverchan_url(self) -> str:
        """优先用完整地址；只填了 SendKey 时按发送渠道的规则拼出来。

        Server酱有两代产品，SendKey 长得不一样，这里都认：
        - Server酱 Turbo：SCT{uid}T...   → https://sctapi.ftqq.com/{key}.send
        - Server酱³    ：sctp{uid}t...  → https://sctp{uid}t.push.ft07.com/send/{key}.send
        """
        url = self.get("serverchan", "url")
        if url:
            return url
        key = self.get("serverchan", "sendkey")
        if not key:
            return ""
        if key.startswith("http"):
            return key
        if re.match(r"^SCT\d+T", key):
            return f"https://sctapi.ftqq.com/{key}.send"
        match = re.match(r"^(sctp\d+t)", key)
        if not match:
            return ""
        return f"https://{match.group(1)}.push.ft07.com/send/{key}.send"

    @property
    def pushplus_token(self) -> str:
        return self.get("pushplus", "token")

    @property
    def wxpusher_token(self) -> str:
        return self.get("wxpusher", "apptoken")

    @property
    def wxpusher_uid(self) -> str:
        return self.get("wxpusher", "uid")

    @property
    def wecom_webhook(self) -> str:
        return self.get("wecom", "webhook")

    @property
    def show_tips(self) -> bool:
        return self.get("study", "tips", "true").lower() in {"1", "true", "yes", "on"}
