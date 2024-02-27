class Port:
    """Represents one port's configuration."""
    def __init__(self):
        self.alias = None    # Str: port alias/description
        self.tagged = []     # List of ints: its tagged VLANs
        self.untagged = None # Int: its untagged VLAN
        self.voip = False     # Bool: whether VoIP is on it

