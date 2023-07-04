# Takes an Enterasys EOS configuration file and creates a Cisco configuration for each VLAN.
# Input the EOS config by pasting it on the CLI and pressing Ctrl+D at the end,
# or redirect it like `python vlans-en-to-cisco.py < config.txt`
import re, sys

oldVlanConfig = sys.stdin.readlines()
print()

vlanTagRegex = re.compile(
    r'set vlan name (?P<tag>\d{1,4}\b) "(?P<name>[\w\-]+\b)"')
vlanCreateRegex = re.compile(
    r"set vlan create (?P<tag>\d{1,4}\b)")
vlanList = []
vlanDict = {}

for line in oldVlanConfig:
    if (match := vlanCreateRegex.match(line)) is not None:
        vlanList.append(match.group("tag"))

    elif (match := vlanTagRegex.match(line)) is not None:
        vlanDict[match.group("tag")] = match.group("name")

for i in vlanList:
    print("vlan", i)
    if (name := vlanDict.get(i)) is not None:
        print(" name", name)

print()
print("VLAN tag list:")
for i in range(len(vlanList)-1):
    print(vlanList[i],end=",")
print(vlanList[len(vlanList)-1])