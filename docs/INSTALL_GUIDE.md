# 📦 Руководство по установке зависимостей

## Быстрая установка

### Основные зависимости
```bash
pip install -r requirements.txt
```

## Решение проблем с установкой

### Проблема: Таймаут при установке pynvml

Если возникает ошибка таймаута при установке `pynvml`:

**Вариант 1: Установка с увеличенным таймаутом**
```bash
pip install --default-timeout=100 pynvml>=11.5.0
```

**Вариант 2: Установка из опциональных зависимостей**
```bash
pip install -r requirements-optional.txt
```

**Вариант 3: Пропустить установку (pynvml опционален)**
`pynvml` используется только для мониторинга GPU (температура, утилизация). 
Код работает и без него - просто мониторинг будет ограничен.

### Проблема: Медленное подключение к PyPI

**Использование зеркала PyPI:**
```bash
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
```

**Или использование кэша:**
```bash
pip install -r requirements.txt --cache-dir ./pip-cache
```

### Проблема: Конфликты версий

**Установка в виртуальном окружении (рекомендуется):**
```bash
python -m venv venv
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

pip install -r requirements.txt
```

## Установка опциональных зависимостей

### GPU Monitoring (pynvml)
Для мониторинга температуры и утилизации NVIDIA GPU:
```bash
pip install pynvml>=11.5.0
```

**Примечание:** Если `pynvml` не установлен, система продолжит работать, но мониторинг GPU будет ограничен (не будет температуры и утилизации).

### PostgreSQL Support
Если используете PostgreSQL вместо SQLite:
```bash
pip install psycopg2-binary>=2.9.9 sqlalchemy>=2.0.0 alembic>=1.12.0
```

### ML Tracking
Для отслеживания экспериментов ML:
```bash
pip install mlflow>=2.8.0 wandb>=0.16.0
```

## Поэтапная установка

### Шаг 1: Основные зависимости
```bash
pip install torch>=2.0.0 torchvision>=0.15.0
pip install ultralytics>=8.0.0
pip install opencv-python>=4.8.0 numpy>=1.24.0 pillow>=10.0.0
```

### Шаг 2: API зависимости
```bash
pip install fastapi>=0.104.0 uvicorn[standard]>=0.24.0 pydantic>=2.5.0
```

### Шаг 3: Остальные зависимости
```bash
pip install -r requirements.txt
```

### Шаг 4: Опциональные (при необходимости)
```bash
pip install -r requirements-optional.txt
```

## Проверка установки

После установки проверьте зависимости:
```bash
python scripts/check_dependencies.py
```

## Устранение неполадок

### Ошибка: "No module named 'X'"
Установите недостающий модуль:
```bash
pip install X
```

### Ошибка: Конфликт версий
Обновите pip:
```bash
python -m pip install --upgrade pip
```

### Ошибка: Нет прав для установки
Используйте флаг `--user`:
```bash
pip install --user -r requirements.txt
```

## Минимальная установка

Для работы только с базовым функционалом (без GUI, LLM, GPU мониторинга):
```bash
pip install ultralytics torch opencv-python numpy pillow
pip install fastapi uvicorn pydantic
pip install paho-mqtt pyyaml aiosqlite requests
```

