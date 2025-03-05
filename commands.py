#!/usr/bin/env python3
import time
import os
from colorama import Fore
from listener import BioreactorListener
from zeroconf import ServiceBrowser, Zeroconf
from concurrent.futures import ThreadPoolExecutor, as_completed

def parse_range(range_str: str) -> list[int]:
    """Parse range string like '1-3,5,7-9' into list of numbers"""
    if not range_str:
        return []

    numbers = set()
    for part in range_str.split(','):
        if '-' in part:
            start, end = map(int, part.split('-'))
            numbers.update(range(start, end + 1))
        else:
            numbers.add(int(part))
    return sorted(list(numbers))

def get_devices(timeout=2, device_range=None):
    """Get list of discovered devices filtered by range"""
    zeroconf = Zeroconf()
    listener = BioreactorListener()
    try:
        browser = ServiceBrowser(zeroconf, "_bioreactor_api._tcp.local.", listener)
        time.sleep(timeout)
        devices = sorted(listener.devices)

        if device_range:
            numbers = parse_range(device_range)
            devices = [d for d in devices if d.number() in numbers]

        return devices
    finally:
        zeroconf.close()

def discover_devices(timeout=2):
    """
    Discover and print available bioreactor devices.
    Args:
        timeout (int): Time to wait for device discovery in seconds
    """
    try:
        devices = get_devices(timeout)
        if devices:
            print(f"Discovered {len(devices)} device/s:")
            print("----------------------")
            for device in devices:
                print(device)
        else:
            print("No devices found")
    except Exception as e:
        print(f"Error during device discovery: {e}")

def execute_parallel(func, items, *args):
    """Execute function in parallel for multiple items"""
    with ThreadPoolExecutor(max_workers=len(items)) as executor:
        futures = [executor.submit(func, item, *args) for item in items]
        for future in as_completed(futures):
            future.result()

def upload_file_to_devices(local_path, remote_path, username, password, timeout=2, parallel=False, device_range=None):
    """Upload file to all detected devices"""
    if not os.path.exists(local_path):
        print(f"{Fore.RED}Error: File {local_path} not found{Fore.RESET}")
        return

    devices = get_devices(timeout, device_range)
    local_path = os.path.abspath(local_path)

    def upload_to_device(device):
        print(f"Uploading file to {device}...")
        success, message = device.upload_file(local_path, remote_path, username, password)
        if success:
            print(f"{Fore.GREEN}Success: {message}{Fore.RESET}")
        else:
            print(f"{Fore.RED}Error uploading to {device}: {message}{Fore.RESET}")

    if parallel:
        execute_parallel(upload_to_device, devices)
    else:
        for device in devices:
            upload_to_device(device)

def execute_command(command, username, password, timeout=2, parallel=False, device_range=None):
    """Execute command on all detected devices"""
    devices = get_devices(timeout, device_range)

    def format_output(device, status, message, color):
        """Format command output with consistent styling"""
        message = message.strip()
        if message.count('\n') > 1:
            return f"{color}{status} on {device}:{Fore.RESET}\n{message}"
        return f"{color}{status} on {device}: {Fore.RESET}{message}"

    def run_on_device(device):
        print(f"Executing on {device}...")
        success, error = device.execute_command(command, username, password)

        if not error:
            print(format_output(device, "Success", success, Fore.GREEN))
        else:
            print(format_output(device, "Error", error, Fore.RED))

    if parallel:
        execute_parallel(run_on_device, devices)
    else:
        for device in devices:
            run_on_device(device)

def update_device_firmware(username, password, timeout=2, firmware_path = None, parallel=False, device_range=None):
    """
    Update firmware on all detected devices
    Args:
        firmware_path (str): Path to firmware file
        username (str): SSH username
        password (str): SSH password
        timeout (int): Discovery timeout in seconds
    """
    if firmware_path:
        upload_file_to_devices(firmware_path, "/home/reactor/", username, password, timeout, parallel, device_range)
        archive_name = os.path.basename(firmware_path)
        execute_command("./update_firmware.sh -l {}".format(archive_name), username, password, timeout, parallel, device_range)
    else:
        execute_command("./update_firmware.sh -f", username, password, timeout, parallel, device_range)
