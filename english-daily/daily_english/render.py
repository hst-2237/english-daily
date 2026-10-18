"""把一句话渲染成微信可读的 Markdown / HTML，以及本地可打开的网页。"""

from __future__ import annotations

import html
from datetime import date
from pathlib import Path

from .corpus import Sentence, Tip

TYPE_COLOR = {
    "连读": "#2f80ed",
    "失爆": "#eb5757",
    "同化": "#9b51e0",
    "弱读": "#f2994a",
    "省音": "#219653",
    "语调": "#2d9cdb",
    "重音": "#b45309",
    "节奏": "#4b5563",
}


def _tip_badge(tip_type: str) -> str:
    color = TYPE_COLOR.get(tip_type, "#6b7280")
    return f'<span class="badge" style="background:{color}1a;color:{color}">{html.escape(tip_type)}</span>'


def markdown(sentence: Sentence, ipa: str, tips: list[Tip], audio_lines: list[str], day: str) -> str:
    """推送给 Server酱 的正文（markdown）。

    实测结论，改之前先看一眼：
    1. Server酱 的消息详情页会完整渲染 markdown——标题、加粗、列表、链接都生效；
    2. 微信「服务通知」的卡片只显示标题，正文不进卡片，所以正文可以放心用 markdown；
    3. 标题里绝对不能出现英文撇号 '，否则微信回 data format error，整条消息丢失。
    """
    lines: list[str] = []
    lines += [f"**{sentence.text}**", sentence.zh, ""]
    if ipa:
        lines += [f"`{ipa}`", ""]
    if tips:
        lines.append("**朗读要点**")
        lines += [f"- {t.type}：{t.text}" for t in tips]
        lines.append("")
    for line in audio_lines:
        text = line.lstrip("- ").strip()
        label, _, url = text.partition("：")
        if url.startswith("http"):
            lines.append(f"[{label}]({url})")
        else:
            lines.append(text)
    return "\n".join(lines).strip()


def html_snippet(sentence: Sentence, ipa: str, tips: list[Tip], online_url: str, day: str) -> str:
    """给 pushplus 这类 HTML 模板用的轻量片段（不是完整网页）。"""
    e = html.escape
    tip_html = "".join(
        f'<li style="margin:6px 0"><b>【{e(t.type)}】</b>{e(t.text)}</li>' for t in tips
    )
    return (
        f"<h2>每日一句 · {e(day)}</h2>"
        f"<p style=\"font-size:17px;line-height:1.6\"><b>{e(sentence.text)}</b><br>"
        f"<span style=\"color:#666\">{e(sentence.zh)}</span></p>"
        + (f'<p style="font-family:serif;font-size:16px">{e(ipa)}</p>' if ipa else "")
        + (f"<ul style=\"padding-left:18px\">{tip_html}</ul>" if tip_html else "")
        + f'<p><a href="{e(online_url)}">▶ 点这里听英音</a></p>'
    )


def html_page(
    sentence: Sentence,
    ipa: str,
    tips: list[Tip],
    audio: dict[str, Path],
    online_url: str,
    day: str,
    push_time: str,
) -> str:
    """本地预览页：手机/电脑浏览器打开即可反复跟读。"""
    e = html.escape

    tip_html = "\n".join(
        f'<li>{_tip_badge(t.type)}<span>{e(t.text)}</span></li>' for t in tips
    ) or "<li>暂无要点</li>"

    players = []
    if "normal" in audio:
        players.append(
            f'<div class="player"><span class="label">常速</span>'
            f'<audio controls preload="metadata" src="{e(audio["normal"].name)}"></audio></div>'
        )
    if "slow" in audio:
        players.append(
            f'<div class="player"><span class="label">慢速跟读</span>'
            f'<audio controls preload="metadata" src="{e(audio["slow"].name)}"></audio></div>'
        )
    if not players:
        players.append(
            f'<div class="player"><span class="label">在线收听</span>'
            f'<a href="{e(online_url)}" target="_blank">点这里播放英音</a></div>'
        )

    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>每日一句 · {e(day)}</title>
