"""
Упрощенная и надежная система отображения видео
Без сложной многопоточности - простой и стабильный подход
"""

import cv2
import threading
import queue
import time
import logging
from pathlib import Path
from typing import Optional, Callable
import numpy as np

logger = logging.getLogger(__name__)


class SimpleVideoDisplay:
    """
    Упрощенный видеоплеер без сложной многопоточности
    Использует простой подход: чтение кадров в отдельном потоке,
    отображение через callback в GUI потоке
    """
    
    def __init__(self, frame_callback: Optional[Callable] = None):
        """
        Инициализация простого видеоплеера
        
        Args:
            frame_callback: Функция для обработки кадров (frame) -> None
        """
        self.cap: Optional[cv2.VideoCapture] = None
        self.source_path: Optional[str] = None
        self.frame_callback = frame_callback
        
        # Управление
        self.is_running = False
        self.is_paused = False
        self.read_thread: Optional[threading.Thread] = None
        self.stop_event = threading.Event()
        
        # Свойства видео
        self.fps = 30.0
        self.total_frames = 0
        self.current_frame_number = 0
        
        logger.info("✅ SimpleVideoDisplay инициализирован")
    
    def load_video(self, source: str) -> bool:
        """
        Загрузка видео (надежная и неблокирующая)
        
        Args:
            source: Путь к файлу, URL или индекс камеры
            
        Returns:
            True если успешно
        """
        try:
            # Остановка предыдущего видео (безопасно)
            try:
                self.stop()
            except Exception:
                pass
            
            logger.info(f"📁 Загрузка видео: {source}")
            
            # Определение типа источника
            cap = None
            source_type = "unknown"
            
            try:
                import sys as _sys
                _is_win = _sys.platform == "win32"

                if isinstance(source, int) or (isinstance(source, str) and source.isdigit()):
                    cam_idx = int(source)
                    source_type = "camera"
                    self.source_path = f"Camera {cam_idx}"

                    backends = [cv2.CAP_DSHOW, cv2.CAP_MSMF, cv2.CAP_ANY] if _is_win else [cv2.CAP_ANY]
                    for backend in backends:
                        cap = cv2.VideoCapture(cam_idx, backend)
                        if cap is not None and cap.isOpened():
                            ret, test_frame = cap.read()
                            if ret and test_frame is not None:
                                logger.info(f"✅ Камера открыта через backend {backend}")
                                break
                            cap.release()
                        elif cap is not None:
                            cap.release()
                        cap = None
                    
                    if cap is None:
                        logger.error(f"❌ Не удалось открыть камеру {cam_idx} ни одним backend")
                        return False

                elif isinstance(source, str) and source.startswith(("http://", "https://", "rtsp://", "rtmp://")):
                    cap = cv2.VideoCapture(source)
                    source_type = "stream"
                    self.source_path = source
                else:
                    path = Path(source)
                    if not path.exists():
                        logger.error(f"❌ Файл не найден: {source}")
                        return False
                    if not path.is_file():
                        logger.error(f"❌ Это не файл: {source}")
                        return False
                    cap = cv2.VideoCapture(str(path))
                    source_type = "file"
                    self.source_path = str(path)
                
                if cap is None:
                    logger.error(f"❌ Не удалось создать VideoCapture для: {source}")
                    return False
                
                cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
                if source_type in ("camera", "stream"):
                    cap.set(cv2.CAP_PROP_FPS, 60)
                    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
                    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
                
                if source_type != "camera":
                    ret, test_frame = cap.read()
                    if not ret or test_frame is None:
                        logger.error(f"❌ Не удалось прочитать первый кадр из: {source}")
                        cap.release()
                        return False
                
                # Сохраняем успешно открытый VideoCapture
                self.cap = cap
                
                # Получение свойств (с обработкой ошибок)
                try:
                    self.fps = cap.get(cv2.CAP_PROP_FPS)
                    if self.fps is None or self.fps <= 0:
                        self.fps = 30.0
                    
                    self.total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT)) if cap.get(cv2.CAP_PROP_FRAME_COUNT) > 0 else 0
                    if self.total_frames == 0:
                        self.total_frames = -1  # Поток или неизвестно
                except Exception as e:
                    logger.warning(f"Не удалось получить свойства видео: {e}")
                    self.fps = 30.0
                    self.total_frames = -1
                
                # Сброс на начало для камер и файлов
                if source_type == "file":
                    try:
                        cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                    except Exception:
                        pass
                
                self.current_frame_number = 0
                logger.info(f"✅ Видео загружено ({source_type}): FPS={self.fps:.2f}, Frames={self.total_frames}")
                return True
                
            except Exception as e:
                # Освобождение ресурсов при ошибке
                if cap:
                    try:
                        cap.release()
                    except Exception:
                        pass
                logger.error(f"❌ Ошибка создания VideoCapture: {e}", exc_info=True)
                return False
            
        except Exception as e:
            logger.error(f"❌ Критическая ошибка загрузки видео: {e}", exc_info=True)
            # Очистка состояния
            self.cap = None
            self.source_path = None
            return False
    
    def start(self):
        """Запуск воспроизведения"""
        if not self.cap or not self.cap.isOpened():
            logger.warning("Видео не загружено")
            return False
        
        if self.is_running:
            return True
        
        self.is_running = True
        self.is_paused = False
        self.stop_event.clear()
        
        # Запуск потока чтения
        if not self.read_thread or not self.read_thread.is_alive():
            self.read_thread = threading.Thread(target=self._read_loop, daemon=True)
            self.read_thread.start()
        
        logger.info("▶️ Воспроизведение запущено")
        return True
    
    def pause(self):
        """Пауза"""
        self.is_paused = True
        logger.info("⏸️ Пауза")
    
    def resume(self):
        """Возобновление"""
        self.is_paused = False
        logger.info("▶️ Возобновление")
    
    def stop(self):
        """Остановка"""
        self.is_running = False
        self.is_paused = False
        self.stop_event.set()
        
        # Ожидание завершения потока
        if self.read_thread and self.read_thread.is_alive():
            self.read_thread.join(timeout=1.0)
        
        # Закрытие видео
        if self.cap:
            try:
                self.cap.release()
            except Exception:
                pass
            self.cap = None
        
        logger.info("⏹️ Остановлено")
    
    def _read_loop(self):
        """Поток чтения кадров (простой и надежный, с защитой от крашей)"""
        try:
            # УБРАНО: frame_time - больше не ограничиваем скорость воспроизведения
            last_time = time.time()
            error_count = 0
            max_errors = 10  # Максимум ошибок подряд
            
            while self.is_running and not self.stop_event.is_set():
                if self.is_paused:
                    time.sleep(0.1)
                    continue
                
                if not self.cap:
                    break
                
                try:
                    # Проверка открытости (неблокирующая)
                    if not self.cap.isOpened():
                        logger.warning("VideoCapture закрыт")
                        break
                    
                    # Чтение кадра (может блокировать, но ненадолго)
                    ret, frame = self.cap.read()
                    
                    if not ret or frame is None:
                        # Конец видео или ошибка
                        logger.debug("Конец видео или ошибка чтения")
                        break
                    
                    # Вызов callback для отображения (с защитой от ошибок)
                    if self.frame_callback:
                        try:
                            # Копируем кадр для безопасности
                            frame_copy = frame.copy()
                            if frame_copy.size > 0:
                                logger.debug(f"📹 Отправка кадра в callback: {frame_copy.shape}")
                                self.frame_callback(frame_copy)
                                error_count = 0  # Сброс счетчика ошибок при успехе
                            else:
                                logger.warning("⚠️ Пустой кадр, пропускаем")
                        except Exception as e:
                            error_count += 1
                            logger.error(f"❌ Ошибка в callback ({error_count}/{max_errors}): {e}", exc_info=True)
                            if error_count >= max_errors:
                                logger.error("❌ Слишком много ошибок в callback, останавливаем чтение")
                                break
                    else:
                        logger.warning("⚠️ frame_callback не установлен")
                    
                    self.current_frame_number += 1
                    
                    # УБРАНО: Контроль скорости - воспроизведение без ограничений FPS
                    # Видео будет воспроизводиться с максимальной скоростью обработки
                    last_time = time.time()
                    
                except Exception as e:
                    error_count += 1
                    logger.error(f"Ошибка чтения кадра ({error_count}/{max_errors}): {e}", exc_info=True)
                    if error_count >= max_errors:
                        logger.error("Слишком много ошибок, останавливаем чтение")
                        break
                    time.sleep(0.1)  # Небольшая задержка при ошибке
                    
        except Exception as e:
            logger.error(f"Критическая ошибка в потоке чтения: {e}", exc_info=True)
        finally:
            logger.debug("Поток чтения завершен")
            self.is_running = False
    
    def get_stats(self) -> dict:
        """Получить статистику"""
        return {
            "fps": self.fps,
            "total_frames": self.total_frames,
            "current_frame": self.current_frame_number,
            "is_running": self.is_running,
            "is_paused": self.is_paused
        }
    
    def release(self):
        """Освобождение ресурсов"""
        self.stop()

