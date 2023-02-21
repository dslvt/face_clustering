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
    NEXT_PERSON, NEXT_IMAGE, ENTER_NAME = map(
        chr, range(13))

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


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "Hi, I'm Wedding Face bot."
    )

    if has_user_preprocessed_images():
        buttons = [[
            InlineKeyboardButton(text='Yes', callback_data=str(MARKING)),
            InlineKeyboardButton(text='No', callback_data=str(UPLOAD_IMAGES))
        ]]
        keyboard = InlineKeyboardMarkup(buttons)
        await update.message.reply_text('You have already preprocessed images. Do you want continue?', reply_markup=keyboard)
    return SELECTING_ACTION


async def upload_images(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.callback_query.answer()
    await update.callback_query.edit_message_text(text='Send images there')

    return PROCESSING


async def marking_images(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    text = 'Enter name of this person:'
    print('helllo')

    await update.callback_query.answer()
    await update.callback_query.edit_message_text(text=text)

    random_embedding = None
    user_photo = None

    return ENTER_NAME


async def processing_images(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    msg = await update.message.reply_text("Processing images...")

    names = [f'input/{str(x).zfill(4)}.JPG' for x in range(579)]

    for i, name in enumerate(names[:20]):
        update_message = f"Processed {i + 1}/{len(names)} images. Found {len(faces)} faces"
        await context.bot.edit_message_text(message_id=msg.message_id, text=update_message, chat_id=context._chat_id)
        image = fr.load_image_file(name)
        for fc in face_locations[i]:
            faces.append(image[fc[0]:fc[2], fc[3]:fc[1], :])


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


async def get_results(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text(f'')


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
    print(update.callback_query.data)
    buttons = [[
        InlineKeyboardButton(text='Yes', callback_data=str(NEXT_IMAGE)),
        InlineKeyboardButton(text='No', callback_data=str(NEXT_IMAGE)),
        InlineKeyboardButton(text='Add new person',
                             callback_data=str(NEXT_PERSON)),
    ]]
    keyboard = InlineKeyboardMarkup(buttons)
    await update.callback_query.edit_message_text(text=f'Is that him/her? {random.randint(0, 10)}', reply_markup=keyboard)


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
            ENTER_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, create_person)],
            SHOW_FULL_IMAGE: [CallbackQueryHandler(
                show_full_image, pattern='^' + str(SHOW_FULL_IMAGE) + '$'
            )],
            NEXT_IMAGE: [CallbackQueryHandler(
                get_next_image, pattern='^' + str(NEXT_IMAGE) + '$'
            )],
            NEXT_PERSON: [CallbackQueryHandler(
                marking_images, pattern="^" + str(NEXT_PERSON) + "$")]
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
                MessageHandler(filters.TEXT, upload_images)
            ],
            SELECTING_ACTION: [marking_conv,
                               CallbackQueryHandler(
                                   upload_images, pattern="^" + str(UPLOAD_IMAGES) + "$"),
                               CallbackQueryHandler(downloading_results, pattern="^" +
                                                    str(DOWNLOADING_RESULTS) + "$")],
            PROCESSING: [
                MessageHandler(
                    filters.TEXT & ~(filters.COMMAND | filters.Regex(
                        "^Done$")), processing_images
                )
            ],
            DOWNLOADING_RESULTS: [
                CallbackQueryHandler(
                    downloading_results, pattern="^" +
                    str(DOWNLOADING_RESULTS) + "$"
                )
            ],
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
