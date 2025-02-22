#!/bin/bash

echo 'Please ensure your Weather Station HAT is connected to your Raspberry Pi, with the battery installed.'
echo 'Please ensure your Raspberry Pi is connected to the Internet'

## Check ready to start
echo "Do you want to install the Weather Station software?"
read -r -p "$1 [y/N] " response < /dev/tty
if [[ $response =~ ^(yes|y|Y)$ ]]; then
    echo "Starting"
else
    echo "Exiting"
    exit
fi

echo 'Updating Raspbian'
## Update and upgrade - especially important for old NOOBS installs and I2C integration
sudo apt-get update && sudo apt-get upgrade -y

# These pacakages needed if using Stretch-lite image

sudo apt-get install python3-smbus git python3-pip -y
sudo pip3 install RPi.GPIO
##E nable I2C
echo ' Enabling I2C'
sudo raspi-config nonint do_i2c 0

## Update config files.
echo "dtoverlay=w1-gpio" | sudo tee -a /boot/config.txt
echo "dtoverlay=pcf8523-rtc" | sudo tee -a /boot/config.txt
echo "i2c-dev" | sudo tee -a /etc/modules
echo "w1-therm" | sudo tee -a /etc/modules

echo 'Setting up RTC'
## Check the RTC exists
if ls /dev/rtc** 1> /dev/null 2>&1; then
    echo "RTC found"
else
    echo "No RTC found - please follow manual setup to Troubleshoot."
    exit 1
fi

## Initialise RTC with correct time
echo "The current date and time set is:"
date
read -r -p "Is this correct [y/N] " response2 < /dev/tty
response2=${response2,,}    # tolower
if [[ $response2 =~ ^(yes|y)$ ]]; then
    sudo hwclock -w
else
    read -p "Enter todays date and time (yyyy-mm-dd hh:mm:ss): "  user_date < /dev/tty
    sudo hwclock --set --date="$user_date" --utc #set hardware clock
fi

#update system clock
sudo hwclock -s

#Update hwclock config
sudo perl -pi -e 's/systz/hctosys/g' /lib/udev/hwclock-set

#Remove hwc package
sudo update-rc.d fake-hwclock remove
sudo apt-get remove fake-hwclock -y

echo 'Installing required packages'
## Install com tools
sudo apt-get install i2c-tools python-smbus telnet -y

## Get the weather station python files
cd ~
git clone https://github.com/raspberrypi/weather-station.git

## Setup rc.local to start weatherstaion daemon
sudo sed -i '/exit 0/d' /etc/rc.local
echo 'echo "Starting Weather Station daemon..."' | sudo tee -a /etc/rc.local
echo '/home/pi/weather-station/interrupt_daemon.py start' | sudo tee -a /etc/rc.local
echo 'exit 0' | sudo tee -a /etc/rc.local

## Alter crontab for periodic uploads
crontab < crontab.save

echo "All done - rebooting"
sudo reboot
