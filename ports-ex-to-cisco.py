# Takes an Extreme EXOS configuration file and creates a Cisco configuration for each switchport.
# Input the EXOS config by pasting it on the CLI and pressing Ctrl+D at the end,
# or redirect it like `python ports-ex-to-cisco.py < config.txt`
#
# CAUTION: Do not take this output as gospel truth! Check it over manually!
# Will fill in empty ports with alias "EMPTY" and the Student and VoIP VLANs, if they exist.
# Assumes that there is only one VoIP and only one Student VLAN. If there are multiple,
# it will take the first of each as the default.
# Only configures the first 48 gigabit ports on each switch in the stack. If there are fewer
# than 48 ports in the original stack, there should be no issue.
# Assumes that each alias is only used for one port.
# Assumes that each switch has at least one port with an alias.

import sys, re

class Port:
    """Represents one port's configuration."""
    def __init__(self):
        self.alias = None    # Str: port alias/description
        self.tagged = []     # List of ints: its tagged VLANs
        self.untagged = None # Int: its untagged VLAN
        self.voip = False     # Bool: whether VoIP is on it


def port_range_to_list(portString):
    """Converts a port range, like "1:3-14,2:4,2:6-10", into a list of individual port strings."""

    output = []
    ranges = portString.split(",")
    for string in ranges:
        if "-" in string:
            if ":" in string:
                rangeStart = int(string[string.find(":")+1 : string.find("-")])
                rangeEnd = int(string[string.find("-")+1 : len(string)])
                for i in range(rangeStart, rangeEnd+1):
                    output.append(string[0:string.find(":")] + ":" + str(i))
            else:
                rangeStart = int(string[0 : string.find("-")])
                rangeEnd = int(string[string.find("-")+1 : len(string)])
                for i in range(rangeStart, rangeEnd+1):
                    output.append(str(i))

        else:
            output.append(string)

    return output


def add_ports_to_dict(switchNum, portsDict):
    """Adds one switch's worth of ports to the dictionary."""
    for i in range(1,49):
        portString = str(switchNum) + ":" + str(i) if switchNum > 0 else str(i)
        if portString in portsDict: raise Exception(portString + " is already in dict")
        portsDict[portString] = Port()



print("Paste the Extreme config file below, then press Ctrl+D...", file=sys.stderr)
originalConfig = sys.stdin.readlines()
print(file=sys.stderr)

ports = {}      # Dictionary of port-string : Port object
vlanTags = {}   # Tag number of each VLAN

voipVlan = 0      # VoIP VLAN is handled differently from the rest
studentVlan = 0   # Default VLAN for blank ports

# Matches lines adding a description string for ports up to port 48 (excludes fiber ports)
descriptionStringRegex = re.compile(
    r'configure ports (?P<port>(\d:)?((\d\b)|([1-3]\d\b)|(4[0-8]\b))) description-string "(?P<alias>.+)"')

displayStringRegex = re.compile(
    r'configure ports (?P<port>(\d:)?((\d\b)|([1-3]\d\b)|(4[0-8]\b))) display-string (?P<alias>.+)')

# Matches lines giving a VLAN a tag number
vlanTagRegex = re.compile(
    r"configure vlan (?P<name>.+\b) tag (?P<tag>\d{1,4}\b)")

# Matches lines adding a port or range of ports to a VLAN
vlanPortRegex = re.compile(
    r"configure vlan (?P<name>.+\b) add ports (?P<ports>((\d:)?(\d\d?)(-\d\d?)?,)*(\d:)?(\d\d?)(-\d\d?)?\b) (?P<tagged>(untagged)|(tagged)\b)")


for line in originalConfig:

    # Get port aliases
    if match := displayStringRegex.match(line):
        portString = match["port"]
        if (":" not in portString and int(portString) > 48) \
        or (":" in portString and int(portString[2:]) > 48):  # Skip fiber ports
            continue

        port = ports.get(portString)
        if not port:
            add_ports_to_dict(int(portString[0]) if ":" in portString else 0, ports)
            port = ports.get(portString)
        if not port.alias:  # Description string overrides display string
            port.alias = match["alias"]


    elif match := descriptionStringRegex.match(line):

        portString = match["port"]
        if (":" not in portString and int(portString) > 48) \
        or (":" in portString and int(portString[2:]) > 48):  # Skip fiber ports
            continue

        port = ports.get(portString)
        if not port:
            add_ports_to_dict(int(portString[0]) if ":" in portString else 0, ports)
            port = ports.get(portString)
        port.alias = match["alias"]

    # Get VLAN tag numbers
    elif match := vlanTagRegex.match(line):
        vlanTags[match["name"]] = int(match["tag"])
        if not studentVlan and "student" in match["name"].lower():
            studentVlan = int(match["tag"])
        elif not voipVlan and "voip" in match["name"].lower():
            voipVlan = int(match["tag"])

    # Get which ports have which VLANs
    elif (match := vlanPortRegex.match(line)) is not None:
        if match["name"] != "Default":
            for portString in port_range_to_list(match["ports"]):

                if (":" not in portString and int(portString) > 48) \
                or (":" in portString and int(portString[2:]) > 48):  # Skip fiber ports
                    continue

                port = ports.get(portString)
                if not port:
                    add_ports_to_dict(int(portString[0]) if ":" in portString else 0, ports)
                    port = ports.get(portString)

                if match["tagged"] == "untagged":
                    port.untagged = vlanTags[match["name"]]
                elif vlanTags[match["name"]] == voipVlan:
                    port.voip = True
                else:
                    port.tagged.append(vlanTags[match["name"]])


# Print the new configuration
if len(ports) > 48:
    numSwitches = len(ports)//48
else:
    numSwitches = 1

for switch in range(1,numSwitches+1):
    for portNum in range(1,49):

        port = ports[str(switch) + ":" + str(portNum)] if numSwitches > 1 else ports[str(portNum)]

        print(f"interface GigabitEthernet{switch}/0/{portNum}")

        if len(port.tagged) == 0:
            print("  switchport mode access")
        else:
            print("  switchport mode trunk")

        # If the port is empty
        if not port.alias:
            print(f"  description EMPTY")
            if studentVlan and not port.untagged:
                print(f"  switchport access vlan {studentVlan}")
            if voipVlan:
                print(f"  switchport voice vlan {voipVlan}")
        else:
            print(f"  description {port.alias}")
            if port.voip:
                print(f"  switchport voice vlan {voipVlan}")

        # Untagged VLAN
        if port.untagged:
            print(f"  switchport access vlan {port.untagged}")

        # Tagged VLANs
        if len(port.tagged):
            trunkedVlans = ""
            trunkedVlans += str(port.tagged[0])
            for i in range(1,len(port.tagged)):
                trunkedVlans += (", " + str(port.tagged[i]))
            print(f"  switchport trunk allowed vlan {trunkedVlans}")

print()
