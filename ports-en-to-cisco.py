# Takes an Enterasys EOS configuration file and creates a Cisco configuration for each switchport.
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

import sys, re

print("Paste the Enterasys config file below, then press Ctrl+D...", file=sys.stderr)
originalConfig = sys.stdin.readlines()
print(file=sys.stderr)

aliases = {}    # Display string of each port
vlanTags = {}   # Tag number of each VLAN
portVlans = {}  # Array of each port's VLANs
untagged = {}   # Each port's untagged VLAN

voipVlan = "0"      # VoIP VLAN is handled differently from the rest
studentVlan = "0"   # Default VLAN for blank ports

# Matches lines adding an alias for ports up to port 48 (excludes fiber ports)
displayStringRegex = re.compile(
    r'set port alias (?P<port>ge\.\d\.((\d\b)|([1-3]\d\b)|(4[0-8]\b))) "(?P<alias>.+)"')

# Matches lines adding VLAN to a port
vlanPortRegex = re.compile(
    r"set port vlan (?P<port>ge\.\d\.((\d\b)|([1-3]\d\b)|(4[0-8]\b))) (?P<vlan>\d{1,4}\b)")

# Matches lines adding a name for a VLAN
vlanNameRegex = re.compile(
    r'set vlan name (?P<vlan>\d{1,4}\b) "(?P<name>.+)"')

# Matches lines setting egress on a port
vlanEgressRegex = re.compile(
    r"set vlan egress (?P<vlan>\d{1,4}\b) (?P<ports>((ge|tg|lag)\.\d\.\d\d?(-\d\d?)?;)*(ge|tg|lag)\.\d\.\d\d?(-\d\d?)?\b) (?P<tagged>(untagged)|(tagged))")

#ciscodpRegex = re.compile(
#    r"set ciscodp port vvid (?P<vlan>\d{1,4}\b) (?P<port>ge\.\d\.((\d\b)|([1-3]\d\b)|(4[0-8]\b)))")

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
        if portVlans.get(match["port"]) is None:
            portVlans[match["port"]] = [match["vlan"]]
        else:
            portVlans[match["port"]].append(match["vlan"])

    elif (match := vlanEgressRegex.match(line)) is not None:
        for port in port_range_to_list(match["ports"]):
            if portVlans.get(port) is None:
                portVlans[port] = [match["vlan"]]
            else:
                portVlans[port].append(match["vlan"])
            if match["tagged"] == "untagged":
                untagged[port] = match["vlan"]

#    # Get which ports have VoIP VLAN
#    elif (match := ciscodpRegex.match(line)) is not None:
 #       if (portVlans.get(match["port"]) is None):
  #          portVlans[match["port"]] = [match["vlan"]]
   #     else:
    #        portVlans[match["port"]].append(match["vlan"])


# Print the new configuration
numSwitches = int(reversed(aliases.keys()).__next__()[3])
for switch in range(1,numSwitches+1):
    for portNum in range(1,49):
        port = "ge."+str(switch)+"."+str(portNum)

        print(f"interface GigabitEthernet{switch}/0/{portNum}")
        print(f"  switchport mode access")

        # If the port is empty
        if (alias := aliases.get(port)) is None:
            print(f"  description EMPTY")
            if studentVlan != "0":
                print(f"  switchport access vlan {studentVlan}")
            if voipVlan != "0":
                print(f"  switchport voice vlan {voipVlan}")
        else:
            print(f"  description {alias}")

            # Untagged VLAN
            if (vlanTag := untagged.get(port)) is not None:
                print(f"  switchport access vlan {vlanTag}")

            # Tagged VLANs
            if (vlanList := portVlans.get(port)) is not None:
                trunkedVlans = ""
                for vlanTag in vlanList:
                    if (untagged.get(port) is None) or (untagged[port] != vlanTag):
                        if vlanTag == voipVlan:
                            print(f"  switchport voice vlan {vlanTag}")
                        else:
                            trunkedVlans += (vlanTag+",")
                if trunkedVlans != "":
                    if trunkedVlans.endswith(","):
                        trunkedVlans = trunkedVlans[0:-1]
                    print(f"  switchport trunk allowed vlan {trunkedVlans}")

print()
