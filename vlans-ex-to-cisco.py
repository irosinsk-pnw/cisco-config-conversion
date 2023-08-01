# Takes an Extreme EXOS configuration file and creates a Cisco configuration for each VLAN.
# Input the EXOS config by pasting it on the CLI and pressing Ctrl+D at the end,
# or redirect it like `python vlans-ex-to-cisco.py < config.txt`
import re, sys

print("Paste the Extreme config file below, then press Ctrl+D...", file=sys.stderr)
oldVlanConfig = sys.stdin.readlines()
print()

vlanTagRegex = re.compile(
    r"configure vlan (?P<name>[\w\d\-]+\b) tag (?P<tag>\d{1,4}\b)")
vlanList = []

for line in oldVlanConfig:
    if (match := vlanTagRegex.match(line)) is not None:
        print("vlan", match.group("tag"))
        print(" name", match.group("name"))
        vlanList.append(match.group("tag"))

print()
print("VLAN tag list:")
for i in range(len(vlanList)-1):
    print(vlanList[i],end=",")
print(vlanList[len(vlanList)-1])