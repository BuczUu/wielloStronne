import socket, ssl, threading, json, sys

PORTS = {1:8441, 2:8442, 3:8443}
NEXT_NODE = {1:2, 2:3, 3:1}
R = 0

def handle_connection(conn, addr, node_id, my_value):
    try:
        context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
        context.verify_mode = ssl.CERT_REQUIRED
        context.load_cert_chain(certfile=f"pki/server/server{node_id}.crt",
                                keyfile=f"pki/server/server{node_id}.key")
        context.load_verify_locations(cafile="pki/ca/ca.crt")

        tls_conn = context.wrap_socket(conn, server_side=True)
        data = tls_conn.recv(1024)
        if not data:
            tls_conn.close()
            return

        msg = json.loads(data.decode())
        current_sum = msg["sum"]
        initiator = msg["initiator"]
        R = msg["R"]

        print(f"[Node {node_id}] Received sum={current_sum} from {addr}")

        # dodaj własną wartość
        current_sum += my_value

        if node_id == initiator:
            # suma wróciła do inicjatora
            final_sum = current_sum - R
            print(f"[Node {node_id}] Final sum after subtracting R={R}: {final_sum}")

            ##################################################
            # dodanie zeby teraz init nodem byl kolejny node
            # i pamiętać że my już byliśmy inicjatorem 
            # czyli losowanie R powinno byc na serwerze inicjatora a nie kliencie
            # klient tylko do wystartowania - powinien wsm sprawdzac czy wszyskie nody sa uruchomione
            ###################################################
        else:
            # forward do następnego w pierścieniu
            next_node = NEXT_NODE[node_id]
            try:
                with socket.create_connection(("127.0.0.1", PORTS[next_node])) as sock2:
                    ctx2 = ssl.create_default_context(ssl.Purpose.SERVER_AUTH, cafile="pki/ca/ca.crt")
                    ctx2.load_cert_chain(certfile=f"pki/client/client{node_id}.crt",
                                         keyfile=f"pki/client/client{node_id}.key")
                    with ctx2.wrap_socket(sock2, server_hostname="localhost") as ssock:
                        send_msg = {"sum": current_sum, "initiator": initiator, "R": R}
                        ssock.sendall(json.dumps(send_msg).encode())
                print(f"[Node {node_id}] Forwarded sum={current_sum} to Node {next_node}")
            except Exception as e:
                print(f"[-] Node {node_id} could not forward to Node {next_node}: {e}")

        tls_conn.close()
    except ssl.SSLError as e:
        print(f"[-] SSL error from {addr}: {e}")

def run_server(node_id, my_value):
    HOST = "127.0.0.1"
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind((HOST, PORTS[node_id]))
    sock.listen(5)
    print(f"[*] Node {node_id} server listening on {PORTS[node_id]}")

    while True:
        conn, addr = sock.accept()
        threading.Thread(target=handle_connection, args=(conn, addr, node_id, my_value), daemon=True).start()

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python3 server_ring.py <node_id> <my_value>")
        sys.exit(1)
    node_id = int(sys.argv[1])
    my_value = int(sys.argv[2])
    run_server(node_id, my_value)
