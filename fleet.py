#!/usr/bin/env python3
import click

from commands import *

# Common options
def common_options(f):
    f = click.option('--timeout', default=2, help='Discovery timeout in seconds')(f)
    f = click.option('--username', default='reactor', help='SSH username')(f)
    f = click.option('--password', default='grow', help='SSH password')(f)
    return f

@click.group()
def cli():
    """Bioreactor Fleet Management Tool"""
    pass

@cli.command()
@click.option('--timeout', default=2, help='Discovery timeout in seconds')
def discover(timeout):
    """Discover available bioreactor devices"""
    discover_devices(timeout)

@cli.command()
@common_options
def update_services(timeout, username, password):
    """Update services on all devices"""
    execute_command("./update_services.sh", username, password, timeout)

@cli.command()
@common_options
def update_firmware(timeout, username, password):
    """Update firmware on all devices"""
    execute_command("./update_firmware.sh", username, password, timeout)

@cli.command()
@common_options
def recipe_start(timeout, username, password):
    """Start recipe runner service"""
    execute_command("sudo systemctl start recipe-runner.service", username, password, timeout)

@cli.command()
@common_options
def recipe_restart(timeout, username, password):
    """Restart recipe runner service"""
    execute_command("sudo systemctl restart recipe-runner.service", username, password, timeout)

@cli.command()
@common_options
def recipe_stop(timeout, username, password):
    """Stop recipe runner service"""
    execute_command("sudo systemctl stop recipe-runner.service", username, password, timeout)

@cli.command()
@common_options
@click.option('--recipe', required=True, type=click.Path(exists=True), help='Path to recipe file')
def recipe_load(recipe, timeout, username, password):
    """Load recipe to all devices"""
    copy_recipe(recipe, username, password, timeout)


@cli.command()
@common_options
@click.option('--local', required=True, type=click.Path(exists=True), help='Path to local file')
@click.option('--remote', required=True, help='Remote destination path')
def upload_file(local, remote, timeout, username, password):
    """Upload file to all devices"""
    upload_file_to_devices(local, remote, username, password, timeout)

@cli.command()
@common_options
@click.option('--cmd', required=True, help='Command to execute on devices')
def execute(cmd, timeout, username, password):
    """Execute custom command on all devices"""
    execute_command(cmd, username, password, timeout)

if __name__ == "__main__":
    cli()
