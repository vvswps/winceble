# Winceble - Windows Alpine Linux Virtual Machine Setup

Winceble is a Python script that automates the setup of an Alpine Linux virtual machine on Windows using VirtualBox. It simplifies the process of creating a virtual machine, installing Alpine Linux, and configuring it based on a YAML configuration file.

I made to just fire up a vm, setup it and deploy my app on it expose it through ngrok so that testing is really simplified

But then I extracted the configuration part to a configuration file so that it can be used for different stacks.

It's really a "Fire-and-Forget" type thing. NOT a management system, just meant for quick testing.

I wanted to automate my app deployment process so I started writing this then found out that I could use Ansible for this but then found that it does'nt work on windows and it just supercharged my rage to build one more tool for the job. IDK maybe better ones exist but this one works for me (or at-least I hope it does I'm writing this before actually making the whole thing ;})

> Would'nt it be great if you could use your already created vms and just run the configuration part on them? Well I might work on that too. But for now you can just use the script to create a new vm and configure it.
## Requirements

- Python 3.x
- VirtualBox (Ensure it is installed on your system)

## Usage

1. Clone this repository or download the `winceble.py` script.

2. Install the required Python libraries using pip:

```bash
pip install pyyaml
```

3. Create a YAML configuration file (`config.yaml`) with your desired settings. Refer to the example configuration below:

```yaml
---
vm_name: MyVM
ram_mb: 2048
disk_gb: 10
cpu_cores: 2
alpine_iso_url: https://example.com/alpine.iso
username: root
password: toor
ssh_key_location: ~/.ssh/vm_ssh_key
packages:
  - git
  - curl
  - python3
  # Add more packages here as needed
```

4. Run the script with the YAML configuration file as a command-line argument:

```bash
python winceble.py config.yaml
```

## Features

- Installs VirtualBox if not found on the system.
- Creates a new virtual machine with specified RAM, disk size, and CPU cores.
- Downloads and installs Alpine Linux using the provided ISO URL.
- Configures Alpine Linux with predefined settings (username, password, etc.).
- Generates an SSH key pair on the host machine and configures SSH key authentication on the virtual machine.
- Sets up port forwarding for SSH access to the virtual machine.
- Installs necessary packages specified in the YAML configuration.

## Note

- The script assumes VirtualBox commands (`VBoxManage`) are accessible from the command line. If not, please add the VirtualBox executable path to your system's PATH environment variable.

- Ensure the Alpine Linux ISO URL in the configuration is valid and accessible.

## Disclaimer

Please use this script responsibly and carefully review the configurations before running it. The author is not responsible for any data loss or damage caused by the misuse of this script.

## Contributions

Contributions and suggestions are welcome! Feel free to open issues or submit pull requests.

## License

This project is licensed under the [MIT License](LICENSE).

Happy virtual machine setup! 🚀