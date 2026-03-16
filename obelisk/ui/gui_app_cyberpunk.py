"""
КИБЕРПАНК интерфейс ЭкоНет
Полностью переработанный интерфейс в стиле киберпанк с живым чатом
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog
import cv2
import asyncio
import threading
import logging
import sys
from pathlib import Path
from PIL import Image, ImageTk, ImageDraw, ImageFont
import yaml
from datetime import datetime
from typing import Optional, Dict, List
import numpy as np
import json
import re

# Добавление корня проекта в путь
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))

from obelisk.services.chat_service import ChatService
from obelisk.services.vision_context import VisionContext
from edge.inference_service.detector import CigaretteDetector
from obelisk.services.active_learner import ActiveLearner
from obelisk.services.database import Database
from obelisk.services.mqtt_client import MQTTClient

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ПРОФЕССИОНАЛЬНАЯ КИБЕРПАНК цветовая схема (на основе лучших практик)
CYBERPUNK = {
    # Фоны (темные с глубиной)
    'bg_main': '#000000',           # Абсолютно черный
    'bg_panel': '#0A0A14',          # Очень темный синий
    'bg_card': '#141420',           # Темный карточки
    'bg_hover': '#1E1E2E',          # Hover эффект
    'bg_glow': '#0F0F1F',           # Фон для свечения
    
    # Неоновые цвета (яркие, насыщенные)
    'neon_cyan': '#00FFFF',         # Чистый циан
    'neon_pink': '#FF00FF',         # Чистый розовый
    'neon_green': '#00FF00',        # Чистый зеленый
    'neon_yellow': '#FFFF00',       # Чистый желтый
    'neon_purple': '#9D00FF',       # Фиолетовый
    'neon_orange': '#FF6600',       # Оранжевый
    
    # Акценты
    'accent': '#00D9FF',            # Яркий циан
    'accent_dark': '#0099CC',       # Темный циан
    'accent_light': '#33E6FF',      # Светлый циан
    
    # Свечение (с прозрачностью)
    'glow_cyan': '#00FFFF44',       # Свечение циан
    'glow_pink': '#FF00FF44',       # Свечение розовый
    'glow_green': '#00FF0044',      # Свечение зеленый
    'glow_yellow': '#FFFF0044',     # Свечение желтый
    
    # Статусы
    'success': '#00FF41',           # Зеленый успех
    'warning': '#FFAA00',           # Оранжевый предупреждение
    'error': '#FF0040',             # Красный ошибка
    'info': '#00D9FF',              # Циан информация
    
    # Текст
    'text_primary': '#E0E0FF',      # Светло-синий текст (высокий контраст)
    'text_secondary': '#A0A0CC',    # Серо-синий
    'text_muted': '#606080',        # Приглушенный
    'text_glow': '#FFFFFF',         # Белый для свечения
    
    # Границы и эффекты
    'border': '#2A2A3E',            # Граница
    'border_glow': '#00FFFF22',     # Свечение границы
    'scanline': '#00FFFF08',        # Сканирующая линия (очень прозрачная)
    'glitch': '#FF00FF',            # Глитч эффект
}


class CyberButton(tk.Canvas):
    """Профессиональная киберпанк кнопка с неоновым свечением и эффектами"""
    def __init__(self, parent, text, command=None, width=140, height=45,
                 color=CYBERPUNK['neon_cyan'], glow_color=CYBERPUNK['glow_cyan']):
        super().__init__(parent, width=width, height=height,
                        highlightthickness=0, bg=CYBERPUNK['bg_main'],
                        cursor='hand2')
        self.command = command
        self.color = color
        self.glow_color = glow_color
        self.width = width
        self.height = height
        self.is_pressed = False
        self.is_hover = False
        self._text = text
        
        self.draw_button()
        
        self.bind('<Enter>', self.on_enter)
        self.bind('<Leave>', self.on_leave)
        self.bind('<Button-1>', self.on_press)
        self.bind('<ButtonRelease-1>', self.on_release)
    
    def draw_button(self):
        """Профессиональная отрисовка кнопки с эффектами"""
        self.delete('all')
        
        # Внешнее свечение (более интенсивное при hover)
        glow_intensity = 0.6 if self.is_hover else 0.3
        if self.is_hover or self.is_pressed:
            # Многослойное свечение для глубины
            for i in range(3, 0, -1):
                alpha = int(glow_intensity * 255 / i)
                glow_hex = f"{self.color[1:3]}{self.color[3:5]}{self.color[5:7]}{alpha:02X}"
                self.create_rectangle(-i*2, -i*2, self.width+i*2, self.height+i*2,
                                    fill=f"#{glow_hex}", outline='', tags='glow')
        
        # Основная рамка с неоновым эффектом
        border_width = 2
        outline_color = self.color if not self.is_pressed else CYBERPUNK['accent_light']
        self.create_rectangle(border_width, border_width,
                             self.width-border_width, self.height-border_width,
                             fill=CYBERPUNK['bg_card'],
                             outline=outline_color,
                             width=2, tags='bg')
        
        # Внутренняя рамка для эффекта глубины (тонкая)
        inner_border = 5
        self.create_rectangle(inner_border, inner_border,
                             self.width-inner_border, self.height-inner_border,
                             outline=CYBERPUNK['border'],
                             width=1, tags='inner')
        
        # Угловые акценты (киберпанк деталь)
        corner_size = 8
        corner_color = self.color
        # Левый верхний
        self.create_line(border_width, border_width,
                        border_width+corner_size, border_width,
                        fill=corner_color, width=2, tags='corner')
        self.create_line(border_width, border_width,
                        border_width, border_width+corner_size,
                        fill=corner_color, width=2, tags='corner')
        # Правый нижний
        self.create_line(self.width-border_width-corner_size, self.height-border_width,
                        self.width-border_width, self.height-border_width,
                        fill=corner_color, width=2, tags='corner')
        self.create_line(self.width-border_width, self.height-border_width-corner_size,
                        self.width-border_width, self.height-border_width,
                        fill=corner_color, width=2, tags='corner')
        
        # Текст с неоновым эффектом
        text_color = self.color if not self.is_pressed else CYBERPUNK['accent_light']
        # Тень текста для эффекта свечения
        self.create_text(self.width//2+1, self.height//2+1,
                        text=self._text,
                        fill=CYBERPUNK['bg_main'],
                        font=('Consolas', 10, 'bold'),
                        tags='text_shadow')
        # Основной текст
        self.create_text(self.width//2, self.height//2,
                        text=self._text,
                        fill=text_color,
                        font=('Consolas', 10, 'bold'),
                        tags='text')
    
    def get_text(self):
        """Получить текст кнопки"""
        return self._text
    
    def set_text(self, text):
        """Установить текст"""
        self._text = text
        self.draw_button()
    
    def on_enter(self, e):
        self.is_hover = True
        self.draw_button()
    
    def on_leave(self, e):
        self.is_hover = False
        self.draw_button()
    
    def on_press(self, e):
        self.is_pressed = True
        self.draw_button()
    
    def on_release(self, e):
        self.is_pressed = False
        self.draw_button()
        if self.command:
            self.command()


class CyberPanel(tk.Frame):
    """Профессиональная киберпанк панель с неоновой рамкой и эффектами"""
    def __init__(self, parent, title="", **kwargs):
        super().__init__(parent, bg=CYBERPUNK['bg_main'], **kwargs)
        self.title = title
        self.setup_panel()
    
    def setup_panel(self):
        """Настройка панели с профессиональными эффектами"""
        # Внешняя неоновая рамка (верхняя)
        border_top = tk.Frame(self, bg=CYBERPUNK['neon_cyan'], height=2)
        border_top.pack(fill='x')
        
        # Внутренний контейнер с отступом
        inner = tk.Frame(self, bg=CYBERPUNK['bg_panel'])
        inner.pack(fill='both', expand=True, padx=2, pady=2)
        
        if self.title:
            # Заголовок с эффектом свечения
            title_frame = tk.Frame(inner, bg=CYBERPUNK['bg_panel'])
            title_frame.pack(fill='x', padx=10, pady=8)
            
            # Угловые акценты перед заголовком
            accent_canvas = tk.Canvas(title_frame, width=20, height=20,
                                     bg=CYBERPUNK['bg_panel'], highlightthickness=0)
            accent_canvas.pack(side='left', padx=(0, 10))
            # Рисуем угол
            accent_canvas.create_line(0, 20, 0, 0, fill=CYBERPUNK['neon_cyan'], width=2)
            accent_canvas.create_line(0, 0, 20, 0, fill=CYBERPUNK['neon_cyan'], width=2)
            
            title_label = tk.Label(title_frame, text=self.title,
                                  bg=CYBERPUNK['bg_panel'],
                                  fg=CYBERPUNK['neon_cyan'],
                                  font=('Consolas', 11, 'bold'))
            title_label.pack(side='left')
            
            # Разделитель с эффектом
            separator = tk.Frame(inner, bg=CYBERPUNK['border'], height=1)
            separator.pack(fill='x', padx=10, pady=(5, 8))
            
            # Тонкая неоновая линия под разделителем
            neon_line = tk.Frame(inner, bg=CYBERPUNK['neon_cyan'], height=1)
            neon_line.pack(fill='x', padx=10, pady=(0, 8))
        
        self.inner = inner


class CyberVideoPanel(CyberPanel):
    """Панель видео с киберпанк стилем"""
    def __init__(self, parent):
        super().__init__(parent, title="[ВИДЕО СТРИМ]")
        self.setup_video()
    
    def setup_video(self):
        """Настройка видео области"""
        # Видео контейнер
        video_container = tk.Frame(self.inner, bg=CYBERPUNK['bg_card'],
                                  highlightthickness=2,
                                  highlightbackground=CYBERPUNK['neon_cyan'])
        video_container.pack(fill='both', expand=True, padx=10, pady=10)
        
        self.video_label = tk.Label(video_container,
                                   text="[ОЖИДАНИЕ ВИДЕО СТРИМА]\n\nЗагрузите видео или подключите камеру",
                                   bg=CYBERPUNK['bg_card'],
                                   fg=CYBERPUNK['text_muted'],
                                   font=('Consolas', 11),
                                   justify='center')
        self.video_label.pack(fill='both', expand=True, padx=20, pady=20)
        self.current_image = None
    
    def display_frame(self, frame, detections=None):
        """Отображение кадра с детекциями"""
        try:
            if frame is None:
                return
            
            display_frame = frame.copy()
            
            # Рисуем детекции в киберпанк стиле
            if detections:
                for det in detections:
                    x, y, w, h = det['bbox']
                    conf = det['confidence']
                    
                    # Неоновая рамка
                    cv2.rectangle(display_frame,
                                (int(x), int(y)),
                                (int(x+w), int(y+h)),
                                (0, 255, 255), 3)  # Циан
                    
                    # Внутренняя рамка
                    cv2.rectangle(display_frame,
                                (int(x)+2, int(y)+2),
                                (int(x+w)-2, int(y+h)-2),
                                (255, 0, 255), 1)  # Розовый
                    
                    # Текст с фоном
                    label = f"CIGARETTE {conf:.0%}"
                    (text_width, text_height), baseline = cv2.getTextSize(
                        label, cv2.FONT_HERSHEY_SIMPLEX, 0.7, 2)
                    
                    # Фон для текста
                    cv2.rectangle(display_frame,
                                 (int(x), int(y)-text_height-15),
                                 (int(x)+text_width+10, int(y)),
                                 (0, 0, 0), -1)
                    
                    # Текст
                    cv2.putText(display_frame, label,
                              (int(x)+5, int(y)-8),
                              cv2.FONT_HERSHEY_SIMPLEX, 0.7,
                              (0, 255, 255), 2)
            
            # Масштабирование для отображения
            height, width = display_frame.shape[:2]
            if height == 0 or width == 0:
                return
            
            max_width = 1200
            max_height = 700
            
            if width > max_width or height > max_height:
                scale = min(max_width / width, max_height / height)
                new_width = int(width * scale)
                new_height = int(height * scale)
                display_frame = cv2.resize(display_frame, (new_width, new_height),
                                         interpolation=cv2.INTER_LINEAR)
            
            # Конвертация для Tkinter
            frame_rgb = cv2.cvtColor(display_frame, cv2.COLOR_BGR2RGB)
            img = Image.fromarray(frame_rgb)
            img_tk = ImageTk.PhotoImage(image=img)
            
            self.video_label.config(image=img_tk, text='')
            self.video_label.image = img_tk  # КРИТИЧНО: сохраняем ссылку!
            self.current_image = img_tk
            
        except Exception as e:
            logger.error(f"Ошибка отображения кадра: {e}", exc_info=True)


class CyberChatPanel(CyberPanel):
    """Живой чат в киберпанк стиле"""
    def __init__(self, parent):
        super().__init__(parent, title="[ДИАЛОГ С ЭКОНЕТ]")
        self.setup_chat()
        self.message_queue = []
        self.is_thinking = False
    
    def setup_chat(self):
        """Настройка чата"""
        # Canvas для прокрутки
        chat_canvas = tk.Canvas(self.inner, bg=CYBERPUNK['bg_card'],
                               highlightthickness=1,
                               highlightbackground=CYBERPUNK['neon_cyan'])
        chat_canvas.pack(fill='both', expand=True, padx=10, pady=10)
        
        scrollbar = tk.Scrollbar(self.inner, orient='vertical',
                                command=chat_canvas.yview,
                                bg=CYBERPUNK['bg_card'],
                                troughcolor=CYBERPUNK['bg_main'],
                                activebackground=CYBERPUNK['neon_cyan'])
        scrollbar.pack(side='right', fill='y', padx=(0, 10), pady=10)
        
        chat_canvas.configure(yscrollcommand=scrollbar.set)
        
        # Фрейм для сообщений
        self.chat_frame = tk.Frame(chat_canvas, bg=CYBERPUNK['bg_card'])
        chat_canvas.create_window((0, 0), window=self.chat_frame, anchor='nw')
        
        self.chat_frame.bind('<Configure>',
                           lambda e: chat_canvas.configure(
                               scrollregion=chat_canvas.bbox('all')))
        
        self.chat_canvas = chat_canvas
        
        # Поле ввода
        input_frame = tk.Frame(self.inner, bg=CYBERPUNK['bg_panel'])
        input_frame.pack(fill='x', padx=10, pady=(0, 10))
        
        self.input_entry = tk.Entry(input_frame,
                                    bg=CYBERPUNK['bg_card'],
                                    fg=CYBERPUNK['text_primary'],
                                    insertbackground=CYBERPUNK['neon_cyan'],
                                    font=('Consolas', 10),
                                    relief='flat',
                                    borderwidth=2,
                                    highlightthickness=1,
                                    highlightbackground=CYBERPUNK['neon_cyan'],
                                    highlightcolor=CYBERPUNK['neon_pink'])
        self.input_entry.pack(side='left', fill='x', expand=True, padx=(0, 5))
        self.input_entry.bind('<Return>', self.on_send)
        
        send_btn = CyberButton(input_frame, "SEND", width=80, height=35,
                              color=CYBERPUNK['neon_green'])
        send_btn.pack(side='right')
        send_btn.command = self.on_send
    
    def on_send(self, event=None):
        """Отправка сообщения"""
        message = self.input_entry.get().strip()
        if message:
            self.input_entry.delete(0, tk.END)
            return message
        return None
    
    def add_message(self, role, content, thinking=None):
        """Добавление сообщения"""
        # Фрейм сообщения
        msg_frame = tk.Frame(self.chat_frame, bg=CYBERPUNK['bg_card'])
        msg_frame.pack(fill='x', padx=10, pady=5)
        
        # Цвет в зависимости от роли
        if role == "user":
            border_color = CYBERPUNK['neon_cyan']
            text_color = CYBERPUNK['neon_cyan']
            name = "[ВЫ]"
        elif role == "assistant":
            border_color = CYBERPUNK['neon_pink']
            text_color = CYBERPUNK['neon_pink']
            name = "[ЭКОНЕТ]"
        else:
            border_color = CYBERPUNK['text_muted']
            text_color = CYBERPUNK['text_muted']
            name = "[СИСТЕМА]"
        
        # Рамка сообщения
        msg_bubble = tk.Frame(msg_frame, bg=CYBERPUNK['bg_panel'],
                             highlightthickness=1,
                             highlightbackground=border_color)
        msg_bubble.pack(fill='x', padx=5)
        
        # Имя и время
        header = tk.Frame(msg_bubble, bg=CYBERPUNK['bg_panel'])
        header.pack(fill='x', padx=10, pady=(8, 5))
        
        name_label = tk.Label(header, text=name,
                             bg=CYBERPUNK['bg_panel'],
                             fg=border_color,
                             font=('Consolas', 9, 'bold'))
        name_label.pack(side='left')
        
        time_label = tk.Label(header, text=datetime.now().strftime("%H:%M:%S"),
                             bg=CYBERPUNK['bg_panel'],
                             fg=CYBERPUNK['text_muted'],
                             font=('Consolas', 8))
        time_label.pack(side='right')
        
        # Текст сообщения
        text_widget = tk.Text(msg_bubble,
                            bg=CYBERPUNK['bg_panel'],
                            fg=text_color,
                            font=('Consolas', 10),
                            wrap=tk.WORD,
                            relief='flat',
                            borderwidth=0,
                            padx=10,
                            pady=5,
                            highlightthickness=0)
        text_widget.pack(fill='x', padx=5, pady=(0, 8))
        text_widget.insert('1.0', content)
        text_widget.config(state=tk.DISABLED)
        
        # Thinking mode
        if thinking:
            thinking_frame = tk.Frame(msg_bubble, bg=CYBERPUNK['bg_card'])
            thinking_frame.pack(fill='x', padx=5, pady=(0, 8))
            
            thinking_label = tk.Label(thinking_frame,
                                     text="[ОБДУМЫВАНИЕ]",
                                     bg=CYBERPUNK['bg_card'],
                                     fg=CYBERPUNK['neon_yellow'],
                                     font=('Consolas', 8, 'bold'))
            thinking_label.pack(anchor='w', padx=10, pady=5)
            
            thinking_text = tk.Text(thinking_frame,
                                   bg=CYBERPUNK['bg_card'],
                                   fg=CYBERPUNK['text_secondary'],
                                   font=('Consolas', 8),
                                   wrap=tk.WORD,
                                   height=3,
                                   relief='flat',
                                   borderwidth=0,
                                   padx=10,
                                   pady=5)
            thinking_text.insert('1.0', thinking[:500])  # Ограничение длины
            thinking_text.config(state=tk.DISABLED)
            thinking_text.pack(fill='x', padx=5, pady=(0, 5))
        
        self.chat_canvas.update_idletasks()
        self.chat_canvas.yview_moveto(1.0)
    
    def show_thinking(self, content):
        """Показать процесс обдумывания"""
        if not self.is_thinking:
            self.is_thinking = True
            thinking_frame = tk.Frame(self.chat_frame, bg=CYBERPUNK['bg_card'])
            thinking_frame.pack(fill='x', padx=10, pady=5)
            
            label = tk.Label(thinking_frame,
                           text="[ЭКОНЕТ ОБДУМЫВАЕТ...]",
                           bg=CYBERPUNK['bg_card'],
                           fg=CYBERPUNK['neon_yellow'],
                           font=('Consolas', 9, 'bold'))
            label.pack(anchor='w', padx=10, pady=5)
            
            self.thinking_text = tk.Text(thinking_frame,
                                        bg=CYBERPUNK['bg_card'],
                                        fg=CYBERPUNK['text_secondary'],
                                        font=('Consolas', 8),
                                        wrap=tk.WORD,
                                        height=4,
                                        relief='flat',
                                        borderwidth=0,
                                        padx=10,
                                        pady=5)
            self.thinking_text.pack(fill='x', padx=5, pady=(0, 5))
            self.thinking_frame = thinking_frame
        
        if content:
            self.thinking_text.config(state=tk.NORMAL)
            self.thinking_text.insert(tk.END, content)
            self.thinking_text.config(state=tk.DISABLED)
            self.chat_canvas.update_idletasks()
            self.chat_canvas.yview_moveto(1.0)
    
    def hide_thinking(self):
        """Скрыть обдумывание"""
        if self.is_thinking and hasattr(self, 'thinking_frame'):
            self.thinking_frame.pack_forget()
            self.is_thinking = False


class CyberStatusPanel(CyberPanel):
    """Панель статуса"""
    def __init__(self, parent):
        super().__init__(parent, title="[СТАТУС СИСТЕМЫ]")
        self.status_labels = {}  # Инициализируем ДО setup_status
        self.setup_status()
    
    def setup_status(self):
        """Настройка статуса"""
        status_items = [
            ("Модель", "Загрузка..."),
            ("Детектор", "Инициализация..."),
            ("Видео", "Не подключено"),
            ("FPS", "0"),
            ("Детекций", "0"),
        ]
        
        for i, (key, value) in enumerate(status_items):
            frame = tk.Frame(self.inner, bg=CYBERPUNK['bg_panel'])
            frame.pack(fill='x', padx=10, pady=5)
            
            key_label = tk.Label(frame, text=f"{key}:",
                               bg=CYBERPUNK['bg_panel'],
                               fg=CYBERPUNK['text_secondary'],
                               font=('Consolas', 9))
            key_label.pack(side='left')
            
            value_label = tk.Label(frame, text=value,
                                 bg=CYBERPUNK['bg_panel'],
                                 fg=CYBERPUNK['neon_green'],
                                 font=('Consolas', 9, 'bold'))
            value_label.pack(side='left', padx=(10, 0))
            
            self.status_labels[key] = value_label
    
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
            
            self.status_labels[key].config(
                text=formatted_value,
                fg=color if color else CYBERPUNK['neon_green']
            )


class EcoNetCyberpunkGUI:
    """Киберпанк интерфейс ЭкоНет"""
    
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("ЭКОНЕТ [КИБЕРПАНК МОДЕ]")
        self.root.geometry("1920x1080")
        self.root.configure(bg=CYBERPUNK['bg_main'])
        
        # Состояние
        self.config = None
        self.detector = None
        self.vision_context = None
        self.chat_service = None
        self.active_learner = None
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
            messagebox.showerror("ОШИБКА", f"Не удалось загрузить конфигурацию: {e}")
            self.config = {}
    
    def setup_ui(self):
        """Настройка интерфейса"""
        # Главный контейнер
        main_container = tk.Frame(self.root, bg=CYBERPUNK['bg_main'])
        main_container.pack(fill='both', expand=True, padx=5, pady=5)
        
        # Верхняя панель с кнопками
        top_panel = tk.Frame(main_container, bg=CYBERPUNK['bg_main'])
        top_panel.pack(fill='x', pady=(0, 5))
        
        btn_frame = tk.Frame(top_panel, bg=CYBERPUNK['bg_main'])
        btn_frame.pack(side='left', padx=10)
        
        CyberButton(btn_frame, "ЗАГРУЗИТЬ ВИДЕО",
                   command=self.load_video,
                   color=CYBERPUNK['neon_cyan']).pack(side='left', padx=5)
        
        CyberButton(btn_frame, "КАМЕРА",
                   command=self.connect_camera,
                   color=CYBERPUNK['neon_pink']).pack(side='left', padx=5)
        
        CyberButton(btn_frame, "IP КАМЕРА",
                   command=self.connect_ip_camera,
                   color=CYBERPUNK['neon_green']).pack(side='left', padx=5)
        
        CyberButton(btn_frame, "СТАРТ ДЕТЕКЦИИ",
                   command=self.start_detection,
                   color=CYBERPUNK['neon_yellow']).pack(side='left', padx=5)
        
        CyberButton(btn_frame, "СТОП",
                   command=self.stop_detection,
                   color=CYBERPUNK['error']).pack(side='left', padx=5)
        
        # Основной контент
        content_frame = tk.Frame(main_container, bg=CYBERPUNK['bg_main'])
        content_frame.pack(fill='both', expand=True)
        
        # Левая панель - видео
        left_panel = tk.Frame(content_frame, bg=CYBERPUNK['bg_main'])
        left_panel.pack(side='left', fill='both', expand=True, padx=(0, 5))
        
        self.video_panel = CyberVideoPanel(left_panel)
        self.video_panel.pack(fill='both', expand=True)
        
        # Правая панель - статус
        right_panel = tk.Frame(content_frame, bg=CYBERPUNK['bg_main'], width=300)
        right_panel.pack(side='right', fill='y', padx=(5, 0))
        right_panel.pack_propagate(False)
        
        self.status_panel = CyberStatusPanel(right_panel)
        self.status_panel.pack(fill='both', expand=True)
        
        # Нижняя панель - чат
        chat_panel_frame = tk.Frame(main_container, bg=CYBERPUNK['bg_main'], height=300)
        chat_panel_frame.pack(fill='x', pady=(5, 0))
        chat_panel_frame.pack_propagate(False)
        
        self.chat_panel = CyberChatPanel(chat_panel_frame)
        self.chat_panel.pack(fill='both', expand=True)
        
        # Привязка отправки сообщений
        self.chat_panel.input_entry.bind('<Return>', lambda e: self.send_message())
    
    def init_async_components(self):
        """Инициализация асинхронных компонентов"""
        def init_loop():
            self.loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self.loop)
            self.loop.run_until_complete(self._async_init())
        
        self.loop_thread = threading.Thread(target=init_loop, daemon=True)
        self.loop_thread.start()
    
    async def _async_init(self):
        """Асинхронная инициализация"""
        try:
            # Проверка модели
            model_path_str = self.config.get("model", {}).get("weights_path",
                                                               "models/cigarette_detector/best.pt")
            model_path = project_root / model_path_str if not Path(model_path_str).is_absolute() else Path(model_path_str)
            
            if model_path.exists():
                self.root.after(0, lambda: self.status_panel.update_status(
                    "Модель", "ГОТОВА", CYBERPUNK['success']))
            else:
                self.root.after(0, lambda: self.status_panel.update_status(
                    "Модель", "НЕ НАЙДЕНА", CYBERPUNK['error']))
            
            # Инициализация детектора
            self.detector = CigaretteDetector(self.config)
            await self.detector.initialize_mqtt()
            self.vision_context = VisionContext(self.detector)
            
            self.root.after(0, lambda: self.status_panel.update_status(
                "Детектор", "АКТИВЕН", CYBERPUNK['success']))
            
            # Инициализация чата с DeepSeek
            from obelisk.services.self_identity import SelfIdentityService
            from obelisk.services.self_modification import SelfModificationService
            from obelisk.services.self_learning import SelfLearningService
            
            self_identity = SelfIdentityService(project_root=project_root)
            self_modification = SelfModificationService(project_root, self_identity)
            self_learning = SelfLearningService(self_identity, self_modification, self.config)
            
            self.chat_service = ChatService(
                self.config,
                detector=self.detector,
                active_learner=self.active_learner,
                self_identity=self_identity,
                self_modification=self_modification,
                self_learning=self_learning
            )
            
            # Приветствие
            greeting = self.chat_service._greet()
            self.root.after(0, lambda: self.chat_panel.add_message("assistant", greeting))
            
            logger.info("Компоненты инициализированы")
            
        except Exception as e:
            logger.error(f"Ошибка инициализации: {e}", exc_info=True)
            error_msg = f"Ошибка инициализации: {e}"
            self.root.after(0, lambda: messagebox.showerror("ОШИБКА", error_msg))
    
    def load_video(self):
        """Загрузка видео из файла"""
        file_path = filedialog.askopenfilename(
            title="Выберите видео",
            filetypes=[("Video files", "*.mp4 *.avi *.mov *.mkv"), ("All files", "*.*")]
        )
        if file_path:
            self.connect_source(file_path)
    
    def connect_camera(self):
        """Подключение к локальной камере"""
        self.connect_source(0)
    
    def connect_ip_camera(self):
        """Подключение к IP камере"""
        ip = tk.simpledialog.askstring("IP Камера", "Введите URL камеры:")
        if ip:
            self.connect_source(ip)
    
    def connect_source(self, source):
        """Подключение к источнику видео"""
        self.stop_detection()
        
        try:
            if isinstance(source, str) and source.isdigit():
                source = int(source)
            
            self.cap = cv2.VideoCapture(source)
            if not self.cap.isOpened():
                raise Exception(f"Не удалось открыть источник: {source}")
            
            # Сразу показываем первый кадр
            ret, frame = self.cap.read()
            if ret and frame is not None:
                self.current_frame = frame
                self.video_panel.display_frame(frame, [])
                self.is_playing = True
            
            source_name = Path(source).name if isinstance(source, str) else f'Камера {source}'
            self.root.after(0, lambda: self.status_panel.update_status(
                "Видео", "ПОДКЛЮЧЕНО", CYBERPUNK['success']))
            self.root.after(0, lambda: self.chat_panel.add_message(
                "system", f"Видео загружено: {source_name}"))
            
        except Exception as e:
            messagebox.showerror("ОШИБКА", f"Не удалось подключиться: {e}")
            logger.error(f"Ошибка подключения: {e}")
    
    def start_detection(self):
        """Запуск детекции"""
        if not self.cap:
            messagebox.showwarning("ВНИМАНИЕ", "Сначала загрузите видео или подключите камеру")
            return
        
        self.is_playing = True
        self.root.after(0, lambda: self.status_panel.update_status(
            "Видео", "ДЕТЕКЦИЯ АКТИВНА", CYBERPUNK['neon_yellow']))
        self.root.after(0, lambda: self.chat_panel.add_message(
            "system", "Детекция запущена"))
    
    def stop_detection(self):
        """Остановка детекции"""
        self.is_playing = False
        if self.cap:
            self.cap.release()
            self.cap = None
        self.current_frame = None
        self.root.after(0, lambda: self.status_panel.update_status(
            "Видео", "ОСТАНОВЛЕНО", CYBERPUNK['text_muted']))
        self.root.after(0, lambda: self.chat_panel.add_message(
            "system", "Детекция остановлена"))
    
    def update_video(self):
        """Обновление видеокадра"""
        if self.cap and self.is_playing:
            ret, frame = self.cap.read()
            if not ret or frame is None:
                self.is_playing = False
                return
            
            self.current_frame = frame
            
            # Асинхронная обработка с детекцией
            if self.loop and self.detector:
                asyncio.run_coroutine_threadsafe(
                    self.process_frame_async(frame),
                    self.loop
                )
            else:
                # Просто отображение если детектор не готов
                self.video_panel.display_frame(frame, [])
        
        # Обновление FPS
        self.fps_counter += 1
        now = datetime.now()
        if (now - self.fps_time).total_seconds() >= 1.0:
            fps = self.fps_counter
            self.fps_counter = 0
            self.fps_time = now
            self.root.after(0, lambda: self.status_panel.update_status(
                "FPS", str(fps), CYBERPUNK['neon_cyan']))
        
        # УБРАНО: ограничение 33ms (~30 FPS) - обновление без задержки для максимальной скорости
        self.root.after(0, self.update_video)
    
    async def process_frame_async(self, frame):
        """Асинхронная обработка кадра"""
        try:
            if not self.detector:
                return
            
            # Детекция
            detections = await self.detector.detect_frame(frame)
            
            if detections:
                self.current_detections = detections
                count = len(detections)
                self.root.after(0, lambda: self.status_panel.update_status(
                    "Детекций", str(count), CYBERPUNK['neon_yellow']))
            else:
                self.current_detections = []
                self.root.after(0, lambda: self.status_panel.update_status(
                    "Детекций", "0", CYBERPUNK['text_muted']))
            
            # Визуальный контекст
            if self.vision_context:
                self.current_visual_context = await self.vision_context.analyze_frame(
                    frame, detections
                )
            
            # Отображение
            self.root.after(0, lambda: self.video_panel.display_frame(frame, detections))
            
        except Exception as e:
            logger.error(f"Ошибка обработки кадра: {e}", exc_info=True)
    
    def send_message(self):
        """Отправка сообщения"""
        message = self.chat_panel.on_send()
        if message:
            self.chat_panel.add_message("user", message)
            
            if self.loop and self.chat_service:
                asyncio.run_coroutine_threadsafe(
                    self.process_message_async(message),
                    self.loop
                )
    
    async def process_message_async(self, message: str):
        """Асинхронная обработка сообщения"""
        try:
            thinking_content = ""
            response_content = ""
            
            # Callback для thinking mode
            async def stream_callback(event_type, content):
                nonlocal thinking_content, response_content
                if event_type == "thinking":
                    thinking_content += content
                    self.root.after(0, lambda: self.chat_panel.show_thinking(content))
                elif event_type == "thinking_done":
                    self.root.after(0, lambda: self.chat_panel.hide_thinking())
                elif event_type == "content":
                    response_content += content
            
            # Получаем ответ
            response = await self.chat_service.process_message(
                message,
                self.current_visual_context,
                stream_callback=stream_callback if self.chat_service.use_llm else None
            )
            
            self.root.after(0, lambda: self.chat_panel.hide_thinking())
            
            if response and response.strip():
                # Показываем thinking если есть
                thinking = thinking_content if thinking_content else None
                self.root.after(0, lambda: self.chat_panel.add_message(
                    "assistant", response, thinking=thinking))
            else:
                fallback = "Я получил ваше сообщение. Попробуйте переформулировать."
                self.root.after(0, lambda: self.chat_panel.add_message("assistant", fallback))
                
        except Exception as e:
            logger.error(f"Ошибка обработки сообщения: {e}", exc_info=True)
            self.root.after(0, lambda: self.chat_panel.hide_thinking())
            self.root.after(0, lambda: self.chat_panel.add_message(
                "error", f"Ошибка: {str(e)[:100]}"))


def main():
    """Главная функция"""
    root = tk.Tk()
    app = EcoNetCyberpunkGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()

