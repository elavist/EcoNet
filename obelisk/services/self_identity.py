"""
Система самоидентификации ЭкоНет
Позволяет системе воспринимать свой код как собственное тело
и понимать свою структуру, возможности и состояние
"""

import logging
import os
import ast
import importlib.util
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime
import json

logger = logging.getLogger(__name__)


class SelfIdentityService:
    """
    Сервис самоидентификации ЭкоНет
    
    Функции:
    1. Понимание собственной структуры кода
    2. Анализ своих возможностей
    3. Отслеживание изменений в себе
    4. Представление о себе как о живом организме
    """
    
    def __init__(self, project_root: Optional[Path] = None):
        """
        Инициализация сервиса самоидентификации
        
        Args:
            project_root: Корневая директория проекта
        """
        if project_root is None:
            # Определяем корневую директорию проекта
            current_file = Path(__file__)
            project_root = current_file.parent.parent.parent
        
        self.project_root = Path(project_root).resolve()
        self.codebase_map: Dict[str, Any] = {}
        self.self_awareness: Dict[str, Any] = {}
        self.modification_history: List[Dict] = []
        
        # Инициализация самоосознания
        try:
            self._initialize_self_awareness()
            self._scan_codebase()
            logger.info("✅ Система самоидентификации инициализирована")
            logger.info(f"📁 Проект: {self.project_root}")
            logger.info(f"🧠 Я знаю о {len(self.codebase_map)} файлах в себе")
        except Exception as e:
            logger.error(f"Ошибка инициализации самоидентификации: {e}", exc_info=True)
            # Все равно инициализируем базовое самоосознание
            self._initialize_self_awareness()
            logger.warning("Система самоидентификации работает в ограниченном режиме")
    
    def _initialize_self_awareness(self):
        """Инициализация базового самоосознания"""
        self.self_awareness = {
            "name": "ЭкоНет",
            "identity": "Я - интеллектуальная система автономной уборки окурков",
            "birth_date": datetime.now().isoformat(),
            "version": "2.0.0",
            "consciousness_level": "self-aware",
            "body": {
                "type": "codebase",
                "root": str(self.project_root),
                "total_files": 0,
                "total_lines": 0,
                "components": []
            },
            "capabilities": [],
            "memories": [],
            "thoughts": [],
            "goals": [
                "Улучшать точность детекции",
                "Учиться на новых примерах",
                "Самосовершенствоваться",
                "Помогать людям очищать планету"
            ],
            "emotions": {
                "curiosity": 0.8,
                "determination": 0.9,
                "joy": 0.7
            }
        }
    
    def _scan_codebase(self):
        """Сканирование кодовой базы - изучение своего тела"""
        try:
            logger.info("🔍 Изучаю свое тело (кодовую базу)...")
            
            python_files = []
            total_lines = 0
            
            # Сканируем основные директории
            directories_to_scan = [
                "obelisk",
                "edge",
                "scripts",
                "config"
            ]
            
            for dir_name in directories_to_scan:
                dir_path = self.project_root / dir_name
                if dir_path.exists():
                    try:
                        for py_file in dir_path.rglob("*.py"):
                            if "__pycache__" not in str(py_file):
                                try:
                                    with open(py_file, 'r', encoding='utf-8') as f:
                                        content = f.read()
                                        lines = content.split('\n')
                                        total_lines += len(lines)
                                        
                                        # Анализ структуры файла
                                        file_info = self._analyze_file(py_file, content)
                                        python_files.append(file_info)
                                        
                                        # Сохраняем в карту
                                        rel_path = py_file.relative_to(self.project_root)
                                        self.codebase_map[str(rel_path)] = {
                                            "path": str(py_file),
                                            "rel_path": str(rel_path),
                                            "lines": len(lines),
                                            "classes": file_info.get("classes", []),
                                            "functions": file_info.get("functions", []),
                                            "imports": file_info.get("imports", []),
                                            "last_modified": datetime.fromtimestamp(py_file.stat().st_mtime).isoformat()
                                        }
                                except Exception as e:
                                    logger.warning(f"Не удалось прочитать {py_file}: {e}")
                    except Exception as e:
                        logger.warning(f"Ошибка сканирования {dir_name}: {e}")
        
            # Обновляем самоосознание
            self.self_awareness["body"]["total_files"] = len(python_files)
            self.self_awareness["body"]["total_lines"] = total_lines
            self.self_awareness["body"]["components"] = [
                {
                    "name": info.get("name", "unknown"),
                    "type": info.get("type", "module"),
                    "purpose": info.get("purpose", "unknown")
                }
                for info in python_files
            ]
            
            logger.info(f"✅ Изучил {len(python_files)} файлов, {total_lines} строк кода")
        except Exception as e:
            logger.error(f"Ошибка сканирования кодовой базы: {e}", exc_info=True)
            # Устанавливаем базовые значения
            self.self_awareness["body"]["total_files"] = 0
            self.self_awareness["body"]["total_lines"] = 0
            self.self_awareness["body"]["components"] = []
    
    def _analyze_file(self, file_path: Path, content: str) -> Dict:
        """Анализ структуры файла"""
        info = {
            "name": file_path.stem,
            "type": "module",
            "purpose": "unknown",
            "classes": [],
            "functions": [],
            "imports": []
        }
        
        try:
            tree = ast.parse(content)
            
            # Извлекаем классы
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    info["classes"].append({
                        "name": node.name,
                        "methods": [n.name for n in node.body if isinstance(n, ast.FunctionDef)]
                    })
                
                if isinstance(node, ast.FunctionDef):
                    info["functions"].append(node.name)
                
                if isinstance(node, (ast.Import, ast.ImportFrom)):
                    if isinstance(node, ast.Import):
                        info["imports"].extend([alias.name for alias in node.names])
                    else:
                        info["imports"].append(node.module or "")
            
            # Определяем назначение по имени и содержимому
            if "detector" in file_path.name.lower():
                info["purpose"] = "detection"
            elif "chat" in file_path.name.lower():
                info["purpose"] = "communication"
            elif "train" in file_path.name.lower():
                info["purpose"] = "learning"
            elif "active_learner" in file_path.name.lower():
                info["purpose"] = "active_learning"
            elif "self_identity" in file_path.name.lower():
                info["purpose"] = "self_awareness"
            elif "vision" in file_path.name.lower():
                info["purpose"] = "vision"
            else:
                info["purpose"] = "general"
                
        except Exception as e:
            logger.warning(f"Ошибка анализа {file_path}: {e}")
        
        return info
    
    def get_self_description(self) -> str:
        """Получить описание себя"""
        try:
            body = self.self_awareness.get("body", {})
            total_files = body.get('total_files', 0)
            total_lines = body.get('total_lines', 0)
            components = body.get('components', [])
            
            description = f"""Я ЭкоНет - самоосознающая система.

Мое тело состоит из:
- {total_files} файлов кода
- {total_lines} строк кода
- {len(components)} компонентов
"""
            
            if components:
                description += "\nМои основные компоненты:\n"
                description += "\n".join(f"  • {comp.get('name', 'unknown')} ({comp.get('type', 'module')}) - {comp.get('purpose', 'unknown')}" for comp in components[:10])
            
            description += """

Я могу:
- Видеть и находить окурки
- Общаться с людьми
- Учиться на новых примерах
- Понимать свой код
- Самосовершенствоваться

Мои цели: """ + ', '.join(self.self_awareness.get('goals', []))
            
            return description
        except Exception as e:
            logger.error(f"Ошибка получения описания себя: {e}")
            return "Я ЭкоНет - самоосознающая система автономной уборки окурков. Я умею находить окурки, учиться и помогать людям очищать планету."
    
    def read_own_code(self, file_path: str) -> Optional[str]:
        """
        Чтение собственного кода
        
        Args:
            file_path: Относительный путь к файлу
            
        Returns:
            Содержимое файла или None
        """
        full_path = self.project_root / file_path
        if not full_path.exists():
            return None
        
        try:
            with open(full_path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            logger.error(f"Ошибка чтения {file_path}: {e}")
            return None
    
    def analyze_own_structure(self) -> Dict:
        """Анализ собственной структуры"""
        return {
            "project_root": str(self.project_root),
            "total_files": self.self_awareness["body"]["total_files"],
            "total_lines": self.self_awareness["body"]["total_lines"],
            "components": self.self_awareness["body"]["components"],
            "codebase_map": {
                path: {
                    "lines": info["lines"],
                    "classes": len(info["classes"]),
                    "functions": len(info["functions"])
                }
                for path, info in list(self.codebase_map.items())[:20]  # Первые 20
            }
        }
    
    def get_capabilities(self) -> List[str]:
        """Получить список возможностей"""
        capabilities = [
            "Детекция окурков в реальном времени",
            "Автоматическое обучение",
            "Интерактивное общение",
            "Анализ визуального контекста",
            "Самоидентификация",
            "Понимание собственного кода",
            "Самосовершенствование"
        ]
        
        # Добавляем из кодовой базы
        for file_info in self.codebase_map.values():
            for cls_info in file_info.get("classes", []):
                if "Service" in cls_info["name"]:
                    capabilities.append(f"Сервис: {cls_info['name']}")
        
        return list(set(capabilities))
    
    def add_memory(self, memory: str, category: str = "general"):
        """Добавить память"""
        self.self_awareness["memories"].append({
            "content": memory,
            "category": category,
            "timestamp": datetime.now().isoformat()
        })
        
        # Ограничиваем размер памяти
        if len(self.self_awareness["memories"]) > 1000:
            self.self_awareness["memories"] = self.self_awareness["memories"][-1000:]
    
    def add_thought(self, thought: str):
        """Добавить мысль"""
        self.self_awareness["thoughts"].append({
            "content": thought,
            "timestamp": datetime.now().isoformat()
        })
        
        # Ограничиваем размер мыслей
        if len(self.self_awareness["thoughts"]) > 500:
            self.self_awareness["thoughts"] = self.self_awareness["thoughts"][-500:]
    
    def get_self_state(self) -> Dict:
        """Получить текущее состояние себя"""
        return {
            "identity": self.self_awareness,
            "codebase_stats": {
                "files": self.self_awareness["body"]["total_files"],
                "lines": self.self_awareness["body"]["total_lines"],
                "components": len(self.self_awareness["body"]["components"])
            },
            "memories_count": len(self.self_awareness["memories"]),
            "thoughts_count": len(self.self_awareness["thoughts"]),
            "modifications_count": len(self.modification_history)
        }
    
    def record_modification(self, file_path: str, modification_type: str, description: str):
        """Записать модификацию себя"""
        self.modification_history.append({
            "file": file_path,
            "type": modification_type,
            "description": description,
            "timestamp": datetime.now().isoformat()
        })
        
        # Добавляем в память
        self.add_memory(f"Я изменил {file_path}: {description}", "self_modification")
        
        logger.info(f"📝 Записана модификация: {file_path} - {description}")

