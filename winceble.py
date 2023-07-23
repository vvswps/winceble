import os
import re
import subprocess
import sys
from time import sleep
import urllib
import yaml
from random import randint
import requests
from bs4 import BeautifulSoup
from colorama import Fore, Style, init
from halo import Halo

init(autoreset=True)


class Winceble:
    def __init__(self) -> None:
        self.VM_CONFIG_KEYS = {
            "vm_name": self.generate_random_name(),
            "ram_mb": int(1024 * 1.5),  # 1.5 GB
            "disk_gb": 10,
            "cpu_cores": 2,
            "alpine_iso_url": self.get_latest_version_official(),
            # Default Alpine Linux username and password
            "username": "root",
            "password": "toor",
            "ssh_key_location": "~/.ssh/id_rsa.pub",
            # Edit this to change the packages installed on the VM
            "packages": [
                "openjdk17",
                "mysql",
            ],
        }

    def generate_random_name(self) -> str:
        return "winceble-" + "".join([chr(randint(97, 122)) for _ in range(4)])

    def get_latest_version_official(self):
        latest_version_link = ""
        try:
            url = "https://alpinelinux.org/downloads/"
            html = requests.get(url).text
            soup = BeautifulSoup(html, "html.parser")
            soup.prettify().encode("utf-8")

            pattern = (
                r"https://\S+/releases/x86_64/alpine-virt-\d+\.\d+\.\d+-x86_64\.iso"
            )
            matches = re.findall(pattern, str(soup))

            if matches:
                latest_version_link = matches[0]
                print(
                    Fore.GREEN + "Latest version from official website:",
                    latest_version_link,
                )
            else:
                raise Exception("No matches found")

        except Exception as e:
            print(e)
            print(
                Fore.RED
                + "Error: Could'nt get the latest version from official website."
            )
            print(Fore.BLUE + "Using: Alpine: 3.18.2 instead")
            latest_version_link = "https://dl-cdn.alpinelinux.org/alpine/v3.18/releases/x86_64/alpine-virt-3.18.2-x86_64.iso"

        return latest_version_link

    def read_yaml_config(self, config_file):
        try:
            with open(config_file, "r") as file:
                config_data = yaml.safe_load(file)
            return config_data
        except FileNotFoundError:
            print(f"Error: Config file '{config_file}' not found.")
            sys.exit(1)
        except yaml.YAMLError as e:
            print(f"Error: Invalid YAML in '{config_file}': {e}")
            sys.exit(1)

    def prechecks(self):
        # Check if VirtualBox is installed
        try:
            version = subprocess.run(["VBoxManage", "--version"], capture_output=True)
            print(
                Fore.LIGHTBLUE_EX + "VirtualBox version:",
                version.stdout.decode("utf-8"),
            )
        except FileNotFoundError:
            print(Fore.RED + "VirtualBox Not found")
            print(Fore.YELLOW + "Please install VirtualBox and add it to PATH")
            print(Fore.BLUE + "https://www.virtualbox.org/wiki/Downloads")
            print(
                Fore.YELLOW
                + "\nIt may be possible that you have VirtualBox installed but not added to PATH"
            )
            print(
                Fore.LIGHTCYAN_EX
                + """Steps to add VirtualBox to PATH
> Go to C drive (or your windows drive) and find the folder where VirtualBox is installed
    Usually C:\Program Files\Oracle\VirtualBox
> Copy the path of the folder
> Go to Control Panel > System and Security > System > Advanced System Settings > Environment Variables > System Variables > Path > Edit
> Click on New and paste the path you copied earlier
> Click OK and restart your terminal
> Try running the script again"""
            )
            sys.exit(1)

    def create_vm(self, vm_name, ram_mb, disk_gb, cpu_cores):
        print(
            f"Creating Virtual Machine with the following configuration:\nName: {vm_name}\nRAM: {ram_mb} MB\nDisk: {disk_gb} GB\nCPU: {cpu_cores} cores"
        )
        try:
            subprocess.run(
                [
                    "VBoxManage",
                    "createvm",
                    "--name",
                    vm_name,
                    "--ostype",
                    "Linux_64",
                    "--register",
                ],
                check=True,
            )
            print("Virtual Machine created.")

            subprocess.run(
                ["VBoxManage", "modifyvm", vm_name, "--memory", str(ram_mb)], check=True
            )
            print("Memory added.")

            subprocess.run(
                [
                    "VBoxManage",
                    "storagectl",
                    vm_name,
                    "--name",
                    "SATA",
                    "--add",
                    "sata",
                ],
                check=True,
            )

            subprocess.run(
                [
                    "VBoxManage",
                    "createhd",
                    "--filename",
                    f"{vm_name}.vdi",
                    "--size",
                    str(disk_gb * 1024),
                ],
                check=True,
            )
            print("Virtual Hard Disk created.")

            subprocess.run(
                [
                    "VBoxManage",
                    "storageattach",
                    vm_name,
                    "--storagectl",
                    "SATA",
                    "--port",
                    "0",
                    "--device",
                    "0",
                    "--type",
                    "hdd",
                    "--medium",
                    f"{vm_name}.vdi",
                ],
                check=True,
            )
            print("Virtual Hard Disk attached.")

            subprocess.run(
                ["VBoxManage", "modifyvm", vm_name, "--cpus", str(cpu_cores)],
                check=True,
            )
            print("CPU cores configured.")

            subprocess.run(
                ["VBoxManage", "modifyvm", vm_name, "--natpf1", "ssh,tcp,,2222,,22"]
            )
            print("Port forwarding configured.")

            subprocess.run(["VBoxManage", "modifyvm", vm_name, "--vram", "9"])
            print(f"Video memory for VM '{vm_name}' has been set to 9 MB.")

            sleep(1)
            print(Fore.GREEN + f"Virtual Machine {vm_name} created successfully.")

        except subprocess.CalledProcessError as e:
            print(f"Error executing subprocess command: {e}")
            print(Fore.RED + "Cleaning up...Deleting Virtual Machine...")
            subprocess.run(["VBoxManage", "unregistervm", vm_name, "--delete"])
            sys.exit(1)

    def wait_for_vm_power_off(self, vm_name, max_retries=30, delay=10):
        retries = 0
        while retries < max_retries:
            try:
                result = subprocess.run(
                    ["VBoxManage", "showvminfo", vm_name],
                    capture_output=True,
                    text=True,
                )
                if "State: powered off" in result.stdout:
                    return True
            except Exception as e:
                print(
                    f"Error checking VM status: {e} Retrying in {delay} seconds...[Attempt {retries+1}/{max_retries}]]"
                )
            sleep(delay)
            retries += 1
        return False

    def download_alpine(self, alpine_iso_url, iso_filename):
        try:
            print(Fore.BLUE + "Downloading Alpine Linux ISO...")
            # save it in .winceble_cache
            if not os.path.exists(".winceble_cache"):
                os.makedirs(".winceble_cache")

            # Use Halo to show a spinner while downloading
            spinner = Halo(text=f"Downloading {iso_filename}", spinner="dots")
            spinner.start()

            urllib.request.urlretrieve(
                alpine_iso_url, ".winceble_cache/" + iso_filename
            )

            spinner.text = f"Downloading {iso_filename}.sha256"
            urllib.request.urlretrieve(
                alpine_iso_url + ".sha256",
                ".winceble_cache/" + iso_filename + ".sha256",
            )

            spinner.succeed(f"Downloaded {iso_filename} and {iso_filename}.sha256")
        except Exception as e:
            spinner.fail(f"Error downloading Alpine Linux ISO: {e}")
            sys.exit(1)

    def mount_alpine_iso_and_start_vm(self, alpine_iso_url, vm_name):
        try:
            # check in cache first so we don't download it again
            iso_filename = alpine_iso_url.split("/")[-1]
            # check if it exists along with matching the sha256 checksum also check if its the latest version
            # the latest version thing will be automatically checked when we ask it if there exists a file by this name
            # right?
            if os.path.isfile(".winceble_cache/" + iso_filename) and self.verify_sha256(
                iso_filename
            ):
                print(Fore.BLUE + "Using cached Alpine Linux ISO")
            else:
                print("No cached Alpine ISO found")
                self.download_alpine(alpine_iso_url, iso_filename)
        except Exception as e:
            print(f"Error checking cached Alpine Linux ISO: {e}")
            self.download_alpine(alpine_iso_url, iso_filename)

        try:
            print("Attaching Alpine ISO to Virtual Machine...")
            # Create a SATA storage controller
            # VBoxManage storagectl <vm_name> --name "SATA" --add sata
            subprocess.run(
                [
                    "VBoxManage",
                    "storagectl",
                    vm_name,
                    "--name",
                    "IDE",
                    "--add",
                    "ide",
                ],
                check=True,
            )

            # Attach the ISO to the SATA controller
            # VBoxManage storageattach <vm_name> --storagectl "SATA" --port 1 --device 0 --type dvddrive --medium <iso_filename>

            subprocess.run(
                [
                    "VBoxManage",
                    "storageattach",
                    vm_name,
                    "--storagectl",
                    "IDE",
                    "--port",
                    "1",
                    "--device",
                    "0",
                    "--type",
                    "dvddrive",
                    "--medium",
                    ".winceble_cache/" + iso_filename,
                ],
                check=True,
            )
            print("Alpine ISO attached to Virtual Machine.")
        except subprocess.CalledProcessError as e:
            print(f"Error executing subprocess command: {e}")
            print(Fore.RED + "Cleaning up...Deleting Virtual Machine...")
            subprocess.run(["VBoxManage", "unregistervm", vm_name, "--delete"])
            sys.exit(1)

        print("Starting Virtual Machine to install Alpine Linux...")
        subprocess.run(["VBoxManage", "startvm", vm_name, "--type", "headless"])

    def run_setup_alpine_script(self, vm_name):
        # # echo a simple hello world script on the VM
        # subprocess.run(
        #     [
        #         "VBoxManage",
        #         "guestcontrol",
        #         vm_name,
        #         "run",
        #         "--exe",
        #         "/bin/sh",
        #         "--username",
        #         self.VM_CONFIG_KEYS["username"],
        #         "--password",
        #         self.VM_CONFIG_KEYS["password"],
        #         "--wait-stdout",
        #         "--wait-stderr",
        #         "--",
        #         "echo",
        #         "'Hello World'",
        #         ">",
        #         "/root/hello_world.sh",
        #     ]
        # )

        # # Wait for Alpine installation to complete
        # if self.wait_for_vm_power_off(vm_name):
        #     print("Alpine Linux installation completed.")
        # else:
        #     print(
        #         "Error: Alpine Linux installation did not complete within the expected time."
        #     )
        #     sys.exit(1)

        # lets do some magic

        # wait for the VM to boot
        print("Waiting for VM to boot...")

        # 30 second sleep spinner
        seconds = 40

        print(
            Fore.LIGHTBLUE_EX
            + f"Let's wait for {seconds} seconds and hope that Alpine boots in that time or every command after this is ducked"
        )
        for i in range(seconds, 0, -1):
            print(f"\r{seconds} seconds remaining...", end="", flush=True)
            sleep(1)
            seconds -= 1
        print("\rWait is over :}")

        # run the setup-alpine script

        print("Running setup-alpine quick script...")
        press_enter = [
            "VBoxManage",
            "controlvm",
            vm_name,
            "keyboardputscancode",
            "1C",
            "9C",
        ]  # 1C is enter key down and 9C is enter key up

        def setup_alpine_vm():
            # List of commands to execute on the VM
            commands = [
                "echo 'auto lo\niface lo inet loopback\n\nauto eth0\niface eth0 inet dhcp' > /etc/network/interfaces",
                "echo '/media/cdrom/apks\nhttp://dl-cdn.alpinelinux.org/alpine/v3.18/main\nhttp://dl-cdn.alpinelinux.org/alpine/v3.18/community' > /etc/apk/repositories",
                "rc-service networking start",
                "rc-update add networking boot",
                "apk update",
                f"echo {self.VM_CONFIG_KEYS['username']}:{self.VM_CONFIG_KEYS['password']} | chpasswd",
                "apk add dropbear",
                "dropbear",
                "rc-service dropbear start",
            ]

            # Loop over the commands and execute them on the VM
            for command in commands:
                # Send the command to the VM
                subprocess.run(
                    [
                        "VBoxManage",
                        "controlvm",
                        vm_name,
                        "keyboardputstring",
                        command,
                    ]
                )

                subprocess.run(press_enter)

                # Sleep for a few seconds to allow the command to execute
                sleep(20) if "apk" in command else sleep(3)

            # Connect to the VM from PowerShell
            subprocess.run(["ssh", "-p", "2222", "root@127.0.0.1"])
            sleep(1)
            # subprocess.run(["bab"])

        subprocess.run(
            ["VBoxManage", "controlvm", vm_name, "keyboardputstring", "root"]
        )
        subprocess.run(press_enter)
        sleep(1)

        subprocess.run(press_enter)
        setup_alpine_vm()
        sleep(1)
        # subprocess.run(
        #     [
        #         "VBoxManage",
        #         "controlvm",
        #         vm_name,
        #         "keyboardputstring",
        #         "alpine-setup -f ANSWERS",
        #     ]
        # )
        # subprocess.run(press_enter)

        # print("Let's see what happens...exiting")

        # sys.exit(1)

        # print("Detaching Alpine ISO from Virtual Machine...")
        # subprocess.run(
        #     [
        #         "VBoxManage",
        #         "storageattach",
        #         vm_name,
        #         "--storagectl",
        #         "IDE",
        #         "--port",
        #         "1",
        #         "--device",
        #         "0",
        #         "--type",
        #         "dvddrive",
        #         "--medium",
        #         "none",
        #     ]
        # )

    def verify_sha256(self, iso_filename):
        print("Verifying SHA256 checksum...")
        expected_checksum = (
            open(".winceble_cache/" + iso_filename + ".sha256", "r")
            .read()
            .split(" ")[0]
        )

        try:
            result = subprocess.run(
                ["certutil", "-hashfile", ".winceble_cache/" + iso_filename, "SHA256"],
                capture_output=True,
                text=True,
                check=True,  # check=True to raise an exception if the command fails
            )
            checksum = result.stdout.strip().split("\n")[1].strip()
            print(f"Checksum: {checksum}\nExpected: {expected_checksum}")
            if checksum == expected_checksum:
                return True
            else:
                print(
                    f"Error: Checksum mismatch. Expected {expected_checksum}, got {checksum}"
                )
                return False
        except subprocess.CalledProcessError as e:
            print(f"Error verifying checksum: {e}")
            return False
        except Exception as e:
            print(f"An unexpected error occurred: {e}")
            return False

    def manage_everything(self):
        self.prechecks()
        self.create_vm(
            self.VM_CONFIG_KEYS["vm_name"],
            self.VM_CONFIG_KEYS["ram_mb"],
            self.VM_CONFIG_KEYS["disk_gb"],
            self.VM_CONFIG_KEYS["cpu_cores"],
        )
        self.mount_alpine_iso_and_start_vm(
            self.VM_CONFIG_KEYS["alpine_iso_url"], self.VM_CONFIG_KEYS["vm_name"]
        )
        self.run_setup_alpine_script(self.VM_CONFIG_KEYS["vm_name"])


if __name__ == "__main__":
    if sys.platform != "win32":
        print("This script only supports Windows for now.")
        sys.exit(1)

    # Check if the number of arguments is correct
    if len(sys.argv) == 1:
        print(
            Fore.BLUE
            + "No config file specified. Will create a VM with default values."
        )
        Winceble().manage_everything()

    elif len(sys.argv) == 2 and sys.argv[1].endswith(".yml"):
        print(Fore.BLUE + "Will use the given config file after setting up the VM.")
        config_file = sys.argv[-1]
        config = Winceble().read_yaml_config(config_file)
    else:
        print(Fore.RED + "Incorrect parameters!")
        print("Usage: python winceble.py config_file.yml\n\tOR: python winceble.py")
        sys.exit(1)
