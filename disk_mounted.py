import socket

from session.session_messages import StorageMessage

IP_ADDRESS = "127.0.0.1"
PORT = 1337

if __name__ == "__main__":
    msg = StorageMessage(True).to_proto()

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.connect((IP_ADDRESS, PORT))
            s.sendall(msg)
        except socket.error:
            pass



