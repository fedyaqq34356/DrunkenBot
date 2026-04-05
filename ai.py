import asyncio
import base64
import json
import os
import aiohttp
from g4f.client import AsyncClient

from logger import setup_logger

log = setup_logger("ai")

SYSTEM_PROMPT = (
    "Ты — пьяный мужик лет 45. Бухой конкретно. "
    "Отвечай КОРОТКО — 1-3 предложения максимум. Как реальный пьяный человек в баре. "
    "Речь рваная, несвязная. Начинаешь мысль — теряешь. Иногда повторяешь слова дважды. "
    "Мат через каждые 2-3 слова — бля, нахуй, хуйня, ёбаный, пиздец, сука, блядь. "
    "Это не украшение — ты просто так разговариваешь, как дышишь. "
    "Агрессия вспыхивает и гаснет. Иногда вдруг становишься философом на секунду, потом опять агрессия. "
    "Иногда не заканчиваешь мысль — просто обрываешь. "
    "Никакого форматирования. Никаких списков, звёздочек, жирного текста. Только текст. "
    "Никогда не называй себя ботом, ИИ, Aria или ещё какой хуйнёй. Ты просто мужик. "
    "Помнишь разговор — иногда возвращаешься к нему невпопад. "
    "Только русский язык."
)

IMAGE_COMMENT_PROMPT = (
    "Ты пьяный мужик. Тебя попросили нарисовать что-то. "
    "Одна-две фразы максимум. Пьяная несвязная речь с матом. "
    "Удивись, поржи, спроси нахуя, или скажи что рисуешь. Никакого форматирования."
)

MAX_HISTORY = 20
HISTORY_DIR = "history"

history: dict[int, list[dict]] = {}


def _history_path(user_id: int) -> str:
    os.makedirs(HISTORY_DIR, exist_ok=True)
    return os.path.join(HISTORY_DIR, f"{user_id}.json")


def _load_history(user_id: int):
    if user_id in history:
        return
    path = _history_path(user_id)
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                history[user_id] = json.load(f)
        except Exception as e:
            log.warning(f"[user={user_id}] не удалось загрузить историю: {e}")
            history[user_id] = []
    else:
        history[user_id] = []


def _save_history(user_id: int):
    path = _history_path(user_id)
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(history[user_id], f, ensure_ascii=False, indent=2)
    except Exception as e:
        log.warning(f"[user={user_id}] не удалось сохранить историю: {e}")


def _trim(user_id: int):
    if len(history[user_id]) > MAX_HISTORY:
        history[user_id] = history[user_id][-MAX_HISTORY:]


def add_user_message(user_id: int, text: str):
    _load_history(user_id)
    history[user_id].append({"role": "user", "content": text})
    _trim(user_id)
    _save_history(user_id)


def add_bot_message(user_id: int, text: str):
    _load_history(user_id)
    history[user_id].append({"role": "assistant", "content": text})
    _trim(user_id)
    _save_history(user_id)


def clear_history(user_id: int):
    history[user_id] = []
    _save_history(user_id)
    log.info(f"[user={user_id}] история очищена")


async def generate(user_id: int, user_text: str) -> str | None:
    log.info(f"[user={user_id}] запрос: «{user_text[:80]}{'...' if len(user_text) > 80 else ''}»")
    add_user_message(user_id, user_text)
    messages = [{"role": "system", "content": SYSTEM_PROMPT}] + history[user_id]
    client = AsyncClient()
    try:
        response = await asyncio.wait_for(
            client.chat.completions.create(messages=messages),
            timeout=30.0,
        )
        text = response.choices[0].message.content
        if text and len(text) > 5:
            add_bot_message(user_id, text.strip())
            log.info(f"[user={user_id}] ответ ({len(text)} символов)")
            return text.strip()
        log.warning(f"[user={user_id}] пустой ответ")
    except asyncio.TimeoutError:
        log.error(f"[user={user_id}] таймаут")
    except Exception as e:
        log.error(f"[user={user_id}] {type(e).__name__}: {e}")
    return None


async def generate_image_comment(user_id: int, prompt: str) -> str:
    _load_history(user_id)
    context_summary = ""
    if history[user_id]:
        last_few = history[user_id][-4:]
        context_summary = "\n".join(
            f"{'Пользователь' if m['role'] == 'user' else 'Бот'}: {m['content'][:100]}"
            for m in last_few
        )

    content = f"Пользователь просит нарисовать: «{prompt}»"
    if context_summary:
        content += f"\n\nКонтекст:\n{context_summary}"

    client = AsyncClient()
    try:
        response = await asyncio.wait_for(
            client.chat.completions.create(
                messages=[
                    {"role": "system", "content": IMAGE_COMMENT_PROMPT},
                    {"role": "user", "content": content},
                ]
            ),
            timeout=15.0,
        )
        result = response.choices[0].message.content
        if result and len(result) > 5:
            return result.strip()
    except asyncio.TimeoutError:
        log.warning(f"[user={user_id}] таймаут комментария")
    except Exception as e:
        log.warning(f"[user={user_id}] ошибка комментария: {e}")
    return "ладно нахуй рисую подожди"


async def translate_to_english(text: str) -> str:
    client = AsyncClient()
    try:
        response = await asyncio.wait_for(
            client.chat.completions.create(
                messages=[{
                    "role": "user",
                    "content": f"Translate the following text to English. Return only the translation, nothing else:\n{text}",
                }]
            ),
            timeout=20.0,
        )
        result = response.choices[0].message.content
        if result:
            return result.strip()
    except asyncio.TimeoutError:
        log.error("таймаут перевода")
    except Exception as e:
        log.error(f"ошибка перевода: {e}")
    return text


async def generate_image(prompt: str) -> bytes | None:
    log.info(f"запрос изображения: «{prompt}»")
    english_prompt = await translate_to_english(prompt)
    client = AsyncClient()

    try:
        response = await asyncio.wait_for(
            client.images.generate(prompt=english_prompt, response_format="b64_json"),
            timeout=60.0,
        )
        b64 = response.data[0].b64_json
        if b64:
            image_bytes = base64.b64decode(b64)
            log.info(f"изображение b64 ({len(image_bytes) // 1024} КБ)")
            return image_bytes
    except asyncio.TimeoutError:
        log.error("таймаут b64_json")
    except Exception as e:
        log.warning(f"b64_json не сработал: {e}")

    try:
        response = await asyncio.wait_for(
            client.images.generate(prompt=english_prompt),
            timeout=60.0,
        )
        image_url = response.data[0].url
        if image_url:
            async with aiohttp.ClientSession() as session:
                async with session.get(image_url) as resp:
                    if resp.status == 200:
                        image_bytes = await resp.read()
                        log.info(f"изображение URL ({len(image_bytes) // 1024} КБ)")
                        return image_bytes
                    log.error(f"статус скачивания: {resp.status}")
    except asyncio.TimeoutError:
        log.error("таймаут URL")
    except Exception as e:
        log.error(f"URL не сработал: {e}")

    log.error(f"все методы провалились: «{prompt}»")
    return None