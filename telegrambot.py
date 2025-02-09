import cv2
import os
from telegram import Update
from telegram.ext import Application, ContextTypes, CommandHandler

from dotenv import load_dotenv

load_dotenv()  # take environment variables from .env
TELEGRAM_TOKEN=os.getenv("TELEGRAM_TOKEN")

class TelegramBot:
    def __init__(self, my_camera, my_led, my_sensor, offset):
        self.application = Application.builder().token(TELEGRAM_TOKEN).post_init(self.post_init).build()
        self.my_camera = my_camera
        self.my_led = my_led
        self.my_sensor = my_sensor
        self.offset = offset # passed by reference

        start_handler = CommandHandler('start', self.start)
        self.application.add_handler(start_handler)

        led_on_handler = CommandHandler('on', self.led_on)
        self.application.add_handler(led_on_handler)

        led_off_handler = CommandHandler('off', self.led_off)
        self.application.add_handler(led_off_handler)

        get_picture_handler = CommandHandler('picture', self.get_picture)
        self.application.add_handler(get_picture_handler)

        led_status_handler = CommandHandler('status', self.led_status)
        self.application.add_handler(led_status_handler)

        get_temperature_handler = CommandHandler('temperature', self.get_temperature)
        self.application.add_handler(get_temperature_handler)

        set_offset_handler = CommandHandler('offset', self.set_offset)
        self.application.add_handler(set_offset_handler)

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await context.bot.send_message(chat_id=update.effective_chat.id,
                                       text="I'm a bot, please talk to me!")

    async def led_on(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        text = self.my_led.on()
        await context.bot.send_message(chat_id=update.effective_chat.id,
                                       text=text)

    async def led_off(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        text = self.my_led.off()
        await context.bot.send_message(chat_id=update.effective_chat.id,
                                       text=text)

    async def led_status(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        text = self.my_led.status()
        await context.bot.send_message(chat_id=update.effective_chat.id,
                                       text=text)

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

    async def get_temperature(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        room = context.bot_data['room']
        my_temperature = self.my_sensor.read('temperature')
        if my_temperature is not None:
            my_temperature += self.offset[0]
            text = 'Temperature in room {0} is: {1:0.1f}C'.format(room, my_temperature)
        else:
            text = 'No sensor found'
        await context.bot.send_message(chat_id=update.effective_chat.id,
                                       text=text)

    async def set_offset(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        #print(update.effective_chat.id)
        result = [arg for arg in context.args if arg.lstrip('-+').isdigit()]  # may be negative
        if len(result) != 0:
            self.offset[0] = int(result[0])
        await context.bot.send_message(chat_id=update.effective_chat.id,
                                       text=f"Current offset is: {self.offset[0]}.")

    async def post_init(self, application: Application) -> None:
        await application.bot.set_my_commands([
            ('picture', 'Get a picture of the room'),
            ('temperature', 'Get room temperature'),
            ('offset', 'Get/Set offset'),
            ('on', 'Turn LED on'),
            ('off', 'Turn LED off'),
            ('status', 'Get LED status'),
        ])
