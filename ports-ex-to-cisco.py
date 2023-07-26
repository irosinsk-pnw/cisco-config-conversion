# Takes an Extreme EXOS configuration file and creates a Cisco configuration for each switchport.
# Input the EXOS config by pasting it on the CLI and pressing Ctrl+D at the end,
# or redirect it like `python ports-ex-to-cisco.py < config.txt`
#
# CAUTION: Do not take this output as gospel truth! Check it over manually!
# Will fill in empty ports with alias "EMPTY" and the Student and VoIP VLANs, if they exist.
# Assumes that there is only one VoIP and only one Student VLAN. If there are multiple,
# it will take the last of each as the default.
# Only configures the first 48 gigabit ports on each switch in the stack. If there are fewer
# than 48 ports in the original stack, there should be no issue.
# Assumes that each alias is only used for one port.

import sys, re

print("Paste the Extreme config file below, then press Ctrl+D...", file=sys.stderr)
originalConfig = sys.stdin.readlines()
print()

aliases = {}    # Display string of each port
vlanTags = {}   # Tag number of each VLAN
tagged = {}     # Array of each port's tagged VLANs
untagged = {}   # Each port's untagged VLAN

voipVlan = "0"      # VoIP VLAN is handled differently from the rest
studentVlan = "0"   # Default VLAN for blank ports

# Matches lines adding a description string for ports up to port 48 (excludes fiber ports)
displayStringRegex = re.compile(
    r'configure ports (?P<port>\d:((\d\b)|([1-3]\d\b)|(4[0-8]\b))) description-string "(?P<alias>.+\b)"')

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
        aliases[match["port"]] = match["alias"]

    # Get VLAN tag numbers
    elif (match := vlanTagRegex.match(line)) is not None:
        vlanTags[match["name"]] = match["tag"]
        if "student" in match["name"].lower():
            studentVlan = match["tag"]
        elif "voip" in match["name"].lower():
            voipVlan = match["tag"]

    # Get which ports have which VLANs
    elif (match := vlanPortRegex.match(line)) is not None:
        for port in port_range_to_list(match.group("ports")):

            if (match.group("tagged") == "untagged"):
                untagged[port] = vlanTags[match["name"]]
            else:
                # Array of tagged ports may not yet exist
                if (tagged.get(port) is None):
                    tagged[port] = [vlanTags[match["name"]]]
                else:
                    tagged[port].append(vlanTags[match["name"]])

# Print the new configuration
numSwitches = int(reversed(aliases.keys()).__next__()[0])
for switch in range(1,numSwitches+1):
    for portNum in range(1,49):
        port = str(switch) + ":" + str(portNum)

        print(f"interface GigabitEthernet{switch}/0/{portNum}")
        print(f"  switchport mode access")

        # If the port is empty
        if (alias := aliases.get(port)) is None:
            print(f"  description \"EMPTY\"")
            if studentVlan != "0":
                print(f"  switchport access vlan {studentVlan}")
            if voipVlan != "0":
                print(f"  switchport voice vlan {voipVlan}")
        else:
            print(f"  description \"{alias}\"")

            # Untagged VLAN
            if (vlanTag := untagged.get(port)) is not None:
                print(f"  switchport access vlan {vlanTag}")

            # Tagged VLANs
            if (vlanList := tagged.get(port)) is not None:
                for vlanTag in vlanList:
                    if vlanTag == voipVlan:
                        print(f"  switchport voice vlan {vlanTag}")
                    else:
                        print(f"  switchport trunk vlan {vlanTag}")

print()
