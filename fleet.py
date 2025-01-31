#!/usr/bin/env python3

import os
from pathlib import Path
from zeroconf import ServiceBrowser, Zeroconf
import socket
import time
import argparse
from device import Device
from scp import SCPClient
import paramiko

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

def start_devices(username, password, timeout=2):
    """Execute update.sh on all detected devices"""
    try:
        devices = get_devices(timeout)
        for device in devices:
            print(f"Executing update.sh on {device}...")
            success, message = device.execute_command("./update.sh", username, password)
            print(message)
    except Exception as e:
        print(f"Error during device update: {e}")

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
        return listener.devices
    finally:
        zeroconf.close()

def copy_recipe(recipe_path, username, password, timeout=2):
    """
    Copy recipe file to all detected devices using paramiko SCP
    Args:
        recipe_path (str): Path to recipe file
        username (str): SSH username
        password (str): SSH password
        timeout (int): Discovery timeout in seconds
    """
    if not os.path.exists(recipe_path):
        print(f"Error: Recipe file {recipe_path} not found")
        return

    devices = get_devices(timeout)
    recipe_path = os.path.abspath(recipe_path)
    remote_path = "/home/reactor/recipe-runner/config/default.yaml"

    for device in devices:
        print(f"Copying recipe to {device}...")
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        try:
            ssh.connect(device.ip_address, username=username, password=password)
            with SCPClient(ssh.get_transport()) as scp:
                scp.put(recipe_path, remote_path)
            print(f"Success: Recipe copied to {device}")
        except Exception as e:
            print(f"Error copying to {device}: {e}")
        finally:
            ssh.close()

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
            print(f"Error on {device}: {error}")
        else:
            print(f"Success on {device}: {output}")

def main():
    parser = argparse.ArgumentParser(description='Bioreactor Fleet Management')
    parser.add_argument('command', choices=['discover', 'update_firmware', 'update_services',
                                          'execute', 'recipe_start', 'recipe_restart', 'recipe_stop', 'recipe_load'],
                       help='Command to execute')
    parser.add_argument('--timeout', type=int, default=2, help='Discovery timeout in seconds')
    parser.add_argument('--username', help='SSH username', default="reactor")
    parser.add_argument('--password', help='SSH password', default="grow")
    parser.add_argument('--cmd', help='Command to execute on devices')
    parser.add_argument('--recipe', help='Path to recipe file')

    args = parser.parse_args()

    if args.command == 'discover':
        discover_devices(args.timeout)
    elif args.command == 'update_services':
        execute_command("./update_services.sh", args.username, args.password, args.timeout)
    elif args.command == 'update_firmware':
        execute_command("./update_firmware.sh", args.username, args.password, args.timeout)
    elif args.command == 'recipe_start':
        execute_command("sudo systemctl start recipe-runner.service", args.username, args.password, args.timeout)
    elif args.command == 'recipe_restart':
        execute_command("sudo systemctl restart recipe-runner.service", args.username, args.password, args.timeout)
    elif args.command == 'recipe_stop':
        execute_command("sudo systemctl stop recipe-runner.service", args.username, args.password, args.timeout)
    elif args.command == 'recipe_load':
        if not args.recipe:
            print("Error: --recipe argument is required for recipe_load command")
            return
        copy_recipe(args.recipe, args.username, args.password, args.timeout)
    elif args.command == 'execute':
        if not args.cmd:
            print("Error: --cmd argument is required for execute command")
            return
        execute_command(args.cmd, args.username, args.password, args.timeout)

if __name__ == "__main__":
    main()
