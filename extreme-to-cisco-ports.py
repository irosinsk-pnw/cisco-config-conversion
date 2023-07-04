# Takes an Extreme EXOS configuration file and creates a Cisco configuration for each switchport.
# Input the EXOS config by pasting it on the CLI and pressing Ctrl+D at the end,
# or redirect it like `python extreme-to-cisco-ports.py < config.txt`
import sys, re

originalConfig = sys.stdin.readlines()
print()

aliases = {}    # Display string of each port
vlanTags = {}   # Tag number of each VLAN
untagged = {}   # Each port's untagged VLAN
tagged = {}     # Array of each port's tagged VLANs

# Matches lines adding a description string for ports up to port 48 (excludes fiber ports)
displayStringRegex = re.compile(
    r'configure ports (?P<port>\d:((\d\b)|([1-3]\d\b)|(4[0-8]\b))) description-string "(?P<alias>[\w\-]+\b)"')

# Matches lines giving a VLAN a tag number
vlanTagRegex = re.compile(
    r"configure vlan (?P<name>[\w\-]+\b) tag (?P<tag>\d{1,4}\b)")

# Matches lines adding a port or range of ports to a VLAN
vlanPortRegex = re.compile(
    r"configure vlan (?P<name>[\w\-]+\b) add ports (?P<ports>(\d:(\d\d?)(-\d\d?)?,)*\d:(\d\d?)(-\d\d?)?\b) (?P<tagged>(untagged)|(tagged)\b)")

def port_range_to_list(portString):
    """Converts a port range, like "1:3-14,2:4,2:6-10", into a list of individual port strings."""

    output = []
    ranges = portString.split(",")
    for string in ranges:
        if "-" in string:
            rangeStart = int(string[string.find(":")+1 : string.find("-")])
            rangeEnd = int(string[string.find("-")+1 : len(string)])
            for i in range(rangeStart, rangeEnd+1):
                output.append(string[0:string.find(":")] + ":" + str(i))

        else:
            output.append(string)

    return output

for line in originalConfig:

    # Get port aliases
    if (match := displayStringRegex.match(line)) is not None:
        aliases[match.group("port")] = match.group("alias")

    # Get VLAN tag numbers
    elif (match := vlanTagRegex.match(line)) is not None:
        vlanTags[match.group("name")] = match.group("tag")

    # Get which ports have which VLANs
    elif (match := vlanPortRegex.match(line)) is not None:
        for port in port_range_to_list(match.group("ports")):

            if (match.group("tagged") == "untagged"):
                untagged[port] = match.group("name")
            else:
                # Array of tagged ports may not yet exist
                if (tagged.get(port) is None):
                    tagged[port] = [match.group("name")]
                else:
                    tagged[port].append(match.group("name"))

# Print the new configuration
for port in aliases:
    (switch, dummy, portNum) = port.partition(":")
    print(f"interface GigabitEthernet{switch}/0/{portNum}")
    print(f"  description {aliases[port]}")
    if (vlanTag := vlanTags.get(untagged.get(port))) is not None:
        print(f"  switchport access vlan {vlanTag}")
    if (vlanList := tagged.get(port)) is not None:
        for vlanName in vlanList:
            if (vlanTag := vlanTags.get(vlanName)) is not None:
                if "voip" in vlanName.lower():
                    print(f"  switchport voice vlan {vlanTag}")
                else:
                    print(f"  switchport trunk vlan {vlanTag}")

print()
