"""
Utils to be used elsewhere
"""

# pylint: disable=consider-using-f-string, subprocess-run-check, raise-missing-from, logging-fstring-interpolation

import hashlib
import subprocess

from typing import List


def _cheap_hash(s):
    return hashlib.md5(s).hexdigest()[:6]


def _clean_one(a):
    if isinstance(a, bytes):
        return a.decode("utf-8").strip(" \n")
    if isinstance(a, str):
        return a.strip(" \n")

    raise ValueError(f"arg to clean must be str or bytes, got {type(a)}")


def _clean(a, *args):
    if len(args) == 0:
        return _clean_one(a)

    ret = [_clean_one(a)]

    for a in args:
        ret.append(_clean_one(a))

    return ret


def _parse_conf_line(conf: List[str], i: int, arg_delim: str = "=") -> str:
    """
    Parses the output of various wireguard config CLI commands
    """
    arg_delim += " "
    line = _clean(conf.split("\n")[i]).split(arg_delim)

    return line[-1]


def _get_keypair():
    """
    Generates an RSA keypair for WG clients
    """
    proc = subprocess.run(["wg", "genkey"], capture_output=True)
    private_key = proc.stdout

    proc = subprocess.run(["wg", "pubkey"], input=private_key, capture_output=True)
    public_key = proc.stdout

    return _clean(private_key, public_key)
