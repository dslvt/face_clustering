from dotenv import dotenv_values

#!/usr/bin/env python
# pylint: disable=unused-argument, wrong-import-position
# This program is dedicated to the public domain under the CC0 license.

"""
Simple Bot to reply to Telegram messages.
First, a few handler functions are defined. Then, those functions are passed to
the Application and registered at their respective places.
Then, the bot is started and runs until we press Ctrl-C on the command line.
Usage:
Basic Echobot example, repeats messages.
Press Ctrl-C on the command line or send a signal to the process to stop the
bot.
"""

import logging
import pickle
import random
import face_recognition as fr
import tqdm
from PIL import Image
import io

from telegram import __version__ as TG_VER

try:
    from telegram import __version_info__
except ImportError:
    __version_info__ = (0, 0, 0, 0, 0)  # type: ignore[assignment]

if __version_info__ < (20, 0, 0, "alpha", 1):
    raise RuntimeError(
        f"This example is not compatible with your current PTB version {TG_VER}. To view the "
        f"{TG_VER} version of this example, "
        f"visit https://docs.python-telegram-bot.org/en/v{TG_VER}/examples.html"
    )
from telegram import ForceReply, Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters, ConversationHandler
import random
from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove, Update


# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)
IMAGE_INPUTING, UPLOAD_IMAGES, PROCESSING, MARKING, DOWNLOADING_RESULTS, SKIP_PROCESSING = range(
    5)

face_embeddings = pickle.load(open("face_embeddings.pkl", "rb"))
face_locations = pickle.load(open('face_locations.pkl', 'rb'))
faces = []

reply_keyboard = [
    ["Age", "Favourite colour"],
    ["Number of siblings", "Something else..."],
    ["Done"],
]
markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)


def has_user_preprocessed_images():
    return True

# Define a few command handlers. These usually take the two arguments update and
# context.


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    # print(type(context))
    # print(context)
    # print(dir(context))
    """Send a message when the command /start is issued."""
    # names = [f'input/{str(x).zfill(4)}.JPG' for x in range(579)]

    # for i, name in enumerate(tqdm.tqdm(names[:20])):
    #     image = fr.load_image_file(name)
    #     for fc in face_locations[i]:
    #         faces.append(image[fc[0]:fc[2], fc[3]:fc[1], :])

    # user = update.effective_user
    # await update.message.reply_html(
    #     rf"Hi {user.mention_html()}! Enter password:",
    #     reply_markup=ForceReply(selective=False),
    # )

    # keyboard = [
    #     [
    #         InlineKeyboardButton("Option 1", callback_data="1"),
    #         InlineKeyboardButton("Option 2", callback_data="2"),
    #     ],
    #     [InlineKeyboardButton("", callback_data="3")],
    # ]

    # reply_markup = InlineKeyboardMarkup(keyboard)

    # await update.message.reply_text("Please choose:", reply_markup=reply_markup)
    # await update.message.reply_text("Enter password, or upload images (jpg, zip)", markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)
    # )
    if has_user_preprocessed_images():
        reply_keyboard = [['Yes', 'No']]
        markup_key = ReplyKeyboardMarkup(
            reply_keyboard, one_time_keyboard=True)
        await update.message.reply_text(text='You have already preprocessed images. Do you want continue?', reply_markup=markup_key)
        return SKIP_PROCESSING
    else:
        return UPLOAD_IMAGES


async def upload_images(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text("Enter password, or upload images (jpg, zip)")


async def skip_processing(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.message.text == 'Yes':
        return PROCESSING
    else:
        return MARKING


async def processing_images(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    msg = await update.message.reply_text("Processing images...")

    names = [f'input/{str(x).zfill(4)}.JPG' for x in range(579)]

    for i, name in enumerate(names[:20]):
        update_message = f"Processed {i + 1}/{len(names)} images. Found {len(faces)} faces"
        await context.bot.edit_message_text(message_id=msg.message_id, text=update_message, chat_id=context._chat_id)
        image = fr.load_image_file(name)
        for fc in face_locations[i]:
            faces.append(image[fc[0]:fc[2], fc[3]:fc[1], :])


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /help is issued."""
    await update.message.reply_text("Help!")


# async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
#     """Echo the user message."""
#     await update.message.reply_text(update.message.text)
# async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    # await update.

async def done(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text(f"Until next time!")


async def random_face(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    random_idx = random.randint(0, len(faces) - 1)
    print(len(faces))
    rf = faces[random_idx]
    rf = Image.fromarray(rf.astype('uint8'), 'RGB')
    buf = io.BytesIO()
    rf.save(buf, format="PNG")
    byte_im = buf.getvalue()

    await update.message.reply_photo(byte_im)


def main() -> None:
    """Run the bot."""
    # Create the Application and pass it your bot's token.

    application = Application.builder().token(
        dotenv_values(".env")['BOT_TOKEN']).build()

    # on different commands - answer in Telegram
    # application.add_handler(CommandHandler("start", start))
    # application.add_handler(CommandHandler('random', random_face))
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            UPLOAD_IMAGES: [
                MessageHandler(filters.Regex("^Yes$") |
                               filters.Regex("^No$"), upload_images)
            ],
            PROCESSING: [
                MessageHandler(
                    filters.TEXT & ~(filters.COMMAND | filters.Regex(
                        "^Done$")), processing_images
                )
            ],
            MARKING: [
                MessageHandler(filters.Regex("^Yes$") |
                               filters.Regex("^No$"), done)
            ],
            DOWNLOADING_RESULTS: [],
            SKIP_PROCESSING: [MessageHandler(
                filters.Regex("^(Yes|No)$"), skip_processing)]
        },
        fallbacks=[MessageHandler(filters.Regex("^Done$"), done)],
    )
    application.add_handler(conv_handler)

    # Run the bot until the user presses Ctrl-C
    application.run_polling()


if __name__ == "__main__":
    main()
