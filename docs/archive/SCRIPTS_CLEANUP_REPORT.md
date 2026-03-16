# 📋 Отчет об анализе скриптов проекта

## 📊 Результаты анализа

### ✅ Активные скрипты (используются часто)

1. **train_model.py** - 14 ссылок
   - Основной скрипт обучения модели
   - Упоминается в документации
   - ✅ **АКТУАЛЕН**

2. **run_econet.py** - 11 ссылок
   - Запуск системы
   - Упоминается в документации
   - ⚠️ **ПРОВЕРИТЬ**: В документации указано что не существует, используется `python -m obelisk.ui.gui_material`

3. **setup_dataset.py** - 9 ссылок
   - Настройка датасета
   - ✅ **АКТУАЛЕН**

4. **test_with_webcam.py** - 8 ссылок
   - Тестирование с веб-камерой
   - ✅ **АКТУАЛЕН**

### 📋 Используемые скрипты (упоминаются)

- **chat_with_econet.py** (5 ссылок) - ⚠️ Проверить актуальность (LLM удален)
- **run_gui.py** (5 ссылок) - ✅ Актуален
- **test_model_load.py** (5 ссылок) - ✅ Актуален
- **start_system.py** (4 ссылок) - ✅ Актуален
- **test_video_file.py** (4 ссылок) - ✅ Актуален
- **clean_project.py** (3 ссылок) - ✅ Актуален
- **setup_ollama_local.py** (3 ссылок) - ⚠️ Проверить актуальность
- **check_gpu_components.py** (2 ссылок) - ✅ Актуален (новый)
- **check_gpu_training_ready.py** (2 ссылок) - ✅ Актуален (новый)
- **retrain_full_dataset.py** (2 ссылок) - ⚠️ Возможно устарел (есть train_model.py)
- И другие...

### ❌ Неиспользуемые скрипты (нет ссылок)

1. **validate_and_replace_model.py** - ⚠️ **ТОЛЬКО ЧТО СОЗДАН**, но еще не упомянут в документации
   - **ДЕЙСТВИЕ**: Добавить в документацию

2. **complete_gpu_installation.py** - Дубликат `install_gpu_components.py`
   - **ДЕЙСТВИЕ**: Удалить (дубликат)

3. **check_and_update_model.py** - Возможно заменен `validate_and_replace_model.py`
   - **ДЕЙСТВИЕ**: Проверить функциональность, возможно удалить

4. **chat_with_video.py** - Chat скрипт (LLM удален)
   - **ДЕЙСТВИЕ**: Удалить (устарел)

5. **chat_with_video_demo.py** - Chat скрипт (LLM удален)
   - **ДЕЙСТВИЕ**: Удалить (устарел)

6. **test_chat_response.py** - Chat тест (LLM удален)
   - **ДЕЙСТВИЕ**: Удалить (устарел)

7. **check_ollama.py** - Проверка Ollama (LLM удален)
   - **ДЕЙСТВИЕ**: Удалить (устарел)

8. **test_ollama_integration.py** - Тест Ollama (LLM удален)
   - **ДЕЙСТВИЕ**: Удалить (устарел)

9. **check_system.py** - Проверка системы
   - **ДЕЙСТВИЕ**: Проверить, возможно удалить или обновить

10. **debug_econet.py** - Отладка
    - **ДЕЙСТВИЕ**: Проверить, возможно удалить

11. **test_gui_functionality.py** - Тест GUI
    - **ДЕЙСТВИЕ**: Проверить, возможно удалить

12. **test_unified_engine.py** - Тест движка
    - **ДЕЙСТВИЕ**: Проверить, возможно удалить

## 🔍 Проблемы

### 1. Дубликаты GPU установки
- `install_gpu_components.py` (1 ссылка) - основной
- `complete_gpu_installation.py` (0 ссылок) - дубликат
- **Рекомендация**: Удалить `complete_gpu_installation.py`

### 2. Дубликаты GPU проверки
- `check_gpu_components.py` (2 ссылки) - детальная проверка
- `check_gpu_training_ready.py` (2 ссылки) - проверка перед обучением
- **Рекомендация**: Оба актуальны, но можно объединить

### 3. Устаревшие chat скрипты
- `chat_with_econet.py` (5 ссылок) - ⚠️ Проверить актуальность
- `chat_with_video.py` (0 ссылок) - удалить
- `chat_with_video_demo.py` (0 ссылок) - удалить
- `test_chat_response.py` (0 ссылок) - удалить

### 4. Недавно созданные скрипты
- `validate_and_replace_model.py` - создан, но не упомянут в документации
- **ДЕЙСТВИЕ**: Добавить в документацию

## 📝 Рекомендации по очистке

### Удалить (устарели/дубликаты):

1. ✅ `complete_gpu_installation.py` - дубликат `install_gpu_components.py`
2. ✅ `chat_with_video.py` - устарел (LLM удален)
3. ✅ `chat_with_video_demo.py` - устарел (LLM удален)
4. ✅ `test_chat_response.py` - устарел (LLM удален)
5. ✅ `check_ollama.py` - устарел (LLM удален)
6. ✅ `test_ollama_integration.py` - устарел (LLM удален)

### Проверить и возможно удалить:

1. ⚠️ `check_and_update_model.py` - возможно заменен `validate_and_replace_model.py`
2. ⚠️ `check_system.py` - проверить функциональность
3. ⚠️ `debug_econet.py` - проверить функциональность
4. ⚠️ `test_gui_functionality.py` - проверить функциональность
5. ⚠️ `test_unified_engine.py` - проверить функциональность
6. ⚠️ `retrain_full_dataset.py` - возможно устарел (есть `train_model.py`)

### Обновить документацию:

1. ✅ Добавить `validate_and_replace_model.py` в документацию
2. ⚠️ Проверить `run_econet.py` - в документации указано что не существует

## 🎯 План действий

### Фаза 1: Удаление явно устаревших (безопасно)

```bash
# Удалить устаревшие chat скрипты
rm scripts/chat_with_video.py
rm scripts/chat_with_video_demo.py
rm scripts/test_chat_response.py
rm scripts/check_ollama.py
rm scripts/test_ollama_integration.py

# Удалить дубликат GPU установки
rm scripts/complete_gpu_installation.py
```

### Фаза 2: Проверка и обновление документации

1. Добавить `validate_and_replace_model.py` в документацию
2. Проверить актуальность `chat_with_econet.py`
3. Проверить `run_econet.py` - существует ли на самом деле?

### Фаза 3: Проверка функциональности (требует ручной проверки)

1. Сравнить `check_and_update_model.py` и `validate_and_replace_model.py`
2. Проверить нужны ли тестовые скрипты
3. Проверить `retrain_full_dataset.py` vs `train_model.py`

## 📊 Итоговая статистика

- **Всего скриптов**: 34
- **Активных**: 4
- **Используемых**: 18
- **Неиспользуемых**: 12

**Можно безопасно удалить**: 6 скриптов
**Требуют проверки**: 6 скриптов

