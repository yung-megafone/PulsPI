import os
import utime
import network
import socket
import machine
import config
try:
    import uping
    NET_AVAILABLE = True
except ImportError:
    uping = None
    NET_AVAILABLE = False
from machine import Pin, I2C
from pico_i2c_lcd import I2cLcd
import dht
import sys

# Non-blocking stdin support (not present on every MicroPython build)
try:
    import select
    SELECT_AVAILABLE = True
except ImportError:
    select = None
    SELECT_AVAILABLE = False

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

# Flicker-free line writer (pads/overwrites, no clears per frame)
_last_l0 = None
_last_l1 = None

def lcd_write_line(row, text):
    global _last_l0, _last_l1
    text = (text + " " * 16)[:16]  # pad/trim to 16 cols

    if row == 0:
        if text == _last_l0:
            return
        _last_l0 = text
    else:
        if text == _last_l1:
            return
        _last_l1 = text

    lcd.move_to(0, row)
    lcd.putstr(text)

def lcd_new_page():
    # Don't clear here; clearing causes visible wipe during slow operations.
    global _last_l0, _last_l1
    _last_l0 = None
    _last_l1 = None


# Network Setup (optional)
if NET_AVAILABLE:
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    wlan.connect(config.SSID, config.PASSWORD)
    print("Network Setup Loaded")

    # Wait for connection (but do not block forever)
    print("Initializing Network")
    for _ in range(10):  # ~10 seconds max, then continue without net
        if wlan.isconnected():
            break
        utime.sleep(1)

    if wlan.isconnected():
        print(f"Network Connected: {wlan.ifconfig()[0]}")
    else:
        print("Network not connected - continuing without network features")
else:
    print("Network features unavalible. Skipping...")

##############################################################################################################
##############################################################################################################

# Overrides / test harness
OVERRIDE_TEMP = None
OVERRIDE_HUM = None

# Uptime override is an OFFSET (seconds), so it keeps counting
OVERRIDE_UPTIME_OFFSET_S = 0

def parse_uptime_str(s):
    """
    Accepts:
      - "H:MM:SS"  (e.g., "5:07:09", "100:07:09")
      - "H:MM"     (treated as H:MM:00)
      - "Xd HH:MM" (e.g., "3d 04:17")
      - "Xd HH:MM:SS" (optional seconds)
    Returns total seconds (int).
    """
    s = s.strip().lower()

    days = 0
    if "d" in s:
        left, right = s.split("d", 1)
        days = int(left.strip() or "0")
        s = right.strip()

    parts = [p for p in s.split(":") if p != ""]
    if len(parts) == 3:
        h = int(parts[0])
        m = int(parts[1])
        sec = int(parts[2])
    elif len(parts) == 2:
        h = int(parts[0])
        m = int(parts[1])
        sec = 0
    elif len(parts) == 1 and parts[0]:
        h = int(parts[0])
        m = 0
        sec = 0
    else:
        h = m = sec = 0

    return days * 86400 + h * 3600 + m * 60 + sec

def poll_command():
    global OVERRIDE_TEMP, OVERRIDE_HUM, OVERRIDE_UPTIME_OFFSET_S

    # If we can't do non-blocking stdin, just skip (don't freeze the program)
    if not SELECT_AVAILABLE:
        return

    if sys.stdin in select.select([sys.stdin], [], [], 0)[0]:
        cmd = sys.stdin.readline().strip()
        if not cmd:
            return

        # ---- Set overrides ----
        if cmd.startswith("temp "):
            OVERRIDE_TEMP = float(cmd.split()[1])
            print(f"[CMD] Override temp = {OVERRIDE_TEMP}")

        elif cmd.startswith("hum "):
            OVERRIDE_HUM = float(cmd.split()[1])
            print(f"[CMD] Override humidity = {OVERRIDE_HUM}")

        elif cmd.startswith("time "):
            desired_str = cmd[5:].strip()
            try:
                desired_seconds = parse_uptime_str(desired_str)
                actual_elapsed_s = (utime.ticks_ms() - start_time) // 1000
                OVERRIDE_UPTIME_OFFSET_S = int(desired_seconds - actual_elapsed_s)
                print(f"[CMD] Uptime set to '{desired_str}' (offset={OVERRIDE_UPTIME_OFFSET_S}s)")
            except Exception as e:
                print(f"[CMD] Bad time format: '{desired_str}' ({e})")

        # ---- Clear overrides ----
        elif cmd == "clear":
            OVERRIDE_TEMP = None
            OVERRIDE_HUM = None
            OVERRIDE_UPTIME_OFFSET_S = 0
            print("[CMD] All overrides cleared")

        elif cmd in ("temp clear", "clear temp"):
            OVERRIDE_TEMP = None
            print("[CMD] Temp override cleared")

        elif cmd in ("hum clear", "clear hum"):
            OVERRIDE_HUM = None
            print("[CMD] Humidity override cleared")

        elif cmd in ("time clear", "clear time"):
            OVERRIDE_UPTIME_OFFSET_S = 0
            print("[CMD] Uptime override cleared")

        # ---- Status ----
        elif cmd == "status":
            print(f"[CMD] temp={OVERRIDE_TEMP} hum={OVERRIDE_HUM} time_offset={OVERRIDE_UPTIME_OFFSET_S}s")

