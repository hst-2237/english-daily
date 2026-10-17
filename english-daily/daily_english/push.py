"""推送渠道：微信生态里最省事的几种方式。

- console    : 不推送，只在终端打印（默认，先跑通再开推送）
- serverchan : Server酱³，消息会以「服务通知」出现在个人微信里
- pushplus   : pushplus，同样是微信服务号通知
- wecom      : 企业微信群机器人，消息出现在企业微信群（需先建群加机器人）
"""

from __future__ import annotations

import json
import urllib.error
import urllib.request

from .config import Config

WECOM_LIMIT = 4000  # 企业微信 markdown 最多 4096 字节，留点余量


class PushError(RuntimeError):
    pass


def _post_json(url: str, payload: dict, timeout: int = 15) -> dict:
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=body,
        headers={"Content-Type": "application/json; charset=utf-8"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as exc:
        detail = exc.read()[:300].decode("utf-8", errors="replace")
        raise PushError(f"接口返回 HTTP {exc.code}：{detail or exc.reason}") from exc
    except urllib.error.URLError as exc:
        raise PushError(f"连不上推送服务（{exc.reason}）——检查网络，或密钥/地址是否写对") from exc
    except TimeoutError as exc:
        raise PushError("请求推送服务超时——网络不稳，或地址/密钥不对") from exc
    except Exception as exc:
        raise PushError(f"请求失败：{exc}") from exc
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return {"raw": raw}


def serverchan(url: str, title: str, desp: str) -> dict:
    if not url:
        raise PushError(
            "没有配置 Server酱：请在 config.ini 的 [serverchan] 里填写 sendkey"
            "（SendKey 页面复制，形如 sctp12345tXXXX），或直接填完整推送地址 url"
        )
    result = _post_json(url, {"title": title, "desp": desp})
    if result.get("code") not in (0, None):
        raise PushError(f"Server酱返回异常：{result}")
    return result


def pushplus(token: str, title: str, content_html: str) -> dict:
    if not token:
        raise PushError("config.ini 里没有填写 [pushplus] token")
    result = _post_json(
        "https://www.pushplus.plus/send",
        {"token": token, "title": title, "content": content_html, "template": "html"},
    )
    if result.get("code") not in (200, None):
        raise PushError(f"pushplus 返回异常：{result}")
    return result


def wecom(webhook: str, content_markdown: str) -> dict:
    if not webhook:
        raise PushError("config.ini 里没有填写 [wecom] webhook")
    content = content_markdown
    while len(content.encode("utf-8")) > WECOM_LIMIT:
        content = content[:-20]
    result = _post_json(webhook, {"msgtype": "markdown", "markdown": {"content": content}})
    if result.get("errcode") not in (0, None):
        raise PushError(f"企业微信返回异常：{result}")
    return result


def wxpusher(app_token: str, uids: str, content_markdown: str, title: str) -> dict:
    """WxPusher：消息以公众号消息的形式出现在微信里，免费。"""
    if not app_token or not uids:
        raise PushError("没有配置 WxPusher：请在 config.ini 的 [wxpusher] 里填写 apptoken 和 uid")
    result = _post_json(
        "https://wxpusher.zjiecode.com/api/send/message",
        {
            "appToken": app_token,
            "content": content_markdown,
            "summary": title[:100],
            "contentType": 3,  # 3 = markdown
            "uids": [u.strip() for u in uids.split(",") if u.strip()],
        },
    )
    if not result.get("success"):
        raise PushError(f"WxPusher 返回异常：{result}")
    return result


def send(cfg: Config, title: str, markdown_text: str, html_text: str) -> str:
    """按配置推送，返回实际使用的渠道名。"""
    channel = cfg.channel
    if channel == "serverchan":
        serverchan(cfg.serverchan_url, title, markdown_text)
    elif channel == "pushplus":
        pushplus(cfg.pushplus_token, title, html_text)
    elif channel == "wxpusher":
        wxpusher(cfg.wxpusher_token, cfg.wxpusher_uid, markdown_text, title)
    elif channel == "wecom":
        wecom(cfg.wecom_webhook, markdown_text)
    elif channel == "console":
        return "console"
    else:
        raise PushError(
            f"未知的推送渠道：{channel}（可选 console / serverchan / pushplus / wxpusher / wecom）"
        )
    return channel
