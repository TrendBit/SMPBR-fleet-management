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
def update_services(timeout, username, password, parallel, range):
    """Update services on all devices"""
    execute_command("./update_services.sh", username, password, timeout, parallel, range)

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

if __name__ == "__main__":
    cli()
