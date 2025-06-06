# migration_add_min_quantity.py
# Файл для добавления поля min_quantity в существующую БД с SQLAlchemy

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text
import os

# Настройки приложения
basedir = os.path.abspath(os.path.dirname(__file__))
db_dir = os.path.join(basedir, 'database')

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{os.path.join(db_dir, "inventory.db")}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)


def migrate():
    """Добавляет поле min_quantity в таблицу item"""
    with app.app_context():
        try:
            # Проверяем, существует ли уже колонка
            result = db.session.execute(text("PRAGMA table_info(item)"))
            columns = [row[1] for row in result]

            if 'min_quantity' not in columns:
                # Добавляем колонку min_quantity с значением по умолчанию 10
                db.session.execute(text("ALTER TABLE item ADD COLUMN min_quantity INTEGER DEFAULT 10"))

                # Добавляем колонку updated_at если её нет
                if 'updated_at' not in columns:
                    db.session.execute(text("ALTER TABLE item ADD COLUMN updated_at DATETIME"))
                    # Устанавливаем текущее время для всех записей
                    db.session.execute(text("UPDATE item SET updated_at = CURRENT_TIMESTAMP"))

                db.session.commit()
                print("✅ Миграция выполнена успешно!")
                print("   - Добавлена колонка min_quantity (по умолчанию: 10)")
                if 'updated_at' not in columns:
                    print("   - Добавлена колонка updated_at")

                # Устанавливаем разумные значения min_quantity для существующих товаров
                db.session.execute(text("""
                                        UPDATE item
                                        SET min_quantity = CASE
                                                               WHEN quantity < 10 THEN 5
                                                               WHEN quantity < 50 THEN 10
                                                               WHEN quantity < 100 THEN 20
                                                               ELSE 30
                                            END
                                        """))
                db.session.commit()
                print("   - Установлены начальные значения минимальных остатков")

            else:
                print("ℹ️ Колонка min_quantity уже существует")

        except Exception as e:
            print(f"❌ Ошибка при миграции: {e}")
            db.session.rollback()


if __name__ == "__main__":
    migrate()