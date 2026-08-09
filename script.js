"use strict";

const tg = window.Telegram?.WebApp ?? null;

const fallbackProducts = [
  { id: 1, slug: "pink-sunrise", name: "Розовый рассвет", collection: "Букеты", productType: "bouquets", images: ["images/rozovyi-rassvet.webp"], basePrice: 2490, description: "Нежные розы, пышная гортензия и орхидеи в матовой премиальной упаковке.", composition: "Розы, гортензия, орхидеи, эвкалипт", createdAt: "2026-07-20T10:00:00" },
  { id: 2, slug: "sunny-day", name: "Солнечный день", collection: "Букеты", productType: "bouquets", images: ["images/solnechnyi-den.webp"], basePrice: 2290, description: "Яркая композиция с герберами и хризантемами.", composition: "Герберы, хризантемы, зелень", createdAt: "2026-07-21T10:00:00" },
  { id: 3, slug: "lavender-air", name: "Лавандовый воздух", collection: "Букеты", productType: "bouquets", images: ["images/lavandovyi-vozdukh.webp"], basePrice: 3190, description: "Авторский букет в спокойной сиреневой гамме.", composition: "Гортензия, диантус, розы, эвкалипт", createdAt: "2026-07-22T10:00:00" },
  { id: 4, slug: "white-cloud", name: "Белое облако", collection: "Букеты", productType: "bouquets", images: ["images/beloe-oblako.webp"], basePrice: 2790, description: "Воздушный букет из белых цветов.", composition: "Белые розы, эвкалипт", createdAt: "2026-07-23T10:00:00" },
  { id: 5, slug: "berry-mousse", name: "Ягодный мусс", collection: "Букеты", productType: "bouquets", images: ["images/iagodnyi-muss.webp"], basePrice: 2990, description: "Розово-бордовая композиция для яркого поздравления.", composition: "Пионовидные розы, кустовые розы, эвкалипт", createdAt: "2026-07-24T10:00:00" },
  { id: 6, slug: "quiet-garden", name: "Тихий сад", collection: "Букеты", productType: "bouquets", images: ["images/tikhii-sad.webp"], basePrice: 3490, description: "Глубокие красные розы в лаконичной натуральной упаковке.", composition: "Красные розы, эвкалипт", createdAt: "2026-07-25T10:00:00" },
  { id: 7, slug: "night-tulip", name: "Ночной тюльпан", collection: "Букеты", productType: "bouquets", images: ["images/pink-tulips.webp"], basePrice: 2690, description: "Стройные розовые тюльпаны с плотной зеленью.", composition: "Розовые тюльпаны, декоративная зелень", createdAt: "2026-07-26T10:00:00" },
  { id: 8, slug: "blue-porcelain", name: "Голубой фарфор", collection: "Букеты", productType: "bouquets", images: ["images/blue-orchid.webp"], basePrice: 4590, description: "Орхидеи, гвоздики и воздушные акценты.", composition: "Орхидеи, гвоздики, эвкалипт", createdAt: "2026-07-27T10:00:00" },
  { id: 9, slug: "spring-kaleidoscope", name: "Весенний калейдоскоп", collection: "Букеты", productType: "bouquets", images: ["images/color-tulips.webp"], basePrice: 3490, description: "Разноцветные тюльпаны для яркого поздравления.", composition: "Разноцветные тюльпаны", createdAt: "2026-07-28T10:00:00" },
  { id: 10, slug: "cloud-dream", name: "Облачный сон", collection: "Букеты", productType: "bouquets", images: ["images/pastel-dream.webp"], basePrice: 3890, description: "Мягкая композиция из пастельных роз и ромашек.", composition: "Розы, ромашки, эвкалипт", createdAt: "2026-07-29T10:00:00" },
  { id: 11, slug: "apricot-light", name: "Абрикосовый свет", collection: "Букеты", productType: "bouquets", images: ["images/apricot-tulips.webp"], basePrice: 2890, description: "Тёплые абрикосовые тюльпаны для комплимента.", composition: "Абрикосовые тюльпаны", createdAt: "2026-07-30T10:00:00" },
  { id: 12, slug: "summer-vow", name: "Летний обет", collection: "Букеты", productType: "bouquets", images: ["images/wedding-meadow.webp"], basePrice: 5290, description: "Садовый букет с дельфиниумом, розами и полевыми цветами.", composition: "Дельфиниум, розы, полевые цветы, зелень", createdAt: "2026-07-31T10:00:00" },
  { id: 9001, slug: "postcard-tender-words", name: "Нежные слова", collection: "Открытки", productType: "postcards", images: ["images/postcard-tender-words.webp"], basePrice: 390, description: "Минималистичная открытка для тёплого поздравления. Внутри достаточно места для личного послания.", composition: "Плотная дизайнерская бумага, матовая печать, конверт", createdAt: "2026-08-01T10:00:00", variants: [{ id: 90011, name: "А6", price: 390, is_default: true }] },
  { id: 9002, slug: "postcard-for-you", name: "Для тебя", collection: "Открытки", productType: "postcards", images: ["images/postcard-for-you.webp"], basePrice: 490, description: "Спокойная голубая открытка с конвертом. Подходит к букетам в холодной гамме.", composition: "Фактурный картон, тиснение, конверт", createdAt: "2026-08-02T10:00:00", variants: [{ id: 90021, name: "А6", price: 490, is_default: true }] },
  { id: 9003, slug: "toy-cloud-bear", name: "Мишка Облако", collection: "Мягкие игрушки", productType: "soft-toys", images: ["images/toy-cloud-bear.webp"], basePrice: 1490, description: "Мягкий плюшевый мишка в светлой гамме — спокойное дополнение к подарку.", composition: "Гипоаллергенный плюш, безопасный наполнитель", createdAt: "2026-08-03T10:00:00", variants: [{ id: 90031, name: "25 см", price: 1490, is_default: true }, { id: 90032, name: "40 см", price: 2290, is_default: false }] },
  { id: 9004, slug: "toy-moon-bunny", name: "Зайка Луна", collection: "Мягкие игрушки", productType: "soft-toys", images: ["images/toy-moon-bunny.webp"], basePrice: 1690, description: "Нежный голубой зайка с длинными ушами. Хорошо сочетается с открыткой и пастельным букетом.", composition: "Мягкий текстиль, гипоаллергенный наполнитель", createdAt: "2026-08-04T10:00:00", variants: [{ id: 90041, name: "30 см", price: 1690, is_default: true }] }
];

const productTypeLabels = {
  bouquets: "Букеты",
  postcards: "Открытки",
  "soft-toys": "Мягкие игрушки"
};

function productTypeLabel(product) {
  return productTypeLabels[product?.productType]
    || product?.collection
    || "Товар";
}

function isProductActive(product) {
  return product?.active !== false && product?.is_active !== false;
}

function publicProducts() {
  return products.filter(isProductActive);
}

const localImagesBySlug = new Map(
  fallbackProducts.map((product) => [product.slug, product.images])
);
let products = fallbackProducts.map((product, index) => ({
  ...product,
  image: product.images[0],
  isFeatured: index < 3,
  featuredPosition: index < 3 ? index : null,
  variants: [],
  addons: []
}));

const appShell = document.querySelector("#appShell");
const profileHero = document.querySelector("#profileHero");
const bottomNav = document.querySelector("#bottomNav");
const checkoutAction = document.querySelector("#checkoutAction");
const checkoutForm = document.querySelector("#checkoutForm");
const placeOrderButton = document.querySelector("#placeOrderButton");
const cartContentElement = document.querySelector("#cartContent");
const deleteConfirm = document.querySelector("#deleteConfirm");
const deleteConfirmText = document.querySelector("#deleteConfirmText");
const confirmDeleteButton = document.querySelector("#confirmDeleteButton");
const pages = [...document.querySelectorAll("[data-page]")];
const navItems = [...document.querySelectorAll("[data-nav]")];
const navTargets = [...document.querySelectorAll("[data-nav-target]")];
const bottomPages = ["main", "search", "cart", "profile"];
const adminWorkspacePages = ["admin-orders", "admin-products"];
let userSession = { loaded: false, authenticated: false, isAdmin: false, stats: null };

let activeProduct = null;

// Эти параметры относятся к фильтру на главной странице.
let appliedCatalogFilter = { price: "all", sort: "featured" };
let pendingCatalogFilter = { ...appliedCatalogFilter };

// Каталог использует отдельные полноценные настройки.
let appliedCatalogType = "all";
let catalogSort = "featured";
let catalogPriceBounds = { min: 0, max: 10000 };
let catalogPriceRange = { min: 0, max: 10000 };
let catalogPriceReady = false;
let catalogRenderFrame = null;
let activeCatalogPicker = null;
let currentGalleryIndex = 0;
let galleryScrollFrame = null;
let selectedSize = "M";
let selectedVariantId = null;
let previousPage = "main";
let cartReturnPage = "main";
let toastTimer = null;
let pendingDeleteIndex = null;
let openSwipeElement = null;
let swipeGesture = null;
let suppressCartClickUntil = 0;
const SWIPE_ACTION_WIDTH = 72;

const revealObserver = "IntersectionObserver" in window
  ? new IntersectionObserver((entries) => {
      entries.forEach((entry) => {
        /*
         * Запускаем появление только когда элемент действительно вошёл
         * в экран, а не когда снизу видна его тонкая полоска.
         */
        if (entry.isIntersecting && entry.intersectionRatio >= 0.18) {
          entry.target.classList.add("is-revealed");
          return;
        }

        /*
         * Класс снимается только после уверенного выхода из экрана.
         * Небольшие изменения высоты, фильтрация и переключение сердечка
         * больше не перезапускают анимацию у крайних карточек.
         */
        const viewportHeight =
          entry.rootBounds?.height || window.innerHeight || 0;
        const fullyAbove = entry.boundingClientRect.bottom < -24;
        const fullyBelow =
          entry.boundingClientRect.top > viewportHeight + 24;

        if (!entry.isIntersecting && (fullyAbove || fullyBelow)) {
          entry.target.classList.remove("is-revealed");
        }
      });
    }, {
      threshold: [0, 0.18],
      rootMargin: "0px 0px -8% 0px"
    })
  : null;

const favorites = new Set(parseStoredArray("bloombox-favorites"));
const cart = sanitizeCart(parseStoredArray("bloombox-cart"));

function parseStoredArray(key) {
  try {
    const value = JSON.parse(localStorage.getItem(key) || "[]");
    return Array.isArray(value) ? value : [];
  } catch {
    return [];
  }
}

function sanitizeCart(items) {
  return items
    .filter((item) => item && Number(item.id) > 0)
    .map((item) => ({
      id: Number(item.id),
      size: String(item.size || "M"),
      variantId: item.variantId ? Number(item.variantId) : null,
      price: Math.max(0, Number(item.price) || 0),
      quantity: Math.max(1, Math.min(99, Number(item.quantity) || 1)),
      addons: Array.isArray(item.addons) ? item.addons : []
    }));
}

function money(value) {
  return `${Math.round(Number(value) || 0).toLocaleString("ru-RU")} ₽`;
}

function currentPage() {
  return document.querySelector(".page.is-active")?.dataset.page || "main";
}

function normalizePage(value) {
  return [...bottomPages, ...adminWorkspacePages, "favorites", "admin"].includes(value) ? value : "main";
}

function profileDestination() {
  // DEV MODE: временно открываем админку через профиль для разработки интерфейса.
  return "admin";
}

function setActivePage(pageName, { haptic = false } = {}) {
  let page = normalizePage(pageName);

  if (page === "profile") {
    page = profileDestination();
  }

  // DEV MODE: админка доступна для просмотра без проверки роли.
  // Перед релизом вернуть проверку userSession.isAdmin.


  const current = currentPage();

  if (page === "cart" && current !== "cart") {
    cartReturnPage = current === "favorites" ? "main" : current;
  }

  pages.forEach((item) => {
    const active = item.dataset.page === page;
    item.hidden = !active;
    item.classList.toggle("is-active", active);
  });

  navItems.forEach((item) => {
    const navPage = page === "admin" ? "profile" : page;
    const active = item.dataset.nav === navPage;
    item.classList.toggle("is-active", active);
    active ? item.setAttribute("aria-current", "page") : item.removeAttribute("aria-current");
  });

  appShell.classList.toggle("is-main", page === "main");
  appShell.classList.toggle("is-cart", page === "cart");
  appShell.classList.toggle("is-admin", page === "admin" || adminWorkspacePages.includes(page));
  profileHero.hidden = page !== "main";
  bottomNav.hidden = page === "cart" || adminWorkspacePages.includes(page);

  if (bottomPages.includes(page) || page === "admin" || adminWorkspacePages.includes(page)) {
    sessionStorage.setItem(
      "bloombox-active-page",
      page === "admin" || adminWorkspacePages.includes(page) ? "profile" : page
    );
  }

  if (page === "favorites") renderFavorites();
  if (page === "search") renderCatalog(filterCatalog());
  if (page === "cart") renderCart();
  if (page === "admin-orders") loadAdminOrders();
  if (page === "admin-products") loadAdminProducts();

  window.requestAnimationFrame(() => prepareReveal(document.querySelector(`[data-page="${page}"]`)));

  updateCheckoutAction(page);
  updateTelegramChrome(page);

  if (haptic) tg?.HapticFeedback?.selectionChanged?.();
  window.scrollTo({ top: 0, behavior: "auto" });
}

function updateTelegramChrome(page) {
  if (!tg) return;
  const main = page === "main";
  tg.setHeaderColor?.(main ? "#24272d" : "#eef2f5");
  tg.setBackgroundColor?.("#eef2f5");

  if (page === "cart" || page === "favorites" || adminWorkspacePages.includes(page)) {
    tg.BackButton?.show?.();
  } else {
    tg.BackButton?.hide?.();
  }
}

function productCard(product) {
  const active = favorites.has(product.id);
  const typeLabel = productTypeLabel(product);
  return `
    <article class="product-card" data-product-id="${product.id}" tabindex="0">
      <div class="product-card__media">
        <img src="${product.image}" alt="${escapeHtml(typeLabel)} — ${escapeHtml(product.name)}" loading="lazy">
        <button class="mini-favorite ${active ? "is-active" : ""}" type="button" data-favorite-id="${product.id}" aria-label="${active ? "Убрать из избранного" : "Добавить в избранное"}" aria-pressed="${active ? "true" : "false"}">
          <svg viewBox="0 0 24 24"><path d="M20.8 4.9a5.45 5.45 0 0 0-7.7 0L12 6l-1.1-1.1a5.45 5.45 0 0 0-7.7 7.7l1.1 1.1L12 21.4l7.7-7.7 1.1-1.1a5.45 5.45 0 0 0 0-7.7Z"/></svg>
        </button>
      </div>
      <div class="product-card__body">
        <span>${escapeHtml(typeLabel)}</span>
        <h3>${escapeHtml(product.name)}</h3>
        <div class="product-card__footer">
          <strong>от ${money(product.basePrice)}</strong>
          <button type="button" data-open-product="${product.id}" aria-label="Открыть ${escapeHtml(product.name)}"><svg viewBox="0 0 24 24"><path d="m9 18 6-6-6-6"/></svg></button>
        </div>
      </div>
    </article>`;
}

function renderProducts(
  target,
  list,
  emptyText = "Добавьте товары в избранное, и они появятся на этой странице.",
  { animate = null, emptyAction = null } = {}
) {
  if (!target) return;

  const firstRender = target.dataset.productsRendered !== "true";
  const shouldAnimate = animate ?? firstRender;

  const emptyActionMarkup = emptyAction
    ? `<button class="empty-state__action" type="button" data-empty-action="${escapeAttribute(emptyAction.action)}">${escapeHtml(emptyAction.label)}</button>`
    : "";

  target.innerHTML = list.length
    ? list.map(productCard).join("")
    : `<div class="empty-state"><div><strong>Пока ничего нет</strong><p>${escapeHtml(emptyText)}</p>${emptyActionMarkup}</div></div>`;

  target.dataset.productsRendered = "true";

  if (shouldAnimate) {
    window.requestAnimationFrame(() => {
      prepareReveal(target, { animate: true });
    });
  } else {
    /*
     * Новая разметка сразу становится видимой. Observer всё равно
     * подключается, поэтому повторное появление при настоящем скролле
     * продолжает работать.
     */
    prepareReveal(target, { animate: false });
  }
}

function homeSearchQuery() {
  return document.querySelector("#homeSearch")?.value.trim().toLowerCase() || "";
}

function catalogSearchQuery() {
  return document.querySelector("#catalogSearch")?.value.trim().toLowerCase() || "";
}

