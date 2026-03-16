"""
Современный интерфейс ЭкоНет на CustomTkinter
Полностью переработанный интерфейс с использованием современной библиотеки
"""

import sys
from pathlib import Path

# Добавление корня проекта в путь
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))

try:
    import customtkinter as ctk
    CTK_AVAILABLE = True
except ImportError:
    print("CustomTkinter не установлен. Установите: pip install customtkinter")
    CTK_AVAILABLE = False
    import tkinter as ctk

import cv2
import asyncio
import threading
import logging
import yaml
from datetime import datetime
from typing import Optional, Dict, List
from PIL import Image, ImageTk
import numpy as np

from obelisk.core.engines.unified_engine import UnifiedEngine

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Киберпанк тема для CustomTkinter
CYBERPUNK_THEME = {
    "bg_color": "#000000",
    "fg_color": "#0A0A14",
    "hover_color": "#1E1E2E",
    "text_color": "#E0E0FF",
    "accent_color": "#00FFFF",
    "accent_hover": "#33E6FF",
    "success_color": "#00FF41",
    "warning_color": "#FFAA00",
    "error_color": "#FF0040",
    "neon_cyan": "#00FFFF",
    "neon_pink": "#FF00FF",
    "neon_green": "#00FF00",
    "neon_yellow": "#FFFF00",
}


