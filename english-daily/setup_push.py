"""推送渠道一键配置向导。

用法：

    python setup_push.py

按提示选一个渠道、把密钥粘进去，脚本会自动写进 config.ini 并立刻发一条测试消息。
全部渠道都是免费的，区别只是消息出现在哪、每天能发多少条。
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

from daily_english.config import CONFIG_PATH
from daily_english.push import PushError, send

ROOT = Path(__file__).resolve().parent

CHANNELS = {
    "1": {
        "name": "serverchan",
        "title": "Server酱（推荐 · 消息进微信「服务通知」）",
        "quota": "免费版每天 5 条，每天推 1 条完全够",
        "steps": [
            "手机微信扫一扫，登录 https://sct.ftqq.com/",
            "登录后点开「SendKey」页面",
            "复制那串 SendKey（SCT... 或 sctp... 开头）",
        ],
        "prompt": "粘贴 SendKey（SCT... 或 sctp... 开头）：",
        "hint": "SCT",
    },
    "2": {
        "name": "wxpusher",
        "title": "WxPusher（消息进微信，像公众号消息一样）",
        "quota": "免费额度很宽裕，个人用基本发不完",
        "steps": [
            "微信扫码登录 https://wxpusher.zjiecode.com/",
            "进入「应用管理」→ 新建应用，复制 appToken（AT_ 开头）",
            "在应用详情里扫码关注，拿到你的 UID（UID_ 开头）",
        ],
        "prompt": "先粘 appToken（AT_ 开头）：",
        "hint": "AT_",
        "extra": ("UID", "再粘你的 UID（UID_ 开头）：", "UID_"),
    },
    "3": {
        "name": "pushplus",
        "title": "pushplus（消息进微信，公众号形式）",
        "quota": "免费版每天 200 条",
        "steps": [
            "微信扫码登录 https://www.pushplus.plus/",
            "点「一对一推送」，复制页面上的 token",
        ],
        "prompt": "粘贴 token：",
        "hint": "",
    },
    "4": {
        "name": "wecom",
        "title": "企业微信群机器人（消息进企业微信的群聊，最像聊天）",
        "quota": "免费且不限量（每分钟最多 20 条）",
        "steps": [
            "手机装「企业微信」，注册一个企业（个人也能注册，免费，不用认证）",
            "随便建一个群，只有自己也可以",
            "群设置 → 群机器人 → 添加 → 复制 Webhook 地址",
        ],
        "prompt": "粘贴 Webhook 地址（https://qyapi.weixin.qq.com/...）：",
        "hint": "https://qyapi.weixin.qq.com",
    },
}


def update_ini(section: str, key: str, value: str) -> None:
    """只改目标行，保留 config.ini 里的注释。"""
    text = CONFIG_PATH.read_text(encoding="utf-8-sig") if CONFIG_PATH.exists() else ""
    lines = text.splitlines()
    if not lines:
        lines = []

    current = ""
    section_start = None
    hit = False
    out: list[str] = []
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("[") and stripped.endswith("]"):
            current = stripped[1:-1].strip()
            if current == section:
                section_start = len(out) + 1
        if current == section and re.match(rf"^\s*{re.escape(key)}\s*=", line):
            out.append(f"{key} = {value}")
            hit = True
            continue
        out.append(line)

    if not hit:
        if section_start is None:
            if out and out[-1].strip():
                out.append("")
            out.append(f"[{section}]")
            out.append(f"{key} = {value}")
        else:
            out.insert(section_start, f"{key} = {value}")

    CONFIG_PATH.write_text("\n".join(out).rstrip() + "\n", encoding="utf-8")


def configure(channel: str, values: dict[str, str]) -> None:
    update_ini("app", "channel", channel)
    for key, value in values.items():
        section = "serverchan" if channel == "serverchan" else channel
        update_ini(section, key, value)


def test_send(channel: str, values: dict[str, str]) -> bool:
    from daily_english.config import Config

    cfg = Config(CONFIG_PATH)
    title = "每日一句 · 推送测试"
    body = (
        "## 推送测试成功 🎉\n\n"
        "如果你在微信里看到这条消息，说明渠道已经打通。\n\n"
        "以后每天运行 `python run.py` 就会收到一句英语。"
    )
    html = "<h2>推送测试成功</h2><p>渠道已打通。</p>"
    try:
        used = send(cfg, title, body, html)
    except PushError as exc:
        print(f"\n[×] 测试失败：{exc}")
        return False
    print(f"\n[✓] 测试消息已通过 {used} 发出，去手机上看一眼。")
    return True


def main() -> int:
    parser = argparse.ArgumentParser(description="配置微信推送渠道")
    parser.add_argument("--channel", choices=["serverchan", "wxpusher", "pushplus", "wecom"])
    parser.add_argument("--key", help="serverchan 的 SendKey / pushplus 的 token / wecom 的 webhook")
    parser.add_argument("--uid", help="WxPusher 的 UID")
    args = parser.parse_args()

    print("=" * 62)
    print(" 英语每日一句 · 推送渠道配置")
    print("=" * 62)
    print(" 只有第 4 项（企业微信）需要你去注册企业，其余扫码就行，全部免费。\n")
    for num, info in CHANNELS.items():
        print(f" {num}. {info['title']}")
        print(f"    额度：{info['quota']}")
    print(" 5. 先不配（只在本地生成网页和音频）\n")

    if args.channel:
        choice = next(k for k, v in CHANNELS.items() if v["name"] == args.channel)
    else:
        choice = input(" 请输入序号 [1-5]（直接回车 = 1 Server酱）：").strip() or "1"

    if choice == "5":
        print("\n好的，只生成本地文件。想开推送时再运行一次本脚本。")
        return 0
    if choice not in CHANNELS:
        print("序号不对，退出。")
        return 1

    info = CHANNELS[choice]
    name = info["name"]

    print(f"\n--- {info['title']} ---")
    for i, step in enumerate(info["steps"], 1):
        print(f"  {i}. {step}")

    if args.key:
        first = args.key.strip()
    else:
        first = input(f"\n {info['prompt']}").strip()

    if not first:
        print("没有输入，退出。")
        return 1
    if info["hint"] and not first.startswith(info["hint"]):
        print(f" [!] 看起来不像 {info['hint']} 开头，先按你输入的试一下。")

    values: dict[str, str] = {}
    if name == "serverchan":
        if first.startswith("http"):
            values["url"] = first
            # 同时也把 sendkey 清掉，避免两处冲突
            values["sendkey"] = ""
        else:
            values["sendkey"] = first
            values["url"] = ""
    elif name == "pushplus":
        values["token"] = first
    elif name == "wecom":
        values["webhook"] = first
    elif name == "wxpusher":
        uid = args.uid.strip() if args.uid else input(f" {info['extra'][1]}").strip()
        if not uid:
            print("没有输入 UID，退出。")
            return 1
        values["apptoken"] = first
        values["uid"] = uid

    configure(name, values)
    print(f"\n 已写入 {CONFIG_PATH.name}：channel = {name}")

    ok = test_send(name, values)
    if ok:
        print("\n 下一步：")
        print("   python run.py --open     # 立刻生成今天这一句并打开预览")
        print("   想每天自动推，见 README「四、每天自动跑」。")
    else:
        print("\n 密钥可能有误，或该渠道需要先关注/建群。按上面提示再检查一次。")
    return 0 if ok else 1


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n已取消。")
        sys.exit(130)
