import os
import utime
import network
import socket
import machine
import config
import uping
from machine import Pin, I2C
from pico_i2c_lcd import I2cLcd
import dht 
##############################################################################################################
##############################################################################################################


# LCD Setup
print("Initializing Display")
I2C_ADDR = 0x27
I2C_SDA = Pin(0)
I2C_SCL = Pin(1)
i2c = I2C(0, sda=I2C_SDA, scl=I2C_SCL, freq=400000)
lcd = I2cLcd(i2c, I2C_ADDR, 2, 16)
print("Display Ready")

# Network Setup
wlan = network.WLAN(network.STA_IF)
wlan.active(True)
wlan.connect(config.SSID, config.PASSWORD)
print("Network Setup Loaded")

# Wait for connection
print("Initializing Network")
while not wlan.isconnected():
    utime.sleep(1)

print(f"Network Connected: {wlan.ifconfig()[0]}")

##############################################################################################################
##############################################################################################################


###### Obviously a program that says it will monitor uptime must in fact monitor uptime  ######
### Side note, i need to work on this for more accuracy as it currently only displays the
### time that the script (the monitor) has been running for. This does not reflect system
### uptime at this moment in time. I will impliment a DS3231 RTC for this later on, but this works for dev
start_time = utime.ticks_ms()

def get_uptime():
    elapsed = utime.ticks_ms() - start_time
    seconds = elapsed // 1000
    minutes = seconds // 60
    hours = minutes // 60
    return f"{hours}:{minutes % 60}:{seconds % 60}"

##############################################################################################################
##############################################################################################################

###### Ping the target and display the latency, otherwise we will tell the user that the target is offline  ######

### This should work, but it doesnt :,(
#### Nope, it does now! Fuck mp_ping, uping is better lol
def ping(ip=config.TARGET):
    try:
        response = uping.ping(ip)
        if isinstance(response, tuple):
            # Assuming the response is a tuple, and the last value is the ping time (ms)
            ping_time = response[1]  # The second value (received) should be the ping time
            print(f"Ping to {ip}: Online, time={ping_time} ms")
            return f"Online, {ping_time} ms"
        elif response is not None:
            # In case response is not a tuple but still contains the ping time
            print(f"Ping to {ip}: Online, time={response} ms")
            return f"Online, {response} ms"
    except Exception as e:
        print(f"Ping to {ip}: Offline")
        return "Offline"

##############################################################################################################
##############################################################################################################


###### We need to initialize the DHT11 and read data from it. Being a single wire digital output, we use GPIO22 (PIN29)

### Specify in which pin the data shall be collected from (rather, where we decided to connect the sensor)
#### This is the GPIO pin number, NOT the physical pin
sensor = dht.DHT11(Pin(22))

### Read sensor values and display them on screen.
def get_temp_and_humidity():
    try:
        utime.sleep(2)
        sensor.measure()
        temp = sensor.temperature()
        hum = sensor.humidity()
        temp_f = temp * (9/5) + 32.0
        print('Temperature: %3.1f C' %temp)
        print('Temperature: %3.1f F' %temp_f)
        print('Humidity: %3.1f %%' %hum)
        return temp, hum
    except OSError as e:
        print('Failed to read sensor.')
        return None, None # Rerurns None upon failure

##############################################################################################################
##############################################################################################################

   
###### And now we get to actually do something different than define a bunch of functions!!! ######
while True:
    start_time_display = utime.time()  # Start a new timer for the display loop

# Display the current uptime and the status (with ping time) for 3 seconds (3000ms)
    while utime.time() - start_time_display < 3:
        uptime = get_uptime()
        status = ping()  # Will now include the ping time if online
    
        lcd.clear()
        lcd.move_to(0, 0)  # Move to first line
        lcd.putstr(f"Uptime: {uptime}")
        lcd.move_to(0, 1)  # Move to second line
        lcd.putstr(f"{status}")  # Now shows status and ping time

        # Refresh the display to show accurate data
        utime.sleep(1)


    # Display current temp and humid levels for 3 seconds
    start_time_display = utime.time()  # Reset the timer
    while utime.time() - start_time_display < 5:
        temperature, humidity = get_temp_and_humidity()

        lcd.clear()
        lcd.move_to(0, 0)
        lcd.putstr(f"Temp: {temperature} \xDF C")
        lcd.move_to(0, 1)
        lcd.putstr(f"Humid: {humidity} % RH")

        # Refresh the display to show accurate data
        utime.sleep(1)