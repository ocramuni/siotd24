import asyncio
import logging
import sensor

import db
import camera
import led
import telegrambot
import utils

ROOM=utils.read_config('DEFAULT', 'Room')
MAX_TEMP=int(utils.read_config('temperature', 'Max'))
MIN_TEMP=int(utils.read_config('temperature', 'Min'))

# Get Led pin
RED=int(utils.read_config('led','Red'))
GREEN=int(utils.read_config('led','Green'))
YELLOW=int(utils.read_config('led','Yellow'))

# Get Sensor pin
SENSOR_PIN = utils.read_config('sensor', 'Pin')

offset = [0]

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO)

def write_data_to_db(influxdb, my_humidity, my_temperature):
    """
    Save humidity and temperature into an InfluxDB database.
    """
    influxdb.write_sensor_data(f"{ROOM}", 'humidity', my_humidity)
    influxdb.write_sensor_data(f"{ROOM}", 'temperature', my_temperature)


async def camera_task(application, my_camera):
    """
    Detect human presence in the room.
    """
    alert_led = application.bot_data['alert_led']
    people_led = application.bot_data['people_led']
    count = 0
    while count < 60:
        picture, humans = my_camera.get_picture()
        if humans > 0:
            logging.debug(f"Number of humans: {humans}")
            people_led.on()
            alert_led.off()
            return True
        else:
            people_led.off()
        await asyncio.sleep(10)
        count += 10
    logging.info(f"No people in the room for {count}s")
    alert_led.on()
    return False


async def sensor_task(application, warning_led, my_sensor, my_camera, influxdb):
    """
    Monitor temperature in the room.
    """
    await utils.send_message(application, f"Starting monitoring temperature in room {ROOM}")
    my_camera_task = None
    alert_led = application.bot_data['alert_led']
    people_led = application.bot_data['people_led']
    try:
        # loop forever
        while True:
            my_temperature = my_sensor.read('temperature')
            my_humidity = my_sensor.read('humidity')
            if my_humidity is not None and my_temperature is not None:
                my_temperature += offset[0]
                write_data_to_db(influxdb, my_humidity, my_temperature)
                if my_temperature < MIN_TEMP or my_temperature > MAX_TEMP:
                    logging.info('Temperature is out of range.')
                    warning_led.on()
                    if my_camera_task is None or my_camera_task.done():
                        logging.info('Starting camera task')
                        my_camera_task = application.create_task(camera_task(application, my_camera))
                else:
                    warning_led.off()
                    alert_led.off()
                    people_led.off()
                    if my_camera_task is not None:
                        logging.info('Cancel camera task')
                        my_camera_task.cancel()
                        #my_camera_task = None
                    logging.info('Temperature is back to normal')
            await asyncio.sleep(10)
    except asyncio.CancelledError as e:
        warning_led.shutdown()


async def main():
    """
    This is the main coroutine that creates and runs several subtasks in parallel.
    """
    # Configure GPIO
    warning_led = led.Led(YELLOW)
    alert_led = led.Led(RED)
    people_led = led.Led(GREEN)

    # Init external hardware
    my_camera = camera.Camera()
    my_sensor = sensor.Sensor(SENSOR_PIN)
    influxdb = db.DB()

    # Init Telegram Bot
    my_telegrambot = telegrambot.TelegramBot(my_camera, warning_led, my_sensor, offset)
    application = my_telegrambot.application
    application.bot_data['room'] = ROOM
    application.bot_data['alert_led'] = alert_led
    application.bot_data['people_led'] = people_led

    await application.initialize()
    await application.start()
    await application.updater.start_polling()
    await application.create_task(sensor_task(application, warning_led, my_sensor, my_camera, influxdb))

    # Cleanup GPIO
    warning_led.shutdown()
    alert_led.shutdown()
    people_led.shutdown()

    await application.updater.stop()
    await application.stop()
    await application.shutdown()

if __name__ == '__main__':
    # Run the main coroutine in the asyncio event loop
    asyncio.run(main())
