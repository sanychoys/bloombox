from typing import Any, Dict, List, Optional, Sequence

import config
from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    WebAppInfo,
)


MINI_APP_URL: str = getattr(config, "MINI_APP_URL", "https://example.com")
SUPPORT_URL: str = getattr(
    config,
    "SUPPORT_URL",
    "https://t.me/telegram",
)


STATUS_ACTIONS = {
    "new": [
        ("✅ Принять", "accepted"),
        ("❌ Отменить", "cancelled"),
    ],
    "accepted": [
        ("🌷 Начать сборку", "assembling"),
        ("❌ Отменить", "cancelled"),
    ],
    "assembling": [
        ("🚚 Передать курьеру", "courier"),
        ("❌ Отменить", "cancelled"),
    ],
    "courier": [
        ("🎉 Отметить доставленным", "delivered"),
        ("❌ Отменить", "cancelled"),
    ],
    "delivered": [],
    "cancelled": [],
}


def main_menu_keyboard(is_admin: bool = False) -> InlineKeyboardMarkup:
    """Главное клиентское меню BloomBox."""
    rows = [
        [
            InlineKeyboardButton(
                text="🌷 Открыть магазин",
                web_app=WebAppInfo(url=MINI_APP_URL),
            )
        ],
        [
            InlineKeyboardButton(
                text="📦 Мои заказы",
                callback_data="menu:orders",
            ),
            InlineKeyboardButton(
                text="🚚 Доставка",
                callback_data="menu:delivery",
            ),
        ],
        [
            InlineKeyboardButton(
                text="💬 Поддержка",
                url=SUPPORT_URL,
            )
        ],
    ]

    if is_admin:
        rows.append(
            [
                InlineKeyboardButton(
                    text="⚙️ Админ-панель",
                    callback_data="menu:admin",
                )
            ]
        )

    return InlineKeyboardMarkup(inline_keyboard=rows)


def back_to_main_keyboard(
    is_admin: bool = False,
) -> InlineKeyboardMarkup:
    """Кнопка возврата в главное меню."""
    rows = [
        [
            InlineKeyboardButton(
                text="⬅️ Главное меню",
                callback_data="menu:main",
            )
        ]
    ]

    if is_admin:
        rows.append(
            [
                InlineKeyboardButton(
                    text="⚙️ Админ-панель",
                    callback_data="menu:admin",
                )
            ]
        )

    return InlineKeyboardMarkup(inline_keyboard=rows)


def admin_menu_keyboard(new_count: int = 0) -> InlineKeyboardMarkup:
    """Главное меню владельца магазина."""
    new_label = "🆕 Новые заказы"
    if new_count > 0:
        new_label += " ({0})".format(new_count)

    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=new_label,
                    callback_data="admin:list:new:0",
                ),
                InlineKeyboardButton(
                    text="📋 Все заказы",
                    callback_data="admin:filters",
                ),
            ],
            [
                InlineKeyboardButton(
                    text="🌷 Товары",
                    callback_data="admin:products",
                ),
                InlineKeyboardButton(
                    text="📊 Статистика",
                    callback_data="admin:stats",
                ),
            ],
            [
                InlineKeyboardButton(
                    text="⬅️ Клиентское меню",
                    callback_data="menu:main",
                )
            ],
        ]
    )


