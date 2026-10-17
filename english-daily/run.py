"""每日一句 · 入口脚本。

在 PyCharm 里直接右键运行本文件即可，等价于：

    python run.py                 # 今天这一句：生成音频 + 网页 + 推送
    python run.py --no-push       # 只生成，不推送
    python run.py --open          # 生成后自动用浏览器打开预览页
    python run.py --index 3       # 指定第 3 句（1 开始）
    python run.py --force         # 同一天也换一句
    python run.py --list          # 看看语料库里都有什么
    python run.py --test-push     # 只发一条测试消息，验证渠道是否配通
"""

from __future__ import annotations

import argparse
import os
import sys
import webbrowser
from datetime import date
from pathlib import Path

from daily_english import audio as audio_mod
from daily_english import clock
from daily_english import phonetics, render, tips as tips_mod
from daily_english import state as state_mod
from daily_english.config import Config
from daily_english.corpus import Sentence, load_corpus
from daily_english.push import PushError, send
from daily_english.state import choose_index

ROOT = Path(__file__).resolve().parent


def _tolerant_console() -> None:
    """老终端是 GBK 编码，音标里的 ə / ʊ 这类符号会直接抛异常，这里降级成 ? 而不是崩掉。"""
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(errors="replace")
        except (AttributeError, OSError):
            pass


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="英语每日一句：句子 + 翻译 + 音标 + 朗读要点 + 英音音频 + 微信推送")
    parser.add_argument("--index", type=int, help="指定用第几句（从 1 开始）")
    parser.add_argument(
        "--by-date",
        action="store_true",
        help="按日期固定轮换，不依赖本地状态文件（GitHub Actions 用这个）",
    )
    parser.add_argument("--force", action="store_true", help="同一天也换下一句")
    parser.add_argument("--date", help="覆盖日期，形如 2026-10-17（仅影响输出目录和标题，便于测试）")
    parser.add_argument("--no-audio", action="store_true", help="不生成音频")
    parser.add_argument("--no-push", action="store_true", help="只生成内容，不推送")
    parser.add_argument("--open", action="store_true", help="生成后用浏览器打开预览页")
    parser.add_argument("--list", action="store_true", help="列出语料库内容")
    parser.add_argument("--test-push", action="store_true", help="发送一条测试消息")
    return parser.parse_args(argv)


def print_sentence(sentence: Sentence, ipa: str) -> None:
    line = "─" * 56
    print(line)
    print(f"  {sentence.text}")
    print(f"  {sentence.zh}")
    if ipa:
        print(f"  {ipa}")
    print(line)


def build(day: str, index: int | None, force: bool, make_audio: bool, cfg: Config) -> tuple[Sentence, dict]:
    corpus = load_corpus()
    if index is not None:
        if not 1 <= index <= len(corpus):
            raise SystemExit(f"--index 超出范围，语料库共 {len(corpus)} 句")
        idx = index - 1
    else:
        idx = choose_index(len(corpus), force_new=force, today=day)

    sentence = corpus[idx]
    ipa, ipa_source = phonetics.resolve(sentence)
    if ipa_source == "auto":
        ipa_note = "自动生成，仅供参考"
    elif ipa_source == "none":
        ipa_note = "暂无音标，可在 data/sentences.json 里补上 ipa_uk"
    else:
        ipa_note = ""

    study_tips = tips_mod.build(sentence) if cfg.show_tips else []

    out_dir = cfg.output_dir / day
    out_dir.mkdir(parents=True, exist_ok=True)

    audio_files: dict[str, Path] = {}
    audio_warning = ""
    if make_audio and cfg.audio_engine == "edge":
        try:
            audio_files = audio_mod.synthesize(
                sentence.text,
                out_dir,
                voice=cfg.voice,
                normal_rate=cfg.normal_rate,
                slow_rate=cfg.slow_rate,
            )
        except audio_mod.AudioError as exc:
            audio_warning = str(exc)
            print(f"[!] {audio_warning}")
            print("    已改为在推送里附上在线英音链接。")
    elif make_audio and cfg.audio_engine != "edge":
        audio_warning = "配置为不生成 mp3，推送里只给在线播放链接"

    online = audio_mod.online_url(sentence.text)

    page = render.html_page(
        sentence=sentence,
        ipa=ipa,
        tips=study_tips,
        audio=audio_files,
        online_url=online,
        day=day,
        push_time=cfg.push_time,
    )
    html_path = render.save_page(out_dir / "index.html", page)

    audio_lines = [f"- 在线英音（点开就能听）：{online}"]
    if audio_files:
        audio_lines.append(f"- 慢速跟读：电脑本地 output/{day}/sentence-slow.mp3")

    md = render.markdown(sentence, ipa, study_tips, audio_lines, day)
    (out_dir / "message.md").write_text(md, encoding="utf-8")
    snippet = render.html_snippet(sentence, ipa, study_tips, online, day)

    print_sentence(sentence, ipa)
    if study_tips:
        print("  朗读要点：")
        for t in study_tips:
            print(f"   · 【{t.type}】{t.text}")
    print(f"  网页预览：{html_path}")
    if ipa_note:
        print(f"  音标说明：{ipa_note}")

    return sentence, {
        "day": day,
        "html": html_path,
        "html_text": page,
        "html_snippet": snippet,
        "markdown": md,
        "audio": audio_files,
        "online": online,
        "index": idx,
        "count": len(corpus),
        "warning": audio_warning,
    }


