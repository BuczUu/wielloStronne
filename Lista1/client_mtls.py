import socket, ssl

HOST = "127.0.0.1"
PORT = 8448

context = ssl.create_default_context(ssl.Purpose.SERVER_AUTH, cafile="pki/ca/ca.crt")
context.load_cert_chain(certfile="pki/client/client3.crt", keyfile="pki/client/client3.key")

#context.load_cert_chain(certfile="pki/fake/fake.crt", keyfile="pki/fake/fake.key")

with socket.create_connection((HOST, PORT)) as sock:
    with context.wrap_socket(sock, server_hostname="localhost") as ssock:
        print("[*] Connected with mTLS. Cipher:", ssock.cipher())

        # Pętla wysyłania wiadomości
        while True:
            msg = input("Enter message to send (or 'exit' to quit): ")
            if msg.lower() == "exit":
                print("[*] Closing connection.")
                break

            ssock.sendall(msg.encode() + b"\n")
            data = ssock.recv(1024)
            print("Received:", data.decode().strip())
