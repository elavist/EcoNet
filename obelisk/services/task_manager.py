"""
Менеджер задач для распределения задач между роботами в рое
Улучшенная логика координации для автономной системы очистки от мусора

Поддерживает два режима назначения:
  1. Классический (расстояние + оценка робота)
  2. Полевой       (через FieldScheduler на основе градиентов эффективности)
"""

import asyncio
import logging
from typing import Dict, List, Optional, Tuple, TYPE_CHECKING
from datetime import datetime, timedelta
import uuid
import math

if TYPE_CHECKING:
    from obelisk.swarm.field_scheduler import FieldScheduler

logger = logging.getLogger(__name__)


class TaskManager:
    """Менеджер задач для распределения задач между роботами в рое"""
    
    def __init__(self, config: Dict, database, mqtt_client):
        """
        Инициализация менеджера задач
        
        Args:
            config: Конфигурация системы
            database: База данных для хранения задач
            mqtt_client: MQTT клиент для коммуникации
        """
        self.config = config
        self.mqtt_client = mqtt_client
        self.db = database
        self.tasks: Dict[str, Dict] = {}
        self.robots: Dict[str, Dict] = {}  # Регистр роботов роя
        self.running = False
        self.loop_task = None
        
        # Полевой планировщик (устанавливается через set_field_scheduler)
        self._field_scheduler: Optional["FieldScheduler"] = None
        self._use_field_scheduling = config.get("swarm_field", {}).get("enabled", False)
        
        # Настройки роя
        swarm_config = config.get("robots", {}).get("swarm", {})
        self.max_task_distance = swarm_config.get("max_task_distance", 100.0)  # Максимальное расстояние для задачи
        self.task_timeout_base = swarm_config.get("task_timeout_base", 300)  # Базовый таймаут задачи
        self.priority_weights = {
            "urgent": 5.0,  # Высокий приоритет (например, много мусора в одном месте)
            "high": 3.0,    # Высокий приоритет (одна детекция)
            "normal": 1.0,  # Обычный приоритет
            "low": 0.5      # Низкий приоритет
        }
        
        # Подписка на MQTT события (только если mqtt_client доступен)
        if self.mqtt_client:
            try:
                self.mqtt_client.subscribe("obelisk/detection", self._on_detection)
                self.mqtt_client.subscribe("robots/+/status", self._on_robot_status)
                self.mqtt_client.subscribe("obelisk/tasks/completed", self._on_task_completed)
                self.mqtt_client.subscribe("obelisk/tasks/failed", self._on_task_failed)
            except Exception as e:
                logger.warning(f"Ошибка подписки на MQTT топики: {e}")
    
    def set_field_scheduler(self, scheduler: "FieldScheduler"):
        """Подключить полевой планировщик для градиентного назначения задач."""
        self._field_scheduler = scheduler
        self._use_field_scheduling = True
        logger.info("TaskManager: полевой планировщик подключён")

    async def start(self):
        """Запуск менеджера задач"""
        self.running = True
        self.loop_task = asyncio.create_task(self._task_loop())
        logger.info("Менеджер задач запущен")
    
    async def stop(self):
        """Остановка менеджера задач"""
        self.running = False
        if self.loop_task:
            self.loop_task.cancel()
            try:
                await self.loop_task
            except asyncio.CancelledError:
                pass
        logger.info("Менеджер задач остановлен")
    
    async def _task_loop(self):
        """Главный цикл обработки задач"""
        while self.running:
            try:
                # Проверка просроченных задач
                await self._check_timeouts()
                
                # Назначение задач доступным роботам
                await self._assign_tasks()
                
                await asyncio.sleep(1)  # Проверка каждую секунду
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Ошибка в task loop: {e}")
                await asyncio.sleep(5)
    
    async def create_task(self, task_data: Dict) -> Dict:
        """
        Создание новой задачи
        
        Args:
            task_data: Данные задачи
            
        Returns:
            Созданная задача с ID
        """
        task_id = f"task_{uuid.uuid4().hex[:8]}"
        
        task = {
            "task_id": task_id,
            "type": task_data.get("type", "collect"),
            "status": "pending",
            "target": task_data.get("target", {}),
            "priority": task_data.get("priority", 1),
            "assigned_to": None,
            "created_at": datetime.utcnow().isoformat(),
            "started_at": None,
            "completed_at": None,
            "timeout": task_data.get("timeout", 300)
        }
        
        self.tasks[task_id] = task
        
        # Сохранить в БД
        await self.db.save_task(task)
        
        # Опубликовать задачу
        await self.mqtt_client.publish("obelisk/tasks", task)
        
        # Дублируем в полевой планировщик для градиентного назначения
        if self._field_scheduler and self._use_field_scheduling:
            self._field_scheduler.submit_task(
                task_id,
                task_type=task.get("type", "collect"),
                priority=task.get("priority", 1),
                payload=task,
            )
        
        logger.info(f"Создана задача {task_id}")
        return task
    
    async def _on_detection(self, topic: str, payload: Dict):
        """Обработчик детекции"""
        try:
            # Создать задачу на сбор при обнаружении окурка
            if payload.get('confidence', 0) > 0.5:  # Порог уверенности
                task_data = {
                    "type": "collect",
                    "target": {
                        "bbox": payload.get("bbox", []),
                        "location": payload.get("location", []),
                        "frame": payload.get("frame_id")
                    },
                    "priority": 2,
                    "timeout": 300
                }
                
                await self.create_task(task_data)
                
        except Exception as e:
            logger.error(f"Ошибка обработки детекции: {e}")
    
    async def _on_robot_status(self, topic: str, payload: Dict):
        """Обработчик статуса робота"""
        robot_id = payload.get("robot_id")
        state = payload.get("state")
        
        # Если робот освободился, можно назначить ему задачу
        if state == "idle":
            await self._assign_tasks()
    
    async def _on_task_completed(self, topic: str, payload: Dict):
        """Обработчик завершения задачи"""
        task_id = payload.get("task_id")
        if task_id in self.tasks:
            self.tasks[task_id]["status"] = "completed"
            self.tasks[task_id]["completed_at"] = datetime.utcnow().isoformat()
            await self.db.update_task(task_id, self.tasks[task_id])
            if self._field_scheduler:
                self._field_scheduler.complete_task(task_id)
    
    async def _on_task_failed(self, topic: str, payload: Dict):
        """Обработчик ошибки задачи"""
        task_id = payload.get("task_id")
        if task_id in self.tasks:
            self.tasks[task_id]["status"] = "failed"
            # Попытаться переназначить
            self.tasks[task_id]["assigned_to"] = None
            await self.db.update_task(task_id, self.tasks[task_id])
            if self._field_scheduler:
                self._field_scheduler.fail_task(task_id)
    
    async def _check_timeouts(self):
        """Проверка просроченных задач"""
        now = datetime.utcnow()
        
        for task_id, task in list(self.tasks.items()):
            if task["status"] in ["pending", "assigned", "in_progress"]:
                created_at = datetime.fromisoformat(task["created_at"])
                timeout = timedelta(seconds=task["timeout"])
                
                if now - created_at > timeout:
                    task["status"] = "failed"
                    task["assigned_to"] = None
                    await self.db.update_task(task_id, task)
                    logger.warning(f"Задача {task_id} просрочена")
    
    async def _assign_tasks(self):
        """Улучшенное назначение задач доступным роботам с учетом расстояния и загрузки"""
        # Получить доступных роботов из регистра
        available_robots = [
            robot for robot in self.robots.values()
            if robot.get("state") == "idle" and robot.get("battery", 100) > 20
        ]
        
        # Если роботов нет в регистре, попробуем получить из БД
        if not available_robots and self.db:
            try:
                db_robots = await self.db.get_available_robots()
                # Обновляем регистр роботов из БД
                for robot in db_robots:
                    self.robots[robot.get("robot_id", "")] = robot
                available_robots = [
                    robot for robot in self.robots.values()
                    if robot.get("state") == "idle" and robot.get("battery", 100) > 20
                ]
            except Exception as e:
                logger.warning(f"Ошибка получения роботов из БД: {e}")
        
        if not available_robots:
            logger.debug("Нет доступных роботов для назначения задач")
            return
        
        # Получить ожидающие задачи, отсортированные по приоритету
        pending_tasks = [
            task for task in self.tasks.values()
            if task["status"] == "pending"
        ]
        
        # Сортировка задач по приоритету и времени создания
        pending_tasks.sort(key=lambda t: (
            self.priority_weights.get(t.get("priority_type", "normal"), 1.0) * t.get("priority", 1),
            -datetime.fromisoformat(t["created_at"]).timestamp()  # Новые задачи в первую очередь
        ), reverse=True)
        
        # Назначить задачи с учетом расстояния и загрузки
        assigned_robots = set()
        for task in pending_tasks:
            if not available_robots:
                break
            
            # Выбрать оптимального робота по расстоянию и загрузке
            best_robot = self._select_best_robot(task, available_robots, assigned_robots)
            
            if best_robot:
                task["status"] = "assigned"
                task["assigned_to"] = best_robot["robot_id"]
                task["started_at"] = datetime.utcnow().isoformat()
                
                # Обновление статуса робота
                best_robot["state"] = "moving"
                self.robots[best_robot["robot_id"]] = best_robot
                assigned_robots.add(best_robot["robot_id"])
                
                # Сохранение в БД
                if self.db:
                    try:
                        await self.db.update_task(task["task_id"], task)
                    except Exception as e:
                        logger.warning(f"Ошибка сохранения задачи в БД: {e}")
                
                # Отправка задачи роботу через MQTT
                if self.mqtt_client:
                    try:
                        await self.mqtt_client.publish(
                            f"robots/{best_robot['robot_id']}/tasks",
                            task
                        )
                        logger.info(f"✅ Задача {task['task_id']} назначена роботу {best_robot['robot_id']} "
                                  f"(расстояние: {best_robot.get('distance_to_task', 'N/A'):.2f}м)")
                    except Exception as e:
                        logger.error(f"Ошибка отправки задачи роботу: {e}")
    
    def _select_best_robot(self, task: Dict, available_robots: List[Dict], assigned_robots: set) -> Optional[Dict]:
        """
        Выбор оптимального робота для задачи на основе расстояния, загрузки и приоритета
        
        Args:
            task: Задача для выполнения
            available_robots: Список доступных роботов
            assigned_robots: Множество уже назначенных роботов
        
        Returns:
            Оптимальный робот или None
        """
        task_location = task.get("target", {}).get("location", [])
        
        if not task_location or len(task_location) < 2:
            # Если локация не указана, выбираем первого свободного
            for robot in available_robots:
                if robot["robot_id"] not in assigned_robots:
                    robot["distance_to_task"] = 0.0
                    return robot
            return None
        
        # Вычисление расстояний и оценок для каждого робота
        robot_scores = []
        
        for robot in available_robots:
            if robot["robot_id"] in assigned_robots:
                continue
            
            robot_position = robot.get("position", [0.0, 0.0])
            
            # Вычисление расстояния до задачи (евклидово расстояние)
            if len(robot_position) >= 2 and len(task_location) >= 2:
                distance = math.sqrt(
                    (robot_position[0] - task_location[0])**2 +
                    (robot_position[1] - task_location[1])**2
                )
            else:
                distance = float('inf')
            
            # Проверка максимального расстояния
            if distance > self.max_task_distance:
                continue
            
            # Улучшенная оценка робота на основе множества факторов для автономной системы роя
            battery = robot.get("battery", 100)
            current_tasks = robot.get("current_tasks_count", 0)
            robot_type = robot.get("type", "collector")
            efficiency = robot.get("efficiency", 1.0)  # Коэффициент эффективности робота
            last_maintenance = robot.get("last_maintenance_hours", 0)
            task_priority = task.get("priority", "normal")
            
            # 1. Расстояние (чем ближе, тем лучше) - вес 0.5
            # Логарифмическая нормализация для сглаживания больших расстояний
            distance_score = 1.0 / (1.0 + math.log(1.0 + distance / 10.0))
            
            # 2. Батарея (чем больше, тем лучше) - вес 0.25
            # Квадратичная функция для приоритета высокого заряда
            battery_normalized = battery / 100.0
            battery_score = battery_normalized ** 1.5  # Приоритет более заряженным
            
            # 3. Загрузка (чем меньше задач, тем лучше) - вес 0.1
            # Экспоненциальное снижение при увеличении нагрузки
            load_score = math.exp(-current_tasks / 2.0)
            
            # 4. Эффективность робота - вес 0.1
            # Учитывает историческую производительность
            efficiency_score = min(efficiency, 1.5) / 1.5  # Ограничение сверху
            
            # 5. Время с последнего обслуживания - вес 0.05
            # Предпочтение роботам, которые недавно обслуживались
            maintenance_score = math.exp(-last_maintenance / 168.0)  # 168 часов = неделя
            
            # 6. Приоритет задачи влияет на веса
            # Для срочных задач приоритет расстоянию и эффективности
            if task_priority == "urgent":
                weights = {
                    'distance': 0.6,
                    'battery': 0.2,
                    'load': 0.05,
                    'efficiency': 0.15,
                    'maintenance': 0.0
                }
            else:
                weights = {
                    'distance': 0.5,
                    'battery': 0.25,
                    'load': 0.1,
                    'efficiency': 0.1,
                    'maintenance': 0.05
                }
            
            # Итоговая взвешенная оценка
            total_score = (
                weights['distance'] * distance_score +
                weights['battery'] * battery_score +
                weights['load'] * load_score +
                weights['efficiency'] * efficiency_score +
                weights['maintenance'] * maintenance_score
            )
            
            # Штраф за низкую батарею (критический фактор)
            if battery < 20:
                total_score *= 0.1  # Сильное снижение при низкой батарее
            elif battery < 50:
                total_score *= 0.7  # Умеренное снижение
            
            robot["distance_to_task"] = distance
            robot["score"] = total_score
            robot_scores.append((total_score, robot))
        
        if not robot_scores:
            return None
        
        # Выбор робота с максимальной оценкой
        robot_scores.sort(key=lambda x: x[0], reverse=True)
        return robot_scores[0][1]
    
    async def get_tasks(self, status: Optional[str] = None, assigned_to: Optional[str] = None, 
                       limit: int = 100, offset: int = 0) -> List[Dict]:
        """Получить список задач"""
        tasks = list(self.tasks.values())
        
        if status:
            tasks = [t for t in tasks if t["status"] == status]
        if assigned_to:
            tasks = [t for t in tasks if t["assigned_to"] == assigned_to]
        
        # Сортировка по времени создания
        tasks.sort(key=lambda t: t["created_at"], reverse=True)
        
        return tasks[offset:offset+limit]
    
    async def get_task(self, task_id: str) -> Optional[Dict]:
        """Получить задачу по ID"""
        return self.tasks.get(task_id)
    
    async def cancel_task(self, task_id: str) -> bool:
        """Отменить задачу"""
        if task_id in self.tasks:
            task = self.tasks[task_id]
            task["status"] = "cancelled"
            await self.db.update_task(task_id, task)
            return True
        return False
    
    def is_running(self) -> bool:
        """Проверка работы менеджера"""
        return self.running