def admin_order_filters_keyboard(
    counts: Dict[str, int],
) -> InlineKeyboardMarkup:
    """Фильтры списка заказов администратора."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🆕 Новые ({0})".format(counts.get("new", 0)),
                    callback_data="admin:list:new:0",
                ),
                InlineKeyboardButton(
                    text="🌷 В работе ({0})".format(
                        counts.get("active", 0)
                    ),
                    callback_data="admin:list:active:0",
                ),
            ],
            [
                InlineKeyboardButton(
                    text="🚚 У курьера ({0})".format(
                        counts.get("courier", 0)
                    ),
                    callback_data="admin:list:courier:0",
                ),
                InlineKeyboardButton(
                    text="🎉 Завершённые ({0})".format(
                        counts.get("completed", 0)
                    ),
                    callback_data="admin:list:completed:0",
                ),
            ],
            [
                InlineKeyboardButton(
                    text="❌ Отменённые ({0})".format(
                        counts.get("cancelled", 0)
                    ),
                    callback_data="admin:list:cancelled:0",
                ),
                InlineKeyboardButton(
                    text="📋 Все ({0})".format(counts.get("all", 0)),
                    callback_data="admin:list:all:0",
                ),
            ],
            [
                InlineKeyboardButton(
                    text="⬅️ Админ-панель",
                    callback_data="menu:admin",
                )
            ],
        ]
    )


def admin_orders_list_keyboard(
    orders: Sequence[Any],
    filter_key: str,
    page: int,
    total_pages: int,
) -> InlineKeyboardMarkup:
    """Кнопки заказов и постраничная навигация."""
    rows: List[List[InlineKeyboardButton]] = []

    for order in orders:
        order_id = int(order["id"])
        order_number = str(order["order_number"] or "Без номера")
        customer_name = str(order["customer_name"] or "Клиент")
        if len(customer_name) > 18:
            customer_name = customer_name[:17] + "…"

        rows.append(
            [
                InlineKeyboardButton(
                    text="{0} · {1}".format(
                        order_number,
                        customer_name,
                    ),
                    callback_data="admin:order:{0}:{1}:{2}".format(
                        order_id,
                        filter_key,
                        page,
                    ),
                )
            ]
        )

    pagination: List[InlineKeyboardButton] = []
    if page > 0:
        pagination.append(
            InlineKeyboardButton(
                text="⬅️",
                callback_data="admin:list:{0}:{1}".format(
                    filter_key,
                    page - 1,
                ),
            )
        )

    if total_pages > 1:
        pagination.append(
            InlineKeyboardButton(
                text="{0}/{1}".format(page + 1, total_pages),
                callback_data="noop",
            )
        )

    if page + 1 < total_pages:
        pagination.append(
            InlineKeyboardButton(
                text="➡️",
                callback_data="admin:list:{0}:{1}".format(
                    filter_key,
                    page + 1,
                ),
            )
        )

    if pagination:
        rows.append(pagination)

    rows.extend(
        [
            [
                InlineKeyboardButton(
                    text="🔎 Фильтры",
                    callback_data="admin:filters",
                )
            ],
            [
                InlineKeyboardButton(
                    text="⬅️ Админ-панель",
                    callback_data="menu:admin",
                )
            ],
        ]
    )

    return InlineKeyboardMarkup(inline_keyboard=rows)


def admin_order_card_keyboard(
    order_id: int,
    current_status: str,
    filter_key: str,
    page: int,
    telegram_id: Optional[int] = None,
    previous_order_id: Optional[int] = None,
    next_order_id: Optional[int] = None,
) -> InlineKeyboardMarkup:
    """Кнопки управления одной карточкой заказа."""
    rows: List[List[InlineKeyboardButton]] = []

    for label, new_status in STATUS_ACTIONS.get(current_status, []):
        rows.append(
            [
                InlineKeyboardButton(
                    text=label,
                    callback_data=(
                        "admin:status:{0}:{1}:{2}:{3}".format(
                            order_id,
                            new_status,
                            filter_key,
                            page,
                        )
                    ),
                )
            ]
        )

    if telegram_id:
        rows.append(
            [
                InlineKeyboardButton(
                    text="💬 Написать клиенту",
                    url="tg://user?id={0}".format(telegram_id),
                )
            ]
        )

    navigation: List[InlineKeyboardButton] = []
    if previous_order_id is not None:
        navigation.append(
            InlineKeyboardButton(
                text="⬅️ Предыдущий",
                callback_data="admin:order:{0}:{1}:{2}".format(
                    previous_order_id,
                    filter_key,
                    page,
                ),
            )
        )

    if next_order_id is not None:
        navigation.append(
            InlineKeyboardButton(
                text="Следующий ➡️",
                callback_data="admin:order:{0}:{1}:{2}".format(
                    next_order_id,
                    filter_key,
                    page,
                ),
            )
        )

    if navigation:
        rows.append(navigation)

    rows.extend(
        [
            [
                InlineKeyboardButton(
                    text="⬅️ К списку заказов",
                    callback_data="admin:list:{0}:{1}".format(
                        filter_key,
                        page,
                    ),
                )
            ],
            [
                InlineKeyboardButton(
                    text="⚙️ Админ-панель",
                    callback_data="menu:admin",
                )
            ],
        ]
    )

    return InlineKeyboardMarkup(inline_keyboard=rows)


def catalog_admin_menu_keyboard(
    product_count: int = 0,
    category_count: int = 0,
    addon_count: int = 0,
    featured_count: int = 0,
) -> InlineKeyboardMarkup:
    """Главное меню управления каталогом."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="📋 Товары ({0})".format(product_count),
                    callback_data="p:list:0",
                ),
                InlineKeyboardButton(
                    text="➕ Добавить товар",
                    callback_data="p:add",
                ),
            ],
            [
                InlineKeyboardButton(
                    text="🎁 Дополнения ({0})".format(addon_count),
                    callback_data="a:list",
                ),
            ],
            [
                InlineKeyboardButton(
                    text="⭐ Популярные ({0})".format(featured_count),
                    callback_data="admin:featured",
                )
            ],
            [
                InlineKeyboardButton(
                    text="⬅️ Админ-панель",
                    callback_data="menu:admin",
                )
            ],
        ]
    )


