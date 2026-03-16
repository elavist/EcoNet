"""
Система самомодификации ЭкоНет
Позволяет системе модифицировать свой собственный код
для самосовершенствования и адаптации
"""

import logging
import ast
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import shutil

logger = logging.getLogger(__name__)


class SelfModificationService:
    """
    Сервис самомодификации ЭкоНет
    
    Функции:
    1. Модификация собственного кода
    2. Добавление новых функций
    3. Улучшение существующего кода
    4. Создание резервных копий перед изменениями
    """
    
    def __init__(self, project_root: Path, self_identity_service):
        """
        Инициализация сервиса самомодификации
        
        Args:
            project_root: Корневая директория проекта
            self_identity_service: Сервис самоидентификации
        """
        self.project_root = Path(project_root).resolve()
        self.self_identity = self_identity_service
        self.backup_dir = self.project_root / "data" / "backups" / "self_modifications"
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info("✅ Система самомодификации инициализирована")
        logger.info(f"💾 Резервные копии: {self.backup_dir}")
    
    def create_backup(self, file_path: Path) -> Optional[Path]:
        """
        Создать резервную копию файла перед модификацией
        
        Args:
            file_path: Путь к файлу
            
        Returns:
            Путь к резервной копии или None
        """
        if not file_path.exists():
            return None
        
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_name = f"{file_path.stem}_{timestamp}{file_path.suffix}"
            backup_path = self.backup_dir / backup_name
            
            shutil.copy2(file_path, backup_path)
            logger.info(f"💾 Создана резервная копия: {backup_path}")
            
            return backup_path
        except Exception as e:
            logger.error(f"Ошибка создания резервной копии: {e}")
            return None
    
    def modify_file(self, file_path: str, modifications: List[Dict]) -> Tuple[bool, str]:
        """
        Модифицировать файл
        
        Args:
            file_path: Относительный путь к файлу
            modifications: Список модификаций:
                - type: "replace", "add", "remove"
                - old_string: Старый текст (для replace)
                - new_string: Новый текст
                - position: Позиция (для add)
                - pattern: Паттерн для поиска (для remove)
        
        Returns:
            (успех, сообщение)
        """
        full_path = self.project_root / file_path
        
        if not full_path.exists():
            return False, f"Файл не найден: {file_path}"
        
        # Создаем резервную копию
        backup_path = self.create_backup(full_path)
        if not backup_path:
            return False, "Не удалось создать резервную копию"
        
        try:
            # Читаем файл
            with open(full_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            original_content = content
            
            # Применяем модификации
            for mod in modifications:
                mod_type = mod.get("type")
                
                if mod_type == "replace":
                    old_str = mod.get("old_string")
                    new_str = mod.get("new_string")
                    if old_str in content:
                        content = content.replace(old_str, new_str, 1)  # Заменяем только первое вхождение
                    else:
                        logger.warning(f"Не найдено для замены: {old_str[:50]}...")
                
                elif mod_type == "add":
                    position = mod.get("position", "end")
                    new_str = mod.get("new_string")
                    
                    if position == "end":
                        content += "\n" + new_str
                    elif position == "beginning":
                        content = new_str + "\n" + content
                    elif isinstance(position, str) and position in content:
                        # Вставляем после найденного текста
                        content = content.replace(position, position + "\n" + new_str, 1)
                
                elif mod_type == "remove":
                    pattern = mod.get("pattern")
                    if pattern:
                        content = re.sub(pattern, "", content, flags=re.MULTILINE)
                    else:
                        old_str = mod.get("old_string")
                        if old_str in content:
                            content = content.replace(old_str, "", 1)
            
            # Проверяем синтаксис
            try:
                ast.parse(content)
            except SyntaxError as e:
                logger.error(f"Синтаксическая ошибка после модификации: {e}")
                # Восстанавливаем из резервной копии
                shutil.copy2(backup_path, full_path)
                return False, f"Синтаксическая ошибка: {e}"
            
            # Сохраняем изменения
            with open(full_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            # Записываем в историю
            self.self_identity.record_modification(
                file_path,
                "modification",
                f"Применено {len(modifications)} модификаций"
            )
            
            logger.info(f"✅ Файл {file_path} успешно модифицирован")
            return True, f"Файл {file_path} успешно модифицирован"
            
        except Exception as e:
            logger.error(f"Ошибка модификации {file_path}: {e}")
            # Восстанавливаем из резервной копии
            if backup_path and backup_path.exists():
                shutil.copy2(backup_path, full_path)
            return False, f"Ошибка: {e}"
    
    def add_function(self, file_path: str, function_code: str, after_function: Optional[str] = None) -> Tuple[bool, str]:
        """
        Добавить новую функцию в файл
        
        Args:
            file_path: Относительный путь к файлу
            function_code: Код функции (полный, с отступами)
            after_function: Имя функции, после которой вставить (опционально)
        
        Returns:
            (успех, сообщение)
        """
        full_path = self.project_root / file_path
        
        if not full_path.exists():
            return False, f"Файл не найден: {file_path}"
        
        # Создаем резервную копию
        backup_path = self.create_backup(full_path)
        if not backup_path:
            return False, "Не удалось создать резервную копию"
        
        try:
            # Читаем файл
            with open(full_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Парсим для проверки
            try:
                tree = ast.parse(content)
            except SyntaxError as e:
                return False, f"Синтаксическая ошибка в файле: {e}"
            
            # Находим место для вставки
            if after_function:
                # Ищем функцию после которой вставить
                pattern = rf"(def {re.escape(after_function)}\(.*?\):.*?)(?=\n\ndef |\nclass |\Z)"
                match = re.search(pattern, content, re.DOTALL)
                if match:
                    insert_pos = match.end()
                    # Находим конец функции (по отступам)
                    lines = content[:insert_pos].split('\n')
                    last_line = lines[-1]
                    indent = len(last_line) - len(last_line.lstrip())
                    # Вставляем новую функцию с правильным отступом
                    function_indent = " " * indent
                    new_function = "\n" + function_indent + function_code.replace("\n", "\n" + function_indent)
                    content = content[:insert_pos] + new_function + "\n" + content[insert_pos:]
                else:
                    return False, f"Функция {after_function} не найдена"
            else:
                # Вставляем в конец файла
                content += "\n\n" + function_code
            
            # Проверяем синтаксис
            try:
                ast.parse(content)
            except SyntaxError as e:
                shutil.copy2(backup_path, full_path)
                return False, f"Синтаксическая ошибка: {e}"
            
            # Сохраняем
            with open(full_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            # Записываем в историю
            self.self_identity.record_modification(
                file_path,
                "add_function",
                f"Добавлена функция"
            )
            
            logger.info(f"✅ Функция добавлена в {file_path}")
            return True, f"Функция успешно добавлена в {file_path}"
            
        except Exception as e:
            logger.error(f"Ошибка добавления функции: {e}")
            if backup_path and backup_path.exists():
                shutil.copy2(backup_path, full_path)
            return False, f"Ошибка: {e}"
    
    def improve_code(self, file_path: str, improvements: List[str]) -> Tuple[bool, str]:
        """
        Улучшить код на основе предложений
        
        Args:
            file_path: Относительный путь к файлу
            improvements: Список предложений по улучшению
        
        Returns:
            (успех, сообщение)
        """
        # Это базовая реализация - можно расширить с помощью LLM для генерации улучшений
        logger.info(f"💡 Получено {len(improvements)} предложений по улучшению {file_path}")
        
        # Пока просто записываем в память
        for improvement in improvements:
            self.self_identity.add_thought(f"Могу улучшить {file_path}: {improvement}")
        
        return True, f"Получено {len(improvements)} предложений по улучшению"
    
    def can_modify(self, file_path: str) -> bool:
        """
        Проверить, можно ли модифицировать файл
        
        Args:
            file_path: Относительный путь к файлу
        
        Returns:
            True если можно модифицировать
        """
        full_path = self.project_root / file_path
        
        # Не модифицируем системные файлы и резервные копии
        protected_patterns = [
            "__pycache__",
            ".git",
            "backups",
            "node_modules"
        ]
        
        path_str = str(full_path)
        if any(pattern in path_str for pattern in protected_patterns):
            return False
        
        return full_path.exists() and full_path.is_file()

