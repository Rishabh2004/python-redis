import socket
import threading


def parse_resp(data: str) -> list[str]:
    lines = data.split("\r\n")
    if not lines[0].startswith("*"):
        raise ValueError("Expected RESP array")

    count = int(lines[0][1:])
    values = []
    idx = 1
    for _ in range(count):
        length_line = lines[idx]
        if not length_line.startswith("$"):
            raise ValueError("Expected bulk string")
        value = lines[idx + 1]
        values.append(value)
        idx += 2
    return values


db = {}


def handle_connection(client_connection: socket.socket, client_address):
    try:
        print(f"[NEW CONNECTION] {client_address} connected.")

        while True:
            request = client_connection.recv(1024)
            if not request:
                break

            data = request.decode()
            print("[DATA] ", data)
            try:
                parts = parse_resp(data)
            except (ValueError, IndexError):
                continue  # malformed input, ignore for now

            if not parts:
                continue

            command = parts[0].lower()
            if command == "echo":
                args = parts[1:]
                response = f"*{len(args)}\r\n"
                for word in args:
                    response += f"${len(word)}\r\n{word}\r\n"
                client_connection.sendall(response.encode())
            elif command == "set":
                key = parts[1]
                val = parts[2]

                db[key] = val
                response = b"+OK\r\n"
                client_connection.sendall(response)
            elif command == "get":
                key = parts[1]
                data = db.get(key)
                print(data)
                if data is None:
                    client_connection.sendall(b"-1\r\n")
                else:
                    rd = f"${len(data)}\r\n{data}\r\n".encode()
                    client_connection.sendall(rd)
            else:
                response = b"+OK\r\n"
                client_connection.sendall(response)
    except ConnectionResetError:
        print(f"[WARNING] Connection abruptly lost with {client_address}.")
    finally:
        client_connection.close()
        print(f"[DISCONNECTED] {client_address} disconnected.")


def main():
    server = socket.create_server(("localhost", 6379), reuse_port=True)
    try:
        while True:
            client_connection, client_addr = server.accept()

            threading.Thread(
                target=handle_connection, args=(client_connection, client_addr)
            ).start()
    except KeyboardInterrupt:
        print("\n[SHUTTING DOWN] Server is stopping.")
    finally:
        server.close()


if __name__ == "__main__":
    main()
