import socket, ssl, threading, json, sys, random, time

PORTS = {1: 8441, 2: 8442, 3: 8443}
NEXT_NODE = {1: 2, 2: 3, 3: 1}

class SecureRingNode:
    def __init__(self, node_id, my_value):
        self.node_id = node_id
        self.my_value = my_value
        self.port = PORTS[node_id]
        self.is_initiator = False
        self.R = 0
        self.N = 1500 # takie N, że wiemy że suma na pewno nie przekroczy N
        self.received_final_sum = False
        self.final_sum = None
        self.protocol_active = False
        
        # PKI paths
        self.CA_CERT = "pki/ca/ca.crt"
        self.SERVER_CERT = f"pki/server/server{node_id}.crt"
        self.SERVER_KEY = f"pki/server/server{node_id}.key"
        self.CLIENT_CERT = f"pki/client/client{node_id}.crt"
        self.CLIENT_KEY = f"pki/client/client{node_id}.key"

    def start_server(self):
        """Uruchamia serwer w osobnym wątku"""
        def server_loop():
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            sock.bind(("127.0.0.1", self.port))
            sock.listen(5)
            print(f"[Node {self.node_id}] Server listening on port {self.port}")

            while True:
                conn, addr = sock.accept()
                threading.Thread(target=self.handle_client, args=(conn, addr), daemon=True).start()

        threading.Thread(target=server_loop, daemon=True).start()

    def reset_protocol_state(self):
        self.is_initiator = False
        self.R = 0
        self.received_final_sum = False
        self.final_sum = None
        self.protocol_active = False
        print(f"[Node {self.node_id}] Protocol state reset - ready for next round")

    def handle_client(self, conn, addr):
        try:
            context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
            context.verify_mode = ssl.CERT_REQUIRED
            context.load_cert_chain(certfile=self.SERVER_CERT, keyfile=self.SERVER_KEY)
            context.load_verify_locations(cafile=self.CA_CERT)

            tls_conn = context.wrap_socket(conn, server_side=True)
            data = tls_conn.recv(1024)
            
            if not data:
                tls_conn.close()
                return

            msg = json.loads(data.decode())
            current_sum = msg["sum"]
            initiator = msg["initiator"]

            print(f"\n[Node {self.node_id}] Received sum={current_sum} from previous node. Initiator: Node {initiator}")

            # po powrocie do inicjatora odzyskujemy prawidłową sumę
            if self.node_id == initiator:
                final_sum = (current_sum - self.R) % self.N
                self.final_sum = final_sum
                self.received_final_sum = True

                print(f"\n{'='*50}")
                print(f"[Node {self.node_id}] FINAL SUM after subtracting R={self.R}: {final_sum}")
                print(f"{'='*50}\n")

                time.sleep(2)
                self.reset_protocol_state()
                
            # przekazanie dalej w pierścieniu
            else:
                current_sum = (current_sum + self.my_value) % self.N

                print(f"[Node {self.node_id}] Added my value {self.my_value}, new sum: {current_sum}")

                time.sleep(0.5)
                success = self.forward_to_next(current_sum, initiator)
                
                if success:
                    time.sleep(2)
                    self.reset_protocol_state()

        except Exception as e:
            print(f"[-] Node {self.node_id} error handling connection: {e}")
            self.reset_protocol_state()

        finally:
            tls_conn.close()

    def forward_to_next(self, current_sum, initiator):
        """Przekazuje sumę do następnego węzła"""
        next_node_id = NEXT_NODE[self.node_id]
        try:
            with socket.create_connection(("127.0.0.1", PORTS[next_node_id])) as sock:
                context = ssl.create_default_context(ssl.Purpose.SERVER_AUTH, cafile=self.CA_CERT)
                context.load_cert_chain(certfile=self.CLIENT_CERT, keyfile=self.CLIENT_KEY)
                
                with context.wrap_socket(sock, server_hostname="localhost") as ssock:
                    send_msg = {"sum": current_sum, "initiator": initiator}
                    ssock.sendall(json.dumps(send_msg).encode())
                    
            print(f"[Node {self.node_id}] Forwarded sum={current_sum} to Node {next_node_id}")
            return True
            
        except Exception as e:
            print(f"[-] Node {self.node_id} could not forward to Node {next_node_id}: {e}")
            return False

    def initiate_protocol(self):
        """Rozpoczyna protokół jako inicjator"""
        if self.protocol_active:
            print(f"[Node {self.node_id}] Protocol already active, please wait...")
            return False
            
        self.reset_protocol_state()
        self.is_initiator = True
        self.protocol_active = True
        self.R = random.randint(1, 2000)
        value_to_send = (self.my_value + self.R) % self.N
        next_node_id = NEXT_NODE[self.node_id]

        print(f"\n[Node {self.node_id}] Starting protocol as INITIATOR")
        print(f"[Node {self.node_id}] My value: {self.my_value}, R: {self.R}")
        print(f"[Node {self.node_id}] Sending masked value: {value_to_send}")

        try:
            with socket.create_connection(("127.0.0.1", PORTS[next_node_id])) as sock:
                context = ssl.create_default_context(ssl.Purpose.SERVER_AUTH, cafile=self.CA_CERT)
                context.load_cert_chain(certfile=self.CLIENT_CERT, keyfile=self.CLIENT_KEY)
                
                with context.wrap_socket(sock, server_hostname="localhost") as ssock:
                    ssock.sendall(json.dumps({
                        "sum": value_to_send,
                        "initiator": self.node_id
                    }).encode())
                    
            print(f"[Node {self.node_id}] Initiated protocol to Node {next_node_id}")
            return True
            
        except Exception as e:
            print(f"[-] Node {self.node_id} could not initiate protocol: {e}")
            self.reset_protocol_state()
            return False

    def wait_for_result(self):
        if self.is_initiator:
            print(f"[Node {self.node_id}] Waiting for sum to complete the ring...")
            start_time = time.time()
            while not self.received_final_sum:
                if time.time() - start_time > 30:
                    print(f"[Node {self.node_id}] Timeout waiting for result")
                    self.reset_protocol_state()
                    return None
                time.sleep(0.1)
            return self.final_sum
        return None

    def check_protocol_status(self):
        """Sprawdza czy protokół jest aktywny"""
        return self.protocol_active

