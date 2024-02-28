# Cisco configuration converter

This script will generate VLAN or interface configurations for a Cisco switch, based on an original Extreme or Enterasys configuration.

## Usage

Command line: `cisco_conversion.py [-h] (-E | -X) [--vlans] [--k6] [-w | -b] [-d DEFAULT] [-v VOIP] [filename]`

### Arguments

`-h`, `--help`:  
Prints the help message and exits.

`-E`, `--enterasys`  
`-X`, `--extreme`:  
Specifies whether the input configuration file is from an Enterasys switch or an Extreme switch.  
(You must specify one of Enterasys or Extreme, but not both.)

`--vlans`:  
Generates the VLAN configuration section. If this option is not present, will generate the interface configuration section.  
See Output for more information.

`--k6`:  
If generating an interface configuration for an Enterasys switch, the script will assume the original config has six 24-port switches that are being converted into three 48-port switches.  
Switches 1 and 2 are combined into new switch 1, 3 and 4 are combined into new switch 2, and so on.

`-b`, `--blue`  
`-w`, `--white`:  
These options control the interface configuration output, allowing the generated configuration to be used on a "blue" 3850-multigig, with the last 12 ports being ten-gigabit, or a "white" 9348, with the first 36 being two-gigabit and the last 12 being ten-gigabit.  
You may specify one of these options, or neither. If neither is specified, the output will have all ports at one-gigabit. See Output for more information.

`-d [DEFAULT]`, `--default [DEFAULT]`:  
This option allows you to manually specify a default VLAN number, which will be used on ports that have no configuration. Usually, this is the number of the Student VLAN.  
If this option is not specified, the program will attempt to automatically find the Student VLAN; if no suitable VLAN is found, empty ports will be left without a VLAN.

`-v [VOIP]`, `--voip [VOIP]`:  
This option allows you to manually specify a VoIP VLAN number, which will be used to determine what ports require a voice configuration.  
If this option is not specified, the program will attempt to automatically find the VoIP VLAN; if no suitable VLAN is found, no voice configuration will be done.

`[filename]`:  
At the end of the command line, you can specify a file to read the original configuration from. See Input for more details.

### Input

The script takes as input an entire Extreme or Enterasys configuration. If you have that configuration saved as a file, you can pass the file's name as the last command line parameter. If no filename is given, the program will read from standard input. You can paste the configuration onto your terminal, then press Ctrl+Z then Enter (Windows) or Ctrl+D (Mac/Linux) to end the input.

### Output

The script will print the configuration sections to standard output. By default, this will dump them on your terminal screen; you can also use redirection to send it to a file.  
For example: `cisco_conversion.py -E > new-config.txt` will print the configuration section to the file `new-config.txt`.

If you specify the `--vlans` option, the script will print out a VLAN configuration suitable for Cisco, along with a list of VLAN tag numbers that can be added to an uplink interface.  
Example:  
`cisco_conversion.py -E --vlans nw-hmd-bldg-x440-s1.txt`

    vlan 2
     name Student
    vlan 172
     name NIMM
    vlan 2911
     name VoIP
    
    VLAN tag list:
    2,172,2911

If you do not specify the `--vlans` option, the script will print out an interface configuration. This will be 48 blocks like the following:

    interface GigabitEthernet1/0/1
     description 123-D
     switchport mode access
     switchport access vlan 2
     switchport voice vlan 2911

The script will automatically determine the description and VLANs, whether there are any trunked VLANs, and whether there is a voice VLAN, all based on the input configuration.  
If the option `--blue` is specified, the last 12 ports of each switch will be TenGigabitEthernet, rather than GigabitEthernet, to match a c3850mg.  
If the option `--white` is specified, the first 36 ports of each switch will be TwoGigabitEthernet and the last 12 will be TenGigabitEthernet, to match a c9348uxm.

## Credits

This script was created by Isaiah Rosinski, originally for use by the PNW Field Operations team. It is licensed under the MIT License; see the LICENSE file.
