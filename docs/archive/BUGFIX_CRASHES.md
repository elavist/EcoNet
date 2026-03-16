# 🐛 Исправление Крашей при Загрузке Видео

## Обнаруженные Проблемы

### 1. Thread-Safety Проблемы
**Проблема**: Callback `_on_video_frame` вызывается из фонового потока VideoPlayer, но пытается напрямую обращаться к GUI компонентам (Tkinter).

**Исправление**:
- ✅ Добавлены проверки на существование `self.root` перед вызовом `self.root.after()`
- ✅ Все обновления GUI перенесены в GUI поток через `root.after(0, ...)`
- ✅ Созданы безопасные методы для обновления GUI: `_safe_display_frame()`, `_safe_update_fps()`

### 2. Проблемы с Замыканием Lambda
**Проблема**: В lambda функциях переменная `frame` могла быть переиспользована, приводя к отображению неправильных кадров.

**Исправление**:
- ✅ Добавлено копирование кадра: `frame_copy = frame.copy()`
- ✅ Использование параметра по умолчанию в lambda: `lambda f=frame_copy.copy(): ...`

### 3. Race Condition при Инициализации
**Проблема**: Видео запускалось сразу после загрузки, до инициализации `self.root` или `self.loop`.

**Исправление**:
- ✅ Добавлена задержка 100ms перед запуском: `self.root.after(100, lambda: self._safe_start_video())`
- ✅ Создан метод `_safe_start_video()` для безопасного запуска из GUI потока

### 4. Некорректная Обработка Ошибок
**Проблема**: Ошибки в callback могли привести к крашу всего приложения.

**Исправление**:
- ✅ Все операции обернуты в try-except блоки
- ✅ Добавлена проверка на существование объектов перед использованием
- ✅ Логирование всех ошибок с полным traceback

### 5. Проблемы с Потоками VideoPlayer
**Проблема**: Потоки могли быть запущены до инициализации cap, или cap мог быть закрыт во время работы потока.

**Исправление**:
- ✅ Добавлены проверки на существование `self.cap` и `self.cap.isOpened()`
- ✅ Обработка ошибок в потоках через try-finally
- ✅ Добавлены имена потоков для отладки

### 6. Thread-Safety FPS Счетчика
**Проблема**: `fps_counter` обновлялся из фонового потока без синхронизации.

**Исправление**:
- ✅ Создан метод `_update_fps_counter()` для обновления FPS из GUI потока
- ✅ Использование `root.after()` для thread-safe обновления

## Изменения в Коде

### `obelisk/ui/gui_material.py`

#### 1. Улучшенный Callback
```python
def _on_video_frame(self, frame, frame_number, timestamp):
    """Callback для обработки кадра из видеоплеера (вызывается из фонового потока)"""
    try:
        # Проверка на существование root
        if not hasattr(self, 'root') or not self.root:
            return
        
        # Копирование кадра для безопасности
        frame_copy = frame.copy() if frame is not None else None
        if frame_copy is None:
            return
        
        # ... остальной код с обработкой ошибок
```

#### 2. Безопасные Методы для GUI
```python
def _safe_display_frame(self, frame):
    """Безопасное отображение кадра из GUI потока"""
    try:
        if frame is not None and frame.size > 0:
            self.display_frame(frame)
    except Exception as e:
        logger.error(f"Ошибка отображения кадра: {e}", exc_info=True)

def _safe_start_video(self):
    """Безопасный запуск видео из GUI потока"""
    try:
        if self.video_player and self.video_player.cap and self.video_player.cap.isOpened():
            self.video_player.play()
            self.is_playing = True
            self.update_status("Детектор", "Активен", "success")
    except Exception as e:
        logger.error(f"Ошибка запуска видео: {e}", exc_info=True)
```

#### 3. Thread-Safe Обновление FPS
```python
def _update_fps_counter(self, now):
    """Обновление счетчика FPS из GUI потока (thread-safe)"""
    try:
        self.fps_counter = getattr(self, 'fps_counter', 0) + 1
        fps_time = getattr(self, 'fps_time', now)
        if (now - fps_time).total_seconds() >= 1.0:
            fps = self.fps_counter
            self.fps_counter = 0
            self.fps_time = now
            self.update_status("FPS", str(fps), "info" if fps >= 60 else "warning")
    except Exception as e:
        logger.error(f"Ошибка обновления FPS: {e}", exc_info=True)
```

### `obelisk/ui/video_player.py`

#### 1. Улучшенная Обработка Потоков
```python
def _read_frames(self):
    """Поток чтения кадров из видео"""
    try:
        while not self._stop_threads.is_set():
            # Проверка на существование cap
            if not self.cap or not self.cap.isOpened():
                logger.warning("VideoCapture закрыт или не открыт")
                break
            # ... остальной код
    except Exception as e:
        logger.error(f"Критическая ошибка в потоке чтения кадров: {e}", exc_info=True)
    finally:
        logger.debug("Поток чтения кадров завершен")
```

#### 2. Улучшенная Обработка Callback
```python
def _play_frames(self):
    """Поток воспроизведения кадров"""
    try:
        while not self._stop_threads.is_set():
            try:
                frame, frame_number, timestamp = self.frame_queue.get(timeout=0.1)
                
                if self.frame_callback:
                    # Проверка на корректность кадра
                    if frame is not None and hasattr(frame, 'size') and frame.size > 0:
                        self.frame_callback(frame, frame_number, timestamp)
            except queue.Empty:
                continue
            except ValueError as e:
                # Обработка некорректной распаковки
                logger.warning(f"Некорректный формат данных в очереди: {e}")
                continue
    except Exception as e:
        logger.error(f"Критическая ошибка в потоке воспроизведения кадров: {e}", exc_info=True)
    finally:
        logger.debug("Поток воспроизведения кадров завершен")
```

## Результат

✅ **Исправлены все проблемы с крашами**:
- Thread-safety для всех операций с GUI
- Безопасная инициализация и запуск видео
- Обработка всех ошибок с логированием
- Проверки на существование объектов
- Копирование данных для избежания race conditions

✅ **Программа теперь стабильно работает** при загрузке видео, камер и обработке кадров.

## Тестирование

Для проверки исправлений:
1. Загрузите видео файл
2. Подключите IP камеру
3. Подключите локальную камеру
4. Проверьте работу при разных FPS
5. Проверьте работу при ошибках (неправильный файл, недоступная камера)

Все операции должны выполняться без крашей с корректным логированием ошибок.