function normalizeSearchWord(value) {
  const word = String(value || "")
    .toLowerCase()
    .replaceAll("ё", "е")
    .replace(/[^а-яa-z0-9-]+/gi, "");

  if (word.length <= 3) return word;

  const endings = [
    "иями", "ями", "ами", "ого", "ему", "ыми", "ими",
    "иях", "ах", "ях", "ов", "ев", "ей", "ом", "ем",
    "ую", "юю", "ая", "яя", "ое", "ее", "ые", "ие",
    "ий", "ый", "ой", "ы", "и", "а", "я", "у", "ю"
  ];

  const ending = endings.find(
    (candidate) => word.endsWith(candidate)
      && word.length - candidate.length >= 3
  );
  return ending ? word.slice(0, -ending.length) : word;
}

function searchTokens(value) {
  return String(value || "")
    .toLowerCase()
    .replaceAll("ё", "е")
    .split(/[^а-яa-z0-9-]+/gi)
    .map(normalizeSearchWord)
    .filter(Boolean);
}

function productMatchesQuery(product, query) {
  const queryTokens = searchTokens(query);
  if (!queryTokens.length) return true;

  const productTokens = searchTokens([
    product.name,
    product.collection,
    product.composition,
    product.description
  ].filter(Boolean).join(" "));

  return queryTokens.every((queryToken) => (
    productTokens.some((productToken) => (
      productToken === queryToken
      || productToken.startsWith(queryToken)
      || queryToken.startsWith(productToken)
    ))
  ));
}

function filterProductsByText(list, query) {
  if (!query) return [...list];
  return list.filter((product) => productMatchesQuery(product, query));
}

function applyPriceAndSort(list) {
  const filtered = list.filter((product) => {
    const price = Number(product.basePrice) || 0;
    return (
      appliedCatalogFilter.price === "all"
      || (appliedCatalogFilter.price === "under3000" && price < 3000)
      || (appliedCatalogFilter.price === "3000to4000" && price >= 3000 && price <= 4000)
      || (appliedCatalogFilter.price === "over4000" && price > 4000)
    );
  });

  if (appliedCatalogFilter.sort === "newest") {
    return filtered.sort((a, b) => productCreatedTime(b) - productCreatedTime(a));
  }
  if (appliedCatalogFilter.sort === "priceAsc") {
    return filtered.sort((a, b) => a.basePrice - b.basePrice);
  }
  if (appliedCatalogFilter.sort === "priceDesc") {
    return filtered.sort((a, b) => b.basePrice - a.basePrice);
  }
  if (appliedCatalogFilter.sort === "nameAsc") {
    return filtered.sort((a, b) => a.name.localeCompare(b.name, "ru"));
  }
  if (appliedCatalogFilter.sort === "nameDesc") {
    return filtered.sort((a, b) => b.name.localeCompare(a.name, "ru"));
  }
  return filtered.sort(compareFeaturedProducts);
}

function renderHome() {
  const query = homeSearchQuery();
  const filtersActive = filterIsActive();
  const searchMode = Boolean(query) || filtersActive;
  const productsSection = document.querySelector("#page-main .products-section");
  const eyebrow = document.querySelector("#homeSectionEyebrow");
  const title = document.querySelector("#homeSectionTitle");
  const clearButton = document.querySelector("#homeSearchClear");
  const showAllButton = document.querySelector("#homeShowAll");

  clearButton.hidden = !query;
  showAllButton.hidden = Boolean(query);
  productsSection.classList.toggle("is-searching", searchMode);

  if (searchMode) {
    const result = applyPriceAndSort(filterProductsByText(publicProducts(), query));

    eyebrow.textContent = query ? "Результаты поиска" : "Подходящие варианты";
    title.textContent = query
      ? `По запросу «${document.querySelector("#homeSearch").value.trim()}»`
      : "Букеты по фильтру";

    renderProducts(
      document.querySelector("#homeProducts"),
      result,
      query
        ? "По вашему запросу букеты не найдены."
        : "По выбранным параметрам букеты не найдены."
    );
    return;
  }

  eyebrow.textContent = "Выбор BloomBox";
  title.textContent = "Популярные букеты";

  const featured = publicProducts()
    .filter((product) => product.isFeatured)
    .sort((a, b) => (a.featuredPosition ?? 999) - (b.featuredPosition ?? 999));

  renderProducts(
    document.querySelector("#homeProducts"),
    featured,
    "Администратор пока не выбрал популярные букеты."
  );
}

function pluralizeProducts(count) {
  const mod10 = count % 10;
  const mod100 = count % 100;
  if (mod10 === 1 && mod100 !== 11) return `${count} товар`;
  if (mod10 >= 2 && mod10 <= 4 && (mod100 < 12 || mod100 > 14)) {
    return `${count} товара`;
  }
  return `${count} товаров`;
}

function catalogHasActiveControls() {
  return (
    Boolean(catalogSearchQuery())
    || appliedCatalogType !== "all"
    || catalogSort !== "featured"
    || !catalogPriceIsFullRange()
  );
}

function resetCatalogAll() {
  const input = document.querySelector("#catalogSearch");
  if (input) input.value = "";
  appliedCatalogType = "all";
  catalogSort = "featured";
  catalogPriceRange = { ...catalogPriceBounds };
  renderCatalog(filterCatalog());
  document.querySelector("[data-catalog-type='all']")?.scrollIntoView({
    behavior: "smooth",
    block: "nearest",
    inline: "start"
  });
  tg?.HapticFeedback?.impactOccurred?.("light");
}

function renderCatalog(list = filterCatalog()) {
  updateCatalogControls();

  const query = catalogSearchQuery();
  const hasActiveControls = catalogHasActiveControls();
  const clearButton = document.querySelector("#catalogSearchClear");
  const resetButton = document.querySelector("#catalogResetAll");
  const countElement = document.querySelector("#catalogResultsCount");

  if (clearButton) clearButton.hidden = !query;
  if (resetButton) resetButton.hidden = !hasActiveControls;
  if (countElement) countElement.textContent = pluralizeProducts(list.length);

  renderProducts(
    document.querySelector("#catalogProducts"),
    list,
    query
      ? "Попробуйте изменить запрос или сбросить параметры."
      : "Попробуйте изменить цену или тип товара.",
    {
      emptyAction: hasActiveControls
        ? { label: "Сбросить фильтры", action: "reset-catalog" }
        : null
    }
  );
}

function renderFavorites(options = {}) {
  renderProducts(
    document.querySelector("#favoriteProducts"),
    publicProducts().filter((product) => favorites.has(product.id)),
    "Добавьте товары в избранное, и они появятся на этой странице.",
    {
      ...options,
      emptyAction: {
        label: "Перейти в каталог",
        action: "open-catalog"
      }
    }
  );
}

function syncFavoriteButtons(productId = null) {
  const selector = productId === null
    ? "[data-favorite-id]"
    : `[data-favorite-id="${Number(productId)}"]`;

  document.querySelectorAll(selector).forEach((button) => {
    const id = Number(button.dataset.favoriteId);
    const active = favorites.has(id);
    button.classList.toggle("is-active", active);
    button.setAttribute(
      "aria-label",
      active ? "Убрать из избранного" : "Добавить в избранное"
    );
    button.setAttribute("aria-pressed", active ? "true" : "false");
  });
}

function playFavoriteFeedback(button) {
  if (!button) return;
  button.classList.remove("is-favorite-feedback");
  void button.offsetWidth;
  button.classList.add("is-favorite-feedback");

  window.setTimeout(() => {
    button.classList.remove("is-favorite-feedback");
  }, 260);
}

function saveFavorites({ changedId = null, sourceButton = null } = {}) {
  localStorage.setItem(
    "bloombox-favorites",
    JSON.stringify([...favorites])
  );

  /*
   * Главное исправление: каталоги не пересоздаются из-за одного
   * сердечка. Поэтому карточки не становятся «новыми» и reveal-анимация
   * у первого и нижних товаров больше не запускается.
   */
  syncFavoriteButtons(changedId);
  updateDetailFavorite();

  if (currentPage() === "favorites") {
    renderFavorites({ animate: false });
  }

  playFavoriteFeedback(sourceButton);
}

const catalogProductTypes = [
  { value: "all", label: "Все" },
  { value: "bouquets", label: "Букеты" },
  { value: "postcards", label: "Открытки" },
  { value: "soft-toys", label: "Мягкие игрушки" }
];

const catalogSortOptions = [
  { value: "featured", label: "Сначала популярные" },
  { value: "newest", label: "Сначала новинки" },
  { value: "priceAsc", label: "Сначала дешевле" },
  { value: "priceDesc", label: "Сначала дороже" },
  { value: "nameAsc", label: "По названию А–Я" },
  { value: "nameDesc", label: "По названию Я–А" }
];

function productCreatedTime(product) {
  const timestamp = Date.parse(product?.createdAt || "");
  return Number.isFinite(timestamp) ? timestamp : Number(product?.id || 0);
}

function compareFeaturedProducts(a, b) {
  if (a.isFeatured !== b.isFeatured) return a.isFeatured ? -1 : 1;
  if (a.isFeatured && b.isFeatured) {
    const difference =
      (a.featuredPosition ?? 999999) - (b.featuredPosition ?? 999999);
    if (difference) return difference;
  }
  return productCreatedTime(b) - productCreatedTime(a);
}

function selectedOptionLabel(options, value, fallback) {
  return options.find((option) => option.value === value)?.label || fallback;
}

function syncCatalogPriceBounds() {
  const prices = publicProducts()
    .map((product) => Number(product.basePrice))
    .filter((price) => Number.isFinite(price) && price >= 0);

  const rawMin = prices.length ? Math.min(...prices) : 0;
  const rawMax = prices.length ? Math.max(...prices) : 10000;
  const nextBounds = {
    min: Math.floor(rawMin / 100) * 100,
    max: Math.max(
      Math.ceil(rawMax / 100) * 100,
      Math.floor(rawMin / 100) * 100 + 100
    )
  };

  const wasFullRange = (
    !catalogPriceReady
    || (
      catalogPriceRange.min === catalogPriceBounds.min
      && catalogPriceRange.max === catalogPriceBounds.max
    )
  );

  catalogPriceBounds = nextBounds;

  if (wasFullRange) {
    catalogPriceRange = { ...nextBounds };
  } else {
    catalogPriceRange = {
      min: Math.max(nextBounds.min, Math.min(catalogPriceRange.min, nextBounds.max)),
      max: Math.min(nextBounds.max, Math.max(catalogPriceRange.max, nextBounds.min))
    };
    if (catalogPriceRange.min > catalogPriceRange.max) {
      catalogPriceRange = { ...nextBounds };
    }
  }

  catalogPriceReady = true;
}

function catalogPriceIsFullRange() {
  return (
    catalogPriceRange.min === catalogPriceBounds.min
    && catalogPriceRange.max === catalogPriceBounds.max
  );
}

function updateCatalogRangeVisuals() {
  const minInput = document.querySelector("#catalogPriceMin");
  const maxInput = document.querySelector("#catalogPriceMax");
  const range = document.querySelector("#catalogRange");
  if (!minInput || !maxInput || !range) return;

  minInput.min = String(catalogPriceBounds.min);
  minInput.max = String(catalogPriceBounds.max);
  minInput.value = String(catalogPriceRange.min);
  maxInput.min = String(catalogPriceBounds.min);
  maxInput.max = String(catalogPriceBounds.max);
  maxInput.value = String(catalogPriceRange.max);

  const total = Math.max(1, catalogPriceBounds.max - catalogPriceBounds.min);
  const from = ((catalogPriceRange.min - catalogPriceBounds.min) / total) * 100;
  const to = ((catalogPriceRange.max - catalogPriceBounds.min) / total) * 100;

  range.style.setProperty("--range-from", `${Math.max(0, Math.min(100, from))}%`);
  range.style.setProperty("--range-to", `${Math.max(0, Math.min(100, to))}%`);
  document.querySelector("#catalogPriceMinLabel").textContent = money(catalogPriceRange.min);
  document.querySelector("#catalogPriceMaxLabel").textContent = money(catalogPriceRange.max);
  document.querySelector("#catalogPriceReset").disabled = catalogPriceIsFullRange();
}

function filterCatalog() {
  syncCatalogPriceBounds();

  const query = catalogSearchQuery();

  const filtered = publicProducts().filter((product) => {
    const typeMatches = (
      appliedCatalogType === "all"
      || product.productType === appliedCatalogType
    );
    const price = Number(product.basePrice) || 0;
    return (
      typeMatches
      && price >= catalogPriceRange.min
      && price <= catalogPriceRange.max
      && productMatchesQuery(product, query)
    );
  });

  if (catalogSort === "newest") {
    return filtered.sort((a, b) => productCreatedTime(b) - productCreatedTime(a));
  }
  if (catalogSort === "priceAsc") {
    return filtered.sort((a, b) => a.basePrice - b.basePrice);
  }
  if (catalogSort === "priceDesc") {
    return filtered.sort((a, b) => b.basePrice - a.basePrice);
  }
  if (catalogSort === "nameAsc") {
    return filtered.sort((a, b) => a.name.localeCompare(b.name, "ru"));
  }
  if (catalogSort === "nameDesc") {
    return filtered.sort((a, b) => b.name.localeCompare(a.name, "ru"));
  }
  return filtered.sort(compareFeaturedProducts);
}

function updateCatalogControls() {
  document.querySelectorAll("[data-catalog-type]").forEach((button) => {
    const active = button.dataset.catalogType === appliedCatalogType;
    button.classList.toggle("is-active", active);
    button.setAttribute("aria-pressed", active ? "true" : "false");
  });
  document.querySelector("#catalogSortValue").textContent =
    selectedOptionLabel(catalogSortOptions, catalogSort, "Сначала популярные");
  updateCatalogRangeVisuals();
}

function catalogPickerConfig() {
  return {
    title: "Сортировка",
    options: catalogSortOptions,
    selected: catalogSort
  };
}

function openCatalogPicker() {
  activeCatalogPicker = "sort";
  const config = catalogPickerConfig();
  document.querySelector("#catalogPickerTitle").textContent = config.title;
  document.querySelector("#catalogPickerOptions").innerHTML = config.options.map((option) => `
    <button
      class="catalog-picker-option ${option.value === config.selected ? "is-active" : ""}"
      type="button"
      data-catalog-picker-value="${escapeAttribute(option.value)}"
    >
      <span>${escapeHtml(option.label)}</span>
      <span class="catalog-picker-option__check" aria-hidden="true">
        <svg viewBox="0 0 24 24"><path d="m6 12 4 4 8-8"/></svg>
      </span>
    </button>
  `).join("");

  document.querySelector("#catalogPickerOverlay").hidden = false;
  document.body.classList.add("is-modal-open");
  tg?.HapticFeedback?.impactOccurred?.("light");
}

function closeCatalogPicker() {
  document.querySelector("#catalogPickerOverlay").hidden = true;
  document.body.classList.remove("is-modal-open");
  activeCatalogPicker = null;
}

function selectCatalogPickerValue(value) {
  if (!catalogSortOptions.some((option) => option.value === value)) return;
  catalogSort = value;
  renderCatalog(filterCatalog());
  closeCatalogPicker();
  tg?.HapticFeedback?.selectionChanged?.();
}

function queueCatalogRender() {
  if (catalogRenderFrame) cancelAnimationFrame(catalogRenderFrame);
  catalogRenderFrame = requestAnimationFrame(() => {
    catalogRenderFrame = null;
    renderCatalog(filterCatalog());
  });
}

function handleCatalogPriceInput(changedInput) {
  const minInput = document.querySelector("#catalogPriceMin");
  const maxInput = document.querySelector("#catalogPriceMax");
  let minValue = Number(minInput.value);
  let maxValue = Number(maxInput.value);

  if (minValue > maxValue) {
    if (changedInput === minInput) maxValue = minValue;
    else minValue = maxValue;
  }

  catalogPriceRange = {
    min: Math.max(catalogPriceBounds.min, minValue),
    max: Math.min(catalogPriceBounds.max, maxValue)
  };

  updateCatalogRangeVisuals();
  queueCatalogRender();
}

function resetCatalogPrice() {
  catalogPriceRange = { ...catalogPriceBounds };
  renderCatalog(filterCatalog());
  tg?.HapticFeedback?.impactOccurred?.("light");
}

function filterIsActive() {
  return (
    appliedCatalogFilter.price !== "all"
    || appliedCatalogFilter.sort !== "featured"
  );
}

function updateFilterButtons() {
  const active = filterIsActive();
  document.querySelector("#homeFilterButton")?.classList.toggle("is-active", active);

}

