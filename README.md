
# macOS-RoutingDNS

This script is designed to manage network configurations on macOS. It allows you to set, reset, backup, and restore DNS, search domains, routes, and gateway configurations for a selected network interface.

## Features

- **Interactive Network Selection**: Lists available network services for user selection.
- **Configuration Backup and Restore**: Save and restore DNS and search domain configurations.
- **Custom Configuration File Parsing**: Parse and apply configurations from a user-defined file.
- **Default Configuration Initialization**: Create a template configuration file for easy setup.
- **Reset Functionality**: Reset network configurations to defaults.
- **Command-Line Options**: Flexible options for various operations.

## Limitations

- **macOS Script**: This script is designed exclusively for macOS and uses `networksetup` commands.
- **Single Gateway Support**: The script supports configuring only one gateway at a time.

## Requirements

- macOS
- Sudo privileges

## Usage

### Options

```
-i                  Initialize a default configuration file.
-b                  Backup current network settings.
-be                 Restore network settings from backup.
-s                  Apply network settings from a configuration file.
-r                  Reset DNS, search domains, and routes to default.
-f <file>           Specify a custom configuration file.
-p <interface>      Specify a network interface.
-o <output_file>    Specify output file for initialization or backup.
-h                  Display help information.
```

### Examples

1. **Initialize a Default Configuration File**:
   ```bash
   ./route.sh -i -o my_config.ini
   ```

2. **Set Configuration from a File**:
   ```bash
   ./route.sh -s -f custom_config.ini -p "Wi-Fi"
   ```

3. **Reset Network Configuration**:
   ```bash
   ./route.sh -r -p "Wi-Fi"
   ```

4. **Backup Current Configuration**:
   ```bash
   ./route.sh -b -p "Wi-Fi" -o backup_config.ini
   ```

5. **Restore Configuration from Backup**:
   ```bash
   ./route.sh -be
   ```

## File Structure

- **config.ini**: Default configuration file with example values.
- **config_backup.ini**: Backup file for storing current network settings.

## Notes

- This script is macOS-specific and utilizes the `networksetup` command.
- Ensure you have the necessary permissions to modify network settings.

## Contributing

Contributions are welcome! Please submit a pull request with any improvements or fixes.

## License

This project is licensed under the MIT License.

