import os
from dotenv import load_dotenv
from influxdb import InfluxDBClient

load_dotenv()  # take environment variables from .env

INFLUXDB_ADDRESS = os.getenv("INFLUXDB_ADDRESS")
INFLUXDB_USER = os.getenv("INFLUXDB_USER")
INFLUXDB_PASSWORD = os.getenv("INFLUXDB_PASSWORD")
INFLUXDB_DATABASE = os.getenv("INFLUXDB_DATABASE")

class DB:
    def __init__(self):
        super(DB, self).__init__()
        self.influxdb_client = InfluxDBClient(host=INFLUXDB_ADDRESS, port=8086, database=INFLUXDB_DATABASE,
                                              username=INFLUXDB_USER, password=INFLUXDB_PASSWORD)

    def write_sensor_data(self, location, measurement, value):
        json_body = [
            {
                "measurement": measurement,
                "tags": {
                    "location": location,
                },
                "fields": {
                    "value": value
                }
            }
        ]
        self.influxdb_client.write_points(json_body)