# Takes an Enterasys EOS configuration file and creates a Cisco configuration for each switchport.
#
# Input the EOS config by pasting it on the CLI and pressing Ctrl+D at the end,
# or redirect it like `python ports-ex-to-cisco.py < config.txt`
#
# CAUTION: Do not take this output as gospel truth! Check it over manually!
# Will fill in empty ports with alias "EMPTY" and the Student and VoIP VLANs, if they exist.
# Assumes that there is only one VoIP and only one Student VLAN. If there are multiple,
# it will take the last of each as the default.
# Only configures the first 48 gigabit ports on each switch in the stack. If there are fewer
# than 48 ports in the original stack, there should be no issue.
# Assumes that each alias is only used for one port.

import sys, re, argparse

# Allows manual specification of default and VoIP VLANs
parser = argparse.ArgumentParser()
parser.add_argument("-d", "--default", type=int, help="Default VLAN for empty ports")
parser.add_argument("-v", "--voip", type=int, help="VoIP VLAN")
args = parser.parse_args()

class Port:
    """Represents one port's configuration."""
    def __init__(self):
        self.alias = None    # Str: port alias/description
        self.tagged = []     # List of ints: its tagged VLANs
        self.untagged = None # Int: its untagged VLAN
        self.voip = False     # Bool: whether VoIP is on it


def port_range_to_list(portString):
    """Converts a port range, like "ge.2.20,24,31-34;ge.3.1;tg.3.50", into a list of individual port strings."""
    output = []
    for string in portString.split(";"):
        if string.startswith("ge."):
            (ge,switch,ranges) = string.split(".")
            for string in ranges.split(","):
                if "-" in string:
                    (rangeStart, rangeEnd) = string.split("-")
                    for i in range(int(rangeStart),int(rangeEnd)+1):
                        output.append( "ge."+switch+"."+str(i) )

                else:
                    output.append( "ge."+switch+"."+string )
    return output


def add_ports_to_dict(switchNum, portsDict):
    """Adds one switch's worth of ports to the dictionary."""
    for i in range(1,49):
        portString = "ge." + str(switchNum) + "." + str(i)
        if portString in portsDict: raise Exception(portString + " is already in dict")
        portsDict[portString] = Port()


print("Paste the Enterasys config file below, then press Ctrl+D...", file=sys.stderr)
originalConfig = sys.stdin.readlines()
print(file=sys.stderr)

ports = {}      # Dictionary of port-string : Port object
vlanTags = {}   # Tag number of each VLAN

voipVlan = args.voip if args.voip else 0            # VoIP VLAN gets a different config line
studentVlan = args.default if args.default else 0   # Default VLAN for blank ports

# Matches lines adding an alias for ports up to port 48 (excludes fiber ports)
displayStringRegex = re.compile(
    r'set port alias (?P<port>ge\.\d\.((\d\b)|([1-3]\d\b)|(4[0-8]\b))) "?(?P<alias>.+[^"\s])"?')

# Matches lines adding a name for a VLAN
vlanNameRegex = re.compile(
    r'set vlan name (?P<vlan>\d{1,4}\b) "?(?P<name>.+)"?')

# Matches lines setting egress on a port
vlanEgressRegex = re.compile(
    r"set vlan egress (?P<vlan>\d{1,4}) (?P<ports>(((ge|tg|lag|tbp)\.\d\.(\d\d?(-\d\d?)?,)*\d\d?(-\d\d?)?);)*(ge|tg|lag|tbp)\.\d\.(\d\d?(-\d\d?)?,)*\d\d?(-\d\d?)?) (?P<tagged>(untagged)|(tagged))")


for line in originalConfig:

    # Get port aliases
    if match := displayStringRegex.match(line):
        portString = match["port"]
        port = ports.get(portString)
        if not port:
            add_ports_to_dict(int(portString[3]), ports)
            port = ports.get(portString)
        port.alias = match["alias"]

    # Get VLAN names
    elif match := vlanNameRegex.match(line):
        vlanTags[match["vlan"]] = match["name"]
        if not voipVlan and "voip" in match["name"].lower():
            voipVlan = int(match["vlan"])
        elif not studentVlan and "student" in match["name"].lower():
            studentVlan = int(match["vlan"])

    elif match := vlanEgressRegex.match(line):
        for portString in port_range_to_list(match["ports"]):
            port = ports.get(portString)
            if not port:
                add_ports_to_dict(portString[3], ports)
                port = ports.get(portString)
            if match["tagged"] == "untagged":
                port.untagged = int(match["vlan"])
            elif int(match["vlan"]) == voipVlan:
                port.voip = True
            else:
                port.tagged.append(int(match["vlan"]))


# Print the new configuration
numSwitches = len(ports)//48 if len(ports) > 48 else 1

for switch in range(1,numSwitches+1):
    for portNum in range(1,49):
        port = ports["ge."+str(switch)+"."+str(portNum)]

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