function syncFilterSheet() {
  document.querySelectorAll("[data-filter-price]").forEach((button) => {
    button.classList.toggle(
      "is-active",
      button.dataset.filterPrice === pendingCatalogFilter.price
    );
  });
  document.querySelectorAll("[data-filter-sort]").forEach((button) => {
    button.classList.toggle(
      "is-active",
      button.dataset.filterSort === pendingCatalogFilter.sort
    );
  });
}

function openCatalogFilter({ navigateToCatalog = false } = {}) {
  if (navigateToCatalog) {
    setActivePage("search", { haptic: true });
  }
  pendingCatalogFilter = { ...appliedCatalogFilter };
  syncFilterSheet();
  const overlay = document.querySelector("#filterOverlay");
  overlay.hidden = false;
  document.body.classList.add("is-modal-open");
  tg?.HapticFeedback?.impactOccurred?.("light");
}

function closeCatalogFilter() {
  const overlay = document.querySelector("#filterOverlay");
  overlay.hidden = true;
  document.body.classList.remove("is-modal-open");
}

function applyCatalogFilter() {
  appliedCatalogFilter = { ...pendingCatalogFilter };
  updateFilterButtons();
  renderHome();
  renderCatalog(filterCatalog());
  closeCatalogFilter();
  tg?.HapticFeedback?.notificationOccurred?.("success");
}

function resetCatalogFilter() {
  pendingCatalogFilter = { price: "all", sort: "featured" };
  syncFilterSheet();
}

function toggleFavorite(id, sourceButton = null) {
  favorites.has(id) ? favorites.delete(id) : favorites.add(id);
  saveFavorites({
    changedId: id,
    sourceButton
  });
  tg?.HapticFeedback?.impactOccurred?.("light");
}

function productVariants(product) {
  if (Array.isArray(product.variants) && product.variants.length) {
    return product.variants
      .map((variant) => ({
        id: Number(variant.id),
        name: String(variant.name),
        price: Number(variant.price),
        isDefault: Boolean(variant.is_default)
      }))
      .filter((variant) => variant.name && Number.isFinite(variant.price) && variant.price >= 0);
  }

  // Только резервный режим для просмотра интерфейса без API.
  // Никакие цены размеров здесь не рассчитываются: в рабочем Mini App
  // все варианты и цены приходят из SQLite, куда их задаёт администратор.
  return [{
    id: null,
    name: "M",
    price: Number(product.basePrice) || 0,
    isDefault: true
  }];
}

function productImages(product) {
  const values = Array.isArray(product?.images)
    ? product.images.filter(Boolean)
    : [];
  if (values.length) return [...new Set(values)];
  return product?.image ? [product.image] : [];
}

function updateGalleryState(index, { scroll = false, instant = false } = {}) {
  const track = document.querySelector("#detailGalleryTrack");
  const dots = [...document.querySelectorAll("[data-gallery-index]")];
  const counter = document.querySelector("#galleryCounter");
  const prev = document.querySelector("#galleryPrev");
  const next = document.querySelector("#galleryNext");
  const total = productImages(activeProduct).length || 1;

  currentGalleryIndex = Math.max(0, Math.min(total - 1, Number(index) || 0));

  dots.forEach((dot, dotIndex) => {
    const active = dotIndex === currentGalleryIndex;
    dot.classList.toggle("is-active", active);
    dot.setAttribute("aria-current", active ? "true" : "false");
  });

  if (counter) {
    counter.textContent = `${currentGalleryIndex + 1} / ${total}`;
  }
  if (prev) prev.disabled = currentGalleryIndex === 0;
  if (next) next.disabled = currentGalleryIndex >= total - 1;

  if (scroll && track) {
    track.scrollTo({
      left: currentGalleryIndex * track.clientWidth,
      behavior: instant ? "auto" : "smooth"
    });
  }
}

function renderProductGallery(product) {
  const images = productImages(product);
  const track = document.querySelector("#detailGalleryTrack");
  const dots = document.querySelector("#galleryDots");
  const prev = document.querySelector("#galleryPrev");
  const next = document.querySelector("#galleryNext");

  track.innerHTML = images.map((src, index) => `
    <div class="detail-gallery__slide">
      <img
        src="${escapeAttribute(src)}"
        alt="${escapeAttribute(`${productTypeLabel(product)} ${product.name}, фото ${index + 1}`)}"
        loading="${index === 0 ? "eager" : "lazy"}"
        draggable="false"
      >
    </div>
  `).join("");

  dots.innerHTML = images.map((_, index) => `
    <button
      class="gallery-dot ${index === 0 ? "is-active" : ""}"
      type="button"
      data-gallery-index="${index}"
      aria-label="Открыть фото ${index + 1}"
      aria-current="${index === 0 ? "true" : "false"}"
    ></button>
  `).join("");

  const multiple = images.length > 1;
  prev.hidden = !multiple;
  next.hidden = !multiple;
  dots.hidden = !multiple;

  currentGalleryIndex = 0;
  window.requestAnimationFrame(() => {
    track.scrollLeft = 0;
    updateGalleryState(0);
  });
}

function openProduct(id) {
  activeProduct = products.find((product) => product.id === id);
  if (!activeProduct) return;
  if (!isProductActive(activeProduct) && currentPage() !== "admin-products") return;

  const variants = productVariants(activeProduct);
  const preferred = variants.find((variant) => variant.name.toUpperCase() === "M") || variants.find((variant) => variant.isDefault) || variants[0];
  selectedSize = preferred?.name || "M";
  selectedVariantId = preferred?.id || null;

  renderProductGallery(activeProduct);
  document.querySelector("#detailCollection").textContent = activeProduct.collection;
  document.querySelector("#detailTitle").textContent = activeProduct.name;
  document.querySelector("#detailOptionTitle").textContent =
    activeProduct.productType === "postcards" ? "Формат" : "Размер";
  const compositionText = activeProduct.composition || "Состав уточняется";
  const descriptionText = activeProduct.description || "";
  document.querySelector("#detailComposition").textContent = compositionText;
  document.querySelector("#detailDescription").textContent = descriptionText;
  document.querySelector("#detailAboutSection").hidden = !descriptionText;
  document.querySelector("#sizeOptions").innerHTML = variants.map((variant) => `
    <button
      class="size-option ${variant.name === selectedSize ? "is-active" : ""}"
      type="button"
      data-size="${escapeAttribute(variant.name)}"
      data-variant-id="${variant.id || ""}"
      data-variant-price="${variant.price}"
      aria-label="Размер ${escapeAttribute(variant.name)}, цена ${escapeAttribute(money(variant.price))}"
    >
      <span class="size-option__name">${escapeHtml(variant.name)}</span>
      <span class="size-option__price">${escapeHtml(money(variant.price))}</span>
    </button>`).join("");

  updateDetailPrice();
  updateDetailFavorite();
  document.querySelector("#productOverlay").hidden = false;
  document.body.style.overflow = "hidden";
}

function closeProduct() {
  document.querySelector("#productOverlay").hidden = true;
  document.body.style.overflow = "";
}

function currentVariantPrice() {
  if (!activeProduct) return 0;
  const variants = productVariants(activeProduct);
  const variant = variants.find((item) => item.id === selectedVariantId) || variants.find((item) => item.name === selectedSize);
  return variant?.price ?? activeProduct.basePrice;
}

function updateDetailPrice({ animate = false } = {}) {
  if (!activeProduct) return;

  const priceElement = document.querySelector("#detailPrice");
  const addButtonLabel = document.querySelector("#addToCartButton span");
  const newPrice = money(currentVariantPrice());

  if (animate) {
    priceElement.classList.remove("is-changing");
    void priceElement.offsetWidth;
    priceElement.classList.add("is-changing");

    window.setTimeout(() => {
      priceElement.textContent = newPrice;
      priceElement.classList.remove("is-changing");
    }, 70);
  } else {
    priceElement.textContent = newPrice;
  }

  if (addButtonLabel) {
    addButtonLabel.textContent = `В корзину · ${selectedSize}`;
  }
}

function updateDetailFavorite() {
  const button = document.querySelector("#detailFavorite");
  if (!button || !activeProduct) return;

  const active = favorites.has(activeProduct.id);
  button.classList.toggle("is-active", active);
  button.setAttribute(
    "aria-label",
    active ? "Убрать из избранного" : "Добавить в избранное"
  );
  button.setAttribute("aria-pressed", active ? "true" : "false");
}

function addToCart() {
  if (!activeProduct) return;

  const existing = cart.find((item) => item.id === activeProduct.id && item.size === selectedSize && item.variantId === selectedVariantId);
  if (existing) {
    existing.quantity = Math.min(99, existing.quantity + 1);
  } else {
    cart.push({
      id: activeProduct.id,
      size: selectedSize,
      variantId: selectedVariantId,
      price: Math.round(currentVariantPrice()),
      quantity: 1,
      addons: []
    });
  }

  saveCart();
  renderCart();
  tg?.HapticFeedback?.notificationOccurred?.("success");
  showToast("Букет добавлен в корзину", "success");
  closeProduct();
}

function saveCart() {
  localStorage.setItem("bloombox-cart", JSON.stringify(cart));
  updateCartIndicator();
}

function updateCartIndicator() {
  const button = document.querySelector('[data-nav="cart"]');
  if (!button) return;
  const count = cart.reduce((sum, item) => sum + item.quantity, 0);
  button.classList.toggle("has-items", count > 0);
  button.setAttribute("aria-label", count > 0 ? `Корзина, товаров: ${count}` : "Корзина");
}

function cartTotals() {
  const subtotal = cart.reduce((sum, item) => sum + item.price * item.quantity + addonTotal(item), 0);
  const deliveryType = document.querySelector('input[name="delivery_type"]:checked')?.value || "delivery";
  const delivery = deliveryType === "delivery" && subtotal > 0 && subtotal < 5000 ? 390 : 0;
  return { subtotal, delivery, total: subtotal + delivery };
}

function addonTotal(item) {
  return (item.addons || []).reduce((sum, addon) => sum + (Number(addon.price) || 0) * (Number(addon.quantity) || 1), 0);
}

function pluralProducts(count) {
  const mod10 = count % 10;
  const mod100 = count % 100;
  if (mod10 === 1 && mod100 !== 11) return `${count} товар`;
  if (mod10 >= 2 && mod10 <= 4 && !(mod100 >= 12 && mod100 <= 14)) return `${count} товара`;
  return `${count} товаров`;
}

function renderCart() {
  const target = document.querySelector("#cartContent");
  const count = cart.reduce((sum, item) => sum + item.quantity, 0);
  document.querySelector("#cartItemsCount").textContent = pluralProducts(count);

  if (!cart.length) {
    target.innerHTML = `
      <div class="cart-empty">
        <div>
          <strong>Корзина пуста</strong>
          <p>Выберите букет, после чего здесь появится форма оформления заказа.</p>
          <button type="button" data-empty-search>Перейти в каталог</button>
        </div>
      </div>`;
    checkoutForm.hidden = true;
    updateSummary();
    updateCheckoutAction(currentPage());
    return;
  }

  checkoutForm.hidden = false;
  target.innerHTML = cart.map((item, index) => {
    const product = products.find((candidate) => candidate.id === item.id) || fallbackProducts.find((candidate) => candidate.id === item.id);
    const addonText = item.addons?.length
      ? `<p>${item.addons.map((addon) => `+ ${escapeHtml(addon.name || "Дополнение")}`).join(" · ")}</p>`
      : "";
    return `
      <article class="cart-swipe" data-swipe-index="${index}">
        <button class="cart-swipe__delete" type="button" data-cart-remove="${index}" aria-label="Удалить ${escapeAttribute(product?.name || "товар")}">
          <svg viewBox="0 0 24 24" aria-hidden="true" focusable="false">
            <path d="M8.2 3.5h7.6l.9 2.3H20v2.3H4V5.8h3.3l.9-2.3Z"/>
            <path d="M6.3 9.2h11.4l-.8 10.3H7.1L6.3 9.2Zm3.1 2.1v5.7h2v-5.7h-2Zm3.2 0v5.7h2v-5.7h-2Z"/>
          </svg>
        </button>
        <div class="cart-item" data-swipe-surface>
          <div class="cart-item__image"><img src="${product?.image || ""}" alt="Букет ${escapeHtml(product?.name || "")}"></div>
          <div class="cart-item__content">
            <div class="cart-item__top">
              <div>
                <h3>${escapeHtml(product?.name || "Букет")}</h3>
                <p>Размер ${escapeHtml(item.size)} · ${money(item.price)} за шт.</p>
                ${addonText}
              </div>
              <strong class="cart-item__price">${money(item.price * item.quantity + addonTotal(item))}</strong>
            </div>
            <div class="cart-item__bottom">
              <div class="quantity-control" aria-label="Количество">
                <button type="button" data-cart-minus="${index}" aria-label="Уменьшить количество"><svg viewBox="0 0 24 24"><path d="M6 12h12"/></svg></button>
                <strong>${item.quantity}</strong>
                <button type="button" data-cart-plus="${index}" aria-label="Увеличить количество"><svg viewBox="0 0 24 24"><path d="M12 6v12M6 12h12"/></svg></button>
              </div>
            </div>
          </div>
        </div>
      </article>`;
  }).join("");

  openSwipeElement = null;
  window.requestAnimationFrame(() => prepareReveal(target));
  updateSummary();
  updateCheckoutAction(currentPage());
}

function updateSummary() {
  const target = document.querySelector("#summaryLines");
  const totals = cartTotals();

  if (!cart.length) {
    target.innerHTML = "";
  } else {
    const deliveryType = document.querySelector('input[name="delivery_type"]:checked')?.value || "delivery";
    target.innerHTML = cart.map((item) => {
      const product = products.find((candidate) => candidate.id === item.id) || fallbackProducts.find((candidate) => candidate.id === item.id);
      const extras = item.addons?.length ? `<small>${item.addons.map((addon) => `+ ${escapeHtml(addon.name || "Дополнение")}`).join(", ")}</small>` : "";
      return `<div class="summary-line"><div><span>${escapeHtml(product?.name || "Букет")} × ${item.quantity}</span><small>Размер ${escapeHtml(item.size)} · ${money(item.price)} за шт.</small>${extras}</div><strong>${money(item.price * item.quantity + addonTotal(item))}</strong></div>`;
    }).join("") + `<div class="summary-line summary-line--delivery"><div><span>${deliveryType === "pickup" ? "Самовывоз" : "Доставка"}</span><small>${deliveryType === "pickup" ? "Заберёте заказ самостоятельно" : (totals.delivery ? "Стандартный тариф" : "Бесплатная доставка")}</small></div><strong>${totals.delivery ? money(totals.delivery) : "0 ₽"}</strong></div>`;
  }

  document.querySelector("#summaryTotal").textContent = money(totals.total);
  document.querySelector("#checkoutActionTotal").textContent = money(totals.total);
}

function updateCheckoutAction(page = currentPage()) {
  const visible = page === "cart" && cart.length > 0;
  checkoutAction.hidden = !visible;
  placeOrderButton.disabled = !visible;
}

function changeCartQuantity(index, delta) {
  const item = cart[index];
  if (!item) return;
  item.quantity = Math.max(1, Math.min(99, item.quantity + delta));
  saveCart();
  renderCart();
  tg?.HapticFeedback?.impactOccurred?.("light");
}

function removeCartItem(index) {
  if (!cart[index]) return;
  cart.splice(index, 1);
  saveCart();
  renderCart();
  tg?.HapticFeedback?.impactOccurred?.("medium");
}

function cartProductName(index) {
  const item = cart[index];
  if (!item) return "этот товар";
  return products.find((product) => product.id === item.id)?.name
    || fallbackProducts.find((product) => product.id === item.id)?.name
    || "этот товар";
}

function openDeleteConfirm(index) {
  if (!cart[index]) return;
  pendingDeleteIndex = index;
  deleteConfirmText.textContent = `Вы уверены, что хотите удалить «${cartProductName(index)}» из корзины?`;
  deleteConfirm.hidden = false;
  document.body.classList.add("is-dialog-open");
  window.requestAnimationFrame(() => deleteConfirm.classList.add("is-visible"));
  window.setTimeout(() => confirmDeleteButton.focus({ preventScroll: true }), 110);
  tg?.HapticFeedback?.notificationOccurred?.("warning");
}

function closeDeleteConfirm() {
  pendingDeleteIndex = null;
  deleteConfirm.classList.remove("is-visible");
  document.body.classList.remove("is-dialog-open");
  window.setTimeout(() => { deleteConfirm.hidden = true; }, 120);
}

function confirmDelete() {
  const index = pendingDeleteIndex;
  if (index === null || !cart[index]) {
    closeDeleteConfirm();
    return;
  }
  const name = cartProductName(index);
  closeDeleteConfirm();
  removeCartItem(index);
  showToast(`«${name}» удалён из корзины`);
}

