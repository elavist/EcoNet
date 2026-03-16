"""
Виджет для ручной разметки изображений
"""
import logging
from pathlib import Path
from typing import Optional, List, Dict, Callable
import cv2
import numpy as np
import customtkinter as ctk

logger = logging.getLogger(__name__)


class AnnotationWidget:
    """Виджет для ручной разметки изображений с рисованием боксов"""
    
    def __init__(self, parent, image_path: Path, on_save: Optional[Callable] = None):
        """
        Инициализация виджета разметки
        
        Args:
            parent: Родительский виджет
            image_path: Путь к изображению для разметки
            on_save: Callback функция для сохранения (bboxes, annotated_image_path)
        """
        self.parent = parent
        self.image_path = image_path
        self.on_save = on_save
        
        # Состояние разметки
        self.bboxes: List[Dict] = []
        self.current_bbox = None
        self.drawing = False
        self.start_point = None
        
        # Загрузка изображения
        self.original_image = cv2.imread(str(image_path))
        if self.original_image is None:
            raise ValueError(f"Не удалось загрузить изображение: {image_path}")
        
        self.display_image = self.original_image.copy()
        self.image_height, self.image_width = self.original_image.shape[:2]
        
        # Создание интерфейса
        self._create_ui()
        
    def _create_ui(self):
        """Создание интерфейса виджета"""
        # Основной фрейм
        self.main_frame = ctk.CTkFrame(self.parent)
        self.main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Заголовок
        title_label = ctk.CTkLabel(
            self.main_frame,
            text="🎨 Ручная разметка",
            font=("Segoe UI", 16, "bold")
        )
        title_label.pack(pady=10)
        
        # Холст для изображения (используем стандартный tkinter Canvas)
        import tkinter as tk
        canvas_width = min(800, self.image_width)
        canvas_height = min(600, self.image_height)
        
        # Создание фрейма для канваса (CustomTkinter может встраивать tkinter виджеты)
        canvas_frame = ctk.CTkFrame(self.main_frame)
        canvas_frame.pack(padx=10, pady=10)
        
        # Используем стандартный tkinter Canvas внутри CTkFrame
        self.canvas = tk.Canvas(
            canvas_frame,
            width=canvas_width,
            height=canvas_height,
            bg="gray20",
            highlightthickness=0
        )
        self.canvas.pack(fill="both", expand=True)
        
        # Привязка событий мыши
        self.canvas.bind("<Button-1>", self._on_mouse_down)
        self.canvas.bind("<B1-Motion>", self._on_mouse_drag)
        self.canvas.bind("<ButtonRelease-1>", self._on_mouse_up)
        
        # Кнопки управления
        buttons_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        buttons_frame.pack(pady=10)
        
        # Кнопка добавления бокса
        self.add_bbox_btn = ctk.CTkButton(
            buttons_frame,
            text="➕ Добавить бокс (100%)",
            command=self._start_drawing,
            width=150
        )
        self.add_bbox_btn.pack(side="left", padx=5)
        
        # Кнопка удаления последнего бокса
        self.undo_btn = ctk.CTkButton(
            buttons_frame,
            text="↩️ Отменить",
            command=self._undo_last,
            width=120
        )
        self.undo_btn.pack(side="left", padx=5)
        
        # Кнопка очистки
        self.clear_btn = ctk.CTkButton(
            buttons_frame,
            text="🗑️ Очистить",
            command=self._clear_all,
            width=120
        )
        self.clear_btn.pack(side="left", padx=5)
        
        # Кнопка сохранения
        self.save_btn = ctk.CTkButton(
            buttons_frame,
            text="💾 Сохранить",
            command=self._save_annotation,
            width=120,
            fg_color="#2196F3",
            hover_color="#1976D2"
        )
        self.save_btn.pack(side="left", padx=5)
        
        # Список добавленных боксов
        self.bbox_list_frame = ctk.CTkScrollableFrame(self.main_frame, height=150)
        self.bbox_list_frame.pack(fill="x", padx=10, pady=10)
        
        # Отображение изображения
        self._update_display()
    
    def _start_drawing(self):
        """Начать рисование бокса"""
        self.drawing = True
        self.add_bbox_btn.configure(text="🎯 Рисуйте на изображении...", state="disabled")
        logger.info("🎨 Режим рисования активирован")
    
    def _on_mouse_down(self, event):
        """Обработка нажатия мыши"""
        if not self.drawing:
            return
        
        # Конвертация координат канваса в координаты изображения
        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()
        
        scale_x = self.image_width / canvas_width
        scale_y = self.image_height / canvas_height
        
        x = int(event.x * scale_x)
        y = int(event.y * scale_y)
        
        self.start_point = (x, y)
        self.current_bbox = {"bbox": [x, y, 0, 0], "class": 0, "confidence": 1.0}
    
    def _on_mouse_drag(self, event):
        """Обработка перетаскивания мыши"""
        if not self.drawing or not self.start_point:
            return
        
        # Конвертация координат
        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()
        
        scale_x = self.image_width / canvas_width
        scale_y = self.image_height / canvas_height
        
        x = int(event.x * scale_x)
        y = int(event.y * scale_y)
        
        # Обновление текущего бокса
        start_x, start_y = self.start_point
        self.current_bbox["bbox"] = [
            min(start_x, x),
            min(start_y, y),
            abs(x - start_x),
            abs(y - start_y)
        ]
        
        # Обновление отображения
        self._update_display()
    
    def _on_mouse_up(self, event):
        """Обработка отпускания мыши"""
        if not self.drawing or not self.start_point:
            return
        
        self.drawing = False
        self.add_bbox_btn.configure(text="➕ Добавить бокс (100%)", state="normal")
        
        # Финализация бокса
        if self.current_bbox and self.current_bbox["bbox"][2] > 10 and self.current_bbox["bbox"][3] > 10:
            self.bboxes.append(self.current_bbox.copy())
            logger.info(f"✅ Бокс добавлен: {self.current_bbox['bbox']}")
            self._update_bbox_list()
        
        self.current_bbox = None
        self.start_point = None
        self._update_display()
    
    def _update_display(self):
        """Обновление отображения изображения с боксами"""
        try:
            # Копируем оригинальное изображение
            display = self.original_image.copy()
            
            # Рисуем сохраненные боксы
            for i, bbox in enumerate(self.bboxes):
                x, y, w, h = bbox["bbox"]
                x1, y1 = int(x), int(y)
                x2, y2 = int(x + w), int(y + h)
                
                cv2.rectangle(display, (x1, y1), (x2, y2), (0, 255, 0), 2)
                cv2.putText(display, f"#{i+1}", (x1, y1 - 10),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
            
            # Рисуем текущий бокс
            if self.current_bbox:
                x, y, w, h = self.current_bbox["bbox"]
                x1, y1 = int(x), int(y)
                x2, y2 = int(x + w), int(y + h)
                
                cv2.rectangle(display, (x1, y1), (x2, y2), (255, 255, 0), 2)
            
            # Получение размеров канваса
            self.canvas.update_idletasks()
            canvas_width = max(self.canvas.winfo_width(), 800)
            canvas_height = max(self.canvas.winfo_height(), 600)
            
            # Изменение размера для отображения
            if canvas_width > 1 and canvas_height > 1:
                scale = min(canvas_width / self.image_width, canvas_height / self.image_height)
                new_width = int(self.image_width * scale)
                new_height = int(self.image_height * scale)
                
                if new_width > 0 and new_height > 0:
                    resized = cv2.resize(display, (new_width, new_height))
                    
                    # Конвертация в формат для Tkinter
                    rgb_image = cv2.cvtColor(resized, cv2.COLOR_BGR2RGB)
                    from PIL import Image, ImageTk
                    pil_image = Image.fromarray(rgb_image)
                    photo = ImageTk.PhotoImage(image=pil_image)
                    
                    # Отображение на канвасе
                    self.canvas.delete("all")
                    self.canvas.create_image(canvas_width // 2, canvas_height // 2, image=photo, anchor="center")
                    self.canvas.image = photo  # Сохранение ссылки
        except Exception as e:
            logger.error(f"❌ Ошибка обновления отображения: {e}", exc_info=True)
    
    def _update_bbox_list(self):
        """Обновление списка боксов"""
        # Очистка списка
        for widget in self.bbox_list_frame.winfo_children():
            widget.destroy()
        
        # Отображение боксов
        for i, bbox in enumerate(self.bboxes):
            x, y, w, h = bbox["bbox"]
            bbox_frame = ctk.CTkFrame(self.bbox_list_frame)
            bbox_frame.pack(fill="x", padx=5, pady=2)
            
            info_label = ctk.CTkLabel(
                bbox_frame,
                text=f"Бокс #{i+1}: x={x:.0f}, y={y:.0f}, w={w:.0f}, h={h:.0f}",
                font=("Segoe UI", 10)
            )
            info_label.pack(side="left", padx=10)
            
            delete_btn = ctk.CTkButton(
                bbox_frame,
                text="🗑️",
                width=30,
                command=lambda idx=i: self._remove_bbox(idx)
            )
            delete_btn.pack(side="right", padx=5)
    
    def _remove_bbox(self, index: int):
        """Удалить бокс по индексу"""
        if 0 <= index < len(self.bboxes):
            self.bboxes.pop(index)
            self._update_bbox_list()
            self._update_display()
            logger.info(f"✅ Бокс #{index+1} удален")
    
    def _undo_last(self):
        """Отменить последний добавленный бокс"""
        if self.bboxes:
            self.bboxes.pop()
            self._update_bbox_list()
            self._update_display()
            logger.info("✅ Последний бокс отменен")
    
    def _clear_all(self):
        """Очистить все боксы"""
        self.bboxes.clear()
        self.current_bbox = None
        self._update_bbox_list()
        self._update_display()
        logger.info("✅ Все боксы очищены")
    
    def _save_annotation(self):
        """Сохранить аннотацию"""
        if not self.bboxes:
            from tkinter import messagebox
            messagebox.showwarning("Предупреждение", "Нет боксов для сохранения")
            return
        
        if self.on_save:
            self.on_save(self.bboxes, self.image_path)
        else:
            logger.warning("⚠️ Callback on_save не установлен")

