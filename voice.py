import random
import tempfile
import os
import subprocess
import edge_tts

from logger import setup_logger

log = setup_logger("voice")

VOICE = "ru-RU-DmitryNeural"
VOICE_CHANCE = 0.35


def should_answer_with_voice() -> bool:
    return random.random() < VOICE_CHANCE


async def text_to_speech(text: str) -> bytes | None:
    tmp_mp3_path = None
    tmp_ogg_path = None
    try:
        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as f:
            tmp_mp3_path = f.name
        with tempfile.NamedTemporaryFile(suffix=".ogg", delete=False) as f:
            tmp_ogg_path = f.name

        communicate = edge_tts.Communicate(text, VOICE)
        await communicate.save(tmp_mp3_path)

        slow_factor = random.uniform(0.78, 0.88)
        vibrato_depth = random.uniform(0.2, 0.35)
        vibrato_freq = random.uniform(2.5, 3.5)
        pitch = random.uniform(0.78, 0.84)
        tempo_compensation = 1.0 / pitch

        af = (
            f"asetrate=44100*{pitch:.4f},"
            f"atempo={min(tempo_compensation, 2.0):.4f},"
            f"atempo={slow_factor:.4f},"
            f"vibrato=f={vibrato_freq:.2f}:d={vibrato_depth:.2f},"
            f"equalizer=f=100:width_type=o:width=2:g=7,"
            f"equalizer=f=3000:width_type=o:width=2:g=-6,"
            f"aresample=48000,"
            f"volume=1.4"
        )

        cmd = [
            "ffmpeg", "-y",
            "-i", tmp_mp3_path,
            "-af", af,
            "-c:a", "libopus",
            "-ar", "48000",
            "-b:a", "64k",
            tmp_ogg_path
        ]

        subprocess.run(cmd, check=True, capture_output=True)

        with open(tmp_ogg_path, "rb") as f:
            result = f.read()

        log.info(f"голос сгенерирован ({len(result) // 1024} КБ)")
        return result

    except Exception as e:
        log.error(f"ошибка генерации голоса: {e}")
        return None
    finally:
        for path in [tmp_mp3_path, tmp_ogg_path]:
            if path:
                try:
                    os.unlink(path)
                except Exception:
                    pass