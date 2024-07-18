from client_db import ClientDB
from ui import new_client_guided, make_configs

if __name__ == "__main__":
    fname = "client_db"
    path = "/Users/peter/Junkspace/vpn_manager"
    db = ClientDB(fname=fname, path=path)

    client = new_client_guided(db)
    server_conf, client_conf = make_configs(
        db=db, server_iface=client.server_iface, client_uuid=client.client_uuid
    )

    with open(path + f"{client.server_iface}.conf", "w", encoding="utf-8") as f:
        f.write(server_conf)

    with open(path + f"{client.client_name}.conf", "w", encoding="utf-8") as f:
        f.write(server_conf)