def products_list_keyboard(
    products: Sequence[Any],
    page: int,
    total_pages: int,
) -> InlineKeyboardMarkup:
    """Список товаров с пагинацией."""
    rows: List[List[InlineKeyboardButton]] = []

    for product in products:
        icon = "🟢" if int(product["is_active"]) else "⚪️"
        featured = "⭐ " if product["featured_position"] is not None else ""
        name = str(product["name"])
        if len(name) > 28:
            name = name[:27] + "…"
        rows.append(
            [
                InlineKeyboardButton(
                    text="{0} {1}{2}".format(icon, featured, name),
                    callback_data="p:view:{0}:{1}".format(
                        int(product["id"]), page
                    ),
                )
            ]
        )

    pagination: List[InlineKeyboardButton] = []
    if page > 0:
        pagination.append(
            InlineKeyboardButton(
                text="⬅️",
                callback_data="p:list:{0}".format(page - 1),
            )
        )
    if total_pages > 1:
        pagination.append(
            InlineKeyboardButton(
                text="{0}/{1}".format(page + 1, total_pages),
                callback_data="noop",
            )
        )
    if page + 1 < total_pages:
        pagination.append(
            InlineKeyboardButton(
                text="➡️",
                callback_data="p:list:{0}".format(page + 1),
            )
        )
    if pagination:
        rows.append(pagination)

    rows.extend(
        [
            [
                InlineKeyboardButton(
                    text="➕ Добавить товар",
                    callback_data="p:add",
                )
            ],
            [
                InlineKeyboardButton(
                    text="⬅️ Каталог",
                    callback_data="admin:products",
                )
            ],
        ]
    )
    return InlineKeyboardMarkup(inline_keyboard=rows)


def featured_products_keyboard(
    products: Sequence[Any],
) -> InlineKeyboardMarkup:
    """Управление блоком популярных товаров на главной."""
    rows: List[List[InlineKeyboardButton]] = []
    total = len(products)

    for index, product in enumerate(products):
        product_id = int(product["id"])
        name = str(product["name"])
        if len(name) > 26:
            name = name[:25] + "…"
        status = "" if int(product["is_active"]) else " · скрыт"
        rows.append(
            [
                InlineKeyboardButton(
                    text="{0}. {1}{2}".format(index + 1, name, status),
                    callback_data="noop",
                )
            ]
        )
        controls: List[InlineKeyboardButton] = []
        if index > 0:
            controls.append(
                InlineKeyboardButton(
                    text="⬆️",
                    callback_data="feat:move:{0}:up".format(product_id),
                )
            )
        if index + 1 < total:
            controls.append(
                InlineKeyboardButton(
                    text="⬇️",
                    callback_data="feat:move:{0}:down".format(product_id),
                )
            )
        controls.append(
            InlineKeyboardButton(
                text="✖ Убрать",
                callback_data="feat:remove:{0}".format(product_id),
            )
        )
        rows.append(controls)

    rows.append(
        [
            InlineKeyboardButton(
                text="➕ Добавить букет",
                callback_data="feat:addlist:0",
            )
        ]
    )

    rows.append(
        [
            InlineKeyboardButton(
                text="⬅️ Каталог",
                callback_data="admin:products",
            )
        ]
    )
    return InlineKeyboardMarkup(inline_keyboard=rows)


