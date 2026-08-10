import asyncio
import hashlib
import hmac
import html
import json
import logging
import mimetypes
import sqlite3
import sys
import time
from datetime import date, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple
from urllib.parse import parse_qsl, quote
from uuid import uuid4

import config
from aiohttp import web
from aiogram import Bot, Dispatcher, F, Router
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import (
    BotCommand,
    CallbackQuery,
    BufferedInputFile,
    FSInputFile,
    InputMediaPhoto,
    MenuButtonWebApp,
    Message,
    User,
    WebAppInfo,
)

from keyboards import (
    addon_card_keyboard,
    addons_list_keyboard,
    addons_select_keyboard,
    admin_menu_keyboard,
    admin_order_card_keyboard,
    admin_order_filters_keyboard,
    admin_orders_list_keyboard,
    back_to_main_keyboard,
    catalog_admin_menu_keyboard,
    catalog_cancel_keyboard,
    categories_list_keyboard,
    category_card_keyboard,
    category_select_keyboard,
    main_menu_keyboard,
    product_card_keyboard,
    product_create_confirm_keyboard,
    product_delete_confirm_keyboard,
    product_gallery_keyboard,
    products_list_keyboard,
    featured_products_keyboard,
    featured_candidates_keyboard,
)


BOT_TOKEN: str = config.BOT_TOKEN
MINI_APP_URL: str = getattr(config, "MINI_APP_URL", "https://example.com")
_configured_database_path = Path(
    getattr(config, "DATABASE_PATH", "bloombox.db")
)
DATABASE_PATH = (
    _configured_database_path
    if _configured_database_path.is_absolute()
    else Path(__file__).resolve().parent / _configured_database_path
)

WEB_HOST: str = str(getattr(config, "WEB_HOST", "0.0.0.0"))
WEB_PORT: int = int(getattr(config, "WEB_PORT", 8080))
INIT_DATA_MAX_AGE: int = int(
    getattr(config, "INIT_DATA_MAX_AGE", 86400)
)
_configured_webapp_dir = Path(
    getattr(config, "WEBAPP_DIR", "webapp")
)
WEBAPP_DIR = (
    _configured_webapp_dir
    if _configured_webapp_dir.is_absolute()
    else Path(__file__).resolve().parent / _configured_webapp_dir
)

ADMIN_IDS: Set[int] = {
    int(admin_id)
    for admin_id in getattr(config, "ADMIN_IDS", [])
}

router = Router()

MAX_PRODUCT_IMAGES = 8
MAX_MAILING_MEDIA_BYTES = 25 * 1024 * 1024
ORDER_STATUS_LABELS = {
    "new": "Новый",
    "accepted": "Принят",
    "assembling": "Собирается",
    "courier": "Передан курьеру",
    "delivered": "Доставлен",
    "cancelled": "Отменён",
}

ORDER_STATUS_EMOJIS = {
    "new": "🆕",
    "accepted": "✅",
    "assembling": "🌷",
    "courier": "🚚",
    "delivered": "🎉",
    "cancelled": "❌",
}

ORDER_FILTER_STATUSES = {
    "new": ("new",),
    "active": ("accepted", "assembling"),
    "courier": ("courier",),
    "completed": ("delivered",),
    "cancelled": ("cancelled",),
    "all": (),
}

ORDER_FILTER_TITLES = {
    "new": "Новые заказы 🆕",
    "active": "Заказы в работе 🌷",
    "courier": "Заказы у курьера 🚚",
    "completed": "Завершённые заказы 🎉",
    "cancelled": "Отменённые заказы ❌",
    "all": "Все заказы 📋",
}

ALLOWED_STATUS_TRANSITIONS = {
    "new": {"accepted", "cancelled"},
    "accepted": {"assembling", "cancelled"},
    "assembling": {"courier", "cancelled"},
    "courier": {"delivered", "cancelled"},
    "delivered": set(),
    "cancelled": set(),
}

STATUS_NOTIFICATION_TEXTS = {
    "accepted": "Ваш заказ <b>{order_number}</b> принят ✅",
    "assembling": "Мы начали собирать заказ <b>{order_number}</b> 🌷",
    "courier": "Заказ <b>{order_number}</b> передан курьеру 🚚",
    "delivered": "Заказ <b>{order_number}</b> доставлен. Спасибо! 🎉",
    "cancelled": "Заказ <b>{order_number}</b> отменён ❌",
}


# ============================================================
# БАЗА ДАННЫХ
# ============================================================


def get_db_connection() -> sqlite3.Connection:
    """Создаёт новое соединение с SQLite."""
    connection = sqlite3.connect(DATABASE_PATH, timeout=20)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def initialize_database_sync() -> None:
    """Создаёт файл базы, таблицы, индексы и демонстрационный каталог."""
    DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)

    with get_db_connection() as connection:
        connection.execute("PRAGMA journal_mode = WAL")

        connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                telegram_id INTEGER NOT NULL UNIQUE,
                username TEXT,
                first_name TEXT NOT NULL,
                last_name TEXT,
                phone TEXT,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS categories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                slug TEXT NOT NULL UNIQUE,
                position INTEGER NOT NULL DEFAULT 0,
                is_active INTEGER NOT NULL DEFAULT 1
                    CHECK (is_active IN (0, 1))
            );

            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                category_id INTEGER,
                name TEXT NOT NULL,
                slug TEXT NOT NULL UNIQUE,
                description TEXT NOT NULL DEFAULT '',
                composition TEXT NOT NULL DEFAULT '',
                base_price INTEGER NOT NULL CHECK (base_price >= 0),
                image_url TEXT,
                badge TEXT,
                is_active INTEGER NOT NULL DEFAULT 1
                    CHECK (is_active IN (0, 1)),
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (category_id)
                    REFERENCES categories(id)
                    ON DELETE SET NULL
            );

            CREATE TABLE IF NOT EXISTS featured_products (
                product_id INTEGER PRIMARY KEY,
                position INTEGER NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (product_id)
                    REFERENCES products(id)
                    ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS product_images (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                product_id INTEGER NOT NULL,
                image_url TEXT NOT NULL,
                position INTEGER NOT NULL DEFAULT 0,
                is_primary INTEGER NOT NULL DEFAULT 0
                    CHECK (is_primary IN (0, 1)),
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                UNIQUE (product_id, image_url),
                FOREIGN KEY (product_id)
                    REFERENCES products(id)
                    ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS product_variants (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                product_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                price INTEGER NOT NULL CHECK (price >= 0),
                is_default INTEGER NOT NULL DEFAULT 0
                    CHECK (is_default IN (0, 1)),
                is_active INTEGER NOT NULL DEFAULT 1
                    CHECK (is_active IN (0, 1)),
                UNIQUE (product_id, name),
                FOREIGN KEY (product_id)
                    REFERENCES products(id)
                    ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS addons (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                price INTEGER NOT NULL CHECK (price >= 0),
                image_url TEXT,
                is_active INTEGER NOT NULL DEFAULT 1
                    CHECK (is_active IN (0, 1))
            );

            CREATE TABLE IF NOT EXISTS product_addons (
                product_id INTEGER NOT NULL,
                addon_id INTEGER NOT NULL,
                PRIMARY KEY (product_id, addon_id),
                FOREIGN KEY (product_id)
                    REFERENCES products(id)
                    ON DELETE CASCADE,
                FOREIGN KEY (addon_id)
                    REFERENCES addons(id)
                    ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                order_number TEXT UNIQUE,
                user_id INTEGER NOT NULL,
                customer_name TEXT NOT NULL,
                customer_phone TEXT,
                recipient_name TEXT,
                recipient_phone TEXT,
                delivery_type TEXT NOT NULL DEFAULT 'delivery'
                    CHECK (delivery_type IN ('delivery', 'pickup')),
                address TEXT,
                delivery_date TEXT,
                delivery_interval TEXT,
                postcard_text TEXT,
                comment TEXT,
                subtotal INTEGER NOT NULL DEFAULT 0 CHECK (subtotal >= 0),
                delivery_price INTEGER NOT NULL DEFAULT 0
                    CHECK (delivery_price >= 0),
                total INTEGER NOT NULL DEFAULT 0 CHECK (total >= 0),
                status TEXT NOT NULL DEFAULT 'new'
                    CHECK (
                        status IN (
                            'new',
                            'accepted',
                            'assembling',
                            'courier',
                            'delivered',
                            'cancelled'
                        )
                    ),
                payment_status TEXT NOT NULL DEFAULT 'unpaid'
                    CHECK (
                        payment_status IN (
                            'unpaid',
                            'pending',
                            'paid',
                            'refunded'
                        )
                    ),
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id)
                    REFERENCES users(id)
                    ON DELETE RESTRICT
            );

            CREATE TABLE IF NOT EXISTS order_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                order_id INTEGER NOT NULL,
                product_id INTEGER,
                product_name TEXT NOT NULL,
                variant_id INTEGER,
                variant_name TEXT,
                unit_price INTEGER NOT NULL CHECK (unit_price >= 0),
                quantity INTEGER NOT NULL CHECK (quantity > 0),
                line_total INTEGER NOT NULL CHECK (line_total >= 0),
                FOREIGN KEY (order_id)
                    REFERENCES orders(id)
                    ON DELETE CASCADE,
                FOREIGN KEY (product_id)
                    REFERENCES products(id)
                    ON DELETE SET NULL,
                FOREIGN KEY (variant_id)
                    REFERENCES product_variants(id)
                    ON DELETE SET NULL
            );

            CREATE TABLE IF NOT EXISTS order_item_addons (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                order_item_id INTEGER NOT NULL,
                addon_id INTEGER,
                addon_name TEXT NOT NULL,
                unit_price INTEGER NOT NULL CHECK (unit_price >= 0),
                quantity INTEGER NOT NULL CHECK (quantity > 0),
                line_total INTEGER NOT NULL CHECK (line_total >= 0),
                FOREIGN KEY (order_item_id)
                    REFERENCES order_items(id)
                    ON DELETE CASCADE,
                FOREIGN KEY (addon_id)
                    REFERENCES addons(id)
                    ON DELETE SET NULL
            );

            CREATE TABLE IF NOT EXISTS order_status_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                order_id INTEGER NOT NULL,
                old_status TEXT,
                new_status TEXT NOT NULL,
                changed_by_telegram_id INTEGER,
                comment TEXT,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (order_id)
                    REFERENCES orders(id)
                    ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS app_settings (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            );

            CREATE INDEX IF NOT EXISTS idx_products_category
                ON products(category_id);

            CREATE INDEX IF NOT EXISTS idx_products_active
                ON products(is_active);

            CREATE INDEX IF NOT EXISTS idx_featured_products_position
                ON featured_products(position, product_id);

            CREATE INDEX IF NOT EXISTS idx_product_images_product
                ON product_images(product_id, position, id);

            CREATE INDEX IF NOT EXISTS idx_orders_user
                ON orders(user_id, created_at DESC);

            CREATE INDEX IF NOT EXISTS idx_orders_status
                ON orders(status, created_at DESC);

            CREATE INDEX IF NOT EXISTS idx_order_items_order
                ON order_items(order_id);
            """
        )

        product_columns = {
            str(row["name"])
            for row in connection.execute(
                "PRAGMA table_info(products)"
            ).fetchall()
        }
        if "composition" not in product_columns:
            connection.execute(
                """
                ALTER TABLE products
                ADD COLUMN composition TEXT NOT NULL DEFAULT ''
                """
            )

        seed_database(connection)
        connection.commit()


def seed_database(connection: sqlite3.Connection) -> None:
    """Добавляет базовые настройки и демонстрационные товары один раз."""
    settings = {
        "store_name": "BloomBox",
        "delivery_price": "390",
        "free_delivery_from": "5000",
        "currency": "RUB",
        "pickup_address": "",
    }

    for key, value in settings.items():
        connection.execute(
            "INSERT OR IGNORE INTO app_settings(key, value) VALUES (?, ?)",
            (key, value),
        )

    # В каталоге используются только три фиксированных типа товаров.
    # Старые тематические категории автоматически удаляются, а существующие
    # товары безопасно переносятся в раздел «Букеты».
    categories = [
        ("Букеты", "bouquets", 10),
        ("Открытки", "postcards", 20),
        ("Мягкие игрушки", "soft-toys", 30),
    ]

    connection.executemany(
        """
        INSERT INTO categories(name, slug, position, is_active)
        VALUES (?, ?, ?, 1)
        ON CONFLICT(slug) DO UPDATE SET
            name = excluded.name,
            position = excluded.position,
            is_active = 1
        """,
        categories,
    )

    category_ids = {
        row["slug"]: int(row["id"])
        for row in connection.execute(
            """
            SELECT id, slug
            FROM categories
            WHERE slug IN ('bouquets', 'postcards', 'soft-toys')
            """
        ).fetchall()
    }

    fixed_category_ids = tuple(category_ids.values())
    fixed_placeholders = ",".join("?" for _ in fixed_category_ids)
    connection.execute(
        """
        UPDATE products
        SET category_id = ?
        WHERE category_id IS NULL
           OR category_id NOT IN ({0})
        """.format(fixed_placeholders),
        (category_ids["bouquets"], *fixed_category_ids),
    )
    connection.execute(
        """
        DELETE FROM categories
        WHERE id NOT IN ({0})
        """.format(fixed_placeholders),
        fixed_category_ids,
    )

    products = [
        (
            category_ids["bouquets"],
            "Розовый рассвет",
            "pink-sunrise",
            "Нежный букет из роз и эвкалипта.",
            2490,
            "images/rozovyi-rassvet.webp",
            "Хит",
        ),
        (
            category_ids["bouquets"],
            "Солнечный день",
            "sunny-day",
            "Яркая композиция с герберами и хризантемами.",
            2290,
            "images/solnechnyi-den.webp",
            "Новинка",
        ),
        (
            category_ids["bouquets"],
            "Лавандовый воздух",
            "lavender-air",
            "Авторский букет в спокойной сиреневой гамме.",
            3190,
            "images/lavandovyi-vozdukh.webp",
            None,
        ),
        (
            category_ids["bouquets"],
            "Белое облако",
            "white-cloud",
            "Воздушный букет из белых цветов.",
            2790,
            "images/beloe-oblako.webp",
            None,
        ),
        (
            category_ids["bouquets"],
            "Ягодный мусс",
            "berry-mousse",
            "Розово-бордовая композиция для яркого поздравления.",
            2990,
            "images/iagodnyi-muss.webp",
            "Хит",
        ),
        (
            category_ids["bouquets"],
            "Тихий сад",
            "quiet-garden",
            "Глубокие красные розы в лаконичной натуральной упаковке.",
            3490,
            "images/tikhii-sad.webp",
            None,
        ),
        (
            category_ids["bouquets"],
            "Ночной тюльпан",
            "night-tulip",
            "Стройные розовые тюльпаны с плотной зеленью и выразительным тёмным настроением.",
            2690,
            "images/pink-tulips.webp",
            "Новинка",
        ),
        (
            category_ids["bouquets"],
            "Голубой фарфор",
            "blue-porcelain",
            "Орхидеи, гвоздики и воздушные акценты в контрастной чёрной упаковке.",
            4590,
            "images/blue-orchid.webp",
            "Limited",
        ),
        (
            category_ids["bouquets"],
            "Весенний калейдоскоп",
            "spring-kaleidoscope",
            "Разноцветные тюльпаны для яркого поздравления и мгновенного весеннего настроения.",
            3490,
            "images/color-tulips.webp",
            "Хит",
        ),
        (
            category_ids["bouquets"],
            "Облачный сон",
            "cloud-dream",
            "Мягкая композиция из пастельных роз и ромашек с эффектом плёночной фотографии.",
            3890,
            "images/pastel-dream.webp",
            None,
        ),
        (
            category_ids["bouquets"],
            "Абрикосовый свет",
            "apricot-light",
            "Тёплые абрикосовые тюльпаны — лёгкий букет для комплимента без повода.",
            2890,
            "images/apricot-tulips.webp",
            "Новинка",
        ),
        (
            category_ids["bouquets"],
            "Летний обет",
            "summer-vow",
            "Садовый букет с дельфиниумом, розами и полевыми цветами в свадебной эстетике.",
            5290,
            "images/wedding-meadow.webp",
            "Premium",
        ),
    ]

    connection.executemany(
        """
        INSERT OR IGNORE INTO products(
            category_id,
            name,
            slug,
            description,
            base_price,
            image_url,
            badge
        )
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        products,
    )

    demo_compositions = {
        "pink-sunrise": "Розы, гортензия, орхидеи, эвкалипт",
        "sunny-day": "Герберы, хризантемы, зелень",
        "lavender-air": "Гортензия, диантус, розы, эвкалипт",
        "white-cloud": "Белые розы, эвкалипт",
        "berry-mousse": "Пионовидные розы, кустовые розы, эвкалипт",
        "quiet-garden": "Красные розы, эвкалипт",
        "night-tulip": "Розовые тюльпаны, декоративная зелень",
        "blue-porcelain": "Орхидеи, гвоздики, эвкалипт",
        "spring-kaleidoscope": "Разноцветные тюльпаны",
        "cloud-dream": "Розы, ромашки, эвкалипт",
        "apricot-light": "Абрикосовые тюльпаны",
        "summer-vow": "Дельфиниум, розы, полевые цветы, зелень",
    }

    for slug, composition in demo_compositions.items():
        connection.execute(
            """
            UPDATE products
            SET composition = ?
            WHERE slug = ?
              AND TRIM(COALESCE(composition, '')) = ''
            """,
            (composition, slug),
        )

    product_rows = connection.execute(
        "SELECT id, slug, base_price, image_url FROM products"
    ).fetchall()

    # В версии v24 демонстрационная галерея ошибочно содержала
    # фотографии разных букетов. Удаляем только эти известные
    # автоматически подставленные изображения. Фото, которые администратор
    # загрузил через Telegram или добавил ссылкой, не затрагиваются.
    legacy_demo_extras_by_slug = {
        "pink-sunrise": {
            "images/pastel-dream.webp",
            "images/iagodnyi-muss.webp",
        },
        "sunny-day": {
            "images/tikhii-sad.webp",
            "images/wedding-meadow.webp",
        },
        "lavender-air": {
            "images/blue-orchid.webp",
            "images/pastel-dream.webp",
        },
        "white-cloud": {
            "images/wedding-meadow.webp",
            "images/apricot-tulips.webp",
        },
        "berry-mousse": {
            "images/rozovyi-rassvet.webp",
            "images/tikhii-sad.webp",
        },
        "quiet-garden": {
            "images/solnechnyi-den.webp",
            "images/iagodnyi-muss.webp",
        },
        "night-tulip": {
            "images/apricot-tulips.webp",
            "images/color-tulips.webp",
        },
        "blue-porcelain": {
            "images/lavandovyi-vozdukh.webp",
            "images/beloe-oblako.webp",
        },
        "spring-kaleidoscope": {
            "images/pink-tulips.webp",
            "images/apricot-tulips.webp",
        },
        "cloud-dream": {
            "images/rozovyi-rassvet.webp",
            "images/beloe-oblako.webp",
        },
        "apricot-light": {
            "images/pink-tulips.webp",
            "images/color-tulips.webp",
        },
        "summer-vow": {
            "images/beloe-oblako.webp",
            "images/blue-orchid.webp",
        },
    }

    for product in product_rows:
        product_id = int(product["id"])
        slug = str(product["slug"])
        image_url = (
            str(product["image_url"])
            if product["image_url"]
            else None
        )

        legacy_extras = legacy_demo_extras_by_slug.get(slug, set())
        if legacy_extras:
            placeholders = ",".join("?" for _ in legacy_extras)
            connection.execute(
                """
                DELETE FROM product_images
                WHERE product_id = ?
                  AND is_primary = 0
                  AND image_url IN ({0})
                """.format(placeholders),
                (product_id, *sorted(legacy_extras)),
            )

        existing_images = connection.execute(
            """
            SELECT id, image_url, is_primary
            FROM product_images
            WHERE product_id = ?
            ORDER BY is_primary DESC, position ASC, id ASC
            """,
            (product_id,),
        ).fetchall()

        if not existing_images and image_url:
            connection.execute(
                """
                INSERT INTO product_images(
                    product_id,
                    image_url,
                    position,
                    is_primary
                )
                VALUES (?, ?, 0, 1)
                """,
                (product_id, image_url),
            )
        elif existing_images and not any(
            bool(row["is_primary"]) for row in existing_images
        ):
            preferred = next(
                (
                    row
                    for row in existing_images
                    if image_url and str(row["image_url"]) == image_url
                ),
                existing_images[0],
            )
            connection.execute(
                """
                UPDATE product_images
                SET is_primary = 1, position = 0
                WHERE id = ?
                """,
                (int(preferred["id"]),),
            )
            connection.execute(
                """
                UPDATE products
                SET image_url = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (str(preferred["image_url"]), product_id),
            )

        base_price = int(product["base_price"])
        variants = [
            (product["id"], "S", base_price, 1),
            (product["id"], "M", base_price + 1000, 0),
            (product["id"], "L", base_price + 2500, 0),
        ]
        connection.executemany(
            """
            INSERT OR IGNORE INTO product_variants(
                product_id,
                name,
                price,
                is_default
            )
            VALUES (?, ?, ?, ?)
            """,
            variants,
        )

    addons = [
        ("Открытка", 200, None),
        ("Конфеты", 690, None),
        ("Мягкая игрушка", 990, None),
    ]

    connection.executemany(
        """
        INSERT OR IGNORE INTO addons(name, price, image_url)
        VALUES (?, ?, ?)
        """,
        addons,
    )

    connection.execute(
        """
        INSERT OR IGNORE INTO product_addons(product_id, addon_id)
        SELECT products.id, addons.id
        FROM products
        CROSS JOIN addons
        """
    )

    featured_initialized = connection.execute(
        "SELECT value FROM app_settings WHERE key = ?",
        ("featured_products_initialized",),
    ).fetchone()
    if featured_initialized is None:
        initial_featured = connection.execute(
            """
            SELECT id
            FROM products
            WHERE is_active = 1
            ORDER BY id DESC
            LIMIT 3
            """
        ).fetchall()
        for position, row in enumerate(initial_featured):
            connection.execute(
                """
                INSERT OR IGNORE INTO featured_products(
                    product_id, position
                )
                VALUES (?, ?)
                """,
                (int(row["id"]), position),
            )
        connection.execute(
            """
            INSERT OR REPLACE INTO app_settings(key, value)
            VALUES (?, ?)
            """,
            ("featured_products_initialized", "1"),
        )


def upsert_user_sync(user: User) -> None:
    """Создаёт пользователя или обновляет его Telegram-данные."""
    with get_db_connection() as connection:
        connection.execute(
            """
            INSERT INTO users(
                telegram_id,
                username,
                first_name,
                last_name
            )
            VALUES (?, ?, ?, ?)
            ON CONFLICT(telegram_id) DO UPDATE SET
                username = excluded.username,
                first_name = excluded.first_name,
                last_name = excluded.last_name,
                updated_at = CURRENT_TIMESTAMP
            """,
            (
                user.id,
                user.username,
                user.first_name or "Пользователь",
                user.last_name,
            ),
        )
        connection.commit()


def get_user_orders_sync(
    telegram_id: int,
    limit: int = 10,
) -> List[sqlite3.Row]:
    """Возвращает последние заказы пользователя."""
    with get_db_connection() as connection:
        return connection.execute(
            """
            SELECT
                orders.order_number,
                orders.total,
                orders.status,
                orders.delivery_date,
                orders.delivery_interval,
                orders.created_at
            FROM orders
            JOIN users ON users.id = orders.user_id
            WHERE users.telegram_id = ?
            ORDER BY orders.id DESC
            LIMIT ?
            """,
            (telegram_id, limit),
        ).fetchall()


def get_orders_sync(
    status: Optional[str] = None,
    limit: int = 10,
) -> List[sqlite3.Row]:
    """Возвращает заказы для админ-панели."""
    query = """
        SELECT
            orders.order_number,
            orders.customer_name,
            orders.total,
            orders.status,
            orders.delivery_date,
            orders.delivery_interval,
            orders.created_at
        FROM orders
    """
    parameters: List[Any] = []

    if status is not None:
        query += " WHERE orders.status = ?"
        parameters.append(status)

    query += " ORDER BY orders.id DESC LIMIT ?"
    parameters.append(limit)

    with get_db_connection() as connection:
        return connection.execute(query, parameters).fetchall()


def normalize_filter_key(filter_key: str) -> str:
    """Возвращает допустимый ключ фильтра заказов."""
    if filter_key in ORDER_FILTER_STATUSES:
        return filter_key
    return "all"


def build_status_condition(
    filter_key: str,
) -> Tuple[str, List[Any]]:
    """Формирует SQL-условие по выбранному фильтру."""
    filter_key = normalize_filter_key(filter_key)
    statuses = ORDER_FILTER_STATUSES[filter_key]

    if not statuses:
        return "", []

    placeholders = ", ".join("?" for _ in statuses)
    return " WHERE orders.status IN ({0})".format(placeholders), list(statuses)


def get_order_counts_sync() -> Dict[str, int]:
    """Возвращает количества заказов для всех фильтров."""
    with get_db_connection() as connection:
        rows = connection.execute(
            """
            SELECT status, COUNT(*) AS amount
            FROM orders
            GROUP BY status
            """
        ).fetchall()

    by_status = {
        str(row["status"]): int(row["amount"] or 0)
        for row in rows
    }

    return {
        "new": by_status.get("new", 0),
        "active": (
            by_status.get("accepted", 0)
            + by_status.get("assembling", 0)
        ),
        "courier": by_status.get("courier", 0),
        "completed": by_status.get("delivered", 0),
        "cancelled": by_status.get("cancelled", 0),
        "all": sum(by_status.values()),
    }


def get_orders_page_sync(
    filter_key: str,
    page: int,
    page_size: int = 5,
) -> Dict[str, Any]:
    """Возвращает одну страницу заказов для админ-панели."""
    filter_key = normalize_filter_key(filter_key)
    page = max(int(page), 0)
    page_size = max(int(page_size), 1)

    where_sql, parameters = build_status_condition(filter_key)

    with get_db_connection() as connection:
        total_row = connection.execute(
            "SELECT COUNT(*) AS amount FROM orders" + where_sql,
            parameters,
        ).fetchone()
        total = int(total_row["amount"] or 0)
        total_pages = max((total + page_size - 1) // page_size, 1)

        if page >= total_pages:
            page = total_pages - 1

        offset = page * page_size

        rows = connection.execute(
            """
            SELECT
                orders.id,
                orders.order_number,
                orders.customer_name,
                orders.total,
                orders.status,
                orders.delivery_date,
                orders.delivery_interval,
                orders.created_at
            FROM orders
            """
            + where_sql
            + " ORDER BY orders.id DESC LIMIT ? OFFSET ?",
            parameters + [page_size, offset],
        ).fetchall()

    return {
        "filter_key": filter_key,
        "page": page,
        "page_size": page_size,
        "total": total,
        "total_pages": total_pages,
        "rows": rows,
    }


def get_order_details_sync(order_id: int) -> Optional[Dict[str, Any]]:
    """Возвращает заказ, состав и историю статусов."""
    with get_db_connection() as connection:
        order = connection.execute(
            """
            SELECT
                orders.*,
                users.telegram_id,
                users.username,
                users.first_name AS telegram_first_name,
                users.last_name AS telegram_last_name
            FROM orders
            JOIN users ON users.id = orders.user_id
            WHERE orders.id = ?
            """,
            (order_id,),
        ).fetchone()

        if order is None:
            return None

        item_rows = connection.execute(
            """
            SELECT *
            FROM order_items
            WHERE order_id = ?
            ORDER BY id ASC
            """,
            (order_id,),
        ).fetchall()

        items: List[Dict[str, Any]] = []
        for item_row in item_rows:
            addons = connection.execute(
                """
                SELECT *
                FROM order_item_addons
                WHERE order_item_id = ?
                ORDER BY id ASC
                """,
                (item_row["id"],),
            ).fetchall()

            item = dict(item_row)
            item["addons"] = [dict(addon) for addon in addons]
            items.append(item)

        history = connection.execute(
            """
            SELECT *
            FROM order_status_history
            WHERE order_id = ?
            ORDER BY id DESC
            """,
            (order_id,),
        ).fetchall()

    return {
        "order": dict(order),
        "items": items,
        "history": [dict(row) for row in history],
    }


def get_adjacent_order_ids_sync(
    order_id: int,
    filter_key: str,
) -> Tuple[Optional[int], Optional[int]]:
    """Возвращает соседние заказы в текущем фильтре."""
    filter_key = normalize_filter_key(filter_key)
    where_sql, parameters = build_status_condition(filter_key)

    extra = " AND " if where_sql else " WHERE "

    with get_db_connection() as connection:
        previous_row = connection.execute(
            "SELECT MIN(orders.id) AS id FROM orders"
            + where_sql
            + extra
            + "orders.id > ?",
            parameters + [order_id],
        ).fetchone()

        next_row = connection.execute(
            "SELECT MAX(orders.id) AS id FROM orders"
            + where_sql
            + extra
            + "orders.id < ?",
            parameters + [order_id],
        ).fetchone()

    previous_id = (
        int(previous_row["id"])
        if previous_row and previous_row["id"] is not None
        else None
    )
    next_id = (
        int(next_row["id"])
        if next_row and next_row["id"] is not None
        else None
    )
    return previous_id, next_id


def update_order_status_sync(
    order_id: int,
    new_status: str,
    admin_telegram_id: int,
) -> Dict[str, Any]:
    """Меняет статус заказа и записывает изменение в историю."""
    if new_status not in ORDER_STATUS_LABELS:
        raise ValueError("Неизвестный статус заказа")

    with get_db_connection() as connection:
        connection.execute("BEGIN IMMEDIATE")

        row = connection.execute(
            """
            SELECT
                orders.id,
                orders.order_number,
                orders.status,
                users.telegram_id
            FROM orders
            JOIN users ON users.id = orders.user_id
            WHERE orders.id = ?
            """,
            (order_id,),
        ).fetchone()

        if row is None:
            raise ValueError("Заказ не найден")

        old_status = str(row["status"])
        if new_status == old_status:
            return {
                "changed": False,
                "order_id": order_id,
                "order_number": str(row["order_number"]),
                "old_status": old_status,
                "new_status": new_status,
                "telegram_id": int(row["telegram_id"]),
            }

        allowed = ALLOWED_STATUS_TRANSITIONS.get(old_status, set())
        if new_status not in allowed:
            raise ValueError(
                "Нельзя изменить статус «{0}» на «{1}»".format(
                    ORDER_STATUS_LABELS.get(old_status, old_status),
                    ORDER_STATUS_LABELS.get(new_status, new_status),
                )
            )

        connection.execute(
            """
            UPDATE orders
            SET status = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (new_status, order_id),
        )

        connection.execute(
            """
            INSERT INTO order_status_history(
                order_id,
                old_status,
                new_status,
                changed_by_telegram_id,
                comment
            )
            VALUES (?, ?, ?, ?, 'Статус изменён администратором')
            """,
            (
                order_id,
                old_status,
                new_status,
                admin_telegram_id,
            ),
        )

        connection.commit()

    return {
        "changed": True,
        "order_id": order_id,
        "order_number": str(row["order_number"]),
        "old_status": old_status,
        "new_status": new_status,
        "telegram_id": int(row["telegram_id"]),
    }


