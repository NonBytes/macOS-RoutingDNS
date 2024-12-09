#!/bin/bash

# Variables for configuration
DNS_SERVERS=()
SEARCH_DOMAIN=()
ROUTES=()
GATEWAY=""
BACKUP_FILE="config_backup.ini"

# Default configuration file
DEFAULT_CONFIG_FILE="config.ini"

# Function to create a default configuration file with examples
create_default_config_file() {
    local output_file="${1:-$DEFAULT_CONFIG_FILE}" # Use passed argument or default to config.ini

    if [[ -f "$output_file" ]]; then
        echo "Error: Configuration file '$output_file' already exists."
        exit 1
    fi

    cat << EOF > "$output_file"
# Default configuration file with example values
# Replace the example values with your own configuration
# If you don't need a section, leave it empty.

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
EOF

    echo "Default configuration file '$output_file' created with example values. Please edit it as needed."
}

# Function to backup current configuration
backup_config() {
    local output_file="${1:-$BACKUP_FILE}" # Use passed argument or default to config_backup.ini

    echo "Backing up current configuration for interface $SELECTED_INTERFACE..."
    {
        echo "DNS"
        DNS=$(networksetup -getdnsservers "$SELECTED_INTERFACE" 2>/dev/null)
        if [[ $DNS == "There aren't any DNS Servers set on"* ]]; then
            echo "#No existing configuration detected."
        else
            echo "$DNS"
        fi
        echo

        echo "DOMAIN"
        DOMAIN=$(networksetup -getsearchdomains "$SELECTED_INTERFACE" 2>/dev/null)
        if [[ $DOMAIN == "There aren't any Search Domains set on"* ]]; then
            echo "#No existing configuration detected."
        else
            echo "$DOMAIN"
        fi
        
        echo
        echo "ROUTES"
        echo "#The route table does not support backups."
        echo
        echo "GATEWAY"
        echo "#The route gateway does not support backups."
    } > "$output_file"

    echo "Backup created at '$output_file'."
}

# Function to display help text
display_help() {
    echo "Usage: $0 [-r | -s | -b | -be] [-p <network_service>] [-f <config_file>] | -i [-o <output_file>]"
    echo
    echo "Options:"
    echo "  -r                 Reset DNS, search domain, and routes."
    echo "  -s                 Set DNS, search domain, and routes using configuration file."
    echo "  -b                 Backup current configuration to 'config_backup.ini' or specified file."
    echo "  -be                Restore configuration from 'config_backup.ini'."
    echo "  -p <interface>     Specify the network interface (e.g., Wi-Fi)."
    echo "  -f <config_file>   Specify a custom configuration file. Defaults to 'config.ini'."
    echo "  -i                 Create a default 'config.ini' file with example values."
    echo "  -o <output_file>   Specify the output file for backup or initialization."
    echo
    echo "If no arguments are provided and 'config.ini' is not found, use '-i' to create a configuration file."
}

# Function to parse the configuration file
parse_config_file() {
    local CONFIG_FILE=$1

    if [[ ! -f "$CONFIG_FILE" ]]; then
        echo "Error: Configuration file '$CONFIG_FILE' not found."
        exit 1
    fi

    local SECTION=""
    while IFS= read -r line || [[ -n "$line" ]]; do
        # Trim leading and trailing whitespace
        line=$(echo "$line" | xargs)

        # Skip global comments and empty lines
        if [[ -z "$line" || "$line" == \#* ]]; then
            # Skip if it's a comment or empty outside any section
            [[ -z "$SECTION" ]] && continue
            # Skip comments within a section
            [[ "$line" == \#* ]] && continue
        fi

        # Detect section headers
        case $line in
            DNS)
                SECTION="DNS"
                ;;
            DOMAIN)
                SECTION="DOMAIN"
                ;;
            ROUTES)
                SECTION="ROUTES"
                ;;
            GATEWAY)
                SECTION="GATEWAY"
                ;;
            "")
                SECTION=""
                ;;
            *)
                # Add to appropriate section
                case $SECTION in
                    DNS)
                        DNS_SERVERS+=("$line")
                        ;;
                    DOMAIN)
                        SEARCH_DOMAIN+=("$line")
                        ;;
                    ROUTES)
                        ROUTES+=("$line")
                        ;;
                    GATEWAY)
                        GATEWAY="$line"
                        ;;
                    *)
                        echo "Warning: Line '$line' does not belong to any recognized section."
                        ;;
                esac
                ;;
        esac
    done < "$CONFIG_FILE"
}


