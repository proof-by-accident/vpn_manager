"""
Objects representing VPN server and client
"""

# pylint: disable=consider-using-f-string, subprocess-run-check, raise-missing-from, logging-fstring-interpolation


import subprocess

from typing import Dict, List

from config_templates import (
    CLIENT_CONFIG_SERVER_ENTRY,
    SERVER_CONFIG_SERVER_ENTRY,
    CLIENT_CONFIG_CLIENT_ENTRY,
    SERVER_CONFIG_CLIENT_ENTRY,
)
from utils import _get_keypair, _cheap_hash, _clean, _parse_conf_line


class Server:
    """
    Basically a data class, represents the VPN server and holds the relevant data
    """

    def __init__(self) -> None:
        self.server_iface: str = ""
        self.server_pub: str = ""
        self.server_pri: str = ""
        self.server_wan_ip: str = ""
        self.server_vpn_ip: str = ""
        self.server_vpn_subnet: str = ""
        self.server_port: str = ""

    def to_dict(self) -> Dict[str, str]:
        """
        outputs class data as a dict
        """
        return {
            "server_iface": self.server_iface,
            "server_pub": self.server_pub,
            "server_pri": self.server_pri,
            "server_wan_ip": self.server_wan_ip,
            "server_vpn_ip": self.server_vpn_ip,
            "server_vpn_subnet": self.server_vpn_subnet,
            "server_port": self.server_port,
        }

    def populate_from_interface(self, iface: str) -> None:
        """
        Populates the class using WG CLI tools, for the provided interface name
        """
        self.server_iface = iface

        # test if any VPN is defined already
        proc = subprocess.run(["sudo", "wg", "showconf", iface], capture_output=True)
        conf = _clean(proc.stdout)
        if len(proc.stdout) == 0:
            _pri, _pub = _get_keypair()
            self.server_pub = _pub
            self.server_pri = _pri
            self.server_port = "52805"
            self.server_vpn_ip = "10.200.200.1"
            self.server_vpn_subnet = "22"

        else:
            # get port num and private key from iface conf
            proc = subprocess.run(
                ["sudo", "wg", "showconf", iface], capture_output=True
            )
            conf = _clean(proc.stdout)

            self.server_port = _parse_conf_line(conf, 1)
            self.server_pri = _parse_conf_line(conf, 2)

            # get public key from wg conf
            proc = subprocess.run(["sudo", "wg", "show"], capture_output=True)
            conf = _clean(proc.stdout)

            self.server_pub = _parse_conf_line(conf, 1, arg_delim=":")

            # get VPN IP addr from shell
            cmd = "ip -f inet addr show {iface} | grep inet | awk '{{$1=$1;print}}' | cut -d ' ' --fields 2".format(
                iface=iface
            )

            proc = subprocess.run(cmd, capture_output=True, shell=True)

            self.server_vpn_ip, self.server_vpn_subnet = _clean(proc.stdout).split("/")

        # get WAN IP addr from shell
        cmd = "ip -f inet addr show eth0 | grep inet | awk '{{$1=$1;print}}' | cut -d ' ' --fields 2"
        proc = subprocess.run(cmd, capture_output=True, shell=True)

        self.server_wan_ip = _clean(proc.stdout).split("/")[0]

    def gen_client_config_entry(self) -> str:
        """docstring"""
        return CLIENT_CONFIG_SERVER_ENTRY.format(
            server_pub=self.server_pub,
            server_wan_ip=self.server_wan_ip,
        )

    def gen_server_config_entry(self) -> str:
        """docstring"""
        return SERVER_CONFIG_SERVER_ENTRY.format(
            server_pri=self.server_pri,
        )

    def gen_config(self, client_list: List["Client"]) -> str:
        """docstring"""

        _entry_space = "/n/n"
        _entries = [self.gen_server_config_entry()] + [
            client.gen_server_config_entry() for client in client_list
        ]

        return _entry_space.join(_entries)


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

    def gen_config(self) -> str:
        """docstring"""

        _entry_space = "/n/n"
        _entries = [
            self.gen_client_config_entry(),
            self.server.gen_client_config_entry(),
        ]

        return _entry_space.join(_entries)
