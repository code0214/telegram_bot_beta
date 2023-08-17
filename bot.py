import json
import logging
import os
import subprocess
from tempfile import TemporaryDirectory
from aiogram import Bot, Dispatcher, executor, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext

import utils

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

try:
    with open("credentials.json", encoding="UTF-8") as f:
        parsed = json.load(f)
        TG_API_TOKEN = parsed["api_token"]
except FileNotFoundError:
    logger.error("Credentials not found. Please create a credentials.json file")
except KeyError:
    logger.error("Wrong credentials.json format")

# Initialize bot and dispatcher
bot = Bot(token=TG_API_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)


@dp.message_handler(commands=["start"])
async def start(message: types.Message, state: FSMContext) -> None:
    """Displays welcome message

    Args:
        message (types.Message): message to be processed
        state (FSMContext): bot state"""

    await message.reply("Hello!\nPlease send me images to be copied!")

@dp.message_handler(commands=["new_pic"])
async def new_pic(message: types.Message, state: FSMContext) -> None:
    await message.reply("Send me a new image to process!")


@dp.message_handler(content_types=types.ContentType.ANY)
async def file_handler(message: types.Message, state: FSMContext) -> None:
    """File handler to process documents and images.

    Args:
        message (types.Message): message to be processed
        state (FSMContext): bot state
    """
    if message.document:
        mime_type = message.document.mime_type
        if mime_type == "image/heic":
            await message.reply("Processing, please wait...")
            await process_heic_document(message=message)
        elif mime_type == "image/x-adobe-dng":
            await message.reply("Processing, please wait...")
            await process_dng_document(message=message)
        else:
            await message.reply("Not a supported document format. Please send me a valid image or document.")
    elif message.photo:
        await message.reply("Processing, please wait...")
        await process_photo(message=message)
    else:    
        await message.reply("Not a valid image or document. Please send me a valid image or document.")


async def send_processed_images(user_id, path_to_photos: str) -> bool:
    """Send processed images to the user

    Args:
        user_id (int): user id
        path_to_photos (str): path to images
    """

    # Loop over photos and send the renamed and edited ones
    for filename in os.listdir(path_to_photos):
        if filename.endswith("_cloaked.jpg") or filename.endswith("_cloaked.png"):
            renamed_filename = filename.replace("_cloaked", "_copied")
            original_path = os.path.join(path_to_photos, filename)
            renamed_path = os.path.join(path_to_photos, renamed_filename)
            
            os.rename(original_path, renamed_path)  # Rename the file
            
            with open(renamed_path, "rb") as photo_file:
                await bot.send_document(chat_id=user_id, document=photo_file)

async def process_document(message: types.Message) -> None:
    with TemporaryDirectory() as temp_dir:
        # Note: this works the same when there's multiple images too
        await message.document.download(make_dirs=True, destination_dir=temp_dir)
        path_to_photos = temp_dir + "/documents/"
        # Run fawkes on our temporary directory
        try:
            await utils.run_fawkes(input_dir_path=path_to_photos, mode="low")
            await send_processed_images(user_id=message.from_id, path_to_photos=path_to_photos)
        except:
            await message.reply("Error when processing image")

async def process_photo(message: types.Message) -> None:
    # Telegram sends a photo in multiple different resolutions,
    # we pick the largest one
    images: types.PhotoSize = message.photo[-1]

    with TemporaryDirectory() as temp_dir:
        # Note: this works the same when there's multiple images too
        await images.download(make_dirs=True, destination_dir=temp_dir)
        path_to_photos = temp_dir + "/photos/"
        # Run fawkes on our temporary directory
        try:
            await utils.run_fawkes(input_dir_path=path_to_photos, mode="low")
            await send_processed_images(user_id=message.from_id, path_to_photos=path_to_photos)
        except:
            await message.reply("Error when processing image.")

async def process_heic(message: types.Message) -> None:
    with TemporaryDirectory() as temp_dir:
        await message.document.download(make_dirs=True, destination_dir=temp_dir)
        heic_path = temp_dir + "/image.heic"
        # Convert HEIC to JPEG
        jpeg_path = temp_dir + "/image.jpg"
        convert_heic_to_jpeg(heic_path, jpeg_path)
        # Process the converted JPEG using Fawkes
        try:
            await utils.run_fawkes(input_dir_path=jpeg_path, mode="low")
            await send_processed_images(user_id=message.from_id, path_to_photos=jpeg_path)
        except:
            await message.reply("Error when processing image.")

async def process_dng(message: types.Message) -> None:
    with TemporaryDirectory() as temp_dir:
        await message.document.download(make_dirs=True, destination_dir=temp_dir)
        dng_path = temp_dir + "/image.dng"
        # Convert DNG to JPEG
        jpeg_path = temp_dir + "/image.jpg"
        convert_dng_to_jpeg(dng_path, jpeg_path)
        # Process the converted JPEG using Fawkes
        try:
            await utils.run_fawkes(input_dir_path=jpeg_path, mode="low")
            await send_processed_images(user_id=message.from_id, path_to_photos=jpeg_path)
        except:
            await message.reply("Error when processing image.")

async def process_heic_document(message: types.Message) -> None:
    with TemporaryDirectory() as temp_dir:
        await message.document.download(make_dirs=True, destination_dir=temp_dir)
        heic_path = temp_dir + "/" + message.document.file_name
        # Convert HEIC to JPEG
        jpeg_path = temp_dir + "/converted_image.jpg"
        convert_heic_to_jpeg(heic_path, jpeg_path)
        # Process the converted JPEG using Fawkes
        try:
            await utils.run_fawkes(input_dir_path=jpeg_path, mode="low")
            await send_processed_images(user_id=message.from_id, path_to_photos=jpeg_path)
        except:
            await message.reply("Error when processing image.")

async def process_dng_document(message: types.Message) -> None:
    with TemporaryDirectory() as temp_dir:
        await message.document.download(make_dirs=True, destination_dir=temp_dir)
        dng_path = temp_dir + "/" + message.document.file_name
        # Convert DNG to JPEG
        jpeg_path = temp_dir + "/converted_image.jpg"
        convert_dng_to_jpeg(dng_path, jpeg_path)
        # Process the converted JPEG using Fawkes
        try:
            await utils.run_fawkes(input_dir_path=jpeg_path, mode="low")
            await send_processed_images(user_id=message.from_id, path_to_photos=jpeg_path)
        except:
            await message.reply("Error when processing image.")

def convert_heic_to_jpeg(heic_path, jpeg_path):
    # FFmpeg command to convert HEIC to JPEG
    ffmpeg_cmd = [
        'ffmpeg',
        '-i', heic_path,
        '-q:v', '2',  # JPEG quality (0-31, higher is better)
        jpeg_path
    ]
    
    # Execute FFmpeg command
    subprocess.run(ffmpeg_cmd)

def convert_dng_to_jpeg(dng_path, jpeg_path):
    # Convert DNG to intermediate PPM format using dcraw
    intermediate_path = dng_path.replace('.dng', '_intermediate.ppm')
    dcraw_cmd = [
        'dcraw',
        '-c',  # Output to stdout
        dng_path
    ]
    with open(intermediate_path, 'wb') as intermediate_file:
        subprocess.run(dcraw_cmd, stdout=intermediate_file)
    
    # Convert PPM to JPEG using FFmpeg
    ffmpeg_cmd = [
        'ffmpeg',
        '-i', intermediate_path,
        '-q:v', '2',  # JPEG quality (0-31, higher is better)
        jpeg_path
    ]
    
    # Execute FFmpeg command
    subprocess.run(ffmpeg_cmd)
    
if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)
