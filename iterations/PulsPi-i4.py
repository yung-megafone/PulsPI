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

# Min/Max stats (since boot)
MIN_TEMP = None
MAX_TEMP = None
MIN_HUM  = None
MAX_HUM  = None

def update_min_max(temp, hum):
    global MIN_TEMP, MAX_TEMP, MIN_HUM, MAX_HUM

    if temp is not None:
        if MIN_TEMP is None or temp < MIN_TEMP:
            MIN_TEMP = temp
        if MAX_TEMP is None or temp > MAX_TEMP:
            MAX_TEMP = temp

    if hum is not None:
        if MIN_HUM is None or hum < MIN_HUM:
            MIN_HUM = hum
        if MAX_HUM is None or hum > MAX_HUM:
            MAX_HUM = hum

def fmt_mm(v):
    return "--" if v is None else f"{int(v):02d}"

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

def print_help(topic=None):
    if topic == "time":
        print("Time formats:")
        print("  time H:MM:SS      (e.g. 5:07:09)")
        print("  time H:MM         (seconds = 00)")
        print("  time Xd HH:MM     (e.g. 3d 04:17)")
        print("  time Xd HH:MM:SS")
        return

    print("Commands:")
    print("  temp <n>          Override temperature (C)")
    print("  hum <n>           Override humidity (%)")
    print("  time <str>        Override uptime")
    print("  clear             Clear all overrides")
    print("  temp clear        Clear temp override")
    print("  hum clear         Clear humidity override")
    print("  time clear        Clear uptime override")
    print("  minmax clear      Reset min/max stats")
    print("  status            Print current state")
    print("  sensor            Show last data source")
    print("  help              Show this help")
    print("  help time         Show uptime formats")
    print("")
    print("Multi-command:")
    print("  hum 50 temp 30")
    print("  temp 30; hum 50; time 3d 04:17")

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

# Ping (kept for debug / future use; not displayed on screen 1 now)
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

# Debug: tracks whether last committed reading came from real sensor or overrides
SENSOR_SOURCE = "unknown"  # "sensor" | "override" | "unknown"

def commit_reading(temp, hum, now_ms, source):
    global LAST_TEMP, LAST_HUM, LAST_READ_MS, SENSOR_SOURCE
    LAST_TEMP = temp
    LAST_HUM = hum
    LAST_READ_MS = now_ms
    SENSOR_SOURCE = source
    update_min_max(temp, hum)

def get_temp_and_humidity():
    global OVERRIDE_TEMP, OVERRIDE_HUM
    global LAST_TEMP, LAST_HUM, LAST_READ_MS

    now = utime.ticks_ms()

    # Overrides behave exactly like real sensor updates
    if OVERRIDE_TEMP is not None or OVERRIDE_HUM is not None:
        temp = OVERRIDE_TEMP if OVERRIDE_TEMP is not None else LAST_TEMP
        hum  = OVERRIDE_HUM  if OVERRIDE_HUM  is not None else LAST_HUM

        # Keep display from showing None if one side was never read yet
        if temp is None:
            temp = 0
        if hum is None:
            hum = 0

        commit_reading(temp, hum, now, "override")
        return temp, hum

    # Too soon to poll DHT again; return cached values immediately (no blocking)
    if (LAST_TEMP is not None and LAST_HUM is not None and
        utime.ticks_diff(now, LAST_READ_MS) < DHT_MIN_INTERVAL_MS):
        return LAST_TEMP, LAST_HUM

    try:
        sensor.measure()  # fast; no sleep
        temp = sensor.temperature()
        hum = sensor.humidity()

        commit_reading(temp, hum, now, "sensor")

        temp_f = temp * (9/5) + 32.0
        print('Temperature: %3.1f C' % temp)
        print('Temperature: %3.1f F' % temp_f)
        print('Humidity: %3.1f %%' % hum)
        return temp, hum
    except OSError:
        return LAST_TEMP, LAST_HUM  # fallback to last-known-good if available

##############################################################################################################
##############################################################################################################

