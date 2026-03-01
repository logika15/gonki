import customtkinter as ctk
import socket, threading, json
from PIL import Image, ImageTk

class Game(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.geometry("1000x700")
        
        # 1. ПІДКЛЮЧЕННЯ
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            self.sock.connect(('127.0.0.1', 5555))
            self.my_id = self.sock.recv(1024).decode()
        except:
            print("ПОМИЛКА: Спочатку запусти server.py!"); return

        self.players = {}
        
        # 2. МАЛЮЄМО ТРАСУ
        self.cv = ctk.CTkCanvas(self, width=950, height=650, bg="#222")
        self.cv.pack(pady=20)
        # Біла дорога (прямокутник)
        self.cv.create_rectangle(50, 50, 900, 600, outline="white", width=60)

        # 3. МАШИНКИ
        try:
            img1 = ImageTk.PhotoImage(Image.open("МАШЫНА-removebg-preview.png").resize((40, 25)))
            img2 = ImageTk.PhotoImage(Image.open("depositphotos_83377494-stock-illustration-yellow-car-top-view-removebg-preview.png").resize((40, 25)))
            self.p0 = self.cv.create_image(50, 80, image=img1)
            self.p1 = self.cv.create_image(50, 120, image=img2)
            self.img_ref = [img1, img2] # Щоб Python не видалив картинки з пам'яті
        except:
            self.p0 = self.cv.create_rectangle(140, 70, 170, 90, fill="red")
            self.p1 = self.cv.create_rectangle(140, 110, 170, 130, fill="blue")

        self.bind("<KeyPress>", self.move)
        threading.Thread(target=self.listen, daemon=True).start()

    def move(self, e):
        me = self.players.get(self.my_id, {"x": 150, "y": 80 if self.my_id=="0" else 120})
        k = e.keysym.lower()
        step = 15

        if self.my_id == "0": # WASD
            if k == 'w': me['y'] -= step
            if k == 's': me['y'] += step
            if k == 'a': me['x'] -= step
            if k == 'd': me['x'] += step
        else: # Arrows
            if k == 'up': me['y'] -= step
            if k == 'down': me['y'] += step
            if k == 'left': me['x'] -= step
            if k == 'right': me['x'] += step
        
        self.sock.send(json.dumps(me).encode())

    def listen(self):
        while True:
            try:
                data = self.sock.recv(1024).decode()
                if not data: break
                self.players = json.loads(data)
                # Оновлюємо позиції
                d0, d1 = self.players.get("0"), self.players.get("1")
                if d0: self.cv.coords(self.p0, d0['x'], d0['y'])
                if d1: self.cv.coords(self.p1, d1['x'], d1['y'])
            except: break

if __name__ == "__main__":
    Game().mainloop()






























































import customtkinter as ctk
import socket
import threading
import json
from PIL import Image, ImageTk

# Однакові IP для сервера та гравця на одному ПК
SERVER_IP = '127.0.0.1' 
PORT = 5555

class FastRace(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Гонки: WASD vs Arrows")
        self.geometry("1100x750")
        
        # 1. Підключення до сервера
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.connect((SERVER_IP, PORT))
            self.my_id = self.sock.recv(1024).decode()
            print(f"Ви підключилися як Гравець {int(self.my_id)+1}")
        except:
            print("ПОМИЛКА: Спочатку запустіть server.py!"); self.destroy(); return

        self.players_data = {}
        
        # 2. Інтерфейс (Траса)
        self.canvas = ctk.CTkCanvas(self, width=1050, height=700, bg="#222")
        self.canvas.pack(pady=20)
        
        # Малюємо білу дорогу (рамку)
        self.canvas.create_rectangle(50, 50, 1000, 650, outline="white", width=60)

        # 3. Машинки
        try:
            # Спробуємо завантажити твої картинки
            img1 = Image.open("МАШЫНА-removebg-preview.png").resize((50, 30))
            self.photo1 = ImageTk.PhotoImage(img1)
            img2 = Image.open("depositphotos_83377494-stock-illustration-yellow-car-top-view-removebg-preview.png").resize((50, 30))
            self.photo2 = ImageTk.PhotoImage(img2)
            
            self.p0_sprite = self.canvas.create_image(150, 300, image=self.photo1)
            self.p1_sprite = self.canvas.create_image(850, 300, image=self.photo2)
        except:
            # Якщо картинок немає, малюємо кольорові бокси
            print("Картинки не знайдено, малюю замінники.")
            self.p0_sprite = self.canvas.create_rectangle(130, 285, 170, 315, fill="green")
            self.p1_sprite = self.canvas.create_rectangle(830, 285, 870, 315, fill="orange")

        # 4. Події та мережа
        self.bind("<KeyPress>", self.send_move)
        threading.Thread(target=self.receive_loop, daemon=True).start()

    def send_move(self, event):
        # Отримуємо поточні координати (або ставимо дефолтні при старті)
        me = self.players_data.get(self.my_id, {"x": 150 if self.my_id=="0" else 850, "y": 300})
        
        key = event.keysym.lower()
        step = 18 # Швидкість руху

        # Логіка для Гравця 1 (WASD)
        if self.my_id == "0":
            if key == 'w': me['y'] -= step
            elif key == 's': me['y'] += step
            elif key == 'a': me['x'] -= step
            elif key == 'd': me['x'] += step
        
        # Логіка для Гравця 2 (Стрілочки)
        elif self.my_id == "1":
            if key == 'up': me['y'] -= step
            elif key == 'down': me['y'] += step
            elif key == 'left': me['x'] -= step
            elif key == 'right': me['x'] += step
        
        # Відправляємо нові координати на сервер
        try:
            self.sock.send(json.dumps(me).encode())
        except:
            pass

    def receive_loop(self):
        while True:
            try:
                data = self.sock.recv(1024).decode()
                if not data: break
                self.players_data = json.loads(data)
                
                # Оновлюємо позиції обох машин на екрані
                p0 = self.players_data.get("0")
                p1 = self.players_data.get("1")
                
                if p0: self.canvas.coords(self.p0_sprite, p0['x'], p0['y'])
                if p1: self.canvas.coords(self.p1_sprite, p1['x'], p1['y'])
            except:
                break

if __name__ == "__main__":
    app = FastRace()
    app.mainloop()