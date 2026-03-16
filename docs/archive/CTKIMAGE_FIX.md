# ✅ Исправление Ошибки CTkImage.size

## 📋 Проблема

**Ошибка:**
```
AttributeError: 'CTkImage' object has no attribute 'size'
```

**Местоположение:** `obelisk/ui/gui_material.py`, строка 934

**Причина:** `CTkImage` в CustomTkinter не имеет атрибута `size` для проверки размера изображения.

## 🔧 Решение

**Было:**
```python
if self.video_image.size != (frame_pil.width, frame_pil.height):
    # Создать новый объект
```

**Стало:**
```python
# Сохраняем размер отдельно
current_size = (frame_pil.width, frame_pil.height)

if not hasattr(self, '_video_image_size') or self._video_image_size != current_size:
    # Размер изменился - создаем новый объект
    self.video_image = ctk.CTkImage(...)
    self._video_image_size = current_size
else:
    # Размер не изменился - обновляем через configure
    self.video_image.configure(light_image=frame_pil, dark_image=frame_pil)
```

## 📝 Изменения

1. ✅ **Добавлено сохранение размера:** `self._video_image_size`
2. ✅ **Проверка размера:** Используется сохраненный размер вместо `self.video_image.size`
3. ✅ **Обработка ошибок:** Если `configure` не работает, создается новый объект

## ✅ Статус

| Проблема | Статус |
|----------|--------|
| AttributeError: 'CTkImage' object has no attribute 'size' | ✅ Исправлено |

## 🚀 Результат

Теперь код:
- ✅ Не пытается получить несуществующий атрибут `size`
- ✅ Сохраняет размер отдельно для проверки
- ✅ Оптимизирует создание объектов (только при изменении размера)
- ✅ Обрабатывает ошибки при обновлении через `configure`