<style>
  :root {{ color-scheme: light; }}
  * {{ box-sizing: border-box; }}
  body {{
    margin: 0; padding: 28px 18px 56px;
    font-family: "Segoe UI", "PingFang SC", "Microsoft YaHei", system-ui, sans-serif;
    background: #f6f4ef; color: #24292f;
  }}
  .card {{
    max-width: 720px; margin: 0 auto; background: #fff; border-radius: 18px;
    padding: 28px 28px 32px; box-shadow: 0 10px 30px rgba(30, 25, 15, .08);
  }}
  .kicker {{ font-size: 13px; letter-spacing: .12em; color: #8a8377; text-transform: uppercase; }}
  h1 {{ font-size: 26px; line-height: 1.45; margin: 10px 0 4px; font-weight: 650; }}
  .zh {{ color: #6b6459; font-size: 16px; margin: 0 0 22px; }}
  .ipa {{
    font-family: "Doulos SIL", "Charis SIL", "Lucida Sans Unicode", "Segoe UI", serif;
    font-size: 19px; background: #faf8f3; border: 1px dashed #ded6c6; border-radius: 10px;
    padding: 12px 16px; color: #4a463c; word-break: break-word;
  }}
  .ipa span.tag {{ font-size: 12px; color: #9a927f; margin-left: 8px; }}
  h2 {{ font-size: 15px; color: #8a8377; letter-spacing: .06em; margin: 28px 0 12px; text-transform: uppercase; }}
  ul.tips {{ list-style: none; padding: 0; margin: 0; }}
  ul.tips li {{ display: flex; gap: 10px; align-items: flex-start; padding: 9px 0; border-bottom: 1px solid #f1ece2; line-height: 1.65; }}
  ul.tips li:last-child {{ border-bottom: 0; }}
  .badge {{ flex: 0 0 auto; font-size: 12px; padding: 2px 9px; border-radius: 999px; font-weight: 600; }}
  .player {{ display: flex; align-items: center; gap: 12px; margin: 10px 0; }}
  .player .label {{ flex: 0 0 68px; font-size: 14px; color: #6b6459; }}
  audio {{ width: 100%; height: 38px; }}
  .footer {{ margin-top: 28px; font-size: 12px; color: #a39a89; text-align: center; }}
  button.ghost {{
    margin-top: 18px; background: #f6f4ef; border: 1px solid #e3dbc9; color: #6b6459;
    padding: 7px 14px; border-radius: 9px; font-size: 13px; cursor: pointer;
  }}
  button.ghost:hover {{ background: #efeade; }}
  .hidden {{ display: none; }}
</style>
</head>
<body>
  <div class="card">
    <div class="kicker">每日一句 · {e(day)}</div>
    <h1>{e(sentence.text)}</h1>
    <p class="zh" id="zh">{e(sentence.zh)}</p>
    <div class="ipa">{e(ipa) if ipa else "（暂无音标）"}</div>

    <h2>朗读要点</h2>
    <ul class="tips">
      {tip_html}
    </ul>

    <h2>跟读音频</h2>
    {"".join(players)}

    <button class="ghost" id="toggle">遮住中文，自测一下</button>
    <div class="footer">每天都来读三遍：常速听 → 慢速跟 → 常速录。</div>
  </div>
<script>
  const btn = document.getElementById('toggle');
  const zh = document.getElementById('zh');
  btn.addEventListener('click', () => {{
    zh.classList.toggle('hidden');
    btn.textContent = zh.classList.contains('hidden') ? '显示中文' : '遮住中文，自测一下';
  }});
</script>
</body>
</html>
"""


def save_page(path: Path, content: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return path


def default_day() -> str:
    return date.today().isoformat()
