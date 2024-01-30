# DNS Ping Monitor

## Overview
DNS Ping Monitor is a system tray application for monitoring the availability of a DNS server by periodically sending ping requests. It is developed using Python and PyQt5, offering an intuitive interface for configuration and real-time status updates.

## Features
- **DNS Monitoring:** Automatically pings a specified DNS server to check its availability.
- **Customizable Settings:** Users can set the DNS server address and define the ping interval.
- **Logging:** Logs all operations and errors, with a feature to backup logs if they contain errors.
- **Single Instance:** Prevents multiple instances of the application from running simultaneously.
- **System Tray Icon:** Accessible via a system tray icon, providing easy access to configuration and exit options.
- **Error Handling:** Robust handling and logging of unhandled exceptions.

## Requirements
- Python 3.x
- PyQt5

## Installation
Clone the repository or download the source code:
```
git clone https://github.com/your-repository/dns-ping-monitor.git
```
Install the required dependencies:
```
pip install PyQt5
```

## Usage
Run the application:
```
python dns_ping_monitor.py
```
Right-click the system tray icon to access the configuration menu or exit the application.

## Configuration
The configuration dialog allows setting the following:
- DNS Server: Choose from saved, recent, or enter a custom DNS/IPv4 address.
- Ping Interval: Set the frequency of the ping requests in minutes.
- Save and manage custom DNS addresses for quick access.

## License
This project is licensed under the [MIT License](LICENSE).

## Contributing
Contributions are welcome. Please open an issue or submit a pull request with your changes.

## Support
If you encounter any issues or have any questions, please open an issue in the GitHub repository.
