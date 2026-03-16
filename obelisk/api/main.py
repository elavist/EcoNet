"""
FastAPI главный сервер Обелиска
Предоставляет REST API для управления системой, мониторинга, управления задачами
"""

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import uvicorn
import yaml
import os
import asyncio
from pathlib import Path

from obelisk.api.routes import detection, tasks, robots, models, system, chat
from obelisk.services.mqtt_client import MQTTClient
from obelisk.services.task_manager import TaskManager
from obelisk.services.database import Database
from obelisk.services.trainer import TrainerService
from obelisk.services.active_learner import ActiveLearner
from obelisk.services.chat_service import ChatService
from obelisk.services.vision_context import VisionContext


# Загрузка конфигурации
def load_config():
    config_path = Path(__file__).parent.parent.parent / "config" / "config.yaml"
    with open(config_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


config = load_config()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Управление жизненным циклом приложения"""
    # Startup
    print("🚀 Запуск Обелиска...")
    
    # Инициализация базы данных
    try:
        db = Database(config['database'])
        await db.init()
        app.state.db = db
        print("✅ База данных инициализирована")
    except Exception as e:
        print(f"❌ Ошибка инициализации базы данных: {e}")
        raise
    
    # Инициализация MQTT клиента
    try:
        mqtt_client = MQTTClient(config['mqtt_topics'], config['obelisk'])
        await mqtt_client.connect()
        app.state.mqtt_client = mqtt_client
        if mqtt_client.is_connected():
            print("✅ MQTT клиент подключен")
        else:
            print("⚠️ MQTT клиент не подключен, но работа продолжается")
    except Exception as e:
        print(f"⚠️ Ошибка подключения к MQTT: {e}")
        print("⚠️ Система продолжит работу без MQTT")
        # Создаем заглушку для mqtt_client чтобы избежать ошибок
        mqtt_client = None
        app.state.mqtt_client = None
    
    # Инициализация менеджера задач
    try:
        # TaskManager может работать без MQTT (проверяет наличие перед использованием)
        task_manager = TaskManager(config, db, mqtt_client)
        await task_manager.start()
        app.state.task_manager = task_manager
        print("✅ Менеджер задач инициализирован")
    except Exception as e:
        print(f"❌ Ошибка инициализации менеджера задач: {e}")
        import traceback
        traceback.print_exc()
        raise
    
    # Инициализация сервиса обучения
    try:
        trainer = TrainerService(config, db, mqtt_client)
        app.state.trainer = trainer
        print("✅ Сервис обучения инициализирован")
    except Exception as e:
        print(f"⚠️ Ошибка инициализации сервиса обучения: {e}")
        app.state.trainer = None
    
    # Инициализация активного обучения ("зародыш интеллекта")
    try:
        active_learner = ActiveLearner(config, db, mqtt_client)
        app.state.active_learner = active_learner
        print("✅ Активное обучение инициализировано")
    except Exception as e:
        print(f"⚠️ Ошибка инициализации активного обучения: {e}")
        active_learner = None
        app.state.active_learner = None
    
    # Запуск активного обучения (в фоне)
    if config.get("active_learning", {}).get("enabled", False) and active_learner:
        try:
            asyncio.create_task(active_learner.learning_loop())
            print("🧠 Активное обучение активировано - система будет учиться автоматически")
        except Exception as e:
            print(f"⚠️ Ошибка запуска активного обучения: {e}")
    
    # Инициализация визуального контекста
    try:
        vision_context = VisionContext()
        app.state.vision_context = vision_context
        print("✅ Визуальный контекст инициализирован")
    except Exception as e:
        print(f"⚠️ Ошибка инициализации визуального контекста: {e}")
        app.state.vision_context = None
    
    # Инициализация GPU системы (венозная система)
    try:
        from obelisk.veins.gpu_circulatory import GPUCirculatorySystem
        from obelisk.veins.gpu_distributor import GPUDistributor
        from obelisk.veins.gpu_monitor import GPUMonitor
        from obelisk.veins.gpu_scheduler import GPUScheduler
        
        gpu_circulatory = GPUCirculatorySystem()
        gpu_distributor = GPUDistributor(gpu_circulatory)
        gpu_monitor = GPUMonitor()
        gpu_scheduler = GPUScheduler(gpu_circulatory)
        
        # Запуск мониторинга GPU
        gpu_monitor.start_monitoring()
        
        app.state.gpu_circulatory = gpu_circulatory
        app.state.gpu_distributor = gpu_distributor
        app.state.gpu_monitor = gpu_monitor
        app.state.gpu_scheduler = gpu_scheduler
        
        print("🩸 GPU венозная система активирована - вычислительные ресурсы распределяются")
    except Exception as e:
        print(f"⚠️ Ошибка инициализации GPU системы: {e}")
        app.state.gpu_circulatory = None
        app.state.gpu_distributor = None
        app.state.gpu_monitor = None
        app.state.gpu_scheduler = None
    
    # Инициализация нейронной сети
    try:
        from obelisk.brain.neural_network_builder import NeuralNetworkBuilder
        from obelisk.core.engines.unified_engine import UnifiedEngine
        
        project_root = Path(__file__).parent.parent.parent
        
        # Создание UnifiedEngine для нейронов
        unified_engine = UnifiedEngine(config, project_root=project_root)
        await unified_engine.initialize()
        app.state.unified_engine = unified_engine
        
        # Создание строителя нейронной сети
        neural_builder = NeuralNetworkBuilder(unified_engine=unified_engine)
        
        # Получение GPU системы из состояния приложения или создание новой
        gpu_circulatory = getattr(app.state, 'gpu_circulatory', None)
        gpu_distributor = getattr(app.state, 'gpu_distributor', None)
        gpu_monitor = getattr(app.state, 'gpu_monitor', None)
        
        # Если GPU система уже создана, используем её
        if gpu_circulatory:
            neural_builder.gpu_circulatory = gpu_circulatory
            neural_builder.gpu_distributor = gpu_distributor
            neural_builder.gpu_monitor = gpu_monitor
        
        # Построение нейронной сети
        neural_builder.build_network()
        app.state.neural_builder = neural_builder
        app.state.collective_mind = neural_builder.collective_mind
        app.state.neural_network = neural_builder.neural_network
        app.state.neurons = neural_builder.neurons
        
        print("🧠 Нейронная сеть активирована - все нейроны подключены и работают")
    except Exception as e:
        print(f"⚠️ Ошибка инициализации нейронной сети: {e}")
        import traceback
        traceback.print_exc()
        app.state.neural_builder = None
        app.state.collective_mind = None
        app.state.neural_network = None
        app.state.neurons = {}
    
    # Инициализация системы самоидентификации
    try:
        from obelisk.services.self_identity import SelfIdentityService
        from obelisk.services.self_modification import SelfModificationService
        from obelisk.services.self_learning import SelfLearningService
        
        project_root = Path(__file__).parent.parent.parent
        self_identity = SelfIdentityService(project_root=project_root)
        self_modification = SelfModificationService(project_root, self_identity)
        self_learning = SelfLearningService(self_identity, self_modification, config)
        
        app.state.self_identity = self_identity
        app.state.self_modification = self_modification
        app.state.self_learning = self_learning
        print("🧠 Система самоидентификации активирована - ЭкоНет осознает себя!")
        
        # Инициализация сервиса диалога (ЭкоНет) с самоидентификацией
        chat_service = ChatService(
            config, 
            active_learner=active_learner,
            self_identity=self_identity,
            self_modification=self_modification,
            self_learning=self_learning
        )
        app.state.chat_service = chat_service
        print("🤖 ЭкоНет активирован - система готова к общению и самосовершенствованию!")
    except Exception as e:
        print(f"⚠️ Ошибка инициализации системы самоидентификации: {e}")
        app.state.self_identity = None
        app.state.self_modification = None
        app.state.self_learning = None
        app.state.chat_service = None
    
    print("✅ Обелиск запущен")
    
    yield
    
    # Shutdown
    print("🛑 Остановка Обелиска...")
    
    # Остановка GPU мониторинга
    try:
        if hasattr(app.state, 'gpu_monitor') and app.state.gpu_monitor:
            app.state.gpu_monitor.stop_monitoring()
            print("🩸 GPU мониторинг остановлен")
    except Exception as e:
        print(f"⚠️ Ошибка при остановке GPU мониторинга: {e}")
    
    # Остановка нейронной сети
    try:
        if hasattr(app.state, 'neural_network') and app.state.neural_network:
            # Очистка нейронной сети при необходимости
            pass
        print("🧠 Нейронная сеть остановлена")
    except Exception as e:
        print(f"⚠️ Ошибка при остановке нейронной сети: {e}")
    
    # Остановка MQTT
    try:
        if hasattr(app.state, 'mqtt_client') and app.state.mqtt_client:
            await app.state.mqtt_client.disconnect()
            print("📡 MQTT клиент отключен")
    except Exception as e:
        print(f"⚠️ Ошибка при отключении MQTT: {e}")
    
    # Закрытие базы данных
    try:
        if hasattr(app.state, 'db') and app.state.db:
            await app.state.db.close()
            print("💾 База данных закрыта")
    except Exception as e:
        print(f"⚠️ Ошибка при закрытии БД: {e}")
    
    # Остановка менеджера задач
    try:
        if hasattr(app.state, 'task_manager') and app.state.task_manager:
            await app.state.task_manager.stop()
            print("📋 Менеджер задач остановлен")
    except Exception as e:
        print(f"⚠️ Ошибка при остановке менеджера задач: {e}")
    
    print("✅ Обелиск остановлен")


# Создание FastAPI приложения
app = FastAPI(
    title="SWARM CLEANER - Обелиск API",
    description="API для управления системой автономной уборки окурков",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # В production ограничить
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Подключение роутов
app.include_router(detection.router, prefix="/api/v1/detections", tags=["detections"])
app.include_router(tasks.router, prefix="/api/v1/tasks", tags=["tasks"])
app.include_router(robots.router, prefix="/api/v1/robots", tags=["robots"])
app.include_router(models.router, prefix="/api/v1/models", tags=["models"])
app.include_router(system.router, prefix="/api/v1/system", tags=["system"])
app.include_router(chat.router, prefix="/api/v1/chat", tags=["chat"])

# Статические файлы для веб-интерфейса
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
ui_path = Path(__file__).parent.parent / "ui"
if ui_path.exists():
    app.mount("/ui", StaticFiles(directory=str(ui_path)), name="ui")
    
    @app.get("/chat")
    async def chat_interface():
        """Веб-интерфейс для общения с ЭкоНет"""
        chat_html = ui_path / "chat.html"
        if chat_html.exists():
            return FileResponse(str(chat_html))
        return {"message": "Веб-интерфейс не найден. Используйте CLI: python scripts/chat_with_econet.py"}


@app.get("/")
async def root():
    """Корневой эндпоинт"""
    return {
        "service": "SWARM CLEANER - Обелиск",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs"
    }


@app.get("/health")
async def health_check():
    """Проверка здоровья системы"""
    services = {
        "mqtt": False,
        "database": False,
        "task_manager": False,
        "neural_network": False,
        "gpu_system": False,
        "collective_mind": False
    }
    
    # Проверка MQTT
    if hasattr(app.state, 'mqtt_client') and app.state.mqtt_client:
        services["mqtt"] = app.state.mqtt_client.is_connected()
    
    # Проверка базы данных
    if hasattr(app.state, 'db') and app.state.db:
        services["database"] = app.state.db.is_connected()
    
    # Проверка менеджера задач
    if hasattr(app.state, 'task_manager') and app.state.task_manager:
        services["task_manager"] = app.state.task_manager.is_running()
    
    # Проверка нейронной сети
    if hasattr(app.state, 'neural_network') and app.state.neural_network:
        services["neural_network"] = True
    
    # Проверка GPU системы
    if (hasattr(app.state, 'gpu_circulatory') and app.state.gpu_circulatory and
        hasattr(app.state, 'gpu_monitor') and app.state.gpu_monitor):
        services["gpu_system"] = True
    
    # Проверка коллективного разума
    if hasattr(app.state, 'collective_mind') and app.state.collective_mind:
        services["collective_mind"] = True
    
    all_healthy = all([
        services["database"],
        services["task_manager"],
        services["neural_network"],
        services["gpu_system"]
    ])
    
    return {
        "status": "healthy" if all_healthy else "degraded",
        "services": services
    }


if __name__ == "__main__":
    port = config['obelisk']['port']
    host = config['obelisk']['host']
    # Используем строку импорта для поддержки reload
    uvicorn.run("obelisk.api.main:app", host=host, port=port, reload=True)


