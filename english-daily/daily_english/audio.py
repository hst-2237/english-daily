"""英音音频：默认用 edge-tts 在本地生成 mp3；不可用时退回在线播放链接。

edge-tts 是微软 Edge 浏览器的离线语音合成接口的封装，免费、无需 API Key，
英音可选 en-GB-RyanNeural（男）与 en-GB-SoniaNeural（女）。
"""

from __future__ import annotations

import asyncio
import urllib.parse
from pathlib import Path


class AudioError(RuntimeError):
    """音频生成失败，通常是没装 edge-tts 或网络不通。"""


def edge_available() -> bool:
    try:
        import edge_tts  # noqa: F401
    except ImportError:
        return False
    return True


def online_url(text: str) -> str:
    """百度翻译的语音接口：lan=uk 为英音，国内网络可直接访问，点开就能听。"""
    return "https://fanyi.baidu.com/gettts?" + urllib.parse.urlencode(
        {"lan": "uk", "text": text, "spd": "3", "source": "web"}
    )


async def _speak(text: str, voice: str, rate: str, target: Path) -> None:
    import edge_tts

    communicate = edge_tts.Communicate(text, voice, rate=rate)
    await communicate.save(str(target))


def synthesize(
    text: str,
    out_dir: Path,
    voice: str = "en-GB-RyanNeural",
    normal_rate: str = "+0%",
    slow_rate: str = "-25%",
) -> dict[str, Path]:
    """生成常速与慢速两个 mp3，返回 {"normal": path, "slow": path}。"""
    if not edge_available():
        raise AudioError("没有安装 edge-tts，无法生成本地音频（pip install edge-tts）")

    out_dir.mkdir(parents=True, exist_ok=True)
    jobs = {
        "normal": (normal_rate, out_dir / "sentence.mp3"),
        "slow": (slow_rate, out_dir / "sentence-slow.mp3"),
    }

    for name, (rate, target) in jobs.items():
        try:
            asyncio.run(_speak(text, voice, rate, target))
        except Exception as exc:  # 网络、鉴权、接口变更都归到这里
            raise AudioError(f"生成 {name} 音频失败：{exc}") from exc
        if not target.exists() or target.stat().st_size == 0:
            raise AudioError(f"生成的 {name} 音频是空文件：{target}")

    return {name: target for name, (_, target) in jobs.items()}
