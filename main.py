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
RED_PIN=int(utils.read_config('led', 'Red'))
GREEN_PIN=int(utils.read_config('led', 'Green'))
YELLOW_PIN=int(utils.read_config('led', 'Yellow'))

# Get Sensor pin
SENSOR_PIN = utils.read_config('sensor', 'Pin')

# Interval and timeout settings
DETECTION_TIMEOUT = int(utils.read_config('camera','DetectionTimeout'))
DETECTION_INTERVAL = int(utils.read_config('camera','DetectionInterval'))
MEASUREMENT_INTERVAL = int(utils.read_config('sensor','MeasurementInterval'))

# offset, minimum temperature, maximum temperature
temperature = {
	'offset': 0,
	'min': MIN_TEMP,
	'max': MAX_TEMP,
}

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
    while count < DETECTION_TIMEOUT:
        picture, humans = my_camera.get_picture()
        if humans > 0:
            logging.debug(f"Number of humans: {humans}")
            people_led.on()
            alert_led.off()
            return True
        else:
            people_led.off()
        await asyncio.sleep(DETECTION_INTERVAL)
        count += DETECTION_INTERVAL
    logging.info(f"No people in the room for {count}s")
    alert_led.on()
    await utils.send_message(application, f"ALERT: no people in room {ROOM}.")
    return False


async def sensor_task(application, warning_led, my_sensor, my_camera, influxdb):
    """
    Monitor temperature in the room.
    """
    await utils.send_message(application, f"Starting monitoring temperature in room {ROOM}")
    my_camera_task = None
    out_of_range = False
    alert_led = application.bot_data['alert_led']
    people_led = application.bot_data['people_led']
    try:
        # loop forever
        while True:
            my_temperature = my_sensor.read('temperature')
            my_humidity = my_sensor.read('humidity')
            if my_humidity is not None and my_temperature is not None:
                my_temperature += temperature['offset']
                write_data_to_db(influxdb, my_humidity, my_temperature)
                if my_temperature < temperature['min'] or my_temperature > temperature['max']:
                    if not out_of_range:
                        logging.info('Temperature is out of range.')
                        await utils.send_message(application, f"WARNING: temperature in room {ROOM} is out of range.")
                        out_of_range = True
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
                    if out_of_range:
                        logging.info('Temperature is back to normal')
                        await utils.send_message(application, f"Temperature in room {ROOM} is back to normal.")
                        out_of_range = False
            await asyncio.sleep(MEASUREMENT_INTERVAL)
    except asyncio.CancelledError as e:
        logging.error(e)
        warning_led.shutdown()


async def main():
    """
    This is the main coroutine that creates and runs several subtasks in parallel.
    """
    # Configure GPIO
    warning_led = led.Led(YELLOW_PIN)
    alert_led = led.Led(RED_PIN)
    people_led = led.Led(GREEN_PIN)

    # Init external hardware
    my_camera = camera.Camera()
    my_sensor = sensor.Sensor(SENSOR_PIN)
    influxdb = db.DB()

    # Init Telegram Bot
    my_telegrambot = telegrambot.TelegramBot(my_camera, warning_led, my_sensor, temperature)
    application = my_telegrambot.application
    application.bot_data['room'] = ROOM
    application.bot_data['alert_led'] = alert_led
    application.bot_data['people_led'] = people_led

    await application.initialize()
    await application.start()
    # change the list of the bot’s commands
    await telegrambot.set_command(application)
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
