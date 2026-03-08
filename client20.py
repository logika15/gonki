import customtkinter as ctk
import socket, threading, json, time
from PIL import Image, ImageTk
import pygame

class Game(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Гонки: Start Top-Left -> Finish Bottom-Right")
        self.geometry("1100x850")
        
        pygame.mixer.init()
        
        # 1. МЕРЕЖА
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            self.sock.connect(('127.0.0.1', 5555))
            self.my_id = self.sock.recv(1024).decode().strip()
        except:
            print("Сервер не знайдено!"); self.destroy(); return

        self.players_data = {}
        self.game_started = False
        self.finished = False

        # 2. ТРАСА (Білий фон, Чорна дорога)
        self.cv = ctk.CTkCanvas(self, width=1000, height=750, bg="white", highlightthickness=0)
        self.cv.pack(pady=10)
        
        # Малюємо прямокутну трасу (товщина 160)
        self.road = self.cv.create_rectangle(150, 150, 850, 600, outline="black", width=160, tags="road")
        
        # ЛІНІЯ СТАРТУ (Вгорі зліва)
        self.cv.create_text(230, 120, text="СТАРТ", font=("Arial", 20, "bold"), fill="green")
        self.cv.create_line(150, 200, 310, 200, fill="green", width=5) 

        # ЛІНІЯ ФІНІШУ (Внизу справа)
        self.cv.create_text(770, 630, text="ФІНІШ", font=("Arial", 20, "bold"), fill="red")
        self.cv.create_line(690, 550, 850, 550, fill="red", width=8, dash=(5, 5))

        # 3. МАШИНКИ (Старт вгорі зліва на білій лінії)
        self.start_pos = {
            "0": {"x": 200, "y": 170, "angle": 0},
            "1": {"x": 260, "y": 170, "angle": 0}
        }

        try:
            self.img_g = Image.open("car_green.png").resize((70, 35))
            self.img_y = Image.open("car_yellow.png").resize((70, 35))
            self.tk_g = ImageTk.PhotoImage(self.img_g)
            self.tk_y = ImageTk.PhotoImage(self.img_y)
            self.p0 = self.cv.create_image(200, 170, image=self.tk_g)
            self.p1 = self.cv.create_image(260, 170, image=self.tk_y)
        except:
            self.p0 = self.cv.create_rectangle(190, 160, 210, 180, fill="green")
            self.p1 = self.cv.create_rectangle(250, 160, 270, 180, fill="yellow")

        # Текст повідомлень
        self.msg_label = self.cv.create_text(500, 375, text="Чекаємо гравців...", font=("Arial", 50, "bold"), fill="blue")

        self.bind("<KeyPress>", self.move)
        threading.Thread(target=self.listen, daemon=True).start()

    def start_countdown(self):
        for i in range(3, 0, -1):
            self.cv.itemconfig(self.msg_label, text=str(i))
            time.sleep(1)
        self.cv.itemconfig(self.msg_label, text="РУШ!", fill="green")
        self.game_started = True
        try:
            pygame.mixer.music.load("race_music.mp3")
            pygame.mixer.music.play(-1)
        except: pass
        time.sleep(1)
        self.cv.itemconfig(self.msg_label, text="")

    def is_on_road(self, x, y):
        # Перевірка колізії з чорною дорогою
        items = self.cv.find_overlapping(x, y, x, y)
        return self.road in items

    def rotate_car(self, pid, angle):
        try:
            orig = self.img_g if pid == "0" else self.img_y
            rotated = orig.rotate(angle, expand=True)
            new_tk = ImageTk.PhotoImage(rotated)
            if pid == "0": self.tk_g = new_tk; self.cv.itemconfig(self.p0, image=self.tk_g)
            else: self.tk_y = new_tk; self.cv.itemconfig(self.p1, image=self.tk_y)
        except: pass

    def move(self, e):
        if not self.game_started or self.finished: return
        
        me = self.players_data.get(self.my_id, self.start_pos[self.my_id])
        nx, ny = me['x'], me['y']
        k, step, angle = e.keysym.lower(), 15, me.get('angle', 0)

        # WASD (0) / Arrows (1)
        if self.my_id == "0":
            if k == 'w': ny -= step; angle = 90
            elif k == 's': ny += step; angle = 270
            elif k == 'a': nx -= step; angle = 180
            elif k == 'd': nx += step; angle = 0
        else:
            if k in ['up', 'kp_up']: ny -= step; angle = 90
            elif k in ['down', 'kp_down']: ny += step; angle = 270
            elif k in ['left', 'kp_left']: nx -= step; angle = 180
            elif k in ['right', 'kp_right']: nx += step; angle = 0

        # Перевірка: чи на дорозі?
        if self.is_on_road(nx, ny):
            # Перевірка ФІНІШУ (Внизу справа)
            # Якщо гравець перетинає лінію y=550 в межах x 690-850
            if ny > 550 and me['y'] <= 550 and 690 < nx < 850:
                self.finished = True
                me['finished'] = True

            me.update({'x': nx, 'y': ny, 'angle': angle})
            self.sock.send(json.dumps(me).encode())

    def listen(self):
        while True:
            try:
                data = self.sock.recv(2048).decode()
                if not data: break
                
                if "START_GAME" in data:
                    threading.Thread(target=self.start_countdown, daemon=True).start()
                    continue

                self.players_data.update(json.loads(data))
                for pid, p in self.players_data.items():
                    target = self.p0 if pid == "0" else self.p1
                    self.cv.coords(target, p['x'], p['y'])
                    self.rotate_car(pid, p.get('angle', 0))
                    
                    if p.get('finished'):
                        self.cv.itemconfig(self.msg_label, text=f"ГРАВЕЦЬ {int(pid)+1} ПЕРЕМІГ!", fill="gold")
                        self.finished = True
            except: break

if __name__ == "__main__":
    Game().mainloop()