"""
Objects representing VPN server and client
"""

# pylint: disable=consider-using-f-string, subprocess-run-check, raise-missing-from, logging-fstring-interpolation


from typing import Dict

from utils import _get_keypair, _cheap_hash
from server import Server

from config_templates import CLIENT_CONFIG_CLIENT_ENTRY, SERVER_CONFIG_CLIENT_ENTRY


class Client:
    """
    Basically a data class except I dont care that much, represents the VPN client and holds the relevant data
    """

    def __init__(self, server_iface: str, name: str, ip: str, **kwargs) -> None:
        self.client_name: str = name
        self.client_ip: str = ip
        self.server_iface: str = server_iface
        self.server: Server = Server().populate_from_interface(server_iface)

        _pri, _pub = _get_keypair()
        self.client_pri: str = kwargs.get("client_pri", _pri)
        self.client_pub: str = kwargs.get("client_pub", _pub)

        self.client_uuid: str = _cheap_hash(name + ip)

    def to_dict(self) -> Dict[str, str]:
        """
        outputs class data as a dict
        """
        return {
            "client_uuid": self.client_uuid,
            "client_name": self.client_name,
            "client_ip": self.client_ip,
            "client_pub": self.client_pub,
            "client_pri": self.client_pri,
            "server_iface": self.server_iface,
        }

    def gen_client_config_entry(self) -> str:
        """docstring"""
        return CLIENT_CONFIG_CLIENT_ENTRY.format(
            client_ip=self.client_ip,
            client_pri=self.client_pri,
            server_vpn_ip=self.server.server_vpn_ip,
        )

    def gen_server_config_entry(self) -> str:
        """docstring"""
        return SERVER_CONFIG_CLIENT_ENTRY.format(
            client_pub=self.client_pub, client_ip=self.client_ip
        )

    def gen_server_config(self, clients: List[Client]) -> str:
        _entry_space = "\n\n"
        entries = [self.gen_s]

