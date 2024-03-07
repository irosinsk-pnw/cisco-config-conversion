import re, sys

def _get_vlans_extreme(config: list[str]) -> dict[int, str]:
    """Parses an Extreme config to create a dictionary of VLAN number : VLAN name."""

    vlans = {}
    vlanTagRegex = re.compile(r"configure vlan (?P<name>[\w\-]+) tag (?P<tag>\d{1,4})")

    for line in config:
        if (match := vlanTagRegex.match(line)):
            vlans[int(match["tag"])] = match["name"]

    return vlans

def _get_vlans_enterasys(config: list[str]) -> dict[int, str]:
    """Parses an Enterasys config to create a dictionary of VLAN number : VLAN name."""

    vlans = {}
    vlanTagRegex = re.compile(r'set vlan name (?P<tag>\d{1,4}) "?(?P<name>.+[^"\s])"?')
    vlanCreateRegex = re.compile(r"set vlan create (?P<tag>\d{1,4})")

    for line in config:
        if (match := vlanTagRegex.match(line)):
            vlans[int(match["tag"])] = match["name"]
        elif (match := vlanCreateRegex.match(line)) and int(match["tag"]) not in vlans:
            vlans[int(match["tag"])] = ""

    return vlans


def print_vlans(config: list[str], brand: str):
    """Parses a config to find VLANs, and prints them in Cisco config style.

    `config`: a list of configuration lines, i.e. from readlines().
    `brand`: should be "e" for Enterasys or "x" for Extreme."""
    brand = brand.lower()
    if brand == "e":
        vlans = _get_vlans_enterasys(config)
    elif brand == "x":
        vlans = _get_vlans_extreme(config)
    else:
        raise ValueError("Brand must be 'e' for enterasys or 'x' for extreme")
    
    vlans = dict(sorted(vlans.items()))
    for tag in vlans:
        print(f"vlan {tag}")
        if vlans[tag] != "":
            print(f" name {vlans[tag]}")

    print("\nVLAN tag list:")
    for tag in list(vlans)[:-1]:
        print(tag,end=",")
    print(list(vlans)[-1])


def get_default_vlan(config: list[str], brand: str, voip: bool = False) -> int:
    """Parses a config to find one of the standard default VLANs.

    `config`: a list of configuration lines, i.e. from readlines().
    `brand`: should be "e" for Enterasys or "x" for Extreme.
    `voip`: if True, searches for the VoIP VLAN. Otherwise,
        searches for the student VLAN."""

    brand = brand.lower()
    if brand == "e":
        vlans = _get_vlans_enterasys(config)
    elif brand == "x":
        vlans = _get_vlans_extreme(config)
    else:
        raise ValueError("Brand must be 'e' for enterasys or 'x' for extreme")

    for tag in vlans:
        if ("voip" if voip else "stu") in vlans[tag].lower():
            return tag
    return None
