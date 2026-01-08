# pulspi_cfg.py  (user editable)

# --- UI timing ---
SPLASH_SECONDS = 2
INIT_SECONDS   = 2          # initial pause before init loop starts (optional)
INIT_TIMEOUT_S = 15         # max time to sit in init loop waiting for sensor ready

PAGE_SECONDS   = 5          # how long each page stays up
UI_TICK_MS     = 1000       # refresh rate inside each page loop (ms)

# --- Sensor polling ---
DHT_MIN_INTERVAL_MS = 2000  # DHT11 needs ~2s between reads
REQUIRED_GOOD_READS = 2     # warm-up reads needed before stats start

# --- LCD hardware ---
I2C_ADDR = 0x27
I2C_FREQ = 400000
I2C_SDA_PIN = 0
I2C_SCL_PIN = 1

# --- DHT hardware ---
DHT_PIN = 22

# --- Debug / printing ---
PRINT_SENSOR_READS = True   # prints temp/hum to serial when valid
