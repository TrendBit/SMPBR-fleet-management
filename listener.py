from zeroconf import ServiceBrowser, Zeroconf
from device import Device
import socket

class BioreactorListener:
    """Listener for Bioreactor mDNS services."""
    def __init__(self):
        self.devices = []

    def remove_service(self, zeroconf, type, name):
        """Called when a service is removed."""
        pass

    def add_service(self, zeroconf, type, name):
        """Called when a service is discovered."""
        try:
            info = zeroconf.get_service_info(type, name)
            if info and info.addresses:
                ip = socket.inet_ntoa(info.addresses[0])
                hostname = info.server.rstrip('.local.')
                device = Device(hostname, ip, info.port)
                self.devices.append(device)
        except Exception as e:
            print(f"Error adding service {name}: {e}")

    def update_service(self, zeroconf, type, name):
        """Called when a service is updated."""
        pass