def featured_candidates_keyboard(
    products: Sequence[Any],
    page: int,
    total_pages: int,
) -> InlineKeyboardMarkup:
    """Список товаров, которые можно добавить в популярные."""
    rows: List[List[InlineKeyboardButton]] = []
    for product in products:
        name = str(product["name"])
        if len(name) > 29:
            name = name[:28] + "…"
        rows.append(
            [
                InlineKeyboardButton(
                    text="➕ {0}".format(name),
                    callback_data="feat:add:{0}:{1}".format(
                        int(product["id"]),
                        page,
                    ),
                )
            ]
        )

    pagination: List[InlineKeyboardButton] = []
    if page > 0:
        pagination.append(
            InlineKeyboardButton(
                text="⬅️",
                callback_data="feat:addlist:{0}".format(page - 1),
            )
        )
    if total_pages > 1:
        pagination.append(
            InlineKeyboardButton(
                text="{0}/{1}".format(page + 1, total_pages),
                callback_data="noop",
            )
        )
    if page + 1 < total_pages:
        pagination.append(
            InlineKeyboardButton(
                text="➡️",
                callback_data="feat:addlist:{0}".format(page + 1),
            )
        )
    if pagination:
        rows.append(pagination)

    rows.append(
        [
            InlineKeyboardButton(
                text="⬅️ К популярным",
                callback_data="admin:featured",
            )
        ]
    )
    return InlineKeyboardMarkup(inline_keyboard=rows)


def product_card_keyboard(
    product_id: int,
    page: int,
    is_active: bool,
    has_image: bool = False,
    image_count: int = 0,
    is_featured: bool = False,
) -> InlineKeyboardMarkup:
    """Управление одним товаром."""
    rows: List[List[InlineKeyboardButton]] = [
        [
            InlineKeyboardButton(
                text="✏️ Название",
                callback_data="p:e:{0}:name".format(product_id),
            ),
            InlineKeyboardButton(
                text="📝 Описание",
                callback_data="p:e:{0}:desc".format(product_id),
            ),
        ],
        [
            InlineKeyboardButton(
                text="🌿 Состав",
                callback_data="p:e:{0}:composition".format(product_id),
            ),
        ],
        [
            InlineKeyboardButton(
                text="🖼 Главное фото",
                callback_data="p:e:{0}:photo".format(product_id),
            ),
            InlineKeyboardButton(
                text="💰 Цены",
                callback_data="p:e:{0}:prices".format(product_id),
            ),
        ],
        [
            InlineKeyboardButton(
                text="🗂 Тип товара",
                callback_data="p:e:{0}:category".format(product_id),
            ),
            InlineKeyboardButton(
                text="🎁 Дополнения",
                callback_data="p:e:{0}:addons".format(product_id),
            ),
        ],
    ]

    rows.append(
        [
            InlineKeyboardButton(
                text="🖼 Галерея ({0})".format(image_count),
                callback_data="p:g:{0}:{1}".format(product_id, page),
            )
        ]
    )

    rows.append(
        [
            InlineKeyboardButton(
                text=(
                    "✖ Убрать из популярных"
                    if is_featured
                    else "⭐ Добавить в популярные"
                ),
                callback_data="feat:toggle:{0}:{1}".format(
                    product_id,
                    page,
                ),
            )
        ]
    )

    if has_image:
        rows.append(
            [
                InlineKeyboardButton(
                    text="👁 Показать главное фото",
                    callback_data="p:photo:{0}".format(product_id),
                )
            ]
        )

    rows.append(
        [
            InlineKeyboardButton(
                text="🙈 Скрыть" if is_active else "👁 Опубликовать",
                callback_data="p:t:{0}:{1}".format(product_id, page),
            ),
            InlineKeyboardButton(
                text="🗑 Удалить",
                callback_data="p:del:{0}:{1}".format(product_id, page),
            ),
        ]
    )
    rows.extend(
        [
            [
                InlineKeyboardButton(
                    text="⬅️ К товарам",
                    callback_data="p:list:{0}".format(page),
                )
            ],
            [
                InlineKeyboardButton(
                    text="⚙️ Каталог",
                    callback_data="admin:products",
                )
            ],
        ]
    )
    return InlineKeyboardMarkup(inline_keyboard=rows)


