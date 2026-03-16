"""
Скрипт запуска всей системы ЭкоНет
Пробуждает Обелиск и все компоненты, проверяет систему
"""

import sys
import os
import asyncio
import subprocess
import time
import signal
from pathlib import Path
from typing import List, Optional

# Исправление кодировки для Windows
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

# Принудительная очистка буфера вывода
def flush_output():
    """Принудительная очистка буферов вывода"""
    sys.stdout.flush()
    sys.stderr.flush()

# Добавление пути к проекту
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import yaml
import requests
from datetime import datetime


class EcoNetSystemLauncher:
    """Запуск и управление системой ЭкоНет"""
    
    def __init__(self):
        self.project_root = Path(__file__).parent.parent
        self.processes: List[subprocess.Popen] = []
        self.config = self._load_config()
        self.running = True
        
        # Обработка сигналов для корректного завершения
        if sys.platform != 'win32':
            signal.signal(signal.SIGINT, self._signal_handler)
            signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _load_config(self):
        """Загрузка конфигурации"""
        config_path = self.project_root / "config" / "config.yaml"
        with open(config_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    
    def _signal_handler(self, signum, frame):
        """Обработчик сигналов для корректного завершения"""
        print("\n🛑 Получен сигнал завершения...")
        self.stop_all()
        sys.exit(0)
    
    def check_mqtt_broker(self) -> bool:
        """Проверка MQTT брокера"""
        print("📡 Проверка MQTT брокера...")
        
        mqtt_host = self.config.get('obelisk', {}).get('mqtt_broker', 'localhost')
        mqtt_port = self.config.get('obelisk', {}).get('mqtt_port', 1883)
        
        try:
            import socket
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(2)
            result = sock.connect_ex((mqtt_host, mqtt_port))
            sock.close()
            
            if result == 0:
                print(f"   ✅ MQTT брокер доступен на {mqtt_host}:{mqtt_port}")
                return True
            else:
                print(f"   ⚠️ MQTT брокер недоступен на {mqtt_host}:{mqtt_port}")
                print("   💡 Запустите: docker-compose up -d mosquitto")
                return False
        except Exception as e:
            print(f"   ⚠️ Ошибка проверки MQTT: {e}")
            return False
    
    def start_mqtt_broker(self) -> bool:
        """Запуск MQTT брокера через Docker"""
        print("🚀 Запуск MQTT брокера...")
        
        try:
            # Проверка Docker
            result = subprocess.run(
                ["docker", "--version"],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode != 0:
                print("   ❌ Docker не найден")
                return False
            
            # Запуск mosquitto
            docker_compose = self.project_root / "docker-compose.yml"
            if docker_compose.exists():
                result = subprocess.run(
                    ["docker-compose", "up", "-d", "mosquitto"],
                    cwd=self.project_root,
                    capture_output=True,
                    text=True,
                    timeout=30
                )
                
                if result.returncode == 0:
                    print("   ✅ MQTT брокер запущен")
                    time.sleep(2)  # Ожидание запуска
                    return True
                else:
                    print(f"   ⚠️ Ошибка запуска: {result.stderr}")
                    return False
            else:
                print("   ⚠️ docker-compose.yml не найден")
                return False
                
        except FileNotFoundError:
            print("   ❌ Docker не установлен")
            return False
        except Exception as e:
            print(f"   ❌ Ошибка: {e}")
            return False
    
    def start_obelisk(self) -> Optional[subprocess.Popen]:
        """Запуск Обелиска"""
        print("🚀 Запуск Обелиска...")
        
        try:
            obelisk_module = "obelisk.api.main"
            host = self.config.get('obelisk', {}).get('host', 'localhost')
            port = self.config.get('obelisk', {}).get('port', 8000)
            
            # Выводим информацию ДО запуска процесса
            print(f"   [INFO] Запускаю Обелиск...")
            sys.stdout.flush()
            
            # Запуск через uvicorn
            # НЕ используем PIPE, чтобы вывод отображался в реальном времени
            process = subprocess.Popen(
                [sys.executable, "-m", "uvicorn", f"{obelisk_module}:app", 
                 "--host", host, "--port", str(port), "--reload"],
                cwd=self.project_root,
                # stdout и stderr идут напрямую в консоль для видимости
                stdout=None,
                stderr=None,
                text=True
            )
            
            self.processes.append(process)
            
            # Выводим информацию ПОСЛЕ запуска
            print(f"   ✅ Обелиск запущен (PID: {process.pid})")
            print(f"   🌐 API: http://{host}:{port}")
            print(f"   📚 Документация: http://{host}:{port}/docs")
            print()
            print("   [INFO] Вывод сервера будет отображаться ниже...")
            print("=" * 60)
            sys.stdout.flush()  # Принудительный вывод перед выводом uvicorn
            
            # Небольшая задержка, чтобы сообщения успели отобразиться
            time.sleep(0.3)
            sys.stdout.flush()
            
            return process
            
        except Exception as e:
            print(f"   ❌ Ошибка запуска Обелиска: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def wait_for_obelisk(self, timeout: int = 30) -> bool:
        """Ожидание готовности Обелиска"""
        print()
        print("⏳ Ожидание готовности Обелиска...")
        
        host = self.config.get('obelisk', {}).get('host', 'localhost')
        port = self.config.get('obelisk', {}).get('port', 8000)
        base_url = f"http://{host}:{port}"
        
        start_time = time.time()
        last_check_time = start_time
        check_count = 0
        
        while time.time() - start_time < timeout:
            elapsed = int(time.time() - start_time)
            
            # Выводим прогресс каждые 2 секунды
            if time.time() - last_check_time >= 2:
                check_count += 1
                print(f"   [CHECK {check_count}] Ожидание готовности... ({elapsed} сек)")
                last_check_time = time.time()
            
            try:
                response = requests.get(f"{base_url}/health", timeout=2)
                if response.status_code == 200:
                    health_data = response.json()
                    print(f"\n   ✅ Обелиск готов! (за {elapsed} сек)")
                    
                    # Показ статуса сервисов
                    if 'services' in health_data:
                        services = health_data['services']
                        print("   📊 Статус сервисов:")
                        for service, status in services.items():
                            status_icon = "✅" if status else "❌"
                            print(f"      {status_icon} {service}: {status}")
                    
                    return True
            except requests.exceptions.ConnectionError:
                # Не выводим сообщение на каждую попытку, чтобы не засорять вывод
                pass
            except Exception as e:
                if time.time() - last_check_time >= 2:
                    print(f"   ⚠️ Ошибка проверки: {e}")
                    last_check_time = time.time()
            
            time.sleep(0.5)
        
        print(f"\n   ⚠️ Таймаут ожидания Обелиска ({timeout} сек)")
        return False
    
    def check_system_health(self) -> bool:
        """Проверка здоровья системы"""
        print("\n" + "=" * 60)
        print("🔍 Проверка здоровья системы")
        print("=" * 60)
        
        host = self.config.get('obelisk', {}).get('host', 'localhost')
        port = self.config.get('obelisk', {}).get('port', 8000)
        base_url = f"http://{host}:{port}"
        
        checks = []
        
        # Проверка root endpoint
        try:
            response = requests.get(f"{base_url}/", timeout=5)
            if response.status_code == 200:
                print("   ✅ Root endpoint: OK")
                checks.append(True)
            else:
                print(f"   ⚠️ Root endpoint: {response.status_code}")
                checks.append(False)
        except Exception as e:
            print(f"   ❌ Root endpoint: {e}")
            checks.append(False)
        
        # Проверка health endpoint
        try:
            response = requests.get(f"{base_url}/health", timeout=5)
            if response.status_code == 200:
                health_data = response.json()
                print("   ✅ Health endpoint: OK")
                status = health_data.get('status', 'N/A')
                print(f"      Status: {status}")
                sys.stdout.flush()  # Принудительный вывод
                checks.append(True)
            else:
                print(f"   ⚠️ Health endpoint: {response.status_code}")
                sys.stdout.flush()
                checks.append(False)
        except Exception as e:
            print(f"   ❌ Health endpoint: {e}")
            sys.stdout.flush()
            checks.append(False)
        
        # Проверка docs endpoint
        try:
            response = requests.get(f"{base_url}/docs", timeout=5)
            if response.status_code == 200:
                print("   ✅ API Documentation: OK")
                checks.append(True)
            else:
                print(f"   ⚠️ API Documentation: {response.status_code}")
                checks.append(False)
        except Exception as e:
            print(f"   ❌ API Documentation: {e}")
            checks.append(False)
        
        return all(checks)
    
    def stop_all(self):
        """Остановка всех процессов"""
        if not self.processes:
            return
            
        print("\n" + "=" * 60)
        print("🛑 Остановка системы...")
        print("=" * 60)
        
        for process in self.processes:
            try:
                # Проверяем, что процесс еще работает
                if process.poll() is None:
                    # Процесс работает, останавливаем
                    if sys.platform == 'win32':
                        # На Windows используем taskkill для более надежного завершения
                        try:
                            subprocess.run(
                                ["taskkill", "/F", "/T", "/PID", str(process.pid)],
                                capture_output=True,
                                timeout=5
                            )
                        except Exception:
                            # Fallback на стандартный метод
                            process.terminate()
                            try:
                                process.wait(timeout=3)
                            except subprocess.TimeoutExpired:
                                process.kill()
                    else:
                        # На Unix-подобных системах
                        process.terminate()
                        try:
                            process.wait(timeout=5)
                        except subprocess.TimeoutExpired:
                            process.kill()
                    
                    print(f"   ✅ Процесс {process.pid} остановлен")
                else:
                    print(f"   ℹ️  Процесс {process.pid} уже завершен")
                    
            except Exception as e:
                print(f"   ⚠️ Ошибка остановки процесса {process.pid}: {e}")
        
        self.processes.clear()
        print("✅ Система остановлена")
    
    def start_gui(self, obelisk_process):
        """Запуск GUI интерфейса"""
        print("\n" + "=" * 60)
        print("🖥️  ЗАПУСК ГРАФИЧЕСКОГО ИНТЕРФЕЙСА")
        print("=" * 60)
        
        try:
            # Попытка запустить GUI в отдельном процессе
            gui_script = self.project_root / "scripts" / "run_econet.py"
            
            if not gui_script.exists():
                print("   ⚠️ Скрипт запуска GUI не найден")
                print(f"   Путь: {gui_script}")
                return None
            
            print("   [INFO] Запускаю GUI интерфейс...")
            sys.stdout.flush()
            
            # Запускаем GUI в отдельном процессе
            gui_process = subprocess.Popen(
                [sys.executable, str(gui_script)],
                cwd=self.project_root,
                stdout=None,
                stderr=None
            )
            
            self.processes.append(gui_process)
            print(f"   ✅ GUI интерфейс запущен (PID: {gui_process.pid})")
            sys.stdout.flush()
            
            return gui_process
            
        except Exception as e:
            print(f"   ⚠️ Ошибка запуска GUI: {e}")
            print("   💡 Можно запустить GUI вручную: python scripts/run_econet.py")
            sys.stdout.flush()
            return None
    
    def run(self, start_gui: bool = True):
        """Главная функция запуска
        
        Args:
            start_gui: Запускать ли GUI интерфейс автоматически
        """
        print("=" * 60)
        print("🚀 ЗАПУСК СИСТЕМЫ ЭКОНЕТ")
        print("=" * 60)
        print(f"Время: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()
        
        # 1. Проверка MQTT брокера
        if not self.check_mqtt_broker():
            print("\n💡 Попытка запуска MQTT брокера...")
            if not self.start_mqtt_broker():
                print("⚠️ Продолжаем без MQTT брокера (некоторые функции могут не работать)")
        
        # 2. Запуск Обелиска
        obelisk_process = self.start_obelisk()
        if not obelisk_process:
            print("❌ Не удалось запустить Обелиск")
            return False
        
        # 3. Ожидание готовности
        if not self.wait_for_obelisk():
            print("⚠️ Обелиск запущен, но не отвечает на health check")
        
        # 4. Проверка системы
        health_ok = self.check_system_health()
        
        # 5. Итоги
        print("\n" + "=" * 60)
        print("📊 ИТОГИ ЗАПУСКА")
        print("=" * 60)
        sys.stdout.flush()
        
        host = self.config.get('obelisk', {}).get('host', 'localhost')
        port = self.config.get('obelisk', {}).get('port', 8000)
        
        print(f"✅ Обелиск запущен")
        print(f"   🌐 API: http://{host}:{port}")
        print(f"   📚 Документация: http://{host}:{port}/docs")
        print(f"   ❤️ Health: http://{host}:{port}/health")
        sys.stdout.flush()
        
        if health_ok:
            print("\n✅ Система работает корректно!")
        else:
            print("\n⚠️ Некоторые проверки не пройдены, но система запущена")
        
        # 6. Запуск GUI (если нужно)
        gui_process = None
        if start_gui:
            gui_process = self.start_gui(obelisk_process)
        
        print("\n💡 Для остановки нажмите Ctrl+C")
        if not gui_process:
            print("💡 Для запуска GUI: python scripts/run_econet.py")
        print("=" * 60)
        print()
        print("📡 Система работает. Ожидание завершения...")
        if gui_process:
            print("   (GUI интерфейс должен открыться в отдельном окне)")
        print("   (Вывод сервера отображается выше)")
        print()
        sys.stdout.flush()  # Принудительно выводим перед циклом ожидания
        
        # Ожидание завершения
        try:
            last_status_time = time.time()
            status_interval = 30  # Выводить статус каждые 30 секунд
            
            while self.running:
                # Проверка что процесс еще работает
                if obelisk_process.poll() is not None:
                    print("\n" + "=" * 60)
                    print("⚠️ Обелиск завершился неожиданно")
                    print(f"   Код возврата: {obelisk_process.returncode}")
                    break
                
                # Периодический вывод статуса
                current_time = time.time()
                if current_time - last_status_time >= status_interval:
                    elapsed = int(current_time - last_status_time)
                    print(f"\n[STATUS] Система работает уже {elapsed // 60} мин {elapsed % 60} сек (PID: {obelisk_process.pid})")
                    sys.stdout.flush()  # Принудительный вывод статуса
                    last_status_time = current_time
                
                # Небольшая задержка для снижения нагрузки на CPU
                time.sleep(1)
                    
        except KeyboardInterrupt:
            print("\n" + "=" * 60)
            print("🛑 Получен сигнал остановки...")
        finally:
            self.stop_all()
        
        return True


def main():
    """Точка входа"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Запуск системы ЭкоНет')
    parser.add_argument(
        '--no-gui',
        action='store_true',
        help='Не запускать GUI интерфейс (только API сервер)'
    )
    
    args = parser.parse_args()
    
    launcher = EcoNetSystemLauncher()
    success = launcher.run(start_gui=not args.no_gui)
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())

