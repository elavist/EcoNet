# 🚀 Полная последовательность команд: от установки до тестирования

## Шаг 1: Установка зависимостей

```powershell
# Перейти в корень проекта
cd "C:\Users\elavi\Desktop\Project '' Family"

# Установить основные зависимости
pip install ultralytics>=8.0.0 paho-mqtt>=1.6.1 fastapi>=0.104.0 pyyaml>=6.0.1 aiosqlite opencv-python

# Или установить все зависимости (если requirements.txt исправлен)
pip install -r requirements.txt
```

**Проверка:**
```powershell
python -c "from ultralytics import YOLO; print('✅ Ultralytics установлен')"
```

---

## Шаг 2: Настройка датасета

```powershell
# Интеграция существующего датасета
python scripts\setup_dataset.py
```

**Проверка:**
```powershell
dir datasets\cigarette_butt\data.yaml
dir datasets\cigarette_butt\train\images
```

---

## Шаг 3: Обучение модели (если еще не обучена)

```powershell
# Запустить обучение
python scripts\train_model.py
```

**Или быстрое обучение (10 эпох для теста):**
```powershell
cd models\cigarette_detector
python -c "from ultralytics import YOLO; model = YOLO('yolov8n.pt'); model.train(data='../../datasets/cigarette_butt/data.yaml', epochs=10, imgsz=640, batch=16)"
cd ..\..
```

**После обучения скопировать модель:**
```powershell
# Проверить наличие модели
dir models\cigarette_detector\train\weights\best.pt

# Скопировать в основную директорию
copy "models\cigarette_detector\train\weights\best.pt" "models\cigarette_detector\best.pt"

# Проверить что скопировалось
dir models\cigarette_detector\best.pt
```

---

## Шаг 4: Проверка модели

```powershell
# Тест загрузки и работы модели
python scripts\test_model_load.py
```

**Ожидаемый результат:**
- ✅ Модель найдена
- ✅ Модель загружена успешно
- ✅ На тестовом изображении найдена детекция

---

## Шаг 5: Проверка конфигурации

```powershell
# Проверить путь к модели в конфиге
type config\config.yaml | Select-String "weights_path"
```

**Должно быть:**
```yaml
weights_path: models/cigarette_detector/best.pt
```

**Если нужно исправить:**
```powershell
# Откройте config\config.yaml и проверьте строку:
# model:
#   weights_path: models/cigarette_detector/best.pt
```

---

## Шаг 6: Подготовка IP Webcam

**На телефоне:**
1. Откройте приложение **IP Webcam**
2. Нажмите **"Start server"** (или "Начать сервер")
3. Запишите IP адрес (например: `192.168.1.100:8080`)
4. Убедитесь, что телефон и компьютер в **одной Wi-Fi сети**

**Проверка в браузере:**
Откройте в браузере: `http://192.168.1.100:8080/video` (замените IP на ваш)
- Должно показать видео с камеры телефона

---

## Шаг 7: Тестирование с IP Webcam

### Вариант A: С пониженным порогом уверенности

```powershell
python scripts\test_with_webcam.py --ip 192.168.1.XXX --conf 0.3
```

Замените `192.168.1.XXX` на IP вашего телефона.

### Вариант B: С очень низким порогом (если A не работает)

```powershell
python scripts\test_with_webcam.py --ip 192.168.1.XXX --conf 0.2
```

### Вариант C: Локальная веб-камера (для проверки)

```powershell
python scripts\test_with_webcam.py --ip 0 --conf 0.3
```

### Вариант D: Только логи (без видео)

```powershell
python scripts\test_with_webcam.py --ip 192.168.1.XXX --conf 0.3 --no-video
```

---

## Шаг 8: Детальная диагностика (если не работает)

```powershell
# Запустить диагностический скрипт
python scripts\diagnose_video.py
```

Этот скрипт покажет:
- ✅ Загружается ли модель
- ✅ Работает ли на статических изображениях
- ✅ Что происходит при обработке видео
- ✅ Детекции с разными порогами (0.2, 0.3, 0.5)

**Использование:**
1. Запустите скрипт
2. Введите IP адрес телефона (или 0 для локальной камеры)
3. Смотрите в консоль - там будет детальная информация
4. Нажмите 'q' для выхода

