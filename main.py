from aiogram import F
import asyncio
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import Command
from PIL import Image
from io import BytesIO

from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.utils.keyboard import ReplyKeyboardBuilder


# Включаем логирование, чтобы не пропустить важные сообщения
logging.basicConfig(level=logging.INFO)
# Объект бота
bot = Bot(token="5581794924:AAE-9g3zDg546E43itu-gONgOoChbEltGN8", default=DefaultBotProperties(parse_mode=ParseMode.HTML))
# Диспетчер
dp = Dispatcher()


# Define the states
class AlbumProcessing(StatesGroup):
    WAIT_FOR_ALBUM = State()


media_groups = []


@dp.message(Command("start"))
async def start_command(message: types.Message):
    custom_keyboard = types.ReplyKeyboardMarkup(
        keyboard=[[types.KeyboardButton(text="/album")]],
        resize_keyboard=True
    )
    await message.answer("Send photos or album to get pdf.\n\nIf you send album(s), when you upload photos fully, enter /album -command or press the bytton /album.", reply_markup=custom_keyboard)


@dp.message(F.photo)
async def download_photo(message: types.Message, state: FSMContext):
    # Check if the message is part of a media group (album)
    if message.media_group_id:
        album_media_group_id = message.media_group_id

        if media_groups:
            # Append the new message to the existing media group
            media_groups.append(message)
        else:
            # Create a new entry for the media group
            media_groups.append(message)
            # Set the state to WAIT_FOR_ALBUM for the first message of the album
            await state.set_state(AlbumProcessing.WAIT_FOR_ALBUM)

        # Save the media group data in the FSM context
        await state.update_data(album=media_groups)
    else:
        # Process a single photo
        await process_single_photo(message)


@dp.message(Command('album'))
async def download_album(message: types.Message, state: FSMContext):
    pdf_buffer = BytesIO()
    media_group = await state.get_data()
    album = media_group.get('album')
    if album:
        # Iterate over the messages in the media group and append photos to a PIL Image
        pil_images = []
        for media_msg in album:
            pil_image = await download_photo_to_pil(media_msg.photo[-1])
            pil_images.append(pil_image)

        # Save the concatenated PIL Images as a PDF
        pil_images[0].save(
            pdf_buffer,
            format='PDF',
            save_all=True,
            append_images=pil_images[1:]
        )

        # Send the PDF file as a document using InputFile
        pdf_content = pdf_buffer.getvalue()
        input_file = types.BufferedInputFile(pdf_content, filename='album.pdf')
        await bot.send_document(message.chat.id, input_file, caption="Album converted to PDF!")
        await state.clear()
        media_groups.clear()
    else:
        await bot.send_message(message.chat.id, "You did not send me album!")


async def process_single_photo(message: types.Message):
    photo_buffer = BytesIO()
    await bot.download(message.photo[-1].file_id, destination=photo_buffer)

    # Convert the photo content to a PIL Image
    pil_image = Image.open(photo_buffer)
    pil_image = pil_image.convert('RGB')  # Ensure RGB mode

    # Create a BytesIO buffer for the PDF
    pdf_buffer = BytesIO()

    # Save the PIL Image to the PDF buffer using img2pdf
    pil_image.save(pdf_buffer, format='PDF')

    pdf_content = pdf_buffer.getvalue()

    # Send the PDF file as a document using InputFile
    input_file = types.BufferedInputFile(pdf_content, filename='Dilshodbek Jamoliddinov.pdf')
    await bot.send_document(message.chat.id, input_file, caption="Photo converted to PDF!")


async def download_photo_to_pil(photo_size: types.PhotoSize) -> Image.Image:
    # Download the file content into a BytesIO buffer
    photo_buffer = BytesIO()
    await bot.download(photo_size.file_id, destination=photo_buffer)
    pil_image = Image.open(photo_buffer)
    return pil_image


# Запуск процесса поллинга новых апдейтов
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
