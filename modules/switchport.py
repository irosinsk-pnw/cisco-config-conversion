class Port:
    """Represents one port's configuration."""
    def __init__(self):
        self.alias = None     # Str: port alias/description
        self.tagged = []      # List of ints: its tagged VLANs
        self.untagged = None  # Int: its untagged VLAN
        self.voip = False     # Bool: whether VoIP is on it
        self.maclock = False  # Bool: whether MAC locking is enabled
        self.fa = 0           # Int: number of allowed first-arrival MACs
        self.macs = []        # List of str: static MAC locks

