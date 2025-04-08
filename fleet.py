#!/usr/bin/env python3
import click

from commands import *
import subprocess
import os

# Common options
def common_options(f):
    f = click.option('--timeout', default=3, help='Discovery timeout in seconds')(f)
    f = click.option('--username', default='root', help='SSH username')(f)
    f = click.option('--password', default='reactor', help='SSH password')(f)
    f = click.option('--parallel/--sequential', default=False, help='Execute in parallel')(f)
    f = click.option('--range', help='Device range (e.g. 1-3,5,7-9)')(f)
    return f

@click.group()
def cli():
    """Bioreactor Fleet Management Tool"""
    pass

@cli.command()
@click.option('--timeout', default=3, help='Discovery timeout in seconds')
def discover(timeout):
    """Discover available bioreactor devices"""
    discover_devices(timeout)

@cli.command()
@common_options
@click.option('--repo', required=True, type=click.Path(exists=True), help='Patch to software repository')
def update_services(timeout, username, password, repo, parallel, range):
    """Update services on all devices"""

    update_script = os.path.join("scripts", "update_rpi.sh")
    script_path = os.path.join(repo, update_script)

    if not os.path.isfile(script_path):
        print(f"Error: Update script not found at {script_path}")
        return False

    # Store current directory to return to it later
    original_dir = os.getcwd()
    results = []

    try:
        # Change to repository directory
        os.chdir(repo)
        devices = get_devices(timeout, range)

        def update_single_device(device):
            hostname = f"{device.hostname}.local"
            print(f"Updating {hostname}...")
            try:
                result = subprocess.run(
                    [f"./scripts/update_rpi.sh", hostname],
                    check=True,
                    capture_output=True,
                    text=True
                )
                print(f"Successfully updated {hostname}")
                return (hostname, True, result.stdout)
            except subprocess.CalledProcessError as e:
                print(f"Failed to update {hostname}: {e}")
                return (hostname, False, e.stderr)

        if parallel:
            # Execute in parallel
            with ThreadPoolExecutor(max_workers=len(devices)) as executor:
                futures = [executor.submit(update_single_device, device) for device in devices]
                for future in as_completed(futures):
                    results.append(future.result())
        else:
            # Execute sequentially
            for device in devices:
                results.append(update_single_device(device))

        print(f"Update completed for {len(devices)} devices")
    finally:
        # Return to original directory
        os.chdir(original_dir)

@cli.command()
@common_options
@click.option('--swu', required=True, type=click.Path(exists=True), help='Path to image update package .swu')
def update_system(timeout, username, password, swu, parallel, range):
    """Update firmware on all devices"""
    upload_file_to_devices(swu, "/home/reactor/", username, password, timeout, parallel, range)
    execute_command(f"rpi_ab_update install {swu}", username, password, timeout, parallel, range)

@cli.command()
@common_options
@click.option('--local', required=False, type=click.Path(exists=True), help='Path to local fw archive')
def update_firmware(timeout, username, password, local, parallel, range):
    """Update firmware on all devices"""
    update_device_firmware(username, password, timeout, local, parallel, range)

@cli.command()
@common_options
@click.option('--recipe', required=True, help='Name of recipe')
def recipe_start(timeout, username, password, parallel, range, recipe):
    """Start recipe runner service"""
    execute_command(f"reactor-script-api -s recipes/{recipe}", username, password, timeout, parallel, range)

@cli.command()
@common_options
def recipe_stop(timeout, username, password, parallel, range):
    """Stop recipe runner service"""
    execute_command("reactor-script-api -x", username, password, timeout, parallel, range)

@cli.command()
@common_options
def recipe_list(timeout, username, password, parallel, range):
    """Start recipe runner service"""
    execute_command("ls /home/reactor/recipes/", username, password, timeout, parallel, range)

@cli.command()
@common_options
@click.option('--recipe', required=True, type=click.Path(exists=True), help='Path to recipe file')
def recipe_load(recipe, timeout, username, password, parallel, range):
    """Load recipe to all devices"""
    upload_file_to_devices(recipe_path, "/home/reactor/recipes/", username, password, timeout, parallel, range)

@cli.command()
@common_options
@click.option('--local', required=True, type=click.Path(exists=True), help='Path to local file')
@click.option('--remote', required=True, help='Remote destination path')
def upload_file(local, remote, timeout, username, password, parallel, range):
    """Upload file to all devices"""
    upload_file_to_devices(local, remote, username, password, timeout, parallel, range)

@cli.command()
@common_options
@click.option('--cmd', required=True, help='Command to execute on devices')
def execute(cmd, timeout, username, password, parallel, range):
    """Execute custom command on all devices"""
    execute_command(cmd, username, password, timeout, parallel, range)

@cli.command()
@common_options
def calibrate(timeout, username, password, parallel, range):
    """Execute custom command on all devices"""
    execute_command("cansend can0 04900061#", username, password, timeout, parallel, range)

if __name__ == "__main__":
    cli()
