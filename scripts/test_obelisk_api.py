"""
Быстрый тест API Обелиска
"""

import sys
import requests
import time

def test_obelisk_api():
    """Тест API endpoints Обелиска"""
    base_url = "http://localhost:8000"
    
    print("=" * 60)
    print("🧪 Тест API Обелиска")
    print("=" * 60)
    
    # Ожидание запуска сервера
    print("⏳ Ожидание запуска сервера...")
    max_attempts = 10
    for i in range(max_attempts):
        try:
            response = requests.get(f"{base_url}/health", timeout=2)
            if response.status_code == 200:
                print("✅ Сервер запущен!")
                break
        except requests.exceptions.ConnectionError:
            if i < max_attempts - 1:
                print(f"   Попытка {i+1}/{max_attempts}...")
                time.sleep(1)
            else:
                print("❌ Сервер не запущен")
                print("   Запустите: python -m obelisk.api.main")
                return False
        except Exception as e:
            print(f"❌ Ошибка: {e}")
            return False
    else:
        print("❌ Сервер не отвечает")
        return False
    
    # Тест endpoints
    endpoints = [
        ("/", "Root"),
        ("/health", "Health check"),
        ("/docs", "API documentation"),
    ]
    
    print("\n📋 Проверка endpoints:")
    results = []
    
    for endpoint, name in endpoints:
        try:
            url = f"{base_url}{endpoint}"
            response = requests.get(url, timeout=5)
            
            if response.status_code == 200:
                print(f"   ✅ {name}: {response.status_code}")
                results.append(True)
            else:
                print(f"   ⚠️ {name}: {response.status_code}")
                results.append(False)
        except Exception as e:
            print(f"   ❌ {name}: {e}")
            results.append(False)
    
    # Проверка health endpoint детально
    try:
        response = requests.get(f"{base_url}/health", timeout=5)
        if response.status_code == 200:
            health_data = response.json()
            print("\n📊 Статус системы:")
            print(f"   Status: {health_data.get('status', 'N/A')}")
            
            if 'services' in health_data:
                services = health_data['services']
                print("   Services:")
                for service, status in services.items():
                    status_icon = "✅" if status else "❌"
                    print(f"      {status_icon} {service}: {status}")
    except Exception as e:
        print(f"   ⚠️ Не удалось получить детальную информацию: {e}")
    
    print("\n" + "=" * 60)
    if all(results):
        print("✅ ВСЕ ТЕСТЫ ПРОЙДЕНЫ")
    else:
        print("⚠️ НЕКОТОРЫЕ ТЕСТЫ НЕ ПРОЙДЕНЫ")
    print("=" * 60)
    
    return all(results)


if __name__ == "__main__":
    success = test_obelisk_api()
    sys.exit(0 if success else 1)