def create_demo_order_sync(telegram_user: User) -> Dict[str, Any]:
    """Создаёт тестовый заказ для проверки админ-панели."""
    with get_db_connection() as connection:
        product = connection.execute(
            """
            SELECT products.id AS product_id, product_variants.id AS variant_id
            FROM products
            JOIN product_variants
              ON product_variants.product_id = products.id
            WHERE products.is_active = 1
              AND product_variants.is_active = 1
            ORDER BY products.id ASC, product_variants.is_default DESC
            LIMIT 1
            """
        ).fetchone()

        addon = connection.execute(
            "SELECT id FROM addons WHERE is_active = 1 ORDER BY id LIMIT 1"
        ).fetchone()

    if product is None:
        raise RuntimeError("В базе нет активных товаров")

    raw_addons: List[Dict[str, int]] = []
    if addon is not None:
        raw_addons.append(
            {
                "addon_id": int(addon["id"]),
                "quantity": 1,
            }
        )

    demo_data: Dict[str, Any] = {
        "items": [
            {
                "product_id": int(product["product_id"]),
                "variant_id": int(product["variant_id"]),
                "quantity": 1,
                "addons": raw_addons,
            }
        ],
        "customer": {
            "name": telegram_user.full_name,
            "phone": "+7 900 000-00-00",
        },
        "recipient": {
            "name": "Получатель",
            "phone": "+7 900 111-11-11",
        },
        "delivery": {
            "type": "delivery",
            "address": "Тестовая улица, 10",
            "date": (date.today() + timedelta(days=1)).isoformat(),
            "interval": "16:00–19:00",
        },
        "postcard_text": "Тестовая открытка",
        "comment": "Демонстрационный заказ для проверки админ-панели",
    }

    return create_order_sync(telegram_user, demo_data)


def get_admin_stats_sync() -> Dict[str, int]:
    """Считает базовую статистику магазина."""
    with get_db_connection() as connection:
        row = connection.execute(
            """
            SELECT
                COUNT(*) AS order_count,
                COALESCE(
                    SUM(CASE WHEN status != 'cancelled' THEN total ELSE 0 END),
                    0
                ) AS revenue,
                COALESCE(
                    CAST(AVG(CASE WHEN status != 'cancelled' THEN total END) AS INTEGER),
                    0
                ) AS average_check,
                SUM(CASE WHEN status = 'new' THEN 1 ELSE 0 END) AS new_count
            FROM orders
            """
        ).fetchone()

        product_count = connection.execute(
            "SELECT COUNT(*) FROM products WHERE is_active = 1"
        ).fetchone()[0]

    return {
        "order_count": int(row["order_count"] or 0),
        "revenue": int(row["revenue"] or 0),
        "average_check": int(row["average_check"] or 0),
        "new_count": int(row["new_count"] or 0),
        "product_count": int(product_count or 0),
    }


def get_setting_int(
    connection: sqlite3.Connection,
    key: str,
    default: int,
) -> int:
    """Получает числовую настройку из app_settings."""
    row = connection.execute(
        "SELECT value FROM app_settings WHERE key = ?",
        (key,),
    ).fetchone()

    if row is None:
        return default

    try:
        return int(row["value"])
    except (TypeError, ValueError):
        return default


def get_setting_text(
    connection: sqlite3.Connection,
    key: str,
    default: str = "",
) -> str:
    """Получает текстовую настройку из app_settings."""
    row = connection.execute(
        "SELECT value FROM app_settings WHERE key = ?",
        (key,),
    ).fetchone()
    if row is None:
        return default
    return str(row["value"] or "").strip()


def set_setting_text_sync(key: str, value: str) -> str:
    """Сохраняет текстовую настройку магазина."""
    cleaned = str(value or "").strip()
    with get_db_connection() as connection:
        connection.execute(
            """
            INSERT INTO app_settings(key, value)
            VALUES (?, ?)
            ON CONFLICT(key) DO UPDATE SET value = excluded.value
            """,
            (key, cleaned),
        )
        connection.commit()
    return cleaned


def get_public_settings_sync() -> Dict[str, str]:
    """Возвращает публичные настройки Mini App."""
    with get_db_connection() as connection:
        return {
            "pickup_address": get_setting_text(
                connection,
                "pickup_address",
                "",
            ),
        }


def positive_int(value: Any, default: int = 1) -> int:
    """Безопасно преобразует значение в положительное целое число."""
    try:
        result = int(value)
    except (TypeError, ValueError):
        return default

    return result if result > 0 else default


