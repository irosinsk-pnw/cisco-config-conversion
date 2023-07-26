# Takes an Enterasys EOS configuration file and creates a Cisco configuration for each switchport.
# Input the EOS config by pasting it on the CLI and pressing Ctrl+D at the end,
# or redirect it like `python ports-ex-to-cisco.py < config.txt`
import sys, re

print("Paste the Enterasys config file below, then press Ctrl+D...", file=sys.stderr)
originalConfig = sys.stdin.readlines()
print()

aliases = {}    # Display string of each port
vlanTags = {}   # Tag number of each VLAN
portVlans = {}  # Array of each port's VLANs
untagged = {}   # Each port's untagged VLAN

voipVlan = "0"      # VoIP VLAN is handled differently from the rest
studentVlan = "0"   # Default VLAN for blank ports

# Matches lines adding an alias for ports up to port 48 (excludes fiber ports)
displayStringRegex = re.compile(
    r'set port alias (?P<port>ge\.\d\.((\d\b)|([1-3]\d\b)|(4[0-8]\b))) "(?P<alias>.+\b)"')

# Matches lines adding VLAN to a port
vlanPortRegex = re.compile(
    r"set port vlan (?P<port>ge\.\d\.((\d\b)|([1-3]\d\b)|(4[0-8]\b))) (?P<vlan>\d{1,4}\b)")

# Matches lines adding a name for a VLAN
vlanNameRegex = re.compile(
    r'set vlan name (?P<vlan>\d{1,4}\b) "(?P<name>[\w\-\(\) ]+\b)"')

# Matches lines setting egress on a port
vlanUntaggedRegex = re.compile(
    r"set vlan egress (?P<vlan>\d{1,4}\b) (?P<ports>((ge|tg|lag)\.\d\.\d\d?(-\d\d?)?;)*(ge|tg|lag)\.\d\.\d\d?(-\d\d?)?\b) untagged")

ciscodpRegex = re.compile(
    r"set ciscodp port vvid (?P<vlan>\d{1,4}\b) (?P<port>ge\.\d\.((\d\b)|([1-3]\d\b)|(4[0-8]\b)))")

def port_range_to_list(portString):
    """Converts a port range, like "ge.2.31-34;ge.3.1;tg.3.50", into a list of individual port strings."""

    output = []
    ranges = portString.split(";")
    for string in ranges:
        if string.startswith("ge."):
            (ge,switch,ports) = string.split(".")
            if "-" in ports:
                (rangeStart, rangeEnd) = ports.split("-")
                for i in range(int(rangeStart),int(rangeEnd)+1):
                    output.append( "ge."+switch+"."+str(i) )

            else:
                output.append( "ge."+switch+"."+ports )

    return output

for line in originalConfig:

    # Get port aliases
    if (match := displayStringRegex.match(line)) is not None:
        aliases[match["port"]] = match["alias"]

    # Get VLAN names
    elif (match := vlanNameRegex.match(line)) is not None:
        vlanTags[match["vlan"]] = match["name"]
        if "voip" in match["name"].lower():
            voipVlan = match["vlan"]
        elif "student" in match["name"].lower():
            studentVlan = match["vlan"]

    # Get which ports have which VLANs
    elif (match := vlanPortRegex.match(line)) is not None:
        # Array of tagged ports may not yet exist
        if (portVlans.get(match["port"]) is None):
            portVlans[match["port"]] = [match["vlan"]]
        else:
            portVlans[match["port"]].append(match["vlan"])

    elif (match := vlanUntaggedRegex.match(line)) is not None:
        for port in port_range_to_list(match["ports"]):
            untagged[port] = match["vlan"]

    # Get which ports have VoIP VLAN
    elif (match := ciscodpRegex.match(line)) is not None:
        if (portVlans.get(match["port"]) is None):
            portVlans[match["port"]] = [match["vlan"]]
        else:
            portVlans[match["port"]].append(match["vlan"])


# Print the new configuration
numSwitches = int(reversed(aliases.keys()).__next__()[3])
for switch in range(1,numSwitches+1):
    for portNum in range(1,49):
        port = "ge."+str(switch)+"."+str(portNum)

        print(f"interface GigabitEthernet{switch}/0/{portNum}")
        print(f"  switchport mode access")

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
            if (vlanList := portVlans.get(port)) is not None:
                for vlanTag in vlanList:
                    if untagged[port] != vlanTag:
                        if vlanTag == voipVlan:
                            print(f"  switchport voice vlan {vlanTag}")
                        else:
                            print(f"  switchport trunk vlan {vlanTag}")

print()
