import os
import sys
import webbrowser
from threading import Timer


def open_browser():
    """Открыть браузер после запуска сервера"""
    webbrowser.open('http://localhost:5090')


if __name__ == '__main__':
    # Проверка, существует ли база данных
    if not os.path.exists('database'):
        os.makedirs('database')

    if not os.path.exists('database/inventory.db'):
        print("База данных не найдена. Создаю новую...")
        from init_db import init_database

        init_database()

    # Импорт и запуск приложения
    from app import app

    print("\n" + "=" * 50)
    print("🚀 Vittavento Inventory Management System")
    print("=" * 50)
    print("\nСервер запущен на: http://localhost:5090")
    print("Для остановки нажмите Ctrl+C")
    print("\n" + "=" * 50 + "\n")

    # Открыть браузер через 1.5 секунды
    Timer(1.5, open_browser).start()

    # Запуск Flask приложения
    app.run(debug=True, host='0.0.0.0', port=5090)