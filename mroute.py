import os
import sys
import argparse
import subprocess
from typing import List

# Constants for default files
DEFAULT_CONFIG_FILE = "config.ini"
BACKUP_FILE = "config_backup.ini"

def run_command(command: List[str]) -> str:
    """Run a shell command and return its output."""
    try:
        result = subprocess.run(command, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        print(f"Error: {e.stderr.strip()}")
        sys.exit(1)

def create_default_config_file(output_file: str = DEFAULT_CONFIG_FILE):
    if os.path.exists(output_file):
        print(f"Error: Configuration file '{output_file}' already exists.")
        sys.exit(1)

    with open(output_file, "w") as file:
        file.write("""
# Default configuration file with example values
# Replace the example values with your own configuration

DNS
# 172.20.11.2
# 172.20.12.2

DOMAIN
# example.com
# test.com

ROUTES
# 172.20.11.0/24
# 172.20.12.0/24

GATEWAY
# 172.20.10.1
""".strip())
    print(f"Default configuration file '{output_file}' created. Please edit it as needed.")

def parse_config_file(config_file: str):
    """Parse configuration file into structured data."""
    dns_servers, search_domains, routes, gateway = [], [], [], ""
    section = None

    if not os.path.exists(config_file):
        print(f"Error: Configuration file '{config_file}' not found.")
        sys.exit(1)

    with open(config_file, "r") as file:
        for line in file:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if line in ["DNS", "DOMAIN", "ROUTES", "GATEWAY"]:
                section = line
            elif section == "DNS":
                dns_servers.append(line)
            elif section == "DOMAIN":
                search_domains.append(line)
            elif section == "ROUTES":
                routes.append(line)
            elif section == "GATEWAY":
                gateway = line

    return dns_servers, search_domains, routes, gateway

def list_network_services() -> List[str]:
    """List all available network services."""
    output = run_command(["networksetup", "-listallnetworkservices"])
    services = output.split("\n")[1:]  # Skip the header
    for i, service in enumerate(services, 1):
        print(f"{i}. {service}")
    return services

def select_network_service(services: List[str]) -> str:
    while True:
        try:
            choice = int(input("Enter the number of the network service: "))
            if 1 <= choice <= len(services):
                return services[choice - 1]
        except ValueError:
            pass
        print("Invalid selection. Try again.")

def set_configuration(interface: str, dns: List[str], domains: List[str], routes: List[str], gateway: str):
    if dns:
        print("Configuring DNS...")
        run_command(["sudo", "networksetup", "-setdnsservers", interface] + dns)
        print(f"DNS servers set to: {', '.join(dns)}")
    if domains:
        print("Configuring search domains...")
        run_command(["sudo", "networksetup", "-setsearchdomains", interface] + domains)
        print(f"Search domains set to: {', '.join(domains)}")
    if routes and gateway:
        print("Adding routes...")
        for route in routes:
            run_command(["sudo", "route", "add", route, gateway])
            print(f"Route added: {route} via {gateway}")
    else:
        print("Skipping routes: No routes or gateway specified.")

def reset_configuration(interface: str):
    print("Resetting DNS and search domains...")
    run_command(["sudo", "networksetup", "-setdnsservers", interface, "Empty"])
    run_command(["sudo", "networksetup", "-setsearchdomains", interface, "Empty"])
    print("DNS and search domains reset.")

def backup_configuration(interface: str, output_file: str = BACKUP_FILE):
    print("Backing up configuration...")
    with open(output_file, "w") as file:
        dns = run_command(["networksetup", "-getdnsservers", interface])
        file.write(f"DNS\n{dns}\n\n")
        domain = run_command(["networksetup", "-getsearchdomains", interface])
        file.write(f"DOMAIN\n{domain}\n\n")
        file.write("ROUTES\n# Manual routes are not backed up.\n\n")
        file.write("GATEWAY\n# Manual gateway is not backed up.\n")
    print(f"Backup saved to {output_file}.")

def main():
    parser = argparse.ArgumentParser(description="Network Configuration Manager")
    parser.add_argument("-r", action="store_true", help="Reset configuration")
    parser.add_argument("-s", action="store_true", help="Set configuration")
    parser.add_argument("-b", action="store_true", help="Backup configuration")
    parser.add_argument("-i", action="store_true", help="Create default configuration file")
    parser.add_argument("-f", metavar="CONFIG", help="Configuration file")
    parser.add_argument("-p", metavar="INTERFACE", help="Network interface")
    args = parser.parse_args()

    if args.i:
        create_default_config_file()
        sys.exit(0)

    services = list_network_services() if not args.p else []
    interface = args.p or select_network_service(services)

    if args.r:
        reset_configuration(interface)
    elif args.b:
        backup_configuration(interface)
    elif args.s:
        config_file = args.f or DEFAULT_CONFIG_FILE
        dns, domains, routes, gateway = parse_config_file(config_file)
        set_configuration(interface, dns, domains, routes, gateway)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
