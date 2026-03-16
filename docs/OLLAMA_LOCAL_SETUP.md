# 🏠 Перенос Ollama в Папку Проекта

## 📋 Описание

Этот скрипт позволяет перенести Ollama из системной установки в папку проекта `tools/ollama/`, чтобы иметь локальную копию для более удобного управления.

## 🚀 Быстрый Старт

### Автоматический Перенос

```powershell
python scripts/setup_ollama_local.py
```

Скрипт автоматически:
1. ✅ Найдет установленный Ollama
2. ✅ Скопирует в `tools/ollama/`
3. ✅ Создаст скрипт запуска
4. ✅ Обновит конфигурацию

## 📁 Структура После Переноса

```
Project Family/
├── tools/
│   └── ollama/
│       ├── ollama.exe          # Исполняемый файл
│       ├── start_ollama.bat    # Скрипт запуска
│       └── ollama.dll          # (если нужен)
└── config/
    └── config.yaml             # Обновленная конфигурация
```

## 🎯 Использование

### Запуск Локального Ollama

**Windows:**
```powershell
.\tools\ollama\start_ollama.bat
```

**Или через командную строку:**
```powershell
cd tools\ollama
.\ollama.exe serve
```

### Установка Моделей

После запуска Ollama, установите нужную модель:

```powershell
.\tools\ollama\ollama.exe pull llama3.1:8b
```

Или если используете системную версию:
```powershell
ollama pull llama3.1:8b
```

## ⚙️ Конфигурация

После переноса в `config/config.yaml` появится:

```yaml
chat:
  ollama_path: "tools/ollama/ollama.exe"  # Путь к локальному Ollama
  llm_provider: "ollama"
  llm_model: "llama3.1:8b"
```

## 📝 Важные Замечания

### 1. Модели Ollama

Модели Ollama **НЕ копируются** автоматически. Они хранятся в:
- Windows: `C:\Users\<ВашеИмя>\.ollama\models`
- Linux/Mac: `~/.ollama/models`

Модели используются **общими** для всех установок Ollama на вашем компьютере.

### 2. Использование Локального vs Системного Ollama

**Локальный Ollama (в проекте):**
- ✅ Не зависит от системной установки
- ✅ Легко обновлять независимо
- ✅ Можно закоммитить в репозиторий (если нужно)

**Системный Ollama:**
- ✅ Автоматический запуск при старте системы
- ✅ Легче обновлять через установщик
- ✅ Интеграция с системой

**Рекомендация:** Используйте локальный Ollama для разработки, системный - для продакшена.

### 3. Запуск Сервера

Ollama должен быть запущен **до** запуска ЭкоНет:

```powershell
# Вариант 1: Локальный
.\tools\ollama\start_ollama.bat

# Вариант 2: Системный
ollama serve
```

Затем проверьте доступность:
```powershell
curl http://localhost:11434/api/tags
```

## 🔧 Ручная Настройка

Если автоматический скрипт не работает:

1. **Найдите Ollama:**
   ```powershell
   where ollama
   ```

2. **Скопируйте вручную:**
   ```powershell
   mkdir tools\ollama
   copy "C:\Users\<ВашеИмя>\AppData\Local\Programs\Ollama\ollama.exe" tools\ollama\
   ```

3. **Создайте скрипт запуска:**
   ```batch
   @echo off
   cd /d "%~dp0"
   ollama.exe serve
   ```

4. **Обновите конфиг:**
   ```yaml
   chat:
     ollama_path: "tools/ollama/ollama.exe"
   ```

## ❓ Устранение Проблем

### Ollama не найден

**Проблема:** Скрипт не может найти Ollama

**Решение:**
1. Установите Ollama: https://ollama.ai/download
2. Добавьте в PATH (обычно делается автоматически)
3. Перезапустите терминал

### Модели не загружаются

**Проблема:** Модели не доступны после переноса

**Решение:**
Модели хранятся отдельно от исполняемого файла. Используйте:
```powershell
.\tools\ollama\ollama.exe pull llama3.1:8b
```

### Конфликт с Системным Ollama

**Проблема:** Оба Ollama работают одновременно

**Решение:**
Используйте только один:
- Локальный: `.\tools\ollama\ollama.exe serve`
- Системный: `ollama serve`

Остановите другой перед запуском ЭкоНет.

## 📚 Дополнительная Информация

- [Официальный сайт Ollama](https://ollama.ai/)
- [Документация Ollama](https://github.com/ollama/ollama/blob/main/docs/README.md)
- [Руководство по Ollama для ЭкоНет](OLLAMA_SETUP_GUIDE.md)