# Function to set DNS, search domain, and routes
set_configuration() {
    if [ ${#DNS_SERVERS[@]} -eq 0 ]; then
        echo "Skipping DNS configuration: No DNS servers specified."
    else
        echo "Configuring DNS for interface $SELECTED_INTERFACE..."
        sudo networksetup -setdnsservers "$SELECTED_INTERFACE" "${DNS_SERVERS[@]}"
        echo "DNS servers configured: ${DNS_SERVERS[*]}"
    fi

    if [ ${#SEARCH_DOMAIN[@]} -eq 0 ]; then
        echo "Skipping search domain configuration: No domains specified."
    else
        echo "Configuring search domains for interface $SELECTED_INTERFACE..."
        sudo networksetup -setsearchdomains "$SELECTED_INTERFACE" "${SEARCH_DOMAIN[@]}"
        echo "Search domains configured: ${SEARCH_DOMAIN[*]}"
    fi

    if [ ${#ROUTES[@]} -eq 0 ]; then
        echo "Skipping route configuration: No routes specified."
    else
        echo "Adding routes..."
        for route in "${ROUTES[@]}"; do
            sudo route add $route $GATEWAY
            echo "Route added: $route via $GATEWAY"
        done
    fi
}

# Function to list available network services with numbers
list_network_services() {
    echo "Available network services:"
    SERVICES=($(networksetup -listallnetworkservices | tail -n +2)) # Get services and skip the header
    for i in "${!SERVICES[@]}"; do
        echo "$((i + 1)). ${SERVICES[$i]}"
    done
}

# Function to select a network service by number
select_network_service() {
    list_network_services
    echo
    read -p "Enter the number of the network service: " SELECTED_NUMBER

    # Validate input
    if ! [[ "$SELECTED_NUMBER" =~ ^[0-9]+$ ]] || [[ "$SELECTED_NUMBER" -lt 1 || "$SELECTED_NUMBER" -gt "${#SERVICES[@]}" ]]; then
        echo "Invalid selection. Please run the script again and select a valid number."
        exit 1
    fi

    SELECTED_INTERFACE="${SERVICES[$((SELECTED_NUMBER - 1))]}"
    echo "You selected: $SELECTED_INTERFACE"
}

# Function to reset DNS, search domain, and routes
reset_configuration() {
    echo "Resetting DNS and search domain for interface $SELECTED_INTERFACE..."

    sudo networksetup -setdnsservers "$SELECTED_INTERFACE" "Empty"
    echo "DNS servers reset to default (automatic)."

    sudo networksetup -setsearchdomains "$SELECTED_INTERFACE" "Empty"
    echo "Search domains reset to default (automatic)."

    if [ ${#ROUTES[@]} -eq 0 ]; then
        echo "Skipping route removal: No routes specified."
    else
        echo "Removing custom routes..."
        for route in "${ROUTES[@]}"; do
            sudo route delete $route
            echo "Route removed: $route"
        done
    fi
}

# Function to restore backup
restore_backup() {
    if [[ ! -f "$BACKUP_FILE" ]]; then
        echo "Error: Backup file '$BACKUP_FILE' not found."
        exit 1
    fi

    echo "Restoring configuration from backup..."
    parse_config_file "$BACKUP_FILE"
    set_configuration
    echo "Configuration restored from '$BACKUP_FILE'."
}

# Main logic to parse options and execute commands
OUTPUT_FILE=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        -r)
            MODE="reset"
            shift
            ;;
        -s)
            MODE="set"
            shift
            ;;
        -b)
            MODE="backup"
            shift
            ;;
        -be)
            MODE="restore"
            shift
            ;;
        -p)
            SELECTED_INTERFACE="$2"
            shift 2
            ;;
        -f)
            CONFIG_FILE="$2"
            shift 2
            ;;
        -i)
            MODE="init"
            shift
            ;;
        -o)
            OUTPUT_FILE="$2"
            shift 2
            ;;
        *)
            display_help
            exit 1
            ;;
    esac
done

# Ensure a mode is specified
if [ -z "$MODE" ]; then
    echo "Error: You must specify one of -r, -s, -b, -be, or -i."
    display_help
    exit 1
fi

# Interactive interface selection if no interface is specified
if [[ "$MODE" != "init" && -z "$SELECTED_INTERFACE" ]]; then
    select_network_service
fi

# Execute the selected mode
case "$MODE" in
    init)
        OUTPUT_FILE="${OUTPUT_FILE:-$DEFAULT_CONFIG_FILE}"
        create_default_config_file "$OUTPUT_FILE"
        ;;
    backup)
        OUTPUT_FILE="${OUTPUT_FILE:-$BACKUP_FILE}"
        backup_config "$OUTPUT_FILE"
        ;;
    set)
        CONFIG_FILE="${CONFIG_FILE:-$DEFAULT_CONFIG_FILE}"
        if [[ ! -f "$CONFIG_FILE" ]]; then
            echo "Error: Configuration file '$CONFIG_FILE' not found."
            exit 1
        fi
        parse_config_file "$CONFIG_FILE"
        set_configuration
        ;;
    reset)
        reset_configuration
        ;;
    restore)
        restore_backup
        ;;
esac

echo "Operation ($MODE) complete."
