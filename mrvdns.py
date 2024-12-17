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

# Function to expand CIDR range into individual IPs
def expand_cidr_range(cidr_range):
    network = ipaddress.IPv4Network(cidr_range, strict=False)
    return [str(ip) for ip in network.hosts()]

# Function to read IPs and CIDR ranges from a file
def read_ips_and_ranges_from_file(file_path):
    all_ips = []
    with open(file_path, "r") as file:
        for line in file:
            entry = line.strip()
            if not entry:
                continue
            try:
                if '/' in entry:
                    all_ips.extend(expand_cidr_range(entry))
                else:
                    ipaddress.IPv4Address(entry)
                    all_ips.append(entry)
            except ValueError:
                print(f"Invalid entry in file: {entry}, skipping.")
    return all_ips

# Main function
def main():
    parser = argparse.ArgumentParser(description="Reverse DNS Lookup Tool with Custom DNS Server")
    parser.add_argument("-s", "--subnet", help="Subnet (e.g., 10.10.10) for sequential IP range")
    parser.add_argument("-r", "--cidr", help="CIDR range (e.g., 10.10.11.0/24) for IP expansion")
    parser.add_argument("-f", "--file", help="File containing IP addresses and/or CIDR ranges")
    parser.add_argument("-d", "--dns", help="DNS server to use for lookups (e.g., 8.8.8.8)", required=True)
    parser.add_argument("-o", "--output", help="Output file to save results", default=None)
    parser.add_argument("-t", "--threads", help="Number of concurrent threads (default: 10)", type=int, default=10)
    args = parser.parse_args()

    # Collect all IPs
    ip_list = []
    if args.subnet:
        print(f"Generating sequential IP range for subnet: {args.subnet}.0/24")
        ip_list.extend(generate_sequential_ips(args.subnet))
    if args.cidr:
        print(f"Expanding CIDR range: {args.cidr}")
        ip_list.extend(expand_cidr_range(args.cidr))
    if args.file:
        print(f"Reading IPs and ranges from file: {args.file}")
        ip_list.extend(read_ips_and_ranges_from_file(args.file))

    if not ip_list:
        print("No valid IPs or ranges found. Please provide input using -s, -r, or -f.")
        return

    # Perform Reverse DNS Lookups
    print("Starting Reverse DNS Lookups...")
    results = []
    with ThreadPoolExecutor(max_workers=args.threads) as executor:
        futures = [executor.submit(reverse_dns_lookup, ip, args.dns) for ip in ip_list]
        for future in futures:
            result = future.result()
            print(result)
            results.append(result)

    # Save results to file if specified
    if args.output:
        with open(args.output, "w") as file:
            file.write("IP Address\tReverse DNS Name\n")
            file.write("\n".join(results))
        print(f"Results saved to {args.output}")

if __name__ == "__main__":
    main()
