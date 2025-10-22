import socket, ssl, sys, random, json

if len(sys.argv) != 3:
    print("Usage: python3 client_initiator.py <initiator_node_id> <my_value>")
    sys.exit(1)

NODE_ID = int(sys.argv[1])
MY_VALUE = int(sys.argv[2])

PORTS = {1:8441, 2:8442, 3:8443}
NEXT_NODE = {1:2, 2:3, 3:1}

# --- inicjator maskuje swoją wartość ---
R = random.randint(1,100)
value_to_send = MY_VALUE + R
next_node = NEXT_NODE[NODE_ID]

CA_CERT = "pki/ca/ca.crt"
CLIENT_CERT = f"pki/client/client{NODE_ID}.crt"
CLIENT_KEY  = f"pki/client/client{NODE_ID}.key"

try:
    with socket.create_connection(("127.0.0.1", PORTS[next_node])) as sock:
        context = ssl.create_default_context(ssl.Purpose.SERVER_AUTH, cafile=CA_CERT)
        context.load_cert_chain(certfile=CLIENT_CERT, keyfile=CLIENT_KEY)
        with context.wrap_socket(sock, server_hostname="localhost") as ssock:
            print(f"[Node {NODE_ID}] Initiating sum {value_to_send} to Node {next_node}")
            ssock.sendall(json.dumps({"sum": value_to_send,
                                      "initiator": NODE_ID,
                                      "R": R}).encode())
except Exception as e:
    print(f"[-] Could not initiate sum: {e}")

print(f"[Node {NODE_ID}] Protocol started. Remember to subtract R={R} when sum returns to initiator.")
