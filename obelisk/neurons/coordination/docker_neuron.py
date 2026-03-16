"""
Нейрон управления Docker контейнерами ЭкоНет
Управление жизненным циклом контейнеров
"""

import logging
import subprocess
import json
from typing import Dict, Any, List, Optional
from datetime import datetime

from obelisk.core.neural_nodes import NeuralNode
from obelisk.core.neural_sync import ComponentState

logger = logging.getLogger(__name__)


class DockerNeuron(NeuralNode):
    """
    Нейрон управления Docker - управление контейнерами
    """
    
    def __init__(self):
        """
        Инициализация DockerNeuron
        """
        super().__init__("docker_neuron", "coordination")
        self.containers_status = {}
        self.containers_history = []
        self.state = ComponentState.READY
        
        logger.info("🐳 DockerNeuron создан")
    
    async def think(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Процесс мышления нейрона Docker"""
        action = context.get("action", "status")
        
        try:
            if action == "status":
                status = await self._get_containers_status()
                return {
                    "action": "status",
                    "containers": status,
                    "confidence": 1.0
                }
            
            elif action == "start":
                container = context.get("container")
                result = await self._start_container(container)
                return {
                    "action": "start",
                    "container": container,
                    "result": result,
                    "confidence": 0.9 if result else 0.0
                }
            
            elif action == "stop":
                container = context.get("container")
                result = await self._stop_container(container)
                return {
                    "action": "stop",
                    "container": container,
                    "result": result,
                    "confidence": 0.9 if result else 0.0
                }
            
            elif action == "restart":
                container = context.get("container")
                result = await self._restart_container(container)
                return {
                    "action": "restart",
                    "container": container,
                    "result": result,
                    "confidence": 0.9 if result else 0.0
                }
            
            else:
                return {
                    "action": "unknown",
                    "error": f"Неизвестное действие: {action}",
                    "confidence": 0.0
                }
                
        except Exception as e:
            logger.error(f"❌ Ошибка Docker нейрона: {e}")
            return {
                "action": "error",
                "error": str(e),
                "confidence": 0.0
            }
    
    async def _get_containers_status(self) -> Dict[str, Any]:
        """Получение статуса всех контейнеров"""
        try:
            # Выполнение docker ps через subprocess
            result = subprocess.run(
                ["docker", "ps", "-a", "--format", "json"],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            containers = []
            for line in result.stdout.strip().split('\n'):
                if line:
                    try:
                        container = json.loads(line)
                        containers.append({
                            "id": container.get("ID", "")[:12],
                            "name": container.get("Names", ""),
                            "status": container.get("Status", ""),
                            "image": container.get("Image", "")
                        })
                    except json.JSONDecodeError:
                        continue
            
            self.containers_status = {c["name"]: c for c in containers}
            
            # Отправка статуса через нейронную сеть
            self.broadcast({
                "type": "docker_status",
                "data": self.containers_status,
                "source": self.name
            })
            
            return self.containers_status
            
        except subprocess.TimeoutExpired:
            logger.error("Таймаут при получении статуса Docker")
            return {}
        except FileNotFoundError:
            logger.warning("Docker не найден в системе")
            return {}
        except Exception as e:
            logger.error(f"Ошибка получения статуса Docker: {e}")
            return {}
    
    async def _start_container(self, container_name: str) -> bool:
        """Запуск контейнера"""
        try:
            result = subprocess.run(
                ["docker", "start", container_name],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            success = result.returncode == 0
            
            self.containers_history.append({
                "action": "start",
                "container": container_name,
                "success": success,
                "timestamp": datetime.now()
            })
            
            if success:
                logger.info(f"✅ Контейнер {container_name} запущен")
            else:
                logger.error(f"❌ Ошибка запуска {container_name}: {result.stderr}")
            
            return success
            
        except Exception as e:
            logger.error(f"Ошибка запуска контейнера: {e}")
            return False
    
    async def _stop_container(self, container_name: str) -> bool:
        """Остановка контейнера"""
        try:
            result = subprocess.run(
                ["docker", "stop", container_name],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            success = result.returncode == 0
            
            self.containers_history.append({
                "action": "stop",
                "container": container_name,
                "success": success,
                "timestamp": datetime.now()
            })
            
            if success:
                logger.info(f"✅ Контейнер {container_name} остановлен")
            else:
                logger.error(f"❌ Ошибка остановки {container_name}: {result.stderr}")
            
            return success
            
        except Exception as e:
            logger.error(f"Ошибка остановки контейнера: {e}")
            return False
    
    async def _restart_container(self, container_name: str) -> bool:
        """Перезапуск контейнера"""
        try:
            result = subprocess.run(
                ["docker", "restart", container_name],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            success = result.returncode == 0
            
            self.containers_history.append({
                "action": "restart",
                "container": container_name,
                "success": success,
                "timestamp": datetime.now()
            })
            
            if success:
                logger.info(f"✅ Контейнер {container_name} перезапущен")
            else:
                logger.error(f"❌ Ошибка перезапуска {container_name}: {result.stderr}")
            
            return success
            
        except Exception as e:
            logger.error(f"Ошибка перезапуска контейнера: {e}")
            return False
    
    def get_statistics(self) -> Dict[str, Any]:
        """Получение статистики Docker нейрона"""
        return {
            "containers_count": len(self.containers_status),
            "containers_status": self.containers_status,
            "history_size": len(self.containers_history),
            "last_actions": self.containers_history[-10:] if self.containers_history else []
        }

