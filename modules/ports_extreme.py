import re
from modules.switchport import Port
from modules.vlans import _get_vlans_extreme

PortNum = tuple[int, int]  # (switch, port)


def _string_to_tuple(portString: str) -> PortNum:
    """Converts a port string like "3:19" or "12" into a tuple like (3,19) or (1,12)."""
    if ":" in portString:
        return (int(portString[0]), int(portString[2:]))
    else:
        return (1, int(portString))


def _port_range_to_list(portString: str) -> list[PortNum]:
    """Converts a port range into a list of individual port tuples."""

    output = []
    ranges = portString.split(",")
    for string in ranges:
        if "-" in string:
            if ":" in string:
                rangeStart = int(string[string.find(":")+1 : string.find("-")])
                rangeEnd = int(string[string.find("-")+1 : len(string)])
                for i in range(rangeStart, rangeEnd+1):
                    output.append( (int(string[0]), i) )
            else:
                rangeStart = int(string[0 : string.find("-")])
                rangeEnd = int(string[string.find("-")+1 : len(string)])
                for i in range(rangeStart, rangeEnd+1):
                    output.append( (1, i) )

        else:
            output.append(_string_to_tuple(string))

    return output


def parse_config(config: list[str], voipVlan: int = 0) -> dict[PortNum, Port]:
    """Creates port configurations from an Extreme config.

    `config`: a list of configuration lines, i.e. from readlines().
    `voipVlan`: Optionally, the tag number of the VoIP VLAN.
    Returns a dictionary of port number tuples to Port objects.
    This dictionary is sorted by port number.

    Does not include a default config for blank ports."""

    ports: dict[PortNum, Port] = {}
    vlanTags: dict[str, int] = {n: t for t, n in _get_vlans_extreme(config).items()}
    # Extreme references VLANs by name instead of number

    # Matches lines adding a description string for ports up to port 48 (excludes fiber ports)
    descriptionStringRegex = re.compile(
        r'configure ports (?P<port>(\d:)?((\d\b)|([1-3]\d\b)|(4[0-8]\b))) description-string "(?P<alias>.+)"')

    displayStringRegex = re.compile(
        r'configure ports (?P<port>(\d:)?((\d\b)|([1-3]\d\b)|(4[0-8]\b))) display-string (?P<alias>.+)')

    # Matches lines adding a port or range of ports to a VLAN
    vlanPortRegex = re.compile(
        r"configure vlan (?P<name>.+\b) add ports (?P<ports>((\d:)?(\d\d?)(-\d\d?)?,)*(\d:)?(\d\d?)(-\d\d?)?\b) (?P<tagged>(untagged)|(tagged)\b)")

    # Matches lines enabling MAC locking on a port.
    maclockEnableRegex = re.compile(
        r"enable mac-locking ports (?P<port>(\d:)?((\d\b)|([1-3]\d\b)|(4[0-8]\b)))")

    # Matches lines setting a maximum first-arrival for a port.
    maclockFARegex = re.compile(
        r"configure mac-locking ports (?P<port>(\d:)?((\d\b)|([1-3]\d\b)|(4[0-8]\b))) first-arrival limit-learning (?P<num>\d+)")

    # TODO: Figure out how Extreme does static-assigned MAC locks.


    for line in config:

        # Get port aliases
        if match := displayStringRegex.match(line):
            portNum = _string_to_tuple(match["port"])
            if portNum[1] > 48:  # Skip fiber ports
                continue

            port = ports.get(portNum)
            if not port:
                # Add port to dict if it does not yet exist
                port = ports[portNum] = Port()

            if not port.alias:  # Description string overrides display string
                port.alias = match["alias"]


        elif match := descriptionStringRegex.match(line):
            portNum = _string_to_tuple(match["port"])
            if portNum[1] > 48:  # Skip fiber ports
                continue

            port = ports.get(portNum)
            if not port:
                port = ports[portNum] = Port()
            port.alias = match["alias"]


        # Get which ports have which VLANs
        elif match := vlanPortRegex.match(line):
            if match["name"] not in ["Default", "nt_login"]:
                for portNum in _port_range_to_list(match["ports"]):

                    if portNum[1] > 48:  # Skip fiber ports
                        continue

                    port = ports.get(portNum)
                    if not port:
                        port = ports[portNum] = Port()

                    if match["tagged"] == "untagged":
                        port.untagged = vlanTags[match["name"]]
                    elif vlanTags[match["name"]] == voipVlan:
                        port.voip = True
                    else:
                        port.tagged.append(vlanTags[match["name"]])

        elif match := maclockEnableRegex.match(line):
            portNum = _string_to_tuple(match["port"])
            if portNum[1] > 48:
                continue

            port = ports.get(portNum)
            if not port:
                port = ports[portNum] = Port()
            port.maclock = True

        elif match := maclockFARegex.match(line):
            portNum = _string_to_tuple(match["port"])
            if portNum[1] > 48:
                continue

            port = ports.get(portNum)
            if not port:
                port = ports[portNum] = Port()
            port.fa = int(match["num"])

    return dict(sorted(ports.items()))


if __name__ == "__main__":
    # Run tests
    assert _string_to_tuple("4:6") == (4,6)
    assert _string_to_tuple("3:11") == (3,11)
    assert _string_to_tuple("10") == (1,10)
    assert _port_range_to_list("1:3-7,2:4,2:6-10") == [(1,3),(1,4),(1,5),(1,6),(1,7),(2,4),(2,6),(2,7),(2,8),(2,9),(2,10)]
    assert _port_range_to_list("1:31") == [(1,31)]
    assert _port_range_to_list("8-11") == [(1,8),(1,9),(1,10),(1,11)]