def main():
    if len(sys.argv) != 3:
        print("Usage: python3 node.py <node_id> <my_value>")
        print("Example: python3 node.py 1 100")
        sys.exit(1)

    node_id = int(sys.argv[1])
    my_value = int(sys.argv[2])

    node = SecureRingNode(node_id, my_value)
    node.start_server()

    print(f"[Node {node_id}] Started with value: {my_value}")
    print(f"[Node {node_id}] Waiting for other nodes to start...")
    
    time.sleep(2)

    while True:
        try:
            print(f"\n{'='*40}")
            print(f"Node {node_id} - Current value: {my_value}")
            if node.check_protocol_status():
                print("Status: PROTOCOL ACTIVE - please wait...")
                time.sleep(2)
                continue
            else:
                print("Status: READY for protocol")
            
            print("Options:")
            print("  's' - Start protocol as initiator")
            print("  'c' - Change my value")
            print("  'q' - Quit")
            choice = input("Select option: ").strip().lower()
            
            if choice == 's':
                if node.initiate_protocol():
                    final = node.wait_for_result()
                    if final is not None:
                        print(f"\n✓ Protocol completed! Final sum: {final}")
                    else:
                        print(f"\n✗ Protocol failed or timed out")
                        
            elif choice == 'c':
                try:
                    new_value = int(input(f"Enter new value (current: {my_value}): "))
                    my_value = new_value
                    node.my_value = new_value
                    print(f"[Node {node_id}] Value updated to: {my_value}")
                except ValueError:
                    print("Invalid value entered")
                    
            elif choice == 'q':
                print("Exiting...")
                break
            else:
                print("Invalid option")
                
        except KeyboardInterrupt:
            print("\nExiting...")
            break

if __name__ == "__main__":
    main()