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

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)
PASSWORD, PHOTO, LOCATION, BIO = range(4)

face_embeddings = pickle.load(open("face_embeddings.pkl", "rb"))
face_locations = pickle.load(open('face_locations.pkl', 'rb'))
faces = []


# Define a few command handlers. These usually take the two arguments update and
# context.
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /start is issued."""
    names = [f'input/{str(x).zfill(4)}.JPG' for x in range(579)]

    for i, name in enumerate(tqdm.tqdm(names[:20])):
        image = fr.load_image_file(name)
        for fc in face_locations[i]:
            faces.append(image[fc[0]:fc[2], fc[3]:fc[1], :])

    user = update.effective_user
    await update.message.reply_html(
        rf"Hi {user.mention_html()}! Enter password:",
        reply_markup=ForceReply(selective=False),
    )

    keyboard = [
        [
            InlineKeyboardButton("Option 1", callback_data="1"),
            InlineKeyboardButton("Option 2", callback_data="2"),
        ],
        [InlineKeyboardButton("", callback_data="3")],
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text("Please choose:", reply_markup=reply_markup)


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /help is issued."""
    await update.message.reply_text("Help!")


# async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
#     """Echo the user message."""
#     await update.message.reply_text(update.message.text)
# async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    # await update.


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
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler('random', random_face))

    # Run the bot until the user presses Ctrl-C
    application.run_polling()


if __name__ == "__main__":
    main()
