import network
import socket
import time
import machine
import ujson

# Wi-Fi credentials
SSID = "your-SSID"
PASSWORD = "your-PASSWORD"

# Ping target
PING_TARGET = "10.0.0.65"

# LED setup
led = machine.Pin("LED", machine.Pin.OUT)

# Blink LED to test
while True:
    led.toggle()
    time.sleep(2)
    led.toggle()
    time.sleep(0.5)

# Connect to Wi-Fi
wlan = network.WLAN(network.STA_IF)
wlan.active(True)
wlan.connect(SSID, PASSWORD)

print("Connecting to Wi-Fi...")
while not wlan.isconnected() and wlan.status() >= 0:
    time.sleep(1)

print("Connected:", wlan.ifconfig())

# Function to check network status
def get_network_status():
    if wlan.isconnected():
        return {
            "status": "Connected",
            "ip": wlan.ifconfig()[0],
            "subnet": wlan.ifconfig()[1],
            "gateway": wlan.ifconfig()[2],
            "dns": wlan.ifconfig()[3]
        }
    else:
        return {"status": "Disconnected"}

# Function to ping a target
def ping(host):
    try:
        addr = socket.getaddrinfo(host, 80)[0][-1][0]  # Resolve IP
        start = time.ticks_ms()
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(1)
        result = s.connect_ex((addr, 80))
        s.close()
        if result == 0:
            latency = time.ticks_diff(time.ticks_ms(), start)
            return f"Ping success: {latency}ms"
        else:
            return "Ping failed"
    except Exception as e:
        return f"Ping error: {str(e)}"

# LED pulsing effect
def pulse_led():
    for i in range(0, 65535, 500):  # Fade in
        led.duty_u16(i)
        time.sleep(0.01)
    for i in range(65535, 0, -500):  # Fade out
        led.duty_u16(i)
        time.sleep(0.01)

# Start a simple web server
def start_server():
    addr = socket.getaddrinfo("0.0.0.0", 80)[0][-1]
    
    # Attempt to create and bind the socket
    s = None
    try:
        s = socket.socket()
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)  # Allow reuse of address
        s.bind(addr)
        s.listen(5)
        print("Web server running on", addr)

    except OSError as e:
        if e.args[0] == 98:  # EADDRINUSE error
            print("Port 80 already in use, force closing previous instance...")
            if s:
                s.close()  # Close the socket
            time.sleep(1)  # Short delay before retrying
            return start_server()  # Restart the server

    while True:
        pulse_led()  # Run LED pulsing

        cl, addr = s.accept()
        print("Client connected from", addr)
        
        request = cl.recv(1024)
        print("Request:", request)

        network_status = get_network_status()
        ping_result = ping(PING_TARGET)

        response = ujson.dumps({"network": network_status, "ping": ping_result})
        
        cl.send("HTTP/1.1 200 OK\r\nContent-Type: application/json\r\n\r\n")
        cl.send(response)
        cl.close()

# Run the web server
start_server()
