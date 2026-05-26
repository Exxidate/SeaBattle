import tkinter as tk
from tkinter import messagebox
import random
import os

# Нові імпорти для медіа сплешу
import cv2
import pygame
from PIL import Image, ImageTk


class SeaBattleGame:
    def __init__(self, root):
        self.root = root
        self.root.title("Sea Battle")
        self.root.resizable(False, False)

        # Конфіг
        self.grid_size = 8
        self.cell_size = 40
        self.ship_sizes = [4, 3, 2, 2]
        self.total_ship_cells = sum(self.ship_sizes)

        # МЕДІА КОНФІГ (Змінюй назви файлів тут!)
        self.video_path = "video.mp4"
        self.music_path = "audio.mp3"

        # Ініціалізація музичного плеєра
        pygame.mixer.init()

        # Ігрові пріколи
        self.reset_game_state()

        # Штукі на акошкє
        self.create_widgets()
        self.start_new_game()

        # Запуск медіа фону
        self.start_background_music()
        self.setup_and_start_video()

    def reset_game_state(self):
        self.player_board = [[0] * self.grid_size for _ in range(self.grid_size)]
        self.enemy_board = [[0] * self.grid_size for _ in range(self.grid_size)]

        self.player_ships = {}
        self.enemy_ships = {}

        self.player_shots = set()
        self.ai_shots = set()

        # ШІ
        self.ai_target_queue = []

        self.player_hits = 0
        self.enemy_hits = 0
        self.game_over = False

        # Фаза ставлення кораблів
        self.placement_phase = True
        self.current_ship_index = 0
        self.current_orientation = "H"

    def create_widgets(self):
        self.status_label = tk.Label(
            self.root,
            text="Setup Phase: Place your ships!",
            font=("Arial", 13, "bold"),
            pady=10
        )
        self.status_label.pack()

        # Управління ставленням
        self.controls_frame = tk.Frame(self.root)
        self.controls_frame.pack(pady=5)

        self.orient_btn = tk.Button(
            self.controls_frame,
            text="Orientation: Horizontal",
            font=("Arial", 10, "bold"),
            bg="#BBDEFB",
            command=self.toggle_orientation
        )
        self.orient_btn.pack(side=tk.LEFT, padx=10)

        # Кадр для гра (Тепер розширюємо по горизонталі для відео)
        self.main_frame = tk.Frame(self.root, padx=10, pady=10)
        self.main_frame.pack()

        # Частина гравця
        self.player_frame = tk.Frame(self.main_frame)
        self.player_frame.pack(side=tk.LEFT, padx=15)
        tk.Label(self.player_frame, text="YOUR FLEET", font=("Arial", 12, "bold")).pack()

        self.player_canvas = tk.Canvas(
            self.player_frame,
            width=self.grid_size * self.cell_size,
            height=self.grid_size * self.cell_size,
            bg="#E1F5FE"
        )
        self.player_canvas.pack()
        self.player_canvas.bind("<Button-1>", self.player_placement_click)

        # Частина ШІ
        self.enemy_frame = tk.Frame(self.main_frame)
        self.enemy_frame.pack(side=tk.LEFT, padx=15)
        tk.Label(self.enemy_frame, text="ENEMY FLEET", font=("Arial", 12, "bold")).pack()

        self.enemy_canvas = tk.Canvas(
            self.enemy_frame,
            width=self.grid_size * self.cell_size,
            height=self.grid_size * self.cell_size,
            bg="#E1F5FE"
        )
        self.enemy_canvas.pack()
        self.enemy_canvas.bind("<Button-1>", self.player_shoot_click)

        # Фрейм для Сабвей Сьорфєрс
        self.media_frame = tk.Frame(self.main_frame, relief=tk.SOLID)
        self.media_frame.pack(side=tk.LEFT, padx=15)

        # Лейбл куди будемо стрімити кадри відео
        self.video_label = tk.Label(self.media_frame, width=200, height=320, bg="black", text="No Video Found",
                                    fg="white")
        self.video_label.pack()

        # Рестарт
        self.restart_btn = tk.Button(
            self.root,
            text="Restart Game",
            font=("Arial", 11),
            command=self.start_new_game,
            bg="#ECEFF1",
            pady=5
        )
        self.restart_btn.pack(pady=15)

    # Медіа
    def start_background_music(self):
        if os.path.exists(self.music_path):
            try:
                pygame.mixer.music.load(self.music_path)
                pygame.mixer.music.play(-1)  # -1 означає зациклення
            except Exception as e:
                print(f"Помилка відтворення аудіо: {e}")
        else:
            print(f"Файл музики '{self.music_path}' не знайдено. Граємо в тиші.")

    def setup_and_start_video(self):
        if os.path.exists(self.video_path):
            self.cap = cv2.VideoCapture(self.video_path)
            self.play_video_frame()
        else:
            self.video_label.config(text="Put 'subway_surfers.mp4'\nhere for full immersion!")

    def play_video_frame(self):
        if not hasattr(self, 'cap') or not self.cap.isOpened():
            return

        ret, frame = self.cap.read()

        # Якщо відео закінчилось
        if not ret:
            self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
            ret, frame = self.cap.read()

        if ret:
            # Конвертація кольорів
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            # Підганяємо розмір під наш фрейм (Ширина: 200, Висота: 320)
            frame = cv2.resize(frame, (200, 320))

            # Картинка для Tk
            img = Image.fromarray(frame)
            img_tk = ImageTk.PhotoImage(image=img)

            self.video_label.img_tk = img_tk  # Тримаємо лінк у пам'яті, щоб сміттєзбірник не видалив
            self.video_label.config(image=img_tk)

        # Оновлюємо кадр
        self.root.after(33, self.play_video_frame)

    def toggle_orientation(self):
        if self.current_orientation == "H":
            self.current_orientation = "V"
            self.orient_btn.config(text="Orientation: Vertical", bg="#C8E6C9")
        else:
            self.current_orientation = "H"
            self.orient_btn.config(text="Orientation: Horizontal", bg="#BBDEFB")

    def start_new_game(self):
        self.reset_game_state()
        self.orient_btn.config(state=tk.NORMAL)

        self.enemy_board, self.enemy_ships = self.generate_ai_board()

        self.player_canvas.delete("all")
        self.enemy_canvas.delete("all")

        self.draw_grid(self.player_canvas, self.player_board, show_ships=True)
        self.draw_grid(self.enemy_canvas, self.enemy_board, show_ships=False)

        self.update_placement_status()

    def update_placement_status(self):
        current_size = self.ship_sizes[self.current_ship_index]
        self.status_label.config(text=f"Place your {current_size}-deck ship on YOUR FLEET board.", fg="#1565C0")

    def check_proximity(self, board, row, col):
        for r in range(max(0, row - 1), min(self.grid_size, row + 2)):
            for c in range(max(0, col - 1), min(self.grid_size, col + 2)):
                if board[r][c] > 0:
                    return False
        return True

    def validate_and_get_coords(self, board, start_row, start_col, size, orientation):
        coords = []
        for i in range(size):
            r = start_row + (i if orientation == 'V' else 0)
            c = start_col + (i if orientation == 'H' else 0)
            if not (0 <= r < self.grid_size and 0 <= c < self.grid_size) or not self.check_proximity(board, r, c):
                return False, []
            coords.append((r, c))
        return True, coords

    def generate_ai_board(self):
        board = [[0] * self.grid_size for _ in range(self.grid_size)]
        ships_tracker = {}

        for ship_id, ship_size in enumerate(self.ship_sizes, start=1):
            placed = False
            while not placed:
                orientation = random.choice(['H', 'V'])
                row, col = random.randint(0, self.grid_size - 1), random.randint(0, self.grid_size - 1)
                valid, coords = self.validate_and_get_coords(board, row, col, ship_size, orientation)
                if valid:
                    ships_tracker[ship_id] = coords
                    for r, c in coords:
                        board[r][c] = ship_id
                    placed = True
        return board, ships_tracker

    def player_placement_click(self, event):
        if not self.placement_phase:
            return

        col, row = event.x // self.cell_size, event.y // self.cell_size
        ship_size = self.ship_sizes[self.current_ship_index]
        ship_id = self.current_ship_index + 1

        valid, coords = self.validate_and_get_coords(self.player_board, row, col, ship_size, self.current_orientation)

        if valid:
            self.player_ships[ship_id] = coords
            for r, c in coords:
                self.player_board[r][c] = ship_id

            self.player_canvas.delete("all")
            self.draw_grid(self.player_canvas, self.player_board, show_ships=True)

            self.current_ship_index += 1
            if self.current_ship_index >= len(self.ship_sizes):
                self.placement_phase = False
                self.orient_btn.config(state=tk.DISABLED)
                self.status_label.config(text="All ships deployed! Your turn. Fire at the Enemy Fleet!", fg="#2E7D32")
            else:
                self.update_placement_status()
        else:
            self.status_label.config(text="Invalid position! Ships cannot overlap or touch neighbor blocks.",
                                     fg="#C62828")

    def draw_grid(self, canvas, board, show_ships):
        for r in range(self.grid_size):
            for c in range(self.grid_size):
                x1, y1 = c * self.cell_size, r * self.cell_size
                x2, y2 = x1 + self.cell_size, y1 + self.cell_size
                color = "#78909C" if (show_ships and board[r][c] > 0) else "#E1F5FE"
                canvas.create_rectangle(x1, y1, x2, y2, fill=color, outline="#B0BEC5")

    def mark_ship_as_sunk(self, canvas, ship_coords):
        for r, c in ship_coords:
            x1, y1 = c * self.cell_size, r * self.cell_size
            x2, y2 = x1 + self.cell_size, y1 + self.cell_size
            canvas.create_rectangle(x1, y1, x2, y2, fill="#B71C1C", outline="#B0BEC5")
            canvas.create_line(x1 + 5, y1 + 5, x2 - 5, y2 - 5, fill="white", width=2)
            canvas.create_line(x1 + 5, y2 - 5, x2 - 5, y1 + 5, fill="white", width=2)

    def player_shoot_click(self, event):
        if self.placement_phase or self.game_over:
            return

        col, row = event.x // self.cell_size, event.y // self.cell_size

        if not (0 <= col < self.grid_size and 0 <= row < self.grid_size) or (row, col) in self.player_shots:
            return

        self.player_shots.add((row, col))
        ship_id = self.enemy_board[row][col]
        x1, y1 = col * self.cell_size, row * self.cell_size
        x2, y2 = x1 + self.cell_size, y1 + self.cell_size

        if ship_id > 0:
            self.enemy_hits += 1
            self.enemy_canvas.create_rectangle(x1, y1, x2, y2, fill="#FF5252", outline="#B0BEC5")

            ship_coords = self.enemy_ships[ship_id]
            if all(coord in self.player_shots for coord in ship_coords):
                self.mark_ship_as_sunk(self.enemy_canvas, ship_coords)
                self.status_label.config(text=f"SUNK! You destroyed an enemy {len(ship_coords)}-deck ship!",
                                         fg="#B71C1C")
            else:
                self.status_label.config(text="Hit! You get another shot!", fg="#D32F2F")

            if self.enemy_hits == self.total_ship_cells:
                self.game_over = True
                self.status_label.config(text="Victory! You destroyed the entire enemy fleet!", fg="#388E3C")
                messagebox.showinfo("Game Over", "Congratulations! You won!")
        else:
            self.enemy_canvas.create_rectangle(x1, y1, x2, y2, fill="#263238", outline="#B0BEC5")
            self.status_label.config(text="Miss! AI is thinking...", fg="#455A64")
            self.root.after(600, self.ai_turn)

    def ai_turn(self):
        if self.game_over:
            return

        row, col = -1, -1

        # 1. Якщо є відмічений, проте непотоплений корабель
        while self.ai_target_queue:
            r, c = self.ai_target_queue.pop(0)
            if (r, c) not in self.ai_shots:
                row, col = r, c
                break

        # 2. Рандом
        if row == -1:
            while True:
                r, c = random.randint(0, self.grid_size - 1), random.randint(0, self.grid_size - 1)
                if (r, c) not in self.ai_shots:
                    row, col = r, c
                    break

        self.ai_shots.add((row, col))
        ship_id = self.player_board[row][col]
        x1, y1 = col * self.cell_size, row * self.cell_size
        x2, y2 = x1 + self.cell_size, y1 + self.cell_size

        if ship_id > 0:  # Попав
            self.player_hits += 1
            self.player_canvas.create_rectangle(x1, y1, x2, y2, fill="#FF5252", outline="#B0BEC5")

            # Умнік
            neighbors = [(row - 1, col), (row + 1, col), (row, col - 1), (row, col + 1)]
            for nr, nc in neighbors:
                if 0 <= nr < self.grid_size and 0 <= nc < self.grid_size:
                    if (nr, nc) not in self.ai_shots and (nr, nc) not in self.ai_target_queue:
                        self.ai_target_queue.append((nr, nc))

            # Перевірка чи потонув човен
            ship_coords = self.player_ships[ship_id]
            if all(coord in self.ai_shots for coord in ship_coords):
                self.mark_ship_as_sunk(self.player_canvas, ship_coords)
                self.status_label.config(text=f"OH NO! AI fully sunk your {len(ship_coords)}-deck ship!", fg="#B71C1C")

                # Прибрати з черги
                self.ai_target_queue.clear()

                # Прибрати не потрібні клітинки
                for sr, sc in ship_coords:
                    for br in range(max(0, sr - 1), min(self.grid_size, sr + 2)):
                        for bc in range(max(0, sc - 1), min(self.grid_size, sc + 2)):
                            self.ai_shots.add((br, bc))
            else:
                self.status_label.config(text="AI Hit your ship! AI fires again...", fg="#D32F2F")

            if self.player_hits == self.total_ship_cells:
                self.game_over = True
                self.status_label.config(text="Defeat! Your fleet was completely destroyed.", fg="#D32F2F")
                messagebox.showinfo("Game Over", "Game Over! The AI won.")
            else:
                self.root.after(600, self.ai_turn)
        else:  # Промазав
            self.player_canvas.create_rectangle(x1, y1, x2, y2, fill="#263238", outline="#B0BEC5")
            self.status_label.config(text="AI Missed! Your turn.", fg="#388E3C")


if __name__ == "__main__":
    window = tk.Tk()
    game = SeaBattleGame(window)
    window.mainloop()