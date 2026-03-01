import socket
import threading
import json

# Використовуємо 0.0.0.0, щоб сервер слухав усі вхідні запити на цьому ПК
HOST = '0.0.0.0'
PORT = 5555

# Початкові позиції: Гравець 0 зліва, Гравець 1 справа
players = {
    "0": {"x": 150, "y": 300}, 
    "1": {"x": 850, "y": 300}
}
clients = []

def handle_client(conn, player_id):
    print(f"Гравець {player_id} приєднався!")
    conn.send(str(player_id).encode())
    
    while True:
        try:
            data = conn.recv(1024).decode()
            if not data: break
            
            # Отримуємо нові координати від одного гравця
            players[str(player_id)] = json.loads(data)
            
            # Відправляємо оновлені позиції УСІМ гравцям
            game_state = json.dumps(players).encode()
            for client in clients:
                client.sendall(game_state)
        except:
            break
    
    print(f"Гравець {player_id} відключився.")
    if conn in clients: clients.remove(conn)
    conn.close()

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind((HOST, PORT))
server.listen(2)

print(">>> СЕРВЕР ЗАПУЩЕНО")
print(">>> Очікування підключення двох гравців...")

while len(clients) < 2:
    conn, addr = server.accept()
    clients.append(conn)
    p_id = len(clients) - 1
    thread = threading.Thread(target=handle_client, args=(conn, p_id), daemon=True)
    thread.start()

# Тримаємо головний потік сервера живим
import time
while True: time.sleep(1)