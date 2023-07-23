import logging
from time import sleep
import paramiko

# Enable debug logging
paramiko_log = logging.getLogger("paramiko")
paramiko_log.setLevel(logging.DEBUG)
paramiko_log.addHandler(logging.StreamHandler())


def install_alpine_vm(vm_ip, vm_port, vm_username, vm_password):
    # Connect to the VM via SSH
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    try:
        client.connect(vm_ip, port=vm_port, username=vm_username, password=vm_password)
    except paramiko.AuthenticationException:
        print("Authentication failed. Please check the username and password.")
        return
    except paramiko.SSHException as e:
        print(f"Error connecting to VM: {e}")
        return

    # Send commands to the VM
    try:
        print("Successfully connected to the VM. Installing Alpine Linux...")
        # stdin, stdout, stderr = client.exec_command("mkdir lol")
        # print("Done that.")
        stdin, stdout, stderr = client.exec_command("setup-disk -m sys -q")
        print("executed setup-disk")
        # stdin.close()
        sleep(1)
        print("going to write sda")
        stdin.write("sda\n")
        # client.exec_command("sda\n")
        print("wrote sda")
        stdin.flush()
        # stdout.channel.shutdown_write()
        sleep(1)
        # print(stdout.read().decode("utf-8"))
        print("going to write y")
        stdin.write("y\n")
        # client.exec_command("y\n")

        print("wrote y")
        stdin.flush()
        # print(stdout.read().decode("utf-8"))
        stdin.close()

        # Wait for the installation process to complete
        while not stdout.channel.exit_status_ready():
            # print(stdout.read().decode("utf-8"))
            pass

        # print(stdout.read().decode("utf-8"))
        # print(stderr.read().decode("utf-8"))
        print("Installation completed successfully.")
        # Send poweroff command to the VM
        # stdin, stdout, stderr = client.exec_command("poweroff")
    except paramiko.SSHException as e:
        print(f"Error executing commands on VM: {e}")
    finally:
        client.close()


# Usage example
install_alpine_vm(
    "127.0.0.4",
    2222,
    "root",
    "a",
)