def main(argv: list[str] | None = None) -> int:
    _tolerant_console()
    args = parse_args(argv)
    cfg = Config(ROOT / "config.ini")

    if args.list:
        corpus = load_corpus()
        for i, s in enumerate(corpus, 1):
            print(f"{i:>3}. {s.text}  —— {s.zh}")
        print(f"\n共 {len(corpus)} 句")
        return 0

    if args.test_push:
        title = "每日一句 · 推送测试"
        body = "## 推送测试成功\n\n如果你在微信里看到这条消息，说明推送渠道已经配置好了。"
        try:
            channel = send(cfg, title, body, f"<h2>{title}</h2><p>{body}</p>")
        except PushError as exc:
            print(f"[×] {exc}")
            return 1
        if channel == "console":
            print("[i] 当前是 console 模式，没有真的发到微信。")
            print("    想在微信里收到：改 config.ini 的 [app] channel，并填好对应的密钥。")
        else:
            print(f"[✓] 已通过 {channel} 发送测试消息，去微信看看。")
        return 0

    day = args.date or clock.today_iso()
    try:
        date.fromisoformat(day)
    except ValueError:
        print(f"[×] --date 格式不对：{day}（应为 2026-10-17 这种）")
        return 1

    # 计划任务会「每天 07:30」和「每次登录」各触发一次，这里按日期去重，
    # 保证一天只推一条。想重推就加 --force。
    if not args.no_push and not args.force and state_mod.pushed_today(day):
        print(f"今天（{day}）已经推送过了，跳过。想强制重推加 --force。")
        return 0

    # 云端每次都是干净环境，读不到本地状态，用日期直接算轮换位置
    index = args.index
    if index is None and args.by_date:
        index = state_mod.index_for_date(len(load_corpus()), day) + 1

    sentence, info = build(day, index, args.force, not args.no_audio, cfg)

    if args.no_push:
        print("\n已跳过推送（--no-push）。")
    else:
        title = f"每日一句 · {sentence.text}"
        try:
            channel = send(cfg, title, info["markdown"], info["html_snippet"])
        except PushError as exc:
            print(f"\n[×] 推送失败：{exc}")
            return 1
        state_mod.mark_pushed(day)
        if channel == "console":
            print("\n（当前是 console 模式，没有真的推送到微信；")
            print("  想在微信里收到，请编辑 config.ini 的 [app] channel 并填写相应密钥）")
        else:
            print(f"\n[✓] 已推送到 {channel}")

    if args.open:
        webbrowser.open(info["html"].as_uri())
    return 0


if __name__ == "__main__":
    sys.exit(main())
