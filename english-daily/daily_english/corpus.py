"""语料库：data/sentences.json 的读取与校验。"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CORPUS_PATH = ROOT / "data" / "sentences.json"


@dataclass
class Tip:
    type: str
    text: str


@dataclass
class Sentence:
    id: str
    text: str
    zh: str
    ipa_uk: str
    tips: list[Tip] = field(default_factory=list)

    @classmethod
    def from_dict(cls, raw: dict) -> "Sentence":
        tips = [Tip(type=t.get("type", "要点"), text=t.get("text", "")) for t in raw.get("tips", [])]
        return cls(
            id=raw.get("id", ""),
            text=raw.get("text", "").strip(),
            zh=raw.get("zh", "").strip(),
            ipa_uk=raw.get("ipa_uk", "").strip(),
            tips=[t for t in tips if t.text],
        )


def load_corpus(path: Path | None = None) -> list[Sentence]:
    """读取语料库；文件缺失或格式错误时给出明确报错。"""
    path = Path(path) if path else CORPUS_PATH
    if not path.exists():
        raise FileNotFoundError(f"找不到语料库文件：{path}")

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"语料库不是合法的 JSON：{path}\n{exc}") from exc

    items = data.get("sentences", data if isinstance(data, list) else [])
    sentences = [Sentence.from_dict(item) for item in items]
    sentences = [s for s in sentences if s.text]

    if not sentences:
        raise ValueError(f"语料库里没有可用的句子：{path}")

    # 同一句重复出现没有意义，顺手去个重
    seen, unique = set(), []
    for s in sentences:
        key = s.text.lower()
        if key not in seen:
            seen.add(key)
            unique.append(s)
    return unique
