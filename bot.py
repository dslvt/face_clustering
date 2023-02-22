from dotenv import dotenv_values
import logging
import pickle
import random
import face_recognition as fr
import tqdm
from PIL import Image
import io
import time
from person import Person, FImage
import hashlib
import os
import re


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
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters, ConversationHandler, CallbackQueryHandler
import random
from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove, Update


# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

SELECTING_ACTION, IMAGE_INPUTING, UPLOAD_IMAGES, PROCESSING, \
    MARKING, DOWNLOADING_RESULTS, SKIP_PROCESSING, DONE, NAME_PERSON, SHOW_FULL_IMAGE, \
    NEXT_PERSON, NEXT_IMAGE, ENTER_NAME, HAS_MESSAGE = map(
        chr, range(14))

face_embeddings = pickle.load(open("face_embeddings.pkl", "rb"))
face_locations = pickle.load(open('face_locations.pkl', 'rb'))
faces = []

reply_keyboard = [
    ["Age", "Favourite colour"],
    ["Number of siblings", "Something else..."],
    ["Done"],
]
markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)


def has_user_preprocessed_images(user_name):
    # TODO: split into create directories and has index
    directory = f'data/{user_name}'
    if not os.path.exists(directory):
        os.makedirs(directory)

    directory_raw_photos = f'data/{user_name}/raw'
    if not os.path.exists(directory_raw_photos):
        os.makedirs(directory_raw_photos)

    directory_faces = f'data/{user_name}/faces'
    if not os.path.exists(directory_faces):
        os.makedirs(directory_faces)

    full_path = f'{directory}/index.pkl'
    return os.path.exists(full_path)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "Hi, I'm Wedding Face bot."
    )

    if has_user_preprocessed_images(update.message.chat.username):
        buttons = [[
            InlineKeyboardButton(text='Yes', callback_data=str(MARKING)),
            InlineKeyboardButton(text='No', callback_data=str(UPLOAD_IMAGES))
        ]]
        keyboard = InlineKeyboardMarkup(buttons)
        await update.message.reply_text('You have already preprocessed images. Do you want continue?', reply_markup=keyboard)
        context.user_data[HAS_MESSAGE] = True
        return SELECTING_ACTION
    else:
        await update.message.reply_text(text='Send images there. zip or jpeg(s)')
        return UPLOAD_IMAGES


async def upload_images(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    photo_file = await update.message.photo[-1].get_file()
    photo_name = photo_file.file_id

    directory = f'data/{update.message.chat.username}/raw'
    await photo_file.download_to_drive(f'{directory}/{photo_name}')

    return UPLOAD_IMAGES


async def marking_images(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    text = f'Enter name of this person or /skip if it is not a person: {random.randint(0, 1000)}'

    if context.user_data.get(HAS_MESSAGE):
        await update.callback_query.answer()
        await update.callback_query.edit_message_text(text=text)
    else:
        await update.message.reply_text(text)

    context.user_data[HAS_MESSAGE] = True

    random_embedding = None
    user_photo = None

    return ENTER_NAME


async def m_images(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    text = f'Enter name of this person or /skip if it is not a person: {random.randint(0, 1000)}'

    await update.message.reply_text(text)

    random_embedding = None
    user_photo = None

    return ENTER_NAME


async def processing_images(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    username = update.message.chat.username
    msg = await update.message.reply_text("Processing images...")

    directory = f'data/{username}/raw'
    names = os.listdir(directory)
    names = [f'{directory}/{name}' for name in names]

    index = []

    for i, name in enumerate(names):
        update_message = f"Processed {i}/{len(names)} images. Found {len(index)} faces"
        if i % 10 == 0:
            await context.bot.edit_message_text(message_id=msg.message_id, text=update_message, chat_id=context._chat_id)
        image = fr.load_image_file(name)
        locations = fr.face_locations(image)
        embeddings = fr.face_encodings(image)
        for j, fl in enumerate(locations):
            face_path = f'data/{username}/faces/{random.randint(1, 1e10)}.png'
            index.append((name, face_path, embeddings[j], locations[j]))
            img = Image.fromarray(image[fl[0]:fl[2],
                                        fl[3]:fl[1], :])
            img.save(face_path)

    # with open(f'data/{username}/index.pkl', 'wb') as f:
    #     pickle.dump(index, f)

    context.user_data[HAS_MESSAGE] = False

    return MARKING


async def downloading_results(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    time.sleep(1)
    # await update.callback_query.edit_message_text(text='Downloading results...')
    msg = await update.message.reply_text("Downloading results...")
    return DONE


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /help is issued."""
    await update.message.reply_text("Help!")


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


async def show_full_image(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    pass


async def get_next_image(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.callback_query.answer()
    buttons = [[
        InlineKeyboardButton(text='Yes', callback_data=str(NEXT_IMAGE)),
        InlineKeyboardButton(text='No', callback_data=str(NEXT_IMAGE)),
        InlineKeyboardButton(text='Add new person',
                             callback_data=str(NEXT_PERSON)),
    ]]
    keyboard = InlineKeyboardMarkup(buttons)
    await update.callback_query.edit_message_text(text=f'Is that him/her? {random.randint(0, 1000)}', reply_markup=keyboard)

    return NEXT_IMAGE


async def create_person(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    buttons = [[
        InlineKeyboardButton(text='Yes', callback_data=str(NEXT_IMAGE)),
        InlineKeyboardButton(text='No', callback_data=str(NEXT_IMAGE)),
        InlineKeyboardButton(text='Add new person',
                             callback_data=str(NEXT_PERSON)),
    ]]
    keyboard = InlineKeyboardMarkup(buttons)
    await update.message.reply_text('Is that him/her?', reply_markup=keyboard)
    return NEXT_IMAGE


def main() -> None:
    """Run the bot."""
    # Create the Application and pass it your bot's token.

    application = Application.builder().token(
        dotenv_values(".env")['BOT_TOKEN']).build()

    marking_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(
            marking_images, pattern="^" + str(MARKING) + "$")],
        states={
            ENTER_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, create_person), CommandHandler('skip', m_images)],
            SHOW_FULL_IMAGE: [CallbackQueryHandler(
                show_full_image, pattern='^' + str(SHOW_FULL_IMAGE) + '$'
            )],
            NEXT_IMAGE: [CallbackQueryHandler(
                get_next_image, pattern='^' + str(NEXT_IMAGE) + '$'
            ), CallbackQueryHandler(
                marking_images, pattern="^" + str(NEXT_PERSON) + "$")],
        },
        fallbacks=[MessageHandler(filters.Regex("^Done$"), done)],
        map_to_parent={
            DONE: SELECTING_ACTION
        }
    )

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            UPLOAD_IMAGES: [
                MessageHandler(
                    filters.PHOTO, upload_images), CommandHandler('done', processing_images), marking_conv
            ],
            SELECTING_ACTION: [marking_conv],
            MARKING: [marking_conv],
            DONE: [
                CallbackQueryHandler(done, pattern="^" + str(DONE) + "$")
            ]
        },
        fallbacks=[MessageHandler(filters.Regex("^Done$"), done)],
    )
    application.add_handler(conv_handler)

    # Run the bot until the user presses Ctrl-C
    application.run_polling()


if __name__ == "__main__":
    main()
