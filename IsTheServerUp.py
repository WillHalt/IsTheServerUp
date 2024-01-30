import logging
import sys
import json
import subprocess
from PyQt5.QtWidgets import QApplication, QSystemTrayIcon, QMenu, QAction, QDialog, QVBoxLayout, QLabel, QPushButton, QComboBox, QLineEdit, QMessageBox
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import QTimer
import os
import socket
import datetime

# Function to check and backup the old log file if it contains errors
def backup_old_log_if_needed():
    log_filename = 'application_log.log'
    error_log_filename = 'error_log.log'
    if os.path.exists(log_filename):
        # Check if the error log is not empty
        if os.path.exists(error_log_filename) and os.path.getsize(error_log_filename) > 0:
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_filename = f'application_log_backup_{timestamp}.log'
            os.rename(log_filename, backup_filename)
        else:
            # Clear the log file if no errors were logged
            open(log_filename, 'w').close()

# Call the function to backup old log file
backup_old_log_if_needed()

# Initialize logging
logging.basicConfig(filename='application_log.log', level=logging.INFO, format='%(asctime)s: %(levelname)s: %(message)s')

# Add a function to check if another instance is already running
def is_another_instance_running():
    # Create a TCP/IP socket
    try:
        global socket_instance
        socket_instance = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # Try to bind to the address; this will fail if another instance is running
        socket_instance.bind(('127.0.0.1', 12345))
    except socket.error:
        return True
    return False

# Additional logger for crash reporting
def handle_exception(exc_type, exc_value, exc_traceback):
    logging.critical("Unhandled exception", exc_info=(exc_type, exc_value, exc_traceback))

sys.excepthook = handle_exception

# Constants for the application
CONFIG_FILE = 'config.json'
DEFAULT_DNS = '8.8.8.8'
DEFAULT_INTERVAL = 5  # in minutes
MAX_SAVED_DNS = 5  # Maximum number of custom DNS addresses to save
MAX_RECENT_DNS = 3 # Maximum number of recent DNS addresses to save

# Function to ping DNS server
def ping_dns(server):
    try:
        response = subprocess.check_output(["ping", "-n", "1", server], stderr=subprocess.STDOUT, shell=True)
        logging.info(f'Ping to {server} successful.')
        return True
    except subprocess.CalledProcessError:
        logging.warning(f'Ping to {server} failed.')
        return False

# Function to load configuration
def load_config():
    try:
        with open(CONFIG_FILE, 'r') as file:
            config = json.load(file)
    except FileNotFoundError:
        config = {'dns': DEFAULT_DNS, 'interval': DEFAULT_INTERVAL, 'custom_dns': [], 'recent_dns': []}

    # Ensure 'custom_dns' key exists
    config.setdefault('custom_dns', [])
    config.setdefault('recent_dns', [])
    return config

# Function to save configuration
def save_config(config):
    with open(CONFIG_FILE, 'w') as file:
        json.dump(config, file)

