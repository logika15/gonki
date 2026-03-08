import customtkinter as ctk
import socket, threading, json, time
from PIL import Image, ImageTk
import pygame

class Game(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Гонки")
        self.geometry("1100x850")

        pygame.mixer.init()

        # сеть
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            self.sock.connect(('127.0.0.1', 5555))
            self.my_id = self.sock.recv(1024).decode().strip()
        except:
            print("Сервер не найден")
            self.destroy()
            return

        self.players_data = {}
        self.game_started = False
        self.finished = False

        # управление
        self.pressed_keys = set()

        # круги
        self.laps = 0
        self.max_laps = 25

        # зоны круга
        self.zone_down = False
        self.zone_right = False
        self.zone_up = False
        self.zone_finish = False
        self.prev_y = 0  # для проверки пересечения сверху вниз

        # физика
        self.vx = 0
        self.vy = 0
        self.friction = 0.92
        self.speed = 2

        # поле
        self.cv = ctk.CTkCanvas(self,width=1000,height=750,bg="white",highlightthickness=0)
        self.cv.pack(pady=10)

        # трасса
        self.road = self.cv.create_rectangle(150,150,850,600,outline="black",width=160)

        # старт
        self.cv.create_text(230,120,text="СТАРТ",font=("Arial",20,"bold"),fill="green")
        self.cv.create_line(150,200,310,200,fill="green",width=5)

        # финиш
        self.finish_y = 550
        self.cv.create_text(770,630,text="ФІНІШ",font=("Arial",20,"bold"),fill="red")
        self.cv.create_line(690,self.finish_y,850,self.finish_y,fill="red",width=8,dash=(5,5))

        # лейбл кругов
        self.lap_label = self.cv.create_text(
            500,50,
            text=f"Круг: {self.laps}/{self.max_laps}",
            font=("Arial",25,"bold")
        )

        # машины
        self.start_pos = {
            "0":{"x":200,"y":170,"angle":0},
            "1":{"x":260,"y":170,"angle":0}
        }

        try:
            self.img_g=Image.open("car_green.png").resize((70,35))
            self.img_y=Image.open("car_yellow.png").resize((70,35))
            self.tk_g=ImageTk.PhotoImage(self.img_g)
            self.tk_y=ImageTk.PhotoImage(self.img_y)
            self.p0=self.cv.create_image(200,170,image=self.tk_g)
            self.p1=self.cv.create_image(260,170,image=self.tk_y)
        except:
            self.p0=self.cv.create_rectangle(190,160,210,180,fill="green")
            self.p1=self.cv.create_rectangle(250,160,270,180,fill="yellow")

        self.msg_label = self.cv.create_text(
            500,375,
            text="Ждем игроков...",
            font=("Arial",50,"bold"),
            fill="blue"
        )

        # управление
        self.bind("<KeyPress>", self.key_down)
        self.bind("<KeyRelease>", self.key_up)

        threading.Thread(target=self.listen,daemon=True).start()
        self.update_loop()

    def key_down(self,e):
        self.pressed_keys.add(e.keysym.lower())

    def key_up(self,e):
        self.pressed_keys.discard(e.keysym.lower())

    def start_countdown(self):
        for i in range(3,0,-1):
            self.cv.itemconfig(self.msg_label,text=str(i))
            time.sleep(1)
        self.cv.itemconfig(self.msg_label,text="GO!",fill="green")
        self.game_started=True
        pygame.mixer.music.load("mrg2.mp3")
        pygame.mixer.music.play(-1)
        time.sleep(1)
        self.cv.itemconfig(self.msg_label,text="")

    def is_on_road(self,x,y):
        items=self.cv.find_overlapping(x,y,x,y)
        return self.road in items

    def rotate_car(self,pid,angle):
        try:
            orig=self.img_g if pid=="0" else self.img_y
            rotated=orig.rotate(angle,expand=True)
            new_tk=ImageTk.PhotoImage(rotated)
            if pid=="0":
                self.tk_g=new_tk
                self.cv.itemconfig(self.p0,image=self.tk_g)
            else:
                self.tk_y=new_tk
                self.cv.itemconfig(self.p1,image=self.tk_y)
        except:
            pass

    def update_loop(self):
        if self.game_started and not self.finished:
            me = self.players_data.get(self.my_id, self.start_pos[self.my_id])
            keys = self.pressed_keys

            # движение
            if self.my_id == "0":
                if "w" in keys: self.vy -= self.speed; me["angle"] = 90
                if "s" in keys: self.vy += self.speed; me["angle"] = 270
                if "a" in keys: self.vx -= self.speed; me["angle"] = 180
                if "d" in keys: self.vx += self.speed; me["angle"] = 0
            else:
                if "up" in keys: self.vy -= self.speed; me["angle"] = 90
                if "down" in keys: self.vy += self.speed; me["angle"] = 270
                if "left" in keys: self.vx -= self.speed; me["angle"] = 180
                if "right" in keys: self.vx += self.speed; me["angle"] = 0

            nx = me["x"] + self.vx
            ny = me["y"] + self.vy

            if self.is_on_road(nx, ny):
                # зоны круга по порядку
                if not self.zone_down and ny > 500:
                    self.zone_down = True
                if self.zone_down and not self.zone_right and nx > 750:
                    self.zone_right = True
                if self.zone_down and self.zone_right and not self.zone_up and ny < 300:
                    self.zone_up = True

                # финальная зона — только если пройдены все предыдущие
                if self.zone_down and self.zone_right and self.zone_up:
                    if 600 < nx < 900 and 450 < ny < 600:
                        # проверка пересечения сверху вниз
                        if self.prev_y < self.finish_y and ny >= self.finish_y:
                            # круг засчитан
                            self.laps += 1
                            self.cv.itemconfig(self.lap_label,text=f"Круг: {self.laps}/{self.max_laps}")
                            # сброс зон для следующего круга
                            self.zone_down = False
                            self.zone_right = False
                            self.zone_up = False
                            self.prev_y = ny
                            if self.laps >= self.max_laps:
                                self.finished = True
                                me["finished"] = True
                                pygame.mixer.music.stop()
                                self.cv.itemconfig(self.msg_label,text="ФИНИШ!",fill="red")

                me["x"] = nx
                me["y"] = ny
                self.prev_y = ny

                try:
                    self.sock.send(json.dumps(me).encode())
                except:
                    pass

            # скольжение
            self.vx *= self.friction
            self.vy *= self.friction

        self.after(30,self.update_loop)

    def listen(self):
        while True:
            try:
                data = self.sock.recv(2048).decode()
                if not data: break
                if "START_GAME" in data:
                    threading.Thread(target=self.start_countdown,daemon=True).start()
                    continue
                self.players_data.update(json.loads(data))
                for pid,p in self.players_data.items():
                    target = self.p0 if pid=="0" else self.p1
                    self.cv.coords(target,p["x"],p["y"])
                    self.rotate_car(pid,p.get("angle",0))
                    if p.get("finished"):
                        self.cv.itemconfig(self.msg_label,text=f"Игрок {int(pid)+1} победил!",fill="gold")
                        self.finished = True
                        pygame.mixer.music.stop()
            except:
                break

if __name__=="__main__":
    Game().mainloop()