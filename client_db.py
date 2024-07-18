"""
Class to handle creating and storing client data in a DB
"""

# pylint: disable=consider-using-f-string, subprocess-run-check, raise-missing-from, logging-fstring-interpolation

import ipaddress as ip
import sqlite3
import subprocess

from logging import getLogger, Logger, basicConfig
from pathlib import Path
from typing import Tuple, Optional, List

from client import Client, Server
from utils import _clean, _parse_conf_line

basicConfig(filename="db.log")
LOG: Logger = getLogger(__name__)


class ClientDBException(BaseException):
    """
    Generic exception for DB operations
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


class ClientDB:
    """
    Class representing the DB of client data
    """

    def __init__(self, fname: str, path: Path) -> None:
        LOG.debug(
            f"Instantiate ClientDB object with params fname: {fname!r} and path: {path!r}..."
        )
        self._fname: str = fname
        self._path: Path = path

        self._schema: Tuple[str, ...] = (
            "client_uuid",
            "client_name",
            "client_ip",
            "client_pub",
            "client_pri",
            "server_iface",
        )

        self._db_path = self._path / (self._fname + ".db")

        self._is_connected = False
        self._con: Optional[sqlite3.Connection] = None

        self._table_name = "clients"

        LOG.debug("...instantiated")

    @property
    def fname(self) -> str:
        """docstring"""
        return self._fname

    @property
    def path(self) -> Path:
        """docstring"""
        return self._path

    @property
    def con(self) -> sqlite3.Connection:
        """docstring"""
        if self._is_connected:
            try:
                assert self._con is not None
            except AssertionError:
                LOG.error("Bad connection state")
                raise ClientDBException("Bad connection state")

        else:
            self._con = sqlite3.connect(str(self._db_path))
            self._is_connected = True

        return self._con

    @property
    def cur(self) -> sqlite3.Cursor:
        """docstring"""
        _con = self.con
        return _con.cursor()

    def _db_create(self) -> None:
        _cur = self.cur
        _cur.execute(f"CREATE TABLE {self._table_name}{self._schema}")

    def _db_exists(self) -> None:
        _cur = self.cur
        _res = _cur.execute(
            f"SELECT name FROM sqlite_master WHERE name={self._table_name!r}"
        )

        tn = _res.fetchone()[0]

        return tn is not None

    def _client_check_already_taken(self, value: str, field: str, iface: str) -> bool:
        _cur = self.cur
        _res = _cur.execute(
            f"""
            SELECT {field}
            FROM {self._table_name}
            WHERE {field}={value!r} AND server_iface={iface!r}
            """
        )

        return _res.fetchone() is not None

    def _client_invalid_input(self, i: str, f: str, iface: str) -> bool:
        if f == "iface":
            return i == ""

        else:
            if i != "":
                return self._client_check_already_taken(i, f, iface)

            else:
                return True

    def _client_propose_ip(self, server):
        _cur = self.cur
        _res = _cur.execute(
            f"SELECT client_ip FROM {self._table_name} WHERE server_iface={server.server_iface!r}"
        )

        ip_l = [ip.ip_address(_[0]) for _ in _res.fetchall()]
        ip_net = ip.IPv4Network(server.server_vpn_ip + server.server_vpn_subnet)

        poss_hosts = ip_net.hosts()
        for host in poss_hosts:
            if host not in ip_l:
                return str(host)

        LOG.error("All IP addresses are taken")
        return ""

    def get_client(self, uuid: str) -> Client:
        """docstring"""
        _cur = self.cur
        _res = _cur.execute(
            f"SELECT client_uuid, client_name, client_ip, client_pub, client_pri, server_iface FROM {self._table_name} WHERE client_uuid = {uuid!r}"
        )
        _row = _res.fetchone()
        _ret = Client(
            server_iface=_row[5],
            name=_row[1],
            ip=_row[2],
            client_pub=_row[3],
            client_pri=_row[4],
        )

        assert uuid == _ret.client_uuid, "Something went wrong :("

    def put_client(self, client: Client) -> None:
        """docstring"""
        _row = client.to_dict()
        _cur = self.cur

        if self._client_check_already_taken(
            client.client_uuid, "client_uuid", client.server_iface
        ):
            raise ValueError("Client already exists!")

        _col_names = "(client_uuid, client_name, client_ip, client_pub, client_pri, server_iface)"
        _col_vals = "({client_uuid}, {client_name!r}, {client_ip!r}, {client_pub!r}, {client_pri!r}, {server_iface!r})".format(
            **_row
        )
        _res = _cur.execute(
            f"INSERT INTO {self._table_name} {_col_names} VALUES {_col_vals}"
        )

        return None

    def get_all_clients_per_server_iface(self: str, iface: str) -> List[Client]:
        """docstring"""
        _cur = self.cur
        _res = _cur.execute(
            f"SELECT client_uuid FROM {self._table_name} WHERE server_iface = {iface!r}"
        )
        _rows = _res.fetchall()
        return [self.get_client(_row[0]) for _row in _rows]

    def new_client_cli(
        self, server_iface: str, client_name: str, client_ip: str
    ) -> None:
        """docstring"""
        server = Server()
        server.populate_from_interface(server_iface)

        new_client = Client(server_iface=server_iface, name=client_name, ip=client_ip)
        self.put_client(new_client)

    def new_client_guided(self) -> None:
        """docstring"""
        proc = subprocess.run(["sudo", "wg", "show"], capture_output=True)
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
        while self._client_invalid_input(client_name, "client_name", server_iface):
            if client_name != "":
                msg = "That client name is already in use! Choose another please:"

            else:
                msg = "Client name is required, please choose one or quit the program:"

            client_name = input(msg)

        default_ip = self._client_propose_ip(server)
        set_ip_q = input(
            f"I propose to use IP addr {default_ip}, do you want to set it to something different? y/[N]"
        )
        if set_ip_q.lower() == "y":
            client_ip = input("Input new client IP:")
            while self._client_invalid_input(client_ip, "client_ip", server_iface):
                if client_ip != "":
                    msg = "That client IP is already in use! Choose another please:"
                    client_ip = input(msg)

                else:
                    print("No IP address entered, using default.")
                    client_ip = default_ip

        else:
            client_ip = default_ip

        new_client = Client(server_iface=server_iface, name=client_name, ip=client_ip)

        self.put_client(new_client)