# Class for the configuration UI
class ConfigDialog(QDialog):
    def __init__(self, icon, parent=None):
        super().__init__(parent)
        self.icon = icon
        self.config = load_config()
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle('Configure Ping Application')

        layout = QVBoxLayout(self)

        # DNS Server configuration
        self.dns_label = QLabel('DNS Server:', self)
        layout.addWidget(self.dns_label)

        self.dns_combo = QComboBox(self)
        self.dns_combo.addItem('Saved')
        self.dns_combo.addItems(self.config['custom_dns'])  # Saved DNS servers
        self.dns_combo.addItem('Recent')
        self.dns_combo.addItems(self.config['recent_dns'])  # Recent DNS servers
        layout.addWidget(self.dns_combo)

        # Disable 'Saved' and 'Recent' items
        self.disable_combo_items(self.dns_combo, ['Saved', 'Recent'])

        self.dns_input = QLineEdit(self)
        self.dns_input.setPlaceholderText('Custom DNS or IPv4 address')
        layout.addWidget(self.dns_input)

        # Save Address button
        self.save_button = QPushButton('Save Address', self)
        self.save_button.setToolTip('Save the current DNS address to the Saved list.')
        self.save_button.clicked.connect(self.save_dns)
        layout.addWidget(self.save_button)

        # Remove button
        self.remove_button = QPushButton('Remove Address', self)
        self.remove_button.setToolTip('Removes the current DNS address from the Saved list.')
        self.remove_button.clicked.connect(self.remove_dns)
        layout.addWidget(self.remove_button)

            # Interval configuration
        # Label
        self.interval_label = QLabel('Ping Interval (minutes):', self)
        self.interval_label.setToolTip('Sets how often this program pings the\naddress to check if it is still up.')
        layout.addWidget(self.interval_label)
        
        # Dropdown
        self.interval_combo = QComboBox(self)
        self.interval_combo.addItems(['1', '5', '10', '30'])
        self.interval_label.setToolTip('Sets how often this program pings the\naddress to check if it is still up.')
        layout.addWidget(self.interval_combo)

        # Custom Interval Input
        self.custom_interval_input = QLineEdit(self)
        self.custom_interval_input.setPlaceholderText('Custom interval (1-60)')
        layout.addWidget(self.custom_interval_input)

        # Apply button
        self.apply_button = QPushButton('Apply', self)
        self.apply_button.clicked.connect(self.save_recent)
        self.apply_button.clicked.connect(self.apply_settings)
        layout.addWidget(self.apply_button)
        
        # Shut Off button
        self.shut_off_button = QPushButton('Shut Off', self)
        self.shut_off_button.clicked.connect(self.shut_off_settings)
        layout.addWidget(self.shut_off_button)

    def disable_combo_items(self, combo_box, items_to_disable):
        for index in range(combo_box.count()):
            if combo_box.itemText(index) in items_to_disable:
                item = combo_box.model().item(index)
                item.setEnabled(False)

    def shut_off_settings(self):
        QApplication.quit()

    def save_dns(self):
        dns = self.dns_input.text().strip()

        #If the input box is empty, use the selected item from the dropdown
        if not dns:
            dns = self.dns_combo.currentText()

            #Skip if the selected item is already 'Saved'
            if dns in ['Saved']:
                return

        # Check if DNS is not already in the custom_dns list and add it
        if dns and dns not in self.config['custom_dns']:
            self.config['custom_dns'].insert(0, dns)
            self.config['custom_dns'] = self.config['custom_dns'][:MAX_SAVED_DNS]
            save_config(self.config)
            self.update_dns_combo()

    def save_recent(self):
        dns = self.dns_input.text().strip()
        if dns and dns not in self.config['recent_dns']:
            self.config['recent_dns'].insert(0, dns)
            self.config['recent_dns'] = self.config['recent_dns'][:MAX_RECENT_DNS]
            save_config(self.config)
            self.update_dns_combo()

    def remove_dns(self):
        dns = self.dns_combo.currentText()
        if dns in self.config['custom_dns']:
            self.config['custom_dns'].remove(dns)
            save_config(self.config)
            self.update_dns_combo()

    def update_dns_combo(self):
        self.dns_combo.clear()
        self.dns_combo.addItem('Saved')
        self.dns_combo.addItems(self.config['custom_dns'])
        self.dns_combo.addItem('Recent')
        self.dns_combo.addItems(self.config['recent_dns'])  # Recent DNS servers
        self.disable_combo_items(self.dns_combo, ['Saved', 'Recent'])

    def apply_settings(self):
        dns = self.dns_input.text().strip() or self.dns_combo.currentText()
 
        # Check if custom interval is provided
        custom_interval = self.custom_interval_input.text().strip()
        if custom_interval:
            try:
                custom_interval = int(custom_interval)
                if 1 <= custom_interval <= 60:
                    interval = custom_interval
                else:
                    QMessageBox.warning(self, 'Invalid Interval', 'Interval must be a whole number between 1 and 60.')
                    return
            except ValueError:
                QMessageBox.warning(self, 'Invalid Interval', 'Interval must be a whole number between 1 and 60.')
                return
        else:
            interval = int(self.interval_combo.currentText())
        
        # Update custom DNS list
        custom_dns = self.config.get('custom_dns', [])

        #Update recent DNS list
        recent_dns = self.config.get('recent_dns', [])
        if dns not in recent_dns:
            recent_dns.insert(0, dns)
            recent_dns = recent_dns[:MAX_RECENT_DNS]

        config = {'dns': dns, 'interval': interval, 'custom_dns': custom_dns, 'recent_dns': recent_dns}
        save_config(config)
        self.icon.update_config()
        logging.info('Configuration updated.')
        self.close()
        
    # Overriding the closeEvent
    def closeEvent(self, event):
        event.ignore()
        self.hide()
        