def product_gallery_keyboard(
    product_id: int,
    page: int,
    images: Sequence[Any],
    max_images: int = 8,
) -> InlineKeyboardMarkup:
    """Управление несколькими фотографиями товара."""
    rows: List[List[InlineKeyboardButton]] = []

    if len(images) < max_images:
        rows.append(
            [
                InlineKeyboardButton(
                    text="➕ Добавить фото",
                    callback_data="pg:add:{0}:{1}".format(
                        product_id,
                        page,
                    ),
                ),
                InlineKeyboardButton(
                    text="👁 Показать все",
                    callback_data="pg:show:{0}:{1}".format(
                        product_id,
                        page,
                    ),
                ),
            ]
        )
    elif images:
        rows.append(
            [
                InlineKeyboardButton(
                    text="👁 Показать все",
                    callback_data="pg:show:{0}:{1}".format(
                        product_id,
                        page,
                    ),
                )
            ]
        )

    for index, image in enumerate(images, start=1):
        image_id = int(image["id"])
        is_primary = bool(image["is_primary"])
        action_text = (
            "⭐ Фото {0} · главное".format(index)
            if is_primary
            else "☆ Фото {0} · сделать главным".format(index)
        )
        action_callback = (
            "noop"
            if is_primary
            else "pg:main:{0}:{1}:{2}".format(
                product_id,
                page,
                image_id,
            )
        )
        rows.append(
            [
                InlineKeyboardButton(
                    text=action_text,
                    callback_data=action_callback,
                ),
                InlineKeyboardButton(
                    text="🗑",
                    callback_data="pg:del:{0}:{1}:{2}".format(
                        product_id,
                        page,
                        image_id,
                    ),
                ),
            ]
        )

    rows.append(
        [
            InlineKeyboardButton(
                text="⬅️ К товару",
                callback_data="p:view:{0}:{1}".format(
                    product_id,
                    page,
                ),
            )
        ]
    )
    return InlineKeyboardMarkup(inline_keyboard=rows)


def product_delete_confirm_keyboard(
    product_id: int,
    page: int,
) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="Да, удалить",
                    callback_data="p:delok:{0}:{1}".format(
                        product_id, page
                    ),
                )
            ],
            [
                InlineKeyboardButton(
                    text="Нет, вернуться",
                    callback_data="p:view:{0}:{1}".format(
                        product_id, page
                    ),
                )
            ],
        ]
    )


def category_select_keyboard(
    categories: Sequence[Any],
    prefix: str,
    selected_id: Optional[int] = None,
) -> InlineKeyboardMarkup:
    """Выбор категории для создания или редактирования товара."""
    rows: List[List[InlineKeyboardButton]] = []
    for category in categories:
        category_id = int(category["id"])
        selected = "✅ " if selected_id == category_id else ""
        rows.append(
            [
                InlineKeyboardButton(
                    text=selected + str(category["name"]),
                    callback_data="{0}:{1}".format(prefix, category_id),
                )
            ]
        )
    rows.append(
        [
            InlineKeyboardButton(
                text="✖️ Отмена",
                callback_data="catalog:cancel",
            )
        ]
    )
    return InlineKeyboardMarkup(inline_keyboard=rows)


