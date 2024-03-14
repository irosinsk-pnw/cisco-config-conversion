import argparse, sys
from modules import ports_extreme, ports_enterasys, vlans

parser = argparse.ArgumentParser()

brand = parser.add_mutually_exclusive_group(required=True)
brand.add_argument("-E", "--enterasys", action="store_true", help="Use an Enterasys config")
brand.add_argument("-X", "--extreme", action="store_true", help="Use an Extreme config")

parser.add_argument("--vlans", action="store_true", help="Print VLAN configuration. Omit for port configuration")

model = parser.add_mutually_exclusive_group()
model.add_argument("-w", "--white", action="store_true", help="Destination switch is 'white' (9348uxm)")
model.add_argument("-b", "--blue", action="store_true", help="Destination switch is 'blue' (3850mg)")

parser.add_argument("-d", "--default", type=int, help="Default VLAN for empty ports")
parser.add_argument("-v", "--voip", type=int, help="VoIP VLAN")
parser.add_argument("filename", nargs="?", help="Input config's filename. Reads from stdin if omitted.")

args = parser.parse_args()

config: list[str]

if args.filename:
    try:
        with open(args.filename, "r") as inputFile:
            config = inputFile.readlines()
    except Exception as e:
        print(e)
        sys.exit(1)

else:
    print("Paste the original configuration file below.\nTo end, press Ctrl+Z then Enter on Windows, or Ctrl+D on Unix.", file=sys.stderr)
    config = sys.stdin.readlines()
    print(file=sys.stderr)

if args.vlans:
    # Print VLAN config rather than port config
    if args.extreme:
        vlans.print_vlans(config, "x")
    elif args.enterasys:
        vlans.print_vlans(config, "e")

else:
    # Print whole port config

    if args.default:
        defaultVlan = args.default
    elif args.extreme:
        defaultVlan = vlans.get_default_vlan(config, "x")
    else: # if args.enterasys
        defaultVlan = vlans.get_default_vlan(config, "e")

    # defaultVlan will be None if no option is provided
    # and the parser can't find a student VLAN

    if args.voip:
        voipVlan = args.voip
    elif args.extreme:
        voipVlan = vlans.get_default_vlan(config, "x", voip=True)
    else: # if args.enterasys
        voipVlan = vlans.get_default_vlan(config, "e", voip=True)

    # voipVlan will be None if no option is provided
    # and the parser can't find a VoIP VLAN.
    # This is no problem because if it isn't found,
    # ports will not be marked with port.voip


    if args.extreme:
        portsDict = ports_extreme.parse_config(config, voipVlan)
    else: # if args.enterasys
        portsDict = ports_enterasys.parse_config(config, voipVlan)

    numSwitches = list(portsDict)[-1][0]

    for switch in range(1,numSwitches+1):
        for portNum in range(1,49):

            if args.white and portNum <= 36:
                print(f"interface TwoGigabitEthernet{switch}/0/{portNum}")
            elif (args.blue or args.white) and portNum > 36:
                print(f"interface TenGigabitEthernet{switch}/0/{portNum}")
            else:
                print(f"interface GigabitEthernet{switch}/0/{portNum}")

            port = portsDict.get( (switch, portNum) )

            if not port or not port.alias: # Print a default config
                print(" description EMPTY")
                print(" switchport mode access")
                print(" spanning-tree portfast")
                print(" switchport port-security")
                print(" switchport port-security maximum 8")
                print(" switchport port-security violation restrict")
                if defaultVlan and (not port or not port.untagged):
                    print(f" switchport access vlan {defaultVlan}")
                elif port and port.untagged:
                    print(f" switchport access vlan {port.untagged}")
                if voipVlan:
                    print(f" switchport voice vlan {voipVlan}")

            else:
                print(f" description {port.alias}")

                if len(port.tagged):
                    print(" switchport mode trunk")
                    trunkedVlans = ""
                    trunkedVlans += str(port.tagged[0])
                    for i in range(1,len(port.tagged)):
                        trunkedVlans += "," + str(port.tagged[i])
                    print(f" switchport trunk allowed vlan {trunkedVlans}")

                else:
                    print(" switchport mode access")
                    print(" spanning-tree portfast")

                if port.untagged:
                    print(f" switchport access vlan {port.untagged}")

                if port.voip:
                    print(f" switchport voice vlan {voipVlan}")

                if port.maclock:
                    print(" switchport port-security")
                    print(f" switchport port-security maximum {port.fa}")
                    print(" switchport port-security violation restrict")
                    for mac in port.macs:
                        print(f" switchport port-security mac-address {mac}")