def create_order_sync(
    telegram_user: User,
    data: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Создаёт настоящий заказ из данных Mini App.

    Ожидаемый формат items:
    [
        {
            "product_id": 1,
            "variant_id": 2,
            "quantity": 1,
            "addons": [{"addon_id": 1, "quantity": 1}]
        }
    ]

    Переданные из Mini App цены игнорируются. Итог считается по базе.
    """
    items = data.get("items")
    if not isinstance(items, list) or not items:
        raise ValueError("В заказе нет товаров")

    customer = data.get("customer")
    if not isinstance(customer, dict):
        customer = {}

    recipient = data.get("recipient")
    if not isinstance(recipient, dict):
        recipient = {}

    delivery = data.get("delivery")
    if not isinstance(delivery, dict):
        delivery = {}

    with get_db_connection() as connection:
        connection.execute("BEGIN IMMEDIATE")

        connection.execute(
            """
            INSERT INTO users(
                telegram_id,
                username,
                first_name,
                last_name
            )
            VALUES (?, ?, ?, ?)
            ON CONFLICT(telegram_id) DO UPDATE SET
                username = excluded.username,
                first_name = excluded.first_name,
                last_name = excluded.last_name,
                updated_at = CURRENT_TIMESTAMP
            """,
            (
                telegram_user.id,
                telegram_user.username,
                telegram_user.first_name or "Пользователь",
                telegram_user.last_name,
            ),
        )

        user_row = connection.execute(
            "SELECT id FROM users WHERE telegram_id = ?",
            (telegram_user.id,),
        ).fetchone()

        if user_row is None:
            raise RuntimeError("Не удалось сохранить пользователя")

        prepared_items: List[Dict[str, Any]] = []
        subtotal = 0

        for raw_item in items:
            if not isinstance(raw_item, dict):
                raise ValueError("Некорректный товар в заказе")

            product_id = positive_int(raw_item.get("product_id"), 0)
            if product_id <= 0:
                raise ValueError("Не указан product_id")

            product = connection.execute(
                """
                SELECT id, name, base_price
                FROM products
                WHERE id = ? AND is_active = 1
                """,
                (product_id,),
            ).fetchone()

            if product is None:
                raise ValueError("Один из товаров недоступен")

            quantity = positive_int(raw_item.get("quantity"), 1)
            variant_id_value = raw_item.get("variant_id")
            variant = None

            if variant_id_value is not None:
                variant_id = positive_int(variant_id_value, 0)
                variant = connection.execute(
                    """
                    SELECT id, name, price
                    FROM product_variants
                    WHERE id = ?
                      AND product_id = ?
                      AND is_active = 1
                    """,
                    (variant_id, product_id),
                ).fetchone()
            else:
                variant = connection.execute(
                    """
                    SELECT id, name, price
                    FROM product_variants
                    WHERE product_id = ?
                      AND is_active = 1
                    ORDER BY is_default DESC, id ASC
                    LIMIT 1
                    """,
                    (product_id,),
                ).fetchone()

            unit_price = (
                int(variant["price"])
                if variant is not None
                else int(product["base_price"])
            )
            item_total = unit_price * quantity
            subtotal += item_total

            prepared_addons: List[Dict[str, Any]] = []
            raw_addons = raw_item.get("addons", [])
            if raw_addons is None:
                raw_addons = []
            if not isinstance(raw_addons, list):
                raise ValueError("Некорректный список дополнений")

            for raw_addon in raw_addons:
                if isinstance(raw_addon, dict):
                    addon_id = positive_int(raw_addon.get("addon_id"), 0)
                    addon_quantity = positive_int(
                        raw_addon.get("quantity"),
                        1,
                    )
                else:
                    addon_id = positive_int(raw_addon, 0)
                    addon_quantity = 1

                addon = connection.execute(
                    """
                    SELECT addons.id, addons.name, addons.price
                    FROM addons
                    JOIN product_addons
                      ON product_addons.addon_id = addons.id
                    WHERE addons.id = ?
                      AND product_addons.product_id = ?
                      AND addons.is_active = 1
                    """,
                    (addon_id, product_id),
                ).fetchone()

                if addon is None:
                    raise ValueError("Одно из дополнений недоступно")

                addon_total = int(addon["price"]) * addon_quantity
                subtotal += addon_total

                prepared_addons.append(
                    {
                        "addon_id": int(addon["id"]),
                        "name": addon["name"],
                        "unit_price": int(addon["price"]),
                        "quantity": addon_quantity,
                        "line_total": addon_total,
                    }
                )

            prepared_items.append(
                {
                    "product_id": int(product["id"]),
                    "product_name": product["name"],
                    "variant_id": int(variant["id"]) if variant else None,
                    "variant_name": variant["name"] if variant else None,
                    "unit_price": unit_price,
                    "quantity": quantity,
                    "line_total": item_total,
                    "addons": prepared_addons,
                }
            )

        delivery_type = str(
            delivery.get(
                "type",
                data.get("delivery_type", "delivery"),
            )
        ).strip().lower()

        if delivery_type not in {"delivery", "pickup"}:
            delivery_type = "delivery"

        delivery_price = 0
        if delivery_type == "delivery":
            standard_delivery_price = get_setting_int(
                connection,
                "delivery_price",
                390,
            )
            free_delivery_from = get_setting_int(
                connection,
                "free_delivery_from",
                5000,
            )
            delivery_price = (
                0
                if subtotal >= free_delivery_from
                else standard_delivery_price
            )

        total = subtotal + delivery_price

        customer_name = str(
            customer.get("name")
            or data.get("customer_name")
            or telegram_user.full_name
        ).strip()

        customer_phone = customer.get("phone") or data.get("customer_phone")
        recipient_name = recipient.get("name") or data.get("recipient_name")
        recipient_phone = recipient.get("phone") or data.get("recipient_phone")
        address = delivery.get("address") or data.get("address")
        if delivery_type == "pickup":
            address = get_setting_text(connection, "pickup_address", "")
        delivery_date = delivery.get("date") or data.get("delivery_date")
        delivery_interval = (
            delivery.get("interval")
            or data.get("delivery_interval")
        )
        postcard_text = data.get("postcard_text")
        comment = data.get("comment")

        cursor = connection.execute(
            """
            INSERT INTO orders(
                user_id,
                customer_name,
                customer_phone,
                recipient_name,
                recipient_phone,
                delivery_type,
                address,
                delivery_date,
                delivery_interval,
                postcard_text,
                comment,
                subtotal,
                delivery_price,
                total,
                status,
                payment_status
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'new', 'unpaid')
            """,
            (
                int(user_row["id"]),
                customer_name,
                customer_phone,
                recipient_name,
                recipient_phone,
                delivery_type,
                address,
                delivery_date,
                delivery_interval,
                postcard_text,
                comment,
                subtotal,
                delivery_price,
                total,
            ),
        )

        order_id = int(cursor.lastrowid)
        order_number = "BB-{0:06d}".format(order_id)

        connection.execute(
            "UPDATE orders SET order_number = ? WHERE id = ?",
            (order_number, order_id),
        )

        for prepared_item in prepared_items:
            item_cursor = connection.execute(
                """
                INSERT INTO order_items(
                    order_id,
                    product_id,
                    product_name,
                    variant_id,
                    variant_name,
                    unit_price,
                    quantity,
                    line_total
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    order_id,
                    prepared_item["product_id"],
                    prepared_item["product_name"],
                    prepared_item["variant_id"],
                    prepared_item["variant_name"],
                    prepared_item["unit_price"],
                    prepared_item["quantity"],
                    prepared_item["line_total"],
                ),
            )

            order_item_id = int(item_cursor.lastrowid)

            for prepared_addon in prepared_item["addons"]:
                connection.execute(
                    """
                    INSERT INTO order_item_addons(
                        order_item_id,
                        addon_id,
                        addon_name,
                        unit_price,
                        quantity,
                        line_total
                    )
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (
                        order_item_id,
                        prepared_addon["addon_id"],
                        prepared_addon["name"],
                        prepared_addon["unit_price"],
                        prepared_addon["quantity"],
                        prepared_addon["line_total"],
                    ),
                )

        connection.execute(
            """
            INSERT INTO order_status_history(
                order_id,
                old_status,
                new_status,
                changed_by_telegram_id,
                comment
            )
            VALUES (?, NULL, 'new', ?, 'Заказ создан через Mini App')
            """,
            (order_id, telegram_user.id),
        )

        connection.commit()

        return {
            "order_id": order_id,
            "order_number": order_number,
            "subtotal": subtotal,
            "delivery_price": delivery_price,
            "total": total,
            "status": "new",
        }


# ============================================================
# УПРАВЛЕНИЕ КАТАЛОГОМ
# ============================================================


def get_catalog_counts_sync() -> Dict[str, int]:
    """Возвращает количества сущностей каталога."""
    with get_db_connection() as connection:
        product_count = int(
            connection.execute(
                "SELECT COUNT(*) FROM products"
            ).fetchone()[0]
        )
        category_count = int(
            connection.execute(
                "SELECT COUNT(*) FROM categories"
            ).fetchone()[0]
        )
        addon_count = int(
            connection.execute(
                "SELECT COUNT(*) FROM addons"
            ).fetchone()[0]
        )
        featured_count = int(
            connection.execute(
                "SELECT COUNT(*) FROM featured_products"
            ).fetchone()[0]
        )
    return {
        "product_count": product_count,
        "category_count": category_count,
        "addon_count": addon_count,
        "featured_count": featured_count,
    }


def _normalize_featured_positions_sync(
    connection: sqlite3.Connection,
) -> None:
    rows = connection.execute(
        """
        SELECT product_id
        FROM featured_products
        ORDER BY position ASC, created_at ASC, product_id ASC
        """
    ).fetchall()
    for position, row in enumerate(rows):
        connection.execute(
            """
            UPDATE featured_products
            SET position = ?
            WHERE product_id = ?
            """,
            (position, int(row["product_id"])),
        )


def get_featured_products_admin_sync() -> List[sqlite3.Row]:
    with get_db_connection() as connection:
        return connection.execute(
            """
            SELECT
                products.id,
                products.name,
                products.is_active,
                featured_products.position
            FROM featured_products
            JOIN products ON products.id = featured_products.product_id
            ORDER BY featured_products.position ASC, products.id ASC
            """
        ).fetchall()


def get_featured_candidates_page_sync(
    page: int,
    page_size: int = 8,
) -> Dict[str, Any]:
    page = max(0, int(page))
    page_size = max(1, min(20, int(page_size)))
    with get_db_connection() as connection:
        total = int(
            connection.execute(
                """
                SELECT COUNT(*)
                FROM products
                JOIN categories ON categories.id = products.category_id
                WHERE products.is_active = 1
                  AND categories.slug = 'bouquets'
                  AND products.id NOT IN (
                      SELECT product_id FROM featured_products
                  )
                """
            ).fetchone()[0]
        )
        total_pages = max(1, (total + page_size - 1) // page_size)
        page = min(page, total_pages - 1)
        rows = connection.execute(
            """
            SELECT products.id, products.name, products.base_price
            FROM products
            JOIN categories ON categories.id = products.category_id
            WHERE products.is_active = 1
              AND categories.slug = 'bouquets'
              AND products.id NOT IN (
                  SELECT product_id FROM featured_products
              )
            ORDER BY products.id DESC
            LIMIT ? OFFSET ?
            """,
            (page_size, page * page_size),
        ).fetchall()
    return {
        "products": rows,
        "page": page,
        "total": total,
        "total_pages": total_pages,
    }


def add_featured_product_sync(product_id: int) -> None:
    with get_db_connection() as connection:
        product = connection.execute(
            """
            SELECT products.id, products.is_active, categories.slug AS category_slug
            FROM products
            LEFT JOIN categories ON categories.id = products.category_id
            WHERE products.id = ?
            """,
            (product_id,),
        ).fetchone()
        if product is None:
            raise ValueError("Товар не найден")
        if not bool(product["is_active"]):
            raise ValueError("Сначала опубликуйте товар")
        if str(product["category_slug"] or "") != "bouquets":
            raise ValueError("На главной можно показывать только букеты")
        if connection.execute(
            "SELECT 1 FROM featured_products WHERE product_id = ?",
            (product_id,),
        ).fetchone():
            return
        position = int(
            connection.execute(
                "SELECT COALESCE(MAX(position), -1) + 1 FROM featured_products"
            ).fetchone()[0]
        )
        connection.execute(
            """
            INSERT INTO featured_products(product_id, position)
            VALUES (?, ?)
            """,
            (product_id, position),
        )
        connection.commit()


def remove_featured_product_sync(product_id: int) -> None:
    with get_db_connection() as connection:
        connection.execute(
            "DELETE FROM featured_products WHERE product_id = ?",
            (product_id,),
        )
        _normalize_featured_positions_sync(connection)
        connection.commit()


def move_featured_product_sync(
    product_id: int,
    direction: str,
) -> None:
    with get_db_connection() as connection:
        rows = connection.execute(
            """
            SELECT product_id
            FROM featured_products
            ORDER BY position ASC, product_id ASC
            """
        ).fetchall()
        product_ids = [int(row["product_id"]) for row in rows]
        if product_id not in product_ids:
            raise ValueError("Букет не найден в популярных")
        index = product_ids.index(product_id)
        target = index - 1 if direction == "up" else index + 1
        if target < 0 or target >= len(product_ids):
            return
        product_ids[index], product_ids[target] = (
            product_ids[target],
            product_ids[index],
        )
        for position, current_id in enumerate(product_ids):
            connection.execute(
                "UPDATE featured_products SET position = ? WHERE product_id = ?",
                (position, current_id),
            )
        connection.commit()


def toggle_featured_product_sync(product_id: int) -> bool:
    with get_db_connection() as connection:
        exists = connection.execute(
            "SELECT 1 FROM featured_products WHERE product_id = ?",
            (product_id,),
        ).fetchone()
    if exists:
        remove_featured_product_sync(product_id)
        return False
    add_featured_product_sync(product_id)
    return True


def get_products_page_sync(
    page: int,
    page_size: int = 8,
) -> Dict[str, Any]:
    """Возвращает страницу товаров для админ-панели."""
    page = max(0, int(page))
    page_size = max(1, min(20, int(page_size)))

    with get_db_connection() as connection:
        total = int(
            connection.execute("SELECT COUNT(*) FROM products").fetchone()[0]
        )
        total_pages = max(1, (total + page_size - 1) // page_size)
        page = min(page, total_pages - 1)
        offset = page * page_size

        rows = connection.execute(
            """
            SELECT
                products.id,
                products.name,
                products.is_active,
                products.base_price,
                categories.name AS category_name,
                featured_products.position AS featured_position,
                MIN(product_variants.price) AS min_price,
                MAX(product_variants.price) AS max_price
            FROM products
            LEFT JOIN categories ON categories.id = products.category_id
            LEFT JOIN featured_products
                ON featured_products.product_id = products.id
            LEFT JOIN product_variants
                ON product_variants.product_id = products.id
            GROUP BY products.id
            ORDER BY products.id DESC
            LIMIT ? OFFSET ?
            """,
            (page_size, offset),
        ).fetchall()

    return {
        "products": rows,
        "page": page,
        "total": total,
        "total_pages": total_pages,
    }


def get_product_admin_sync(product_id: int) -> Optional[Dict[str, Any]]:
    """Возвращает полную карточку товара для администратора."""
    with get_db_connection() as connection:
        product = connection.execute(
            """
            SELECT
                products.*,
                categories.name AS category_name,
                featured_products.position AS featured_position
            FROM products
            LEFT JOIN categories ON categories.id = products.category_id
            LEFT JOIN featured_products
                ON featured_products.product_id = products.id
            WHERE products.id = ?
            """,
            (product_id,),
        ).fetchone()
        if product is None:
            return None

        variants = connection.execute(
            """
            SELECT id, name, price, is_default, is_active
            FROM product_variants
            WHERE product_id = ?
            ORDER BY CASE name WHEN 'S' THEN 1 WHEN 'M' THEN 2 WHEN 'L' THEN 3 ELSE 4 END
            """,
            (product_id,),
        ).fetchall()

        addons = connection.execute(
            """
            SELECT addons.id, addons.name, addons.price, addons.is_active
            FROM addons
            JOIN product_addons ON product_addons.addon_id = addons.id
            WHERE product_addons.product_id = ?
            ORDER BY addons.id
            """,
            (product_id,),
        ).fetchall()

        images = connection.execute(
            """
            SELECT id, image_url, position, is_primary
            FROM product_images
            WHERE product_id = ?
            ORDER BY is_primary DESC, position ASC, id ASC
            """,
            (product_id,),
        ).fetchall()

    return {
        "product": product,
        "variants": variants,
        "addons": addons,
        "images": images,
    }


def get_categories_admin_sync() -> List[sqlite3.Row]:
    """Возвращает категории с количеством товаров."""
    with get_db_connection() as connection:
        return connection.execute(
            """
            SELECT
                categories.id,
                categories.name,
                categories.slug,
                categories.position,
                categories.is_active,
                COUNT(products.id) AS product_count
            FROM categories
            LEFT JOIN products ON products.category_id = categories.id
            GROUP BY categories.id
            ORDER BY categories.position, categories.id
            """
        ).fetchall()


def get_category_admin_sync(category_id: int) -> Optional[sqlite3.Row]:
    with get_db_connection() as connection:
        return connection.execute(
            """
            SELECT
                categories.id,
                categories.name,
                categories.slug,
                categories.position,
                categories.is_active,
                COUNT(products.id) AS product_count
            FROM categories
            LEFT JOIN products ON products.category_id = categories.id
            WHERE categories.id = ?
            GROUP BY categories.id
            """,
            (category_id,),
        ).fetchone()


def get_addons_admin_sync() -> List[sqlite3.Row]:
    """Возвращает все дополнения."""
    with get_db_connection() as connection:
        return connection.execute(
            """
            SELECT id, name, price, image_url, is_active
            FROM addons
            ORDER BY id
            """
        ).fetchall()


def get_addon_admin_sync(addon_id: int) -> Optional[sqlite3.Row]:
    with get_db_connection() as connection:
        return connection.execute(
            """
            SELECT id, name, price, image_url, is_active
            FROM addons
            WHERE id = ?
            """,
            (addon_id,),
        ).fetchone()


def create_product_admin_sync(data: Dict[str, Any]) -> int:
    """Создаёт товар, варианты размеров и связи с дополнениями."""
    name = str(data["name"]).strip()
    description = str(data.get("description") or "").strip()
    composition = str(data.get("composition") or "").strip()
    category_id = int(data["category_id"])
    image_url = data.get("image_url")
    prices = data["prices"]
    addon_ids = sorted({int(value) for value in data.get("addon_ids", [])})

    if not name:
        raise ValueError("Название товара не может быть пустым")

    with get_db_connection() as connection:
        category = connection.execute(
            "SELECT id FROM categories WHERE id = ?",
            (category_id,),
        ).fetchone()
        if category is None:
            raise ValueError("Категория не найдена")

        slug = "product-{0}".format(uuid4().hex[:12])
        base_price = int(prices["S"])
        cursor = connection.execute(
            """
            INSERT INTO products(
                category_id,
                name,
                slug,
                description,
                composition,
                base_price,
                image_url,
                is_active
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, 1)
            """,
            (
                category_id,
                name,
                slug,
                description,
                composition,
                base_price,
                image_url,
            ),
        )
        product_id = int(cursor.lastrowid)

        if image_url:
            connection.execute(
                """
                INSERT INTO product_images(
                    product_id,
                    image_url,
                    position,
                    is_primary
                )
                VALUES (?, ?, 0, 1)
                """,
                (product_id, image_url),
            )

        for index, size in enumerate(("S", "M", "L")):
            connection.execute(
                """
                INSERT INTO product_variants(
                    product_id,
                    name,
                    price,
                    is_default,
                    is_active
                )
                VALUES (?, ?, ?, ?, 1)
                """,
                (
                    product_id,
                    size,
                    int(prices[size]),
                    1 if index == 0 else 0,
                ),
            )

        if addon_ids:
            valid_addons = connection.execute(
                "SELECT id FROM addons WHERE id IN ({0})".format(
                    ",".join("?" for _ in addon_ids)
                ),
                addon_ids,
            ).fetchall()
            for addon in valid_addons:
                connection.execute(
                    """
                    INSERT OR IGNORE INTO product_addons(product_id, addon_id)
                    VALUES (?, ?)
                    """,
                    (product_id, int(addon["id"])),
                )

        connection.commit()
        return product_id


def update_product_text_sync(
    product_id: int,
    field: str,
    value: Optional[str],
) -> None:
    allowed = {"name", "description", "composition", "image_url"}
    if field not in allowed:
        raise ValueError("Недопустимое поле товара")

    with get_db_connection() as connection:
        exists = connection.execute(
            "SELECT id, image_url FROM products WHERE id = ?",
            (product_id,),
        ).fetchone()
        if exists is None:
            raise ValueError("Товар не найден")

        if field != "image_url":
            connection.execute(
                "UPDATE products SET {0} = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?".format(field),
                (value, product_id),
            )
            connection.commit()
            return

        primary = connection.execute(
            """
            SELECT id, image_url
            FROM product_images
            WHERE product_id = ? AND is_primary = 1
            ORDER BY id
            LIMIT 1
            """,
            (product_id,),
        ).fetchone()

        if value:
            connection.execute(
                "UPDATE product_images SET is_primary = 0 WHERE product_id = ?",
                (product_id,),
            )
            existing_image = connection.execute(
                """
                SELECT id
                FROM product_images
                WHERE product_id = ? AND image_url = ?
                """,
                (product_id, value),
            ).fetchone()

            if existing_image:
                connection.execute(
                    """
                    UPDATE product_images
                    SET is_primary = 1, position = 0
                    WHERE id = ?
                    """,
                    (int(existing_image["id"]),),
                )
            elif primary:
                connection.execute(
                    """
                    UPDATE product_images
                    SET image_url = ?, is_primary = 1, position = 0
                    WHERE id = ?
                    """,
                    (value, int(primary["id"])),
                )
            else:
                connection.execute(
                    """
                    INSERT INTO product_images(
                        product_id, image_url, position, is_primary
                    )
                    VALUES (?, ?, 0, 1)
                    """,
                    (product_id, value),
                )

            connection.execute(
                """
                UPDATE products
                SET image_url = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (value, product_id),
            )
        else:
            if primary:
                connection.execute(
                    "DELETE FROM product_images WHERE id = ?",
                    (int(primary["id"]),),
                )

            next_image = connection.execute(
                """
                SELECT id, image_url
                FROM product_images
                WHERE product_id = ?
                ORDER BY position ASC, id ASC
                """,
                (product_id,),
            ).fetchone()

            if next_image:
                connection.execute(
                    """
                    UPDATE product_images
                    SET is_primary = 1, position = 0
                    WHERE id = ?
                    """,
                    (int(next_image["id"]),),
                )
                next_url: Optional[str] = str(next_image["image_url"])
            else:
                next_url = None

            connection.execute(
                """
                UPDATE products
                SET image_url = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (next_url, product_id),
            )

        connection.commit()


def add_product_image_sync(product_id: int, image_url: str) -> int:
    image_url = str(image_url or "").strip()
    if not image_url:
        raise ValueError("Фотография не получена")

    with get_db_connection() as connection:
        product = connection.execute(
            "SELECT id, image_url FROM products WHERE id = ?",
            (product_id,),
        ).fetchone()
        if product is None:
            raise ValueError("Товар не найден")

        count = int(
            connection.execute(
                "SELECT COUNT(*) FROM product_images WHERE product_id = ?",
                (product_id,),
            ).fetchone()[0]
        )
        if count >= MAX_PRODUCT_IMAGES:
            raise ValueError(
                "Для одного товара можно добавить не более {0} фотографий".format(
                    MAX_PRODUCT_IMAGES
                )
            )

        duplicate = connection.execute(
            """
            SELECT id
            FROM product_images
            WHERE product_id = ? AND image_url = ?
            """,
            (product_id, image_url),
        ).fetchone()
        if duplicate:
            raise ValueError("Эта фотография уже есть в галерее")

        position = int(
            connection.execute(
                """
                SELECT COALESCE(MAX(position), -1) + 1
                FROM product_images
                WHERE product_id = ?
                """,
                (product_id,),
            ).fetchone()[0]
        )
        is_primary = 1 if count == 0 else 0
        cursor = connection.execute(
            """
            INSERT INTO product_images(
                product_id, image_url, position, is_primary
            )
            VALUES (?, ?, ?, ?)
            """,
            (product_id, image_url, position, is_primary),
        )

        if is_primary or not product["image_url"]:
            connection.execute(
                """
                UPDATE products
                SET image_url = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (image_url, product_id),
            )

        connection.commit()
        return int(cursor.lastrowid)


def set_product_primary_image_sync(product_id: int, image_id: int) -> None:
    with get_db_connection() as connection:
        image = connection.execute(
            """
            SELECT id, image_url
            FROM product_images
            WHERE id = ? AND product_id = ?
            """,
            (image_id, product_id),
        ).fetchone()
        if image is None:
            raise ValueError("Фотография не найдена")

        connection.execute(
            "UPDATE product_images SET is_primary = 0 WHERE product_id = ?",
            (product_id,),
        )
        connection.execute(
            """
            UPDATE product_images
            SET is_primary = 1, position = 0
            WHERE id = ?
            """,
            (image_id,),
        )
        connection.execute(
            """
            UPDATE products
            SET image_url = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (str(image["image_url"]), product_id),
        )
        connection.commit()


def delete_product_image_sync(product_id: int, image_id: int) -> None:
    with get_db_connection() as connection:
        image = connection.execute(
            """
            SELECT id, image_url, is_primary
            FROM product_images
            WHERE id = ? AND product_id = ?
            """,
            (image_id, product_id),
        ).fetchone()
        if image is None:
            raise ValueError("Фотография не найдена")

        connection.execute(
            "DELETE FROM product_images WHERE id = ?",
            (image_id,),
        )

        if bool(image["is_primary"]):
            next_image = connection.execute(
                """
                SELECT id, image_url
                FROM product_images
                WHERE product_id = ?
                ORDER BY position ASC, id ASC
                """,
                (product_id,),
            ).fetchone()
            if next_image:
                connection.execute(
                    """
                    UPDATE product_images
                    SET is_primary = 1, position = 0
                    WHERE id = ?
                    """,
                    (int(next_image["id"]),),
                )
                next_url: Optional[str] = str(next_image["image_url"])
            else:
                next_url = None

            connection.execute(
                """
                UPDATE products
                SET image_url = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (next_url, product_id),
            )

        connection.commit()


def update_product_prices_sync(
    product_id: int,
    prices: Dict[str, int],
) -> None:
    """Обновляет цены S/M/L и базовую цену."""
    for size in ("S", "M", "L"):
        if int(prices[size]) < 0:
            raise ValueError("Цена не может быть отрицательной")

    with get_db_connection() as connection:
        exists = connection.execute(
            "SELECT id FROM products WHERE id = ?",
            (product_id,),
        ).fetchone()
        if exists is None:
            raise ValueError("Товар не найден")

        for index, size in enumerate(("S", "M", "L")):
            connection.execute(
                """
                INSERT INTO product_variants(
                    product_id, name, price, is_default, is_active
                )
                VALUES (?, ?, ?, ?, 1)
                ON CONFLICT(product_id, name) DO UPDATE SET
                    price = excluded.price,
                    is_active = 1,
                    is_default = excluded.is_default
                """,
                (product_id, size, int(prices[size]), 1 if index == 0 else 0),
            )

        connection.execute(
            """
            UPDATE products
            SET base_price = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (int(prices["S"]), product_id),
        )
        connection.commit()


def set_product_category_sync(product_id: int, category_id: int) -> None:
    with get_db_connection() as connection:
        category = connection.execute(
            "SELECT id FROM categories WHERE id = ?",
            (category_id,),
        ).fetchone()
        if category is None:
            raise ValueError("Категория не найдена")
        cursor = connection.execute(
            """
            UPDATE products
            SET category_id = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (category_id, product_id),
        )
        if cursor.rowcount == 0:
            raise ValueError("Товар не найден")
        connection.commit()


def set_product_addons_sync(
    product_id: int,
    addon_ids: List[int],
) -> None:
    addon_ids = sorted({int(value) for value in addon_ids})
    with get_db_connection() as connection:
        product = connection.execute(
            "SELECT id FROM products WHERE id = ?",
            (product_id,),
        ).fetchone()
        if product is None:
            raise ValueError("Товар не найден")

        connection.execute(
            "DELETE FROM product_addons WHERE product_id = ?",
            (product_id,),
        )
        if addon_ids:
            valid_ids = {
                int(row["id"])
                for row in connection.execute(
                    "SELECT id FROM addons WHERE id IN ({0})".format(
                        ",".join("?" for _ in addon_ids)
                    ),
                    addon_ids,
                ).fetchall()
            }
            for addon_id in addon_ids:
                if addon_id in valid_ids:
                    connection.execute(
                        "INSERT INTO product_addons(product_id, addon_id) VALUES (?, ?)",
                        (product_id, addon_id),
                    )
        connection.commit()


