"""
База данных для хранения данных системы
"""

import sqlite3
import aiosqlite
import json
import logging
from typing import Dict, List, Optional
from pathlib import Path
from datetime import datetime

logger = logging.getLogger(__name__)


class Database:
    """База данных для Обелиска"""
    
    def __init__(self, config: Dict):
        """
        Инициализация базы данных
        
        Args:
            config: Конфигурация БД
        """
        self.config = config
        self.db_path = None
        self.connection = None
        
        if config.get("type") == "sqlite":
            db_dir = Path(config["sqlite_path"]).parent
            db_dir.mkdir(parents=True, exist_ok=True)
            self.db_path = config["sqlite_path"]
    
    async def init(self):
        """Инициализация БД и создание таблиц"""
        if self.config.get("type") == "sqlite":
            self.connection = await aiosqlite.connect(self.db_path)
            self.connection.row_factory = aiosqlite.Row
            await self._create_tables()
            logger.info(f"База данных SQLite инициализирована: {self.db_path}")
        else:
            # TODO: PostgreSQL support
            raise NotImplementedError("PostgreSQL not implemented yet")
    
    async def close(self):
        """Закрытие соединения с БД"""
        if self.connection:
            await self.connection.close()
            logger.info("Соединение с БД закрыто")
    
    async def _create_tables(self):
        """Создание таблиц"""
        async with self.connection.cursor() as cursor:
            # Таблица детекций
            await cursor.execute("""
                CREATE TABLE IF NOT EXISTS detections (
                    id TEXT PRIMARY KEY,
                    source TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    bbox TEXT NOT NULL,
                    class_name TEXT NOT NULL,
                    confidence REAL NOT NULL,
                    frame_id TEXT,
                    location TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Таблица задач
            await cursor.execute("""
                CREATE TABLE IF NOT EXISTS tasks (
                    task_id TEXT PRIMARY KEY,
                    type TEXT NOT NULL,
                    status TEXT NOT NULL,
                    target TEXT NOT NULL,
                    priority INTEGER NOT NULL,
                    assigned_to TEXT,
                    created_at TEXT NOT NULL,
                    started_at TEXT,
                    completed_at TEXT,
                    timeout INTEGER NOT NULL
                )
            """)
            
            # Таблица роботов
            await cursor.execute("""
                CREATE TABLE IF NOT EXISTS robots (
                    robot_id TEXT PRIMARY KEY,
                    state TEXT NOT NULL,
                    battery INTEGER NOT NULL,
                    position TEXT NOT NULL,
                    current_task TEXT,
                    last_heartbeat TEXT NOT NULL,
                    capabilities TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Таблица моделей
            await cursor.execute("""
                CREATE TABLE IF NOT EXISTS models (
                    model_id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    version TEXT NOT NULL,
                    path TEXT NOT NULL,
                    map REAL,
                    precision REAL,
                    recall REAL,
                    is_active INTEGER DEFAULT 0,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    deployed_at TEXT
                )
            """)
            
            await self.connection.commit()
    
    async def save_detection(self, detection: Dict) -> str:
        """Сохранение детекции"""
        import uuid
        detection_id = f"det_{uuid.uuid4().hex[:8]}"
        
        async with self.connection.cursor() as cursor:
            await cursor.execute("""
                INSERT INTO detections 
                (id, source, timestamp, bbox, class_name, confidence, frame_id, location)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                detection_id,
                detection.get("source"),
                datetime.utcnow().isoformat(),
                json.dumps(detection.get("bbox", [])),
                detection.get("class_name"),
                detection.get("confidence"),
                detection.get("frame_id"),
                json.dumps(detection.get("location", [])) if detection.get("location") else None
            ))
            await self.connection.commit()
        
        return detection_id
    
    async def get_detections(self, limit: int = 100, offset: int = 0,
                           source: Optional[str] = None,
                           min_confidence: Optional[float] = None) -> List[Dict]:
        """Получить детекции"""
        query = "SELECT * FROM detections WHERE 1=1"
        params = []
        
        if source:
            query += " AND source = ?"
            params.append(source)
        if min_confidence is not None:
            query += " AND confidence >= ?"
            params.append(min_confidence)
        
        query += " ORDER BY timestamp DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])
        
        async with self.connection.cursor() as cursor:
            await cursor.execute(query, params)
            rows = await cursor.fetchall()
            
            return [{
                "id": row["id"],
                "source": row["source"],
                "timestamp": row["timestamp"],
                "bbox": json.loads(row["bbox"]),
                "class_name": row["class_name"],
                "confidence": row["confidence"],
                "frame_id": row["frame_id"],
                "location": json.loads(row["location"]) if row["location"] else None
            } for row in rows]
    
    async def get_detection(self, detection_id: str) -> Optional[Dict]:
        """Получить детекцию по ID"""
        async with self.connection.cursor() as cursor:
            await cursor.execute("SELECT * FROM detections WHERE id = ?", (detection_id,))
            row = await cursor.fetchone()
            
            if row:
                return {
                    "id": row["id"],
                    "source": row["source"],
                    "timestamp": row["timestamp"],
                    "bbox": json.loads(row["bbox"]),
                    "class_name": row["class_name"],
                    "confidence": row["confidence"],
                    "frame_id": row["frame_id"],
                    "location": json.loads(row["location"]) if row["location"] else None
                }
            return None
    
    async def save_task(self, task: Dict):
        """Сохранение задачи"""
        async with self.connection.cursor() as cursor:
            await cursor.execute("""
                INSERT OR REPLACE INTO tasks
                (task_id, type, status, target, priority, assigned_to, 
                 created_at, started_at, completed_at, timeout)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                task["task_id"],
                task["type"],
                task["status"],
                json.dumps(task["target"]),
                task["priority"],
                task.get("assigned_to"),
                task["created_at"],
                task.get("started_at"),
                task.get("completed_at"),
                task["timeout"]
            ))
            await self.connection.commit()
    
    async def update_task(self, task_id: str, task: Dict):
        """Обновление задачи"""
        async with self.connection.cursor() as cursor:
            await cursor.execute("""
                UPDATE tasks SET
                    status = ?, assigned_to = ?, started_at = ?, completed_at = ?
                WHERE task_id = ?
            """, (
                task["status"],
                task.get("assigned_to"),
                task.get("started_at"),
                task.get("completed_at"),
                task_id
            ))
            await self.connection.commit()
    
    async def get_robots(self) -> List[Dict]:
        """Получить список роботов"""
        async with self.connection.cursor() as cursor:
            await cursor.execute("SELECT * FROM robots")
            rows = await cursor.fetchall()
            
            return [{
                "robot_id": row["robot_id"],
                "state": row["state"],
                "battery": row["battery"],
                "position": json.loads(row["position"]),
                "current_task": row["current_task"],
                "last_heartbeat": row["last_heartbeat"],
                "capabilities": json.loads(row["capabilities"]) if row["capabilities"] else []
            } for row in rows]
    
    async def get_robot(self, robot_id: str) -> Optional[Dict]:
        """Получить робота по ID"""
        async with self.connection.cursor() as cursor:
            await cursor.execute("SELECT * FROM robots WHERE robot_id = ?", (robot_id,))
            row = await cursor.fetchone()
            
            if row:
                return {
                    "robot_id": row["robot_id"],
                    "state": row["state"],
                    "battery": row["battery"],
                    "position": json.loads(row["position"]),
                    "current_task": row["current_task"],
                    "last_heartbeat": row["last_heartbeat"],
                    "capabilities": json.loads(row["capabilities"]) if row["capabilities"] else []
                }
            return None
    
    async def get_available_robots(self) -> List[Dict]:
        """Получить доступных роботов (idle, battery > 20%)"""
        async with self.connection.cursor() as cursor:
            await cursor.execute("""
                SELECT * FROM robots 
                WHERE state = 'idle' AND battery > 20
            """)
            rows = await cursor.fetchall()
            
            return [{
                "robot_id": row["robot_id"],
                "state": row["state"],
                "battery": row["battery"],
                "position": json.loads(row["position"]),
                "current_task": row["current_task"]
            } for row in rows]
    
    async def get_robot_telemetry(self, robot_id: str) -> Optional[Dict]:
        """Получить телеметрию робота"""
        robot = await self.get_robot(robot_id)
        if robot:
            return {
                "robot_id": robot["robot_id"],
                "state": robot["state"],
                "battery": robot["battery"],
                "position": robot["position"],
                "velocity": None,  # TODO: добавить в таблицу
                "sensors": {}  # TODO: добавить в таблицу
            }
        return None
    
    async def get_models(self) -> List[Dict]:
        """Получить список моделей"""
        async with self.connection.cursor() as cursor:
            await cursor.execute("SELECT * FROM models ORDER BY created_at DESC")
            rows = await cursor.fetchall()
            
            return [{
                "model_id": row["model_id"],
                "name": row["name"],
                "version": row["version"],
                "path": row["path"],
                "mAP": row["map"],
                "precision": row["precision"],
                "recall": row["recall"],
                "is_active": bool(row["is_active"]),
                "created_at": row["created_at"],
                "deployed_at": row["deployed_at"]
            } for row in rows]
    
    async def get_active_model(self) -> Optional[Dict]:
        """Получить активную модель"""
        async with self.connection.cursor() as cursor:
            await cursor.execute("SELECT * FROM models WHERE is_active = 1 LIMIT 1")
            row = await cursor.fetchone()
            
            if row:
                return {
                    "model_id": row["model_id"],
                    "name": row["name"],
                    "version": row["version"],
                    "path": row["path"],
                    "mAP": row["map"],
                    "precision": row["precision"],
                    "recall": row["recall"],
                    "is_active": True,
                    "created_at": row["created_at"],
                    "deployed_at": row["deployed_at"]
                }
            return None
    
    async def get_system_statistics(self) -> Dict:
        """Получить статистику системы"""
        async with self.connection.cursor() as cursor:
            stats = {}
            
            # Количество детекций
            await cursor.execute("SELECT COUNT(*) as count FROM detections")
            stats["total_detections"] = (await cursor.fetchone())["count"]
            
            # Количество задач
            await cursor.execute("SELECT COUNT(*) as count FROM tasks")
            stats["total_tasks"] = (await cursor.fetchone())["count"]
            
            # Количество роботов
            await cursor.execute("SELECT COUNT(*) as count FROM robots")
            stats["total_robots"] = (await cursor.fetchone())["count"]
            
            # Активные задачи
            await cursor.execute("""
                SELECT COUNT(*) as count FROM tasks 
                WHERE status IN ('pending', 'assigned', 'in_progress')
            """)
            stats["active_tasks"] = (await cursor.fetchone())["count"]
            
            return stats
    
    def is_connected(self) -> bool:
        """Проверка подключения"""
        return self.connection is not None


