#!/usr/bin/python3
import interrupt_client, wind_direction, HTU21D, bmp085, tgs260#0, ds18b20_therm

pressure = bmp085.BMP085()
#temp_probe = ds18b20_therm.DS18B20()
air_qual = tgs2600.TGS2600(adc_channel = 0)
humidity = HTU21D.HTU21D()
wind_dir = wind_direction.wind_direction(adc_channel = 0, config_file="wind_direction.json")
interrupts = interrupt_client.interrupt_client(port = 49501)

wind_average = wind_dir.get_value(5)

print("Reading values...")
#print(temp_probe.temp())
print((humidity.read_temperature()), (air_qual.get_value()), (pressure.get_pressure()), (humidity.read_humidity()), wind_average, (interrupts.get_wind()), (interrupts.get_wind_gust()), (interrupts.get_rain()))
print("done")

interrupts.reset()
