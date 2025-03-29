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

# Non-blocking LED blinking using Timer
def blink_led(timer):
    led.toggle()

# Set up a timer to toggle LED every 2.5 seconds
timer = machine.Timer()
timer.init(freq=0.4, mode=machine.Timer.PERIODIC, callback=blink_led)

# Connect to Wi-Fi
wlan = network.WLAN(network.STA_IF)
wlan.active(True)
wlan.connect(SSID, PASSWORD)

print("Connecting to Wi-Fi...")
timeout = 10  # Timeout after 10 seconds
while not wlan.isconnected() and timeout > 0:
    print("Waiting for connection...")
    time.sleep(1)
    timeout -= 1

if wlan.isconnected():
    print("Connected! IP address:", wlan.ifconfig()[0])
else:
    print("Failed to connect. Check credentials and signal strength.")

# Start the web server
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
        cl, addr = s.accept()
        print("Client connected from", addr)
        
        request = cl.recv(1024)
        print("Request:", request)

        network_status = {
            "status": "Connected" if wlan.isconnected() else "Disconnected",
            "ip": wlan.ifconfig()[0] if wlan.isconnected() else "N/A"
        }

        response = ujson.dumps({"network": network_status})
        
        cl.send("HTTP/1.1 200 OK\r\nContent-Type: application/json\r\n\r\n")
        cl.send(response)
        cl.close()

# Run the web server
start_server()