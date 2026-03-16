"""
Современный Material Design интерфейс ЭкоНет
Чистый, минималистичный дизайн без киберпанка
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
from obelisk.ui.video_display_simple import SimpleVideoDisplay
from obelisk.services.media_manager import MediaManager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Современная Material Design палитра
MATERIAL_THEME = {
    # Основные цвета
    "primary": "#2196F3",  # Синий
    "primary_dark": "#1976D2",
    "primary_light": "#BBDEFB",
    "secondary": "#FF9800",  # Оранжевый
    "accent": "#4CAF50",  # Зеленый
    
    # Фон
    "background": "#FAFAFA",  # Светло-серый
    "surface": "#FFFFFF",  # Белый
    "surface_variant": "#F5F5F5",
    
    # Текст
    "text_primary": "#212121",  # Почти черный
    "text_secondary": "#757575",  # Серый
    "text_hint": "#BDBDBD",
    
    # Статусы
    "success": "#4CAF50",
    "warning": "#FF9800",
    "error": "#F44336",
    "info": "#2196F3",
    
    # Тени и границы
    "border": "#E0E0E0",
    "divider": "#BDBDBD",
    
    # Темная тема (опционально)
    "dark_background": "#121212",
    "dark_surface": "#1E1E1E",
    "dark_text": "#FFFFFF",
}


class MaterialButton(ctk.CTkButton):
    """Кнопка в стиле Material Design"""
    
    def __init__(self, parent, text="", command=None, variant="primary", **kwargs):
        # Определение цветов по варианту
        if variant == "primary":
            default_fg_color = MATERIAL_THEME["primary"]
            default_hover_color = MATERIAL_THEME["primary_dark"]
            default_text_color = "white"
        elif variant == "secondary":
            default_fg_color = MATERIAL_THEME["secondary"]
            default_hover_color = "#F57C00"
            default_text_color = "white"
        elif variant == "success":
            default_fg_color = MATERIAL_THEME["success"]
            default_hover_color = "#388E3C"
            default_text_color = "white"
        elif variant == "outlined":
            default_fg_color = "transparent"
            default_hover_color = MATERIAL_THEME["surface_variant"]
            default_text_color = MATERIAL_THEME["primary"]
            kwargs.setdefault("border_width", 2)
            kwargs.setdefault("border_color", MATERIAL_THEME["primary"])
        else:
            default_fg_color = MATERIAL_THEME["surface"]
            default_hover_color = MATERIAL_THEME["surface_variant"]
            default_text_color = MATERIAL_THEME["text_primary"]
        
        # Использовать значения из kwargs, если они переданы, иначе значения по умолчанию
        # Извлекаем параметры, которые могут быть переданы через kwargs
        fg_color = kwargs.pop("fg_color", default_fg_color)
        hover_color = kwargs.pop("hover_color", default_hover_color)
        text_color = kwargs.pop("text_color", default_text_color)
        font = kwargs.pop("font", ("Segoe UI", 12, "normal"))
        corner_radius = kwargs.pop("corner_radius", 8)
        height = kwargs.pop("height", 40)
        
        # Передаем parent как позиционный аргумент, остальное через kwargs
        super().__init__(
            parent,  # master/parent - обязательный позиционный аргумент
            text=text,
            command=command,
            fg_color=fg_color,
            hover_color=hover_color,
            text_color=text_color,
            font=font,
            corner_radius=corner_radius,
            height=height,
            **kwargs  # Оставшиеся параметры
        )


class MaterialCard(ctk.CTkFrame):
    """Карточка в стиле Material Design"""
    
    def __init__(self, parent, title="", **kwargs):
        super().__init__(
            parent,
            fg_color=MATERIAL_THEME["surface"],
            corner_radius=12,
            border_width=1,
            border_color=MATERIAL_THEME["border"],
            **kwargs
        )
        
        if title:
            title_label = ctk.CTkLabel(
                self,
                text=title,
                font=("Segoe UI", 16, "bold"),
                text_color=MATERIAL_THEME["text_primary"]
            )
            title_label.pack(anchor="w", padx=20, pady=(20, 10))


class MaterialEcoNetGUI:
    """Современный Material Design интерфейс ЭкоНет"""
    
    def __init__(self):
        if not CTK_AVAILABLE:
            raise ImportError("CustomTkinter не установлен. Установите: pip install customtkinter")
        
        # Настройка CustomTkinter
        ctk.set_appearance_mode("light")  # Светлая тема
        ctk.set_default_color_theme("blue")
        
        # Создание окна
        self.root = ctk.CTk()
        self.root.title("ЭкоНет - Система автономной уборки")
        self.root.geometry("1920x1080")
        self.root.configure(fg_color=MATERIAL_THEME["background"])
        
        # Состояние
        self.config = None
        self.unified_engine = None
        self.media_manager: Optional[MediaManager] = None
        self.video_display: Optional[SimpleVideoDisplay] = None
        self.cap = None  # Старый метод для обратной совместимости
        self.is_playing = False
        self.current_detections = []
        self.current_visual_context = None
        self.fps_counter = 0
        self.fps_time = datetime.now()
        self.current_frame = None
        # Фильтр детекции убран - используется только предобработка
        self.current_media_file = None  # Текущий загруженный файл
        self.current_saved_detections = None  # Сохраненные детекции для предобработанного видео
        self.current_frame_number = 0  # Счетчик кадров для сопоставления с детекциями
        
        # Инициализация сервисов
        self.cache_manager = None
        self.model_selector = None
        self.annotation_tool = None
        
        # Переменные для оптимизации отображения
        self._scale_factor = 1.0
        self._scaled_size = None
        self._last_frame_size = None
        self._photo_image = None  # ImageTk.PhotoImage (быстрее CTkImage)
        self._display_busy = False  # frame-dropping: пропускаем кадр если GUI ещё рисует
        
        # Оптимизация производительности GUI
        self.frame_skip_gui = 0
        self._detect_frame_counter = 0
        self._detect_every_n = 1  # YOLO inference на КАЖДОМ кадре (FP16 + cuDNN = достаточно быстро)
        self._inference_running = False  # Guard: не запускать новый inference пока текущий не закончился
        self.last_display_time = datetime.now()
        
        # DeepSeek chat
        self.deepseek_neuron = None
        self.chat_history: List[Dict] = []
        self._chat_sending = False
        self.chat_window = None
        self.chat_display = None
        self.chat_input = None
        self.chat_send_btn = None
        self.chat_status_label = None
        
        # Асинхронный event loop
        self.loop = None
        self.loop_thread = None
        
        # Загрузка конфигурации
        self.load_config()
        
        # Инициализация MediaManager
        try:
            self.media_manager = MediaManager(project_root, media_dir="data/media")
            logger.info("✅ MediaManager инициализирован")
        except Exception as e:
            logger.error(f"Ошибка инициализации MediaManager: {e}", exc_info=True)
            self.media_manager = None
        
        # Настройка UI
        self.setup_ui()
        
        # Инициализация компонентов
        self.init_async_components()
        
        # Загрузка списка файлов (только если MediaManager инициализирован)
        if self.media_manager:
            self.refresh_media_list()
    
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
        """Настройка интерфейса"""
        # Главный контейнер
        main_container = ctk.CTkFrame(self.root, fg_color="transparent")
        main_container.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Верхняя панель - заголовок и кнопки
        header_frame = MaterialCard(main_container, title="ЭкоНет")
        header_frame.pack(fill="x", pady=(0, 20))
        
        # Кнопки управления
        button_frame = ctk.CTkFrame(header_frame, fg_color="transparent")
        button_frame.pack(fill="x", padx=20, pady=(0, 20))
        
        # Загрузка видео убрана - используется импорт с предобработкой
        
        MaterialButton(button_frame, text="🌐 IP камера",
                      command=self.connect_ip_camera,
                      variant="outlined").pack(side="left", padx=5)
        
        MaterialButton(button_frame, text="📷 Камера",
                      command=self.connect_camera,
                      variant="outlined").pack(side="left", padx=5)
        
        MaterialButton(button_frame, text="▶️ Старт",
                      command=self.start_detection,
                      variant="primary").pack(side="left", padx=5)
        
        MaterialButton(button_frame, text="⏸️ Пауза",
                      command=self.pause_detection,
                      variant="secondary").pack(side="left", padx=5)
        
        MaterialButton(button_frame, text="⏹️ Стоп",
                      command=self.stop_detection,
                      variant="error").pack(side="left", padx=5)
        
        MaterialButton(button_frame, text="🧠 DeepSeek",
                      command=self.open_chat_window,
                      variant="outlined").pack(side="right", padx=5)
        
        # Основной контент - две колонки
        content_frame = ctk.CTkFrame(main_container, fg_color="transparent")
        content_frame.pack(fill="both", expand=True)
        
        # Левая колонка - видео
        left_column = MaterialCard(content_frame, title="Видео поток")
        left_column.pack(side="left", fill="both", expand=True, padx=(0, 10))
        
        # Видео область
        video_container = ctk.CTkFrame(left_column, fg_color=MATERIAL_THEME["surface_variant"],
                                      corner_radius=8)
        video_container.pack(fill="both", expand=True, padx=20, pady=(0, 20))
        
        import tkinter as tk
        self.video_label = tk.Label(
            video_container,
            text="Загрузите видео или подключите камеру",
            font=("Segoe UI", 14),
            fg=MATERIAL_THEME["text_secondary"],
            bg=MATERIAL_THEME["surface_variant"],
            anchor="center"
        )
        self.video_label.pack(expand=True, fill="both")
        
        # Правая колонка - медиа список, статус и чат
        right_column = ctk.CTkFrame(content_frame, fg_color="transparent")
        right_column.pack(side="right", fill="y", padx=(10, 0))
        right_column.pack_propagate(False)
        right_column.configure(width=400)
        
        # Панель списка медиа файлов
        media_card = MaterialCard(right_column, title="📁 Медиа файлы")
        media_card.pack(fill="x", pady=(0, 10))
        
        # Кнопки управления медиа
        media_buttons = ctk.CTkFrame(media_card, fg_color="transparent")
        media_buttons.pack(fill="x", padx=20, pady=(0, 10))
        
        MaterialButton(media_buttons, text="🔄 Обновить",
                      command=self.refresh_media_list,
                      variant="outlined").pack(side="left", padx=2)
        
        MaterialButton(media_buttons, text="➕ Импорт",
                      command=self.import_media_file,
                      variant="outlined").pack(side="left", padx=2)
        
        # Список медиа файлов
        media_scroll = ctk.CTkScrollableFrame(
            media_card,
            fg_color=MATERIAL_THEME["surface_variant"],
            height=200,
            label_anchor="w"
        )
        media_scroll.pack(fill="both", expand=True, padx=20, pady=(0, 20))
        # Ограничиваем ширину прокручиваемого фрейма
        media_scroll.configure(width=360)  # Ширина с учетом padding
        self.media_list_container = media_scroll
        self.media_items = {}  # Словарь элементов списка {file_id: frame}
        
        # Панель выбора модели
        model_card = MaterialCard(right_column, title="Выбор модели")
        model_card.pack(fill="x", pady=(0, 10))
        
        model_buttons = ctk.CTkFrame(model_card, fg_color="transparent")
        model_buttons.pack(fill="both", expand=True, padx=20, pady=(0, 10))
        
        # Используем grid layout для равномерного расположения кнопок
        # 2 ряда по 2 кнопки - гарантирует, что все поместятся
        button_width = 140  # Немного уменьшили для лучшего размещения
        button_height = 35
        button_padx = 5
        button_pady = 5
        
        # Первый ряд: 2 кнопки
        btn1 = MaterialButton(model_buttons, text="📦 Выбрать модель",
                      command=self.show_model_selector,
                      variant="outlined",
                      width=button_width,
                      height=button_height)
        btn1.grid(row=0, column=0, padx=button_padx, pady=button_pady, sticky="ew")
        
        btn2 = MaterialButton(model_buttons, text="🧹 Очистить кэш",
                      command=self.clear_cache,
                      variant="outlined",
                      width=button_width,
                      height=button_height)
        btn2.grid(row=0, column=1, padx=button_padx, pady=button_pady, sticky="ew")
        
        # Второй ряд: 2 кнопки
        btn3 = MaterialButton(model_buttons, text="🎨 Разметка",
                      command=self.show_annotation_tool,
                      variant="outlined",
                      width=button_width,
                      height=button_height)
        btn3.grid(row=1, column=0, padx=button_padx, pady=button_pady, sticky="ew")
        
        btn4 = MaterialButton(model_buttons, text="🏷️ Добавить метку",
                      command=self.add_label_from_frame,
                      variant="outlined",
                      width=button_width,
                      height=button_height)
        btn4.grid(row=1, column=1, padx=button_padx, pady=button_pady, sticky="ew")
        
        # Настройка весов колонок для равномерного распределения
        model_buttons.grid_columnconfigure(0, weight=1)
        model_buttons.grid_columnconfigure(1, weight=1)
        
        # Статус панель со скроллом
        status_card = MaterialCard(right_column, title="Статус системы")
        status_card.pack(fill="both", expand=True, pady=(0, 10))
        
        status_scroll = ctk.CTkScrollableFrame(
            status_card,
            fg_color="transparent",
            height=180
        )
        status_scroll.pack(fill="both", expand=True, padx=12, pady=(0, 12))
        
        self.status_labels = {}
        status_items = [
            ("Модель", "Инициализация...", "info"),
            ("Видео", "Не подключено", "warning"),
            ("FPS", "0", "info"),
            ("Детекций", "0", "info"),
            ("Обработано", "0 видео", "info"),
            ("Кадров", "0 кадров", "info"),
            ("GPU", "—", "info"),
            ("GPU Память", "—", "info"),
            ("Время инф.", "— ms", "info"),
            ("Нейроны", "—", "info"),
            ("MQTT", "—", "info"),
            ("Swarm", "—", "info"),
            ("Veins", "—", "info"),
        ]
        
        for key, value, status_type in status_items:
            row = ctk.CTkFrame(status_scroll, fg_color=MATERIAL_THEME["surface_variant"],
                               corner_radius=5, height=30)
            row.pack(fill="x", padx=2, pady=1)
            row.pack_propagate(False)
            
            rc = ctk.CTkFrame(row, fg_color="transparent")
            rc.pack(fill="both", expand=True, padx=8, pady=4)
            
            ctk.CTkLabel(rc, text=key + ":", font=("Segoe UI", 9),
                         text_color=MATERIAL_THEME["text_secondary"],
                         anchor="w", width=90).pack(side="left", padx=(0, 6))
            
            max_length = 30
            vl = ctk.CTkLabel(rc, text=value, font=("Segoe UI", 10, "bold"),
                              text_color=MATERIAL_THEME.get(status_type, MATERIAL_THEME["text_primary"]),
                              anchor="w", width=180)
            vl.pack(side="left", fill="x", expand=True)
            
            self.status_labels[key] = {"label": vl, "max_length": max_length, "full_value": value}
        
    def init_async_components(self):
        """Инициализация асинхронных компонентов"""
        def init_loop():
            self.loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self.loop)
            # Инициализация компонентов
            self.loop.run_until_complete(self._async_init())
            # ВАЖНО: Запускаем loop постоянно для обработки корутин
            logger.info("🔄 Event loop запущен для обработки корутин")
            self.loop.run_forever()
        
        self.loop_thread = threading.Thread(target=init_loop, daemon=True)
        self.loop_thread.start()
    
    async def _async_init(self):
        """Асинхронная инициализация с проверкой модели и автоматической обработкой видео"""
        try:
            # Инициализация сервисов
            from obelisk.services.cache_manager import CacheManager
            from obelisk.services.model_selector import ModelSelector
            from obelisk.services.annotation_tool import AnnotationTool
            self.cache_manager = CacheManager(self.config, project_root)
            self.model_selector = ModelSelector(self.config, project_root)
            self.annotation_tool = AnnotationTool(self.config, project_root)
            
            # Инициализация UnifiedEngine
            self.unified_engine = UnifiedEngine(self.config, project_root)
            await self.unified_engine.initialize()
            
            logger.info("✅ UnifiedEngine инициализирован")
            
            # ПРОВЕРКА МОДЕЛИ ПРИ ЗАПУСКЕ (простая система с GPU венами)
            from obelisk.core.model_testing import ModelTester
            
            # Получаем GPU венозную систему из unified_engine если доступна
            gpu_circulatory = None
            if hasattr(self.unified_engine, 'gpu_circulatory'):
                gpu_circulatory = self.unified_engine.gpu_circulatory
            
            model_tester = ModelTester(self.unified_engine, gpu_circulatory=gpu_circulatory)
            
            # Простая проверка модели с GPU венами
            model_info_dict = model_tester.get_model_info()
            test_result = await model_tester.test_single_frame(use_gpu=True)
            
            if model_info_dict["loaded"] and test_result["success"]:
                model_name = model_info_dict["names"][0] if model_info_dict["names"] else "model"
                device_info = model_info_dict["device"]
                status_text = f"{model_name} ({model_info_dict['count']} модель) [{device_info}]"
                
                logger.info(f"✅ Модель проверена: {model_info_dict['count']} модель(ей), устройство: {device_info}, детекций: {test_result['detections']}")
                self.root.after(0, lambda text=status_text: self.update_status("Модель", text, "success"))
                
                await self._auto_process_videos()
            else:
                error_msg = test_result.get("error", "Модель не загружена")
                logger.warning(f"⚠️ Модель не проверена: {error_msg}")
                self.root.after(0, lambda text="Не загружена": self.update_status("Модель", text, "error"))
            
            # Инициализация DeepSeek нейрона для чата
            if (self.unified_engine and 
                hasattr(self.unified_engine, 'neural_architecture') and
                self.unified_engine.neural_architecture):
                self.deepseek_neuron = self.unified_engine.neural_architecture.deepseek_neuron
                if self.deepseek_neuron and self.deepseek_neuron.available:
                    logger.info("✅ DeepSeek-нейрон подключён к чату")
                    self.root.after(0, lambda: self._update_chat_status("READY"))
                else:
                    logger.info("DeepSeek-нейрон недоступен (LLM не подключён)")
                    self.root.after(0, lambda: self._update_chat_status("PAUSED"))
            
            # Запуск периодического обновления статуса системы
            self.root.after(1000, self._periodic_system_status)
        
        except Exception as e:
            logger.error(f"Ошибка инициализации: {e}", exc_info=True)
            self.root.after(0, lambda: self.update_status("Модель", f"Ошибка: {str(e)[:30]}", "error"))
    
    def _periodic_system_status(self):
        """Периодическое обновление расширенного статуса (каждые 2 сек)"""
        try:
            import torch
            if torch.cuda.is_available():
                dev = torch.cuda.get_device_properties(0)
                name = dev.name.replace("NVIDIA ", "").replace("GeForce ", "")
                alloc = torch.cuda.memory_allocated(0) / 1024**3
                total = dev.total_memory / 1024**3
                fp16 = "FP16" if (self.unified_engine and 
                    hasattr(self.unified_engine, 'model_engine') and 
                    self.unified_engine.model_engine and 
                    getattr(self.unified_engine.model_engine, 'half_precision', False)) else "FP32"
                cudnn = "cuDNN" if torch.backends.cudnn.benchmark else ""
                mode = f"{fp16} {cudnn}".strip()
                self.update_status("GPU", f"{name} [{mode}]", "success")
                self.update_status("GPU Память", f"{alloc:.1f} / {total:.1f} GB", "info")
            
            if self.unified_engine:
                if hasattr(self.unified_engine, 'neural_architecture') and self.unified_engine.neural_architecture:
                    na = self.unified_engine.neural_architecture
                    nodes = []
                    if na.yolo_neuron:
                        nodes.append("YOLO")
                    if na.deepseek_neuron and na.deepseek_neuron.available:
                        nodes.append("DeepSeek")
                    if na.coordinator_neuron:
                        nodes.append("Coord")
                    if na.hub_neuron:
                        nodes.append("Hub")
                    self.update_status("Нейроны", f"{len(nodes)}: {', '.join(nodes)}", "success")
                
                mqtt = getattr(self.unified_engine, 'mqtt_client', None)
                if mqtt and hasattr(mqtt, 'connected') and mqtt.connected:
                    self.update_status("MQTT", "Подключён", "success")
                else:
                    self.update_status("MQTT", "Отключён", "warning")
                
                sk = getattr(self.unified_engine, 'swarm_kernel', None)
                if sk:
                    n_nodes = len(sk.field.nodes) if hasattr(sk, 'field') else 0
                    self.update_status("Swarm", f"{n_nodes} узлов", "success")
                
                stats = getattr(self.unified_engine, '_stats', None)
                if stats and 'avg_detection_time' in stats:
                    ms = stats['avg_detection_time'] * 1000
                    color = "success" if ms < 20 else ("warning" if ms < 50 else "error")
                    self.update_status("Время инф.", f"{ms:.1f} ms", color)
                
                # Veins (GPU кровообращение)
                circ = getattr(self.unified_engine, 'gpu_circulatory', None)
                if circ:
                    v_stats = circ.get_statistics()
                    active = v_stats.get('active_tasks', 0)
                    self.update_status("Veins", f"OK ({active} задач)", "success")
        except Exception as e:
            logger.debug(f"Status update error: {e}")
        
        if hasattr(self, 'root') and self.root and self.root.winfo_exists():
            self.root.after(2000, self._periodic_system_status)
    
    def update_status(self, key: str, value: str, status_type: str = "info"):
        """Обновление статуса с форматированием чисел и обрезкой длинного текста"""
        try:
            if key in self.status_labels:
                color = MATERIAL_THEME.get(status_type, MATERIAL_THEME["text_primary"])
                
                # Форматируем значение: числа с разделителями тысяч, текст обрезаем
                formatted_value = value
                try:
                    # Пытаемся преобразовать в число и отформатировать
                    num_value = int(value)
                    formatted_value = f"{num_value:,}".replace(",", " ")  # Разделитель тысяч
                except (ValueError, TypeError):
                    # Если не число, обрезаем если слишком длинное
                    max_length = 25
                    if len(value) > max_length:
                        formatted_value = value[:max_length-3] + "..."
                
                # Если status_labels[key] - это словарь (новая структура с ограничениями)
                if isinstance(self.status_labels[key], dict):
                    label = self.status_labels[key]["label"]
                    
                    # Сохраняем полное значение
                    self.status_labels[key]["full_value"] = value
                    
                    # Обновляем отображаемое значение
                    label.configure(text=formatted_value, text_color=color)
                else:
                    # Старая структура (для обратной совместимости)
                    self.status_labels[key].configure(text=formatted_value, text_color=color)
        except Exception as e:
            logger.error(f"Ошибка обновления статуса {key}: {e}", exc_info=True)
    
    # ─── DeepSeek Chat (отдельное окно) ─────────────────────────────

    def open_chat_window(self):
        """Открытие окна чата DeepSeek"""
        if self.chat_window is not None and self.chat_window.winfo_exists():
            self.chat_window.focus()
            return
        
        win = ctk.CTkToplevel(self.root)
        win.title("🧠 DeepSeek — ЭкоНет")
        win.geometry("520x640")
        win.configure(fg_color=MATERIAL_THEME["background"])
        win.resizable(True, True)
        win.minsize(400, 400)
        self.chat_window = win
        
        win.protocol("WM_DELETE_WINDOW", self._on_chat_window_close)
        
        # Контейнер
        container = ctk.CTkFrame(win, fg_color="transparent")
        container.pack(fill="both", expand=True, padx=16, pady=16)
        
        # Заголовок + статус
        header = ctk.CTkFrame(container, fg_color="transparent")
        header.pack(fill="x", pady=(0, 8))
        
        ctk.CTkLabel(
            header, text="DeepSeek нейрон",
            font=("Segoe UI", 18, "bold"),
            text_color=MATERIAL_THEME["text_primary"]
        ).pack(side="left")
        
        self.chat_status_label = ctk.CTkLabel(
            header,
            text="PAUSED",
            font=("Segoe UI", 11),
            text_color=MATERIAL_THEME["text_hint"],
            anchor="e"
        )
        self.chat_status_label.pack(side="right")
        
        if self.deepseek_neuron and self.deepseek_neuron.available:
            self._update_chat_status("READY")
        
        # Область сообщений
        self.chat_display = ctk.CTkTextbox(
            container,
            font=("Segoe UI", 12),
            fg_color=MATERIAL_THEME["surface"],
            text_color=MATERIAL_THEME["text_primary"],
            corner_radius=10,
            border_width=1,
            border_color=MATERIAL_THEME["border"],
            wrap="word",
            state="disabled"
        )
        self.chat_display.pack(fill="both", expand=True, pady=(0, 10))
        
        # Восстановление истории
        for msg in self.chat_history:
            self._append_chat(msg["role"], msg["content"])
        
        # Поле ввода + кнопка
        input_frame = ctk.CTkFrame(container, fg_color="transparent")
        input_frame.pack(fill="x")
        
        self.chat_input = ctk.CTkEntry(
            input_frame,
            placeholder_text="Введите сообщение...",
            font=("Segoe UI", 12),
            fg_color=MATERIAL_THEME["surface"],
            text_color=MATERIAL_THEME["text_primary"],
            border_color=MATERIAL_THEME["primary"],
            corner_radius=10,
            height=40
        )
        self.chat_input.pack(side="left", fill="x", expand=True, padx=(0, 8))
        self.chat_input.bind("<Return>", lambda e: self.send_chat_message())
        
        self.chat_send_btn = MaterialButton(
            input_frame,
            text="➤",
            command=self.send_chat_message,
            variant="primary",
            width=50,
            height=40,
            font=("Segoe UI", 16)
        )
        self.chat_send_btn.pack(side="right")
        
        self.chat_input.focus()

    def _on_chat_window_close(self):
        """Закрытие окна чата без потери данных"""
        if self.chat_window:
            self.chat_window.destroy()
        self.chat_window = None
        self.chat_display = None
        self.chat_input = None
        self.chat_send_btn = None
        self.chat_status_label = None

    def _update_chat_status(self, status: str):
        """Обновление индикатора статуса чата"""
        status_map = {
            "READY": ("READY", MATERIAL_THEME["success"]),
            "PAUSED": ("PAUSED", MATERIAL_THEME["text_hint"]),
            "THINKING": ("Думаю...", MATERIAL_THEME["info"]),
            "ERROR": ("Ошибка", MATERIAL_THEME["error"]),
        }
        text, color = status_map.get(status, (status, MATERIAL_THEME["text_hint"]))
        if self.chat_status_label and self.chat_window and self.chat_window.winfo_exists():
            self.chat_status_label.configure(text=text, text_color=color)

    def _append_chat(self, role: str, text: str):
        """Добавление сообщения в окно чата"""
        if not self.chat_display:
            return
        try:
            self.chat_display.configure(state="normal")
            if role == "user":
                self.chat_display.insert("end", f"\n🧑 Вы:\n{text}\n")
            elif role == "assistant":
                self.chat_display.insert("end", f"\n🤖 DeepSeek:\n{text}\n")
            elif role == "system":
                self.chat_display.insert("end", f"\n⚙️ {text}\n")
            self.chat_display.configure(state="disabled")
            self.chat_display.see("end")
        except Exception:
            pass

    def send_chat_message(self):
        """Отправка сообщения в DeepSeek нейрон"""
        if self._chat_sending:
            return
        if not self.chat_input:
            return
        
        text = self.chat_input.get().strip()
        if not text:
            return
        
        self.chat_input.delete(0, "end")
        self._append_chat("user", text)
        self.chat_history.append({"role": "user", "content": text})
        
        if not self.deepseek_neuron or not self.deepseek_neuron.available:
            self._append_chat("system", "DeepSeek-нейрон не подключён. Запустите Ollama и перезапустите приложение.")
            return
        
        self._chat_sending = True
        self._update_chat_status("THINKING")
        if self.chat_send_btn:
            self.chat_send_btn.configure(state="disabled")
        
        async def _do_request():
            try:
                return await self.deepseek_neuron.process_message(text)
            except Exception as exc:
                logger.error(f"DeepSeek chat error: {exc}", exc_info=True)
                return f"Ошибка: {exc}"
        
        future = asyncio.run_coroutine_threadsafe(_do_request(), self.loop)
        
        def _poll_result():
            if not future.done():
                self.root.after(100, _poll_result)
                return
            try:
                response = future.result()
                self._append_chat("assistant", response)
                self.chat_history.append({"role": "assistant", "content": response})
                self._update_chat_status("READY")
            except Exception as exc:
                self._append_chat("system", f"Ошибка: {exc}")
                self._update_chat_status("ERROR")
            finally:
                self._chat_sending = False
                if self.chat_send_btn:
                    self.chat_send_btn.configure(state="normal")
        
        self.root.after(100, _poll_result)

    # ─── End Chat ─────────────────────────────────────────────────────

    def import_media_file(self):
        """Импорт медиа файла (копирование в проект)"""
        from tkinter import filedialog
        file_path = filedialog.askopenfilename(
            title="Выберите видео или фото файл",
            filetypes=[
                ("Video files", "*.mp4 *.avi *.mov *.mkv *.wmv *.flv *.webm"),
                ("Image files", "*.jpg *.jpeg *.png *.bmp *.tiff *.webp"),
                ("All files", "*.*")
            ]
        )
        if not file_path:
            return
        
        try:
            if not self.media_manager:
                logger.error("MediaManager не инициализирован")
                self.update_status("Видео", "Ошибка: MediaManager не доступен", "error")
                return
            
            # Определение типа файла по расширению
            ext = Path(file_path).suffix.lower()
            video_exts = {'.mp4', '.avi', '.mov', '.mkv', '.wmv', '.flv', '.webm'}
            file_type = "video" if ext in video_exts else "photo"
            
            # Импорт файла через MediaManager
            logger.info(f"📁 Импорт {file_type}: {file_path}")
            file_meta = self.media_manager.import_file(file_path, file_type)
            
            if file_meta:
                logger.info(f"✅ Файл импортирован: {file_meta['name']}")
                self.update_status("Видео", f"Импортировано: {file_meta['name']}", "success")
                
                # ВАЖНО: Если это видео, запускаем предобработку YOLO
                if file_type == "video":
                    self.update_status("Видео", f"Обработка: {file_meta['name']}...", "info")
                    # Запускаем предобработку в фоне
                    if hasattr(self, 'loop') and self.loop and not self.loop.is_closed():
                        asyncio.run_coroutine_threadsafe(
                            self._preprocess_video(file_meta["id"]),
                            self.loop
                        )
                
                # Обновление списка медиа
                self.refresh_media_list()
            else:
                logger.error(f"Не удалось импортировать файл: {file_path}")
                self.update_status("Видео", "Ошибка импорта", "error")
                
        except Exception as e:
            logger.error(f"Ошибка импорта файла: {e}", exc_info=True)
            self.update_status("Видео", f"Ошибка: {str(e)[:30]}", "error")
    
    def load_video(self):
        """Загрузка видео из файла - УБРАНО (используется импорт с предобработкой)"""
        # Функция удалена - используйте импорт видео
        self.import_media_file()
    
    def load_media_file(self, file_id: str):
        """Загрузка медиа файла из списка в плеер"""
        try:
            if not self.media_manager:
                logger.error("MediaManager не инициализирован")
                return
            
            # Получение метаданных файла
            file_meta = self.media_manager.get_file(file_id)
            if not file_meta:
                logger.error(f"Файл не найден: {file_id}")
                return
            
            if file_meta["file_type"] != "video":
                logger.warning(f"Файл не является видео: {file_id}")
                self.update_status("Видео", "Выберите видео файл", "warning")
                return
            
            # ВАЖНО: Проверка что видео обработано перед воспроизведением
            if not file_meta.get("processed", False):
                status = file_meta.get("processing_status", "pending")
                if status == "processing":
                    self.update_status("Видео", f"Обработка: {file_meta['name']}...", "info")
                    logger.info(f"⏳ Видео {file_id} обрабатывается, ожидаем завершения")
                    return
                else:
                    self.update_status("Видео", f"Видео не обработано: {file_meta['name']}", "warning")
                    logger.warning(f"⚠️ Видео {file_id} еще не обработано (статус: {status}). Воспроизведение недоступно.")
                    return
            
            file_path = file_meta["full_path"]
            
            # Загрузка сохраненных детекций
            saved_detections = self.media_manager.load_detections(file_id)
            if not saved_detections:
                logger.warning(f"Детекции не найдены для видео: {file_id}")
                self.update_status("Видео", f"Детекции не найдены: {file_meta['name']}", "warning")
                saved_detections = {}
            
            # Создание видеоплеера с проверкой
            if not self.video_display:
                try:
                    self.video_display = SimpleVideoDisplay(frame_callback=self._on_video_frame)
                    logger.info("✅ SimpleVideoDisplay создан")
                except Exception as e:
                    logger.error(f"Ошибка создания видеоплеера: {e}", exc_info=True)
                    self.update_status("Видео", "Ошибка создания плеера", "error")
                    return
            
            # Загрузка видео в плеер
            if self.video_display.load_video(file_path):
                # Сохранение текущего файла и детекций
                self.current_media_file = file_meta
                self.current_saved_detections = saved_detections
                self.current_frame_number = 0  # Счетчик кадров для сопоставления
                
                # Обновление UI и статистики обработки видео
                detections_count = len(saved_detections) if saved_detections else 0
                total_detections = sum(len(dets) for dets in saved_detections.values()) if saved_detections else 0
                
                self.update_status("Видео", f"Готово: {file_meta['name']}", "success")
                self.update_status("Кадров", f"{detections_count} кадров", "info")
                self.update_status("Детекций", f"{total_detections}", "info")
                
                logger.info(f"✅ Видео загружено: {file_meta['name']} с {detections_count} кадрами ({total_detections} детекций)")
            else:
                logger.error(f"Не удалось загрузить видео: {file_path}")
                self.update_status("Видео", "Ошибка загрузки", "error")
                
        except Exception as e:
            logger.error(f"Ошибка загрузки медиа файла: {e}", exc_info=True)
            self.update_status("Видео", f"Ошибка: {str(e)[:30]}", "error")
    
    def connect_ip_camera(self):
        """Подключение IP камеры через диалоговое окно"""
        dialog = ctk.CTkToplevel(self.root)
        dialog.title("IP камера")
        dialog.geometry("500x220")
        dialog.resizable(False, False)
        dialog.configure(fg_color=MATERIAL_THEME["background"])
        dialog.transient(self.root)
        dialog.grab_set()
        
        # Центрирование
        dialog.update_idletasks()
        x = self.root.winfo_x() + (self.root.winfo_width() - 500) // 2
        y = self.root.winfo_y() + (self.root.winfo_height() - 220) // 2
        dialog.geometry(f"+{x}+{y}")
        
        ctk.CTkLabel(
            dialog, text="Введите адрес IP камеры",
            font=("Segoe UI", 18, "bold"),
            text_color=MATERIAL_THEME["text_primary"]
        ).pack(padx=30, pady=(25, 5))
        
        ctk.CTkLabel(
            dialog, text="Например: 192.168.0.100:8080",
            font=("Segoe UI", 13),
            text_color=MATERIAL_THEME["text_secondary"]
        ).pack(padx=30, pady=(0, 10))
        
        ip_entry = ctk.CTkEntry(
            dialog,
            placeholder_text="192.168.0.100:8080",
            font=("Segoe UI", 16),
            fg_color=MATERIAL_THEME["surface"],
            text_color=MATERIAL_THEME["text_primary"],
            border_color=MATERIAL_THEME["primary"],
            corner_radius=10,
            height=46,
            width=420,
            justify="center"
        )
        ip_entry.pack(padx=30, pady=(0, 15))
        ip_entry.focus()
        
        btn_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        btn_frame.pack(fill="x", padx=30, pady=(0, 20))
        
        def on_connect():
            ip = ip_entry.get().strip()
            if not ip:
                return
            dialog.destroy()
            self._do_connect_ip(ip)
        
        ip_entry.bind("<Return>", lambda e: on_connect())
        
        MaterialButton(btn_frame, text="Подключить", command=on_connect,
                       variant="primary", width=200, height=42,
                       font=("Segoe UI", 14)).pack(side="right", padx=(5, 0))
        MaterialButton(btn_frame, text="Отмена", command=dialog.destroy,
                       variant="outlined", width=120, height=42,
                       font=("Segoe UI", 14)).pack(side="right")

    def _do_connect_ip(self, ip: str):
        """Выполнение подключения к IP камере"""
        try:
            if not self.root:
                return
            
            if not self.video_display:
                try:
                    self.video_display = SimpleVideoDisplay(frame_callback=self._on_video_frame)
                except Exception as e:
                    logger.error(f"Ошибка создания видеоплеера: {e}", exc_info=True)
                    self.update_status("Видео", "Ошибка создания плеера", "error")
                    return
            
            url = f"http://{ip}/video"
            if self.video_display.load_video(url):
                if hasattr(self, 'current_saved_detections'):
                    self.current_saved_detections = None
                if hasattr(self, 'current_media_file'):
                    self.current_media_file = None
                
                self.update_status("Видео", f"IP: {ip}", "success")
                logger.info(f"✅ IP камера подключена: {url}")
            else:
                logger.error(f"Не удалось подключиться к IP камере: {url}")
                self.update_status("Видео", "Ошибка подключения", "error")
        except Exception as e:
            logger.error(f"Критическая ошибка подключения IP камеры: {e}", exc_info=True)
            self.update_status("Видео", f"Ошибка: {str(e)[:30]}", "error")
    
    def connect_camera(self):
        """Подключение локальной камеры"""
        try:
            # Проверка готовности системы
            if not self.root:
                logger.error("GUI не инициализирован")
                return
            
            # Создание видеоплеера с проверкой
            if not self.video_display:
                try:
                    self.video_display = SimpleVideoDisplay(frame_callback=self._on_video_frame)
                    logger.info("✅ SimpleVideoDisplay создан")
                except Exception as e:
                    logger.error(f"Ошибка создания видеоплеера: {e}", exc_info=True)
                    self.update_status("Видео", "Ошибка создания плеера", "error")
                    return
            
            if self.video_display.load_video(0):  # 0 для локальной камеры
                # Очищаем предобработанные детекции (для камеры не нужны)
                self.current_saved_detections = None
                self.current_media_file = None
                
                self.update_status("Видео", "Локальная камера", "success")
                if hasattr(self, 'video_info_label'):
                    self.video_info_label.configure(text="Локальная камера")
                
                # НЕ запускаем автоматически
                logger.info("✅ Локальная камера подключена (ожидание ручного запуска, обработка в реальном времени)")
            else:
                logger.error("Не удалось открыть локальную камеру")
                self.update_status("Видео", "Ошибка подключения", "error")
        except Exception as e:
            logger.error(f"Критическая ошибка подключения камеры: {e}", exc_info=True)
            self.update_status("Видео", f"Ошибка: {str(e)[:30]}", "error")
    
    def start_detection(self):
        """Запуск детекции"""
        try:
            if not self.video_display:
                logger.warning("Видеоплеер не создан")
                # Статус Детектор удален
                return
            
            if not hasattr(self.video_display, 'cap') or not self.video_display.cap:
                logger.warning("Видео не загружено")
                # Статус Детектор удален
                return
            
            if not self.video_display.cap.isOpened():
                logger.warning("Видео не открыто")
                # Статус Детектор удален
                return
            
            if self.video_display.start():
                self.is_playing = True
                # Статус Детектор удален
                logger.info("✅ Детекция запущена")
            else:
                logger.error("Не удалось запустить детекцию")
                # Статус Детектор удален
        except Exception as e:
            logger.error(f"Ошибка запуска детекции: {e}", exc_info=True)
            # Статус Детектор удален
    
    def pause_detection(self):
        """Пауза детекции"""
        try:
            if not self.video_display:
                logger.warning("Видеоплеер не создан")
                return
            
            if hasattr(self.video_display, 'is_paused') and self.video_display.is_paused:
                # Возобновление
                self.video_display.resume()
                self.is_playing = True
                # Статус Детектор удален
                logger.info("✅ Детекция возобновлена")
            else:
                # Пауза
                self.video_display.pause()
                self.is_playing = False
                # Статус Детектор удален
                logger.info("⏸️ Детекция на паузе")
        except Exception as e:
            logger.error(f"Ошибка паузы детекции: {e}", exc_info=True)
            # Статус Детектор удален
    
    def stop_detection(self):
        """Остановка детекции"""
        try:
            if self.video_display:
                self.video_display.stop()
            self.is_playing = False
            
            # Очистка старого cap для обратной совместимости
            if self.cap:
                try:
                    self.cap.release()
                except Exception:
                    pass
                self.cap = None
            
            self.update_status("Видео", "Не подключено", "warning")
            # Статус Детектор удален
            
            if hasattr(self, 'video_info_label'):
                self.video_info_label.configure(text="Нет видео")
            
            logger.info("⏹️ Детекция остановлена")
        except Exception as e:
            logger.error(f"Ошибка остановки детекции: {e}", exc_info=True)
            # Статус Детектор удален
    
    def _on_video_frame(self, frame):
        """
        Упрощенный callback для обработки кадра (вызывается из фонового потока)
        
        Args:
            frame: Кадр видео (numpy array)
        """
        try:
            if not hasattr(self, 'root') or not self.root:
                return
            if not self.root.winfo_exists():
                return
            if frame is None or not hasattr(frame, 'shape'):
                return
            
            # Frame-dropping: пропускаем если GUI ещё рисует предыдущий кадр
            if self._display_busy:
                return
            
            try:
                frame_copy = frame.copy()
                if frame_copy.size == 0:
                    return
            except Exception as e:
                logger.debug(f"Ошибка копирования кадра: {e}")
                return
            
            # Сохранение текущего кадра
            self.current_frame = frame_copy
            
            # ВАЖНО: Определяем тип источника - предобработанное видео или камера
            is_preprocessed_video = (hasattr(self, 'current_saved_detections') and 
                                    self.current_saved_detections and
                                    hasattr(self, 'current_media_file') and 
                                    self.current_media_file)
            
            if is_preprocessed_video:
                # ПРЕДОБРАБОТАННОЕ ВИДЕО: Используем сохраненные детекции
                # Синхронизируем счетчик с SimpleVideoDisplay
                if hasattr(self, 'video_display') and self.video_display:
                    frame_number = self.video_display.current_frame_number
                else:
                    if hasattr(self, 'current_frame_number'):
                        self.current_frame_number += 1
                        frame_number = self.current_frame_number
                    else:
                        self.current_frame_number = 1
                        frame_number = 1
                
                # Получение детекций для текущего кадра
                frame_detections = self.current_saved_detections.get(frame_number, [])
                
                # Рисуем детекции на кадре
                if frame_detections:
                    frame_with_detections = frame_copy.copy()
                    for det in frame_detections:
                        try:
                            if 'bbox' in det:
                                bbox = det['bbox']
                                if len(bbox) == 4:
                                    # ИСПРАВЛЕНИЕ: bbox формат [x, y, w, h] из model_engine
                                    x, y, w, h = bbox
                                    x1, y1 = int(x), int(y)
                                    x2, y2 = int(x + w), int(y + h)
                                    
                                    # Проверка границ кадра
                                    frame_h, frame_w = frame_with_detections.shape[:2]
                                    # Ограничиваем координаты границами кадра
                                    x1 = max(0, min(x1, frame_w - 1))
                                    y1 = max(0, min(y1, frame_h - 1))
                                    x2 = max(x1 + 1, min(x2, frame_w))
                                    y2 = max(y1 + 1, min(y2, frame_h))
                                    
                                    if x2 > x1 and y2 > y1:
                                        # Рисуем прямоугольник
                                        cv2.rectangle(frame_with_detections, (x1, y1), (x2, y2), (76, 175, 80), 2)
                                        
                                        # Текст
                                        conf = det.get('confidence', 0.0)
                                        label = f"{conf:.0%}"
                                        (text_width, text_height), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)
                                        if y1 > text_height + 5:
                                            text_y = y1 - 5
                                            cv2.rectangle(frame_with_detections, (x1, text_y - text_height - 5), 
                                                        (x1 + text_width + 10, text_y + 5), (76, 175, 80), -1)
                                            cv2.putText(frame_with_detections, label, (x1 + 5, text_y),
                                                      cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
                        except Exception as e:
                            logger.debug(f"Ошибка отрисовки детекции: {e}")
                            continue
                    
                    # Обновляем отображение с детекциями
                    self.root.after(0, lambda f=frame_with_detections.copy(): self.display_frame(f))
                    
                    # Обновление статуса
                    count = len(frame_detections)
                    self.root.after(0, lambda cnt=count: self.update_status("Детекций", str(cnt), "info"))
                else:
                    # Нет детекций для этого кадра
                    self.root.after(0, lambda f=frame_copy.copy(): self.display_frame(f))
            else:
                # КАМЕРА: рисуем последние известные детекции на КАЖДОМ кадре (без мигания)
                display = frame_copy
                if hasattr(self, 'current_detections') and self.current_detections:
                    display = frame_copy.copy()
                    for det in self.current_detections:
                        try:
                            bbox = det.get('bbox')
                            if bbox and len(bbox) == 4:
                                x, y, w, h = bbox
                                x1, y1, x2, y2 = int(x), int(y), int(x + w), int(y + h)
                                fh, fw = display.shape[:2]
                                if 0 <= x1 < fw and 0 <= y1 < fh and x2 > x1 and y2 > y1:
                                    cv2.rectangle(display, (x1, y1), (x2, y2), (76, 175, 80), 3)
                                    conf = det.get('confidence', 0.0)
                                    label = f"{conf:.0%}"
                                    (tw, th), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)
                                    ty = max(y1 - 5, th + 5)
                                    cv2.rectangle(display, (x1, ty - th - 5), (x1 + tw + 10, ty + 5), (76, 175, 80), -1)
                                    cv2.putText(display, label, (x1 + 5, ty), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
                        except Exception:
                            continue
                
                self.root.after(0, lambda f=display: self.display_frame(f))
                
                # YOLO inference — каждый N-й кадр, но НЕ запускаем если предыдущий ещё работает
                self._detect_frame_counter += 1
                if (self._detect_frame_counter % self._detect_every_n == 0 and
                    not self._inference_running and
                    hasattr(self, 'unified_engine') and self.unified_engine and
                    hasattr(self, 'loop') and self.loop and not self.loop.is_closed()):
                    try:
                        if (hasattr(self.unified_engine, 'model_engine') and 
                            self.unified_engine.model_engine is not None):
                            self._inference_running = True
                            asyncio.run_coroutine_threadsafe(
                                self._process_frame_async(frame_copy),
                                self.loop
                            )
                    except Exception as e:
                        self._inference_running = False
                        logger.error(f"Ошибка обработки кадра камеры: {e}", exc_info=True)
                
                try:
                    now = datetime.now()
                    self.root.after(0, lambda n=now: self._update_fps_counter(n))
                except Exception:
                    pass
            # Для предобработанного видео FPS не обновляем
                
        except Exception as e:
            logger.error(f"Ошибка в callback кадра: {e}", exc_info=True)
    
    # Метод _toggle_detection_filter убран - фильтр детекции больше не используется
    
    def _safe_display_frame(self, frame):
        """Безопасное отображение кадра из GUI потока"""
        try:
            # Проверка на существование компонентов
            if not hasattr(self, 'root') or not self.root or not self.root.winfo_exists():
                return
            
            if frame is None:
                return
            
            # Проверка размера кадра
            if not hasattr(frame, 'size') or frame.size == 0:
                return
            
            # Отображение кадра
            if hasattr(self, 'display_frame'):
                self.display_frame(frame)
        except Exception as e:
            logger.error(f"Ошибка отображения кадра: {e}", exc_info=True)
    
    def _update_fps_counter(self, now):
        """Обновление счетчика FPS из GUI потока (thread-safe)"""
        try:
            # Проверка на существование компонентов
            if not hasattr(self, 'root') or not self.root or not self.root.winfo_exists():
                return
            
            # Инкрементируем счетчик
            if not hasattr(self, 'fps_counter'):
                self.fps_counter = 0
            self.fps_counter = self.fps_counter + 1
            
            # Проверяем, прошла ли секунда
            if not hasattr(self, 'fps_time'):
                self.fps_time = now
                return
            
            fps_time = self.fps_time
            if (now - fps_time).total_seconds() >= 1.0:
                fps = self.fps_counter
                self.fps_counter = 0
                self.fps_time = now
                if hasattr(self, 'update_status'):
                    # Показываем FPS только если это камера/поток (не видео файл)
                    # Для видео файлов FPS не имеет смысла - это просто FPS файла
                    is_video_file = (hasattr(self, 'current_saved_detections') and 
                                    self.current_saved_detections and
                                    hasattr(self, 'current_media_file') and 
                                    self.current_media_file)
                    if not is_video_file:
                        # Это камера/поток - показываем FPS
                        self.update_status("FPS", str(fps), "info" if fps >= 60 else "warning")
                    else:
                        # Это видео файл - скрываем FPS или показываем "N/A"
                        self.update_status("FPS", "N/A", "info")
        except Exception as e:
            logger.error(f"Ошибка обновления FPS: {e}", exc_info=True)
    
    def _safe_update_fps(self, fps):
        """Безопасное обновление FPS из GUI потока (legacy метод)"""
        try:
            self.update_status("FPS", str(fps), "info" if fps >= 60 else "warning")
        except Exception as e:
            logger.error(f"Ошибка обновления FPS: {e}", exc_info=True)
    
    def _video_play(self):
        """Запуск воспроизведения"""
        if self.video_display:
            if self.video_display.is_paused:
                self.video_display.resume()
            else:
                self.video_display.start()
            self.is_playing = True
            self.update_status("Детектор", "Активен", "success")
    
    def _video_pause(self):
        """Пауза воспроизведения"""
        if self.video_display:
            self.video_display.pause()
            self.is_playing = False
            self.update_status("Детектор", "На паузе", "warning")
    
    def _video_stop(self):
        """Остановка воспроизведения"""
        if self.video_display:
            self.video_display.stop()
            self.is_playing = False
            self.update_status("Видео", "Не подключено", "warning")
            # Статус Детектор удален
            if hasattr(self, 'video_info_label'):
                self.video_info_label.configure(text="Нет видео")
    
    def _safe_start_video(self):
        """Безопасный запуск видео из GUI потока"""
        try:
            if not hasattr(self, 'video_display') or not self.video_display:
                logger.error("❌ VideoDisplay не создан")
                self.update_status("Видео", "Ошибка: плеер не создан", "error")
                return
            
            # Проверка что видео загружено
            if not hasattr(self.video_display, 'cap') or not self.video_display.cap:
                logger.error("❌ VideoCapture не создан")
                self.update_status("Видео", "Ошибка: каптура не создана", "error")
                return
            
            if not self.video_display.cap.isOpened():
                logger.error("❌ VideoCapture не открыт")
                self.update_status("Видео", "Ошибка: каптура не открыта", "error")
                return
            
            # Проверка статистики видео
            stats = self.video_display.get_stats()
            logger.info(f"📹 Статистика видео: FPS={stats.get('fps', 0):.2f}, Frames={stats.get('total_frames', 0)}")
            
            # Запуск воспроизведения (неблокирующий)
            try:
                logger.info("▶️ Попытка запуска видео...")
                if self.video_display.start():
                    self.is_playing = True
                    logger.info("✅ Видео запущено успешно!")
                    self.update_status("Видео", "Воспроизведение", "success")
                    # Статус Детектор удален
                    
                    # Проверка что поток чтения запущен
                    if hasattr(self.video_display, 'read_thread') and self.video_display.read_thread:
                        if self.video_display.read_thread.is_alive():
                            logger.info("✅ Поток чтения активен")
                        else:
                            logger.warning("⚠️ Поток чтения не активен")
                else:
                    logger.error("❌ Не удалось запустить видео")
                    self.update_status("Видео", "Ошибка запуска", "error")
                    # Статус Детектор удален
            except Exception as e:
                logger.error(f"❌ Ошибка запуска видео: {e}", exc_info=True)
                self.update_status("Видео", f"Ошибка: {str(e)[:30]}", "error")
                # Статус Детектор удален
                
        except Exception as e:
            logger.error(f"❌ Критическая ошибка запуска видео: {e}", exc_info=True)
            self.update_status("Видео", f"Критическая ошибка", "error")
            self.update_status("Детектор", "Ошибка запуска", "error")
    
    def _format_time(self, seconds: float) -> str:
        """Форматирование времени в MM:SS"""
        if seconds < 0:
            return "00:00"
        mins = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{mins:02d}:{secs:02d}"
    
    def update_video(self):
        """Обновление видео потока (legacy метод для обратной совместимости)"""
        # SimpleVideoDisplay обрабатывает кадры сам через callback
        # Этот метод больше не нужен, но оставлен для обратной совместимости
        # НЕ вызываем рекурсивно, так как SimpleVideoDisplay сам управляет кадрами
        try:
            if hasattr(self, 'video_display') and self.video_display:
                pass
        except Exception:
            pass
    
    async def _preprocess_video(self, file_id: str):
        """
        Предобработка видео при импорте - обработка всех кадров YOLO заранее
        
        Args:
            file_id: ID импортированного видео
        """
        try:
            logger.info(f"🎬 Начало предобработки видео: {file_id}")
            
            if not self.media_manager:
                logger.error("MediaManager не инициализирован")
                return
            
            if not self.unified_engine or not self.unified_engine.model_engine:
                logger.error("UnifiedEngine или ModelEngine не готовы")
                if self.media_manager:
                    self.media_manager.update_processing_status(file_id, "error")
                return
            
            # Получение метаданных файла
            file_meta = self.media_manager.get_file(file_id)
            if not file_meta or file_meta["file_type"] != "video":
                logger.error(f"Видео не найдено: {file_id}")
                return
            
            # Обновление статуса
            if self.media_manager:
                self.media_manager.update_processing_status(file_id, "processing")
            # Начало обработки - показываем 0% в статусе "Обработано"
            self.root.after(0, lambda: self.update_status("Обработано", "0%", "info"))
            self.root.after(0, lambda: self.update_status("Видео", f"Обработка: {file_meta['name']}...", "info"))
            
            # Открытие видео
            import cv2
            video_path = file_meta["full_path"]
            cap = cv2.VideoCapture(video_path)
            
            if not cap.isOpened():
                logger.error(f"Не удалось открыть видео: {video_path}")
                if self.media_manager:
                    self.media_manager.update_processing_status(file_id, "error")
                return
            
            # Получение информации о видео
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            fps = cap.get(cv2.CAP_PROP_FPS)
            
            logger.info(f"📹 Видео: {total_frames} кадров, {fps:.2f} FPS")
            
            # Словарь для хранения детекций {frame_number: [detections]}
            all_detections = {}
            frame_number = 0
            processed_frames = 0
            
            # Инициализация трекера объектов (IoU > 0.86)
            from obelisk.core.processors.object_tracker import ObjectTracker
            tracker = ObjectTracker(iou_threshold=0.86, max_missed_frames=5)
            
            # Обработка всех кадров
            while True:
                ret, frame = cap.read()
                if not ret:
                    break
                
                frame_number += 1
                
                # Обработка кадра через UnifiedEngine (максимальная детекция)
                try:
                    # ШАГ 1: Получаем МАКСИМАЛЬНОЕ количество детекций с низким порогом confidence
                    result = await self.unified_engine.process_frame(frame, frame_id=f"frame_{frame_number}")
                    detections = result.get("detections", [])
                    
                    # ШАГ 2: Трекинг объектов применяется ПОСЛЕ получения всех детекций
                    # Трекинг добавляет track_id для отслеживания объектов между кадрами
                    if detections:
                        logger.debug(f"📊 Кадр {frame_number}: получено {len(detections)} детекций (до трекинга)")
                        
                        # Обновление трекеров (добавляет track_id к детекциям, не удаляет их)
                        tracked_detections = tracker.update(detections, frame_number)
                        
                        logger.debug(f"✅ Кадр {frame_number}: после трекинга - {len(tracked_detections)} детекций с track_id")
                        
                        # Сохранение детекций с track_id (ВСЕ детекции сохраняются)
                        all_detections[frame_number] = tracked_detections
                        processed_frames += 1
                    else:
                        # Кадр без детекций - не сохраняем (оптимизация)
                        logger.debug(f"⚠️ Кадр {frame_number}: детекций не найдено")
                        pass
                    
                    # Обновление прогресса каждые 10 кадров
                    if frame_number % 10 == 0:
                        progress = (frame_number / total_frames) * 100 if total_frames > 0 else 0
                        logger.info(f"📊 Прогресс: {progress:.1f}% ({frame_number}/{total_frames} кадров)")
                        # Обновляем статус "Обработано" только процентом в виде цифр
                        self.root.after(0, lambda p=progress: self.update_status(
                            "Обработано", 
                            f"{p:.0f}%", 
                            "info"
                        ))
                
                except Exception as e:
                    logger.warning(f"Ошибка обработки кадра {frame_number}: {e}")
                    continue
            
            cap.release()
            
            # Сохранение детекций
            if all_detections and self.media_manager:
                self.media_manager.save_detections(file_id, all_detections)
                
                # Обновление статистики обработки видео
                processed_videos_count = sum(
                    1 for v in self.media_manager.get_files("video") 
                    if v.get("processed", False)
                )
                total_detections = sum(len(dets) for dets in all_detections.values())
                
                logger.info(f"✅ Предобработка завершена: {processed_frames} кадров с детекциями из {total_frames} ({total_detections} детекций)")
                self.root.after(0, lambda: self.update_status(
                    "Видео", 
                    f"Готово: {file_meta['name']}", 
                    "success"
                ))
                self.root.after(0, lambda: self.update_status(
                    "Обработано",
                    f"{processed_videos_count} видео",
                    "success"
                ))
                self.root.after(0, lambda: self.update_status(
                    "Кадров",
                    f"{processed_frames} кадров",
                    "info"
                ))
                self.root.after(0, lambda: self.update_status(
                    "Детекций",
                    f"{total_detections}",
                    "info"
                ))
            else:
                logger.warning(f"⚠️ Детекций не найдено в видео: {file_id}")
                if self.media_manager:
                    self.media_manager.update_processing_status(file_id, "completed")
                self.root.after(0, lambda: self.update_status(
                    "Видео", 
                    f"Готово: {file_meta['name']} (детекций нет)", 
                    "warning"
                ))
                self.root.after(0, lambda: self.update_status(
                    "Кадров",
                    "0 кадров",
                    "warning"
                ))
                self.root.after(0, lambda: self.update_status(
                    "Детекций",
                    "0",
                    "warning"
                ))
            
            # Обновление списка медиа
            self.root.after(0, lambda: self.refresh_media_list())
            
        except Exception as e:
            logger.error(f"❌ Ошибка предобработки видео: {e}", exc_info=True)
            if self.media_manager:
                self.media_manager.update_processing_status(file_id, "error")
            self.root.after(0, lambda: self.update_status("Видео", f"Ошибка обработки", "error"))
    
    async def _auto_process_videos(self):
        """
        Автоматическая обработка непроработанных видео после проверки модели
        Запускается после инициализации и проверки модели
        """
        try:
            if not self.media_manager:
                logger.warning("MediaManager не доступен для автоматической обработки")
                return
            
            # Получаем список видео файлов
            videos = self.media_manager.get_files("video")
            
            if not videos:
                logger.info("Нет видео для автоматической обработки")
                return
            
            # Фильтруем непроработанные видео
            unprocessed_videos = [
                v for v in videos 
                if not v.get("processed", False) and v.get("processing_status") != "processing"
            ]
            
            if not unprocessed_videos:
                logger.info("Все видео уже обработаны")
                # Обновление статистики обработанных видео
                processed_count = len([v for v in videos if v.get("processed", False)])
                self.root.after(0, lambda: self.update_status("Обработано", f"{processed_count} видео", "success"))
                return
            
            logger.info(f"🎬 Найдено {len(unprocessed_videos)} непроработанных видео. Начинаем автоматическую обработку...")
            self.root.after(0, lambda: self.update_status("Видео", f"Автообработка: {len(unprocessed_videos)} видео...", "info"))
            
            # Обрабатываем каждое видео
            for video_meta in unprocessed_videos:
                file_id = video_meta.get("id")
                video_name = video_meta.get("name", "unknown")
                
                logger.info(f"📹 Автоматическая обработка: {video_name}")
                
                # Запускаем предобработку
                await self._preprocess_video(file_id)
                
                # Небольшая задержка между видео
                await asyncio.sleep(1)
            
            logger.info(f"✅ Автоматическая обработка завершена: обработано {len(unprocessed_videos)} видео")
            
            # Обновление статистики обработанных видео
            processed_count = len([v for v in self.media_manager.get_files("video") if v.get("processed", False)])
            self.root.after(0, lambda: self.update_status("Видео", "Готово", "success"))
            self.root.after(0, lambda: self.update_status("Обработано", f"{processed_count} видео", "success"))
            
            # Обновляем список медиа
            self.root.after(0, lambda: self.refresh_media_list())
            
        except Exception as e:
            logger.error(f"❌ Ошибка автоматической обработки видео: {e}", exc_info=True)
            self.root.after(0, lambda: self.update_status("Видео", f"Ошибка автообработки", "error"))
    
    async def _process_frame_async(self, frame):
        """Асинхронная YOLO-детекция. Обновляет self.current_detections — отрисовка в _on_video_frame."""
        try:
            if not self.unified_engine:
                return
            if not hasattr(self.unified_engine, 'model_engine') or not self.unified_engine.model_engine:
                return
            if not hasattr(self.unified_engine.model_engine, 'models') or not self.unified_engine.model_engine.models:
                return
            
            result = await self.unified_engine.process_frame(frame)
            detections = result.get("detections", [])
            
            self.current_detections = detections
            self.current_visual_context = result.get("visual_context")
            
            count = len(detections)
            self.root.after(0, lambda cnt=count: self.update_status("Детекций", str(cnt), "info" if cnt > 0 else "warning"))
            
        except Exception as e:
            logger.error(f"Ошибка обработки кадра: {e}", exc_info=True)
        finally:
            self._inference_running = False
    
    def display_frame(self, frame):
        """Быстрое отображение кадра через ImageTk.PhotoImage (без CTkImage overhead)"""
        try:
            if frame is None or not hasattr(frame, 'shape') or len(frame.shape) < 2:
                return
            if not hasattr(self, 'video_label') or not self.video_label:
                return
            
            self._display_busy = True
            
            height, width = frame.shape[:2]
            if height == 0 or width == 0:
                self._display_busy = False
                return
            
            max_w, max_h = 1200, 800
            if not hasattr(self, '_last_frame_size') or self._last_frame_size != (width, height):
                self._last_frame_size = (width, height)
                if width > max_w or height > max_h:
                    s = min(max_w / width, max_h / height)
                    self._scale_factor = s
                    self._scaled_size = (int(width * s), int(height * s))
                else:
                    self._scale_factor = 1.0
                    self._scaled_size = (width, height)
            
            if self._scale_factor != 1.0:
                frame = cv2.resize(frame, self._scaled_size, interpolation=cv2.INTER_LINEAR)
            
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            pil_img = Image.fromarray(frame_rgb)
            self._photo_image = ImageTk.PhotoImage(image=pil_img)
            self.video_label.configure(image=self._photo_image, text="")
            
            self._display_busy = False
        except Exception as e:
            self._display_busy = False
            logger.error(f"display_frame error: {e}", exc_info=True)
    
    def refresh_media_list(self):
        """Обновление списка медиа файлов в интерфейсе"""
        try:
            if not hasattr(self, 'media_list_container'):
                logger.warning("media_list_container не существует")
                return
            
            # Очистка текущего списка
            for widget in self.media_list_container.winfo_children():
                widget.destroy()
            self.media_items = {}
            
            if not self.media_manager:
                logger.warning("MediaManager не инициализирован")
                return
            
            # Получение списка файлов
            all_files = self.media_manager.get_files()
            
            if not all_files:
                # Нет файлов - показываем сообщение
                empty_label = ctk.CTkLabel(
                    self.media_list_container,
                    text="Нет загруженных файлов\nИспользуйте кнопку 'Импорт'",
                    font=("Segoe UI", 11),
                    text_color=MATERIAL_THEME["text_secondary"],
                    justify="center"
                )
                empty_label.pack(pady=20)
                return
            
            # Создание элементов списка для каждого файла
            for file_meta in all_files[:20]:  # Ограничение до 20 файлов для производительности
                file_id = file_meta.get("id")
                file_name = file_meta.get("name", "Unknown")
                file_type = file_meta.get("file_type", "unknown")
                file_size_mb = file_meta.get("size_mb", 0)
                
                # Фрейм для элемента списка
                item_frame = ctk.CTkFrame(
                    self.media_list_container,
                    fg_color=MATERIAL_THEME["surface"],
                    corner_radius=5
                )
                item_frame.pack(fill="x", padx=5, pady=3)
                
                # Иконка типа файла
                icon = "🎥" if file_type == "video" else "📷"
                
                # Информация о файле
                info_frame = ctk.CTkFrame(item_frame, fg_color="transparent")
                info_frame.pack(fill="x", padx=10, pady=5)
                
                # Название файла (кликабельное для загрузки)
                # Обрезаем длинное имя файла если нужно
                display_name = f"{icon} {file_name}"
                if len(display_name) > 35:  # Ограничение по количеству символов
                    display_name = display_name[:32] + "..."
                
                name_button = ctk.CTkButton(
                    info_frame,
                    text=display_name,
                    font=("Segoe UI", 10, "bold"),
                    fg_color="transparent",
                    hover_color=MATERIAL_THEME["surface_variant"],
                    anchor="w",
                    command=lambda fid=file_id: self.load_media_file(fid),
                    text_color=MATERIAL_THEME["text_primary"],
                    width=250  # Ограничение ширины
                )
                name_button.pack(side="left", fill="x", expand=True, padx=(0, 10))
                
                # Размер файла
                size_label = ctk.CTkLabel(
                    info_frame,
                    text=f"{file_size_mb} MB",
                    font=("Segoe UI", 9),
                    text_color=MATERIAL_THEME["text_secondary"]
                )
                size_label.pack(side="right", padx=(10, 0))
                
                # Кнопки управления
                buttons_frame = ctk.CTkFrame(item_frame, fg_color="transparent")
                buttons_frame.pack(fill="x", padx=10, pady=(0, 5))
                
                # Кнопка удаления
                delete_btn = ctk.CTkButton(
                    buttons_frame,
                    text="🗑️",
                    width=30,
                    height=25,
                    fg_color=MATERIAL_THEME["error"],
                    hover_color="#D32F2F",
                    font=("Segoe UI", 12),
                    command=lambda fid=file_id: self.delete_media_file(fid)
                )
                delete_btn.pack(side="right", padx=2)
                
                # Сохранение элемента
                self.media_items[file_id] = item_frame
            
            logger.info(f"✅ Список медиа обновлен: {len(all_files)} файлов")
            
        except Exception as e:
            logger.error(f"Ошибка обновления списка медиа: {e}", exc_info=True)
    
    def delete_media_file(self, file_id: str):
        """Удаление медиа файла"""
        try:
            if not self.media_manager:
                logger.error("MediaManager не инициализирован")
                return
            
            # Подтверждение удаления
            from tkinter import messagebox
            file_meta = self.media_manager.get_file(file_id)
            if not file_meta:
                logger.error(f"Файл не найден: {file_id}")
                return
            
            file_name = file_meta.get("name", "Unknown")
            if not messagebox.askyesno("Удаление файла", f"Удалить файл {file_name}?"):
                return
            
            # Удаление через MediaManager
            if self.media_manager.delete_file(file_id):
                logger.info(f"✅ Файл удален: {file_name}")
                # Если удаляемый файл был текущим - очистить плеер
                if self.current_media_file and self.current_media_file.get("id") == file_id:
                    self.current_media_file = None
                    if self.video_display:
                        self.video_display.stop()
                    self.update_status("Видео", "Не подключено", "warning")
                # Обновление списка
                self.refresh_media_list()
            else:
                logger.error(f"Не удалось удалить файл: {file_id}")
                messagebox.showerror("Ошибка", "Не удалось удалить файл")
                
        except Exception as e:
            logger.error(f"Ошибка удаления файла: {e}", exc_info=True)
            from tkinter import messagebox
            try:
                messagebox.showerror("Ошибка", f"Не удалось удалить файл: {str(e)[:100]}")
            except Exception:
                pass
    
    def show_model_selector(self):
        """Показать диалог выбора модели"""
        try:
            if not self.model_selector:
                logger.error("ModelSelector не инициализирован")
                self.update_status("Модель", "Ошибка: ModelSelector не готов", "error")
                return
            
            # Получаем список доступных моделей
            models = self.model_selector.get_available_models()
            
            if not models:
                from tkinter import messagebox
                messagebox.showinfo("Выбор модели", "Доступные модели не найдены")
                return
            
            # Создание окна выбора модели
            selector_window = ctk.CTkToplevel(self.root)
            selector_window.title("Выбор модели")
            selector_window.geometry("600x500")
            selector_window.transient(self.root)
            
            # Заголовок
            title_label = ctk.CTkLabel(
                selector_window,
                text="📦 Выберите модель",
                font=("Segoe UI", 16, "bold")
            )
            title_label.pack(pady=20)
            
            # Список моделей
            scroll_frame = ctk.CTkScrollableFrame(selector_window, height=300, label_anchor="w")
            scroll_frame.pack(fill="both", expand=True, padx=20, pady=10)
            # Ограничиваем ширину прокручиваемого фрейма (600px окно - 40px padding = 560px)
            scroll_frame.configure(width=560)
            
            # Отображение моделей
            for model in models:
                # Главный фрейм для модели
                model_frame = ctk.CTkFrame(scroll_frame)
                model_frame.pack(fill="x", padx=5, pady=5)
                model_frame.pack_propagate(False)
                
                # Левая колонка - информация (ограничиваем ширину)
                info_frame = ctk.CTkFrame(model_frame, fg_color="transparent")
                info_frame.pack(side="left", fill="both", expand=True, padx=(10, 5), pady=10)
                info_frame.pack_propagate(False)
                
                # Название модели (с переносом при необходимости)
                name_text = model['name']
                name_label = ctk.CTkLabel(
                    info_frame,
                    text=name_text,
                    font=("Segoe UI", 12, "bold"),
                    anchor="w",
                    justify="left",
                    wraplength=350  # Ограничение ширины для переноса
                )
                name_label.pack(anchor="w", fill="x", pady=(0, 5))
                
                # Базовая информация
                basic_info = f"📦 {model['size'] / (1024*1024):.2f} MB | 📅 {model['modified'].strftime('%Y-%m-%d %H:%M')}"
                if model.get('training_dir'):
                    basic_info += f" | 📁 {model['training_dir']}"
                
                basic_label = ctk.CTkLabel(
                    info_frame,
                    text=basic_info,
                    font=("Segoe UI", 9),
                    anchor="w",
                    justify="left",
                    text_color=MATERIAL_THEME["text_secondary"],
                    wraplength=350  # Ограничение ширины
                )
                basic_label.pack(anchor="w", fill="x", pady=(0, 5))
                
                # Метрики (если есть)
                metrics_parts = []
                if model.get('map50') is not None:
                    metrics_parts.append(f"mAP@0.5: {model['map50']:.3f}")
                if model.get('precision') is not None:
                    metrics_parts.append(f"P: {model['precision']:.3f}")
                if model.get('recall') is not None:
                    metrics_parts.append(f"R: {model['recall']:.3f}")
                if model.get('map50_95') is not None:
                    metrics_parts.append(f"mAP: {model['map50_95']:.3f}")
                if model.get('epochs') is not None:
                    metrics_parts.append(f"Epochs: {model['epochs']}")
                
                if metrics_parts:
                    # Разбиваем на две строки если метрик много
                    if len(metrics_parts) > 3:
                        metrics_text1 = " | ".join(metrics_parts[:3])
                        metrics_text2 = " | ".join(metrics_parts[3:])
                        metrics_label1 = ctk.CTkLabel(
                            info_frame,
                            text=f"📊 {metrics_text1}",
                            font=("Segoe UI", 9),
                            anchor="w",
                            justify="left",
                            text_color=MATERIAL_THEME["primary"],
                            wraplength=350
                        )
                        metrics_label1.pack(anchor="w", fill="x", pady=(0, 2))
                        
                        metrics_label2 = ctk.CTkLabel(
                            info_frame,
                            text=f"   {metrics_text2}",
                            font=("Segoe UI", 9),
                            anchor="w",
                            justify="left",
                            text_color=MATERIAL_THEME["primary"],
                            wraplength=350
                        )
                        metrics_label2.pack(anchor="w", fill="x")
                    else:
                        metrics_text = " | ".join(metrics_parts)
                        metrics_label = ctk.CTkLabel(
                            info_frame,
                            text=f"📊 {metrics_text}",
                            font=("Segoe UI", 9),
                            anchor="w",
                            justify="left",
                            text_color=MATERIAL_THEME["primary"],
                            wraplength=350
                        )
                        metrics_label.pack(anchor="w", fill="x")
                
                # Правая колонка - кнопка (фиксированная ширина)
                button_frame = ctk.CTkFrame(model_frame, fg_color="transparent")
                button_frame.pack(side="right", padx=(5, 10), pady=10)
                button_frame.pack_propagate(False)
                button_frame.configure(width=100)
                
                select_btn = MaterialButton(
                    button_frame,
                    text="Выбрать",
                    command=lambda p=model['path'], n=model['name']: self._select_model(p, n, selector_window),
                    variant="outlined",
                    width=90
                )
                select_btn.pack()
            
            # Кнопка закрытия
            close_btn = MaterialButton(
                selector_window,
                text="Закрыть",
                command=selector_window.destroy,
                variant="outlined"
            )
            close_btn.pack(pady=10)
            
        except Exception as e:
            logger.error(f"❌ Ошибка показа выбора модели: {e}", exc_info=True)
            from tkinter import messagebox
            messagebox.showerror("Ошибка", f"Не удалось загрузить список моделей: {e}")
    
    def _select_model(self, model_path: str, model_name: str, window):
        """Выбрать модель и применить её"""
        try:
            if not self.model_selector:
                logger.error("ModelSelector не инициализирован")
                return
            
            # Подтверждение
            from tkinter import messagebox
            result = messagebox.askyesno(
                "Выбор модели",
                f"Выбрать модель '{model_name}'?\n\n"
                f"Текущая модель будет сохранена в backups."
            )
            
            if not result:
                return
            
            # Выбор модели
            if self.model_selector.select_model(model_path, backup_current=True):
                logger.info(f"✅ Модель выбрана: {model_name}")
                self.update_status("Модель", f"Изменена: {model_name}", "info")
                messagebox.showinfo("Успех", f"Модель '{model_name}' выбрана.\n\nПерезапустите программу для применения.")
                window.destroy()
            else:
                messagebox.showerror("Ошибка", "Не удалось выбрать модель")
                
        except Exception as e:
            logger.error(f"❌ Ошибка выбора модели: {e}", exc_info=True)
            from tkinter import messagebox
            messagebox.showerror("Ошибка", f"Не удалось выбрать модель: {e}")
    
    def clear_cache(self):
        """Очистить кэш системы"""
        try:
            if not self.cache_manager:
                logger.error("CacheManager не инициализирован")
                self.update_status("Модель", "Ошибка: CacheManager не готов", "error")
                return
            
            from tkinter import messagebox
            result = messagebox.askyesno(
                "Очистка кэша",
                "Очистить весь кэш системы?\n\n"
                "Это удалит:\n"
                "- Кэш детекций\n"
                "- Кэш датасетов (.cache файлы)\n"
                "- Временные файлы (__pycache__)"
            )
            
            if not result:
                return
            
            # Очистка кэша
            results = self.cache_manager.clear_all_cache(self.unified_engine)
            
            # Показ результата
            total_size_mb = results["total_size"] / (1024 * 1024)
            messagebox.showinfo(
                "Очистка завершена",
                f"Кэш очищен:\n\n"
                f"- Удалено файлов: {results['total_cleared']}\n"
                f"- Освобождено места: {total_size_mb:.2f} MB"
            )
            
            logger.info(f"✅ Кэш очищен: {results['total_cleared']} файлов ({total_size_mb:.2f} MB)")
            self.update_status("Модель", f"Кэш очищен: {total_size_mb:.2f} MB", "success")
            
        except Exception as e:
            logger.error(f"❌ Ошибка очистки кэша: {e}", exc_info=True)
            from tkinter import messagebox
            messagebox.showerror("Ошибка", f"Не удалось очистить кэш: {e}")
    
    def show_annotation_tool(self):
        """Показать инструмент ручной разметки на текущем кадре"""
        try:
            if not self.annotation_tool:
                logger.error("AnnotationTool не инициализирован")
                self.update_status("Модель", "Ошибка: AnnotationTool не готов", "error")
                return
            
            # Проверка наличия текущего кадра
            if not hasattr(self, 'current_frame') or self.current_frame is None:
                from tkinter import messagebox
                messagebox.showwarning("Предупреждение", "Нет текущего кадра для разметки.\nСначала загрузите видео или подключите камеру.")
                return
            
            # Остановка видео перед разметкой
            was_playing = False
            if hasattr(self, 'is_playing') and self.is_playing:
                if self.video_display:
                    self.video_display.pause()
                was_playing = True
                logger.info("⏸️ Видео приостановлено для разметки")
            
            # Сохранение текущего кадра во временный файл (скриншот)
            import tempfile
            with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as tmp_file:
                temp_image_path = Path(tmp_file.name)
                cv2.imwrite(str(temp_image_path), self.current_frame)
                logger.info(f"📸 Скриншот сохранен: {temp_image_path}")
            
            # Создание окна разметки
            annotation_window = ctk.CTkToplevel(self.root)
            annotation_window.title("Инструмент разметки")
            annotation_window.geometry("900x700")
            annotation_window.transient(self.root)
            
            # Флаг для отслеживания сохранения
            annotation_saved = {"value": False}
            
            # Создание виджета разметки
            try:
                from obelisk.ui.annotation_widget import AnnotationWidget
                
                def on_save_annotation(bboxes: List[Dict], original_path: Path):
                    """Callback для сохранения аннотации"""
                    try:
                        # Сохранение через AnnotationTool (автоматически отправляет в датасет)
                        result = self.annotation_tool.save_annotation(
                            original_path,
                            bboxes,
                            save_annotated_image=True
                        )
                        
                        if result.get("success"):
                            annotation_saved["value"] = True
                            from tkinter import messagebox
                            messagebox.showinfo(
                                "Успех",
                                f"Аннотация сохранена в датасет для обучения!\n\n"
                                f"- Изображение: {result['image_path']}\n"
                                f"- Метки: {result['label_path']}\n"
                                f"- Размеченное: {result['annotated_image_path']}\n"
                                f"- Объектов: {result['bboxes_count']}"
                            )
                            logger.info(f"✅ Аннотация сохранена в датасет: {result['bboxes_count']} объектов")
                            self.update_status("Модель", f"Разметка сохранена: {result['bboxes_count']} объектов", "success")
                            annotation_window.destroy()
                        else:
                            from tkinter import messagebox
                            messagebox.showerror("Ошибка", f"Не удалось сохранить аннотацию: {result.get('error', 'Неизвестная ошибка')}")
                    except Exception as e:
                        logger.error(f"❌ Ошибка сохранения аннотации: {e}", exc_info=True)
                        from tkinter import messagebox
                        messagebox.showerror("Ошибка", f"Не удалось сохранить аннотацию: {e}")
                
                annotation_widget = AnnotationWidget(
                    annotation_window,
                    temp_image_path,
                    on_save=on_save_annotation
                )
                
                # Обработка закрытия окна
                def on_close():
                    # Удаление временного файла
                    try:
                        if temp_image_path.exists():
                            temp_image_path.unlink()
                            logger.debug(f"🗑️ Временный файл удален: {temp_image_path}")
                    except Exception as e:
                        logger.warning(f"⚠️ Не удалось удалить временный файл: {e}")
                    
                    # Возобновление видео если оно было запущено и разметка не сохранена
                    if was_playing and not annotation_saved["value"]:
                        if self.video_display:
                            self.video_display.play()
                        logger.info("▶️ Видео возобновлено")
                    
                    annotation_window.destroy()
                
                annotation_window.protocol("WM_DELETE_WINDOW", on_close)
                
            except Exception as e:
                logger.error(f"❌ Ошибка создания виджета разметки: {e}", exc_info=True)
                from tkinter import messagebox
                messagebox.showerror("Ошибка", f"Не удалось открыть инструмент разметки: {e}")
                
                # Удаление временного файла
                try:
                    if temp_image_path.exists():
                        temp_image_path.unlink()
                except Exception:
                    pass
                
                # Возобновление видео
                if was_playing:
                    if self.video_display:
                        self.video_display.play()
                
                annotation_window.destroy()
                
        except Exception as e:
            logger.error(f"❌ Ошибка показа инструмента разметки: {e}", exc_info=True)
            from tkinter import messagebox
            messagebox.showerror("Ошибка", f"Не удалось открыть инструмент разметки: {e}")
    
    def add_label_from_frame(self):
        """Добавить метку из текущего кадра с детекциями"""
        try:
            if not self.annotation_tool:
                logger.error("AnnotationTool не инициализирован")
                self.update_status("Модель", "Ошибка: AnnotationTool не готов", "error")
                return
            
            # Проверка наличия текущего кадра и детекций
            if not hasattr(self, 'current_frame') or self.current_frame is None:
                from tkinter import messagebox
                messagebox.showwarning("Предупреждение", "Нет текущего кадра для разметки")
                return
            
            # Получаем детекции из текущего кадра
            # Если есть сохраненные детекции - используем их
            detections = []
            if hasattr(self, 'current_saved_detections') and self.current_saved_detections:
                if hasattr(self, 'video_display') and self.video_display:
                    frame_number = self.video_display.current_frame_number
                    detections = self.current_saved_detections.get(frame_number, [])
            elif hasattr(self, 'current_detections') and self.current_detections:
                detections = self.current_detections
            
            if not detections:
                from tkinter import messagebox
                messagebox.showwarning("Предупреждение", "Нет детекций на текущем кадре для разметки")
                return
            
            # Подтверждение
            from tkinter import messagebox
            result = messagebox.askyesno(
                "Добавить метку",
                f"Добавить метки для {len(detections)} объектов с confidence 100%?\n\n"
                f"Изображение будет сохранено в датасет для обучения."
            )
            
            if not result:
                return
            
            # Сохранение текущего кадра во временный файл
            import tempfile
            with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as tmp_file:
                temp_image_path = Path(tmp_file.name)
                cv2.imwrite(str(temp_image_path), self.current_frame)
            
            try:
                # Конвертация детекций в формат для аннотации
                bboxes = []
                for det in detections:
                    bbox = det.get('bbox', [0, 0, 0, 0])
                    class_id = det.get('class', 0)
                    # Все метки с confidence 100%
                    bboxes.append({
                        "bbox": bbox,
                        "class": class_id,
                        "confidence": 1.0
                    })
                
                # Сохранение через AnnotationTool
                result = self.annotation_tool.save_annotation(
                    temp_image_path,
                    bboxes,
                    save_annotated_image=True
                )
                
                if result.get("success"):
                    messagebox.showinfo(
                        "Успех",
                        f"Метки добавлены!\n\n"
                        f"- Изображение: {result['image_path']}\n"
                        f"- Метки: {result['label_path']}\n"
                        f"- Размеченное: {result['annotated_image_path']}\n"
                        f"- Объектов: {result['bboxes_count']}"
                    )
                    logger.info(f"✅ Метки добавлены: {result['bboxes_count']} объектов")
                    self.update_status("Модель", f"Метки добавлены: {result['bboxes_count']} объектов", "success")
                else:
                    messagebox.showerror("Ошибка", f"Не удалось сохранить метки: {result.get('error', 'Неизвестная ошибка')}")
                    
            finally:
                # Удаление временного файла
                try:
                    if temp_image_path.exists():
                        temp_image_path.unlink()
                except Exception:
                    pass
                    
        except Exception as e:
            logger.error(f"❌ Ошибка добавления метки: {e}", exc_info=True)
            from tkinter import messagebox
            messagebox.showerror("Ошибка", f"Не удалось добавить метку: {e}")
    
    def run(self):
        """Запуск интерфейса"""
        self.root.mainloop()


def main():
    """Главная функция"""
    try:
        app = MaterialEcoNetGUI()
        app.run()
    except Exception as e:
        logger.error(f"Ошибка запуска приложения: {e}", exc_info=True)
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()