def poll_command():
    global OVERRIDE_TEMP, OVERRIDE_HUM, OVERRIDE_UPTIME_OFFSET_S
    global MIN_TEMP, MAX_TEMP, MIN_HUM, MAX_HUM
    global SENSOR_SOURCE, LAST_TEMP, LAST_HUM

    if not SELECT_AVAILABLE:
        return

    if sys.stdin in select.select([sys.stdin], [], [], 0)[0]:
        line = sys.stdin.readline().strip()
        if not line:
            return

        def handle_cmd(cmd):
            global OVERRIDE_TEMP, OVERRIDE_HUM, OVERRIDE_UPTIME_OFFSET_S
            global MIN_TEMP, MAX_TEMP, MIN_HUM, MAX_HUM
            global SENSOR_SOURCE, LAST_TEMP, LAST_HUM

            # ---- Help ----
            if cmd == "help":
                print_help()
                return
            if cmd.startswith("help "):
                parts = cmd.split()
                if len(parts) >= 2:
                    print_help(parts[1])
                else:
                    print_help()
                return

            # ---- Set overrides ----
            if cmd.startswith("temp "):
                OVERRIDE_TEMP = float(cmd.split()[1])
                print(f"[CMD] Override temp = {OVERRIDE_TEMP}")
                return

            if cmd.startswith("hum "):
                OVERRIDE_HUM = float(cmd.split()[1])
                print(f"[CMD] Override humidity = {OVERRIDE_HUM}")
                return

            if cmd.startswith("time "):
                desired_str = cmd[5:].strip()
                try:
                    desired_seconds = parse_uptime_str(desired_str)
                    actual_elapsed_s = (utime.ticks_ms() - start_time) // 1000
                    OVERRIDE_UPTIME_OFFSET_S = int(desired_seconds - actual_elapsed_s)
                    print(f"[CMD] Uptime set to '{desired_str}' (offset={OVERRIDE_UPTIME_OFFSET_S}s)")
                except Exception as e:
                    print(f"[CMD] Bad time format: '{desired_str}' ({e})")
                return

            # ---- Clear overrides ----
            if cmd == "clear":
                OVERRIDE_TEMP = None
                OVERRIDE_HUM = None
                OVERRIDE_UPTIME_OFFSET_S = 0
                print("[CMD] All overrides cleared")
                return

            if cmd in ("temp clear", "clear temp"):
                OVERRIDE_TEMP = None
                print("[CMD] Temp override cleared")
                return

            if cmd in ("hum clear", "clear hum"):
                OVERRIDE_HUM = None
                print("[CMD] Humidity override cleared")
                return

            if cmd in ("time clear", "clear time"):
                OVERRIDE_UPTIME_OFFSET_S = 0
                print("[CMD] Uptime override cleared")
                return

            # ---- Min/Max reset ----
            if cmd in ("minmax clear", "clear minmax"):
                MIN_TEMP = MAX_TEMP = MIN_HUM = MAX_HUM = None
                print("[CMD] Min/Max reset")
                return

            # ---- Sensor source debug ----
            if cmd == "sensor":
                print(f"[CMD] sensor_source={SENSOR_SOURCE} last_temp={LAST_TEMP} last_hum={LAST_HUM}")
                return

            # ---- Status ----
            if cmd == "status":
                print(f"[CMD] temp={OVERRIDE_TEMP} hum={OVERRIDE_HUM} time_offset={OVERRIDE_UPTIME_OFFSET_S}s "
                      f"minmax=T({MIN_TEMP},{MAX_TEMP}) H({MIN_HUM},{MAX_HUM}) sensor_source={SENSOR_SOURCE}")
                return

            print(f"[CMD] Unknown: {cmd}")

        # 1) Semicolon-delimited commands: "temp 43; hum 69; time 3d 04:17"
        if ";" in line:
            parts = [p.strip() for p in line.split(";") if p.strip()]
            for p in parts:
                handle_cmd(p)
            return

        # 2) Token-walk mode: "hum 69 temp 43 time 30"
        tokens = line.split()
        i = 0
        while i < len(tokens):
            t = tokens[i].lower()

            # single-word commands
            if t in ("clear", "status", "sensor", "help"):
                handle_cmd(t)
                i += 1
                continue

            # "help time"
            if t == "help" and i + 1 < len(tokens):
                handle_cmd(f"help {tokens[i+1]}")
                i += 2
                continue

            # two-word clear commands (temp clear / clear temp etc.)
            if i + 1 < len(tokens) and tokens[i+1].lower() == "clear" and t in ("temp", "hum", "time", "minmax"):
                handle_cmd(f"{t} clear")
                i += 2
                continue
            if i + 1 < len(tokens) and t == "clear" and tokens[i+1].lower() in ("temp", "hum", "time", "minmax"):
                handle_cmd(f"clear {tokens[i+1].lower()}")
                i += 2
                continue

            # key/value commands (temp 43 / hum 69 / time 30)
            if t in ("temp", "hum", "time") and i + 1 < len(tokens):
                handle_cmd(f"{t} {tokens[i+1]}")
                i += 2
                continue

            # fallback: treat the rest as one command (lets "time 3d 04:17" work if typed alone)
            handle_cmd(" ".join(tokens[i:]))
            break

##############################################################################################################
##############################################################################################################

while True:
    # --- Uptime / stats page ---
    lcd_new_page()
    start_time_display = utime.time()
    while utime.time() - start_time_display < 5:
        poll_command()

        uptime = get_uptime()

        # Ensure min/max gets populated even if user stares at page 1 forever
        # (non-blocking due to caching/rate-limit)
        get_temp_and_humidity()

        lcd_write_line(0, f"Up: {uptime}")

        # T xx/XX  H xx/XX (fits in 16)
        stats_line = f"T {fmt_mm(MIN_TEMP)}/{fmt_mm(MAX_TEMP)} H {fmt_mm(MIN_HUM)}/{fmt_mm(MAX_HUM)}"
        lcd_write_line(1, stats_line)

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