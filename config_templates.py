"""
Templates for config files
"""

CLIENT_CONFIG_CLIENT_ENTRY: str = """
[Interface]
Address = {client_ip}/22
PrivateKey = {client_pri}
DNS = {server_vpn_ip}
"""

CLIENT_CONFIG_SERVER_ENTRY: str = """
[Peer]
PublicKey = {server_pub}
Endpoint = {server_wan_ip}:51820
AllowedIPs = 0.0.0.0/0, ::/0
PersistentKeepalive = 21
"""

SERVER_CONFIG_SERVER_ENTRY: str = """
[Interface]
ListenPort = 51820
PrivateKey = {server_pri}
"""

SERVER_CONFIG_CLIENT_ENTRY: str = """
[Peer]
PublicKey = {client_pub}
AllowedIPs = {client_ip}/22
"""
