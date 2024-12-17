#!/usr/bin/env python3

import ipaddress
import argparse
import subprocess
from concurrent.futures import ThreadPoolExecutor

# Function to perform Reverse DNS Lookup using nslookup with a custom DNS server
def reverse_dns_lookup(ip, dns_server):
    try:
        result = subprocess.run(
            ["nslookup", ip, dns_server],
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True,
            timeout=5
        )
        output = result.stdout
        # Parse the output to find the PTR record
        for line in output.splitlines():
            if "name =" in line:
                reverse_name = line.split("name =")[-1].strip()
                return f"{ip}\t{reverse_name}"
        return f"{ip}\tNo PTR Record Found"
    except subprocess.TimeoutExpired:
        return f"{ip}\tTimeout"
    except Exception as e:
        return f"{ip}\tError: {str(e)}"

# Function to generate sequential IP addresses
def generate_sequential_ips(subnet):
    network = ipaddress.IPv4Network(f"{subnet}.0/24", strict=False)
    return [str(ip) for ip in network.hosts()]

# Function to expand CIDR range
def expand_cidr_range(cidr_range):
    network = ipaddress.IPv4Network(cidr_range, strict=False)
    return [str(ip) for ip in network.hosts()]

# Function to read IPs from a file
def read_ips_from_file(file_path):
    with open(file_path, "r") as file:
        return [line.strip() for line in file if line.strip()]

# Main function
def main():
    parser = argparse.ArgumentParser(description="Reverse DNS Lookup Tool with Custom DNS Server")
    parser.add_argument("-s", "--subnet", help="Subnet (e.g., 10.10.10) for sequential IP range")
    parser.add_argument("-r", "--cidr", help="CIDR range (e.g., 10.10.10.0/24) for IP expansion")
    parser.add_argument("-f", "--file", help="File containing IP addresses (one per line)")
    parser.add_argument("-d", "--dns", help="DNS server to use for lookups (e.g., 8.8.8.8)", required=True)
    parser.add_argument("-o", "--output", help="Output file to save results", default=None)
    parser.add_argument("-t", "--threads", help="Number of concurrent threads (default: 10)", type=int, default=10)
    args = parser.parse_args()

    # Validate input
    if not args.subnet and not args.cidr and not args.file:
        print("Error: Either --subnet, --cidr, or --file must be provided.")
        parser.print_help()
        return

    # Generate list of IP addresses
    if args.subnet:
        print(f"Generating sequential IP range for subnet: {args.subnet}.0/24")
        ip_list = generate_sequential_ips(args.subnet)
    elif args.cidr:
        print(f"Expanding CIDR range: {args.cidr}")
        ip_list = expand_cidr_range(args.cidr)
    elif args.file:
        print(f"Reading IPs from file: {args.file}")
        ip_list = read_ips_from_file(args.file)

    # Perform Reverse DNS Lookups
    print("Starting Reverse DNS Lookups...")
    results = []
    with ThreadPoolExecutor(max_workers=args.threads) as executor:
        futures = [executor.submit(reverse_dns_lookup, ip, args.dns) for ip in ip_list]
        for future in futures:
            result = future.result()
            print(result)  # Print each result
            results.append(result)

    # Save results to file if specified
    if args.output:
        with open(args.output, "w") as file:
            file.write("IP Address\tReverse DNS Name\n")
            file.write("\n".join(results))
        print(f"Results saved to {args.output}")

if __name__ == "__main__":
    main()
