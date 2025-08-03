import zmq

from ipc.session_messages import StorageMessage

IP_ADDRESS = "127.0.0.1"
PORT = 1337

if __name__ == "__main__":
    msg = StorageMessage(False).to_proto()

    ctx = zmq.Context()
    sock = ctx.socket(zmq.PAIR)
    try :
        with sock.connect(f"tcp://{IP_ADDRESS}:{PORT}") as s :
            s.send(msg)
    except Exception as e:
        print(e)
        pass