# Class for the system tray icon
class SystemTrayIcon(QSystemTrayIcon):
    def __init__(self, icon, parent=None):
        super().__init__(icon, parent)
        self.menu = QMenu(parent)
        self.config_action = QAction("Configure", self)
        self.config_action.triggered.connect(self.show_config_dialog)
        self.menu.addAction(self.config_action)
        self.config_dialog = None  # Track the config dialog instance
        self.update_tooltip()

        # Exit action
        self.exit_action = QAction("Exit", self)
        self.exit_action.triggered.connect(self.exit_application)
        self.menu.addAction(self.exit_action)

        self.setContextMenu(self.menu)
        self.config = load_config()
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.perform_ping)
        self.timer.start(self.config['interval'] * 60000)
        self.perform_ping()
        self.update_tooltip()  # Call this method to set the initial tooltip

    def update_tooltip(self):
        # Retrieve the current configuration
        config = load_config()
        dns = config.get('dns', DEFAULT_DNS)
        interval = config.get('interval', DEFAULT_INTERVAL)
        tooltip_text = f"Pinging {dns}\nInterval: {interval} mins"
        self.setToolTip(tooltip_text)

    def on_tray_icon_activated(self, reason):
        if reason == QSystemTrayIcon.Trigger:  # Left click
            self.show_config_dialog()

    def show_config_dialog(self):

        if self.config_dialog is not None and not self.config_dialog.isHidden():
            self.config_dialog.raise_()
            self.config_dialog.activateWindow()
        else:
            self.config_dialog = ConfigDialog(self)
            self.config_dialog.dns_input.setText('')
            self.config_dialog.dns_combo.setCurrentText(self.config['dns'])
            self.config_dialog.interval_combo.setCurrentText(str(self.config['interval']))
            self.config_dialog.show()

    def exit_application(self):
        print ('Icon Exit Key Used')
        QApplication.quit()

    def update_icon(self, success):
        if success:
            self.setIcon(QIcon('connected.png'))
        else:
            self.setIcon(QIcon('disconnected.png'))

    def perform_ping(self):
        success = ping_dns(self.config['dns'])
        self.update_icon(success)

    def show_config_dialog(self):
        dialog = ConfigDialog(self)
        dialog.dns_input.setText('')
        dialog.dns_combo.setCurrentText(self.config['dns'])
        dialog.interval_combo.setCurrentText(str(self.config['interval']))
        dialog.exec_()

    def update_config(self):
        self.config = load_config()
        self.timer.stop()
        self.timer.start(self.config['interval'] * 60000)
        self.perform_ping()
        self.update_tooltip()  # Update the tooltip whenever the configuration changes

# Main application setup
def main():
    app = QApplication(sys.argv)
    if is_another_instance_running():
        error_dialog = QMessageBox()
        error_dialog.setIcon(QMessageBox.Critical)
        error_dialog.setText("Error: Application already running.")
        error_dialog.exec_()
        return  # Exit the application
    tray_icon = SystemTrayIcon(QIcon('default_icon.png'))
    tray_icon.show()
    # Ensuring that the application does not quit when the last window is closed
    app.setQuitOnLastWindowClosed(False)
    sys.exit(app.exec_())


# Uncomment the below line to run the application
main()
