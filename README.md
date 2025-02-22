# Raspberry Pi Weather Station with MQTT

## Table of Contents

  * [About](#about)
  * [Feature List](#feature-list)
  * [Planned Features](#planned-features)
  * [Hardware List](#hardware-list)
  * [MQTT Configuration](#mqtt-configuration)
  * [Running Script When Pi Starts](#running-script-when-pi-starts)
  * [Home Assistant Implementation](#home-assistant-implementation)

## Sensors

The following sensors are broadcast as a JSON dict over MQTT, and displayed in a Home Assistant dashboard:

- Local Ambient Temp
- Local Ground Temp
- Local Wind Speed
- Local Wind Gust
- Local Air Quality
- Local Rainfall
- Local Wind Direction
- Local Humidity
- Local Pressure
- System CPU temperature

## Hardware List

Uses the official Raspberry PI Foundation Oracle based hardware (https://projects.raspberrypi.org/en/projects/oracle-raspberrypi-weather-station/0)

## Setup

```sh wsinstall.sh```

Test with

```
sudo python log_all_sensors.py
```

## MQTT Configuration

The MQTT configuration requires an environment file for username, password, host ip, and port. You can hardcode these in if you really want by finding the MQTT constant variables in weather_station.py and defining them there. To use the environment variables, start by installing the dotenv library by SSHing into your raspi and typing the following:

```
sudo pip3 install -U python-dotenv
```

In your project folder create a new file ".env". This is a per-project file, so you should only need one. Hence, it doesn't need a name, simply the extension will be fine. In this file paste the following:

```
MQTT_USER="username"
MQTT_PASSWORD="password"
MQTT_HOST="host ip"
MQTT_PORT=1883
```

Replace username and password with the credentials for your MQTT server. Add your MQTT host IP. The default port is 1883, so if yours is different change it here.

## Running Script When Pi Starts

**NOTE:** I strongly advise you to run the main weather_station.py program in your IDE or through SSH before you start trying to get the program to launch when the raspi boots. You will be able to diagnose any problems or error messages much easier than taking guesses as to why the raspi isn't launching the main python file. Trust me: it will save you a lot of time and headache.

These were the steps I had to take so the weather station script will run on boot. SSH into your raspberry pi and type the following to create a new system service:

```
sudo nano /etc/systemd/system/weatherstation.service
```

Paste this into the new file:

```
[Unit]
Description=Weather Station Service
Wants=systemd-networkd-wait-online.service
After=systemd-networkd-wait-online.service

[Service]
Type=simple
ExecStartPre=/bin/sh -c 'until ping -c1 google.com; do sleep 1; done;'
ExecStart=/usr/bin/python3 /home/pi/weather-station/weather_station.py > /home/pi/weather-station/logs/log.txt 2>$1

[Install]
WantedBy=multi-user.target
```

**NOTICE:** This program uses python3, so it's explicitly called within the ExecStart command. Also note the absolute file path to the weather station main program, along with absolute path to any error log output. You need to update this path to the location of your main weather station python program if it's different from mine.

TODO: The ExecStartPre command is executed because the service consistently started before the network services were active and made the program error out and fail. Having the service require a single ping out before startup ensures the pi is indeed connected to the internet before it attempts to connect via MQTT. This will most likely be changed in the future because the connection error needs to be handled at the program level, not the service level. I also don't want to rely on it connecting outside of the local network, so it should check MQTT connection status before moving to main program loop as opposed to dialing outside the network.

Systemd needs to be made aware of the configuration change. Reload the systemd daemon with the following:

```
sudo systemctl daemon-reload
```

Enable the new weatherstation service:

```
sudo systemctl enable weatherstation.service
```

The systemd-networkd-wait-online service needs to be enabled. Type this next:

```
sudo systemctl enable systemd-networkd-wait-online.service
```

Restart the pi and once the network services are loaded, the script should run and start broadcasting sensor data over MQTT. If it doesn't, type in this command to see the status of the service and diagnose from there.

```
sudo systemctl status weatherstation.service
```

## Test

## Home Assistant Implementation

To get the sensor data into Home Assistant you need to create an MQTT sensor within your Home Assistant configuration file. The best way to do this (if you haven't already) is to create a new file in your Home Assistant config folder named 'mqtt.yaml'. In your configuration.yaml file add this line:

```
mqtt: !include mqtt.yaml
```

Next, create the new file named mqtt.yaml and paste the following into it to start listening on the MQTT topics that you defined in the main weatherstation.py program:

```
sensor:
  - name: "Weather Station"
    state_topic: "raspberry/ws/status"
    json_attributes_topic: "raspberry/ws/sensors"
```

This will create a new sensor in Home Assistant with the name "sensor.weather_station".

**NOTE:** You need to make sure the state_topic and the json_attributes_topic in this sensor match the topics in the main weatherstation.py file on the raspberry pi. If they don't match, Home Assistant won't be able to 'hear' the broadcast because it's listening on the wrong topics.

Next, you need to break out the main sensor.weather_station attributes into their own sensors so they can be displayed on a dashboard that you create. To do this, create a new file named "template.yaml" (if you don't already have one) and add the following line to your configuration.yaml:

```
template: !include template.yaml
```

In the new template.yaml file you've created paste the following:

```
# Weather Station

# Weather Station

- sensor:
    - name: "Local Ambient Temp"
      state: "{{ state_attr('sensor.weather_station', 'ambient_temp') | float | round(1) }}"
      icon: mdi:thermometer
      unit_of_measurement: °C

    - name: "Local Ground Temp"
      state: "{{ state_attr('sensor.weather_station', 'ground_temp') | float | round(1) }}"
      icon: mdi:thermometer
      unit_of_measurement: °C

    - name: "Local Wind Speed"
      state: "{{ state_attr('sensor.weather_station', 'wind_speed') | float }}"
      icon: mdi:weather-windy
      unit_of_measurement: mph

    - name: "Local Wind Gust"
      state: "{{ state_attr('sensor.weather_station', 'wind_gust') | float }}"
      icon: mdi:weather-windy
      unit_of_measurement: mph

    - name: "Local Air Quality"
      state: "{{ state_attr('sensor.weather_station', 'air_quality') | float }}"
      icon: mdi:weather-windy
      unit_of_measurement: aqi

    - name: "Local Rainfall"
      state: "{{ state_attr('sensor.weather_station', 'rainfall') | float }}"
      icon: mdi:water
      unit_of_measurement: 'mm'

    - name: "Local Wind Direction"
      state: "{{ state_attr('sensor.weather_station', 'wind_direction') | string }}"
      icon: mdi:compass

    - name: "Local Humidity"
      state: "{{ state_attr('sensor.weather_station', 'humidity') | float | round(1) }}"
      icon: mdi:water-percent
      unit_of_measurement: "%"

    - name: "Local Pressure"
      state: "{{ state_attr('sensor.weather_station', 'pressure') | float }}"
      icon: mdi:gauge
      unit_of_measurement: "mbar"

    - name: "Last Message"
      state: "{{ state_attr('sensor.weather_station', 'last_message') }}"
      icon: mdi:clock

    - name: "WX CPU Temp"
      state: "{{ state_attr('sensor.weather_station', 'cpu_temp') }}"
      icon: mdi:thermometer
      unit_of_measurement: °C

    - name: "WX Uptime"
      state: "{{ state_attr('sensor.weather_station', 'system_uptime') }}"
      icon: mdi:sort-clock-descending
      unit_of_measurement: ""
```

This is what gives you all the individual sensors that can be used as entities within a Home Assistant dashboard. The name of each is how you find the sensor name. For example, for the last sensor in the template, WX Uptime, this data will be in the "sensor.wx_uptime" sensor. For WX CPU Temp, you'll be able to display it with "sensor.wx_cpu_temp", etc etc.
