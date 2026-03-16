# ✅ Проверка зависимостей проекта

## Дата проверки
Проверка выполнена автоматически с помощью `scripts/check_dependencies.py`

## Результаты

### ✅ Найденные зависимости
Все необходимые зависимости найдены и добавлены в `requirements.txt`:

- **aiosqlite>=0.19.0** - для асинхронной работы с SQLite
- **onnxruntime>=1.16.0** - для работы с ONNX моделями (опционально)
- **pynvml>=11.5.0** - для мониторинга NVIDIA GPU

### 🔧 Исправления
1. ✅ Добавлена недостающая зависимость `aiosqlite`
2. ✅ Добавлена недостающая зависимость `onnxruntime`
3. ✅ Добавлена недостающая зависимость `pynvml`
4. ✅ Удален дубликат `pillow` из секции GUI

### 📋 Структура requirements.txt

#### Core dependencies
- ultralytics>=8.0.0
- torch>=2.0.0
- torchvision>=0.15.0
- opencv-python>=4.8.0
- numpy>=1.24.0
- pillow>=10.0.0
- onnxruntime>=1.16.0 (опционально)

#### API and Web
- fastapi>=0.104.0
- uvicorn[standard]>=0.24.0
- pydantic>=2.5.0
- websockets>=12.0

#### MQTT
- paho-mqtt>=1.6.1

#### Database
- sqlalchemy>=2.0.0
- psycopg2-binary>=2.9.9
- alembic>=1.12.0
- **aiosqlite>=0.19.0** ✨ (добавлено)

#### Data processing
- pandas>=2.1.0
- pyyaml>=6.0.1

#### Image processing
- imageio>=2.31.0
- scikit-image>=0.22.0

#### ML Ops
- mlflow>=2.8.0
- wandb>=0.16.0

#### Utilities
- python-dotenv>=1.0.0
- tqdm>=4.66.0
- **pynvml>=11.5.0** ✨ (добавлено)

#### Testing
- pytest>=7.4.0
- pytest-asyncio>=0.21.0
- pytest-cov>=4.1.0
- pytest-xdist>=3.5.0
- pytest-mock>=3.12.0

#### Chat and LLM (optional)
- openai>=1.0.0
- requests>=2.31.0
- groq>=0.4.0
- google-generativeai>=0.3.0
- aiohttp>=3.9.0

#### GUI
- customtkinter>=5.2.0

## ⚠️ Опциональные зависимости

Некоторые зависимости помечены как "неиспользуемые" скриптом проверки, но они используются опционально или в тестах:

- **alembic** - миграции БД (если используется PostgreSQL)
- **pandas** - обработка данных (может использоваться в скриптах)
- **sqlalchemy** - ORM (если используется PostgreSQL)
- **psycopg2-binary** - драйвер PostgreSQL (если используется PostgreSQL)
- **pytest**, **pytest-*** - тестирование (используется в tests/)
- **python-dotenv** - переменные окружения (может использоваться)
- **mlflow**, **wandb** - отслеживание экспериментов ML
- **websockets** - WebSocket поддержка (может использоваться в API)
- **torchvision** - дополнение к PyTorch
- **tqdm** - прогресс-бары (может использоваться в скриптах)
- **imageio**, **scikit-image** - обработка изображений (может использоваться)

## 🚀 Установка зависимостей

```bash
pip install -r requirements.txt
```

## 🔍 Проверка зависимостей

Для проверки зависимостей используйте скрипт:

```bash
python scripts/check_dependencies.py
```

## ✅ Статус

**Все зависимости проверены и актуальны!**

