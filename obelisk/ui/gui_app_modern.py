"""
Современный графический интерфейс для ЭкоНет
Улучшенный дизайн в стиле ЭкоНет с градиентами и анимациями
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
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


# Цветовая схема ЭкоНет 2025 - Современный стиль с градиентами
COLORS = {
    # Основные цвета с градиентами
    'primary': '#6366F1',           # Индиго основной (современный)
    'primary_dark': '#4F46E5',      # Индиго темный
    'primary_light': '#818CF8',     # Индиго светлый
    'primary_gradient_start': '#6366F1',  # Начало градиента
    'primary_gradient_end': '#8B5CF6',    # Конец градиента (фиолетовый)
    
    'accent': '#06B6D4',            # Циан акцент (яркий)
    'accent_dark': '#0891B2',       # Циан темный
    'accent_light': '#22D3EE',      # Циан светлый
    'accent_gradient_start': '#06B6D4',   # Градиент акцента
    'accent_gradient_end': '#3B82F6',     # К синему
    
    # Статусные цвета
    'success': '#10B981',           # Изумрудный (современный зеленый)
    'success_light': '#34D399',     # Светлый зеленый
    'warning': '#F59E0B',           # Янтарный (современный оранжевый)
    'warning_light': '#FBBF24',     # Светлый оранжевый
    'error': '#EF4444',             # Красный (современный)
    'error_light': '#F87171',       # Светлый красный
    'info': '#3B82F6',              # Синий информационный
    
    # Фоны (темная тема 2025)
    'bg_dark': '#0F172A',           # Очень темный синий (slate-900)
    'bg_medium': '#1E293B',         # Темный синий (slate-800)
    'bg_light': '#334155',          # Средний синий (slate-700)
    'bg_panel': '#1E293B',          # Фон панелей (slate-800)
    'bg_glass': 'rgba(30, 41, 59, 0.7)',  # Стеклянный эффект
    'bg_card': '#1E293B',           # Фон карточек
    
    # Текст
    'text_primary': '#F8FAFC',      # Почти белый (slate-50)
    'text_secondary': '#CBD5E1',    # Светло-серый (slate-300)
    'text_muted': '#94A3B8',        # Серый (slate-400)
    'text_disabled': '#64748B',     # Приглушенный (slate-500)
    
    # Границы и эффекты
    'border': '#334155',            # Граница (slate-700)
    'border_light': '#475569',      # Светлая граница (slate-600)
    'border_focus': '#6366F1',      # Фокус (индиго)
    'shadow': 'rgba(0, 0, 0, 0.3)', # Тень
    'glow': 'rgba(99, 102, 241, 0.5)',  # Свечение (индиго)
}


class ModernButton(tk.Canvas):
    """Современная кнопка 2025 - с градиентом и эффектами"""
    def __init__(self, parent, text, command=None, width=140, height=42,
                 bg_color=COLORS['primary'], hover_color=COLORS['primary_light'],
                 text_color=COLORS['text_primary'], icon=None, rounded=True):
        super().__init__(parent, width=width, height=height,
                        highlightthickness=0, bg=COLORS['bg_dark'],
                        cursor='hand2')
        self.command = command
        self.bg_color = bg_color
        self.hover_color = hover_color
        self.text_color = text_color
        self.is_pressed = False
        self.rounded = rounded
        self.radius = 12 if rounded else 0
        
        # Градиентный фон (имитация через несколько прямоугольников)
        self._draw_gradient_background(width, height, bg_color)
        
        # Текст с лучшей типографикой
        self.create_text(width//2, height//2, text=text,
                        fill=text_color, font=('Segoe UI', 11, 'bold'),
                        tags='text')
        
        # События
        self.bind('<Enter>', self.on_enter)
        self.bind('<Leave>', self.on_leave)
        self.bind('<Button-1>', self.on_press)
        self.bind('<ButtonRelease-1>', self.on_release)
    
    def _draw_gradient_background(self, width, height, color):
        """Рисует градиентный фон"""
        # Имитация градиента через несколько слоев
        steps = 5
        for i in range(steps):
            alpha = 1.0 - (i * 0.15)
            y_pos = (height / steps) * i
            if self.rounded:
                # Скругленные углы (упрощенная версия)
                self.create_rectangle(2, y_pos, width-2, height-2,
                                     fill=color, outline='', tags='bg',
                                     width=0)
            else:
                self.create_rectangle(2, y_pos, width-2, height-2,
                                     fill=color, outline='', tags='bg',
                                     width=0)
    
    def on_enter(self, e):
        if not self.is_pressed:
            # Плавное изменение цвета при наведении
            self.itemconfig('bg', fill=self.hover_color, outline=self.hover_color)
            # Эффект свечения
            self.configure(bg=COLORS['bg_medium'])
    
    def on_leave(self, e):
        if not self.is_pressed:
            self.itemconfig('bg', fill=self.bg_color, outline=self.bg_color)
            self.configure(bg=COLORS['bg_dark'])
    
    def on_press(self, e):
        self.is_pressed = True
        self.itemconfig('bg', fill=COLORS['primary_dark'], outline=COLORS['primary_dark'])
        # Эффект нажатия
        self.move('text', 0, 1)
    
    def on_release(self, e):
        self.is_pressed = False
        self.itemconfig('bg', fill=self.bg_color, outline=self.bg_color)
        self.move('text', 0, -1)
        if self.command:
            self.command()


class ModernPanel(tk.Frame):
    """Современная панель 2025 - с glassmorphism эффектом"""
    def __init__(self, parent, title="", **kwargs):
        bg = kwargs.pop('bg', COLORS['bg_panel'])
        super().__init__(parent, bg=bg, relief='flat', bd=0, **kwargs)
        
        # Скругленные углы (через canvas overlay)
        self.configure(highlightbackground=COLORS['border_light'],
                      highlightthickness=1)
        
        if title:
            title_frame = tk.Frame(self, bg=COLORS['bg_panel'], height=40)
            title_frame.pack(fill=tk.X, padx=12, pady=(12, 8))
            title_frame.pack_propagate(False)
            
            # Градиентный заголовок
            title_label = tk.Label(title_frame, text=title, bg=COLORS['bg_panel'],
                                  fg=COLORS['primary_light'],
                                  font=('Segoe UI', 12, 'bold'),
                                  anchor='w')
            title_label.pack(side=tk.LEFT, padx=12)
            
            # Современная линия-разделитель с градиентом
            separator = tk.Frame(self, bg=COLORS['border_light'], height=1)
            separator.pack(fill=tk.X, padx=12, pady=(0, 8))


class EcoNetGUI:
    """Главное окно приложения ЭкоНет - современный дизайн"""
    
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("ЭкоНет - Система автономной уборки окурков")
        self.root.geometry("1800x1050")
        self.root.configure(bg=COLORS['bg_dark'])
        
        # Современные настройки окна
        try:
            # Windows 11 стиль (если доступно)
            self.root.attributes('-alpha', 0.98)  # Легкая прозрачность
        except:
            pass
        
        # Состояние
        self.config = None
        self.detector = None
        self.vision_context = None
        self.chat_service = None
        self.active_learner = None
        self.cap = None
        self.current_source = None
        self.is_playing = False
        self.current_frame = None
        self.current_detections = []
        self.current_visual_context = None
        self.mode = "detection"
        
        # Асинхронный event loop
        self.loop = None
        self.loop_thread = None
        
        # Загрузка конфигурации
        self.load_config()
        
        # Настройка стилей
        self.setup_styles()
        
        # Инициализация UI
        self.setup_ui()
        self.init_async_components()
        
        # Обновление видео
        self.update_video()
    
    def setup_styles(self):
        """Настройка современных стилей"""
        style = ttk.Style()
        style.theme_use('clam')
        
        # Настройка стилей
        style.configure('Title.TLabel',
                       background=COLORS['bg_dark'],
                       foreground=COLORS['text_primary'],
                       font=('Segoe UI', 20, 'bold'))
        
        style.configure('Heading.TLabel',
                       background=COLORS['bg_panel'],
                       foreground=COLORS['primary_light'],
                       font=('Segoe UI', 13, 'bold'))
        
        # Современные стили 2025
        style.configure('Modern.TLabel',
                       background=COLORS['bg_panel'],
                       foreground=COLORS['text_primary'],
                       font=('Segoe UI', 10))
        
        style.configure('Modern.TEntry',
                       fieldbackground=COLORS['bg_light'],
                       foreground=COLORS['text_primary'],
                       borderwidth=1,
                       relief='flat',
                       padding=8)
        
        style.configure('Custom.TFrame',
                       background=COLORS['bg_panel'],
                       relief='flat')
        
        style.configure('Custom.TLabelFrame',
                       background=COLORS['bg_panel'],
                       foreground=COLORS['text_primary'],
                       borderwidth=0,
                       relief='flat')
        
        style.configure('Custom.TRadiobutton',
                       background=COLORS['bg_panel'],
                       foreground=COLORS['text_primary'],
                       font=('Segoe UI', 10),
                       focuscolor='none')
        
        style.map('Custom.TRadiobutton',
                 background=[('selected', COLORS['bg_panel']),
                           ('active', COLORS['bg_light'])],
                 foreground=[('selected', COLORS['primary_light']),
                           ('active', COLORS['text_primary'])],
                 indicatorcolor=[('selected', COLORS['primary']),
                               ('!selected', COLORS['border'])])
    
    def load_config(self):
        """Загрузка конфигурации"""
        try:
            config_path = project_root / "config" / "config.yaml"
            with open(config_path, 'r', encoding='utf-8') as f:
                self.config = yaml.safe_load(f)
        except Exception as e:
            logger.error(f"Ошибка загрузки конфигурации: {e}")
            messagebox.showerror("Ошибка", f"Не удалось загрузить конфигурацию: {e}")
            self.config = {}
    
    def init_async_components(self):
        """Инициализация асинхронных компонентов"""
        def init_loop():
            self.loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self.loop)
            self.loop.run_until_complete(self._async_init())
        
        self.loop_thread = threading.Thread(target=init_loop, daemon=True)
        self.loop_thread.start()
    
    async def _async_init(self):
        """Асинхронная инициализация компонентов"""
        try:
            self.detector = CigaretteDetector(self.config)
            await self.detector.initialize_mqtt()
            self.vision_context = VisionContext(self.detector)
            
            if self.config.get("active_learning", {}).get("enabled", False):
                db = Database(self.config['database'])
                await db.init()
                mqtt_client = MQTTClient(self.config['mqtt_topics'], self.config['obelisk'])
                await mqtt_client.connect()
                self.active_learner = ActiveLearner(self.config, db, mqtt_client)
            
            # Инициализация системы самоидентификации
            from obelisk.services.self_identity import SelfIdentityService
            from obelisk.services.self_modification import SelfModificationService
            from obelisk.services.self_learning import SelfLearningService
            from pathlib import Path
            
            project_root = Path(__file__).parent.parent.parent
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
            
            logger.info("✅ Компоненты инициализированы")
            
            # Отправка приветствия
            try:
                greeting = self.chat_service._greet()
                self.root.after(0, lambda: self.add_chat_message("assistant", greeting))
                logger.info("✅ Приветствие отправлено")
            except Exception as e:
                logger.error(f"Ошибка отправки приветствия: {e}", exc_info=True)
                # Fallback приветствие
                self.root.after(0, lambda: self.add_chat_message(
                    "assistant",
                    "Привет! Я ЭкоНет, система автономной уборки окурков. Готов помочь!"
                ))
            
        except Exception as e:
            logger.error(f"Ошибка инициализации: {e}", exc_info=True)
            error_msg = f"Ошибка инициализации: {e}"
            self.root.after(0, lambda: messagebox.showerror("Ошибка", error_msg))
            # Все равно показываем приветствие
            self.root.after(0, lambda: self.add_chat_message(
                "assistant",
                "Привет! Я ЭкоНет. Некоторые компоненты не инициализированы, но я готов общаться!"
            ))
    
    def setup_ui(self):
        """Настройка современного интерфейса"""
        # Заголовок
        header = tk.Frame(self.root, bg=COLORS['bg_dark'], height=60)
        header.pack(fill=tk.X)
        header.pack_propagate(False)
        
        title = tk.Label(header, text="🤖 ЭкоНет", bg=COLORS['bg_dark'],
                        fg=COLORS['primary_light'], font=('Segoe UI', 24, 'bold'))
        title.pack(side=tk.LEFT, padx=20, pady=15)
        
        subtitle = tk.Label(header, text="Система автономной уборки окурков",
                           bg=COLORS['bg_dark'], fg=COLORS['text_secondary'],
                           font=('Segoe UI', 11))
        subtitle.pack(side=tk.LEFT, padx=10, pady=15)
        
        # Главный контейнер
        main_container = tk.Frame(self.root, bg=COLORS['bg_dark'])
        main_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Верхняя часть: Видео и управление
        top_container = tk.Frame(main_container, bg=COLORS['bg_dark'])
        top_container.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # Левая часть: Видеоплеер
        video_panel = ModernPanel(top_container, title="👁️ Что видит ЭкоНет")
        video_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))
        
        # Видео область
        video_container = tk.Frame(video_panel, bg=COLORS['bg_dark'])
        video_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        self.video_label = tk.Label(video_container,
                                   text="Выберите источник видео",
                                   bg=COLORS['bg_dark'],
                                   fg=COLORS['text_muted'],
                                   font=('Segoe UI', 12))
        self.video_label.pack(fill=tk.BOTH, expand=True)
        
        # Панель управления видео
        controls_frame = tk.Frame(video_panel, bg=COLORS['bg_panel'])
        controls_frame.pack(fill=tk.X, padx=10, pady=10)
        
        # Кнопки управления
        btn_frame = tk.Frame(controls_frame, bg=COLORS['bg_panel'])
        btn_frame.pack(side=tk.LEFT)
        
        ModernButton(btn_frame, "📁 Видео", self.load_video,
                    width=100, height=35).pack(side=tk.LEFT, padx=3)
        ModernButton(btn_frame, "📱 IP Webcam", self.connect_ip_webcam,
                    width=120, height=35).pack(side=tk.LEFT, padx=3)
        ModernButton(btn_frame, "📷 Камера", self.connect_camera,
                    width=100, height=35).pack(side=tk.LEFT, padx=3)
        
        ModernButton(btn_frame, "▶️ Play", self.play_video,
                    width=80, height=35, bg_color=COLORS['success']).pack(side=tk.LEFT, padx=5)
        ModernButton(btn_frame, "⏸️ Pause", self.pause_video,
                    width=90, height=35, bg_color=COLORS['warning']).pack(side=tk.LEFT, padx=3)
        ModernButton(btn_frame, "⏹️ Stop", self.stop_video,
                    width=80, height=35, bg_color=COLORS['error']).pack(side=tk.LEFT, padx=3)
        
        # Информация о видео
        self.video_info_label = tk.Label(controls_frame, text="Источник не выбран",
                                        bg=COLORS['bg_panel'], fg=COLORS['text_secondary'],
                                        font=('Segoe UI', 9))
        self.video_info_label.pack(side=tk.RIGHT, padx=10)
        
        # Правая часть: Управление
        control_panel = ModernPanel(top_container, title="⚙️ Управление")
        control_panel.pack(side=tk.RIGHT, fill=tk.Y, padx=(5, 0))
        
        # Режимы работы
        mode_panel = tk.Frame(control_panel, bg=COLORS['bg_panel'])
        mode_panel.pack(fill=tk.X, padx=15, pady=10)
        
        mode_title = tk.Label(mode_panel, text="Режимы работы",
                             bg=COLORS['bg_panel'], fg=COLORS['text_primary'],
                             font=('Segoe UI', 10, 'bold'))
        mode_title.pack(anchor=tk.W, pady=(0, 8))
        
        self.mode_var = tk.StringVar(value="detection")
        modes = [
            ("🔍 Детекция", "detection"),
            ("👁️ Просмотр", "no_detection"),
            ("✏️ Обучение", "teaching")
        ]
        
        for text, value in modes:
            rb = ttk.Radiobutton(mode_panel, text=text, variable=self.mode_var,
                               value=value, command=self.change_mode,
                               style='Custom.TRadiobutton')
            rb.pack(anchor=tk.W, pady=3)
        
        # Статистика
        stats_panel = tk.Frame(control_panel, bg=COLORS['bg_panel'])
        stats_panel.pack(fill=tk.X, padx=15, pady=10)
        
        stats_title = tk.Label(stats_panel, text="📊 Статистика",
                              bg=COLORS['bg_panel'], fg=COLORS['text_primary'],
                              font=('Segoe UI', 10, 'bold'))
        stats_title.pack(anchor=tk.W, pady=(0, 8))
        
        self.stats_label = tk.Label(stats_panel,
                                    text="Детекций: 0\nУверенность: 0%",
                                    bg=COLORS['bg_panel'],
                                    fg=COLORS['text_secondary'],
                                    font=('Segoe UI', 10),
                                    justify=tk.LEFT)
        self.stats_label.pack(anchor=tk.W)
        
        # Быстрые действия
        actions_panel = tk.Frame(control_panel, bg=COLORS['bg_panel'])
        actions_panel.pack(fill=tk.X, padx=15, pady=10)
        
        actions_title = tk.Label(actions_panel, text="⚡ Быстрые действия",
                                bg=COLORS['bg_panel'], fg=COLORS['text_primary'],
                                font=('Segoe UI', 10, 'bold'))
        actions_title.pack(anchor=tk.W, pady=(0, 8))
        
        quick_actions = [
            ("Что видишь?", "Что видишь?"),
            ("Сколько окурков?", "Сколько окурков?"),
            ("Где окурки?", "Где окурки?"),
            ("Статус", "Статус")
        ]
        
        for text, msg in quick_actions:
            btn = ModernButton(actions_panel, text, lambda m=msg: self.send_message(m),
                             width=160, height=32, bg_color=COLORS['bg_light'],
                             hover_color=COLORS['bg_medium'])
            btn.pack(fill=tk.X, pady=3)
        
        # Нижняя часть: Чат - СОВРЕМЕННЫЙ ДИЗАЙН
        chat_panel = ModernPanel(main_container, title="💬 Диалог с ЭкоНет")
        chat_panel.pack(fill=tk.BOTH, expand=False, pady=(0, 0))
        
        # Чат контейнер с современным дизайном
        chat_container = tk.Frame(chat_panel, bg=COLORS['bg_panel'])
        chat_container.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)
        
        # Canvas для чата с прокруткой и современным дизайном
        chat_canvas_frame = tk.Frame(chat_container, bg=COLORS['bg_dark'], 
                                     highlightthickness=1, highlightbackground=COLORS['border_light'])
        chat_canvas_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 12))
        
        # Canvas для сообщений
        self.chat_canvas = tk.Canvas(chat_canvas_frame, 
                                     bg=COLORS['bg_dark'],
                                     highlightthickness=0,
                                     borderwidth=0)
        scrollbar = tk.Scrollbar(chat_canvas_frame, 
                                orient="vertical", 
                                command=self.chat_canvas.yview,
                                bg=COLORS['bg_light'],
                                troughcolor=COLORS['bg_dark'],
                                activebackground=COLORS['primary'],
                                width=12)
        
        self.chat_scrollable_frame = tk.Frame(self.chat_canvas, bg=COLORS['bg_dark'])
        self.chat_scrollable_frame.bind(
            "<Configure>",
            lambda e: self.chat_canvas.configure(scrollregion=self.chat_canvas.bbox("all"))
        )
        
        self.chat_canvas.create_window((0, 0), window=self.chat_scrollable_frame, anchor="nw")
        self.chat_canvas.configure(yscrollcommand=scrollbar.set)
        
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.chat_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Привязка прокрутки колесиком мыши
        def _on_mousewheel(event):
            self.chat_canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        self.chat_canvas.bind_all("<MouseWheel>", _on_mousewheel)
        
        # Индикатор печати
        self.typing_indicator_frame = tk.Frame(self.chat_scrollable_frame, bg=COLORS['bg_dark'])
        self.typing_indicator_label = tk.Label(
            self.typing_indicator_frame,
            text="ЭкоНет печатает...",
            bg=COLORS['bg_dark'],
            fg=COLORS['text_muted'],
            font=('Segoe UI', 10, 'italic')
        )
        self.typing_indicator_label.pack(side=tk.LEFT, padx=15, pady=8)
        self.typing_indicator_visible = False
        
        # Поле ввода - современный дизайн
        input_container = tk.Frame(chat_container, bg=COLORS['bg_panel'])
        input_container.pack(fill=tk.X)
        
        # Внутренний фрейм для поля ввода с закругленными углами (имитация)
        input_inner = tk.Frame(input_container, 
                               bg=COLORS['bg_light'],
                               highlightthickness=1,
                               highlightbackground=COLORS['border_light'],
                               highlightcolor=COLORS['primary'])
        input_inner.pack(fill=tk.X, ipady=8)
        
        self.input_entry = tk.Entry(input_inner,
                                   bg=COLORS['bg_light'],
                                   fg=COLORS['text_primary'],
                                   font=('Segoe UI', 11),
                                   insertbackground=COLORS['primary'],
                                   relief='flat',
                                   borderwidth=0,
                                   highlightthickness=0)
        self.input_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=12, pady=8)
        self.input_entry.bind('<Return>', lambda e: self.send_message())
        self.input_entry.bind('<KeyPress>', self.on_input_key)
        
        # Кнопка отправки - современная
        send_btn = ModernButton(input_inner, "➤", self.send_message,
                              width=50, height=36, 
                              bg_color=COLORS['primary'],
                              hover_color=COLORS['primary_light'],
                              rounded=True)
        send_btn.pack(side=tk.RIGHT, padx=(8, 12), pady=6)
    
    def change_mode(self):
        """Изменение режима работы"""
        self.mode = self.mode_var.get()
        mode_names = {
            "detection": "🔍 Детекция",
            "no_detection": "👁️ Просмотр",
            "teaching": "✏️ Обучение"
        }
        self.add_chat_message("system", f"Режим изменен: {mode_names.get(self.mode, self.mode)}")
    
    def load_video(self):
        """Загрузка видеофайла"""
        file_path = filedialog.askopenfilename(
            title="Выберите видеофайл",
            filetypes=[
                ("Видео файлы", "*.mp4 *.avi *.mov *.mkv"),
                ("Все файлы", "*.*")
            ]
        )
        if file_path:
            self.connect_source(file_path)
    
    def connect_ip_webcam(self):
        """Подключение к IP Webcam"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Подключение к IP Webcam")
        dialog.geometry("450x180")
        dialog.configure(bg=COLORS['bg_dark'])
        dialog.transient(self.root)
        dialog.grab_set()
        
        # Центрирование окна
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() // 2) - (dialog.winfo_width() // 2)
        y = (dialog.winfo_screenheight() // 2) - (dialog.winfo_height() // 2)
        dialog.geometry(f"+{x}+{y}")
        
        title = tk.Label(dialog, text="📱 Подключение к IP Webcam",
                        bg=COLORS['bg_dark'], fg=COLORS['primary_light'],
                        font=('Segoe UI', 12, 'bold'))
        title.pack(pady=20)
        
        ip_frame = tk.Frame(dialog, bg=COLORS['bg_dark'])
        ip_frame.pack(pady=10)
        
        tk.Label(ip_frame, text="IP адрес:", bg=COLORS['bg_dark'],
                fg=COLORS['text_primary'], font=('Segoe UI', 10)).pack(side=tk.LEFT, padx=5)
        
        ip_entry = tk.Entry(ip_frame, width=25, bg=COLORS['bg_light'],
                           fg=COLORS['text_primary'], font=('Segoe UI', 10),
                           insertbackground=COLORS['primary'],
                           relief='flat', borderwidth=1,
                           highlightthickness=1,
                           highlightcolor=COLORS['primary'],
                           highlightbackground=COLORS['border'])
        ip_entry.pack(side=tk.LEFT, padx=5)
        ip_entry.insert(0, "192.168.1.")
        ip_entry.focus()
        ip_entry.select_range(0, tk.END)
        
        btn_frame = tk.Frame(dialog, bg=COLORS['bg_dark'])
        btn_frame.pack(pady=20)
        
        def connect():
            ip = ip_entry.get().strip()
            if ip:
                url = f"http://{ip}:8080/video"
                self.connect_source(url)
                dialog.destroy()
        
        ModernButton(btn_frame, "Подключиться", connect,
                    width=120, height=35).pack(side=tk.LEFT, padx=5)
        ModernButton(btn_frame, "Отмена", dialog.destroy,
                    width=100, height=35,
                    bg_color=COLORS['bg_light'],
                    hover_color=COLORS['bg_medium']).pack(side=tk.LEFT, padx=5)
        
        ip_entry.bind('<Return>', lambda e: connect())
    
    def connect_camera(self):
        """Подключение к локальной камере"""
        self.connect_source(0)
    
    def connect_source(self, source):
        """Подключение к источнику видео"""
        self.stop_video()
        
        try:
            if isinstance(source, str) and source.isdigit():
                source = int(source)
            
            self.cap = cv2.VideoCapture(source)
            if not self.cap.isOpened():
                raise Exception(f"Не удалось открыть источник: {source}")
            
            self.current_source = source
            
            if isinstance(source, (int, str)) and (isinstance(source, int) or source.isdigit()):
                info = f"Камера {source}"
            else:
                fps = self.cap.get(cv2.CAP_PROP_FPS)
                frame_count = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))
                info = f"{Path(source).name if isinstance(source, str) else source} | FPS: {fps:.1f} | {frame_count} кадров"
            
            self.video_info_label.config(text=info, fg=COLORS['success'])
            self.add_chat_message("system", f"✅ Подключено: {info}")
            
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось подключиться: {e}")
            logger.error(f"Ошибка подключения: {e}")
    
    def play_video(self):
        """Воспроизведение видео"""
        if not self.cap:
            messagebox.showwarning("Предупреждение", "Сначала выберите источник видео")
            return
        
        self.is_playing = True
        self.add_chat_message("system", "▶️ Воспроизведение начато")
    
    def pause_video(self):
        """Пауза видео"""
        self.is_playing = False
        self.add_chat_message("system", "⏸️ Воспроизведение приостановлено")
    
    def stop_video(self):
        """Остановка видео"""
        self.is_playing = False
        if self.cap:
            self.cap.release()
            self.cap = None
        self.current_source = None
        self.video_label.config(image='', text="Выберите источник видео")
        self.video_info_label.config(text="Источник не выбран", fg=COLORS['text_secondary'])
        self.add_chat_message("system", "⏹️ Воспроизведение остановлено")
    
    def update_video(self):
        """Обновление видеокадра"""
        if self.cap and self.is_playing:
            ret, frame = self.cap.read()
            if not ret:
                self.is_playing = False
                return
            
            if self.mode == "detection" or self.mode == "teaching":
                if self.loop and self.detector:
                    asyncio.run_coroutine_threadsafe(
                        self.process_frame_async(frame),
                        self.loop
                    )
            else:
                self.display_frame(frame)
        
        # УБРАНО: ограничение 33ms (~30 FPS) - обновление без задержки для максимальной скорости
        self.root.after(0, self.update_video)
    
    async def process_frame_async(self, frame):
        """Асинхронная обработка кадра"""
        try:
            detections = await self.detector.detect_frame(
                frame,
                frame_id=f"frame_{int(datetime.now().timestamp())}"
            )
            
            visual_context = await self.vision_context.analyze_frame(frame, detections)
            
            self.current_detections = detections
            self.current_visual_context = visual_context
            
            display_frame = frame.copy()
            for det in detections:
                x, y, w, h = det['bbox']
                conf = det['confidence']
                cv2.rectangle(display_frame, (int(x), int(y)), (int(x+w), int(y+h)), (0, 255, 0), 2)
                label = f"cig_butt {conf:.1%}"
                cv2.putText(display_frame, label, (int(x), int(y)-10),
                          cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
            
            self.root.after(0, lambda: self.update_stats(detections))
            self.root.after(0, lambda: self.display_frame(display_frame))
            
        except Exception as e:
            logger.error(f"Ошибка обработки кадра: {e}")
    
    def display_frame(self, frame):
        """Отображение кадра"""
        try:
            height, width = frame.shape[:2]
            max_width = 900
            max_height = 600
            
            if width > max_width or height > max_height:
                scale = min(max_width / width, max_height / height)
                new_width = int(width * scale)
                new_height = int(height * scale)
                frame = cv2.resize(frame, (new_width, new_height))
            
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            img = Image.fromarray(frame_rgb)
            img_tk = ImageTk.PhotoImage(image=img)
            
            self.video_label.config(image=img_tk, text='')
            self.video_label.image = img_tk
            
        except Exception as e:
            logger.error(f"Ошибка отображения кадра: {e}")
    
    def update_stats(self, detections: List[Dict]):
        """Обновление статистики"""
        count = len(detections)
        if count > 0:
            avg_conf = sum(d.get('confidence', 0) for d in detections) / count
            self.stats_label.config(
                text=f"Детекций: {count}\nУверенность: {avg_conf:.1%}",
                fg=COLORS['success']
            )
        else:
            self.stats_label.config(
                text="Детекций: 0\nУверенность: 0%",
                fg=COLORS['text_secondary']
            )
    
    def on_input_key(self, event):
        """Обработка нажатий клавиш в поле ввода"""
        # Позволяет отправлять Shift+Enter для новой строки
        pass
    
    def send_message(self, message: Optional[str] = None):
        """Отправка сообщения в чат"""
        if message is None:
            message = self.input_entry.get().strip()
            self.input_entry.delete(0, tk.END)
        
        if not message:
            return
        
        # Показываем сообщение пользователя
        self.add_chat_message("user", message)
        
        # Показываем индикатор печати
        self.show_typing_indicator()
        
        # Отправляем на обработку
        if self.loop and self.chat_service:
            asyncio.run_coroutine_threadsafe(
                self.process_message_async(message),
                self.loop
            )
        else:
            # Если сервис не готов, показываем сообщение
            self.hide_typing_indicator()
            self.add_chat_message("error", "Сервис диалога не готов. Подождите инициализации...")
    
    def show_typing_indicator(self):
        """Показать индикатор печати"""
        if not self.typing_indicator_visible:
            self.typing_indicator_frame.pack(fill=tk.X, pady=5)
            self.typing_indicator_visible = True
            self.update_chat_scroll()
    
    def hide_typing_indicator(self):
        """Скрыть индикатор печати"""
        if self.typing_indicator_visible:
            self.typing_indicator_frame.pack_forget()
            self.typing_indicator_visible = False
    
    def update_chat_scroll(self):
        """Обновить прокрутку чата"""
        self.chat_canvas.update_idletasks()
        self.chat_canvas.configure(scrollregion=self.chat_canvas.bbox("all"))
        self.chat_canvas.yview_moveto(1.0)
    
    async def process_message_async(self, message: str):
        """Асинхронная обработка сообщения"""
        try:
            if not self.chat_service:
                error_msg = "Сервис диалога не инициализирован. Попробуйте перезапустить приложение."
                logger.error(error_msg)
                self.root.after(0, lambda: self.hide_typing_indicator())
                self.root.after(0, lambda: self.add_chat_message("error", error_msg))
                return
            
            logger.info(f"Обработка сообщения: {message[:50]}...")
            
            # Получаем ответ
            response = await self.chat_service.process_message(
                message,
                self.current_visual_context
            )
            
            # Скрываем индикатор печати
            self.root.after(0, lambda: self.hide_typing_indicator())
            
            # Гарантируем ответ
            if response and response.strip():
                logger.info(f"Получен ответ: {response[:100]}...")
                self.root.after(0, lambda: self.add_chat_message("assistant", response))
            else:
                logger.warning("Пустой ответ от chat_service, используем fallback")
                # Fallback ответ
                fallback = "Я получил ваше сообщение. Попробуйте переформулировать вопрос или задать другой."
                try:
                    if self.chat_service:
                        fallback = self.chat_service._simple_response(message, self.current_visual_context)
                except:
                    pass
                self.root.after(0, lambda: self.add_chat_message("assistant", fallback))
            
        except Exception as e:
            logger.error(f"Ошибка обработки сообщения: {e}", exc_info=True)
            # Скрываем индикатор
            self.root.after(0, lambda: self.hide_typing_indicator())
            
            # Пытаемся дать fallback ответ
            try:
                if self.chat_service:
                    fallback = self.chat_service._simple_response(message, self.current_visual_context)
                    self.root.after(0, lambda: self.add_chat_message("assistant", fallback))
                else:
                    self.root.after(0, lambda: self.add_chat_message(
                        "error", 
                        f"Ошибка обработки: {str(e)[:100]}"
                    ))
            except Exception as fallback_error:
                logger.error(f"Ошибка fallback: {fallback_error}")
                self.root.after(0, lambda: self.add_chat_message(
                    "assistant",
                    "Извините, произошла ошибка. Попробуйте еще раз."
                ))
    
    def add_chat_message(self, role: str, message: str):
        """Добавление сообщения в чат с современным дизайном как в мессенджерах"""
        # Цвета для разных ролей
        bg_colors = {
            "user": COLORS['primary'],           # Индиго для пользователя
            "assistant": COLORS['bg_light'],      # Темный для ЭкоНет
            "system": COLORS['warning'],         # Янтарный для системы
            "error": COLORS['error']             # Красный для ошибок
        }
        
        text_colors = {
            "user": COLORS['text_primary'],
            "assistant": COLORS['text_primary'],
            "system": COLORS['text_primary'],
            "error": COLORS['text_primary']
        }
        
        # Иконки и имена
        icons = {
            "user": "👤",
            "assistant": "🤖",
            "system": "⚙️",
            "error": "⚠️"
        }
        
        names = {
            "user": "Вы",
            "assistant": "ЭкоНет",
            "system": "Система",
            "error": "Ошибка"
        }
        
        bg_color = bg_colors.get(role, COLORS['bg_light'])
        text_color = text_colors.get(role, COLORS['text_primary'])
        icon = icons.get(role, "•")
        name = names.get(role, "Неизвестно")
        timestamp = datetime.now().strftime("%H:%M")
        
        # Создаем фрейм для сообщения
        msg_frame = tk.Frame(self.chat_scrollable_frame, bg=COLORS['bg_dark'])
        msg_frame.pack(fill=tk.X, padx=12, pady=6)
        
        # Выравнивание: пользователь справа, остальные слева
        if role == "user":
            msg_frame.pack(anchor=tk.E)
            # Контейнер сообщения пользователя
            msg_container = tk.Frame(msg_frame, bg=COLORS['bg_dark'])
            msg_container.pack(anchor=tk.E)
            
            # Внутренний фрейм с закругленными углами (имитация через padding)
            msg_bubble = tk.Frame(msg_container, 
                                 bg=bg_color,
                                 highlightthickness=0)
            msg_bubble.pack(anchor=tk.E, padx=(60, 0))
            
            # Текст сообщения - используем Text для многострочных сообщений
            if '\n' in message or len(message) > 100:
                msg_text = tk.Text(msg_bubble,
                                  bg=bg_color,
                                  fg=text_color,
                                  font=('Segoe UI', 11),
                                  wrap=tk.WORD,
                                  width=40,
                                  height=1,
                                  relief='flat',
                                  borderwidth=0,
                                  padx=16,
                                  pady=12,
                                  highlightthickness=0,
                                  insertbackground=text_color)
                msg_text.insert('1.0', message)
                msg_text.config(state=tk.DISABLED)
                # Автоматически подстраиваем высоту
                msg_text.update_idletasks()
                lines = int(msg_text.index('end-1c').split('.')[0])
                msg_text.config(height=min(lines, 10))
            else:
                msg_text = tk.Label(msg_bubble,
                                  text=message,
                                  bg=bg_color,
                                  fg=text_color,
                                  font=('Segoe UI', 11),
                                  wraplength=500,
                                  justify=tk.LEFT,
                                  anchor='w',
                                  padx=16,
                                  pady=12)
            msg_text.pack()
            
            # Время справа
            time_label = tk.Label(msg_container,
                                text=timestamp,
                                bg=COLORS['bg_dark'],
                                fg=COLORS['text_disabled'],
                                font=('Segoe UI', 9))
            time_label.pack(anchor=tk.E, pady=(4, 0))
        else:
            # Сообщения ЭкоНет и системы слева
            msg_frame.pack(anchor=tk.W)
            msg_container = tk.Frame(msg_frame, bg=COLORS['bg_dark'])
            msg_container.pack(anchor=tk.W)
            
            # Заголовок с иконкой и именем
            header_frame = tk.Frame(msg_container, bg=COLORS['bg_dark'])
            header_frame.pack(anchor=tk.W, pady=(0, 4))
            
            icon_label = tk.Label(header_frame,
                                 text=icon,
                                 bg=COLORS['bg_dark'],
                                 font=('Segoe UI', 12))
            icon_label.pack(side=tk.LEFT, padx=(0, 6))
            
            name_label = tk.Label(header_frame,
                                 text=name,
                                 bg=COLORS['bg_dark'],
                                 fg=COLORS['text_secondary'],
                                 font=('Segoe UI', 10, 'bold'))
            name_label.pack(side=tk.LEFT, padx=(0, 8))
            
            time_label = tk.Label(header_frame,
                                text=timestamp,
                                bg=COLORS['bg_dark'],
                                fg=COLORS['text_disabled'],
                                font=('Segoe UI', 9))
            time_label.pack(side=tk.LEFT)
            
            # Пузырек сообщения
            msg_bubble = tk.Frame(msg_container,
                                 bg=bg_color,
                                 highlightthickness=0)
            msg_bubble.pack(anchor=tk.W, padx=(0, 60))
            
            # Текст сообщения - используем Text для многострочных сообщений
            if '\n' in message or len(message) > 100:
                msg_text = tk.Text(msg_bubble,
                                  bg=bg_color,
                                  fg=text_color,
                                  font=('Segoe UI', 11),
                                  wrap=tk.WORD,
                                  width=40,
                                  height=1,
                                  relief='flat',
                                  borderwidth=0,
                                  padx=16,
                                  pady=12,
                                  highlightthickness=0,
                                  insertbackground=text_color)
                msg_text.insert('1.0', message)
                msg_text.config(state=tk.DISABLED)
                # Автоматически подстраиваем высоту
                msg_text.update_idletasks()
                lines = int(msg_text.index('end-1c').split('.')[0])
                msg_text.config(height=min(lines, 10))
            else:
                msg_text = tk.Label(msg_bubble,
                                  text=message,
                                  bg=bg_color,
                                  fg=text_color,
                                  font=('Segoe UI', 11),
                                  wraplength=500,
                                  justify=tk.LEFT,
                                  anchor='w',
                                  padx=16,
                                  pady=12)
            msg_text.pack()
        
        # Обновляем прокрутку
        self.update_chat_scroll()


def main():
    """Главная функция"""
    root = tk.Tk()
    app = EcoNetGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()

