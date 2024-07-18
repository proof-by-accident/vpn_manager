"""
Objects representing VPN server and client
"""

# pylint: disable=consider-using-f-string, subprocess-run-check, raise-missing-from, logging-fstring-interpolation

import subprocess

from typing import Dict

from utils import _clean, _parse_conf_line
from config_templates import CLIENT_CONFIG_SERVER_ENTRY, SERVER_CONFIG_SERVER_ENTRY


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

        # get port num and private key from iface conf
        proc = subprocess.run(["sudo", "wg", "showconf", iface], capture_output=True)
        conf = _clean(proc.stdout)

        self.server_port = _parse_conf_line(conf, 1)
        self.server_pri = _parse_conf_line(conf, 2)

        # get public key from wg conf
        proc = subprocess.run(["sudo", "wg", "show"], capture_output=True)
        conf = _clean(proc.stdout)

        self.server_pub = _parse_conf_line(conf, 1, arg_delim=":")

        # get WAN IP addr from shell
        cmd = "ip -f inet addr show eth0 | grep inet | awk '{{$1=$1;print}}' | cut -d ' ' --fields 2"
        proc = subprocess.run(cmd, capture_output=True, shell=True)

        self.server_wan_ip = _clean(proc.stdout).split("/")[0]

        # get VPN IP addr from shell
        cmd = "ip -f inet addr show {iface} | grep inet | awk '{{$1=$1;print}}' | cut -d ' ' --fields 2".format(
            iface=iface
        )

        proc = subprocess.run(cmd, capture_output=True, shell=True)

        self.server_vpn_ip, self.server_vpn_subnet = _clean(proc.stdout).split("/")

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
