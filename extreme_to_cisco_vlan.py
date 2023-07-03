import re, sys

oldVlanConfig = sys.stdin.readlines()
print()

vlanTagRegex = re.compile(
    r"configure vlan (?P<name>[\w\-]+\b) tag (?P<tag>\d{1,4}\b)")
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
print(vlanList[len(vlanList)-1)