def toggle_product_active_sync(product_id: int) -> bool:
    with get_db_connection() as connection:
        row = connection.execute(
            "SELECT is_active FROM products WHERE id = ?",
            (product_id,),
        ).fetchone()
        if row is None:
            raise ValueError("Товар не найден")
        new_value = 0 if int(row["is_active"]) else 1
        connection.execute(
            """
            UPDATE products
            SET is_active = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (new_value, product_id),
        )
        if not new_value:
            connection.execute(
                "DELETE FROM featured_products WHERE product_id = ?",
                (product_id,),
            )
            _normalize_featured_positions_sync(connection)
        connection.commit()
        return bool(new_value)


def delete_product_sync(product_id: int) -> None:
    """Удаляет товар; снимки в старых заказах сохраняются."""
    with get_db_connection() as connection:
        cursor = connection.execute(
            "DELETE FROM products WHERE id = ?",
            (product_id,),
        )
        if cursor.rowcount == 0:
            raise ValueError("Товар не найден")
        connection.commit()


def create_category_sync(name: str) -> int:
    raise ValueError(
        "Типы товаров фиксированы: Букеты, Открытки и Мягкие игрушки"
    )


def rename_category_sync(category_id: int, name: str) -> None:
    raise ValueError("Названия типов товаров зафиксированы")


def toggle_category_sync(category_id: int) -> bool:
    raise ValueError("Типы товаров нельзя скрывать")


def move_category_sync(category_id: int, direction: str) -> None:
    raise ValueError("Порядок типов товаров зафиксирован")


def create_addon_sync(name: str, price: int) -> int:
    name = name.strip()
    price = int(price)
    if not name:
        raise ValueError("Название дополнения не может быть пустым")
    if price < 0:
        raise ValueError("Цена не может быть отрицательной")
    with get_db_connection() as connection:
        try:
            cursor = connection.execute(
                "INSERT INTO addons(name, price, is_active) VALUES (?, ?, 1)",
                (name, price),
            )
        except sqlite3.IntegrityError as error:
            raise ValueError("Дополнение с таким названием уже существует") from error
        addon_id = int(cursor.lastrowid)
        connection.execute(
            """
            INSERT OR IGNORE INTO product_addons(product_id, addon_id)
            SELECT id, ? FROM products
            """,
            (addon_id,),
        )
        connection.commit()
        return addon_id


def update_addon_name_sync(addon_id: int, name: str) -> None:
    name = name.strip()
    if not name:
        raise ValueError("Название дополнения не может быть пустым")
    with get_db_connection() as connection:
        try:
            cursor = connection.execute(
                "UPDATE addons SET name = ? WHERE id = ?",
                (name, addon_id),
            )
        except sqlite3.IntegrityError as error:
            raise ValueError("Дополнение с таким названием уже существует") from error
        if cursor.rowcount == 0:
            raise ValueError("Дополнение не найдено")
        connection.commit()


def update_addon_price_sync(addon_id: int, price: int) -> None:
    price = int(price)
    if price < 0:
        raise ValueError("Цена не может быть отрицательной")
    with get_db_connection() as connection:
        cursor = connection.execute(
            "UPDATE addons SET price = ? WHERE id = ?",
            (price, addon_id),
        )
        if cursor.rowcount == 0:
            raise ValueError("Дополнение не найдено")
        connection.commit()


def toggle_addon_sync(addon_id: int) -> bool:
    with get_db_connection() as connection:
        row = connection.execute(
            "SELECT is_active FROM addons WHERE id = ?",
            (addon_id,),
        ).fetchone()
        if row is None:
            raise ValueError("Дополнение не найдено")
        new_value = 0 if int(row["is_active"]) else 1
        connection.execute(
            "UPDATE addons SET is_active = ? WHERE id = ?",
            (new_value, addon_id),
        )
        connection.commit()
        return bool(new_value)


async def initialize_database() -> None:
    await asyncio.to_thread(initialize_database_sync)


async def upsert_user(user: User) -> None:
    await asyncio.to_thread(upsert_user_sync, user)


async def get_user_orders(
    telegram_id: int,
    limit: int = 10,
) -> List[sqlite3.Row]:
    return await asyncio.to_thread(
        get_user_orders_sync,
        telegram_id,
        limit,
    )


async def get_orders(
    status: Optional[str] = None,
    limit: int = 10,
) -> List[sqlite3.Row]:
    return await asyncio.to_thread(
        get_orders_sync,
        status,
        limit,
    )


async def get_order_counts() -> Dict[str, int]:
    return await asyncio.to_thread(get_order_counts_sync)


async def get_orders_page(
    filter_key: str,
    page: int,
    page_size: int = 5,
) -> Dict[str, Any]:
    return await asyncio.to_thread(
        get_orders_page_sync,
        filter_key,
        page,
        page_size,
    )


async def get_order_details(
    order_id: int,
) -> Optional[Dict[str, Any]]:
    return await asyncio.to_thread(get_order_details_sync, order_id)


async def get_adjacent_order_ids(
    order_id: int,
    filter_key: str,
) -> Tuple[Optional[int], Optional[int]]:
    return await asyncio.to_thread(
        get_adjacent_order_ids_sync,
        order_id,
        filter_key,
    )


async def update_order_status(
    order_id: int,
    new_status: str,
    admin_telegram_id: int,
) -> Dict[str, Any]:
    return await asyncio.to_thread(
        update_order_status_sync,
        order_id,
        new_status,
        admin_telegram_id,
    )


async def create_demo_order(telegram_user: User) -> Dict[str, Any]:
    return await asyncio.to_thread(create_demo_order_sync, telegram_user)


async def get_admin_stats() -> Dict[str, int]:
    return await asyncio.to_thread(get_admin_stats_sync)




async def get_catalog_counts() -> Dict[str, int]:
    return await asyncio.to_thread(get_catalog_counts_sync)


async def get_featured_products_admin() -> List[sqlite3.Row]:
    return await asyncio.to_thread(get_featured_products_admin_sync)


async def get_featured_candidates_page(
    page: int,
    page_size: int = 8,
) -> Dict[str, Any]:
    return await asyncio.to_thread(
        get_featured_candidates_page_sync,
        page,
        page_size,
    )


async def add_featured_product(product_id: int) -> None:
    await asyncio.to_thread(add_featured_product_sync, product_id)


async def remove_featured_product(product_id: int) -> None:
    await asyncio.to_thread(remove_featured_product_sync, product_id)


async def move_featured_product(
    product_id: int,
    direction: str,
) -> None:
    await asyncio.to_thread(
        move_featured_product_sync,
        product_id,
        direction,
    )


async def toggle_featured_product(product_id: int) -> bool:
    return await asyncio.to_thread(
        toggle_featured_product_sync,
        product_id,
    )


async def get_products_page(
    page: int,
    page_size: int = 8,
) -> Dict[str, Any]:
    return await asyncio.to_thread(get_products_page_sync, page, page_size)


async def get_product_admin(product_id: int) -> Optional[Dict[str, Any]]:
    return await asyncio.to_thread(get_product_admin_sync, product_id)


async def get_categories_admin() -> List[sqlite3.Row]:
    return await asyncio.to_thread(get_categories_admin_sync)


async def get_category_admin(category_id: int) -> Optional[sqlite3.Row]:
    return await asyncio.to_thread(get_category_admin_sync, category_id)


async def get_addons_admin() -> List[sqlite3.Row]:
    return await asyncio.to_thread(get_addons_admin_sync)


async def get_addon_admin(addon_id: int) -> Optional[sqlite3.Row]:
    return await asyncio.to_thread(get_addon_admin_sync, addon_id)


async def create_product_admin(data: Dict[str, Any]) -> int:
    return await asyncio.to_thread(create_product_admin_sync, data)


async def update_product_text(
    product_id: int,
    field: str,
    value: Optional[str],
) -> None:
    await asyncio.to_thread(update_product_text_sync, product_id, field, value)


async def add_product_image(product_id: int, image_url: str) -> int:
    return await asyncio.to_thread(
        add_product_image_sync,
        product_id,
        image_url,
    )


async def set_product_primary_image(
    product_id: int,
    image_id: int,
) -> None:
    await asyncio.to_thread(
        set_product_primary_image_sync,
        product_id,
        image_id,
    )


async def delete_product_image(
    product_id: int,
    image_id: int,
) -> None:
    await asyncio.to_thread(
        delete_product_image_sync,
        product_id,
        image_id,
    )


async def update_product_prices(
    product_id: int,
    prices: Dict[str, int],
) -> None:
    await asyncio.to_thread(update_product_prices_sync, product_id, prices)


async def set_product_category(product_id: int, category_id: int) -> None:
    await asyncio.to_thread(set_product_category_sync, product_id, category_id)


async def set_product_addons(product_id: int, addon_ids: List[int]) -> None:
    await asyncio.to_thread(set_product_addons_sync, product_id, addon_ids)


async def toggle_product_active(product_id: int) -> bool:
    return await asyncio.to_thread(toggle_product_active_sync, product_id)


async def delete_product(product_id: int) -> None:
    await asyncio.to_thread(delete_product_sync, product_id)


async def create_category(name: str) -> int:
    return await asyncio.to_thread(create_category_sync, name)


async def rename_category(category_id: int, name: str) -> None:
    await asyncio.to_thread(rename_category_sync, category_id, name)


async def toggle_category(category_id: int) -> bool:
    return await asyncio.to_thread(toggle_category_sync, category_id)


async def move_category(category_id: int, direction: str) -> None:
    await asyncio.to_thread(move_category_sync, category_id, direction)


async def create_addon(name: str, price: int) -> int:
    return await asyncio.to_thread(create_addon_sync, name, price)


async def update_addon_name(addon_id: int, name: str) -> None:
    await asyncio.to_thread(update_addon_name_sync, addon_id, name)


async def update_addon_price(addon_id: int, price: int) -> None:
    await asyncio.to_thread(update_addon_price_sync, addon_id, price)


async def toggle_addon(addon_id: int) -> bool:
    return await asyncio.to_thread(toggle_addon_sync, addon_id)


async def create_order(
    telegram_user: User,
    data: Dict[str, Any],
) -> Dict[str, Any]:
    return await asyncio.to_thread(
        create_order_sync,
        telegram_user,
        data,
    )




class ProductCreateStates(StatesGroup):
    name = State()
    description = State()
    composition = State()
    image = State()
    price_s = State()
    price_m = State()
    price_l = State()
    category = State()
    addons = State()
    confirm = State()


class CatalogEditStates(StatesGroup):
    waiting_value = State()


class ProductGalleryStates(StatesGroup):
    add_image = State()


class CategoryStates(StatesGroup):
    add_name = State()
    rename = State()


class AddonStates(StatesGroup):
    add_name = State()
    add_price = State()
    edit_name = State()
    edit_price = State()


def parse_price_text(text: str) -> int:
    """Преобразует '2 490 ₽' в 2490."""
    cleaned = (
        text.replace("₽", "")
        .replace("руб.", "")
        .replace("руб", "")
        .replace(" ", "")
        .replace("_", "")
        .strip()
    )
    if not cleaned.isdigit():
        raise ValueError("Введите цену целым числом, например 2490")
    value = int(cleaned)
    if value < 0 or value > 10_000_000:
        raise ValueError("Цена должна быть от 0 до 10 000 000 ₽")
    return value


def parse_three_prices(text: str) -> Dict[str, int]:
    """Читает три цены из одной строки: S M L."""
    normalized = text.replace(",", " ").replace(";", " ").replace("/", " ")
    parts = [part for part in normalized.split() if part]
    if len(parts) != 3:
        raise ValueError("Введите три цены через пробел: 2490 3490 4990")
    values = [parse_price_text(part) for part in parts]
    return {"S": values[0], "M": values[1], "L": values[2]}


def normalize_optional_text(text: str) -> str:
    value = text.strip()
    if value.lower() in {"-", "нет", "пропустить", "/skip"}:
        return ""
    return value


def extract_image_value(message: Message) -> Optional[str]:
    """Возвращает URL или Telegram file_id с префиксом."""
    if message.photo:
        return "telegram:{0}".format(message.photo[-1].file_id)

    text = (message.text or "").strip()
    if text.lower() in {"-", "нет", "пропустить", "/skip"}:
        return None
    if text.startswith("https://") or text.startswith("http://"):
        return text
    raise ValueError("Пришлите фотографию, ссылку http(s) или слово «пропустить»")


def product_image_source(image_value: Optional[str]) -> Optional[str]:
    if not image_value:
        return None
    if image_value.startswith("telegram:"):
        return image_value.split(":", 1)[1]
    return image_value


def product_image_for_telegram(image_value: str) -> Any:
    value = str(image_value)
    if value.startswith("telegram:"):
        return value.split(":", 1)[1]
    if value.startswith("http://") or value.startswith("https://"):
        return value

    candidate = (WEBAPP_DIR / value).resolve()
    webapp_root = WEBAPP_DIR.resolve()
    try:
        candidate.relative_to(webapp_root)
    except ValueError as error:
        raise ValueError("Недопустимый путь к фотографии") from error

    if not candidate.is_file():
        raise ValueError("Локальный файл фотографии не найден")
    return FSInputFile(candidate)


def format_product_gallery_admin(details: Dict[str, Any]) -> str:
    product = details["product"]
    images = details.get("images", [])
    lines = []
    for index, image in enumerate(images, start=1):
        marker = "⭐ главное" if bool(image["is_primary"]) else "дополнительное"
        lines.append(
            "{0}. <b>Фото {0}</b> — {1}".format(index, marker)
        )

    return (
        "<b>Галерея: {0}</b>\n\n"
        "Добавлено: <b>{1}/{2}</b>\n"
        "{3}\n\n"
        "Главное фото используется в каталоге. "
        "Остальные пользователь листает внутри карточки."
    ).format(
        html.escape(str(product["name"])),
        len(images),
        MAX_PRODUCT_IMAGES,
        "\n".join(lines) or "Фотографий пока нет.",
    )


def format_product_admin_card(details: Dict[str, Any]) -> str:
    product = details["product"]
    variants = details["variants"]
    addons = details["addons"]
    images = details.get("images", [])

    variant_lines = []
    for variant in variants:
        status = "" if int(variant["is_active"]) else " (скрыт)"
        variant_lines.append(
            "• {0}: <b>{1}</b>{2}".format(
                html.escape(str(variant["name"])),
                format_money(int(variant["price"])),
                status,
            )
        )

    addon_text = ", ".join(
        html.escape(str(addon["name"])) for addon in addons
    ) or "не выбраны"

    image_value = product["image_url"]
    if image_value:
        image_text = "загружено в Telegram" if str(image_value).startswith("telegram:") else html.escape(str(image_value))
    else:
        image_text = "не добавлено"

    return (
        "<b>{0}</b>\n\n"
        "Статус: <b>{1}</b>\n"
        "На главной: <b>{2}</b>\n"
        "Тип товара: <b>{3}</b>\n"
        "Состав: {4}\n"
        "Описание: {5}\n"
        "Главное фото: {6}\n"
        "Галерея: <b>{7} фото</b>\n\n"
        "<b>Размеры и цены</b>\n{8}\n\n"
        "<b>Дополнения</b>\n{9}\n\n"
        "ID товара: <code>{10}</code>"
    ).format(
        html.escape(str(product["name"])),
        "опубликован" if int(product["is_active"]) else "скрыт",
        (
            "⭐ популярный, позиция {0}".format(
                int(product["featured_position"]) + 1
            )
            if product["featured_position"] is not None
            else "не выбран"
        ),
        html.escape(str(product["category_name"] or "Без категории")),
        html.escape(str(product["composition"] or "—")),
        html.escape(str(product["description"] or "—")),
        image_text,
        len(images),
        "\n".join(variant_lines) or "Варианты не созданы",
        addon_text,
        int(product["id"]),
    )


def format_product_draft(data: Dict[str, Any]) -> str:
    prices = data.get("prices", {})
    addon_names = data.get("addon_names", [])
    return (
        "<b>Проверьте новый товар</b>\n\n"
        "Название: <b>{0}</b>\n"
        "Состав: {1}\n"
        "Описание: {2}\n"
        "Тип товара: <b>{3}</b>\n"
        "Фото: {4}\n\n"
        "S — <b>{5}</b>\n"
        "M — <b>{6}</b>\n"
        "L — <b>{7}</b>\n\n"
        "Дополнения: {8}"
    ).format(
        html.escape(str(data.get("name", ""))),
        html.escape(str(data.get("composition") or "—")),
        html.escape(str(data.get("description") or "—")),
        html.escape(str(data.get("category_name", "—"))),
        "добавлено" if data.get("image_url") else "нет",
        format_money(int(prices.get("S", 0))),
        format_money(int(prices.get("M", 0))),
        format_money(int(prices.get("L", 0))),
        ", ".join(html.escape(str(name)) for name in addon_names) or "не выбраны",
    )


async def ensure_admin_message(message: Message) -> bool:
    if user_is_admin(message.from_user.id):
        return True
    await message.answer("У вас нет доступа к этому действию.")
    return False


# ============================================================
# ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ БОТА
# ============================================================


def user_is_admin(user_id: int) -> bool:
    """Проверяет, является ли пользователь администратором."""
    return user_id in ADMIN_IDS


def format_money(value: int) -> str:
    """Форматирует целое количество рублей."""
    return "{0:,} ₽".format(value).replace(",", " ")


def format_orders(rows: List[sqlite3.Row], title: str) -> str:
    """Формирует компактный список заказов."""
    if not rows:
        return "<b>{0}</b>\n\nЗаказов пока нет.".format(title)

    lines = ["<b>{0}</b>".format(title), ""]

    for row in rows:
        status = ORDER_STATUS_LABELS.get(row["status"], row["status"])
        order_number = html.escape(str(row["order_number"] or "Без номера"))
        lines.append(
            "<b>{0}</b> · {1}\n"
            "Статус: {2}".format(
                order_number,
                format_money(int(row["total"])),
                html.escape(status),
            )
        )

        if "customer_name" in row.keys():
            lines.append(
                "Клиент: {0}".format(
                    html.escape(str(row["customer_name"]))
                )
            )

        if row["delivery_date"]:
            delivery_text = str(row["delivery_date"])
            if row["delivery_interval"]:
                delivery_text += " · " + str(row["delivery_interval"])
            lines.append("Доставка: {0}".format(html.escape(delivery_text)))

        lines.append("")

    return "\n".join(lines).strip()


def safe_text(value: Any, default: str = "—") -> str:
    """Экранирует значение для HTML-разметки Telegram."""
    if value is None:
        return default

    text = str(value).strip()
    if not text:
        return default
    return html.escape(text)


def format_admin_orders_page(page_data: Dict[str, Any]) -> str:
    """Формирует текст страницы заказов администратора."""
    filter_key = str(page_data["filter_key"])
    title = ORDER_FILTER_TITLES.get(filter_key, ORDER_FILTER_TITLES["all"])
    rows = page_data["rows"]

    if not rows:
        return "<b>{0}</b>\n\nЗаказов в этом разделе пока нет.".format(
            title
        )

    lines = [
        "<b>{0}</b>".format(title),
        "Показано: <b>{0}</b> из <b>{1}</b>".format(
            len(rows),
            page_data["total"],
        ),
        "",
    ]

    for row in rows:
        status = str(row["status"])
        emoji = ORDER_STATUS_EMOJIS.get(status, "•")
        label = ORDER_STATUS_LABELS.get(status, status)
        lines.append(
            "{0} <b>{1}</b> · {2}\n"
            "{3} · {4}".format(
                emoji,
                safe_text(row["order_number"], "Без номера"),
                format_money(int(row["total"] or 0)),
                safe_text(row["customer_name"], "Клиент"),
                safe_text(label),
            )
        )

        if row["delivery_date"]:
            delivery = str(row["delivery_date"])
            if row["delivery_interval"]:
                delivery += " · " + str(row["delivery_interval"])
            lines.append("Доставка: {0}".format(safe_text(delivery)))

        lines.append("")

    return "\n".join(lines).strip()


def format_order_card(details: Dict[str, Any]) -> str:
    """Формирует подробную карточку одного заказа."""
    order = details["order"]
    items = details["items"]
    history = details["history"]

    status = str(order["status"])
    status_label = ORDER_STATUS_LABELS.get(status, status)
    status_emoji = ORDER_STATUS_EMOJIS.get(status, "•")

    lines = [
        "<b>Заказ {0}</b>".format(
            safe_text(order["order_number"], "Без номера")
        ),
        "{0} Статус: <b>{1}</b>".format(
            status_emoji,
            safe_text(status_label),
        ),
        "",
        "<b>Клиент</b>",
        "Имя: {0}".format(safe_text(order["customer_name"])),
        "Телефон: {0}".format(safe_text(order["customer_phone"])),
        "Telegram ID: <code>{0}</code>".format(
            int(order["telegram_id"])
        ),
    ]

    username = order.get("username")
    if username:
        lines.append("Username: @{0}".format(safe_text(username)))

    lines.extend(
        [
            "",
            "<b>Получатель</b>",
            "Имя: {0}".format(safe_text(order["recipient_name"])),
            "Телефон: {0}".format(safe_text(order["recipient_phone"])),
            "",
            "<b>Состав заказа</b>",
        ]
    )

    for index, item in enumerate(items, start=1):
        variant = ""
        if item.get("variant_name"):
            variant = " · размер {0}".format(
                safe_text(item["variant_name"])
            )

        lines.append(
            "{0}. <b>{1}</b>{2}\n"
            "   {3} × {4} = {5}".format(
                index,
                safe_text(item["product_name"]),
                variant,
                format_money(int(item["unit_price"])),
                int(item["quantity"]),
                format_money(int(item["line_total"])),
            )
        )

        for addon in item.get("addons", []):
            lines.append(
                "   + {0} × {1} — {2}".format(
                    safe_text(addon["addon_name"]),
                    int(addon["quantity"]),
                    format_money(int(addon["line_total"])),
                )
            )

    lines.extend(
        [
            "",
            "<b>Доставка</b>",
            "Тип: {0}".format(
                "Доставка"
                if order["delivery_type"] == "delivery"
                else "Самовывоз"
            ),
            "Дата: {0}".format(safe_text(order["delivery_date"])),
            "Интервал: {0}".format(
                safe_text(order["delivery_interval"])
            ),
            "Адрес: {0}".format(safe_text(order["address"])),
        ]
    )

    if order["postcard_text"]:
        lines.append(
            "Открытка: {0}".format(safe_text(order["postcard_text"]))
        )

    if order["comment"]:
        lines.append(
            "Комментарий: {0}".format(safe_text(order["comment"]))
        )

    lines.extend(
        [
            "",
            "<b>Сумма</b>",
            "Товары: {0}".format(
                format_money(int(order["subtotal"] or 0))
            ),
            "Доставка: {0}".format(
                format_money(int(order["delivery_price"] or 0))
            ),
            "Итого: <b>{0}</b>".format(
                format_money(int(order["total"] or 0))
            ),
        ]
    )

    if history:
        last_change = history[0]
        lines.extend(
            [
                "",
                "Последнее изменение: {0}".format(
                    safe_text(last_change["created_at"])
                ),
            ]
        )

    return "\n".join(lines)


def parse_int(value: str, default: int = 0) -> int:
    """Безопасно преобразует часть callback_data в число."""
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


async def edit_or_send(
    callback: CallbackQuery,
    text: str,
    reply_markup=None,
) -> None:
    """Редактирует текущее сообщение или отправляет новое."""
    if isinstance(callback.message, Message):
        try:
            await callback.message.edit_text(
                text=text,
                reply_markup=reply_markup,
            )
            return
        except TelegramBadRequest as error:
            if "message is not modified" in str(error).lower():
                return
            logging.warning("Не удалось отредактировать сообщение: %s", error)
        except Exception:
            logging.exception("Не удалось отредактировать сообщение")

    await callback.bot.send_message(
        chat_id=callback.from_user.id,
        text=text,
        reply_markup=reply_markup,
    )


async def get_admin_menu_markup():
    """Возвращает админ-меню с актуальным числом новых заказов."""
    counts = await get_order_counts()
    return admin_menu_keyboard(new_count=counts["new"])


async def show_admin_filters(callback: CallbackQuery) -> None:
    """Показывает фильтры заказов."""
    counts = await get_order_counts()
    await edit_or_send(
        callback=callback,
        text=(
            "<b>Все заказы 📋</b>\n\n"
            "Выберите статус, по которому нужно отфильтровать заказы."
        ),
        reply_markup=admin_order_filters_keyboard(counts),
    )


async def show_admin_orders(
    callback: CallbackQuery,
    filter_key: str,
    page: int,
) -> None:
    """Показывает страницу заказов с кнопками карточек."""
    page_data = await get_orders_page(filter_key, page)
    await edit_or_send(
        callback=callback,
        text=format_admin_orders_page(page_data),
        reply_markup=admin_orders_list_keyboard(
            orders=page_data["rows"],
            filter_key=page_data["filter_key"],
            page=page_data["page"],
            total_pages=page_data["total_pages"],
        ),
    )


async def show_admin_order_card(
    callback: CallbackQuery,
    order_id: int,
    filter_key: str,
    page: int,
) -> None:
    """Показывает подробную карточку заказа."""
    details = await get_order_details(order_id)
    if details is None:
        await show_admin_orders(callback, filter_key, page)
        return

    previous_id, next_id = await get_adjacent_order_ids(
        order_id,
        filter_key,
    )
    order = details["order"]

    await edit_or_send(
        callback=callback,
        text=format_order_card(details),
        reply_markup=admin_order_card_keyboard(
            order_id=order_id,
            current_status=str(order["status"]),
            filter_key=normalize_filter_key(filter_key),
            page=max(page, 0),
            telegram_id=int(order["telegram_id"]),
            previous_order_id=previous_id,
            next_order_id=next_id,
        ),
    )


async def notify_customer_status(
    bot: Bot,
    status_result: Dict[str, Any],
) -> None:
    """Уведомляет клиента об изменении статуса заказа."""
    template = STATUS_NOTIFICATION_TEXTS.get(
        str(status_result["new_status"])
    )
    if not template:
        return

    text = template.format(
        order_number=safe_text(status_result["order_number"])
    )

    try:
        await bot.send_message(
            chat_id=int(status_result["telegram_id"]),
            text=text,
            reply_markup=main_menu_keyboard(
                is_admin=user_is_admin(int(status_result["telegram_id"]))
            ),
        )
    except Exception:
        logging.exception(
            "Не удалось уведомить клиента %s о заказе %s",
            status_result["telegram_id"],
            status_result["order_number"],
        )


# ============================================================
# ОБРАБОТЧИКИ ПОЛЬЗОВАТЕЛЯ
# ============================================================


@router.message(CommandStart())
async def start_handler(message: Message) -> None:
    """Главное приветствие бота и регистрация пользователя."""
    await upsert_user(message.from_user)

    first_name = html.escape(message.from_user.first_name or "друг")

    text = (
        f"<b>Привет, {first_name}! 🌷</b>\n\n"
        "Это <b>BloomBox</b> — магазин букетов внутри Telegram.\n\n"
        "В приложении можно выбрать букет, добавить открытку, "
        "оформить доставку и следить за статусом заказа."
    )

    await message.answer(
        text=text,
        reply_markup=main_menu_keyboard(
            is_admin=user_is_admin(message.from_user.id)
        ),
    )


@router.message(Command("help"))
async def help_handler(message: Message) -> None:
    """Краткая справка."""
    await upsert_user(message.from_user)

    text = (
        "<b>Как пользоваться BloomBox</b>\n\n"
        "1. Нажмите «Открыть магазин».\n"
        "2. Выберите букет и дополнения.\n"
        "3. Укажите данные доставки.\n"
        "4. Подтвердите заказ.\n\n"
        "Статус заказа будет приходить сообщениями в этот чат."
    )

    await message.answer(
        text=text,
        reply_markup=back_to_main_keyboard(
            is_admin=user_is_admin(message.from_user.id)
        ),
    )


@router.message(Command("admin"))
async def admin_command_handler(message: Message) -> None:
    """Открывает админ-меню только владельцу."""
    if not user_is_admin(message.from_user.id):
        await message.answer("У вас нет доступа к админ-панели.")
        return

    await message.answer(
        text=(
            "<b>Админ-панель BloomBox</b>\n\n"
            "База данных подключена. Здесь отображаются реальные "
            "заказы, товары и статистика."
        ),
        reply_markup=await get_admin_menu_markup(),
    )


@router.message(Command("demo_order"))
async def demo_order_handler(message: Message) -> None:
    """Создаёт тестовый заказ, чтобы проверить весь админский цикл."""
    if not user_is_admin(message.from_user.id):
        await message.answer("У вас нет доступа к этой команде.")
        return

    try:
        order = await create_demo_order(message.from_user)
    except Exception:
        logging.exception("Не удалось создать демонстрационный заказ")
        await message.answer("Не удалось создать тестовый заказ.")
        return

    await message.answer(
        text=(
            "<b>Тестовый заказ создан ✅</b>\n\n"
            "Номер: <b>{0}</b>\n"
            "Сумма: <b>{1}</b>\n\n"
            "Откройте админ-панель и проверьте смену статусов."
        ).format(
            safe_text(order["order_number"]),
            format_money(int(order["total"])),
        ),
        reply_markup=await get_admin_menu_markup(),
    )


@router.callback_query(F.data == "menu:main")
async def main_menu_callback(callback: CallbackQuery) -> None:
    await callback.answer()
    await upsert_user(callback.from_user)

    await edit_or_send(
        callback=callback,
        text="<b>BloomBox 🌷</b>\n\nВыберите нужный раздел.",
        reply_markup=main_menu_keyboard(
            is_admin=user_is_admin(callback.from_user.id)
        ),
    )


@router.callback_query(F.data == "menu:orders")
async def orders_callback(callback: CallbackQuery) -> None:
    await callback.answer()
    await upsert_user(callback.from_user)

    rows = await get_user_orders(callback.from_user.id)
    text = format_orders(rows, "Мои заказы 📦")

    await edit_or_send(
        callback=callback,
        text=text,
        reply_markup=back_to_main_keyboard(
            is_admin=user_is_admin(callback.from_user.id)
        ),
    )


@router.callback_query(F.data == "menu:delivery")
async def delivery_callback(callback: CallbackQuery) -> None:
    await callback.answer()

    text = (
        "<b>Доставка и оплата 🚚</b>\n\n"
        "• Стандартная доставка — 390 ₽.\n"
        "• При заказе от 5 000 ₽ доставка бесплатная.\n"
        "• Доступные интервалы выбираются при оформлении.\n"
        "• Онлайн-оплату добавим отдельным этапом."
    )

    await edit_or_send(
        callback=callback,
        text=text,
        reply_markup=back_to_main_keyboard(
            is_admin=user_is_admin(callback.from_user.id)
        ),
    )


# ============================================================
# ОБРАБОТЧИКИ АДМИНИСТРАТОРА
# ============================================================


async def check_admin_callback(callback: CallbackQuery) -> bool:
    if user_is_admin(callback.from_user.id):
        return True

    await callback.answer(text="У вас нет доступа.", show_alert=True)
    return False


@router.callback_query(F.data == "menu:admin")
async def admin_menu_callback(callback: CallbackQuery) -> None:
    if not await check_admin_callback(callback):
        return

    await callback.answer()

    await edit_or_send(
        callback=callback,
        text=(
            "<b>Админ-панель BloomBox</b>\n\n"
            "Выберите раздел управления."
        ),
        reply_markup=await get_admin_menu_markup(),
    )


@router.callback_query(F.data == "admin:filters")
async def admin_filters_callback(callback: CallbackQuery) -> None:
    if not await check_admin_callback(callback):
        return

    await callback.answer()
    await show_admin_filters(callback)


@router.callback_query(F.data.startswith("admin:list:"))
async def admin_orders_list_callback(callback: CallbackQuery) -> None:
    if not await check_admin_callback(callback):
        return

    parts = str(callback.data).split(":")
    if len(parts) != 4:
        await callback.answer("Некорректная кнопка.", show_alert=True)
        return

    filter_key = normalize_filter_key(parts[2])
    page = max(parse_int(parts[3]), 0)

    await callback.answer()
    await show_admin_orders(callback, filter_key, page)


@router.callback_query(F.data.startswith("admin:order:"))
async def admin_order_card_callback(callback: CallbackQuery) -> None:
    if not await check_admin_callback(callback):
        return

    parts = str(callback.data).split(":")
    if len(parts) != 5:
        await callback.answer("Некорректная кнопка.", show_alert=True)
        return

    order_id = parse_int(parts[2])
    filter_key = normalize_filter_key(parts[3])
    page = max(parse_int(parts[4]), 0)

    if order_id <= 0:
        await callback.answer("Некорректный номер заказа.", show_alert=True)
        return

    await callback.answer()
    await show_admin_order_card(
        callback,
        order_id,
        filter_key,
        page,
    )


@router.callback_query(F.data.startswith("admin:status:"))
async def admin_status_callback(callback: CallbackQuery) -> None:
    if not await check_admin_callback(callback):
        return

    parts = str(callback.data).split(":")
    if len(parts) != 6:
        await callback.answer("Некорректная кнопка.", show_alert=True)
        return

    order_id = parse_int(parts[2])
    new_status = parts[3]
    filter_key = normalize_filter_key(parts[4])
    page = max(parse_int(parts[5]), 0)

    try:
        result = await update_order_status(
            order_id=order_id,
            new_status=new_status,
            admin_telegram_id=callback.from_user.id,
        )
    except ValueError as error:
        await callback.answer(str(error), show_alert=True)
        return
    except Exception:
        logging.exception("Не удалось изменить статус заказа %s", order_id)
        await callback.answer(
            "Не удалось изменить статус заказа.",
            show_alert=True,
        )
        return

    if result["changed"]:
        await callback.answer(
            "Статус: {0}".format(
                ORDER_STATUS_LABELS.get(new_status, new_status)
            )
        )
        await notify_customer_status(callback.bot, result)
    else:
        await callback.answer("Статус уже установлен.")

    await show_admin_order_card(
        callback,
        order_id,
        filter_key,
        page,
    )


@router.callback_query(F.data == "admin:new_orders")
async def legacy_admin_new_orders_callback(callback: CallbackQuery) -> None:
    """Совместимость со старыми кнопками."""
    if not await check_admin_callback(callback):
        return

    await callback.answer()
    await show_admin_orders(callback, "new", 0)


@router.callback_query(F.data == "admin:all_orders")
async def legacy_admin_all_orders_callback(callback: CallbackQuery) -> None:
    """Совместимость со старыми кнопками."""
    if not await check_admin_callback(callback):
        return

    await callback.answer()
    await show_admin_filters(callback)


@router.callback_query(F.data == "noop")
async def noop_callback(callback: CallbackQuery) -> None:
    await callback.answer()


@router.callback_query(F.data == "admin:products")
async def admin_products_callback(
    callback: CallbackQuery,
    state: FSMContext,
) -> None:
    """Главное меню управления каталогом."""
    if not await check_admin_callback(callback):
        return
    await state.clear()
    await callback.answer()
    counts = await get_catalog_counts()
    await edit_or_send(
        callback,
        (
            "<b>Управление каталогом 🌷</b>\n\n"
            "Товары: <b>{0}</b>\n"
            "Типы товаров: <b>Букеты · Открытки · Мягкие игрушки</b>\n"
            "Дополнения: <b>{1}</b>\n"
            "Популярные: <b>{2}</b>\n\n"
            "Выберите раздел."
        ).format(
            counts["product_count"],
            counts["addon_count"],
            counts["featured_count"],
        ),
        catalog_admin_menu_keyboard(**counts),
    )


async def show_featured_products_admin(
    callback: CallbackQuery,
) -> None:
    featured = await get_featured_products_admin()
    lines = []
    for index, product in enumerate(featured, start=1):
        status = "" if bool(product["is_active"]) else " — скрыт"
        lines.append(
            "{0}. <b>{1}</b>{2}".format(
                index,
                html.escape(str(product["name"])),
                status,
            )
        )

    text = (
        "<b>Популярные букеты ⭐</b>\n\n"
        "На главной отображаются все выбранные букеты "
        "в указанном порядке. Количество не ограничено.\n\n"
        "{0}"
    ).format(
        "\n".join(lines) or "Популярные букеты пока не выбраны.",
    )
    await edit_or_send(
        callback,
        text,
        featured_products_keyboard(featured),
    )


async def show_featured_candidates_admin(
    callback: CallbackQuery,
    page: int,
) -> None:
    data = await get_featured_candidates_page(page)
    await edit_or_send(
        callback,
        (
            "<b>Добавить в популярные</b>\n\n"
            "Выберите опубликованный букет. "
            "Он появится в конце блока на главной."
        ),
        featured_candidates_keyboard(
            data["products"],
            data["page"],
            data["total_pages"],
        ),
    )


@router.callback_query(F.data == "admin:featured")
async def admin_featured_callback(callback: CallbackQuery) -> None:
    if not await check_admin_callback(callback):
        return
    await callback.answer()
    await show_featured_products_admin(callback)


@router.callback_query(F.data.startswith("feat:addlist:"))
async def featured_add_list_callback(callback: CallbackQuery) -> None:
    if not await check_admin_callback(callback):
        return
    page = parse_int(callback.data.split(":")[2], 0)
    await callback.answer()
    await show_featured_candidates_admin(callback, page)


@router.callback_query(F.data.startswith("feat:add:"))
async def featured_add_callback(callback: CallbackQuery) -> None:
    if not await check_admin_callback(callback):
        return
    parts = callback.data.split(":")
    product_id = parse_int(parts[2])
    try:
        await add_featured_product(product_id)
    except ValueError as error:
        await callback.answer(str(error), show_alert=True)
        return
    await callback.answer("Букет добавлен на главную ⭐")
    await show_featured_products_admin(callback)


@router.callback_query(F.data.startswith("feat:remove:"))
async def featured_remove_callback(callback: CallbackQuery) -> None:
    if not await check_admin_callback(callback):
        return
    product_id = parse_int(callback.data.split(":")[2])
    await remove_featured_product(product_id)
    await callback.answer("Букет убран с главной")
    await show_featured_products_admin(callback)


@router.callback_query(F.data.startswith("feat:move:"))
async def featured_move_callback(callback: CallbackQuery) -> None:
    if not await check_admin_callback(callback):
        return
    parts = callback.data.split(":")
    product_id = parse_int(parts[2])
    direction = parts[3] if len(parts) > 3 else ""
    if direction not in {"up", "down"}:
        await callback.answer("Некорректное направление", show_alert=True)
        return
    try:
        await move_featured_product(product_id, direction)
    except ValueError as error:
        await callback.answer(str(error), show_alert=True)
        return
    await callback.answer("Порядок изменён")
    await show_featured_products_admin(callback)


@router.callback_query(F.data.startswith("feat:toggle:"))
async def featured_toggle_callback(callback: CallbackQuery) -> None:
    if not await check_admin_callback(callback):
        return
    parts = callback.data.split(":")
    product_id = parse_int(parts[2])
    page = parse_int(parts[3], 0)
    try:
        enabled = await toggle_featured_product(product_id)
    except ValueError as error:
        await callback.answer(str(error), show_alert=True)
        return
    await callback.answer(
        "Добавлен в популярные ⭐" if enabled else "Убран с главной"
    )
    await show_product_admin(callback, product_id, page)


async def show_products_admin(callback: CallbackQuery, page: int) -> None:
    data = await get_products_page(page)
    text = (
        "<b>Товары 🌷</b>\n\n"
        "Всего товаров: <b>{0}</b>\n"
        "🟢 — опубликован, ⚪️ — скрыт."
    ).format(data["total"])
    await edit_or_send(
        callback,
        text,
        products_list_keyboard(
            data["products"],
            data["page"],
            data["total_pages"],
        ),
    )


async def show_product_admin(
    callback: CallbackQuery,
    product_id: int,
    page: int,
) -> None:
    details = await get_product_admin(product_id)
    if details is None:
        await callback.answer("Товар не найден.", show_alert=True)
        await show_products_admin(callback, page)
        return
    product = details["product"]
    await edit_or_send(
        callback,
        format_product_admin_card(details),
        product_card_keyboard(
            product_id=product_id,
            page=page,
            is_active=bool(product["is_active"]),
            has_image=bool(product["image_url"]),
            image_count=len(details.get("images", [])),
            is_featured=product["featured_position"] is not None,
        ),
    )


async def show_product_gallery_admin(
    callback: CallbackQuery,
    product_id: int,
    page: int,
) -> None:
    details = await get_product_admin(product_id)
    if details is None:
        await callback.answer("Товар не найден.", show_alert=True)
        return
    await edit_or_send(
        callback,
        format_product_gallery_admin(details),
        product_gallery_keyboard(
            product_id=product_id,
            page=page,
            images=details.get("images", []),
            max_images=MAX_PRODUCT_IMAGES,
        ),
    )


@router.callback_query(F.data.startswith("p:g:"))
async def product_gallery_callback(callback: CallbackQuery) -> None:
    if not await check_admin_callback(callback):
        return
    parts = callback.data.split(":")
    product_id = parse_int(parts[2])
    page = parse_int(parts[3], 0)
    await callback.answer()
    await show_product_gallery_admin(callback, product_id, page)


@router.callback_query(F.data.startswith("pg:add:"))
async def product_gallery_add_callback(
    callback: CallbackQuery,
    state: FSMContext,
) -> None:
    if not await check_admin_callback(callback):
        return
    parts = callback.data.split(":")
    product_id = parse_int(parts[2])
    page = parse_int(parts[3], 0)
    details = await get_product_admin(product_id)
    if details is None:
        await callback.answer("Товар не найден.", show_alert=True)
        return
    if len(details.get("images", [])) >= MAX_PRODUCT_IMAGES:
        await callback.answer(
            "Достигнут лимит фотографий.",
            show_alert=True,
        )
        return

    await state.clear()
    await state.update_data(
        gallery_product_id=product_id,
        gallery_page=page,
    )
    await state.set_state(ProductGalleryStates.add_image)
    await callback.answer()
    await edit_or_send(
        callback,
        (
            "<b>Добавление фотографии</b>\n\n"
            "Пришлите фотографию сообщением или отправьте http(s)-ссылку.\n"
            "До <b>{0}</b> фотографий на один товар."
        ).format(MAX_PRODUCT_IMAGES),
        catalog_cancel_keyboard(),
    )


@router.message(ProductGalleryStates.add_image)
async def product_gallery_add_message(
    message: Message,
    state: FSMContext,
) -> None:
    if not await ensure_admin_message(message):
        return
    data = await state.get_data()
    product_id = int(data["gallery_product_id"])
    page = int(data.get("gallery_page", 0))

    try:
        image_url = extract_image_value(message)
        if not image_url:
            raise ValueError("Пришлите фотографию или ссылку")
        await add_product_image(product_id, image_url)
    except ValueError as error:
        await message.answer(str(error))
        return

    await state.clear()
    details = await get_product_admin(product_id)
    await message.answer(
        "Фотография добавлена ✅\n\n"
        + format_product_gallery_admin(details),
        reply_markup=product_gallery_keyboard(
            product_id=product_id,
            page=page,
            images=details.get("images", []),
            max_images=MAX_PRODUCT_IMAGES,
        ),
    )


@router.callback_query(F.data.startswith("pg:show:"))
async def product_gallery_show_callback(callback: CallbackQuery) -> None:
    if not await check_admin_callback(callback):
        return
    parts = callback.data.split(":")
    product_id = parse_int(parts[2])
    details = await get_product_admin(product_id)
    if details is None:
        await callback.answer("Товар не найден.", show_alert=True)
        return

    images = details.get("images", [])
    if not images:
        await callback.answer("Галерея пустая.", show_alert=True)
        return

    try:
        media = []
        for index, image in enumerate(images[:10]):
            caption = None
            if index == 0:
                caption = "<b>{0}</b> · {1} фото".format(
                    html.escape(str(details["product"]["name"])),
                    len(images),
                )
            media.append(
                InputMediaPhoto(
                    media=product_image_for_telegram(
                        str(image["image_url"])
                    ),
                    caption=caption,
                    parse_mode=ParseMode.HTML if caption else None,
                )
            )

        if len(media) == 1:
            await callback.message.answer_photo(
                photo=media[0].media,
                caption=media[0].caption,
            )
        else:
            await callback.message.answer_media_group(media=media)
        await callback.answer()
    except Exception:
        logging.exception(
            "Не удалось показать галерею товара %s",
            product_id,
        )
        await callback.answer(
            "Не удалось открыть одну из фотографий.",
            show_alert=True,
        )


@router.callback_query(F.data.startswith("pg:main:"))
async def product_gallery_primary_callback(callback: CallbackQuery) -> None:
    if not await check_admin_callback(callback):
        return
    parts = callback.data.split(":")
    product_id = parse_int(parts[2])
    page = parse_int(parts[3], 0)
    image_id = parse_int(parts[4])
    try:
        await set_product_primary_image(product_id, image_id)
    except ValueError as error:
        await callback.answer(str(error), show_alert=True)
        return
    await callback.answer("Главное фото изменено ✅")
    await show_product_gallery_admin(callback, product_id, page)


@router.callback_query(F.data.startswith("pg:del:"))
async def product_gallery_delete_callback(callback: CallbackQuery) -> None:
    if not await check_admin_callback(callback):
        return
    parts = callback.data.split(":")
    product_id = parse_int(parts[2])
    page = parse_int(parts[3], 0)
    image_id = parse_int(parts[4])
    try:
        await delete_product_image(product_id, image_id)
    except ValueError as error:
        await callback.answer(str(error), show_alert=True)
        return
    await callback.answer("Фотография удалена")
    await show_product_gallery_admin(callback, product_id, page)


@router.callback_query(F.data.startswith("p:list:"))
async def products_list_callback(callback: CallbackQuery) -> None:
    if not await check_admin_callback(callback):
        return
    await callback.answer()
    page = parse_int(callback.data.split(":")[2], 0)
    await show_products_admin(callback, page)


@router.callback_query(F.data.startswith("p:view:"))
async def product_view_callback(callback: CallbackQuery) -> None:
    if not await check_admin_callback(callback):
        return
    parts = callback.data.split(":")
    product_id = parse_int(parts[2])
    page = parse_int(parts[3], 0)
    await callback.answer()
    await show_product_admin(callback, product_id, page)


@router.callback_query(F.data.startswith("p:photo:"))
async def product_photo_callback(callback: CallbackQuery) -> None:
    if not await check_admin_callback(callback):
        return
    product_id = parse_int(callback.data.split(":")[2])
    details = await get_product_admin(product_id)
    if details is None or not details["product"]["image_url"]:
        await callback.answer("У товара нет фотографии.", show_alert=True)
        return
    try:
        source = product_image_for_telegram(
            str(details["product"]["image_url"])
        )
        await callback.message.answer_photo(
            photo=source,
            caption="<b>{0}</b>".format(
                html.escape(str(details["product"]["name"]))
            ),
        )
        await callback.answer()
    except Exception:
        logging.exception("Не удалось показать фото товара %s", product_id)
        await callback.answer(
            "Не удалось открыть фотографию. Обновите её.",
            show_alert=True,
        )


@router.callback_query(F.data == "p:add")
async def product_add_start_callback(
    callback: CallbackQuery,
    state: FSMContext,
) -> None:
    if not await check_admin_callback(callback):
        return
    await state.clear()
    await state.set_state(ProductCreateStates.name)
    await callback.answer()
    await edit_or_send(
        callback,
        "<b>Новый товар — шаг 1/9</b>\n\nВведите название букета.",
        catalog_cancel_keyboard(),
    )


@router.message(Command("cancel"))
async def catalog_cancel_command(message: Message, state: FSMContext) -> None:
    if not user_is_admin(message.from_user.id):
        return
    current = await state.get_state()
    if current is None:
        await message.answer("Сейчас нет активного действия.")
        return
    await state.clear()
    await message.answer(
        "Действие отменено.",
        reply_markup=catalog_admin_menu_keyboard(**(await get_catalog_counts())),
    )


@router.message(ProductCreateStates.name)
async def product_add_name_message(message: Message, state: FSMContext) -> None:
    if not await ensure_admin_message(message):
        return
    name = (message.text or "").strip()
    if len(name) < 2 or len(name) > 80:
        await message.answer("Название должно содержать от 2 до 80 символов.")
        return
    await state.update_data(name=name)
    await state.set_state(ProductCreateStates.description)
    await message.answer(
        "<b>Шаг 2/9</b>\n\nВведите описание букета. Для пустого описания отправьте <code>-</code>.",
        reply_markup=catalog_cancel_keyboard(),
    )


@router.message(ProductCreateStates.description)
async def product_add_description_message(
    message: Message,
    state: FSMContext,
) -> None:
    if not await ensure_admin_message(message):
        return
    description = normalize_optional_text(message.text or "")
    if len(description) > 1000:
        await message.answer("Описание не должно превышать 1000 символов.")
        return
    await state.update_data(description=description)
    await state.set_state(ProductCreateStates.composition)
    await message.answer(
        "<b>Шаг 3/9</b>\n\n"
        "Для букета введите состав через запятую. "
        "Для открытки или игрушки отправьте <code>-</code>.\n"
        "Например: <code>розы, гортензия, орхидеи, эвкалипт</code>.",
        reply_markup=catalog_cancel_keyboard(),
    )


@router.message(ProductCreateStates.composition)
async def product_add_composition_message(
    message: Message,
    state: FSMContext,
) -> None:
    if not await ensure_admin_message(message):
        return
    composition = normalize_optional_text(message.text or "")
    if len(composition) > 500:
        await message.answer("Состав не должен превышать 500 символов.")
        return
    await state.update_data(composition=composition)
    await state.set_state(ProductCreateStates.image)
    await message.answer(
        "<b>Шаг 4/9</b>\n\nПришлите фотографию букета, прямую http(s)-ссылку или слово <code>пропустить</code>.",
        reply_markup=catalog_cancel_keyboard(),
    )


@router.message(ProductCreateStates.image)
async def product_add_image_message(message: Message, state: FSMContext) -> None:
    if not await ensure_admin_message(message):
        return
    try:
        image_url = extract_image_value(message)
    except ValueError as error:
        await message.answer(str(error))
        return
    await state.update_data(image_url=image_url)
    await state.set_state(ProductCreateStates.price_s)
    await message.answer(
        "<b>Шаг 5/9</b>\n\nВведите цену размера <b>S</b> в рублях, например <code>2490</code>.",
        reply_markup=catalog_cancel_keyboard(),
    )


@router.message(ProductCreateStates.price_s)
async def product_add_price_s_message(message: Message, state: FSMContext) -> None:
    if not await ensure_admin_message(message):
        return
    try:
        price = parse_price_text(message.text or "")
    except ValueError as error:
        await message.answer(str(error))
        return
    await state.update_data(price_s=price)
    await state.set_state(ProductCreateStates.price_m)
    await message.answer(
        "<b>Шаг 6/9</b>\n\nВведите цену размера <b>M</b>.",
        reply_markup=catalog_cancel_keyboard(),
    )


@router.message(ProductCreateStates.price_m)
async def product_add_price_m_message(message: Message, state: FSMContext) -> None:
    if not await ensure_admin_message(message):
        return
    try:
        price = parse_price_text(message.text or "")
    except ValueError as error:
        await message.answer(str(error))
        return
    data = await state.get_data()
    if price < int(data["price_s"]):
        await message.answer("Цена M не должна быть ниже цены S.")
        return
    await state.update_data(price_m=price)
    await state.set_state(ProductCreateStates.price_l)
    await message.answer(
        "<b>Шаг 7/9</b>\n\nВведите цену размера <b>L</b>.",
        reply_markup=catalog_cancel_keyboard(),
    )


@router.message(ProductCreateStates.price_l)
async def product_add_price_l_message(message: Message, state: FSMContext) -> None:
    if not await ensure_admin_message(message):
        return
    try:
        price = parse_price_text(message.text or "")
    except ValueError as error:
        await message.answer(str(error))
        return
    data = await state.get_data()
    if price < int(data["price_m"]):
        await message.answer("Цена L не должна быть ниже цены M.")
        return

    categories = await get_categories_admin()
    active_categories = [row for row in categories if int(row["is_active"])]
    if not active_categories:
        await message.answer(
            "Не найдены системные типы товаров. Перезапустите бота."
        )
        await state.clear()
        return

    await state.update_data(
        prices={
            "S": int(data["price_s"]),
            "M": int(data["price_m"]),
            "L": price,
        }
    )
    await state.set_state(ProductCreateStates.category)
    await message.answer(
        "<b>Шаг 8/9</b>\n\nВыберите категорию товара.",
        reply_markup=category_select_keyboard(
            active_categories,
            prefix="pa:cat",
        ),
    )


@router.callback_query(F.data.startswith("pa:cat:"))
async def product_add_category_callback(
    callback: CallbackQuery,
    state: FSMContext,
) -> None:
    if not await check_admin_callback(callback):
        return
    category_id = parse_int(callback.data.split(":")[2])
    category = await get_category_admin(category_id)
    if category is None:
        await callback.answer("Категория не найдена.", show_alert=True)
        return

    addons = [row for row in await get_addons_admin() if int(row["is_active"])]
    await state.update_data(
        category_id=category_id,
        category_name=str(category["name"]),
        addon_ids=[],
    )
    await state.set_state(ProductCreateStates.addons)
    await callback.answer()
    await edit_or_send(
        callback,
        "<b>Шаг 9/9</b>\n\nВыберите доступные дополнения. Можно не выбирать ни одного.",
        addons_select_keyboard(
            addons,
            [],
            toggle_prefix="pa:addon",
            done_callback="pa:done",
        ),
    )


@router.callback_query(F.data.startswith("pa:addon:"))
async def product_add_addon_toggle_callback(
    callback: CallbackQuery,
    state: FSMContext,
) -> None:
    if not await check_admin_callback(callback):
        return
    addon_id = parse_int(callback.data.split(":")[2])
    data = await state.get_data()
    selected = {int(value) for value in data.get("addon_ids", [])}
    if addon_id in selected:
        selected.remove(addon_id)
    else:
        selected.add(addon_id)
    await state.update_data(addon_ids=sorted(selected))
    addons = [row for row in await get_addons_admin() if int(row["is_active"])]
    await callback.answer()
    await edit_or_send(
        callback,
        "<b>Шаг 9/9</b>\n\nВыберите доступные дополнения.",
        addons_select_keyboard(
            addons,
            sorted(selected),
            toggle_prefix="pa:addon",
            done_callback="pa:done",
        ),
    )


@router.callback_query(F.data == "pa:done")
async def product_add_done_callback(
    callback: CallbackQuery,
    state: FSMContext,
) -> None:
    if not await check_admin_callback(callback):
        return
    data = await state.get_data()
    addon_ids = {int(value) for value in data.get("addon_ids", [])}
    addons = await get_addons_admin()
    addon_names = [str(row["name"]) for row in addons if int(row["id"]) in addon_ids]
    await state.update_data(addon_names=addon_names)
    await state.set_state(ProductCreateStates.confirm)
    final_data = await state.get_data()
    await callback.answer()
    await edit_or_send(
        callback,
        format_product_draft(final_data),
        product_create_confirm_keyboard(),
    )


@router.callback_query(F.data == "pa:confirm")
async def product_add_confirm_callback(
    callback: CallbackQuery,
    state: FSMContext,
) -> None:
    if not await check_admin_callback(callback):
        return
    data = await state.get_data()
    try:
        product_id = await create_product_admin(data)
    except (ValueError, sqlite3.Error) as error:
        logging.exception("Не удалось создать товар")
        await callback.answer(str(error), show_alert=True)
        return
    await state.clear()
    await callback.answer("Товар создан ✅")
    await show_product_admin(callback, product_id, 0)


@router.callback_query(F.data == "catalog:cancel")
async def catalog_cancel_callback(
    callback: CallbackQuery,
    state: FSMContext,
) -> None:
    if not await check_admin_callback(callback):
        return
    await state.clear()
    await callback.answer("Действие отменено.")
    counts = await get_catalog_counts()
    await edit_or_send(
        callback,
        "<b>Управление каталогом 🌷</b>\n\nДействие отменено.",
        catalog_admin_menu_keyboard(**counts),
    )




@router.callback_query(F.data.startswith("p:e:"))
async def product_edit_start_callback(
    callback: CallbackQuery,
    state: FSMContext,
) -> None:
    if not await check_admin_callback(callback):
        return
    parts = callback.data.split(":")
    product_id = parse_int(parts[2])
    field = parts[3]
    details = await get_product_admin(product_id)
    if details is None:
        await callback.answer("Товар не найден.", show_alert=True)
        return

    if field == "category":
        categories = await get_categories_admin()
        await callback.answer()
        await edit_or_send(
            callback,
            "<b>Выберите новый тип товара</b>",
            category_select_keyboard(
                categories,
                prefix="pe:cat:{0}:0".format(product_id),
                selected_id=details["product"]["category_id"],
            ),
        )
        return

    if field == "addons":
        addons = await get_addons_admin()
        selected = [int(row["id"]) for row in details["addons"]]
        await callback.answer()
        await edit_or_send(
            callback,
            "<b>Дополнения товара</b>\n\nИзменения сохраняются сразу.",
            addons_select_keyboard(
                addons,
                selected,
                toggle_prefix="pe:addon:{0}:0".format(product_id),
                done_callback="pe:addondone:{0}:0".format(product_id),
                cancel_callback="p:view:{0}:0".format(product_id),
            ),
        )
        return

    prompts = {
        "name": "Введите новое название товара.",
        "desc": "Введите новое описание. Для пустого описания отправьте <code>-</code>.",
        "composition": (
            "Введите новый состав через запятую. "
            "Например: <code>розы, гортензия, эвкалипт</code>."
        ),
        "photo": "Пришлите новую фотографию, http(s)-ссылку или слово <code>пропустить</code>, чтобы удалить фото.",
        "prices": "Введите цены S, M и L через пробел, например: <code>2490 3490 4990</code>.",
    }
    if field not in prompts:
        await callback.answer("Неизвестное действие.", show_alert=True)
        return

    await state.clear()
    await state.update_data(
        edit_product_id=product_id,
        edit_field=field,
        edit_page=0,
    )
    await state.set_state(CatalogEditStates.waiting_value)
    await callback.answer()
    await edit_or_send(
        callback,
        "<b>Редактирование товара</b>\n\n{0}".format(prompts[field]),
        catalog_cancel_keyboard(),
    )


@router.message(CatalogEditStates.waiting_value)
async def product_edit_value_message(
    message: Message,
    state: FSMContext,
) -> None:
    if not await ensure_admin_message(message):
        return
    data = await state.get_data()
    product_id = int(data["edit_product_id"])
    field = str(data["edit_field"])

    try:
        if field == "name":
            value = (message.text or "").strip()
            if len(value) < 2 or len(value) > 80:
                raise ValueError("Название должно содержать от 2 до 80 символов")
            await update_product_text(product_id, "name", value)
        elif field == "desc":
            value = normalize_optional_text(message.text or "")
            if len(value) > 1000:
                raise ValueError("Описание не должно превышать 1000 символов")
            await update_product_text(product_id, "description", value)
        elif field == "composition":
            value = normalize_optional_text(message.text or "")
            if len(value) > 500:
                raise ValueError("Состав не должен превышать 500 символов")
            await update_product_text(product_id, "composition", value)
        elif field == "photo":
            value = extract_image_value(message)
            await update_product_text(product_id, "image_url", value)
        elif field == "prices":
            prices = parse_three_prices(message.text or "")
            if not (prices["S"] <= prices["M"] <= prices["L"]):
                raise ValueError("Цены должны идти по возрастанию: S ≤ M ≤ L")
            await update_product_prices(product_id, prices)
        else:
            raise ValueError("Неизвестное поле")
    except ValueError as error:
        await message.answer(str(error))
        return

    await state.clear()
    details = await get_product_admin(product_id)
    await message.answer(
        "Изменения сохранены ✅\n\n" + format_product_admin_card(details),
        reply_markup=product_card_keyboard(
            product_id,
            int(data.get("edit_page", 0)),
            bool(details["product"]["is_active"]),
            bool(details["product"]["image_url"]),
            len(details.get("images", [])),
            details["product"]["featured_position"] is not None,
        ),
    )


@router.callback_query(F.data.startswith("pe:cat:"))
async def product_edit_category_callback(callback: CallbackQuery) -> None:
    if not await check_admin_callback(callback):
        return
    parts = callback.data.split(":")
    product_id = parse_int(parts[2])
    page = parse_int(parts[3], 0)
    category_id = parse_int(parts[4])
    try:
        await set_product_category(product_id, category_id)
    except ValueError as error:
        await callback.answer(str(error), show_alert=True)
        return
    await callback.answer("Тип товара изменён ✅")
    await show_product_admin(callback, product_id, page)


@router.callback_query(F.data.startswith("pe:addon:"))
async def product_edit_addon_callback(callback: CallbackQuery) -> None:
    if not await check_admin_callback(callback):
        return
    parts = callback.data.split(":")
    product_id = parse_int(parts[2])
    page = parse_int(parts[3], 0)
    addon_id = parse_int(parts[4])
    details = await get_product_admin(product_id)
    if details is None:
        await callback.answer("Товар не найден.", show_alert=True)
        return
    selected = {int(row["id"]) for row in details["addons"]}
    if addon_id in selected:
        selected.remove(addon_id)
    else:
        selected.add(addon_id)
    await set_product_addons(product_id, sorted(selected))
    addons = await get_addons_admin()
    await callback.answer("Сохранено")
    await edit_or_send(
        callback,
        "<b>Дополнения товара</b>\n\nИзменения сохраняются сразу.",
        addons_select_keyboard(
            addons,
            sorted(selected),
            toggle_prefix="pe:addon:{0}:{1}".format(product_id, page),
            done_callback="pe:addondone:{0}:{1}".format(product_id, page),
            cancel_callback="p:view:{0}:{1}".format(product_id, page),
        ),
    )


@router.callback_query(F.data.startswith("pe:addondone:"))
async def product_edit_addons_done_callback(callback: CallbackQuery) -> None:
    if not await check_admin_callback(callback):
        return
    parts = callback.data.split(":")
    product_id = parse_int(parts[2])
    page = parse_int(parts[3], 0)
    await callback.answer("Дополнения сохранены ✅")
    await show_product_admin(callback, product_id, page)


@router.callback_query(F.data.startswith("p:t:"))
async def product_toggle_callback(callback: CallbackQuery) -> None:
    if not await check_admin_callback(callback):
        return
    parts = callback.data.split(":")
    product_id = parse_int(parts[2])
    page = parse_int(parts[3], 0)
    try:
        active = await toggle_product_active(product_id)
    except ValueError as error:
        await callback.answer(str(error), show_alert=True)
        return
    await callback.answer("Товар опубликован" if active else "Товар скрыт")
    await show_product_admin(callback, product_id, page)


@router.callback_query(F.data.startswith("p:del:"))
async def product_delete_callback(callback: CallbackQuery) -> None:
    if not await check_admin_callback(callback):
        return
    parts = callback.data.split(":")
    product_id = parse_int(parts[2])
    page = parse_int(parts[3], 0)
    details = await get_product_admin(product_id)
    if details is None:
        await callback.answer("Товар не найден.", show_alert=True)
        return
    await callback.answer()
    await edit_or_send(
        callback,
        (
            "<b>Удалить товар?</b>\n\n"
            "{0}\n\n"
            "Карточка исчезнет из каталога. В старых заказах название и цена сохранятся."
        ).format(html.escape(str(details["product"]["name"]))),
        product_delete_confirm_keyboard(product_id, page),
    )


@router.callback_query(F.data.startswith("p:delok:"))
async def product_delete_confirm_callback(callback: CallbackQuery) -> None:
    if not await check_admin_callback(callback):
        return
    parts = callback.data.split(":")
    product_id = parse_int(parts[2])
    page = parse_int(parts[3], 0)
    try:
        await delete_product(product_id)
    except ValueError as error:
        await callback.answer(str(error), show_alert=True)
        return
    await callback.answer("Товар удалён ✅")
    await show_products_admin(callback, page)


async def show_categories_admin(callback: CallbackQuery) -> None:
    categories = await get_categories_admin()
    await edit_or_send(
        callback,
        "<b>Типы товаров</b>\n\nСписок зафиксирован и используется в каталоге Mini App.",
        categories_list_keyboard(categories),
    )


async def show_category_admin(callback: CallbackQuery, category_id: int) -> None:
    category = await get_category_admin(category_id)
    if category is None:
        await callback.answer("Категория не найдена.", show_alert=True)
        await show_categories_admin(callback)
        return
    await edit_or_send(
        callback,
        (
            "<b>{0}</b>\n\n"
            "Статус: <b>{1}</b>\n"
            "Товаров: <b>{2}</b>\n"
            "Позиция: <code>{3}</code>"
        ).format(
            html.escape(str(category["name"])),
            "показывается" if int(category["is_active"]) else "скрыта",
            int(category["product_count"]),
            int(category["position"]),
        ),
        category_card_keyboard(category_id, bool(category["is_active"])),
    )


@router.callback_query(F.data == "c:list")
async def categories_list_callback(callback: CallbackQuery) -> None:
    if not await check_admin_callback(callback):
        return
    await callback.answer()
    await show_categories_admin(callback)


@router.callback_query(F.data.startswith("c:view:"))
async def category_view_callback(callback: CallbackQuery) -> None:
    if not await check_admin_callback(callback):
        return
    category_id = parse_int(callback.data.split(":")[2])
    await callback.answer()
    await show_category_admin(callback, category_id)


@router.callback_query(F.data == "c:add")
async def category_add_start_callback(
    callback: CallbackQuery,
    state: FSMContext,
) -> None:
    if not await check_admin_callback(callback):
        return
    await state.clear()
    await state.set_state(CategoryStates.add_name)
    await callback.answer()
    await edit_or_send(
        callback,
        "<b>Новая категория</b>\n\nВведите название.",
        catalog_cancel_keyboard(),
    )


@router.message(CategoryStates.add_name)
async def category_add_name_message(message: Message, state: FSMContext) -> None:
    if not await ensure_admin_message(message):
        return
    try:
        category_id = await create_category(message.text or "")
    except ValueError as error:
        await message.answer(str(error))
        return
    await state.clear()
    category = await get_category_admin(category_id)
    await message.answer(
        "Категория создана ✅\n\n<b>{0}</b>".format(
            html.escape(str(category["name"]))
        ),
        reply_markup=category_card_keyboard(category_id, True),
    )


@router.callback_query(F.data.startswith("c:e:"))
async def category_rename_start_callback(
    callback: CallbackQuery,
    state: FSMContext,
) -> None:
    if not await check_admin_callback(callback):
        return
    category_id = parse_int(callback.data.split(":")[2])
    await state.clear()
    await state.update_data(category_id=category_id)
    await state.set_state(CategoryStates.rename)
    await callback.answer()
    await edit_or_send(
        callback,
        "Введите новое название категории.",
        catalog_cancel_keyboard(),
    )


@router.message(CategoryStates.rename)
async def category_rename_message(message: Message, state: FSMContext) -> None:
    if not await ensure_admin_message(message):
        return
    data = await state.get_data()
    category_id = int(data["category_id"])
    try:
        await rename_category(category_id, message.text or "")
    except ValueError as error:
        await message.answer(str(error))
        return
    await state.clear()
    category = await get_category_admin(category_id)
    await message.answer(
        "Категория переименована ✅\n\n<b>{0}</b>".format(
            html.escape(str(category["name"]))
        ),
        reply_markup=category_card_keyboard(
            category_id, bool(category["is_active"])
        ),
    )


@router.callback_query(F.data.startswith("c:t:"))
async def category_toggle_callback(callback: CallbackQuery) -> None:
    if not await check_admin_callback(callback):
        return
    category_id = parse_int(callback.data.split(":")[2])
    try:
        active = await toggle_category(category_id)
    except ValueError as error:
        await callback.answer(str(error), show_alert=True)
        return
    await callback.answer("Категория включена" if active else "Категория скрыта")
    await show_category_admin(callback, category_id)


@router.callback_query(F.data.startswith("c:m:"))
async def category_move_callback(callback: CallbackQuery) -> None:
    if not await check_admin_callback(callback):
        return
    parts = callback.data.split(":")
    category_id = parse_int(parts[2])
    direction = parts[3]
    try:
        await move_category(category_id, direction)
    except ValueError as error:
        await callback.answer(str(error), show_alert=True)
        return
    await callback.answer("Порядок изменён")
    await show_categories_admin(callback)


async def show_addons_admin(callback: CallbackQuery) -> None:
    addons = await get_addons_admin()
    await edit_or_send(
        callback,
        "<b>Дополнения 🎁</b>\n\nОтключённые дополнения сохраняются в старых заказах, но не показываются клиентам.",
        addons_list_keyboard(addons),
    )


async def show_addon_admin(callback: CallbackQuery, addon_id: int) -> None:
    addon = await get_addon_admin(addon_id)
    if addon is None:
        await callback.answer("Дополнение не найдено.", show_alert=True)
        await show_addons_admin(callback)
        return
    await edit_or_send(
        callback,
        (
            "<b>{0}</b>\n\n"
            "Цена: <b>{1}</b>\n"
            "Статус: <b>{2}</b>"
        ).format(
            html.escape(str(addon["name"])),
            format_money(int(addon["price"])),
            "включено" if int(addon["is_active"]) else "отключено",
        ),
        addon_card_keyboard(addon_id, bool(addon["is_active"])),
    )


@router.callback_query(F.data == "a:list")
async def addons_list_callback(callback: CallbackQuery) -> None:
    if not await check_admin_callback(callback):
        return
    await callback.answer()
    await show_addons_admin(callback)


@router.callback_query(F.data.startswith("a:view:"))
async def addon_view_callback(callback: CallbackQuery) -> None:
    if not await check_admin_callback(callback):
        return
    addon_id = parse_int(callback.data.split(":")[2])
    await callback.answer()
    await show_addon_admin(callback, addon_id)


@router.callback_query(F.data == "a:add")
async def addon_add_start_callback(
    callback: CallbackQuery,
    state: FSMContext,
) -> None:
    if not await check_admin_callback(callback):
        return
    await state.clear()
    await state.set_state(AddonStates.add_name)
    await callback.answer()
    await edit_or_send(
        callback,
        "<b>Новое дополнение — шаг 1/2</b>\n\nВведите название.",
        catalog_cancel_keyboard(),
    )


@router.message(AddonStates.add_name)
async def addon_add_name_message(message: Message, state: FSMContext) -> None:
    if not await ensure_admin_message(message):
        return
    name = (message.text or "").strip()
    if len(name) < 2 or len(name) > 80:
        await message.answer("Название должно содержать от 2 до 80 символов.")
        return
    await state.update_data(addon_name=name)
    await state.set_state(AddonStates.add_price)
    await message.answer(
        "<b>Новое дополнение — шаг 2/2</b>\n\nВведите цену в рублях.",
        reply_markup=catalog_cancel_keyboard(),
    )


@router.message(AddonStates.add_price)
async def addon_add_price_message(message: Message, state: FSMContext) -> None:
    if not await ensure_admin_message(message):
        return
    try:
        price = parse_price_text(message.text or "")
    except ValueError as error:
        await message.answer(str(error))
        return
    data = await state.get_data()
    try:
        addon_id = await create_addon(str(data["addon_name"]), price)
    except ValueError as error:
        await message.answer(str(error))
        return
    await state.clear()
    addon = await get_addon_admin(addon_id)
    await message.answer(
        "Дополнение создано ✅\n\n<b>{0}</b> — {1}".format(
            html.escape(str(addon["name"])),
            format_money(int(addon["price"])),
        ),
        reply_markup=addon_card_keyboard(addon_id, True),
    )


@router.callback_query(F.data.startswith("a:en:"))
async def addon_edit_name_start_callback(
    callback: CallbackQuery,
    state: FSMContext,
) -> None:
    if not await check_admin_callback(callback):
        return
    addon_id = parse_int(callback.data.split(":")[2])
    await state.clear()
    await state.update_data(addon_id=addon_id)
    await state.set_state(AddonStates.edit_name)
    await callback.answer()
    await edit_or_send(
        callback,
        "Введите новое название дополнения.",
        catalog_cancel_keyboard(),
    )


@router.message(AddonStates.edit_name)
async def addon_edit_name_message(message: Message, state: FSMContext) -> None:
    if not await ensure_admin_message(message):
        return
    data = await state.get_data()
    addon_id = int(data["addon_id"])
    try:
        await update_addon_name(addon_id, message.text or "")
    except ValueError as error:
        await message.answer(str(error))
        return
    await state.clear()
    addon = await get_addon_admin(addon_id)
    await message.answer(
        "Название сохранено ✅\n\n<b>{0}</b>".format(
            html.escape(str(addon["name"]))
        ),
        reply_markup=addon_card_keyboard(addon_id, bool(addon["is_active"])),
    )


@router.callback_query(F.data.startswith("a:ep:"))
async def addon_edit_price_start_callback(
    callback: CallbackQuery,
    state: FSMContext,
) -> None:
    if not await check_admin_callback(callback):
        return
    addon_id = parse_int(callback.data.split(":")[2])
    await state.clear()
    await state.update_data(addon_id=addon_id)
    await state.set_state(AddonStates.edit_price)
    await callback.answer()
    await edit_or_send(
        callback,
        "Введите новую цену дополнения.",
        catalog_cancel_keyboard(),
    )


@router.message(AddonStates.edit_price)
async def addon_edit_price_message(message: Message, state: FSMContext) -> None:
    if not await ensure_admin_message(message):
        return
    data = await state.get_data()
    addon_id = int(data["addon_id"])
    try:
        price = parse_price_text(message.text or "")
        await update_addon_price(addon_id, price)
    except ValueError as error:
        await message.answer(str(error))
        return
    await state.clear()
    addon = await get_addon_admin(addon_id)
    await message.answer(
        "Цена сохранена ✅\n\n<b>{0}</b> — {1}".format(
            html.escape(str(addon["name"])),
            format_money(int(addon["price"])),
        ),
        reply_markup=addon_card_keyboard(addon_id, bool(addon["is_active"])),
    )


@router.callback_query(F.data.startswith("a:t:"))
async def addon_toggle_callback(callback: CallbackQuery) -> None:
    if not await check_admin_callback(callback):
        return
    addon_id = parse_int(callback.data.split(":")[2])
    try:
        active = await toggle_addon(addon_id)
    except ValueError as error:
        await callback.answer(str(error), show_alert=True)
        return
    await callback.answer("Дополнение включено" if active else "Дополнение отключено")
    await show_addon_admin(callback, addon_id)

@router.callback_query(F.data == "admin:stats")
async def admin_stats_callback(callback: CallbackQuery) -> None:
    if not await check_admin_callback(callback):
        return

    await callback.answer()
    stats = await get_admin_stats()

    await edit_or_send(
        callback=callback,
        text=(
            "<b>Статистика 📊</b>\n\n"
            "Новых заказов: <b>{0}</b>\n"
            "Всего заказов: <b>{1}</b>\n"
            "Выручка: <b>{2}</b>\n"
            "Средний чек: <b>{3}</b>\n"
            "Активных товаров: <b>{4}</b>"
        ).format(
            stats["new_count"],
            stats["order_count"],
            format_money(stats["revenue"]),
            format_money(stats["average_check"]),
            stats["product_count"],
        ),
        reply_markup=await get_admin_menu_markup(),
    )


# ============================================================
# ДАННЫЕ ИЗ MINI APP
# ============================================================


@router.message(F.web_app_data)
async def web_app_data_handler(message: Message) -> None:
    """Принимает корзину из Mini App и создаёт заказ в SQLite."""
    raw_data = message.web_app_data.data

    try:
        data = json.loads(raw_data)
    except json.JSONDecodeError:
        logging.warning("Mini App передал некорректный JSON: %r", raw_data)
        await message.answer(
            "Не удалось обработать данные заказа. Попробуйте ещё раз."
        )
        return

    if not isinstance(data, dict):
        await message.answer("Mini App передал некорректные данные заказа.")
        return

    try:
        order = await create_order(message.from_user, data)
    except ValueError as error:
        await message.answer(
            "Не удалось оформить заказ: {0}.".format(
                html.escape(str(error))
            )
        )
        return
    except Exception:
        logging.exception("Ошибка создания заказа")
        await message.answer(
            "Произошла ошибка при оформлении заказа. Попробуйте ещё раз."
        )
        return

    await message.answer(
        text=(
            "<b>Заказ оформлен ✅</b>\n\n"
            "Номер: <b>{0}</b>\n"
            "Товары: {1}\n"
            "Доставка: {2}\n"
            "Итого: <b>{3}</b>\n\n"
            "Статус заказа: <b>Новый</b>."
        ).format(
            html.escape(order["order_number"]),
            format_money(order["subtotal"]),
            format_money(order["delivery_price"]),
            format_money(order["total"]),
        ),
        reply_markup=main_menu_keyboard(
            is_admin=user_is_admin(message.from_user.id)
        ),
    )

    safe_name = html.escape(message.from_user.full_name)
    admin_text = (
        "<b>Новый заказ 🆕</b>\n\n"
        "Номер: <b>{0}</b>\n"
        "Клиент: {1}\n"
        "Telegram ID: <code>{2}</code>\n"
        "Сумма: <b>{3}</b>"
    ).format(
        html.escape(order["order_number"]),
        safe_name,
        message.from_user.id,
        format_money(order["total"]),
    )

    for admin_id in ADMIN_IDS:
        try:
            await message.bot.send_message(
                chat_id=admin_id,
                text=admin_text,
                reply_markup=admin_order_card_keyboard(
                    order_id=int(order["order_id"]),
                    current_status="new",
                    filter_key="new",
                    page=0,
                    telegram_id=message.from_user.id,
                ),
            )
        except Exception:
            logging.exception(
                "Не удалось отправить заказ администратору %s",
                admin_id,
            )


@router.message()
async def fallback_handler(message: Message) -> None:
    await upsert_user(message.from_user)

    await message.answer(
        text=(
            "Я пока работаю через кнопки ниже.\n"
            "Откройте магазин или выберите нужный раздел."
        ),
        reply_markup=main_menu_keyboard(
            is_admin=user_is_admin(message.from_user.id)
        ),
    )




# ============================================================
# API И TELEGRAM MINI APP
# ============================================================


def public_image_url(image_value: Optional[str]) -> Optional[str]:
    """Преобразует сохранённое изображение в URL для Mini App."""
    if not image_value:
        return None
    value = str(image_value)
    if value.startswith("telegram:"):
        file_id = value.split(":", 1)[1]
        return "/api/media?file_id={0}".format(quote(file_id, safe=""))
    return value


def get_public_categories_sync() -> List[Dict[str, Any]]:
    """Возвращает активные категории с количеством товаров."""
    with get_db_connection() as connection:
        rows = connection.execute(
            """
            SELECT
                categories.id,
                categories.name,
                categories.slug,
                categories.position,
                COUNT(products.id) AS products_count
            FROM categories
            LEFT JOIN products
              ON products.category_id = categories.id
             AND products.is_active = 1
            WHERE categories.is_active = 1
            GROUP BY categories.id
            ORDER BY categories.position ASC, categories.id ASC
            """
        ).fetchall()

    return [
        {
            "id": int(row["id"]),
            "name": row["name"],
            "slug": row["slug"],
            "position": int(row["position"]),
            "products_count": int(row["products_count"]),
        }
        for row in rows
    ]


def _public_product_from_rows(
    product: sqlite3.Row,
    variants: List[sqlite3.Row],
    addons: List[sqlite3.Row],
    images: List[sqlite3.Row],
) -> Dict[str, Any]:
    variant_items = [
        {
            "id": int(row["id"]),
            "name": row["name"],
            "price": int(row["price"]),
            "is_default": bool(row["is_default"]),
        }
        for row in variants
    ]
    addon_items = [
        {
            "id": int(row["id"]),
            "name": row["name"],
            "price": int(row["price"]),
            "image_url": public_image_url(row["image_url"]),
        }
        for row in addons
    ]
    image_items = [
        public_image_url(row["image_url"])
        for row in images
        if public_image_url(row["image_url"])
    ]
    if not image_items:
        fallback_image = public_image_url(product["image_url"])
        if fallback_image:
            image_items = [fallback_image]

    min_price = min(
        [item["price"] for item in variant_items]
        or [int(product["base_price"])]
    )
    return {
        "id": int(product["id"]),
        "name": product["name"],
        "slug": product["slug"],
        "description": product["description"],
        "composition": product["composition"],
        "badge": product["badge"],
        "created_at": product["created_at"],
        "is_featured": product["featured_position"] is not None,
        "featured_position": (
            int(product["featured_position"])
            if product["featured_position"] is not None
            else None
        ),
        "image_url": image_items[0] if image_items else None,
        "images": image_items,
        "base_price": int(product["base_price"]),
        "min_price": min_price,
        "category": {
            "id": int(product["category_id"])
            if product["category_id"] is not None
            else None,
            "name": product["category_name"],
            "slug": product["category_slug"],
        },
        "variants": variant_items,
        "addons": addon_items,
    }


def get_public_products_sync(
    category_id: Optional[int] = None,
) -> List[Dict[str, Any]]:
    """Возвращает опубликованные товары, размеры и дополнения."""
    query = """
        SELECT
            products.id,
            products.category_id,
            products.name,
            products.slug,
            products.description,
            products.composition,
            products.base_price,
            products.image_url,
            products.badge,
            products.created_at,
            featured_products.position AS featured_position,
            categories.name AS category_name,
            categories.slug AS category_slug
        FROM products
        LEFT JOIN categories ON categories.id = products.category_id
        LEFT JOIN featured_products
            ON featured_products.product_id = products.id
        WHERE products.is_active = 1
          AND (categories.id IS NULL OR categories.is_active = 1)
    """
    params: List[Any] = []
    if category_id is not None:
        query += " AND products.category_id = ?"
        params.append(category_id)
    query += (
        " ORDER BY "
        "CASE WHEN featured_products.position IS NULL THEN 1 ELSE 0 END, "
        "featured_products.position ASC, products.id DESC"
    )

    with get_db_connection() as connection:
        products = connection.execute(query, params).fetchall()
        result: List[Dict[str, Any]] = []
        for product in products:
            variants = connection.execute(
                """
                SELECT id, name, price, is_default
                FROM product_variants
                WHERE product_id = ? AND is_active = 1
                ORDER BY is_default DESC, id ASC
                """,
                (int(product["id"]),),
            ).fetchall()
            addons = connection.execute(
                """
                SELECT addons.id, addons.name, addons.price, addons.image_url
                FROM addons
                JOIN product_addons
                  ON product_addons.addon_id = addons.id
                WHERE product_addons.product_id = ?
                  AND addons.is_active = 1
                ORDER BY addons.id ASC
                """,
                (int(product["id"]),),
            ).fetchall()
            images = connection.execute(
                """
                SELECT image_url, position, is_primary
                FROM product_images
                WHERE product_id = ?
                ORDER BY is_primary DESC, position ASC, id ASC
                """,
                (int(product["id"]),),
            ).fetchall()
            result.append(
                _public_product_from_rows(
                    product,
                    variants,
                    addons,
                    images,
                )
            )
    return result


def get_public_product_sync(product_id: int) -> Optional[Dict[str, Any]]:
    """Возвращает один опубликованный товар."""
    with get_db_connection() as connection:
        product = connection.execute(
            """
            SELECT
                products.id,
                products.category_id,
                products.name,
                products.slug,
                products.description,
                products.composition,
                products.base_price,
                products.image_url,
                products.badge,
                products.created_at,
                featured_products.position AS featured_position,
                categories.name AS category_name,
                categories.slug AS category_slug
            FROM products
            LEFT JOIN categories ON categories.id = products.category_id
            LEFT JOIN featured_products
                ON featured_products.product_id = products.id
            WHERE products.id = ?
              AND products.is_active = 1
              AND (categories.id IS NULL OR categories.is_active = 1)
            """,
            (product_id,),
        ).fetchone()
        if product is None:
            return None
        variants = connection.execute(
            """
            SELECT id, name, price, is_default
            FROM product_variants
            WHERE product_id = ? AND is_active = 1
            ORDER BY is_default DESC, id ASC
            """,
            (product_id,),
        ).fetchall()
        addons = connection.execute(
            """
            SELECT addons.id, addons.name, addons.price, addons.image_url
            FROM addons
            JOIN product_addons
              ON product_addons.addon_id = addons.id
            WHERE product_addons.product_id = ?
              AND addons.is_active = 1
            ORDER BY addons.id ASC
            """,
            (product_id,),
        ).fetchall()
        images = connection.execute(
            """
            SELECT image_url, position, is_primary
            FROM product_images
            WHERE product_id = ?
            ORDER BY is_primary DESC, position ASC, id ASC
            """,
            (product_id,),
        ).fetchall()
    return _public_product_from_rows(
        product,
        variants,
        addons,
        images,
    )


def get_public_addons_sync() -> List[Dict[str, Any]]:
    with get_db_connection() as connection:
        rows = connection.execute(
            """
            SELECT id, name, price, image_url
            FROM addons
            WHERE is_active = 1
            ORDER BY id ASC
            """
        ).fetchall()
    return [
        {
            "id": int(row["id"]),
            "name": row["name"],
            "price": int(row["price"]),
            "image_url": public_image_url(row["image_url"]),
        }
        for row in rows
    ]


def get_public_orders_sync(telegram_id: int) -> List[Dict[str, Any]]:
    """Возвращает историю заказов авторизованного пользователя."""
    with get_db_connection() as connection:
        rows = connection.execute(
            """
            SELECT
                orders.id,
                orders.order_number,
                orders.total,
                orders.status,
                orders.delivery_type,
                orders.delivery_date,
                orders.delivery_interval,
                orders.created_at,
                COUNT(order_items.id) AS items_count
            FROM orders
            JOIN users ON users.id = orders.user_id
            LEFT JOIN order_items ON order_items.order_id = orders.id
            WHERE users.telegram_id = ?
            GROUP BY orders.id
            ORDER BY orders.created_at DESC, orders.id DESC
            LIMIT 50
            """,
            (telegram_id,),
        ).fetchall()
    return [
        {
            "id": int(row["id"]),
            "order_number": row["order_number"],
            "total": int(row["total"]),
            "status": row["status"],
            "status_label": ORDER_STATUS_LABELS.get(
                row["status"], row["status"]
            ),
            "delivery_type": row["delivery_type"],
            "delivery_date": row["delivery_date"],
            "delivery_interval": row["delivery_interval"],
            "items_count": int(row["items_count"]),
            "created_at": row["created_at"],
        }
        for row in rows
    ]


async def get_public_categories() -> List[Dict[str, Any]]:
    return await asyncio.to_thread(get_public_categories_sync)


async def get_public_products(
    category_id: Optional[int] = None,
) -> List[Dict[str, Any]]:
    return await asyncio.to_thread(get_public_products_sync, category_id)


async def get_public_product(product_id: int) -> Optional[Dict[str, Any]]:
    return await asyncio.to_thread(get_public_product_sync, product_id)


async def get_public_addons() -> List[Dict[str, Any]]:
    return await asyncio.to_thread(get_public_addons_sync)


async def get_public_orders(telegram_id: int) -> List[Dict[str, Any]]:
    return await asyncio.to_thread(get_public_orders_sync, telegram_id)


def get_admin_mailing_recipients_sync(audience: str) -> List[int]:
    """Возвращает Telegram ID клиентов для рассылки."""
    normalized_audience = (audience or "Все клиенты").strip().lower()
    with get_db_connection() as connection:
        rows = connection.execute(
            """
            SELECT
                users.telegram_id,
                COUNT(orders.id) AS orders_count
            FROM users
            LEFT JOIN orders ON orders.user_id = users.id
            GROUP BY users.id
            ORDER BY users.id ASC
            """
        ).fetchall()

    recipients: List[int] = []
    for row in rows:
        telegram_id = int(row["telegram_id"])
        if telegram_id in ADMIN_IDS:
            continue

        orders_count = int(row["orders_count"] or 0)
        if normalized_audience == "клиенты с заказами" and orders_count <= 0:
            continue
        if normalized_audience == "постоянные клиенты" and orders_count < 2:
            continue
        if normalized_audience == "новые клиенты" and orders_count != 0:
            continue

        recipients.append(telegram_id)

    return recipients


async def get_admin_mailing_recipients(audience: str) -> List[int]:
    return await asyncio.to_thread(get_admin_mailing_recipients_sync, audience)


def get_admin_mailing_media_kind(content_type: str, filename: str) -> str:
    """Определяет, является ли вложение фото или видео."""
    normalized_type = (content_type or "").lower()
    normalized_name = (filename or "").lower()
    if normalized_type.startswith("image/") or normalized_name.endswith(
        (".jpg", ".jpeg", ".png", ".webp", ".gif")
    ):
        return "image"
    if normalized_type.startswith("video/") or normalized_name.endswith(
        (".mp4", ".mov", ".webm", ".m4v")
    ):
        return "video"
    return ""


def format_admin_mailing_text(title: str, message: str) -> str:
    parts: List[str] = []
    normalized_title = title.strip()
    normalized_message = message.strip()
    if normalized_title:
        parts.append("<b>{0}</b>".format(html.escape(normalized_title)))
    if normalized_message:
        parts.append(html.escape(normalized_message))
    return "\n\n".join(parts)


async def send_admin_mailing_item(
    bot: Bot,
    chat_id: int,
    text: str,
    media: Optional[Dict[str, Any]],
) -> None:
    """Отправляет одно сообщение рассылки конкретному клиенту."""
    if not media:
        await bot.send_message(chat_id=chat_id, text=text)
        return

    input_file = BufferedInputFile(
        media["data"],
        filename=media["filename"],
    )
    caption = text if text and len(text) <= 900 else None

    if media["kind"] == "image":
        await bot.send_photo(
            chat_id=chat_id,
            photo=input_file,
            caption=caption,
        )
    elif media["kind"] == "video":
        await bot.send_video(
            chat_id=chat_id,
            video=input_file,
            caption=caption,
        )
    else:
        await bot.send_document(
            chat_id=chat_id,
            document=input_file,
            caption=caption,
        )

    if text and caption is None:
        await bot.send_message(chat_id=chat_id, text=text)


def validate_telegram_init_data(
    init_data: str,
) -> Dict[str, Any]:
    """Проверяет подпись и срок действия Telegram.WebApp.initData."""
    if not init_data:
        raise ValueError("Mini App не передало данные авторизации Telegram")

    parsed = dict(parse_qsl(init_data, keep_blank_values=True))
    received_hash = parsed.pop("hash", None)
    if not received_hash:
        raise ValueError("В initData отсутствует hash")

    data_check_string = "\n".join(
        "{0}={1}".format(key, parsed[key])
        for key in sorted(parsed)
    )
    secret_key = hmac.new(
        b"WebAppData",
        BOT_TOKEN.encode("utf-8"),
        hashlib.sha256,
    ).digest()
    calculated_hash = hmac.new(
        secret_key,
        data_check_string.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()

    if not hmac.compare_digest(calculated_hash, received_hash):
        raise ValueError("Подпись initData не прошла проверку")

    try:
        auth_date = int(parsed.get("auth_date", "0"))
    except ValueError as error:
        raise ValueError("Некорректный auth_date") from error

    current_time = int(time.time())
    if auth_date <= 0 or current_time - auth_date > INIT_DATA_MAX_AGE:
        raise ValueError("Срок действия авторизации Telegram истёк")
    if auth_date > current_time + 60:
        raise ValueError("Некорректное время авторизации Telegram")

    raw_user = parsed.get("user")
    if not raw_user:
        raise ValueError("Telegram не передал пользователя")
    try:
        user_data = json.loads(raw_user)
    except json.JSONDecodeError as error:
        raise ValueError("Некорректные данные пользователя") from error
    if not isinstance(user_data, dict) or not user_data.get("id"):
        raise ValueError("Некорректный пользователь Telegram")

    return {
        "query": parsed,
        "user": user_data,
    }


def telegram_user_from_init_data(auth: Dict[str, Any]) -> User:
    user = auth["user"]
    return User(
        id=int(user["id"]),
        is_bot=False,
        first_name=str(user.get("first_name") or "Пользователь"),
        last_name=user.get("last_name"),
        username=user.get("username"),
        language_code=user.get("language_code"),
    )


def request_init_data(request: web.Request, payload: Any = None) -> str:
    value = request.headers.get("X-Telegram-Init-Data", "")
    if value:
        return value
    if isinstance(payload, dict):
        raw = payload.get("init_data")
        if isinstance(raw, str):
            return raw
    return ""


def api_json(
    data: Any,
    status: int = 200,
) -> web.Response:
    return web.json_response(
        data,
        status=status,
        headers={
            "Cache-Control": "no-store",
            "X-Content-Type-Options": "nosniff",
        },
        dumps=lambda value: json.dumps(
            value,
            ensure_ascii=False,
            separators=(",", ":"),
        ),
    )


async def api_health_handler(request: web.Request) -> web.Response:
    return api_json({"ok": True, "service": "BloomBox API"})


async def api_session_handler(request: web.Request) -> web.Response:
    """Возвращает проверенную роль пользователя Mini App."""
    try:
        auth = validate_telegram_init_data(request_init_data(request))
    except ValueError as error:
        return api_json({"error": str(error)}, 401)

    user = auth["user"]
    telegram_id = int(user["id"])
    is_admin = user_is_admin(telegram_id)

    admin_data: Optional[Dict[str, Any]] = None
    if is_admin:
        admin_data = {
            "stats": await get_admin_stats(),
        }

    return api_json(
        {
            "authenticated": True,
            "is_admin": is_admin,
            "user": {
                "id": telegram_id,
                "first_name": str(user.get("first_name") or ""),
                "last_name": str(user.get("last_name") or ""),
                "username": user.get("username"),
            },
            "admin": admin_data,
        }
    )


async def api_categories_handler(request: web.Request) -> web.Response:
    return api_json(await get_public_categories())


async def api_settings_handler(request: web.Request) -> web.Response:
    return api_json(await asyncio.to_thread(get_public_settings_sync))


async def api_admin_pickup_address_handler(request: web.Request) -> web.Response:
    try:
        payload = await request.json()
    except (json.JSONDecodeError, web.HTTPBadRequest):
        return api_json({"error": "Некорректный JSON"}, 400)
    if not isinstance(payload, dict):
        return api_json({"error": "Некорректные данные настроек"}, 400)

    try:
        auth = validate_telegram_init_data(
            request_init_data(request, payload)
        )
    except ValueError as error:
        return api_json({"error": str(error)}, 401)

    admin_id = int(auth["user"]["id"])
    if not user_is_admin(admin_id):
        return api_json({"error": "Доступ запрещён"}, 403)

    address = str(payload.get("pickup_address") or "").strip()
    if not address:
        return api_json({"error": "Укажите адрес самовывоза"}, 400)
    if len(address) > 300:
        return api_json({"error": "Адрес самовывоза слишком длинный"}, 400)

    saved_address = await asyncio.to_thread(
        set_setting_text_sync,
        "pickup_address",
        address,
    )
    return api_json({"ok": True, "pickup_address": saved_address})


async def api_products_handler(request: web.Request) -> web.Response:
    category_id: Optional[int] = None
    raw_category = request.query.get("category_id")
    if raw_category:
        try:
            category_id = int(raw_category)
        except ValueError:
            return api_json({"error": "Некорректная категория"}, 400)
    return api_json(await get_public_products(category_id))


async def api_product_handler(request: web.Request) -> web.Response:
    try:
        product_id = int(request.match_info["product_id"])
    except (KeyError, ValueError):
        return api_json({"error": "Некорректный товар"}, 400)
    product = await get_public_product(product_id)
    if product is None:
        return api_json({"error": "Товар не найден"}, 404)
    return api_json(product)


async def api_addons_handler(request: web.Request) -> web.Response:
    return api_json(await get_public_addons())


async def api_orders_handler(request: web.Request) -> web.Response:
    try:
        auth = validate_telegram_init_data(request_init_data(request))
    except ValueError as error:
        return api_json({"error": str(error)}, 401)

    telegram_id = int(auth["user"]["id"])
    path_id = request.match_info.get("telegram_id")
    if path_id is not None:
        try:
            if int(path_id) != telegram_id:
                return api_json({"error": "Доступ запрещён"}, 403)
        except ValueError:
            return api_json({"error": "Некорректный Telegram ID"}, 400)
    return api_json(await get_public_orders(telegram_id))


async def api_create_order_handler(request: web.Request) -> web.Response:
    try:
        payload = await request.json()
    except (json.JSONDecodeError, web.HTTPBadRequest):
        return api_json({"error": "Некорректный JSON"}, 400)
    if not isinstance(payload, dict):
        return api_json({"error": "Некорректные данные заказа"}, 400)

    try:
        auth = validate_telegram_init_data(
            request_init_data(request, payload)
        )
    except ValueError as error:
        return api_json({"error": str(error)}, 401)

    try:
        telegram_user = telegram_user_from_init_data(auth)
        order = await create_order(telegram_user, payload)
    except ValueError as error:
        return api_json({"error": str(error)}, 400)
    except Exception:
        logging.exception("Ошибка API при создании заказа")
        return api_json({"error": "Не удалось создать заказ"}, 500)

    bot: Bot = request.app["bot"]
    try:
        await bot.send_message(
            chat_id=telegram_user.id,
            text=(
                "<b>Заказ оформлен ✅</b>\n\n"
                "Номер: <b>{0}</b>\n"
                "Итого: <b>{1}</b>\n\n"
                "Статус: <b>Новый</b>."
            ).format(
                html.escape(order["order_number"]),
                format_money(order["total"]),
            ),
            reply_markup=main_menu_keyboard(
                is_admin=user_is_admin(telegram_user.id)
            ),
        )
    except Exception:
        logging.exception("Не удалось подтвердить заказ клиенту")

    admin_text = (
        "<b>Новый заказ из Mini App 🆕</b>\n\n"
        "Номер: <b>{0}</b>\n"
        "Клиент: {1}\n"
        "Telegram ID: <code>{2}</code>\n"
        "Сумма: <b>{3}</b>"
    ).format(
        html.escape(order["order_number"]),
        html.escape(telegram_user.full_name),
        telegram_user.id,
        format_money(order["total"]),
    )
    for admin_id in ADMIN_IDS:
        try:
            await bot.send_message(
                chat_id=admin_id,
                text=admin_text,
                reply_markup=admin_order_card_keyboard(
                    order_id=int(order["order_id"]),
                    current_status="new",
                    filter_key="new",
                    page=0,
                    telegram_id=telegram_user.id,
                ),
            )
        except Exception:
            logging.exception(
                "Не удалось уведомить администратора %s", admin_id
            )

    return api_json({"ok": True, "order": order}, 201)


async def read_admin_mailing_request(
    request: web.Request,
) -> Tuple[Dict[str, str], Optional[Dict[str, Any]]]:
    """Читает данные рассылки из JSON или multipart/form-data."""
    fields: Dict[str, str] = {}
    media: Optional[Dict[str, Any]] = None

    if request.content_type.startswith("multipart/"):
        reader = await request.multipart()
        async for part in reader:
            if part.name == "media" and part.filename:
                content = await part.read(decode=False)
                if len(content) > MAX_MAILING_MEDIA_BYTES:
                    raise ValueError("Файл слишком большой для рассылки")
                filename = Path(part.filename).name or "mailing-media"
                content_type = part.headers.get("Content-Type", "")
                if not content_type:
                    content_type = mimetypes.guess_type(filename)[0] or ""
                kind = get_admin_mailing_media_kind(content_type, filename)
                if not kind:
                    raise ValueError("Можно прикрепить только фото или видео")
                media = {
                    "filename": filename,
                    "content_type": content_type,
                    "kind": kind,
                    "data": content,
                    "size": len(content),
                }
                continue

            if part.name:
                fields[part.name] = (await part.text()).strip()
        return fields, media

    try:
        payload = await request.json()
    except (json.JSONDecodeError, web.HTTPBadRequest):
        raise ValueError("Некорректные данные рассылки")
    if not isinstance(payload, dict):
        raise ValueError("Некорректные данные рассылки")
    for key, value in payload.items():
        fields[str(key)] = "" if value is None else str(value).strip()
    return fields, media


async def api_admin_send_mailing_handler(request: web.Request) -> web.Response:
    try:
        fields, media = await read_admin_mailing_request(request)
    except ValueError as error:
        return api_json({"error": str(error)}, 400)

    try:
        auth = validate_telegram_init_data(
            request_init_data(request, fields)
        )
    except ValueError as error:
        return api_json({"error": str(error)}, 401)

    admin_id = int(auth["user"]["id"])
    if not user_is_admin(admin_id):
        return api_json({"error": "Доступ запрещён"}, 403)

    title = fields.get("title", "").strip()
    message = fields.get("message", "").strip()
    audience = fields.get("audience", "Все клиенты").strip() or "Все клиенты"
    text = format_admin_mailing_text(title, message)
    if not text and not media:
        return api_json({"error": "Добавьте текст, фото или видео"}, 400)

    recipients = await get_admin_mailing_recipients(audience)
    if not recipients:
        return api_json({"error": "Для выбранной аудитории нет получателей"}, 400)

    bot: Bot = request.app["bot"]
    sent_count = 0
    failed_count = 0
    for telegram_id in recipients:
        try:
            await send_admin_mailing_item(
                bot=bot,
                chat_id=telegram_id,
                text=text,
                media=media,
            )
            sent_count += 1
            await asyncio.sleep(0.05)
        except TelegramBadRequest:
            failed_count += 1
            logging.exception(
                "Не удалось отправить рассылку клиенту %s",
                telegram_id,
            )
        except Exception:
            failed_count += 1
            logging.exception(
                "Ошибка рассылки клиенту %s",
                telegram_id,
            )

    return api_json(
        {
            "ok": True,
            "sent_count": sent_count,
            "failed_count": failed_count,
            "total_recipients": len(recipients),
        }
    )


async def api_media_handler(request: web.Request) -> web.Response:
    file_id = request.query.get("file_id", "").strip()
    if not file_id or len(file_id) > 512:
        raise web.HTTPBadRequest(text="Некорректный file_id")
    bot: Bot = request.app["bot"]
    try:
        telegram_file = await bot.get_file(file_id)
        if not telegram_file.file_path:
            raise RuntimeError("Telegram не вернул путь к файлу")
        stream = await bot.download_file(telegram_file.file_path)
        if stream is None:
            raise RuntimeError("Telegram не вернул файл")
        content = stream.getvalue()
        content_type = mimetypes.guess_type(
            telegram_file.file_path
        )[0] or "application/octet-stream"
        return web.Response(
            body=content,
            content_type=content_type,
            headers={
                "Cache-Control": "public, max-age=3600",
                "X-Content-Type-Options": "nosniff",
            },
        )
    except web.HTTPException:
        raise
    except Exception:
        logging.exception("Не удалось отдать Telegram-файл")
        raise web.HTTPNotFound(text="Изображение не найдено")


def webapp_file(name: str) -> Path:
    path = (WEBAPP_DIR / name).resolve()
    if WEBAPP_DIR.resolve() not in path.parents:
        raise web.HTTPForbidden()
    if not path.is_file():
        raise web.HTTPNotFound()
    return path


async def webapp_index_handler(request: web.Request) -> web.StreamResponse:
    return web.FileResponse(webapp_file("index.html"))


async def webapp_asset_handler(request: web.Request) -> web.StreamResponse:
    name = request.match_info["name"]
    if name not in {"styles.css", "script.js"}:
        raise web.HTTPNotFound()
    response = web.FileResponse(webapp_file(name))
    response.headers["Cache-Control"] = "no-cache"
    return response


async def webapp_image_handler(request: web.Request) -> web.StreamResponse:
    name = request.match_info["name"]
    suffix = Path(name).suffix.lower()
    if Path(name).name != name or suffix not in {
        ".webp",
        ".png",
        ".jpg",
        ".jpeg",
    }:
        raise web.HTTPNotFound()
    response = web.FileResponse(webapp_file("images/{0}".format(name)))
    response.headers["Cache-Control"] = "public, max-age=86400"
    response.headers["X-Content-Type-Options"] = "nosniff"
    return response


async def api_admin_create_product_handler(request: web.Request) -> web.Response:
    data = await request.json()
    product_id = await create_product_admin(data)
    return web.json_response({"id": product_id})


async def api_admin_delete_product_handler(request: web.Request) -> web.Response:
    await delete_product(int(request.match_info["product_id"]))
    return web.json_response({"ok": True})


async def api_admin_update_product_handler(request: web.Request) -> web.Response:
    product_id = int(request.match_info["product_id"])
    data = await request.json()
    if "name" in data:
        await update_product_text(product_id, "name", data["name"])
    if "description" in data:
        await update_product_text(product_id, "description", data["description"])
    if "composition" in data:
        await update_product_text(product_id, "composition", data["composition"])
    if "image_url" in data:
        await update_product_text(product_id, "image_url", data["image_url"])
    if "prices" in data:
        await update_product_prices(product_id, data["prices"])
    return web.json_response({"ok": True})


def create_web_application(bot: Bot) -> web.Application:
    app = web.Application(client_max_size=32 * 1024 * 1024)
    app["bot"] = bot
    app.router.add_get("/api/health", api_health_handler)
    app.router.add_get("/api/session", api_session_handler)
    app.router.add_get("/api/categories", api_categories_handler)
    app.router.add_get("/api/settings", api_settings_handler)
    app.router.add_get("/api/products", api_products_handler)
    app.router.add_get(
        "/api/products/{product_id:\\d+}", api_product_handler
    )
    app.router.add_get("/api/addons", api_addons_handler)
    app.router.add_get("/api/orders", api_orders_handler)
    app.router.add_get(
        "/api/orders/{telegram_id:\\d+}", api_orders_handler
    )
    app.router.add_post("/api/orders", api_create_order_handler)
    app.router.add_post("/api/admin/mailings/send", api_admin_send_mailing_handler)
    app.router.add_put("/api/admin/settings/pickup-address", api_admin_pickup_address_handler)
    app.router.add_post("/api/admin/products", api_admin_create_product_handler)
    app.router.add_put("/api/admin/products/{product_id:\\d+}", api_admin_update_product_handler)
    app.router.add_delete("/api/admin/products/{product_id:\\d+}", api_admin_delete_product_handler)
    app.router.add_get("/api/media", api_media_handler)
    app.router.add_get("/", webapp_index_handler)
    app.router.add_get("/index.html", webapp_index_handler)
    app.router.add_get("/{name:styles\\.css|script\\.js}", webapp_asset_handler)
    app.router.add_get("/images/{name}", webapp_image_handler)
    return app


async def start_web_server(bot: Bot) -> web.AppRunner:
    if not WEBAPP_DIR.is_dir():
        raise RuntimeError(
            "Папка Mini App не найдена: {0}".format(WEBAPP_DIR)
        )
    runner = web.AppRunner(create_web_application(bot))
    await runner.setup()
    site = web.TCPSite(runner, host=WEB_HOST, port=WEB_PORT)
    await site.start()
    logging.info(
        "BloomBox Mini App и API запущены: http://%s:%s",
        WEB_HOST,
        WEB_PORT,
    )
    return runner


# ============================================================
# ЗАПУСК
# ============================================================


async def set_bot_interface(bot: Bot) -> None:
    await bot.set_my_commands(
        commands=[
            BotCommand(command="start", description="Главное меню"),
            BotCommand(command="help", description="Как пользоваться ботом"),
        ]
    )

    try:
        await bot.set_chat_menu_button(
            menu_button=MenuButtonWebApp(
                text="Открыть BloomBox",
                web_app=WebAppInfo(url=MINI_APP_URL),
            )
        )
    except Exception:
        logging.exception(
            "Не удалось установить кнопку Mini App. "
            "Проверьте MINI_APP_URL в config.py."
        )


async def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        stream=sys.stdout,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )

    if not BOT_TOKEN or BOT_TOKEN == "ВСТАВЬ_СЮДА_ТОКЕН":
        raise RuntimeError(
            "В config.py нужно заменить BOT_TOKEN на токен от @BotFather"
        )

    await initialize_database()
    logging.info("База данных готова: %s", DATABASE_PATH.resolve())

    bot = Bot(
        token=BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )

    dispatcher = Dispatcher()
    dispatcher.include_router(router)

    await set_bot_interface(bot)
    web_runner: Optional[web.AppRunner] = None

    try:
        web_runner = await start_web_server(bot)
        await dispatcher.start_polling(
            bot,
            allowed_updates=dispatcher.resolve_used_update_types(),
        )
    finally:
        if web_runner is not None:
            await web_runner.cleanup()
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
