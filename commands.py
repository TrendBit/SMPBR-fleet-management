#!/usr/bin/env python3
import time
import os
from colorama import Fore
from listener import BioreactorListener
from zeroconf import ServiceBrowser, Zeroconf
from concurrent.futures import ThreadPoolExecutor, as_completed

def get_devices(timeout=2):
    """
    Get list of available bioreactor devices.
    Args:
        timeout (int): Time to wait for device discovery in seconds
    Returns:
        list: List of Device objects
    """
    zeroconf = Zeroconf()
    listener = BioreactorListener()
    try:
        browser = ServiceBrowser(zeroconf, "_bioreactor_api._tcp.local.", listener)
        time.sleep(timeout)
        return sorted(listener.devices)
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

def upload_file_to_devices(local_path, remote_path, username, password, timeout=2, parallel=False):
    """Upload file to all detected devices"""
    if not os.path.exists(local_path):
        print(f"{Fore.RED}Error: File {local_path} not found{Fore.RESET}")
        return

    devices = get_devices(timeout)
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

def execute_command(command, username, password, timeout=2, parallel=False):
    """Execute command on all detected devices"""
    devices = get_devices(timeout)

    def run_on_device(device):
        print(f"Executing on {device}...")
        success, message = device.execute_command(command, username, password)
        if success:
            print(f"{Fore.GREEN}Success on {device}: {message}{Fore.RESET}")
        else:
            print(f"{Fore.RED}Error on {device}: {message}{Fore.RESET}")

    if parallel:
        execute_parallel(run_on_device, devices)
    else:
        for device in devices:
            run_on_device(device)

def update_firmware(username, password, timeout=2, firmware_path = None):
    """
    Update firmware on all detected devices
    Args:
        firmware_path (str): Path to firmware file
        username (str): SSH username
        password (str): SSH password
        timeout (int): Discovery timeout in seconds
    """
    if firmware_path:
        upload_file_to_devices(firmware_path, "~", username, password, timeout)
        archive_name = os.path.basename(firmware_path)
        execute_command("./update_firmware.sh --local {}".format(archive_name), username, password, timeout)
    else:
        execute_command("./update_firmware.sh --fetch", username, password, timeout)


def copy_recipe(recipe_path, username, password, timeout=2, parallel=False):
    """
    Copy recipe file to all detected devices using SCP
    Args:
        recipe_path (str): Path to recipe file
        username (str): SSH username
        password (str): SSH password
        timeout (int): Discovery timeout in seconds
    """
    remote_path = "/home/reactor/recipe-runner/config/default.yaml"
    upload_file_to_devices(recipe_path, remote_path, username, password, timeout, parallel)



