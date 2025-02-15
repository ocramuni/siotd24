import os

from dotenv import load_dotenv
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler

load_dotenv()  # take environment variables from .env
TELEGRAM_TOKEN=os.getenv("TELEGRAM_TOKEN")

async def hello(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print(update.effective_chat.id)
    await context.bot.send_message(chat_id=update.effective_chat.id,
                                   text="Hello World!")

def main():
    application = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    hello_handler = CommandHandler('hello', hello)
    application.add_handler(hello_handler)

    # Run the bot until the user presses Ctrl-C
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()