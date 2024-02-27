import re
from modules.switchport import Port

PortNum = tuple[int, int]  # (switch, port)


def _string_to_tuple(portString: str) -> PortNum:
    """Converts a port string like "ge.3.19" into a tuple like (3,19)."""

    return (int(portString[3]), int(portString[5:]))


def _port_range_to_list(portString: str) -> list[PortNum]:
    """Converts a port range into a list of individual port tuples."""

    output = []
    for string in portString.split(";"):
        if string.startswith("ge."):
            (ge,switch,ranges) = string.split(".")
            for string in ranges.split(","):
                if "-" in string:
                    (rangeStart, rangeEnd) = string.split("-")
                    for i in range(int(rangeStart),int(rangeEnd)+1):
                        output.append( (int(switch), i) )

                else:
                    output.append( (int(switch), int(string)) )
    return output


def parse_config(config: list[str], voipVlan: int = 0) -> dict[PortNum, Port]:

    ports: dict[PortNum, Port] = {}

    # Matches lines adding an alias for ports up to port 48 (excludes fiber ports)
    displayStringRegex = re.compile(
        r'set port alias (?P<port>ge\.\d\.((\d\b)|([1-3]\d\b)|(4[0-8]\b))) "?(?P<alias>.+[^"\s])"?')

    # Matches lines setting egress on a port
    vlanEgressRegex = re.compile(
        r"set vlan egress (?P<vlan>\d{1,4}) (?P<ports>(((ge|tg|lag|tbp)\.\d\.(\d\d?(-\d\d?)?,)*\d\d?(-\d\d?)?);)*(ge|tg|lag|tbp)\.\d\.(\d\d?(-\d\d?)?,)*\d\d?(-\d\d?)?) (?P<tagged>(untagged)|(tagged))")

    for line in config:

        # Get port aliases
        if match := displayStringRegex.match(line):
            portNum = _string_to_tuple(match["port"])
            port = ports.get(portNum)
            if not port:
                # Add port to dict if it does not yet exist
                port = ports[portNum] = Port()
            port.alias = match["alias"]

        elif match := vlanEgressRegex.match(line):
            for portNum in _port_range_to_list(match["ports"]):
                port = ports.get(portNum)
                if not port:
                    port = ports[portNum] = Port()
                if match["tagged"] == "untagged":
                    port.untagged = int(match["vlan"])
                elif int(match["vlan"]) == voipVlan:
                    port.voip = True
                else:
                    port.tagged.append(int(match["vlan"]))

    return dict(sorted(ports.items()))
