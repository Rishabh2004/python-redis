import socket


def send_command(*args, host="localhost", port=6379):
    # Encode as RESP array of bulk strings
    cmd = f"*{len(args)}\r\n"
    for arg in args:
        arg = str(arg)
        cmd += f"${len(arg)}\r\n{arg}\r\n"

    with socket.create_connection((host, port)) as sock:
        sock.sendall(cmd.encode())
        response = sock.recv(4096)
        print(response.decode())


if __name__ == "__main__":
    send_command("PING")
    send_command("SET", "foo", "bar")
    send_command("GET", "foo")
