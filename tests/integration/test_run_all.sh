#!/bin/bash
# Скрипт для запуска всех тестов
# Использование: ./tests/integration/test_run_all.sh

echo "=========================================="
echo "Запуск всех тестов ЭКОНЕТ (EcoNet)"
echo "=========================================="

# Проверка установки pytest
if ! command -v pytest &> /dev/null; then
    echo "Ошибка: pytest не установлен"
    echo "Установите: pip install pytest pytest-asyncio pytest-cov pytest-xdist"
    exit 1
fi

# Запуск всех тестов с подробным выводом
echo ""
echo "1. Запуск всех тестов..."
pytest tests/ -v

# Запуск с покрытием кода
echo ""
echo "2. Запуск с покрытием кода..."
pytest tests/ --cov=obelisk --cov-report=term-missing --cov-report=html

echo ""
echo "=========================================="
echo "Все тесты завершены"
echo "Отчет о покрытии: htmlcov/index.html"
echo "=========================================="

