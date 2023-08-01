These scripts automate moving certain sections of switch config from Extreme or Enterasys to Cisco.

Scripts named with "en" convert Enterasys configs, and scripts with "ex" convert Extreme configs.

The "vlans" scripts will read the VLAN names and numbers from the old config, and print them out in Cisco config format, like:

```
vlan 10
  name Student
vlan 20
  name Admin
```
The "ports" scripts will read port numbers, aliases, and VLANs from the old config, and print them out in Cisco config format, like:

```
interface GigabitEthernet1/0/1
  switchport mode access
  description "101-A"
  switchport access vlan 10
  switchport voice vlan 398
. . .
```
Each script reads in the entire old configuration file from STDIN, and will output the new configuration sections to STDOUT.

If you run it as `python {script-name}`, you will need to paste the old configuration into the terminal, and the new configuration will be dumped onto the terminal.

You can also run it with redirection, like `python {script-name} <input.txt >output.txt`.