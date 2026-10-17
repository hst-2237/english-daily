"""音标：优先用人工校订的英式音标，缺失时尝试自动生成。

自动生成的顺序：
1. 本机装了 espeak-ng 时，用它按 en-gb 规则转写（质量尚可）；
2. 再退一步，逐词查 free dictionary API（偏美音，仅供参考）。
自动结果会带一个「仅供参考」的标记，避免让人误以为是权威标注。
"""

from __future__ import annotations

import json
import re
import shutil
import subprocess
import urllib.parse
import urllib.request

from .corpus import Sentence


def _espeak_ipa(text: str) -> str | None:
    exe = shutil.which("espeak-ng") or shutil.which("espeak")
    if not exe:
        return None
    try:
        out = subprocess.run(
            [exe, "-v", "en-gb", "--ipa", "-q", text],
            capture_output=True,
            text=True,
            timeout=15,
            encoding="utf-8",
            errors="replace",
        )
    except (OSError, subprocess.SubprocessError):
        return None
    ipa = " ".join(out.stdout.split())
    return f"/{ipa}/" if ipa else None


def _word_ipa(word: str) -> str | None:
    clean = re.sub(r"[^a-zA-Z'-]", "", word)
    if not clean:
        return None
    url = "https://api.dictionaryapi.dev/api/v2/entries/en/" + urllib.parse.quote(clean)
    try:
        with urllib.request.urlopen(url, timeout=6) as resp:
            data = json.load(resp)
    except Exception:  # 网络问题不该拖垮整个推送
        return None
    for entry in data if isinstance(data, list) else []:
        for ph in entry.get("phonetics", []):
            text = (ph.get("text") or "").strip()
            if text:
                return text.strip("/")
    return None


def _auto_ipa(sentence: str) -> str | None:
    ipa = _espeak_ipa(sentence)
    if ipa:
        return ipa

    parts = [_word_ipa(w) for w in sentence.split()]
    if any(parts):
        joined = " ".join(p or w.strip(".,!?;:") for p, w in zip(parts, sentence.split()))
        return f"/{joined}/"
    return None


def resolve(sentence: Sentence) -> tuple[str, str]:
    """返回 (音标, 来源)。来源为 curated / auto / none。"""
    if sentence.ipa_uk:
        return sentence.ipa_uk, "curated"

    auto = _auto_ipa(sentence.text)
    if auto:
        return auto, "auto"
    return "", "none"
