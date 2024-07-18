"""
Functions to perform basic tasks
"""

# pylint: disable=consider-using-f-string, subprocess-run-check, raise-missing-from, logging-fstring-interpolation
import subprocess

from typing import Tuple
from logging import getLogger, Logger

from peer_objects import Client, Server
from client_db import ClientDB
from utils import _clean, _parse_conf_line


LOG: Logger = getLogger(__name__)


def new_client(db, server_iface: str, client_name: str, client_ip: str) -> Client:
    """docstring"""

    server = Server()
    server.populate_from_interface(server_iface)

    client = Client(server_iface=server_iface, name=client_name, ip=client_ip)
    db.put_client(client)

    return client


def new_client_guided(db: ClientDB) -> Client:
    """docstring"""
    proc = subprocess.run(["sudo", "wg", "show"], capture_output=True)

    if len(proc.stdout) == 0:
        default_iface = "wg0"

    else:
        conf = _clean(proc.stdout)
        default_iface = _parse_conf_line(conf, 1, arg_delim=":")

    server_iface = input(
        f"Which VPN interface do you want to add the client to? (default={default_iface!r}"
    )
    if server_iface == "":
        server_iface = default_iface

    server = Server()
    server.populate_from_interface(server_iface)

    client_name = input("Input new client name:")
    while db.client_invalid_input(client_name, "client_name", server_iface):
        if client_name != "":
            msg = "That client name is already in use! Choose another please:"

        else:
            msg = "Client name is required, please choose one or quit the program:"

        client_name = input(msg)

    default_ip = db.client_propose_ip(server)
    set_ip_q = input(
        f"I propose to use IP addr {default_ip}, do you want to set it to something different? y/[N]"
    )
    if set_ip_q.lower() == "y":
        client_ip = input("Input new client IP:")
        while db.client_invalid_input(client_ip, "client_ip", server_iface):
            if client_ip != "":
                msg = "That client IP is already in use! Choose another please:"
                client_ip = input(msg)

            else:
                print("No IP address entered, using default.")
                client_ip = default_ip

    else:
        client_ip = default_ip

    client = Client(server_iface=server_iface, name=client_name, ip=client_ip)

    db.put_client(client)

    return client


def make_configs(db: ClientDB, server_iface: str, client_uuid: str) -> Tuple[str, str]:
    client = db.get_client(client_uuid)
    all_clients = db.get_all_clients_per_server_iface(server_iface)

    server = Server()
    server.populate_from_interface(server_iface)

    server.gen_server_config_entry()

    return server.gen_config(all_clients), client.gen_config()
