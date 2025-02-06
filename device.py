import paramiko
from scp import SCPClient

class Device:
    def __init__(self, hostname, ip_address, port):
        self.hostname = hostname
        self.ip_address = ip_address
        self.port = port

    def __str__(self):
        return f"{self.hostname} {self.ip_address}"

    def __lt__(self, other):
        """Enable sorting by hostname"""
        return self.hostname < other.hostname

    def execute_command(self, command, username, password):
        """
        Execute command on device using SSH.
        Args:
            command (str): Command to execute
            username (str): SSH username
            password (str): SSH password
        Returns:
            tuple: (output, error)
        """
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        try:
            client.connect(self.ip_address, username=username, password=password)
            stdin, stdout, stderr = client.exec_command(command)
            output = stdout.read().decode()
            error = stderr.read().decode()
            return output, error
        finally:
            client.close()

    def upload_file(self, local_path: str, remote_path: str, username: str, password: str) -> tuple[bool, str]:
        """
        Upload file to device using SCP
        Args:
            local_path (str): Path to local file
            remote_path (str): Remote destination path
            username (str): SSH username
            password (str): SSH password
        Returns:
            tuple: (success, message)
        """
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        try:
            ssh.connect(self.ip_address, username=username, password=password)
            with SCPClient(ssh.get_transport()) as scp:
                scp.put(local_path, remote_path)
            return True, f"File uploaded successfully to {self}"
        except Exception as e:
            return False, str(e)
        finally:
            ssh.close()