function setSwipePosition(wrapper, offset, animate = true) {
  if (!wrapper?.isConnected) return;
  const surface = wrapper.querySelector("[data-swipe-surface]");
  if (!surface) return;
  surface.style.transition = animate ? "" : "none";
  surface.style.transform = `translate3d(${offset}px, 0, 0)`;
  wrapper.dataset.swipeOffset = String(offset);
  wrapper.classList.toggle("is-open", offset <= -(SWIPE_ACTION_WIDTH - 8));
  if (!animate) window.requestAnimationFrame(() => { surface.style.transition = ""; });
}

function closeOpenSwipe(animate = true) {
  if (!openSwipeElement?.isConnected) {
    openSwipeElement = null;
    return;
  }
  setSwipePosition(openSwipeElement, 0, animate);
  openSwipeElement = null;
}

function finishSwipe(open) {
  const wrapper = swipeGesture?.wrapper;
  if (!wrapper) return;
  if (open) {
    if (openSwipeElement && openSwipeElement !== wrapper) setSwipePosition(openSwipeElement, 0);
    setSwipePosition(wrapper, -SWIPE_ACTION_WIDTH);
    openSwipeElement = wrapper;
    tg?.HapticFeedback?.selectionChanged?.();
  } else {
    setSwipePosition(wrapper, 0);
    if (openSwipeElement === wrapper) openSwipeElement = null;
  }
}

function prepareReveal(
  root = document,
  { animate = true } = {}
) {
  if (!root) return;

  const selector = ".feature-card, .search-panel, .section-heading, .page-heading, .product-card, .checkout-header, .checkout-card, .cart-swipe, .simple-page, .empty-state";
  const elements = [...root.querySelectorAll(selector)]
    .filter((element) => !element.dataset.revealReady);

  elements.forEach((element, index) => {
    element.dataset.revealReady = "true";
    element.classList.add("reveal-item");

    /*
     * Карточкам товара не задаём ступенчатую задержку. Иначе нижняя
     * карточка начинала двигаться уже тогда, когда её край был виден.
     */
    const delay = (
      animate && !element.matches(".product-card")
        ? Math.min(index, 5) * 36
        : 0
    );
    element.style.setProperty("--reveal-delay", `${delay}ms`);

    if (!animate) {
      element.classList.add("is-revealed");
    }

    if (revealObserver) {
      revealObserver.observe(element);
    } else {
      element.classList.add("is-revealed");
    }
  });
}

function updateDeliveryFields() {
  const type = document.querySelector('input[name="delivery_type"]:checked')?.value || "delivery";
  const address = document.querySelector("#deliveryAddress");
  const deliveryFields = document.querySelector("#deliveryFields");
  const isDelivery = type === "delivery";
  address.required = isDelivery;
  address.disabled = !isDelivery;
  address.closest(".field").hidden = !isDelivery;
  deliveryFields.dataset.type = type;
  updateSummary();
}

function updateRecipientFields() {
  const same = document.querySelector("#sameRecipient").checked;
  const customerName = document.querySelector("#customerName");
  const customerPhone = document.querySelector("#customerPhone");
  const recipientName = document.querySelector("#recipientName");
  const recipientPhone = document.querySelector("#recipientPhone");

  if (same) {
    recipientName.value = customerName.value;
    recipientPhone.value = customerPhone.value;
  }

  [recipientName, recipientPhone].forEach((field) => {
    field.disabled = same;
    field.required = !same;
  });
  document.querySelector("#recipientFields").classList.toggle("is-disabled", same);
}

function localDateString(date = new Date()) {
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, "0");
  const day = String(date.getDate()).padStart(2, "0");
  return `${year}-${month}-${day}`;
}

async function submitOrder(event) {
  event.preventDefault();
  document.querySelector("#formStatus").textContent = "";
  document.querySelector("#formStatus").classList.remove("is-success");

  if (!cart.length) {
    showFormError("Добавьте хотя бы один букет в корзину.");
    return;
  }

  updateRecipientFields();
  updateDeliveryFields();

  if (!checkoutForm.checkValidity()) {
    checkoutForm.reportValidity();
    showFormError("Проверьте обязательные поля формы.");
    return;
  }

  if (!tg?.initData) {
    showFormError("Для отправки настоящего заказа откройте Mini App внутри Telegram.");
    showToast("Форма готова. Реальный заказ отправляется внутри Telegram.", "error");
    return;
  }

  const sameRecipient = document.querySelector("#sameRecipient").checked;
  const payload = {
    init_data: tg.initData,
    items: cart.map((item) => {
      const prepared = {
        product_id: item.id,
        quantity: item.quantity,
        addons: (item.addons || []).map((addon) => ({ addon_id: addon.addon_id || addon.id, quantity: addon.quantity || 1 })).filter((addon) => addon.addon_id)
      };
      if (item.variantId) prepared.variant_id = item.variantId;
      return prepared;
    }),
    customer: {
      name: document.querySelector("#customerName").value.trim(),
      phone: document.querySelector("#customerPhone").value.trim()
    },
    recipient: {
      name: sameRecipient ? document.querySelector("#customerName").value.trim() : document.querySelector("#recipientName").value.trim(),
      phone: sameRecipient ? document.querySelector("#customerPhone").value.trim() : document.querySelector("#recipientPhone").value.trim()
    },
    delivery: {
      type: document.querySelector('input[name="delivery_type"]:checked').value,
      address: document.querySelector('input[name="delivery_type"]:checked').value === "delivery" ? document.querySelector("#deliveryAddress").value.trim() : "",
      date: document.querySelector("#deliveryDate").value,
      interval: document.querySelector("#deliveryInterval").value
    },
    postcard_text: document.querySelector("#postcardText").value.trim(),
    comment: document.querySelector("#orderComment").value.trim()
  };

  setSubmitLoading(true);
  try {
    const response = await fetch("/api/orders", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-Telegram-Init-Data": tg.initData
      },
      body: JSON.stringify(payload)
    });
    const data = await response.json().catch(() => ({}));
    if (!response.ok) throw new Error(data.error || "Не удалось оформить заказ");

    cart.splice(0, cart.length);
    saveCart();
    checkoutForm.reset();
    applyTelegramUser();
    setDefaultFormValues();
    renderCart();
    document.querySelector("#formStatus").textContent = `Заказ ${data.order?.order_number || ""} успешно оформлен.`;
    document.querySelector("#formStatus").classList.add("is-success");
    showToast(`Заказ ${data.order?.order_number || ""} оформлен`, "success");
    tg?.HapticFeedback?.notificationOccurred?.("success");
  } catch (error) {
    showFormError(error.message || "Не удалось оформить заказ");
    showToast(error.message || "Не удалось оформить заказ", "error");
    tg?.HapticFeedback?.notificationOccurred?.("error");
  } finally {
    setSubmitLoading(false);
  }
}

function setSubmitLoading(loading) {
  placeOrderButton.disabled = loading || !cart.length;
  placeOrderButton.querySelector("span").textContent = loading ? "Отправляем…" : "Заказать";
}

function showFormError(message) {
  const status = document.querySelector("#formStatus");
  status.textContent = message;
  status.classList.remove("is-success");
}

function showToast(message, type = "") {
  const toast = document.querySelector("#toast");
  const icon = type === "success"
    ? '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="m6.75 12.25 3.2 3.2 7.3-7.3"/></svg>'
    : type === "error"
      ? '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="m8 8 8 8M16 8l-8 8"/></svg>'
      : '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M12 7.25v5.5M12 16.5h.01"/><circle cx="12" cy="12" r="8.25"/></svg>';

  window.clearTimeout(toastTimer);
  toast.className = `toast${type ? ` is-${type}` : ""}${currentPage() === "cart" ? " is-cart-context" : ""}`;
  toast.innerHTML = `<span class="toast__icon">${icon}</span><span class="toast__message">${escapeHtml(message)}</span>`;
  toast.hidden = false;
  window.requestAnimationFrame(() => toast.classList.add("is-visible"));

  toastTimer = window.setTimeout(() => {
    toast.classList.remove("is-visible");
    window.setTimeout(() => { toast.hidden = true; }, 130);
  }, 1500);
}

function setDefaultFormValues() {
  const dateInput = document.querySelector("#deliveryDate");
  dateInput.min = localDateString();
  if (!dateInput.value) dateInput.value = localDateString(new Date(Date.now() + 86400000));
  document.querySelector('input[name="delivery_type"][value="delivery"]').checked = true;
  updateDeliveryFields();
  updateRecipientFields();
}

