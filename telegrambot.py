import cv2
import os
from telegram import Update, KeyboardButton, ReplyKeyboardMarkup
from telegram.ext import Application, ContextTypes, CommandHandler, MessageHandler, filters

from dotenv import load_dotenv

load_dotenv()  # take environment variables from .env
TELEGRAM_TOKEN=os.getenv("TELEGRAM_TOKEN")

async def set_command(application: Application) -> None:
    await application.bot.set_my_commands([
        ('picture', 'Get a picture of the room'),
        ('people', 'Get the number of the people in the room'),
        ('temperature', 'Get room temperature'),
        ('offset', 'Get/Set temperature offset'),
        ('minimum', 'Get/Set the minimum temperature'),
        ('maximum', 'Get/Set the maximum temperature'),
    ])

class TelegramBot:
    def __init__(self, my_camera, my_led, my_sensor, temperature):
        self.application = Application.builder().token(TELEGRAM_TOKEN).build()
        self.my_camera = my_camera
        self.my_led = my_led
        self.my_sensor = my_sensor
        self.temperature = temperature # temperature dictionary passed by reference

        start_handler = CommandHandler(['start','help'], self.start)
        start_message_handler = MessageHandler(filters.TEXT & (~ filters.COMMAND), self.start_message)
        self.application.add_handler(start_handler)
        self.application.add_handler(start_message_handler)

        get_picture_handler = CommandHandler('picture', self.get_picture)
        self.application.add_handler(get_picture_handler)

        get_people_handler = CommandHandler('people', self.get_people)
        self.application.add_handler(get_people_handler)

        get_temperature_handler = CommandHandler('temperature', self.get_temperature)
        self.application.add_handler(get_temperature_handler)

        set_offset_handler = CommandHandler('offset', self.set_offset)
        self.application.add_handler(set_offset_handler)

        set_maximum_handler = CommandHandler('maximum', self.set_maximum)
        self.application.add_handler(set_maximum_handler)

        set_minimum_handler = CommandHandler('minimum', self.set_minimum)
        self.application.add_handler(set_minimum_handler)

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        buttons = [[KeyboardButton('Temperature'), KeyboardButton('People')],
                   [KeyboardButton('Picture')]]
        room = context.bot_data['room']
        await context.bot.send_message(chat_id=update.effective_chat.id,
                                       text=f"I'm monitoring temperature in room {room}",
                                       reply_markup=ReplyKeyboardMarkup(buttons))

    async def start_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if 'Temperature' in update.message.text:
            await self.get_temperature(update, context)
        elif 'People' in update.message.text:
            await self.get_people(update, context)
        elif 'Picture' in update.message.text:
            await self.get_picture(update, context)

    def _to_bytes(self, image):
        is_success, im_buf_arr = cv2.imencode(".jpg", image)
        byte_im = im_buf_arr.tobytes()
        return byte_im

    async def get_picture(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        room = context.bot_data['room']
        annotated_image, detections = self.my_camera.get_picture()
        image_bytes = self._to_bytes(annotated_image)
        await context.bot.send_photo(chat_id=update.effective_chat.id,
                                     photo=image_bytes,
                                     caption=f"Room {room}")

    async def get_people(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        annotated_image, detections = self.my_camera.get_picture()
        await context.bot.send_message(chat_id=update.effective_chat.id,
                                       text=detections)

    async def get_temperature(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        room = context.bot_data['room']
        my_temperature = self.my_sensor.read('temperature')
        if my_temperature is not None:
            my_temperature += self.temperature['offset']
            text = 'Temperature in room {0} is: {1:0.1f}C'.format(room, my_temperature)
        else:
            text = 'No sensor found'
        await context.bot.send_message(chat_id=update.effective_chat.id,
                                       text=text)

    async def set_offset(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        result = [arg for arg in context.args if arg.lstrip('-+').isdigit()]  # may be negative
        if len(result) != 0:
            self.temperature['offset'] = int(result[0])
        await context.bot.send_message(chat_id=update.effective_chat.id,
                                       text=f"Current offset is: {self.temperature['offset']}.")

    async def set_minimum(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        result = [arg for arg in context.args if arg.lstrip('-+').isdigit()]  # may be negative
        if len(result) != 0:
            self.temperature['min'] = int(result[0])
        await context.bot.send_message(chat_id=update.effective_chat.id,
                                       text=f"Current minimum temperature is: {self.temperature['min']}.")

    async def set_maximum(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        result = [arg for arg in context.args if arg.lstrip('-+').isdigit()]  # may be negative
        if len(result) != 0:
            self.temperature['max'] = int(result[0])
        await context.bot.send_message(chat_id=update.effective_chat.id,
                                       text=f"Current maximum temperature is: {self.temperature['max']}.")
