import asyncio
import logging
from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, BufferedInputFile
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.exceptions import TelegramBadRequest

from config import BOT_TOKEN
from logger import setup_logger
import ai
import voice

log = setup_logger("main")
logging.getLogger("aiogram").setLevel(logging.WARNING)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())


@dp.message(CommandStart())
async def cmd_start(message: Message):
    log.info(f"[user={message.from_user.id}] @{message.from_user.username} запустил бота (/start)")
    ai.clear_history(message.from_user.id)
    await message.answer("Чё надо? Пиши, не стесняйся, блять.")


@dp.message(Command("reset"))
async def cmd_reset(message: Message):
    log.info(f"[user={message.from_user.id}] сброс истории (/reset)")
    ai.clear_history(message.from_user.id)
    await message.answer("Всё, забыл нахер про тебя. Начинаем заново.")


@dp.message(Command("image"))
async def cmd_image(message: Message):
    prompt = message.text.removeprefix("/image").strip()
    log.info(f"[user={message.from_user.id}] запрос /image: «{prompt}»")

    if not prompt:
        log.warning(f"[user={message.from_user.id}] пустой промт в /image")
        await message.answer("Блять, ты забыл написать что рисовать. Пиши: /image <описание>")
        return

    comment = await ai.generate_image_comment(message.from_user.id, prompt)
    await message.answer(comment)
    log.debug(f"[user={message.from_user.id}] отправлен комментарий: «{comment}»")

    await bot.send_chat_action(message.chat.id, "upload_photo")
    image_bytes = await ai.generate_image(prompt)

    if image_bytes:
        log.info(f"[user={message.from_user.id}] отправка изображения ({len(image_bytes) // 1024} КБ)")
        await message.answer_photo(BufferedInputFile(image_bytes, filename="image.png"))
    else:
        log.error(f"[user={message.from_user.id}] не удалось сгенерировать изображение для: «{prompt}»")
        await message.answer("Хуй знает, не смог нарисовать. Попробуй ещё раз.")


@dp.message(F.text)
async def handle_message(message: Message):
    log.info(f"[user={message.from_user.id}] @{message.from_user.username}: «{message.text[:80]}{'...' if len(message.text) > 80 else ''}»")
    await bot.send_chat_action(message.chat.id, "typing")
    result = await ai.generate(message.from_user.id, message.text)

    if result:
        if voice.should_answer_with_voice():
            log.info(f"[user={message.from_user.id}] режим ответа: голосовой")
            await bot.send_chat_action(message.chat.id, "record_voice")
            ogg = await voice.text_to_speech(result)
            if ogg:
                try:
                    log.info(f"[user={message.from_user.id}] отправка голосового")
                    await message.answer_voice(BufferedInputFile(ogg, filename="voice.ogg"))
                except TelegramBadRequest as e:
                    log.warning(f"[user={message.from_user.id}] голосовые запрещены пользователем, фолбек на текст: {e}")
                    await message.answer(result)
            else:
                log.warning(f"[user={message.from_user.id}] голос не сгенерировался, фолбек на текст")
                await message.answer(result)
        else:
            log.info(f"[user={message.from_user.id}] режим ответа: текст")
            await message.answer(result)
    else:
        log.error(f"[user={message.from_user.id}] генерация провалилась")
        await message.answer("Блять, все модели сдохли. Попробуй ещё раз.")


async def main():
    log.info("бот запускается...")
    await bot.delete_webhook(drop_pending_updates=True)
    log.info("вебхук удалён, начинаем поллинг")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())