function escapeHtml(value) {
  return String(value ?? "").replace(/[&<>'"]/g, (character) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", "'": "&#39;", '"': "&quot;" })[character]);
}

function escapeAttribute(value) {
  return escapeHtml(value).replace(/`/g, "&#96;");
}

function getInitials(firstName = "", lastName = "") {
  return `${firstName.trim().charAt(0)}${lastName.trim().charAt(0)}`.trim().toUpperCase() || "BB";
}

function applyTelegramUser() {
  const user = tg?.initDataUnsafe?.user;
  if (!user) return;

  const fullName = [user.first_name, user.last_name].filter(Boolean).join(" ") || user.username || "Гость BloomBox";
  document.querySelector("#userName").textContent = fullName;
  document.querySelector("#userInitials").textContent = getInitials(user.first_name, user.last_name);
  document.querySelector("#customerName").value = fullName;

  if (user.photo_url) {
    const avatar = document.querySelector("#userAvatar");
    const image = new Image();
    image.alt = "";
    image.referrerPolicy = "no-referrer";
    image.onload = () => avatar.replaceChildren(image);
    image.src = user.photo_url;
  }
}


function adminMoney(value) {
  return `${Math.round(Number(value) || 0).toLocaleString("ru-RU")} ₽`;
}

function applyAdminStats(stats = {}) {
  const newCount = Math.max(0, Number(stats.new_count) || 0);
  const orderCount = Math.max(0, Number(stats.order_count) || 0);
  const productCount = Math.max(0, Number(stats.product_count) || 0);
  const revenue = Math.max(0, Number(stats.revenue) || 0);

  document.querySelector("#adminNewOrders").textContent =
    newCount.toLocaleString("ru-RU");
  document.querySelector("#adminOrderCount").textContent =
    orderCount.toLocaleString("ru-RU");
  document.querySelector("#adminProductCount").textContent =
    productCount.toLocaleString("ru-RU");
  document.querySelector("#adminRevenue").textContent =
    adminMoney(revenue);

  const badge = document.querySelector("#adminOrdersBadge");
  if (badge) {
    badge.textContent = newCount > 99 ? "99+" : String(newCount);
    badge.hidden = newCount <= 0;
  }
}

function updateProfileNavigationForRole() {
  const profileItem = document.querySelector('[data-nav="profile"]');
  if (!profileItem) return;

  profileItem.setAttribute(
    "aria-controls",
    userSession.isAdmin ? "page-admin" : "page-profile"
  );
  profileItem.setAttribute(
    "aria-label",
    userSession.isAdmin ? "Админ-панель" : "Профиль"
  );
}

async function loadUserSession() {
  if (!tg?.initData) {
    userSession = {
      loaded: true,
      authenticated: false,
      isAdmin: false,
      stats: null
    };
    updateProfileNavigationForRole();
    return;
  }

  try {
    const response = await fetch("/api/session", {
      headers: {
        Accept: "application/json",
        "X-Telegram-Init-Data": tg.initData
      },
      cache: "no-store"
    });

    if (!response.ok) {
      throw new Error("Не удалось проверить права доступа");
    }

    const data = await response.json();
    userSession = {
      loaded: true,
      authenticated: Boolean(data.authenticated),
      isAdmin: Boolean(data.is_admin),
      stats: data.admin?.stats || null
    };

    updateProfileNavigationForRole();

    if (userSession.isAdmin) {
      applyAdminStats(userSession.stats || {});
      const name = [
        data.user?.first_name,
        data.user?.last_name
      ].filter(Boolean).join(" ");
      if (name) {
        document.querySelector("#adminGreeting").textContent =
          `${name}, доступ администратора подтверждён`;
      }

      if (currentPage() === "profile") {
        setActivePage("admin");
      }
    } else if (currentPage() === "admin") {
      setActivePage("profile");
    }
  } catch (error) {
    console.warn("BloomBox session:", error);
    userSession = {
      loaded: true,
      authenticated: false,
      isAdmin: false,
      stats: null
    };
    updateProfileNavigationForRole();

    if (currentPage() === "admin") {
      setActivePage("profile");
    }
  }
}

async function hydrateProductsFromApi() {
  try {
    const response = await fetch("/api/products", { headers: { Accept: "application/json" }, cache: "no-store" });
    if (!response.ok) return;
    const apiProducts = await response.json();
    if (!Array.isArray(apiProducts) || !apiProducts.length) return;

    const apiCatalogProducts = apiProducts.map((item, index) => {
      const fallback = fallbackProducts.find((product) => product.slug === item.slug) || fallbackProducts.find((product) => product.id === Number(item.id)) || fallbackProducts[index % fallbackProducts.length];
      const apiImages = Array.isArray(item.images)
        ? item.images.filter(Boolean)
        : [];
      const localImages = localImagesBySlug.get(item.slug) || fallback.images;
      const images = apiImages.length
        ? apiImages
        : (item.image_url ? [item.image_url] : localImages);

      return mergeAdminOverride({
        id: Number(item.id),
        name: item.name || fallback.name,
        collection: item.category?.name || fallback.collection,
        productType: item.category?.slug || fallback.productType || "bouquets",
        createdAt: item.created_at || fallback.createdAt || "",
        images: [...new Set(images.filter(Boolean))],
        image: images[0] || fallback.images[0],
        image_url: images[0] || fallback.images[0],
        basePrice: Number(item.min_price || item.base_price || fallback.basePrice),
        base_price: Number(item.min_price || item.base_price || fallback.basePrice),
        description: item.description || fallback.description,
        composition: item.composition || fallback.composition || "",
        active: item.is_active !== false,
        is_active: item.is_active !== false,
        isFeatured: Boolean(item.is_featured),
        featuredPosition: Number.isInteger(item.featured_position)
          ? item.featured_position
          : null,
        variants: Array.isArray(item.variants) ? item.variants : [],
        addons: Array.isArray(item.addons) ? item.addons : []
      });
    });

    const presentTypes = new Set(
      apiCatalogProducts.map((product) => product.productType)
    );
    const demoSupplements = fallbackProducts
      .filter((product) => product.id >= 9000)
      .filter((product) => !presentTypes.has(product.productType))
      .map((product) => ({
        ...product,
        image: product.images[0],
        active: true,
        is_active: true,
        isFeatured: false,
        featuredPosition: null,
        addons: []
      }));

    products = appendAdminCreatedProducts([...apiCatalogProducts, ...demoSupplements]).map((product) => mergeAdminOverride(product));

    cart.forEach((item) => {
      const product = products.find((candidate) => candidate.id === item.id);
      if (!product) return;
      const variant = productVariants(product).find((candidate) => candidate.name === item.size);
      if (variant) {
        item.variantId = variant.id;
        item.price = variant.price;
      }
    });
    saveCart();
    renderAllProducts();
    renderCart();
  } catch {
    // Локальная демонстрационная версия продолжает работать без API.
  }
}

function renderAllProducts() {
  renderHome();
  renderCatalog(filterCatalog());
  updateFilterButtons();
  renderFavorites();
}

function initTelegram() {
  if (!tg) return;
  tg.ready();
  tg.expand();
  tg.BackButton?.onClick?.(() => {
    if (!document.querySelector("#adminProductEditor")?.hidden) {
      closeAdminProductEditor();
      return;
    }
    if (!document.querySelector("#adminProductTypePicker")?.hidden) {
      closeAdminProductTypePicker();
      return;
    }
    if (!document.querySelector("#productOverlay").hidden) {
      closeProduct();
      return;
    }
    if (currentPage() === "cart") {
      setActivePage(cartReturnPage || "main", { haptic: true });
    } else if (currentPage() === "favorites") {
      setActivePage(previousPage || "main", { haptic: true });
    } else if (adminWorkspacePages.includes(currentPage())) {
      setActivePage("admin", { haptic: true });
    }
  });
}

navItems.forEach((item) => item.addEventListener("click", () => {
  const target = item.dataset.nav === "profile"
    ? profileDestination()
    : item.dataset.nav;
  setActivePage(target, { haptic: true });
}));

navTargets.forEach((item) => item.addEventListener("click", () => {
  const target = item.dataset.navTarget === "profile"
    ? profileDestination()
    : item.dataset.navTarget;
  setActivePage(target, { haptic: true });
}));



async function loadAdminOrders() {
  const list = document.querySelector("#adminOrdersList");
  if (!list) return;
  try {
    const response = await fetch("/api/orders");
    const data = await response.json();
    const orders = Array.isArray(data) ? data : (data.orders || []);
    list.innerHTML = orders.length ? orders.map(order => `
      <article class="admin-order-card card-surface">
        <b>Заказ #${order.id ?? "—"}</b>
        <span>${order.status ?? "Новый"} • ${order.total ?? ""} ₽</span>
        <small>${order.customer_name ?? order.name ?? "Клиент"}</small>
        <strong>${order.status ?? "Новый"}</strong>
      </article>`).join("") : `<article class="admin-order-card card-surface">Заказов пока нет</article>`;
  } catch(e) {
    list.innerHTML = `<article class="admin-order-card card-surface">Не удалось загрузить заказы</article>`;
  }
}

let adminProductsCache = [];
let adminProductsFilter = "all";
let adminProductsSearch = "";
const adminProductOverridesKey = "bloombox-admin-product-overrides";
const adminCreatedProductsKey = "bloombox-admin-created-products";
const adminMainHeroImageKey = "bloombox-admin-main-hero-image";
let adminProductOverrides = readAdminProductOverrides();
let adminHeroImageDraft = null;
let adminEditorProductId = null;
let adminEditorOriginal = null;
let adminEditorPendingDraft = null;
let adminEditorMode = "edit";
let adminFeaturedDragState = null;

const adminProductTypePresets = {
  bouquets: {
    label: "Букет",
    collection: "Букеты",
    productType: "bouquets",
    description: "",
    composition: "",
    variants: [
      { name: "S", price: 0, is_default: true },
      { name: "M", price: 0, is_default: false },
      { name: "L", price: 0, is_default: false }
    ]
  },
  postcards: {
    label: "Открытка",
    collection: "Открытки",
    productType: "postcards",
    description: "",
    composition: "Плотная дизайнерская бумага, печать, конверт",
    variants: [{ name: "А6", price: 0, is_default: true }]
  },
  "soft-toys": {
    label: "Игрушка",
    collection: "Мягкие игрушки",
    productType: "soft-toys",
    description: "",
    composition: "Мягкий текстиль, безопасный наполнитель",
    variants: [{ name: "30 см", price: 0, is_default: true }]
  }
};

function mainHeroImageElement() {
  return document.querySelector("#mainHeroImage");
}

function defaultMainHeroImage() {
  const image = mainHeroImageElement();
  return image?.dataset.defaultSrc || image?.getAttribute("src") || "images/rozovyi-rassvet.webp";
}

function readAdminMainHeroImage() {
  try {
    return String(localStorage.getItem(adminMainHeroImageKey) || "").trim();
  } catch {
    return "";
  }
}

function saveAdminMainHeroImage(value) {
  const image = String(value || "").trim();
  try {
    if (image) {
      localStorage.setItem(adminMainHeroImageKey, image);
    } else {
      localStorage.removeItem(adminMainHeroImageKey);
    }
  } catch {
    showToast("Не удалось сохранить главную картинку", "error");
  }
}

function currentMainHeroImage() {
  return readAdminMainHeroImage() || defaultMainHeroImage();
}

function renderAdminMainHeroPreview(value = currentMainHeroImage()) {
  const image = String(value || "").trim() || defaultMainHeroImage();
  const preview = document.querySelector("#adminHeroImagePreview");
  const input = document.querySelector("#adminHeroImageInput");

  if (preview) {
    preview.innerHTML = `<img src="${escapeAttribute(image)}" alt="">`;
    preview.classList.toggle("has-device-photo", isInlineAdminImage(image));
  }
  if (input && input.value !== image) {
    input.value = image;
  }
}

function applyMainHeroImage(value = currentMainHeroImage()) {
  const image = String(value || "").trim() || defaultMainHeroImage();
  const heroImage = mainHeroImageElement();
  if (heroImage) heroImage.src = image;
  adminHeroImageDraft = image;
  renderAdminMainHeroPreview(image);
}

async function setAdminMainHeroImageFromFile(file) {
  if (!file) return;
  if (!String(file.type || "").startsWith("image/")) {
    showToast("Выберите изображение", "error");
    return;
  }

  try {
    showToast("Загружаю фото…");
    const rawDataUrl = await readAdminImageFile(file);
    const imageDataUrl = await compressAdminImageDataUrl(rawDataUrl);
    adminHeroImageDraft = imageDataUrl;
    renderAdminMainHeroPreview(imageDataUrl);
    showToast("Фото выбрано", "success");
    tg?.HapticFeedback?.notificationOccurred?.("success");
  } catch(e) {
    showToast("Не удалось открыть фото", "error");
  }
}

function saveAdminMainHeroImageDraft() {
  const input = document.querySelector("#adminHeroImageInput");
  const nextImage = String(input?.value || adminHeroImageDraft || "").trim();
  if (!nextImage) {
    showToast("Выберите фото или укажите путь", "error");
    input?.focus();
    return;
  }

  saveAdminMainHeroImage(nextImage);
  applyMainHeroImage(nextImage);
  showToast("Главная картинка обновлена", "success");
  tg?.HapticFeedback?.notificationOccurred?.("success");
}

function resetAdminMainHeroImage() {
  saveAdminMainHeroImage("");
  applyMainHeroImage(defaultMainHeroImage());
  const fileInput = document.querySelector("#adminHeroImageFile");
  if (fileInput) fileInput.value = "";
  showToast("Главная картинка сброшена", "success");
  tg?.HapticFeedback?.selectionChanged?.();
}

function readAdminProductOverrides() {
  try {
    const value = JSON.parse(localStorage.getItem(adminProductOverridesKey) || "{}");
    return value && typeof value === "object" && !Array.isArray(value) ? value : {};
  } catch {
    return {};
  }
}

function saveAdminProductOverrides() {
  try {
    localStorage.setItem(adminProductOverridesKey, JSON.stringify(adminProductOverrides));
  } catch {
    showToast("Не удалось сохранить изменения в браузере", "error");
  }
}


function readAdminCreatedProducts() {
  try {
    const value = JSON.parse(localStorage.getItem(adminCreatedProductsKey) || "[]");
    if (!Array.isArray(value)) return [];
    return value
      .map((product, index) => normalizeAdminProduct(product, fallbackProducts.length + index))
      .filter((product) => product && product.id);
  } catch {
    return [];
  }
}

function saveAdminCreatedProducts(productsToSave) {
  try {
    localStorage.setItem(adminCreatedProductsKey, JSON.stringify(productsToSave || []));
  } catch {
    showToast("Не удалось сохранить новый товар в браузере", "error");
  }
}

function appendAdminCreatedProducts(source = []) {
  const result = Array.isArray(source) ? [...source] : [];
  const sourceIds = new Set(result.map((product) => Number(product.id)).filter(Boolean));
  readAdminCreatedProducts().forEach((product) => {
    const id = Number(product.id);
    if (!id || sourceIds.has(id)) return;
    result.push(product);
    sourceIds.add(id);
  });
  return result;
}

function ensureAdminSupplementProducts(source = []) {
  const result = appendAdminCreatedProducts(source).map((product, index) => normalizeAdminProduct(product, index));
  const presentTypes = new Set(result.map((product) => product.productType).filter(Boolean));
  const presentIds = new Set(result.map((product) => Number(product.id)).filter(Boolean));
  const presentSlugs = new Set(result.map((product) => product.slug).filter(Boolean));

  fallbackProducts
    .filter((product) => product.productType !== "bouquets")
    .filter((product) => !presentTypes.has(product.productType))
    .forEach((product) => {
      if (presentIds.has(Number(product.id)) || presentSlugs.has(product.slug)) return;
      const preparedProduct = normalizeAdminProduct({
        ...product,
        image: product.images?.[0] || "",
        image_url: product.images?.[0] || "",
        active: true,
        is_active: true,
        featured: false,
        isFeatured: false,
        is_featured: false,
        featuredPosition: null,
        featured_position: null
      }, fallbackProducts.indexOf(product));

      result.push(preparedProduct);
      presentIds.add(Number(preparedProduct.id));
      presentSlugs.add(preparedProduct.slug);
      presentTypes.add(preparedProduct.productType);
    });

  return result.map(mergeAdminOverride);
}

function upsertAdminCreatedProduct(product) {
  if (!product?.id) return;

  const createdProducts = readAdminCreatedProducts();
  const index = createdProducts.findIndex((item) => Number(item.id) === Number(product.id));
  const nextProduct = normalizeAdminProduct({
    ...product,
    active: product.active !== false,
    is_active: product.active !== false,
    isCreatedByAdmin: true
  }, createdProducts.length);

  if (index >= 0) {
    createdProducts[index] = nextProduct;
  } else {
    createdProducts.push(nextProduct);
  }

  saveAdminCreatedProducts(createdProducts);
}

function adminProductTypePreset(type) {
  return adminProductTypePresets[type] || adminProductTypePresets.bouquets;
}

function createAdminProductId() {
  return Date.now();
}

function createAdminVariantId(productId, index) {
  const base = Number(productId) || Date.now();
  return base * 10 + index + 1;
}

function normalizeAdminVariant(variant, index = 0) {
  const name = String(variant?.name || `Вариант ${index + 1}`).trim();
  const numericPrice = Number(variant?.price);
  return {
    id: variant?.id ? Number(variant.id) : null,
    name: name || `Вариант ${index + 1}`,
    price: Number.isFinite(numericPrice) ? Math.max(0, Math.round(numericPrice)) : NaN,
    is_default: Boolean(variant?.is_default ?? variant?.isDefault ?? index === 0)
  };
}

function mergeAdminOverride(product) {
  const override = adminProductOverrides[String(product?.id || "")];
  const source = override ? { ...product, ...override } : { ...product };

  const variants = Array.isArray(source.variants) && source.variants.length
    ? source.variants.map(normalizeAdminVariant)
    : (Array.isArray(product?.variants) ? product.variants.map(normalizeAdminVariant) : []);
  const images = Array.isArray(source.images)
    ? source.images.filter(Boolean)
    : (Array.isArray(product?.images) ? product.images.filter(Boolean) : []);
  const image = source.image ?? source.image_url ?? images[0] ?? product?.image ?? product?.image_url ?? "";
  const variantPrices = variants
    .map((variant) => Number(variant.price))
    .filter((price) => Number.isFinite(price));
  const basePrice = Number(
    source.basePrice
    ?? source.base_price
    ?? source.price
    ?? (variantPrices.length ? Math.min(...variantPrices) : product?.basePrice ?? product?.base_price ?? product?.price)
    ?? 0
  );
  const featured = Boolean(source.featured ?? source.isFeatured ?? source.is_featured);
  const featuredPositionValue = Number(source.featuredPosition ?? source.featured_position);
  const featuredPosition = featured && Number.isFinite(featuredPositionValue) ? featuredPositionValue : null;
  const active = source.active !== false && source.is_active !== false;

  return {
    ...product,
    ...(override || {}),
    image,
    image_url: image,
    images: image ? [image, ...images.filter((item) => item !== image)] : images,
    basePrice,
    base_price: basePrice,
    price: basePrice,
    min_price: basePrice,
    active,
    is_active: active,
    featured,
    isFeatured: featured,
    is_featured: featured,
    featuredPosition,
    featured_position: featuredPosition,
    variants,
    variantsCount: variants.length || product?.variantsCount || 0,
    imagesCount: (image ? 1 : 0) + images.filter((item) => item !== image).length
  };
}

function editableAdminVariants(product) {
  const variants = productVariants(product).map(normalizeAdminVariant);
  if (variants.length) return variants;
  return [normalizeAdminVariant({ name: "M", price: product?.price ?? product?.basePrice ?? product?.base_price ?? 0 }, 0)];
}

function getAdminProductById(productId) {
  const id = Number(productId);
  return getAdminProductSource().find((item) => item.id === id)
    || products.map((product, index) => normalizeAdminProduct(product, index)).find((item) => item.id === id)
    || null;
}

function cloneAdminProduct(product) {
  return JSON.parse(JSON.stringify(product || {}));
}

function normalizeAdminProduct(item, index = 0) {
  const fallback = fallbackProducts.find((product) => product.slug === item?.slug)
    || fallbackProducts.find((product) => product.id === Number(item?.id))
    || fallbackProducts[index % fallbackProducts.length];
  const images = Array.isArray(item?.images)
    ? item.images.filter(Boolean)
    : [];
  const fallbackImages = Array.isArray(fallback?.images) ? fallback.images : [];
  const image = images[0]
    || item?.image
    || item?.image_url
    || fallbackImages[0]
    || "";
  const variants = Array.isArray(item?.variants) ? item.variants : [];
  const price = Number(
    item?.basePrice
    ?? item?.base_price
    ?? item?.min_price
    ?? item?.price
    ?? fallback?.basePrice
    ?? 0
  );
  const rawFeatured = item?.featured ?? item?.isFeatured ?? item?.is_featured ?? false;
  const rawFeaturedPosition = Number(item?.featuredPosition ?? item?.featured_position);
  const featured = Boolean(rawFeatured);
  const featuredPosition = featured && Number.isFinite(rawFeaturedPosition) ? rawFeaturedPosition : null;

  const product = {
    id: Number(item?.id || fallback?.id || index + 1),
    slug: item?.slug || fallback?.slug || `product-${index + 1}`,
    name: item?.name || fallback?.name || "Без названия",
    category: item?.category?.name || item?.collection || fallback?.collection || "Товар",
    collection: item?.category?.name || item?.collection || fallback?.collection || "Товар",
    productType: item?.category?.slug || item?.productType || fallback?.productType || "bouquets",
    image,
    image_url: image,
    images: images.length ? images : (image ? [image] : []),
    price,
    basePrice: price,
    base_price: price,
    min_price: price,
    description: item?.description || fallback?.description || "Описание пока не заполнено",
    composition: item?.composition || fallback?.composition || "Состав не указан",
    active: item?.active !== false && item?.is_active !== false,
    is_active: item?.active !== false && item?.is_active !== false,
    featured,
    isFeatured: featured,
    is_featured: featured,
    featuredPosition,
    featured_position: featuredPosition,
    variants: variants.length ? variants.map(normalizeAdminVariant) : productVariants({ ...fallback, ...item }).map(normalizeAdminVariant),
    variantsCount: variants.length || productVariants({ ...fallback, ...item }).length,
    imagesCount: images.length || productImages({ ...fallback, ...item }).length || (image ? 1 : 0)
  };

  return mergeAdminOverride(product);
}

function getAdminProductSource() {
  if (Array.isArray(adminProductsCache) && adminProductsCache.length) return adminProductsCache;
  return products.map((product, index) => normalizeAdminProduct(product, index));
}

function updateAdminProductStats(items) {
  const total = items.length;
  const active = items.filter((product) => product.active).length;
  const featured = items.filter((product) => product.featured).length;
  const totalElement = document.querySelector("#adminProductTotal");
  const activeElement = document.querySelector("#adminProductActive");
  const featuredElement = document.querySelector("#adminProductFeatured");

  if (totalElement) totalElement.textContent = String(total);
  if (activeElement) activeElement.textContent = String(active);
  if (featuredElement) featuredElement.textContent = String(featured);
}

function isProductFeatured(product) {
  return Boolean(product?.featured ?? product?.isFeatured ?? product?.is_featured);
}

function productFeaturedPosition(product) {
  const position = Number(product?.featuredPosition ?? product?.featured_position);
  return Number.isFinite(position) ? position : 999999;
}

function getSortedFeaturedProducts(source = getAdminProductSource()) {
  return [...source]
    .filter(isProductFeatured)
    .sort((a, b) => {
      const difference = productFeaturedPosition(a) - productFeaturedPosition(b);
      if (difference) return difference;
      return Number(a.id || 0) - Number(b.id || 0);
    });
}

function getAdminFeaturedIds() {
  return getSortedFeaturedProducts().map((product) => Number(product.id)).filter(Boolean);
}

function setAdminFeaturedIds(ids, { silent = false } = {}) {
  const uniqueIds = [...new Set(ids.map(Number).filter(Boolean))];
  const positionMap = new Map(uniqueIds.map((id, index) => [id, index]));
  const sourceIds = new Set(getAdminProductSource().map((product) => Number(product.id)).filter(Boolean));
  const validIds = uniqueIds.filter((id) => sourceIds.has(id));
  const validPositionMap = new Map(validIds.map((id, index) => [id, index]));

  getAdminProductSource().forEach((product) => {
    const id = Number(product.id);
    if (!id) return;

    const featured = validPositionMap.has(id);
    const position = featured ? validPositionMap.get(id) : null;
    const key = String(id);
    adminProductOverrides[key] = {
      ...(adminProductOverrides[key] || {}),
      featured,
      isFeatured: featured,
      is_featured: featured,
      featuredPosition: position,
      featured_position: position
    };
  });

  saveAdminProductOverrides();

  const applyFeaturedState = (product) => {
    const id = Number(product.id);
    const featured = validPositionMap.has(id);
    const position = featured ? validPositionMap.get(id) : null;
    return mergeAdminOverride({
      ...product,
      featured,
      isFeatured: featured,
      is_featured: featured,
      featuredPosition: position,
      featured_position: position
    });
  };

  adminProductsCache = getAdminProductSource().map(applyFeaturedState);
  products = products.map(applyFeaturedState);

  renderAdminProductsList();
  renderAllProducts();

  if (!silent) showToast("Популярное обновлено", "success");
}

function toggleAdminProductFeatured(productId) {
  const id = Number(productId);
  if (!id) return;

  const ids = getAdminFeaturedIds();
  const nextIds = ids.includes(id)
    ? ids.filter((item) => item !== id)
    : [...ids, id];

  setAdminFeaturedIds(nextIds);
  tg?.HapticFeedback?.selectionChanged?.();
}

function toggleAdminProductActive(productId) {
  const id = Number(productId);
  if (!id) return;

  const currentProduct = getAdminProductById(id);
  const nextActive = !isProductActive(currentProduct);
  const key = String(id);

  adminProductOverrides[key] = {
    ...(adminProductOverrides[key] || {}),
    active: nextActive,
    is_active: nextActive
  };

  saveAdminProductOverrides();

  const applyActiveState = (product) => (
    Number(product.id) === id
      ? mergeAdminOverride({ ...product, active: nextActive, is_active: nextActive })
      : mergeAdminOverride(product)
  );

  adminProductsCache = getAdminProductSource().map(applyActiveState);
  products = products.map(applyActiveState);

  renderAdminProductsList();
  renderAllProducts();
  showToast(nextActive ? "Товар снова в наличии" : "Товар скрыт с витрины", nextActive ? "success" : "info");
  tg?.HapticFeedback?.selectionChanged?.();
}

function renderAdminFeaturedManager() {
  const list = document.querySelector("#adminFeaturedList");
  if (!list) return;

  const featuredProducts = getSortedFeaturedProducts();

  if (!featuredProducts.length) {
    list.innerHTML = `
      <article class="admin-featured-empty">
        <strong>Популярное пустое</strong>
        <span>Нажмите «В популярное» у товара ниже, чтобы добавить его на главную.</span>
      </article>`;
    return;
  }

  list.innerHTML = featuredProducts.map((product, index) => `
    <article class="admin-featured-item ${isProductActive(product) ? "" : "is-inactive"}" data-admin-featured-id="${product.id}">
      <div class="admin-featured-item__preview" aria-hidden="true">
        <span class="admin-featured-item__number">${index + 1}</span>
        <span class="admin-featured-item__image">
          ${product.image ? `<img src="${escapeAttribute(product.image)}" alt="" loading="lazy">` : `<i>${escapeHtml(product.name.charAt(0))}</i>`}
        </span>
      </div>
      <div class="admin-featured-item__content">
        <strong>${escapeHtml(product.name)}</strong>
        <span>от ${money(product.price)}</span>
      </div>
      <button class="admin-featured-item__remove" type="button" data-admin-featured-remove="${product.id}" aria-label="Убрать ${escapeAttribute(product.name)} из популярного">×</button>
      <button class="admin-featured-item__handle" type="button" data-admin-featured-drag aria-label="Перетащить ${escapeAttribute(product.name)}">
        <span></span><span></span><span></span>
      </button>
    </article>`).join("");
}

function getFeaturedDragAfterElement(container, y) {
  const items = [...container.querySelectorAll(".admin-featured-item:not(.is-dragging)")];
  return items.reduce((closest, child) => {
    const box = child.getBoundingClientRect();
    const offset = y - box.top - box.height / 2;
    if (offset < 0 && offset > closest.offset) {
      return { offset, element: child };
    }
    return closest;
  }, { offset: Number.NEGATIVE_INFINITY, element: null }).element;
}

function finishAdminFeaturedDrag({ canceled = false } = {}) {
  if (!adminFeaturedDragState) return;

  const { item, list, dragging, pointerId } = adminFeaturedDragState;
  try { item.releasePointerCapture?.(pointerId); } catch {}

  item.classList.remove("is-held", "is-dragging");
  list?.classList.remove("is-sorting");

  if (dragging && !canceled && list) {
    const ids = [...list.querySelectorAll("[data-admin-featured-id]")]
      .map((element) => Number(element.dataset.adminFeaturedId))
      .filter(Boolean);
    setAdminFeaturedIds(ids);
    tg?.HapticFeedback?.notificationOccurred?.("success");
  }

  adminFeaturedDragState = null;
}

function renderAdminProductsList() {
  const list = document.querySelector("#adminProductsList");
  if (!list) return;

  const source = getAdminProductSource();
  const query = adminProductsSearch.trim().toLowerCase();
  const visible = source.filter((product) => {
    const matchesType = adminProductsFilter === "all" || product.productType === adminProductsFilter;
    const haystack = `${product.name} ${product.category} ${product.composition}`.toLowerCase();
    return matchesType && (!query || haystack.includes(query));
  });

  updateAdminProductStats(source);
  renderAdminFeaturedManager();

  if (!visible.length) {
    list.innerHTML = `
      <article class="admin-empty-card card-surface">
        <strong>Товары не найдены</strong>
        <span>Попробуйте изменить поиск или выбрать другой фильтр.</span>
      </article>`;
    return;
  }

  list.innerHTML = visible.map((product) => `
    <article class="admin-product-card card-surface ${product.active ? "" : "is-inactive"}" data-admin-product-id="${product.id}">
      <button class="admin-product-card__image" type="button" data-open-product="${product.id}" aria-label="Открыть ${escapeAttribute(product.name)}">
        ${product.image ? `<img src="${escapeAttribute(product.image)}" alt="${escapeAttribute(product.name)}" loading="lazy">` : `<span>${escapeHtml(product.name.charAt(0))}</span>`}
      </button>
      <div class="admin-product-card__body">
        <div class="admin-product-card__top">
          <span>${escapeHtml(product.category)}</span>
        </div>
        <h2>${escapeHtml(product.name)}</h2>
        <p>${escapeHtml(product.composition || product.description)}</p>
        <div class="admin-product-meta">
          <span>от ${money(product.price)}</span>
          <span>${product.imagesCount} фото</span>
        </div>
        <div class="admin-product-actions">
          <button type="button" data-admin-product-action="edit" data-admin-product-id="${product.id}">Редактировать</button>
          <button class="${product.active ? "is-stock-on" : "is-stock-off"}" type="button" data-admin-product-action="active" data-admin-product-id="${product.id}">${product.active ? "В наличии" : "Нет в наличии"}</button>
          <button class="${product.featured ? "is-featured" : ""}" type="button" data-admin-product-action="featured" data-admin-product-id="${product.id}">${product.featured ? "В популярном" : "В популярное"}</button>
          <button type="button" data-open-product="${product.id}">Открыть</button>
        </div>
      </div>
    </article>`).join("");
}

async function loadAdminProducts() {
  const list = document.querySelector("#adminProductsList");
  if (!list) return;

  list.innerHTML = `
    <article class="admin-empty-card card-surface">
      <strong>Загружаю товары</strong>
      <span>Подготавливаю интерфейс каталога.</span>
    </article>`;

  try {
    const response = await fetch("/api/products", {
      headers: { Accept: "application/json" },
      cache: "no-store"
    });
    if (!response.ok) throw new Error("products_unavailable");
    const data = await response.json();
    const rawProducts = Array.isArray(data) ? data : (data.products || []);
    adminProductsCache = ensureAdminSupplementProducts(rawProducts);
  } catch(e) {
    adminProductsCache = ensureAdminSupplementProducts(products);
  }

  renderAdminProductsList();
  renderAdminMainHeroPreview();
}

function isInlineAdminImage(value) {
  return /^data:image\//i.test(String(value || "").trim());
}

function describeAdminImage(value) {
  const image = String(value || "").trim();
  if (!image) return "Фото не добавлено";
  if (isInlineAdminImage(image)) return "Фото с устройства";
  return compactText(image);
}

function renderAdminEditorPhoto(value, title = "") {
  const preview = document.querySelector("#adminEditPhotoPreview");
  if (!preview) return;

  const image = String(value || "").trim();
  preview.classList.toggle("has-device-photo", isInlineAdminImage(image));
  preview.innerHTML = image
    ? `<img src="${escapeAttribute(image)}" alt="">`
    : `<span>${escapeHtml(String(title || "Т").charAt(0))}</span>`;
}

function setAdminEditorImage(value) {
  const input = document.querySelector("#adminEditImageUrl");
  const title = document.querySelector("#adminEditName")?.value || document.querySelector("#adminEditPhotoTitle")?.textContent || "Товар";
  if (input) input.value = String(value || "").trim();
  renderAdminEditorPhoto(value, title);
}

function readAdminImageFile(file) {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => resolve(String(reader.result || ""));
    reader.onerror = () => reject(reader.error || new Error("image_read_error"));
    reader.readAsDataURL(file);
  });
}

function compressAdminImageDataUrl(dataUrl) {
  return new Promise((resolve) => {
    const source = String(dataUrl || "");
    if (!source || source.startsWith("data:image/svg")) {
      resolve(source);
      return;
    }

    const image = new Image();
    image.onload = () => {
      const maxSide = 1600;
      const longestSide = Math.max(image.naturalWidth || image.width, image.naturalHeight || image.height);
      const scale = longestSide > maxSide ? maxSide / longestSide : 1;
      const width = Math.max(1, Math.round((image.naturalWidth || image.width) * scale));
      const height = Math.max(1, Math.round((image.naturalHeight || image.height) * scale));
      const canvas = document.createElement("canvas");
      canvas.width = width;
      canvas.height = height;
      const context = canvas.getContext("2d");
      if (!context) {
        resolve(source);
        return;
      }
      context.drawImage(image, 0, 0, width, height);
      resolve(canvas.toDataURL("image/jpeg", 0.86));
    };
    image.onerror = () => resolve(source);
    image.src = source;
  });
}

async function setAdminEditorImageFromFile(file) {
  if (!file) return;
  if (!String(file.type || "").startsWith("image/")) {
    showToast("Выберите изображение", "error");
    return;
  }

  try {
    showToast("Загружаю фото…");
    const rawDataUrl = await readAdminImageFile(file);
    const imageDataUrl = await compressAdminImageDataUrl(rawDataUrl);
    setAdminEditorImage(imageDataUrl);
    showToast("Фото выбрано", "success");
    tg?.HapticFeedback?.notificationOccurred?.("success");
  } catch(e) {
    showToast("Не удалось открыть фото", "error");
  }
}

function renderAdminEditorVariants(product) {
  const list = document.querySelector("#adminEditVariants");
  if (!list) return;

  const variants = editableAdminVariants(product);
  list.innerHTML = variants.map((variant, index) => `
    <article class="admin-edit-variant-row" data-admin-edit-variant-row data-variant-id="${variant.id || ""}" data-variant-default="${variant.is_default || index === 0 ? "1" : "0"}">
      <label class="admin-edit-variant-name">
        <span>Размер</span>
        <input type="text" value="${escapeAttribute(variant.name)}" data-admin-edit-variant-name aria-label="Название размера ${index + 1}" placeholder="S, M, L или 30 см">
      </label>
      <label class="admin-edit-variant-price">
        <span>Цена</span>
        <input type="number" inputmode="numeric" min="0" step="1" value="${escapeAttribute(variant.price)}" data-admin-edit-variant-price aria-label="Цена размера ${escapeAttribute(variant.name)}">
      </label>
      <button class="admin-edit-variant-remove" type="button" data-admin-edit-variant-remove aria-label="Удалить размер ${escapeAttribute(variant.name)}" ${variants.length <= 1 ? "disabled" : ""}>×</button>
    </article>`).join("");
}

function setAdminEditorMode(mode) {
  const form = document.querySelector("#adminProductEditForm");
  const confirm = document.querySelector("#adminProductConfirm");
  if (!form || !confirm) return;

  const confirming = mode === "confirm";
  form.hidden = confirming;
  confirm.hidden = !confirming;
}

function populateAdminProductEditor(product, { mode = "edit" } = {}) {
  adminEditorMode = mode;
  adminEditorProductId = Number(product.id);
  adminEditorOriginal = cloneAdminProduct({
    ...product,
    variants: editableAdminVariants(product),
    images: productImages(product),
    isNew: mode === "create"
  });
  adminEditorPendingDraft = null;

  const typeLabel = productTypeLabel(product);
  const createLabel = adminProductTypePreset(product.productType).label.toLowerCase();
  document.querySelector("#adminProductEditorTitle").textContent = mode === "create" ? `Новый ${createLabel}` : product.name;
  document.querySelector("#adminEditPhotoTitle").textContent = product.name || typeLabel;
  document.querySelector("#adminEditImageUrl").value = product.image || product.image_url || productImages(product)[0] || "";
  const imageFileInput = document.querySelector("#adminEditImageFile");
  if (imageFileInput) imageFileInput.value = "";
  document.querySelector("#adminEditName").value = mode === "create" ? "" : (product.name || "");
  document.querySelector("#adminEditDescription").value = product.description || "";
  document.querySelector("#adminEditComposition").value = product.composition || "";
  renderAdminEditorPhoto(product.image || product.image_url || productImages(product)[0] || "", product.name || typeLabel);
  renderAdminEditorVariants(adminEditorOriginal);
  setAdminEditorMode("edit");

  const overlay = document.querySelector("#adminProductEditor");
  overlay.hidden = false;
  document.body.classList.add("is-dialog-open");
  tg?.HapticFeedback?.impactOccurred?.("light");
}

function openAdminProductEditor(productId) {
  const product = getAdminProductById(productId);
  if (!product) {
    showToast("Товар не найден", "error");
    return;
  }

  populateAdminProductEditor(product, { mode: "edit" });
}

function openAdminCreateProductEditor(type) {
  const preset = adminProductTypePreset(type);
  const id = createAdminProductId();
  const product = normalizeAdminProduct({
    id,
    slug: `admin-product-${id}`,
    name: `Новый ${preset.label.toLowerCase()}`,
    category: preset.collection,
    collection: preset.collection,
    productType: preset.productType,
    image: "",
    image_url: "",
    images: [],
    basePrice: 0,
    base_price: 0,
    price: 0,
    min_price: 0,
    description: preset.description,
    composition: preset.composition,
    active: true,
    is_active: true,
    featured: false,
    isFeatured: false,
    is_featured: false,
    featuredPosition: null,
    featured_position: null,
    variants: preset.variants.map((variant, index) => normalizeAdminVariant({
      ...variant,
      id: createAdminVariantId(id, index)
    }, index)),
    imagesCount: 0,
    variantsCount: preset.variants.length,
    createdAt: new Date().toISOString(),
    isCreatedByAdmin: true
  });

  closeAdminProductTypePicker();
  populateAdminProductEditor(product, { mode: "create" });
}

function openAdminProductTypePicker() {
  const overlay = document.querySelector("#adminProductTypePicker");
  if (!overlay) return;
  overlay.hidden = false;
  document.body.classList.add("is-dialog-open");
  tg?.HapticFeedback?.impactOccurred?.("light");
}

function closeAdminProductTypePicker() {
  const overlay = document.querySelector("#adminProductTypePicker");
  if (!overlay) return;
  overlay.hidden = true;
  if (document.querySelector("#adminProductEditor")?.hidden !== false) {
    document.body.classList.remove("is-dialog-open");
  }
}

function closeAdminProductEditor() {
  const overlay = document.querySelector("#adminProductEditor");
  if (!overlay) return;

  overlay.hidden = true;
  document.body.classList.remove("is-dialog-open");
  adminEditorProductId = null;
  adminEditorOriginal = null;
  adminEditorPendingDraft = null;
  adminEditorMode = "edit";
}

function collectAdminEditorDraft() {
  if (!adminEditorOriginal) return null;

  const name = document.querySelector("#adminEditName").value.trim();
  const image = document.querySelector("#adminEditImageUrl").value.trim();
  const description = document.querySelector("#adminEditDescription").value.trim();
  const composition = document.querySelector("#adminEditComposition").value.trim();
  const variantRows = [...document.querySelectorAll("[data-admin-edit-variant-row]")];
  const variants = variantRows.map((row, index) => {
    const nameInput = row.querySelector("[data-admin-edit-variant-name]");
    const priceInput = row.querySelector("[data-admin-edit-variant-price]");
    return normalizeAdminVariant({
      id: row.dataset.variantId ? Number(row.dataset.variantId) : createAdminVariantId(adminEditorProductId, index),
      name: nameInput?.value,
      price: priceInput?.value,
      is_default: row.dataset.variantDefault === "1" || index === 0
    }, index);
  });

  if (!name) {
    showToast("Укажите название товара", "error");
    document.querySelector("#adminEditName")?.focus();
    return null;
  }

  const emptyVariantName = variants.find((variant) => !String(variant.name || "").trim());
  if (emptyVariantName) {
    showToast("Укажите название каждого размера", "error");
    return null;
  }

  const invalidPrice = variants.find((variant) => !Number.isFinite(variant.price) || variant.price < 0);
  if (invalidPrice) {
    showToast("Проверьте цены размеров", "error");
    return null;
  }

  const basePrice = variants.length
    ? Math.min(...variants.map((variant) => variant.price))
    : Math.max(0, Number(adminEditorOriginal.price || adminEditorOriginal.basePrice) || 0);

  return {
    id: adminEditorProductId,
    slug: adminEditorOriginal.slug || `admin-product-${adminEditorProductId}`,
    name,
    category: adminEditorOriginal.category || adminEditorOriginal.collection || productTypeLabel(adminEditorOriginal),
    collection: adminEditorOriginal.collection || adminEditorOriginal.category || productTypeLabel(adminEditorOriginal),
    productType: adminEditorOriginal.productType || "bouquets",
    image,
    image_url: image,
    images: image ? [image] : [],
    description,
    composition,
    variants,
    variantsCount: variants.length,
    imagesCount: image ? 1 : 0,
    active: adminEditorOriginal.active !== false,
    is_active: adminEditorOriginal.active !== false,
    featured: Boolean(adminEditorOriginal.featured),
    isFeatured: Boolean(adminEditorOriginal.featured),
    is_featured: Boolean(adminEditorOriginal.featured),
    featuredPosition: adminEditorOriginal.featuredPosition ?? null,
    featured_position: adminEditorOriginal.featuredPosition ?? null,
    basePrice,
    base_price: basePrice,
    price: basePrice,
    min_price: basePrice,
    createdAt: adminEditorOriginal.createdAt || new Date().toISOString(),
    updatedAt: new Date().toISOString(),
    isCreatedByAdmin: adminEditorMode === "create" || Boolean(adminEditorOriginal.isCreatedByAdmin)
  };
}


function collectAdminEditorVariantsFromForm() {
  const rows = [...document.querySelectorAll("[data-admin-edit-variant-row]")];
  return rows.map((row, index) => {
    const nameInput = row.querySelector("[data-admin-edit-variant-name]");
    const priceInput = row.querySelector("[data-admin-edit-variant-price]");
    return normalizeAdminVariant({
      id: row.dataset.variantId ? Number(row.dataset.variantId) : createAdminVariantId(adminEditorProductId, index),
      name: nameInput?.value || `Размер ${index + 1}`,
      price: priceInput?.value || 0,
      is_default: row.dataset.variantDefault === "1" || index === 0
    }, index);
  });
}

function addAdminEditorVariant() {
  if (!adminEditorOriginal) return;
  const variants = collectAdminEditorVariantsFromForm();
  const nextIndex = variants.length;
  variants.push(normalizeAdminVariant({
    id: createAdminVariantId(adminEditorProductId, nextIndex),
    name: `Размер ${nextIndex + 1}`,
    price: 0,
    is_default: false
  }, nextIndex));
  adminEditorOriginal.variants = variants;
  renderAdminEditorVariants(adminEditorOriginal);
  tg?.HapticFeedback?.selectionChanged?.();
}

function removeAdminEditorVariant(row) {
  if (!adminEditorOriginal || !row) return;
  const rows = [...document.querySelectorAll("[data-admin-edit-variant-row]")];
  if (rows.length <= 1) {
    showToast("Должен остаться хотя бы один размер", "error");
    return;
  }
  const variants = collectAdminEditorVariantsFromForm().filter((_, index) => rows[index] !== row);
  adminEditorOriginal.variants = variants.map((variant, index) => ({
    ...variant,
    is_default: index === 0
  }));
  renderAdminEditorVariants(adminEditorOriginal);
  tg?.HapticFeedback?.selectionChanged?.();
}

function compactText(value) {
  const text = String(value ?? "").replace(/\s+/g, " ").trim();
  return text.length > 94 ? `${text.slice(0, 91)}…` : text || "—";
}

function buildAdminProductChanges(original, draft) {
  const changes = [];
  if (!original || !draft) return changes;

  if (adminEditorMode === "create" || original.isNew) {
    changes.push({ label: "Тип", value: draft.collection || productTypeLabel(draft) });
    changes.push({ label: "Название", value: compactText(draft.name) });
    changes.push({ label: "Фото", value: describeAdminImage(draft.image) });
    changes.push({ label: "Описание", value: compactText(draft.description) });
    changes.push({ label: "Состав", value: compactText(draft.composition) });
    draft.variants.forEach((variant) => {
      changes.push({ label: `Размер ${variant.name}`, value: money(variant.price) });
    });
    return changes;
  }

  if (String(original.name || "").trim() !== draft.name) {
    changes.push({ label: "Название", value: `${compactText(original.name)} → ${compactText(draft.name)}` });
  }

  const originalImage = String(original.image || original.image_url || productImages(original)[0] || "").trim();
  if (originalImage !== draft.image) {
    changes.push({ label: "Фото", value: draft.image ? `Новое фото: ${describeAdminImage(draft.image)}` : "Фото будет очищено" });
  }

  if (String(original.description || "").trim() !== draft.description) {
    changes.push({ label: "Описание", value: compactText(draft.description) });
  }

  if (String(original.composition || "").trim() !== draft.composition) {
    changes.push({ label: "Состав", value: compactText(draft.composition) });
  }

  const originalVariants = editableAdminVariants(original);
  draft.variants.forEach((variant, index) => {
    const oldVariant = originalVariants.find((item) => item.id && variant.id && item.id === variant.id)
      || originalVariants.find((item) => item.name === variant.name)
      || originalVariants[index];
    if (!oldVariant) {
      changes.push({ label: `Новый размер ${variant.name}`, value: money(variant.price) });
      return;
    }
    if (oldVariant.name !== variant.name) {
      changes.push({ label: "Размер", value: `${compactText(oldVariant.name)} → ${compactText(variant.name)}` });
    }
    if (Number(oldVariant.price) !== Number(variant.price)) {
      changes.push({ label: `Цена ${variant.name}`, value: `${money(oldVariant.price || 0)} → ${money(variant.price)}` });
    }
  });

  originalVariants.forEach((oldVariant) => {
    const exists = draft.variants.some((variant) => (
      oldVariant.id && variant.id ? oldVariant.id === variant.id : oldVariant.name === variant.name
    ));
    if (!exists) changes.push({ label: "Удалён размер", value: compactText(oldVariant.name) });
  });

  return changes;
}

function showAdminProductConfirm(draft) {
  const changes = buildAdminProductChanges(adminEditorOriginal, draft);
  const list = document.querySelector("#adminProductChanges");
  if (!list) return;

  if (!changes.length) {
    showToast("Изменений нет");
    return;
  }

  list.innerHTML = changes.map((change) => `
    <article>
      <strong>${escapeHtml(change.label)}</strong>
      <span>${escapeHtml(change.value)}</span>
    </article>`).join("");

  adminEditorPendingDraft = draft;
  setAdminEditorMode("confirm");
  tg?.HapticFeedback?.impactOccurred?.("light");
}

function applyAdminProductDraft(draft) {
  if (!draft || !draft.id) return;

  const isCreatedProduct = adminEditorMode === "create" || draft.isCreatedByAdmin || Boolean(adminEditorOriginal?.isCreatedByAdmin);
  const previousOverride = adminProductOverrides[String(draft.id)] || {};
  adminProductOverrides[String(draft.id)] = {
    ...previousOverride,
    name: draft.name,
    category: draft.category,
    collection: draft.collection,
    productType: draft.productType,
    image: draft.image,
    image_url: draft.image,
    images: draft.images,
    description: draft.description,
    composition: draft.composition,
    variants: draft.variants,
    variantsCount: draft.variantsCount,
    imagesCount: draft.imagesCount,
    basePrice: draft.basePrice,
    base_price: draft.base_price,
    price: draft.price,
    min_price: draft.min_price,
    active: draft.active,
    is_active: draft.is_active,
    updatedAt: draft.updatedAt,
    isCreatedByAdmin: isCreatedProduct
  };
  saveAdminProductOverrides();

  if (isCreatedProduct) {
    upsertAdminCreatedProduct(draft);
  }

  const applyDraftToList = (list) => {
    const normalizedDraft = mergeAdminOverride(normalizeAdminProduct(draft, list.length));
    let found = false;
    const next = list.map((product) => {
      if (Number(product.id) !== Number(draft.id)) return mergeAdminOverride(product);
      found = true;
      return mergeAdminOverride({ ...product, ...normalizedDraft });
    });
    if (!found) next.push(normalizedDraft);
    return next;
  };

  adminProductsCache = applyDraftToList(getAdminProductSource());
  products = applyDraftToList(products);

  renderAdminProductsList();
  renderAllProducts();
  closeAdminProductEditor();
  showToast(isCreatedProduct ? "Товар добавлен" : "Изменения применены", "success");
  tg?.HapticFeedback?.notificationOccurred?.("success");
}

document.querySelectorAll("[data-admin-back]").forEach(btn => {
  btn.addEventListener("click", () => setActivePage("admin", {haptic:true}));
});

document.querySelectorAll("[data-admin-section]").forEach((button) => {
  button.addEventListener("click", () => {
    if (["orders", "products"].includes(button.dataset.adminSection)) return;

    const labels = {
      addons: "Дополнения",
      customers: "Клиенты",
      notifications: "Рассылки",
      analytics: "Аналитика",
      settings: "Настройки"
    };
    const label = labels[button.dataset.adminSection] || "Раздел";
    showToast(`${label}: интерфейс будет добавлен на следующем этапе`);
    tg?.HapticFeedback?.impactOccurred?.("light");
  });
});

const adminProductSearchInput = document.querySelector("#adminProductSearch");
if (adminProductSearchInput) {
  adminProductSearchInput.addEventListener("input", () => {
    adminProductsSearch = adminProductSearchInput.value;
    renderAdminProductsList();
  });
}

document.querySelectorAll("[data-admin-product-filter]").forEach((button) => {
  button.addEventListener("click", () => {
    adminProductsFilter = button.dataset.adminProductFilter || "all";
    document.querySelectorAll("[data-admin-product-filter]").forEach((item) => {
      item.classList.toggle("is-active", item === button);
    });
    renderAdminProductsList();
    tg?.HapticFeedback?.selectionChanged?.();
  });
});

const adminAddProductButton = document.querySelector("#adminAddProductButton");
if (adminAddProductButton) {
  adminAddProductButton.addEventListener("click", () => openAdminProductTypePicker());
}

const adminHeroImageInput = document.querySelector("#adminHeroImageInput");
if (adminHeroImageInput) {
  adminHeroImageInput.addEventListener("input", () => {
    adminHeroImageDraft = adminHeroImageInput.value.trim();
    renderAdminMainHeroPreview(adminHeroImageDraft || defaultMainHeroImage());
  });
}

const adminHeroImageFileInput = document.querySelector("#adminHeroImageFile");
const adminHeroImageButton = document.querySelector("#adminHeroImageButton");
if (adminHeroImageButton) {
  adminHeroImageButton.addEventListener("click", () => {
    adminHeroImageFileInput?.click();
    tg?.HapticFeedback?.impactOccurred?.("light");
  });
}

if (adminHeroImageFileInput) {
  adminHeroImageFileInput.addEventListener("change", () => {
    const file = adminHeroImageFileInput.files?.[0];
    setAdminMainHeroImageFromFile(file);
  });
}

const adminHeroImagePathButton = document.querySelector("#adminHeroImagePathButton");
if (adminHeroImagePathButton) {
  adminHeroImagePathButton.addEventListener("click", () => {
    adminHeroImageInput?.focus({ preventScroll: true });
    adminHeroImageInput?.select?.();
    tg?.HapticFeedback?.impactOccurred?.("light");
  });
}

const adminHeroImageSaveButton = document.querySelector("#adminHeroImageSave");
if (adminHeroImageSaveButton) {
  adminHeroImageSaveButton.addEventListener("click", () => saveAdminMainHeroImageDraft());
}

const adminHeroImageResetButton = document.querySelector("#adminHeroImageReset");
if (adminHeroImageResetButton) {
  adminHeroImageResetButton.addEventListener("click", () => resetAdminMainHeroImage());
}

document.querySelectorAll("[data-admin-type-close]").forEach((button) => {
  button.addEventListener("click", () => closeAdminProductTypePicker());
});

document.querySelectorAll("[data-admin-create-type]").forEach((button) => {
  button.addEventListener("click", () => openAdminCreateProductEditor(button.dataset.adminCreateType));
});

const adminEditImageUrlInput = document.querySelector("#adminEditImageUrl");
if (adminEditImageUrlInput) {
  adminEditImageUrlInput.addEventListener("input", () => {
    renderAdminEditorPhoto(adminEditImageUrlInput.value, document.querySelector("#adminEditName")?.value || "Товар");
  });
}

const adminEditImageFileInput = document.querySelector("#adminEditImageFile");
const adminEditPhotoButton = document.querySelector("#adminEditPhotoButton");
if (adminEditPhotoButton) {
  adminEditPhotoButton.addEventListener("click", () => {
    adminEditImageFileInput?.click();
    tg?.HapticFeedback?.impactOccurred?.("light");
  });
}

if (adminEditImageFileInput) {
  adminEditImageFileInput.addEventListener("change", () => {
    const file = adminEditImageFileInput.files?.[0];
    setAdminEditorImageFromFile(file);
  });
}

const adminEditPhotoPathButton = document.querySelector("#adminEditPhotoPathButton");
if (adminEditPhotoPathButton) {
  adminEditPhotoPathButton.addEventListener("click", () => {
    adminEditImageUrlInput?.focus({ preventScroll: true });
    adminEditImageUrlInput?.select?.();
    tg?.HapticFeedback?.impactOccurred?.("light");
  });
}

const adminEditAddVariantButton = document.querySelector("#adminEditAddVariant");
if (adminEditAddVariantButton) {
  adminEditAddVariantButton.addEventListener("click", () => addAdminEditorVariant());
}

document.addEventListener("click", (event) => {
  const removeVariantButton = event.target.closest("[data-admin-edit-variant-remove]");
  if (!removeVariantButton) return;
  removeAdminEditorVariant(removeVariantButton.closest("[data-admin-edit-variant-row]"));
});

const adminProductEditForm = document.querySelector("#adminProductEditForm");
if (adminProductEditForm) {
  adminProductEditForm.addEventListener("submit", (event) => {
    event.preventDefault();
    const draft = collectAdminEditorDraft();
    if (draft) showAdminProductConfirm(draft);
  });
}

document.querySelectorAll("[data-admin-editor-close]").forEach((button) => {
  button.addEventListener("click", () => closeAdminProductEditor());
});

const adminEditBackToForm = document.querySelector("#adminEditBackToForm");
if (adminEditBackToForm) {
  adminEditBackToForm.addEventListener("click", () => {
    setAdminEditorMode("edit");
    tg?.HapticFeedback?.selectionChanged?.();
  });
}

const adminProductConfirmSave = document.querySelector("#adminProductConfirmSave");
if (adminProductConfirmSave) {
  adminProductConfirmSave.addEventListener("click", () => {
    applyAdminProductDraft(adminEditorPendingDraft);
  });
}

document.addEventListener("click", (event) => {
  const actionButton = event.target.closest("[data-admin-product-action]");
  if (!actionButton) return;

  const product = getAdminProductSource().find((item) => item.id === Number(actionButton.dataset.adminProductId));
  const action = actionButton.dataset.adminProductAction;

  if (action === "edit") {
    openAdminProductEditor(product?.id || actionButton.dataset.adminProductId);
  } else if (action === "featured") {
    toggleAdminProductFeatured(product?.id || actionButton.dataset.adminProductId);
  } else if (action === "active") {
    toggleAdminProductActive(product?.id || actionButton.dataset.adminProductId);
  }
});

document.addEventListener("pointerdown", (event) => {
  const handle = event.target.closest("[data-admin-featured-drag]");
  if (!handle) return;

  const item = handle.closest("[data-admin-featured-id]");
  const list = item?.closest("#adminFeaturedList");
  if (!item || !list) return;

  adminFeaturedDragState = {
    item,
    list,
    pointerId: event.pointerId,
    startX: event.clientX,
    startY: event.clientY,
    dragging: false
  };

  item.setPointerCapture?.(event.pointerId);
  item.classList.add("is-held");
});

document.addEventListener("pointermove", (event) => {
  if (!adminFeaturedDragState || adminFeaturedDragState.pointerId !== event.pointerId) return;

  const state = adminFeaturedDragState;
  const deltaX = Math.abs(event.clientX - state.startX);
  const deltaY = Math.abs(event.clientY - state.startY);

  if (!state.dragging && Math.max(deltaX, deltaY) < 9) return;

  event.preventDefault();
  state.dragging = true;
  state.item.classList.add("is-dragging");
  state.list.classList.add("is-sorting");

  const afterElement = getFeaturedDragAfterElement(state.list, event.clientY);
  if (!afterElement) {
    state.list.appendChild(state.item);
  } else if (afterElement !== state.item.nextElementSibling) {
    state.list.insertBefore(state.item, afterElement);
  }
});

document.addEventListener("pointerup", (event) => {
  if (!adminFeaturedDragState || adminFeaturedDragState.pointerId !== event.pointerId) return;
  finishAdminFeaturedDrag();
});

document.addEventListener("pointercancel", (event) => {
  if (!adminFeaturedDragState || adminFeaturedDragState.pointerId !== event.pointerId) return;
  finishAdminFeaturedDrag({ canceled: true });
});

document.addEventListener("click", (event) => {
  const removeButton = event.target.closest("[data-admin-featured-remove]");
  if (!removeButton) return;

  toggleAdminProductFeatured(removeButton.dataset.adminFeaturedRemove);
});

document.querySelector("#favoriteAction").addEventListener("click", () => {
  previousPage = currentPage();
  setActivePage("favorites", { haptic: true });
});

document.querySelector("#favoritesBack").addEventListener("click", () => setActivePage(bottomPages.includes(previousPage) ? previousPage : "main", { haptic: true }));
document.querySelector("#cartBack").addEventListener("click", () => setActivePage(bottomPages.includes(cartReturnPage) && cartReturnPage !== "cart" ? cartReturnPage : "main", { haptic: true }));
document.querySelector("#notificationAction").addEventListener("click", (event) => {
  event.currentTarget.classList.remove("has-dot");
  tg?.HapticFeedback?.impactOccurred?.("light");
});
const homeSearchInput = document.querySelector("#homeSearch");
const homeSearchClear = document.querySelector("#homeSearchClear");

homeSearchInput.addEventListener("input", renderHome);
homeSearchInput.addEventListener("keydown", (event) => {
  if (event.key !== "Escape" || !homeSearchInput.value) return;
  homeSearchInput.value = "";
  renderHome();
  tg?.HapticFeedback?.impactOccurred?.("light");
});

homeSearchClear.addEventListener("click", () => {
  homeSearchInput.value = "";
  renderHome();
  homeSearchInput.focus({ preventScroll: true });
  tg?.HapticFeedback?.impactOccurred?.("light");
});

const catalogSearchInput = document.querySelector("#catalogSearch");
const catalogSearchClear = document.querySelector("#catalogSearchClear");

catalogSearchInput.addEventListener("input", () => {
  renderCatalog(filterCatalog());
});

catalogSearchInput.addEventListener("keydown", (event) => {
  if (event.key !== "Escape" || !catalogSearchInput.value) return;
  catalogSearchInput.value = "";
  renderCatalog(filterCatalog());
  tg?.HapticFeedback?.impactOccurred?.("light");
});

catalogSearchClear.addEventListener("click", () => {
  catalogSearchInput.value = "";
  renderCatalog(filterCatalog());
  catalogSearchInput.focus({ preventScroll: true });
  tg?.HapticFeedback?.impactOccurred?.("light");
});

document.querySelector("#homeFilterButton").addEventListener("click", () => {
  openCatalogFilter();
});
document.querySelector("#catalogTypeTabs").addEventListener("click", (event) => {
  const button = event.target.closest("[data-catalog-type]");
  if (!button) return;
  appliedCatalogType = button.dataset.catalogType || "all";
  renderCatalog(filterCatalog());
  button.scrollIntoView({
    behavior: "smooth",
    block: "nearest",
    inline: "center"
  });
  tg?.HapticFeedback?.selectionChanged?.();
});

const catalogTypeTabs = document.querySelector("#catalogTypeTabs");
let catalogTypeDrag = null;
let suppressCatalogTypeClick = false;

catalogTypeTabs.addEventListener("pointerdown", (event) => {
  if (event.pointerType !== "mouse" || event.button !== 0) return;
  catalogTypeDrag = {
    pointerId: event.pointerId,
    startX: event.clientX,
    scrollLeft: catalogTypeTabs.scrollLeft,
    moved: false
  };
  catalogTypeTabs.classList.add("is-dragging");
  catalogTypeTabs.setPointerCapture?.(event.pointerId);
});

catalogTypeTabs.addEventListener("pointermove", (event) => {
  if (!catalogTypeDrag || catalogTypeDrag.pointerId !== event.pointerId) return;
  const delta = event.clientX - catalogTypeDrag.startX;
  if (Math.abs(delta) > 4) catalogTypeDrag.moved = true;
  catalogTypeTabs.scrollLeft = catalogTypeDrag.scrollLeft - delta;
});

function finishCatalogTypeDrag(event) {
  if (!catalogTypeDrag || catalogTypeDrag.pointerId !== event.pointerId) return;
  suppressCatalogTypeClick = catalogTypeDrag.moved;
  catalogTypeTabs.classList.remove("is-dragging");
  catalogTypeTabs.releasePointerCapture?.(event.pointerId);
  catalogTypeDrag = null;
  window.setTimeout(() => {
    suppressCatalogTypeClick = false;
  }, 0);
}

catalogTypeTabs.addEventListener("click", (event) => {
  if (!suppressCatalogTypeClick) return;
  event.preventDefault();
  event.stopImmediatePropagation();
}, true);

catalogTypeTabs.addEventListener("pointerup", finishCatalogTypeDrag);
catalogTypeTabs.addEventListener("pointercancel", finishCatalogTypeDrag);

catalogTypeTabs.addEventListener("wheel", (event) => {
  if (Math.abs(event.deltaY) <= Math.abs(event.deltaX)) return;
  catalogTypeTabs.scrollLeft += event.deltaY;
  event.preventDefault();
}, { passive: false });

document.querySelector("[data-open-catalog-picker='sort']").addEventListener("click", openCatalogPicker);

document.querySelectorAll("[data-close-catalog-picker]").forEach((button) => {
  button.addEventListener("click", closeCatalogPicker);
});

document.querySelector("#catalogPickerOptions").addEventListener("click", (event) => {
  const button = event.target.closest("[data-catalog-picker-value]");
  if (!button) return;
  selectCatalogPickerValue(button.dataset.catalogPickerValue);
});

const catalogPriceMinInput = document.querySelector("#catalogPriceMin");
const catalogPriceMaxInput = document.querySelector("#catalogPriceMax");

catalogPriceMinInput.addEventListener("input", () => {
  handleCatalogPriceInput(catalogPriceMinInput);
});
catalogPriceMaxInput.addEventListener("input", () => {
  handleCatalogPriceInput(catalogPriceMaxInput);
});
document.querySelector("#catalogPriceReset").addEventListener("click", resetCatalogPrice);
document.querySelector("#catalogResetAll").addEventListener("click", resetCatalogAll);

document.addEventListener("click", (event) => {
  const button = event.target.closest("[data-empty-action]");
  if (!button) return;

  if (button.dataset.emptyAction === "reset-catalog") {
    resetCatalogAll();
    return;
  }

  if (button.dataset.emptyAction === "open-catalog") {
    setActivePage("search", { haptic: true });
  }
});
document.querySelectorAll("[data-close-filter]").forEach((button) => {
  button.addEventListener("click", closeCatalogFilter);
});
document.querySelectorAll("[data-filter-price]").forEach((button) => {
  button.addEventListener("click", () => {
    pendingCatalogFilter.price = button.dataset.filterPrice;
    syncFilterSheet();
    tg?.HapticFeedback?.selectionChanged?.();
  });
});
document.querySelectorAll("[data-filter-sort]").forEach((button) => {
  button.addEventListener("click", () => {
    pendingCatalogFilter.sort = button.dataset.filterSort;
    syncFilterSheet();
    tg?.HapticFeedback?.selectionChanged?.();
  });
});
document.querySelector("#filterReset").addEventListener("click", resetCatalogFilter);
document.querySelector("#filterApply").addEventListener("click", applyCatalogFilter);
document.querySelector("#detailFavorite").addEventListener("click", (event) => {
  if (!activeProduct) return;
  toggleFavorite(activeProduct.id, event.currentTarget);
});
document.querySelector("#addToCartButton").addEventListener("click", addToCart);
document.querySelector("#checkoutForm").addEventListener("submit", submitOrder);
document.querySelector("#sameRecipient").addEventListener("change", updateRecipientFields);
document.querySelector("#customerName").addEventListener("input", () => document.querySelector("#sameRecipient").checked && updateRecipientFields());
document.querySelector("#customerPhone").addEventListener("input", () => document.querySelector("#sameRecipient").checked && updateRecipientFields());
document.querySelectorAll('input[name="delivery_type"]').forEach((input) => input.addEventListener("change", updateDeliveryFields));
document.querySelectorAll('[data-delete-cancel]').forEach((button) => button.addEventListener("click", closeDeleteConfirm));
confirmDeleteButton.addEventListener("click", confirmDelete);

cartContentElement.addEventListener("pointerdown", (event) => {
  if (event.pointerType === "mouse" && event.button !== 0) return;
  if (event.target.closest("button, input, select, textarea, a, label")) return;
  const surface = event.target.closest("[data-swipe-surface]");
  const wrapper = surface?.closest(".cart-swipe");
  if (!surface || !wrapper) return;
  swipeGesture = {
    wrapper,
    surface,
    pointerId: event.pointerId,
    startX: event.clientX,
    startY: event.clientY,
    baseOffset: wrapper.classList.contains("is-open") ? -SWIPE_ACTION_WIDTH : 0,
    horizontal: null,
    moved: false
  };
  surface.setPointerCapture?.(event.pointerId);
});

cartContentElement.addEventListener("pointermove", (event) => {
  if (!swipeGesture || swipeGesture.pointerId !== event.pointerId) return;
  const dx = event.clientX - swipeGesture.startX;
  const dy = event.clientY - swipeGesture.startY;
  if (swipeGesture.horizontal === null) {
    if (Math.abs(dx) < 6 && Math.abs(dy) < 6) return;
    swipeGesture.horizontal = Math.abs(dx) > Math.abs(dy) * 1.15;
    if (!swipeGesture.horizontal) return;
  }
  if (!swipeGesture.horizontal) return;
  event.preventDefault();
  swipeGesture.moved = true;
  const offset = Math.max(-SWIPE_ACTION_WIDTH, Math.min(0, swipeGesture.baseOffset + dx));
  setSwipePosition(swipeGesture.wrapper, offset, false);
});

function endSwipeGesture(event) {
  if (!swipeGesture || swipeGesture.pointerId !== event.pointerId) return;
  const offset = Number(swipeGesture.wrapper.dataset.swipeOffset || 0);
  if (swipeGesture.moved) suppressCartClickUntil = Date.now() + 160;
  finishSwipe(offset < -SWIPE_ACTION_WIDTH * 0.44);
  swipeGesture = null;
}
cartContentElement.addEventListener("pointerup", endSwipeGesture);
cartContentElement.addEventListener("pointercancel", endSwipeGesture);

const detailGalleryTrack = document.querySelector("#detailGalleryTrack");

detailGalleryTrack.addEventListener("scroll", () => {
  if (galleryScrollFrame) cancelAnimationFrame(galleryScrollFrame);
  galleryScrollFrame = requestAnimationFrame(() => {
    const width = detailGalleryTrack.clientWidth;
    if (!width) return;
    updateGalleryState(Math.round(detailGalleryTrack.scrollLeft / width));
  });
}, { passive: true });

document.querySelector("#galleryPrev").addEventListener("click", () => {
  updateGalleryState(currentGalleryIndex - 1, { scroll: true });
  tg?.HapticFeedback?.selectionChanged?.();
});

document.querySelector("#galleryNext").addEventListener("click", () => {
  updateGalleryState(currentGalleryIndex + 1, { scroll: true });
  tg?.HapticFeedback?.selectionChanged?.();
});

document.querySelector("#shareProduct").addEventListener("click", async () => {
  if (!activeProduct) return;
  const text = `${activeProduct.name} — ${money(activeProduct.basePrice)}`;
  try {
    if (navigator.share) await navigator.share({ title: activeProduct.name, text });
    else await navigator.clipboard?.writeText(text);
  } catch {
    // Пользователь отменил системное меню.
  }
});

document.addEventListener("click", (event) => {
  if (Date.now() < suppressCartClickUntil && event.target.closest("[data-swipe-surface]")) {
    event.preventDefault();
    return;
  }
  const tappedSwipeSurface = event.target.closest("[data-swipe-surface]");
  if (openSwipeElement && tappedSwipeSurface && tappedSwipeSurface.closest(".cart-swipe") === openSwipeElement && !event.target.closest("button")) {
    closeOpenSwipe();
    return;
  }
  if (openSwipeElement && !event.target.closest(".cart-swipe")) closeOpenSwipe();
  const favorite = event.target.closest("[data-favorite-id]");
  if (favorite) {
    event.stopPropagation();
    toggleFavorite(
      Number(favorite.dataset.favoriteId),
      favorite
    );
    return;
  }

  const opener = event.target.closest("[data-open-product], [data-product-id]");
  if (opener && !event.target.closest("button[data-favorite-id]")) {
    openProduct(Number(opener.dataset.openProduct || opener.dataset.productId));
    return;
  }

  if (event.target.closest("[data-close-product]")) {
    closeProduct();
    return;
  }

  const galleryDot = event.target.closest("[data-gallery-index]");
  if (galleryDot) {
    updateGalleryState(Number(galleryDot.dataset.galleryIndex), {
      scroll: true
    });
    tg?.HapticFeedback?.selectionChanged?.();
    return;
  }

  const size = event.target.closest("[data-size]");
  if (size) {
    selectedSize = size.dataset.size;
    selectedVariantId = size.dataset.variantId ? Number(size.dataset.variantId) : null;
    document.querySelectorAll(".size-option").forEach((button) => button.classList.toggle("is-active", button === size));
    updateDetailPrice({ animate: true });
    tg?.HapticFeedback?.selectionChanged?.();
    return;
  }

  const minus = event.target.closest("[data-cart-minus]");
  if (minus) {
    changeCartQuantity(Number(minus.dataset.cartMinus), -1);
    return;
  }

  const plus = event.target.closest("[data-cart-plus]");
  if (plus) {
    changeCartQuantity(Number(plus.dataset.cartPlus), 1);
    return;
  }

  const remove = event.target.closest("[data-cart-remove]");
  if (remove) {
    openDeleteConfirm(Number(remove.dataset.cartRemove));
    return;
  }

  if (event.target.closest("[data-empty-search]")) {
    setActivePage("search", { haptic: true });
  }
});

document.addEventListener("keydown", (event) => {
  if (event.key === "Escape" && !document.querySelector("#adminProductEditor")?.hidden) {
    closeAdminProductEditor();
    return;
  }
  if (event.key === "Escape" && !document.querySelector("#adminProductTypePicker")?.hidden) {
    closeAdminProductTypePicker();
    return;
  }
  if (event.key === "Escape" && !document.querySelector("#catalogPickerOverlay").hidden) {
    closeCatalogPicker();
    return;
  }
  if (event.key === "Escape" && !document.querySelector("#filterOverlay").hidden) {
    closeCatalogFilter();
    return;
  }
  if (event.key !== "Escape") return;
  if (!deleteConfirm.hidden) {
    closeDeleteConfirm();
    return;
  }
  if (!document.querySelector("#productOverlay").hidden) closeProduct();
});

initTelegram();
applyTelegramUser();
setDefaultFormValues();
applyMainHeroImage();
products = appendAdminCreatedProducts(products).map((product) => mergeAdminOverride(product));
renderAllProducts();
renderCart();
prepareReveal(document);
updateCartIndicator();
setActivePage(sessionStorage.getItem("bloombox-active-page") || "main");
hydrateProductsFromApi();
loadUserSession();

document.querySelectorAll("[data-admin-section]").forEach((button) => {
  button.addEventListener("click", () => {
    if (button.dataset.adminSection === "orders") setActivePage("admin-orders", {haptic:true});
    if (button.dataset.adminSection === "products") setActivePage("admin-products", {haptic:true});
  });
});
document.querySelectorAll("[data-admin-back]").forEach((button) => {
  button.addEventListener("click", () => setActivePage("admin", {haptic:true}));
});