---

## Шаг 9: Диагностика проблем

### Если модель не загружается:

```powershell
# Проверить наличие файла
dir models\cigarette_detector\best.pt

# Проверить размер (должен быть ~12 MB)
# Если файл отсутствует или слишком маленький - переобучить
```

### Если детекции не находятся:

```powershell
# 1. Проверить работу модели на тестовом изображении
python scripts\test_model_load.py

# 2. Проверить подключение к IP Webcam
# Откройте в браузере: http://IP:8080/video

# 3. Попробовать еще более низкий порог
python scripts\test_with_webcam.py --ip 192.168.1.XXX --conf 0.15

# 4. Проверить логи - должны быть сообщения о загрузке модели
```

### Если IP Webcam не подключается:

```powershell
# Проверить ping
ping 192.168.1.XXX

# Проверить в браузере
# http://192.168.1.XXX:8080/video

# Попробовать другой порт (если указан в приложении)
python scripts\test_with_webcam.py --ip 192.168.1.XXX --port 8081 --conf 0.3
```

---

## 🔍 ВАЖНО: Если детекции не находятся

**Сначала запустите диагностику:**
```powershell
python scripts\diagnose_video.py
```

Это покажет:
- Работает ли модель на статических изображениях
- Что происходит при обработке видео
- Все найденные детекции с разными порогами

**Возможные причины:**
1. Окурки слишком маленькие на видео → поднесите камеру ближе
2. Плохое освещение → улучшите освещение
3. Модель не видит из-за угла съемки → попробуйте другой угол
4. Видео имеет другое качество → попробуйте изменить разрешение в IP Webcam

---

## Полная последовательность (для копирования)

```powershell
# 1. Установка зависимостей
cd "C:\Users\elavi\Desktop\Project '' Family"
pip install ultralytics>=8.0.0 paho-mqtt>=1.6.1 fastapi>=0.104.0 pyyaml>=6.0.1 aiosqlite opencv-python

# 2. Настройка датасета
python scripts\setup_dataset.py

# 3. Проверка модели (если уже обучена)
dir models\cigarette_detector\best.pt

# 4. Если модели нет - обучить
python scripts\train_model.py
# Или быстро: cd models\cigarette_detector && python -c "from ultralytics import YOLO; model = YOLO('yolov8n.pt'); model.train(data='../../datasets/cigarette_butt/data.yaml', epochs=10, imgsz=640, batch=16)" && cd ..\..

# 5. Копирование модели (если обучена)
copy "models\cigarette_detector\train\weights\best.pt" "models\cigarette_detector\best.pt"

# 6. Проверка модели
python scripts\test_model_load.py

# 7. Тест с IP Webcam (ЗАМЕНИТЕ IP!)
python scripts\test_with_webcam.py --ip 192.168.1.XXX --conf 0.3
```

---

## Проверочный чеклист

Перед тестированием убедитесь:

- [ ] ✅ Зависимости установлены (`python -c "from ultralytics import YOLO"`)
- [ ] ✅ Датасет настроен (`dir datasets\cigarette_butt\data.yaml`)
- [ ] ✅ Модель существует (`dir models\cigarette_detector\best.pt`)
- [ ] ✅ Модель работает (`python scripts\test_model_load.py` - находит детекции)
- [ ] ✅ IP Webcam запущен на телефоне
- [ ] ✅ Телефон и компьютер в одной Wi-Fi сети
- [ ] ✅ Видео доступно в браузере (`http://IP:8080/video`)

---

## Если ничего не помогает

1. **Переобучить модель заново:**
   ```powershell
   python scripts\train_model.py
   copy "models\cigarette_detector\train\weights\best.pt" "models\cigarette_detector\best.pt"
   ```

2. **Проверить конфигурацию вручную:**
   - Откройте `config\config.yaml`
   - Проверьте `model.weights_path`
   - Проверьте `model.confidence_threshold`

3. **Попробовать на локальной камере:**
   ```powershell
   python scripts\test_with_webcam.py --ip 0 --conf 0.2
   ```

4. **Проверить логи детально:**
   - Запустите с `--no-video` чтобы видеть все логи
   - Ищите сообщения "Модель загружена" и "найдено детекций"

