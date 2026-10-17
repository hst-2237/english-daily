"""朗读要点：语料库里人工标注的连读、失爆、同化、弱读、语调等。

如果某句没有人工标注，则根据句子类型给出通用的朗读提示，而不是硬编造细节。
"""

from __future__ import annotations

from .corpus import Sentence, Tip

WEAK_FORMS = {"a", "an", "the", "to", "of", "and", "for", "at", "in", "on", "can", "have", "been", "me"}


def _generic_tips(sentence: Sentence) -> list[Tip]:
    text = sentence.text.strip()
    words = text.split()
    tips: list[Tip] = []

    if text.endswith("?"):
        tips.append(Tip("语调", "一般疑问句/反问句句尾用升调；特殊疑问句（what/why/how 开头）用降调。"))
    elif text.endswith("!"):
        tips.append(Tip("语调", "感叹句整体降调，把关键词读重、读长。"))
    else:
        tips.append(Tip("语调", "陈述句用降调，句尾自然下滑，别每句都上扬。"))

    if len(words) >= 4:
        tips.append(Tip("节奏", f"整句 {len(words)} 个词，先按意群断开：{' / '.join(words[:3])} … 再连起来读。"))

    weak = [w.strip(".,!?;:").lower() for w in words if w.strip(".,!?;:").lower() in WEAK_FORMS]
    if weak:
        tips.append(Tip("弱读", "功能词 " + "、".join(dict.fromkeys(weak)) + " 在句中要弱读，元音变成 /ə/ 或 /ɪ/，不要每个词都读满。"))

    return tips


def build(sentence: Sentence) -> list[Tip]:
    return sentence.tips if sentence.tips else _generic_tips(sentence)
