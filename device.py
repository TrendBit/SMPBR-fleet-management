import paramiko

class Device:
    def __init__(self, hostname, ip_address, port):
        self.hostname = hostname
        self.ip_address = ip_address
        self.port = port

    def __str__(self):
        return f"{self.hostname} {self.ip_address}"

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