##############################################################################################################
##############################################################################################################

# Uptime
start_time = utime.ticks_ms()

def get_uptime():
    elapsed_s = (utime.ticks_ms() - start_time) // 1000
    total_seconds = elapsed_s + OVERRIDE_UPTIME_OFFSET_S
    if total_seconds < 0:
        total_seconds = 0

    days = total_seconds // 86400
    rem = total_seconds % 86400

    hours = rem // 3600
    rem %= 3600

    minutes = rem // 60
    seconds = rem % 60

    total_hours = total_seconds // 3600

    if total_hours >= 72:
        return f"{days}d {hours:02}:{minutes:02}"
    else:
        return f"{total_hours}:{minutes:02}:{seconds:02}"

##############################################################################################################
##############################################################################################################

# Ping
def ping(ip=config.TARGET):
    if NET_AVAILABLE:
        if not wlan.isconnected():
            return ""

        try:
            response = uping.ping(ip)
            if isinstance(response, tuple):
                ping_time = response[1]
                print(f"Ping to {ip}: Online, time={ping_time} ms")
                return f"Online, {ping_time} ms"
            elif response is not None:
                print(f"Ping to {ip}: Online, time={response} ms")
                return f"Online, {response} ms"
        except Exception as e:
            print(f"Ping to {ip}: Offline")
            return ""
    return ""

##############################################################################################################
##############################################################################################################

# DHT11
sensor = dht.DHT11(Pin(22))

# Cached sensor values (prevents UI freezing)
LAST_TEMP = None
LAST_HUM = None
LAST_READ_MS = 0
DHT_MIN_INTERVAL_MS = 2000  # DHT11 needs ~2s between valid reads

def get_temp_and_humidity():
    global OVERRIDE_TEMP, OVERRIDE_HUM
    global LAST_TEMP, LAST_HUM, LAST_READ_MS

    # Overrides for testing
    if OVERRIDE_TEMP is not None or OVERRIDE_HUM is not None:
        return (
            OVERRIDE_TEMP if OVERRIDE_TEMP is not None else 0,
            OVERRIDE_HUM if OVERRIDE_HUM is not None else 0
        )

    now = utime.ticks_ms()
    if (LAST_TEMP is not None and LAST_HUM is not None and
        utime.ticks_diff(now, LAST_READ_MS) < DHT_MIN_INTERVAL_MS):
        # Too soon to poll DHT again; return cached values immediately (no blocking)
        return LAST_TEMP, LAST_HUM

    try:
        sensor.measure()  # fast; no sleep
        temp = sensor.temperature()
        hum = sensor.humidity()
        LAST_TEMP = temp
        LAST_HUM = hum
        LAST_READ_MS = now

        temp_f = temp * (9/5) + 32.0
        print('Temperature: %3.1f C' % temp)
        print('Temperature: %3.1f F' % temp_f)
        print('Humidity: %3.1f %%' % hum)
        return temp, hum
    except OSError:
        return LAST_TEMP, LAST_HUM  # fallback to last-known-good if available

##############################################################################################################
##############################################################################################################

while True:
    # --- Uptime / ping page ---
    lcd_new_page()
    start_time_display = utime.time()
    while utime.time() - start_time_display < 5:
        poll_command()

        uptime = get_uptime()
        status = ping()

        lcd_write_line(0, f"Up: {uptime}")
        lcd_write_line(1, status if status else "")

        utime.sleep(1)

    # --- Temp/RH page ---
    lcd_new_page()
    start_time_display = utime.time()
    while utime.time() - start_time_display < 5:
        poll_command()

        temperature, humidity = get_temp_and_humidity()

        lcd_write_line(0, f"Temp: {temperature} \xDF C")
        lcd_write_line(1, f"Humid: {humidity} % RH")

        utime.sleep(1)