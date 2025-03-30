import os
import utime
import network
import socket
import machine
import config
import uping
from machine import Pin, I2C
from pico_i2c_lcd import I2cLcd

# LCD Setup
I2C_ADDR = 0x27  # Adjust if needed
I2C_SDA = Pin(0)  # Adjust for your setup
I2C_SCL = Pin(1)
i2c = I2C(0, sda=I2C_SDA, scl=I2C_SCL, freq=400000)
lcd = I2cLcd(i2c, I2C_ADDR, 2, 16)


# Network Setup
wlan = network.WLAN(network.STA_IF)
wlan.active(True)
wlan.connect(config.SSID, config.PASSWORD)

# Wait for connection
while not wlan.isconnected():
    utime.sleep(1)

print(f"Network Connected: {wlan.ifconfig()[0]}")

# Uptime Counter
start_time = utime.ticks_ms()

###### Obviously a program that says it will monitor uptime must in fact monitor uptime  ######
### Side note, i need to work on this for more accuracy as it currently only displays the
### time that the script (the monitor) has been running for. This does not reflect system
### uptime at this moment in time. I will impliment a DS3231 RTC for this later on, but this works for dev
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
        if response is not None:
            print(f"Ping to {ip}: Online")
            return "Online"
    except:
        pass
    print(f"Ping to {ip}: Offline")
    return "Offline"

### Current server config and firewall rules prevent establishing the TCP socket required by the following code block
#### Will be adding this to the "will fix" list but not urgent since uping works fine. Sockets may prove more effiencient, though
'''
def ping(ip=config.TARGET):
    try:
        addr = socket.getaddrinfo(ip, 1)[0][-1]
        s = socket.socket()
        s.settimeout(1)
        s.connect(addr)
        s.close()
        print(f"Ping to {ip}: Online")
        return "Online"
    except:
        print(f"Ping to {ip}: Offline")
        return "Offline"
'''
##############################################################################################################
##############################################################################################################
    
    
###### And now we get to actually do something different than define a bunch of functions!!! ######
while True:
    uptime = get_uptime()
    status = ping()
    
    lcd.clear()
    lcd.putstr(f"Uptime: {uptime}\n")
    lcd.putstr(f"Ping: {status}")
    
    utime.sleep(2)  # Refresh every 5 seconds
