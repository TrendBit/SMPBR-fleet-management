#!/usr/bin/env python3
import time
import os
from colorama import Fore
from listener import BioreactorListener
from zeroconf import ServiceBrowser, Zeroconf

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

def upload_file_to_devices(local_path, remote_path, username, password, timeout=2):
    """
    Upload file to all detected devices
    Args:
        local_path (str): Path to local file
        remote_path (str): Remote destination path
        username (str): SSH username
        password (str): SSH password
        timeout (int): Discovery timeout in seconds
    """
    if not os.path.exists(local_path):
        print(f"{Fore.RED}Error: File {local_path} not found{Fore.RESET}")
        return

    devices = get_devices(timeout)
    local_path = os.path.abspath(local_path)

    for device in devices:
        print(f"Uploading file to {device}...")
        success, message = device.upload_file(local_path, remote_path, username, password)
        if success:
            print(f"{Fore.GREEN}Success: {message}{Fore.RESET}")
        else:
            print(f"{Fore.RED}Error uploading to {device}: {message}{Fore.RESET}")

def copy_recipe(recipe_path, username, password, timeout=2):
    """
    Copy recipe file to all detected devices using SCP
    Args:
        recipe_path (str): Path to recipe file
        username (str): SSH username
        password (str): SSH password
        timeout (int): Discovery timeout in seconds
    """
    remote_path = "/home/reactor/recipe-runner/config/default.yaml"
    upload_file_to_devices(recipe_path, remote_path, username, password, timeout)


def execute_command(command, username, password, timeout=2):
    """
    Execute command on all detected devices
    Args:
        command (str): Command to execute
        username (str): SSH username
        password (str): SSH password
        timeout (int): Discovery timeout in seconds
    """
    devices = get_devices(timeout)
    for device in devices:
        print(f"Executing '{command}' on {device}...")
        output, error = device.execute_command(command, username, password, )
        if error:
            print(f"{Fore.RED}Error on {device}: {error}{Fore.RESET}")
        else:
            print(f"{Fore.GREEN}Success on {device}: {output}{Fore.RESET}")
