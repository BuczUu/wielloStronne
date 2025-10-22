import socket, ssl

HOST = "127.0.0.1"
PORT = 8448

context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
context.verify_mode = ssl.CERT_REQUIRED
context.load_cert_chain(certfile="pki/server/server1.crt", keyfile="pki/server/server1.key")
context.load_verify_locations(cafile="pki/ca/ca.crt")

bindsock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
bindsock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
bindsock.bind((HOST, PORT))
bindsock.listen(5)
print(f"[*] mTLS server listening on {HOST}:{PORT}")

while True:
    newsock, addr = bindsock.accept()
    try:
        tls_conn = context.wrap_socket(newsock, server_side=True)
        cert = tls_conn.getpeercert()
        cn = cert['subject'][0][0][1] if cert else "Unknown"
        print(f"[+] Client connected: {addr}, CN = {cn}")

        # Pętla odbioru wielu wiadomości
        while True:
            data = tls_conn.recv(1024)
            if not data:  # klient zakończył połączenie
                print(f"[*] Client {addr} disconnected")
                break
            print("Received:", data.decode().strip())
            tls_conn.sendall(b"Hello from secure mTLS server!\n")

        tls_conn.close()
    except ssl.SSLError as e:
        print(f"[-] Rejected connection from {addr}: {e}")
        newsock.close()
