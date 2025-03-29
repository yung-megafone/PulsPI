# PulsPI

**PulsPI** is a Raspberry Pi Pico W-powered server uptime monitor designed to provide real-time insights into server performance and availability. With customizable monitoring intervals and performance tracking, PulsPI ensures your network stays in check.

## Features
- **Server Monitoring:** Continuously pings your server to check its uptime and responsiveness.
- **Latency Measurement:** Tracks response times to assess network performance.
- **Local Display:** Outputs real-time status to a display.
- **Future Expansion:** Planned features include SSH-based uptime checks, error detection, temperature monitoring, and automated auxiliary fan control.

## Planned Features
- ✅ Server status monitoring using ICMP ping  
- ✅ Performance estimation based on response times  
- 🚧 SSH integration for accurate uptime data  
- 🚧 Display support for real-time feedback  
- 🚧 User input via physical buttons for additional stats (error count, connections, bandwidth)  
- 🚧 Temperature-based fan control using relays and a DHT11 sensor  

## Getting Started
### Prerequisites
- **Raspberry Pi Pico W** (for Wi-Fi capability)  
- **MicroPython** installed on the Pico  
- **USB cable** for flashing and debugging  
- **Wi-Fi network**  
- Optional: DHT11 sensor, relays, and buttons for future expansions  

### Installation
1. Clone the repo:
    ```bash
    git clone https://github.com/yourusername/PulsPI.git
    cd PulsPI
    ```
2. Install **MicroPython** on your Pico W using [Thonny](https://thonny.org/) or your preferred editor.  
3. Update the script with your Wi-Fi credentials and server IP.  
4. Upload the script to the Pico.  

### Usage
- Connect your Pico W to power.  
- View the console output for real-time status updates.  
- Future updates will include display integration and external button controls.  

## Contributing
Contributions are welcome! Feel free to fork the project, create a feature branch, and submit a pull request.  

## License
This project is licensed under the **Prosperity License**.