class ModernEcoNetGUI:
    """Современный интерфейс ЭкоНет на CustomTkinter"""
    
    def __init__(self):
        if not CTK_AVAILABLE:
            raise ImportError("CustomTkinter не установлен. Установите: pip install customtkinter")
        
        # Настройка CustomTkinter
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")
        
        # Создание окна
        self.root = ctk.CTk()
        self.root.title("ЭКОНЕТ [СОВРЕМЕННЫЙ ИНТЕРФЕЙС]")
        self.root.geometry("1920x1080")
        self.root.configure(fg_color=CYBERPUNK_THEME["bg_color"])
        
        # Состояние
        self.config = None
        self.unified_engine = None  # Единый движок
        self.cap = None
        self.is_playing = False
        self.current_detections = []
        self.current_visual_context = None
        self.fps_counter = 0
        self.fps_time = datetime.now()
        self.current_frame = None
        
        # Асинхронный event loop
        self.loop = None
        self.loop_thread = None
        
        # Загрузка конфигурации
        self.load_config()
        
        # Настройка UI
        self.setup_ui()
        
        # Инициализация компонентов
        self.init_async_components()
        
        # Запуск обновления видео
        self.update_video()
    
    def load_config(self):
        """Загрузка конфигурации"""
        try:
            config_path = project_root / "config" / "config.yaml"
            with open(config_path, 'r', encoding='utf-8') as f:
                self.config = yaml.safe_load(f)
        except Exception as e:
            logger.error(f"Ошибка загрузки конфигурации: {e}")
            self.config = {}
    
    def setup_ui(self):
        """Настройка современного интерфейса"""
        # Главный контейнер
        main_frame = ctk.CTkFrame(self.root, fg_color=CYBERPUNK_THEME["bg_color"])
        main_frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Верхняя панель с кнопками
        top_panel = ctk.CTkFrame(main_frame, fg_color=CYBERPUNK_THEME["fg_color"],
                                corner_radius=0)
        top_panel.pack(fill="x", pady=(0, 5))
        
        button_frame = ctk.CTkFrame(top_panel, fg_color="transparent")
        button_frame.pack(side="left", padx=10, pady=10)
        
        # Кнопки управления
        ctk.CTkButton(button_frame, text="ЗАГРУЗИТЬ ВИДЕО",
                     command=self.load_video,
                     fg_color=CYBERPUNK_THEME["neon_cyan"],
                     hover_color=CYBERPUNK_THEME["accent_hover"],
                     text_color="black",
                     font=("Consolas", 12, "bold"),
                     corner_radius=5).pack(side="left", padx=5)
        
        ctk.CTkButton(button_frame, text="КАМЕРА",
                     command=self.connect_camera,
                     fg_color=CYBERPUNK_THEME["neon_pink"],
                     hover_color="#FF33FF",
                     text_color="black",
                     font=("Consolas", 12, "bold"),
                     corner_radius=5).pack(side="left", padx=5)
        
        ctk.CTkButton(button_frame, text="СТАРТ ДЕТЕКЦИИ",
                     command=self.start_detection,
                     fg_color=CYBERPUNK_THEME["neon_green"],
                     hover_color="#33FF33",
                     text_color="black",
                     font=("Consolas", 12, "bold"),
                     corner_radius=5).pack(side="left", padx=5)
        
        ctk.CTkButton(button_frame, text="СТОП",
                     command=self.stop_detection,
                     fg_color=CYBERPUNK_THEME["error_color"],
                     hover_color="#FF3366",
                     text_color="white",
                     font=("Consolas", 12, "bold"),
                     corner_radius=5).pack(side="left", padx=5)
        
        # Основной контент
        content_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        content_frame.pack(fill="both", expand=True)
        
        # Левая панель - видео
        left_panel = ctk.CTkFrame(content_frame, fg_color=CYBERPUNK_THEME["fg_color"],
                                 corner_radius=10)
        left_panel.pack(side="left", fill="both", expand=True, padx=(0, 5))
        
        video_title = ctk.CTkLabel(left_panel, text="[ВИДЕО СТРИМ]",
                                 font=("Consolas", 14, "bold"),
                                 text_color=CYBERPUNK_THEME["neon_cyan"])
        video_title.pack(anchor="w", padx=15, pady=(15, 10))
        
        self.video_label = ctk.CTkLabel(left_panel,
                                        text="[ОЖИДАНИЕ ВИДЕО СТРИМА]\n\nЗагрузите видео или подключите камеру",
                                        font=("Consolas", 12),
                                        text_color=CYBERPUNK_THEME["text_color"],
                                        fg_color=CYBERPUNK_THEME["bg_color"],
                                        corner_radius=10)
        self.video_label.pack(fill="both", expand=True, padx=15, pady=(0, 15))
        self.video_image = None
        
        # Правая панель - статус
        right_panel = ctk.CTkFrame(content_frame, fg_color=CYBERPUNK_THEME["fg_color"],
                                  corner_radius=10, width=300)
        right_panel.pack(side="right", fill="y", padx=(5, 0))
        right_panel.pack_propagate(False)
        
        status_title = ctk.CTkLabel(right_panel, text="[СТАТУС СИСТЕМЫ]",
                                   font=("Consolas", 14, "bold"),
                                   text_color=CYBERPUNK_THEME["neon_cyan"])
        status_title.pack(anchor="w", padx=15, pady=(15, 10))
        
        self.status_labels = {}
        status_items = [
            ("Модель", "Загрузка..."),
            ("Детектор", "Инициализация..."),
            ("Видео", "Не подключено"),
            ("FPS", "0"),
            ("Детекций", "0"),
        ]
        
        for key, value in status_items:
            frame = ctk.CTkFrame(right_panel, fg_color="transparent")
            frame.pack(fill="x", padx=15, pady=5)
            
            key_label = ctk.CTkLabel(frame, text=f"{key}:",
                                    font=("Consolas", 10),
                                    text_color=CYBERPUNK_THEME["text_color"])
            key_label.pack(side="left")
            
            value_label = ctk.CTkLabel(frame, text=value,
                                      font=("Consolas", 10, "bold"),
                                      text_color=CYBERPUNK_THEME["neon_green"])
            value_label.pack(side="left", padx=(10, 0))
            
            self.status_labels[key] = value_label
        
        # Нижняя панель - чат
        chat_panel = ctk.CTkFrame(main_frame, fg_color=CYBERPUNK_THEME["fg_color"],
                                 corner_radius=10, height=300)
        chat_panel.pack(fill="x", pady=(5, 0))
        chat_panel.pack_propagate(False)
        
        chat_title = ctk.CTkLabel(chat_panel, text="[ДИАЛОГ С ЭКОНЕТ]",
                                 font=("Consolas", 14, "bold"),
                                 text_color=CYBERPUNK_THEME["neon_pink"])
        chat_title.pack(anchor="w", padx=15, pady=(15, 10))
        
        # Чат область
        chat_container = ctk.CTkFrame(chat_panel, fg_color=CYBERPUNK_THEME["bg_color"],
                                      corner_radius=5)
        chat_container.pack(fill="both", expand=True, padx=15, pady=(0, 15))
        
        # Scrollable frame для сообщений
        self.chat_scroll = ctk.CTkScrollableFrame(chat_container,
                                                  fg_color=CYBERPUNK_THEME["bg_color"])
        self.chat_scroll.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Поле ввода
        input_frame = ctk.CTkFrame(chat_container, fg_color="transparent")
        input_frame.pack(fill="x", padx=5, pady=(0, 5))
        
        self.chat_input = ctk.CTkEntry(input_frame,
                                        placeholder_text="Введите сообщение...",
                                        font=("Consolas", 11),
                                        fg_color=CYBERPUNK_THEME["fg_color"],
                                        border_color=CYBERPUNK_THEME["neon_cyan"],
                                        text_color=CYBERPUNK_THEME["text_color"])
        self.chat_input.pack(side="left", fill="x", expand=True, padx=(0, 5))
        self.chat_input.bind("<Return>", lambda e: self.send_message())
        
        ctk.CTkButton(input_frame, text="SEND",
                     command=self.send_message,
                     fg_color=CYBERPUNK_THEME["neon_green"],
                     hover_color="#33FF33",
                     text_color="black",
                     font=("Consolas", 11, "bold"),
                     width=80).pack(side="right")
    
    def init_async_components(self):
        """Инициализация асинхронных компонентов"""
        def init_loop():
            self.loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self.loop)
            self.loop.run_until_complete(self._async_init())
        
        self.loop_thread = threading.Thread(target=init_loop, daemon=True)
        self.loop_thread.start()
    
    async def _async_init(self):
        """Асинхронная инициализация через UnifiedEngine"""
        try:
            # Инициализация единого движка (объединяет все компоненты)
            self.unified_engine = UnifiedEngine(self.config, project_root)
            await self.unified_engine.initialize()
            
            self.root.after(0, lambda: self.update_status(
                "Модель", "ГОТОВА", CYBERPUNK_THEME["success_color"]))
            self.root.after(0, lambda: self.update_status(
                "Детектор", "АКТИВЕН", CYBERPUNK_THEME["success_color"]))
            
            # Приветствие через UnifiedEngine
            if self.unified_engine.chat_service:
                greeting = self.unified_engine.chat_service._greet()
                self.root.after(0, lambda: self.add_chat_message("assistant", greeting))
            
            logger.info("✅ UnifiedEngine инициализирован - все компоненты готовы")
            
        except Exception as e:
            logger.error(f"Ошибка инициализации: {e}", exc_info=True)
    
    def update_status(self, key, value, color=None):
        """Обновление статуса с форматированием чисел"""
        if key in self.status_labels:
            # Форматируем числа с разделителями тысяч
            formatted_value = value
            try:
                num_value = int(value)
                formatted_value = f"{num_value:,}".replace(",", " ")
            except (ValueError, TypeError):
                # Если не число, оставляем как есть
                pass
            
            self.status_labels[key].configure(
                text=formatted_value,
                text_color=color if color else CYBERPUNK_THEME["neon_green"]
            )
    
    def load_video(self):
        """Загрузка видео"""
        from tkinter import filedialog
        file_path = filedialog.askopenfilename(
            title="Выберите видео",
            filetypes=[("Video files", "*.mp4 *.avi *.mov *.mkv"), ("All files", "*.*")]
        )
        if file_path:
            self.connect_source(file_path)
    
    def connect_camera(self):
        """Подключение камеры"""
        self.connect_source(0)
    
    def connect_source(self, source):
        """Подключение к источнику"""
        self.stop_detection()
        
        try:
            if isinstance(source, str) and source.isdigit():
                source = int(source)
            
            self.cap = cv2.VideoCapture(source)
            if not self.cap.isOpened():
                raise Exception(f"Не удалось открыть источник: {source}")
            
            # Показываем первый кадр
            ret, frame = self.cap.read()
            if ret and frame is not None:
                self.current_frame = frame
                self.display_frame(frame, [])
                self.is_playing = True
            
            source_name = Path(source).name if isinstance(source, str) else f'Камера {source}'
            self.root.after(0, lambda: self.update_status(
                "Видео", "ПОДКЛЮЧЕНО", CYBERPUNK_THEME["success_color"]))
            self.root.after(0, lambda: self.add_chat_message(
                "system", f"Видео загружено: {source_name}"))
            
        except Exception as e:
            from tkinter import messagebox
            messagebox.showerror("ОШИБКА", f"Не удалось подключиться: {e}")
            logger.error(f"Ошибка подключения: {e}")
    
    def start_detection(self):
        """Запуск детекции"""
        if not self.cap:
            from tkinter import messagebox
            messagebox.showwarning("ВНИМАНИЕ", "Сначала загрузите видео или подключите камеру")
            return
        
        self.is_playing = True
        self.root.after(0, lambda: self.update_status(
            "Видео", "ДЕТЕКЦИЯ АКТИВНА", CYBERPUNK_THEME["neon_yellow"]))
        self.root.after(0, lambda: self.add_chat_message("system", "Детекция запущена"))
    
    def stop_detection(self):
        """Остановка детекции"""
        self.is_playing = False
        if self.cap:
            self.cap.release()
            self.cap = None
        self.current_frame = None
        self.root.after(0, lambda: self.update_status(
            "Видео", "ОСТАНОВЛЕНО", CYBERPUNK_THEME["text_color"]))
        self.root.after(0, lambda: self.add_chat_message("system", "Детекция остановлена"))
    
    def display_frame(self, frame, detections=None):
        """Отображение кадра"""
        try:
            if frame is None:
                return
            
            display_frame = frame.copy()
            
            # Рисуем детекции
            if detections:
                for det in detections:
                    x, y, w, h = det['bbox']
                    conf = det['confidence']
                    
                    # Неоновая рамка
                    cv2.rectangle(display_frame,
                                (int(x), int(y)),
                                (int(x+w), int(y+h)),
                                (0, 255, 255), 3)
                    
                    # Текст
                    label = f"CIGARETTE {conf:.0%}"
                    cv2.putText(display_frame, label,
                              (int(x), int(y)-10),
                              cv2.FONT_HERSHEY_SIMPLEX, 0.7,
                              (0, 255, 255), 2)
            
            # Масштабирование
            height, width = display_frame.shape[:2]
            if height == 0 or width == 0:
                return
            
            max_width = 1200
            max_height = 700
            
            if width > max_width or height > max_height:
                scale = min(max_width / width, max_height / height)
                new_width = int(width * scale)
                new_height = int(height * scale)
                display_frame = cv2.resize(display_frame, (new_width, new_height))
            
            # Конвертация для отображения
            frame_rgb = cv2.cvtColor(display_frame, cv2.COLOR_BGR2RGB)
            img = Image.fromarray(frame_rgb)
            img_tk = ctk.CTkImage(light_image=img, dark_image=img, size=(img.width, img.height))
            
            self.video_label.configure(image=img_tk, text="")
            self.video_image = img_tk
            
        except Exception as e:
            logger.error(f"Ошибка отображения кадра: {e}", exc_info=True)
    
    def update_video(self):
        """Обновление видео"""
        if self.cap and self.is_playing:
            ret, frame = self.cap.read()
            if not ret or frame is None:
                self.is_playing = False
                return
            
            self.current_frame = frame
            
            # Асинхронная обработка через UnifiedEngine
            if self.loop and self.unified_engine:
                asyncio.run_coroutine_threadsafe(
                    self.process_frame_async(frame),
                    self.loop
                )
            else:
                self.display_frame(frame, [])
        
        # Обновление FPS
        self.fps_counter += 1
        now = datetime.now()
        if (now - self.fps_time).total_seconds() >= 1.0:
            fps = self.fps_counter
            self.fps_counter = 0
            self.fps_time = now
            self.root.after(0, lambda: self.update_status(
                "FPS", str(fps), CYBERPUNK_THEME["neon_cyan"]))
        
        # УБРАНО: ограничение 33ms (~30 FPS) - обновление без задержки для максимальной скорости
        self.root.after(0, self.update_video)
    
    async def process_frame_async(self, frame):
        """Асинхронная обработка кадра через UnifiedEngine"""
        try:
            if not self.unified_engine:
                return
            
            # Обработка через единый движок (включает детекцию и визуальный анализ)
            result = await self.unified_engine.process_frame(frame)
            
            detections = result.get("detections", [])
            visual_context = result.get("visual_context")
            
            if detections:
                self.current_detections = detections
                count = len(detections)
                self.root.after(0, lambda: self.update_status(
                    "Детекций", str(count), CYBERPUNK_THEME["neon_yellow"]))
            else:
                self.current_detections = []
                self.root.after(0, lambda: self.update_status(
                    "Детекций", "0", CYBERPUNK_THEME["text_color"]))
            
            self.current_visual_context = visual_context
            
            # Отображение
            self.root.after(0, lambda: self.display_frame(frame, detections))
            
        except Exception as e:
            logger.error(f"Ошибка обработки кадра: {e}", exc_info=True)
    
    def add_chat_message(self, role, content):
        """Добавление сообщения в чат"""
        color = CYBERPUNK_THEME["neon_cyan"] if role == "user" else CYBERPUNK_THEME["neon_pink"]
        name = "[ВЫ]" if role == "user" else "[ЭКОНЕТ]"
        
        msg_frame = ctk.CTkFrame(self.chat_scroll, fg_color=CYBERPUNK_THEME["fg_color"],
                                corner_radius=5)
        msg_frame.pack(fill="x", padx=5, pady=5)
        
        name_label = ctk.CTkLabel(msg_frame, text=name,
                                font=("Consolas", 10, "bold"),
                                text_color=color)
        name_label.pack(anchor="w", padx=10, pady=(8, 5))
        
        text_label = ctk.CTkLabel(msg_frame, text=content,
                                  font=("Consolas", 10),
                                  text_color=CYBERPUNK_THEME["text_color"],
                                  wraplength=800,
                                  justify="left")
        text_label.pack(anchor="w", padx=10, pady=(0, 8))
    
    def send_message(self):
        """Отправка сообщения"""
        message = self.chat_input.get().strip()
        if message:
            self.chat_input.delete(0, "end")
            self.add_chat_message("user", message)
            
            if self.loop and self.unified_engine:
                asyncio.run_coroutine_threadsafe(
                    self.process_message_async(message),
                    self.loop
                )
    
    async def process_message_async(self, message: str):
        """Асинхронная обработка сообщения через UnifiedEngine"""
        try:
            # Обработка через единый движок (использует DeepSeek)
            response = await self.unified_engine.process_message(
                message,
                self.current_visual_context
            )
            
            if response and response.strip():
                self.root.after(0, lambda: self.add_chat_message("assistant", response))
            else:
                fallback = "Я получил ваше сообщение. Попробуйте переформулировать."
                self.root.after(0, lambda: self.add_chat_message("assistant", fallback))
                
        except Exception as e:
            logger.error(f"Ошибка обработки сообщения: {e}", exc_info=True)
    
    def run(self):
        """Запуск интерфейса"""
        self.root.mainloop()


def main():
    """Главная функция"""
    try:
        app = ModernEcoNetGUI()
        app.run()
    except ImportError as e:
        print(f"Ошибка: {e}")
        print("Установите CustomTkinter: pip install customtkinter")
        sys.exit(1)


if __name__ == "__main__":
    main()

