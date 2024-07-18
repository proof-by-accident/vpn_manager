import subprocess

if __name__ == "__main__":
    iface = "wg0"
    proc = subprocess.run(["sudo", "wg", "showconf", iface], capture_output=True)
    print(proc.stdout)
    conf = _clean(proc.stdout)
