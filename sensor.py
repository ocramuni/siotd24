import adafruit_dht
import board
import time

class Sensor:
    def __init__(self, pin: str):
        self.pin = getattr(board, pin)
        self.dht_device = adafruit_dht.DHT22(self.pin)

    def read(self, measurement):
        """
        Get measurement from sensor

        :param measurement: temperature, humidity
        :return: measurement
        """
        my_measurement = None
        try:
            my_measurement = getattr(self.dht_device, measurement)
        except RuntimeError as error:
            print(error.args[0])
            time.sleep(1.0)
        except Exception as error:
            self.dht_device.exit()
            print('DHT killed, restarting...')
            time.sleep(1.0)
            self.dht_device = adafruit_dht.DHT22(self.pin)
        return my_measurement