def addons_select_keyboard(
    addons: Sequence[Any],
    selected_ids: Sequence[int],
    toggle_prefix: str,
    done_callback: str,
    cancel_callback: str = "catalog:cancel",
) -> InlineKeyboardMarkup:
    """Множественный выбор дополнений."""
    selected = set(int(value) for value in selected_ids)
    rows: List[List[InlineKeyboardButton]] = []
    for addon in addons:
        addon_id = int(addon["id"])
        mark = "✅" if addon_id in selected else "▫️"
        rows.append(
            [
                InlineKeyboardButton(
                    text="{0} {1} · {2} ₽".format(
                        mark,
                        addon["name"],
                        int(addon["price"]),
                    ),
                    callback_data="{0}:{1}".format(
                        toggle_prefix, addon_id
                    ),
                )
            ]
        )
    rows.extend(
        [
            [
                InlineKeyboardButton(
                    text="Готово ✅",
                    callback_data=done_callback,
                )
            ],
            [
                InlineKeyboardButton(
                    text="✖️ Отмена",
                    callback_data=cancel_callback,
                )
            ],
        ]
    )
    return InlineKeyboardMarkup(inline_keyboard=rows)


def product_create_confirm_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✅ Опубликовать",
                    callback_data="pa:confirm",
                )
            ],
            [
                InlineKeyboardButton(
                    text="✖️ Отмена",
                    callback_data="catalog:cancel",
                )
            ],
        ]
    )


def catalog_cancel_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✖️ Отменить действие",
                    callback_data="catalog:cancel",
                )
            ]
        ]
    )


def categories_list_keyboard(
    categories: Sequence[Any],
) -> InlineKeyboardMarkup:
    rows: List[List[InlineKeyboardButton]] = []
    for category in categories:
        rows.append(
            [
                InlineKeyboardButton(
                    text="{0} ({1})".format(
                        category["name"],
                        int(category["product_count"]),
                    ),
                    callback_data="c:view:{0}".format(
                        int(category["id"])
                    ),
                )
            ]
        )
    rows.append(
        [
            InlineKeyboardButton(
                text="⬅️ Каталог",
                callback_data="admin:products",
            )
        ]
    )
    return InlineKeyboardMarkup(inline_keyboard=rows)


def category_card_keyboard(
    category_id: int,
    is_active: bool,
) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="⬅️ К типам товаров",
                    callback_data="c:list",
                )
            ]
        ]
    )


def addons_list_keyboard(addons: Sequence[Any]) -> InlineKeyboardMarkup:
    rows: List[List[InlineKeyboardButton]] = []
    for addon in addons:
        icon = "🟢" if int(addon["is_active"]) else "⚪️"
        rows.append(
            [
                InlineKeyboardButton(
                    text="{0} {1} · {2} ₽".format(
                        icon,
                        addon["name"],
                        int(addon["price"]),
                    ),
                    callback_data="a:view:{0}".format(int(addon["id"])),
                )
            ]
        )
    rows.extend(
        [
            [
                InlineKeyboardButton(
                    text="➕ Добавить дополнение",
                    callback_data="a:add",
                )
            ],
            [
                InlineKeyboardButton(
                    text="⬅️ Каталог",
                    callback_data="admin:products",
                )
            ],
        ]
    )
    return InlineKeyboardMarkup(inline_keyboard=rows)


def addon_card_keyboard(
    addon_id: int,
    is_active: bool,
) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✏️ Название",
                    callback_data="a:en:{0}".format(addon_id),
                ),
                InlineKeyboardButton(
                    text="💰 Цена",
                    callback_data="a:ep:{0}".format(addon_id),
                ),
            ],
            [
                InlineKeyboardButton(
                    text="🙈 Отключить" if is_active else "👁 Включить",
                    callback_data="a:t:{0}".format(addon_id),
                )
            ],
            [
                InlineKeyboardButton(
                    text="⬅️ К дополнениям",
                    callback_data="a:list",
                )
            ],
        ]
    )
