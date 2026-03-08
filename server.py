import socket, threading, json, time

HOST = '0.0.0.0'
PORT = 5555

players = {}
clients = []

def handle_client(conn, player_id):
    conn.send(str(player_id).encode())
    while True:
        try:
            data = conn.recv(1024).decode()
            if not data: break
            players[str(player_id)] = json.loads(data)
            state = json.dumps(players).encode()
            for c in clients:
                try: c.sendall(state)
                except: pass
        except: break
    conn.close()

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind((HOST, PORT))
server.listen(2)
print(">>> СЕРВЕР ЗАПУЩЕНО. Очікування 2-х гравців...")

while len(clients) < 2:
    conn, addr = server.accept()
    clients.append(conn)
    threading.Thread(target=handle_client, args=(conn, len(clients)-1), daemon=True).start()

time.sleep(1)
print(">>> Обидва гравці на місці! Даю команду на старт.")
for c in clients:
    c.sendall("START_GAME".encode())

while True: time.sleep(1)