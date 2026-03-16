@echo off
REM Скрипт для запуска всех тестов (Windows)
REM Использование: tests\integration\test_run_all.bat

echo ==========================================
echo Запуск всех тестов ЭКОНЕТ (EcoNet)
echo ==========================================

REM Проверка установки pytest
where pytest >nul 2>&1
if %errorlevel% neq 0 (
    echo Ошибка: pytest не установлен
    echo Установите: pip install pytest pytest-asyncio pytest-cov pytest-xdist
    exit /b 1
)

REM Запуск всех тестов с подробным выводом
echo.
echo 1. Запуск всех тестов...
pytest tests\ -v

REM Запуск с покрытием кода
echo.
echo 2. Запуск с покрытием кода...
pytest tests\ --cov=obelisk --cov-report=term-missing --cov-report=html

echo.
echo ==========================================
echo Все тесты завершены
echo Отчет о покрытии: htmlcov\index.html
echo ==========================================
pause

