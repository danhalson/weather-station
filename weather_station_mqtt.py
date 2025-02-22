from dotenv import load_dotenv
from gpiozero import CPUTemperature
from os.path import join, dirname
import time
import HTU21D
import bmp085
import wind_direction
#import ds18b20_therm
import tgs2600
import paho.mqtt.client as mqtt
import json
import os
from datetime import datetime
import interrupt_client

dotenv_path = join(dirname(__file__), '.env')
load_dotenv(dotenv_path)

# Load .env variables
MQTT_USER = os.environ.get('MQTT_USER')
MQTT_PASSWORD = os.environ.get('MQTT_PASSWORD')
MQTT_HOST = os.environ.get('MQTT_HOST')
MQTT_PORT = int(os.environ.get('MQTT_PORT'))

# Global variable definition
flag_connected = 0 # Loop flag for waiting to connect to MQTT broker

# Constant variable definition
MQTT_STATUS_TOPIC = "raspberry/ws/status"
MQTT_SENSORS_TOPIC = "raspberry/ws/sensors"

# Define variables
interval = 5 # Data collection interval in secs. 5 mins = 5 * 60 = 300

# Fudge factor for temp calibration
offset = 4.6

# MQTT
def on_connect(client, userdata, flags, rc):
    print("Connected with flags [%s] rtn code [%d]"% (flags, rc) )
    global flag_connected
    flag_connected = 1

def on_disconnect(client, userdata, rc):
    print("disconnected with rtn code [%d]"% (rc) )
    global flag_connected
    flag_connected = 0

client = mqtt.Client("WX")
client.on_connect = on_connect
client.on_disconnect = on_disconnect
client.username_pw_set(MQTT_USER, MQTT_PASSWORD)
client.connect(MQTT_HOST, MQTT_PORT)

# System Uptime
def uptime():
    t = os.popen('uptime -p').read()[:-1]
    uptime = t.replace('up ', '')
    return uptime

# Read CPU temp for future fan logic
cpu = CPUTemperature()

pressure_sensor = bmp085.BMP085()
#temp_probe = ds18b20_therm.DS18B20()
air_quality_sensor = tgs2600.TGS2600(adc_channel = 0)
humidity_sensor = HTU21D.HTU21D()
interrupts = interrupt_client.interrupt_client(port = 49501)

# Main loop
if __name__ == '__main__':
    client.loop_start()

    # Wait to receive the connected callback for MQTT
    while flag_connected == 0:
        print("Not connected. Waiting 1 second.")
        time.sleep(1)

    while True:
        start_time = time.time()

        rainfall = interrupts.get_rain()
        wind_dir = wind_direction.wind_direction(adc_channel = 0, config_file="wind_direction.json")
        wind_dir_int = wind_dir.get_value(interval)
        wind_dir_str = wind_dir.get_dir_str(adc_value = wind_dir_int)
        wind_speed = interrupts.get_wind()
#        ground_temp = temp_probe.read_temp()
        wind_gust = interrupts.get_wind_gust()

        pressure = pressure_sensor.get_pressure()
        humidity = humidity_sensor.read_temperature()
#        ambient_temp = temp_probe.read_temp()

        air_quality = air_quality_sensor.get_value()

        # Round wind_direction, humidity, pressure, ambient_temp, ground_temp, and rainfall to 1 decimals
        air_quality = round(air_quality, 1)
        wind_speed = round(wind_speed)
        wind_gust = round(wind_gust)
        humidity = round(humidity, 1)
        pressure = round(pressure, 1)
#        ambient_temp = round(ambient_temp, 2)
#        ground_temp = round(ground_temp, 2)

        cpu_temp = round(cpu.temperature, 1)

        # Record current date and time for message timestamp
        now = datetime.now()

        # Format message timestamp to mm/dd/YY H:M:S
        last_message = now.strftime("%m/%d/%Y %H:%M:%S")

        # Get current system uptime
        sys_uptime = uptime()

        # Create JSON dict for MQTT transmission
        send_msg = {
            'air_quality': air_quality,
            'wind_gust': wind_gust,
            'wind_speed': wind_speed,
            'rainfall': rainfall,
            'wind_direction': wind_dir_str,
            'humidity': humidity,
            'pressure': pressure,
#            'ambient_temp': ambient_temp,
#            'ground_temp': ground_temp,
            'last_message': last_message,
            'cpu_temp': cpu_temp,
            # 'system_uptime': sys_uptime
        }

        # Convert message to json
        payload_sensors = json.dumps(send_msg)

        # Debugging (used when testing and need to print variables)
        # print(payload_sensors)

        # Set status payload
        payload_status = "Online"

        # Publish status to mqtt
        client.publish(MQTT_STATUS_TOPIC, payload_status, qos=0)

        # Publish sensor data to mqtt
        client.publish(MQTT_SENSORS_TOPIC, payload_sensors, qos=0)

        interrupts.reset()
    client.loop_stop()
    print("Loop Stopped.")
    client.disconnect()
    print("MQTT Disconnected.")
    interrupts.reset()
