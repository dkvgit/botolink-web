// D:\aRabota\TelegaBoom\030_mylinkspace\templates\base\base.js

let currentToastTimeout = null;
let currentModalId = null;

// Инициализация при загрузке страницы
document.addEventListener('DOMContentLoaded', function() {
    console.log("Base JS: Инициализация...");

    // 1. Функция навигации Stories (теперь со ВСЕЙ логикой внутри)
    function initStoriesNavigation() {
        const container = document.getElementById('stories-scroll-container');
        const wrapper = document.getElementById('stories-wrapper');
        const items = document.querySelectorAll('.story-item');

        if (!container || !wrapper) return;

        // Логика стрелок
        const updateStoryArrows = () => {
            const tolerance = 5;
            const maxScroll = container.scrollWidth - container.clientWidth;
            if (container.scrollLeft > tolerance) wrapper.classList.add('can-scroll-left');
            else wrapper.classList.remove('can-scroll-left');

            if (maxScroll > tolerance && (container.scrollLeft + container.clientWidth) < (maxScroll - tolerance)) {
                wrapper.classList.add('can-scroll-right');
            } else {
                wrapper.classList.remove('can-scroll-right');
            }
        };

        // КЛИК ПО ИКОНКЕ (Возвращаем плавность)
        items.forEach(item => {
            item.addEventListener('click', function(e) {
                const targetId = this.getAttribute('href');
                if (targetId && targetId.startsWith('#')) {
                    e.preventDefault(); // Отключаем резкий прыжок
                    const targetEl = document.querySelector(targetId);
                    if (targetEl) {
                        // Плавный скролл страницы вниз к категории
                        const offset = 110;
                        const targetPos = targetEl.getBoundingClientRect().top + window.pageYOffset - offset;
                        window.scrollTo({ top: targetPos, behavior: 'smooth' });
                    }
                }

                // Подсветка активной
                items.forEach(i => i.classList.remove('active-story'));
                this.classList.add('active-story');

                // Центрирование иконки в самой ленте
                const centerPos = this.offsetLeft - (container.offsetWidth / 2) + (this.offsetWidth / 2);
                container.scrollTo({ left: centerPos, behavior: 'smooth' });
            });
        });

        // Запуск и события прокрутки
        updateStoryArrows();
        container.addEventListener('scroll', updateStoryArrows, { passive: true });
        window.addEventListener('resize', updateStoryArrows);

        // Прокрутка колесиком
        container.addEventListener('wheel', (e) => {
            e.preventDefault();
            container.scrollLeft += e.deltaY;
        }, { passive: false });
    }

    // 2. Обработка кликов по карточкам ссылок (Модалки)
        const cards = document.querySelectorAll('.link-card');
        cards.forEach(card => {
            card.addEventListener('click', function(e) {
                // Если кликнули по кнопке-стрелке внутри или это прямая ссылка (target="_blank")
                if (e.target.closest('.link-arrow-btn') || this.getAttribute('target') === '_blank') {
                    return; // Ничего не делаем, даем браузеру открыть ссылку
                }

                const linkId = this.getAttribute('data-link-id');
                const modalId = 'modal_' + linkId;

                // Если это НЕ прямая ссылка, отменяем переход и открываем модалку
                e.preventDefault();
                e.stopPropagation();

                if (typeof window.openModal === 'function') {
                    openModal(modalId);
                }
            });
        });

    // 3. Вызов навигации
    initStoriesNavigation();
});



// === ЛОГИКА НАВИГАЦИИ (STORIES) ===
function initStoriesNavigation() {
    const container = document.getElementById('stories-scroll-container');
    const items = document.querySelectorAll('.story-item');
    const wrapper = document.getElementById('stories-wrapper');

    if (!container) return;

    // --- А. Перемотка колесиком мыши (для ПК) ---
    container.addEventListener('wheel', (evt) => {
        evt.preventDefault();
        container.scrollLeft += evt.deltaY;
    }, { passive: false });

    // --- Б. Клик по иконке (центрование + активный класс) ---
    items.forEach(item => {
        item.addEventListener('click', function(e) {
            // Убираем активный класс у всех
            items.forEach(i => i.classList.remove('active-story'));
            this.classList.add('active-story');

            // Центрирование
            const containerWidth = container.offsetWidth;
            const itemOffset = this.offsetLeft;
            const itemWidth = this.offsetWidth;

            container.scrollTo({
                left: itemOffset - (containerWidth / 2) + (itemWidth / 2),
                behavior: 'smooth'
            });
        });
    });

    // --- В. Синхронизация при скролле страницы (Intersection Observer) ---
    const observerOptions = {
        root: null,
        rootMargin: '-15% 0px -75% 0px', // Зона срабатывания
        threshold: 0
    };

    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                const id = entry.target.getAttribute('id')?.replace('cat-', '');
                if (!id) return;

                const activeItem = document.querySelector(`.story-item[data-category="${id}"]`);
                if (activeItem) {
                    items.forEach(i => i.classList.remove('active-story'));
                    activeItem.classList.add('active-story');

                    // Опционально: центрировать иконку при скролле страницы
                    /*
                    container.scrollTo({
                        left: activeItem.offsetLeft - (container.offsetWidth / 2) + (activeItem.offsetWidth / 2),
                        behavior: 'smooth'
                    });
                    */
                }
            }
        });
    }, observerOptions);

    document.querySelectorAll('.link-group').forEach(section => observer.observe(section));

    // --- Г. Управление стрелками (Двусторонняя навигация) ---
    // Вызываем сразу и вешаем на события
    updateStoryArrows();
    window.addEventListener('resize', updateStoryArrows);
    container.addEventListener('scroll', updateStoryArrows, { passive: true });
}


function openBankModal(element) {
    const linkId = element.getAttribute('data-link-id');
    const modalId = 'modal_' + linkId;
    const modal = document.getElementById(modalId);

    if (modal) {
        // 1. Запоминаем, где мы сейчас находимся
        const scrollY = window.scrollY;

        // 2. Показываем модалку
        modal.style.setProperty('display', 'flex', 'important');
        setTimeout(() => modal.classList.add('active'), 10);

        // 3. Блокируем скролл БЕЗ прыжков (используем метод с фиксированной позицией)
        // Вычисляем ширину скроллбара, чтобы страница не дергалась вправо
        const scrollBarWidth = window.innerWidth - document.documentElement.clientWidth;

        document.body.style.paddingRight = `${scrollBarWidth}px`;
        document.body.style.position = 'fixed';
        document.body.style.top = `-${scrollY}px`;
        document.body.style.width = '100%';
        document.body.style.overflowY = 'hidden';
    }
}


// Функция для копирования конкретной строки (IBAN, SWIFT и т.д.)
function copyField(element, fieldName) {
    const text = element.getAttribute('data-copy-value');
    if (!text) return;

    navigator.clipboard.writeText(text).then(() => {
        showToast(`✅ ${fieldName} скопирован`);
        element.style.transform = 'scale(0.92)';
        setTimeout(() => element.style.transform = '', 100);
    });
}

// Универсальное копирование всех реквизитов из модалки
function copyFullBankDetails(linkId) {
    const modal = document.getElementById(`modal_${linkId}`);
    if (!modal) return;

    let result = "";
    const title = modal.querySelector('.link-title')?.innerText || "Bank Details";
    result += `🏦 ${title}\n` + `─`.repeat(20) + `\n`;

    // Ищем все пары Метка: Значение (по твоим классам из шаблона)
    const rows = modal.querySelectorAll('.detail-row');
    rows.forEach(row => {
        const label = row.querySelector('.detail-label')?.innerText;
        const value = row.querySelector('.detail-value')?.innerText;
        if (label && value && value !== 'не указано') {
            result += `${label} ${value}\n`;
        }
    });

    copyText(result || modal.innerText.trim());
}


// === ФУНКЦИИ ДЛЯ КОПИРОВАНИЯ ===

function copyText(text, btn) {
    if (!text) return;

    const performCopy = () => {
        // Выводим весь текст целиком без обрезки
        showToast(`✨ Скопировано: ${text}`);

        if (btn) {
            const icon = btn.querySelector('i');
            if (icon) {
                const originalClass = icon.className;
                icon.className = 'fas fa-check';
                btn.style.color = '#10b981'; // Зеленый цвет успеха

                setTimeout(() => {
                    icon.className = originalClass;
                    btn.style.color = '';
                }, 2000);
            }
        }
    };

    if (navigator.clipboard && navigator.clipboard.writeText) {
        navigator.clipboard.writeText(text).then(performCopy).catch(err => {
            fallbackCopyText(text, performCopy);
        });
    } else {
        fallbackCopyText(text, performCopy);
    }
}




function fallbackCopyText(text, callback) {
    const textarea = document.createElement('textarea');
    textarea.value = text;
    textarea.style.position = 'fixed'; // Чтобы не дергался скролл
    document.body.appendChild(textarea);
    textarea.select();
    try {
        document.execCommand('copy');
        if (callback) callback();
    } catch (err) {
        console.error('Критическая ошибка копирования:', err);
    }
    document.body.removeChild(textarea);
}


// === БАНКОВСКИЕ ФУНКЦИИ ===
function copyAllBankDetails(linkId) {
    const modal = document.getElementById(`modal_${linkId}`);
    if (!modal) return;

    let textToCopy = '';

    // Заголовок
    const title = modal.querySelector('.modal-content span[style*="font-size:1.2rem"]');
    if (title) {
        textToCopy += title.textContent + '\n';
        // textToCopy += '─'.repeat(20) + '\n\n';
    }

    // Собираем все поля
    const rows = modal.querySelectorAll('div[style*="justify-content:space-between"]');

    rows.forEach(row => {
        const labelSpan = row.querySelector('span[style*="color:#6c757d"]');
        const valueDiv = row.querySelector('div[style*="justify-content:flex-end"]');
        const valueSpan = valueDiv ? valueDiv.querySelector('span[style*="color:#003366"]') : null;

        if (labelSpan && valueSpan && valueSpan.textContent !== 'не указано') {
            textToCopy += labelSpan.textContent + ' ' + valueSpan.textContent + '\n';
        }
    });

    if (textToCopy) {
        copyText(textToCopy);
    } else {
        copyText(modal.innerText.trim());
    }
}

/**
 * Копирует данные карты USA (адаптировано под общую структуру)
 * Сейчас работает идентично copyAllBankDetails, так как HTML у них одинаковый
 */
function copyAllUSACardDetails(linkId) {
    // Просто вызываем универсальную функцию, так как структура HTML единая
    copyAllBankDetails(linkId);
}

/**
 * Переключение табов (Валюты/Сети) внутри крипто-модалки.
 * ВНИМАНИЕ: Эта функция сработает только если ты используешь шаблон
 * base_modal_crypto.html с табами. В текущем простом HTML она ничего не сделает.
 */
function switchCurrencyTab(linkId, tabIndex) {
    const modal = document.getElementById(`modal_${linkId}`);
    if (!modal) return;

    const targetIdx = parseInt(tabIndex);
    if (isNaN(targetIdx)) return;

    // Ищем кнопки табов (если они есть в шаблоне)
    const tabs = modal.querySelectorAll('.currency-tab');
    const contents = modal.querySelectorAll('.currency-tab-content');

    // Если табов нет в DOM (простая модалка), выходим
    if (tabs.length === 0 && contents.length === 0) {
        console.log('Табы не найдены, используется простой шаблон.');
        return;
    }

    // Переключаем классы active
    tabs.forEach((tab, i) => {
        if (i === targetIdx) tab.classList.add('active');
        else tab.classList.remove('active');
    });

    contents.forEach((content, i) => {
        if (i === targetIdx) {
            content.classList.add('active');
            content.style.display = 'block'; // Принудительно показываем

            // Генерируем QR для активного таба
            const qrContainer = content.querySelector('.auto-qr');
            if (qrContainer && qrContainer.innerHTML.trim() === '') {
                generateQRCodes(qrContainer);
            }
        } else {
            content.classList.remove('active');
            content.style.display = 'none'; // Скрываем
        }
    });
}

// // base.js



// === TOAST УВЕДОМЛЕНИЯ ===
window.showToast = function(message, type = 'success', event = null) {
    let toast = document.getElementById('toast');

    if (!toast) {
        toast = document.createElement('div');
        toast.id = 'toast';
        document.body.appendChild(toast);
    }

    if (typeof currentToastTimeout !== 'undefined' && currentToastTimeout) {
        clearTimeout(currentToastTimeout);
    }

    // УБРАЛИ ОБРЕЗКУ: Теперь используем полный message
    toast.textContent = (type === 'copy' ? 'Скопировано: ' : '') + message;

    toast.className = 'toast ' + type;

    if (event && event.clientX) {
        toast.style.position = 'fixed';
        toast.style.left = event.clientX + 'px';
        toast.style.top = event.clientY + 'px';
        toast.style.bottom = 'auto';
        toast.style.transform = 'translate(-50%, -30px)';
    } else {
        toast.style.position = 'fixed';
        toast.style.left = '50%';
        toast.style.bottom = '30px';
        toast.style.top = 'auto';
        toast.style.transform = 'translateX(-50%)';
    }

    toast.classList.remove('hidden');
    setTimeout(() => toast.classList.add('show'), 10);

    window.currentToastTimeout = setTimeout(() => {
        toast.classList.remove('show');
        setTimeout(() => toast.classList.add('hidden'), 300);
    }, 2000);
};

// === ГЕНЕРАЦИЯ И РАБОТА С QR ===
function generateQRCodes(scopeElement) {
    const container = scopeElement || document;
    let qrElements = container.classList && container.classList.contains('auto-qr')
                     ? [container]
                     : container.querySelectorAll('.auto-qr');

    if (typeof QRCode === 'undefined') return;

    qrElements.forEach(qrBox => {
        const text = qrBox.getAttribute('data-qr-text');
        const iconSrc = qrBox.getAttribute('data-qr-icon');

        if (text && text.length > 2) {
            qrBox.innerHTML = '';

            new QRCode(qrBox, {
                text: text,
                // Рисуем в 4 раза крупнее для четкости (Retina-эффект)
                width: 640,
                height: 640,
                colorDark: "#000000",
                colorLight: "#ffffff",
                correctLevel: QRCode.CorrectLevel.H,

                // Настройки логотипа
                logo: iconSrc,
                logoWidth: 160, // Пропорционально размеру 640
                logoHeight: 160,
                logoBackgroundColor: '#ffffff',
                logoBackgroundTransparent: false,

                // Важно для качества:
                quietZone: 20,
                version: 0,

                onRenderingEnd: function(opts, dataURL) {
                    // После рендера находим canvas/img и заставляем их сжаться до 160px в браузере
                    const finalElement = qrBox.querySelector('canvas') || qrBox.querySelector('img');
                    if (finalElement) {
                        finalElement.style.width = '160px';
                        finalElement.style.height = '160px';
                        finalElement.style.display = 'block';
                    }
                    qrBox.style.opacity = '1';
                }
            });
        }
    });
}


// === ТРЕКИНГ ===




// === QR КОДЫ ===
function saveQR(imagePath) {
    if (!imagePath) {
        showToast('❌ QR-код не найден');
        return;
    }

    fetch(imagePath)
        .then(response => response.blob())
        .then(blob => {
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = 'qr-code.png';
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
            document.body.removeChild(a);
            showToast('✅ QR-код сохранен');
        })
        .catch(() => {
            window.open(imagePath, '_blank');
            showToast('📱 QR-код открыт в новой вкладке');
        });
}

function shareQR(imagePath, title) {
    if (!imagePath) {
        showToast('❌ QR-код не найден');
        return;
    }

    if (navigator.share) {
        fetch(imagePath)
            .then(response => response.blob())
            .then(blob => {
                const file = new File([blob], 'qr-code.png', {type: 'image/png'});
                navigator.share({
                    title: title,
                    text: 'QR-код для оплаты',
                    files: [file]
                }).catch(() => {
                });
            }).catch(() => {
            copyText(imagePath);
            showToast('🔗 Ссылка на QR-код скопирована');
        });
    } else {
        saveQR(imagePath);
    }
}












function saveQRFromContainer(containerId) {
    const container = document.getElementById(containerId);
    if (!container) return;

    const canvas = container.querySelector('canvas');
    if (!canvas) {
        showToast('❌ QR-код еще не загружен');
        return;
    }

    const link = document.createElement('a');
    link.href = canvas.toDataURL("image/png");
    link.download = 'qr-code.png';
    link.click();
    showToast('✅ QR-код сохранен');
}

// Шеринг QR из контейнера
async function shareQRFromContainer(containerId, title) {
    const container = document.getElementById(containerId);
    if (!container) return;

    const canvas = container.querySelector('canvas');
    if (!canvas) {
        showToast('❌ QR-код еще не загружен');
        return;
    }

    canvas.toBlob(async (blob) => {
        if (!blob) return;
        const file = new File([blob], 'qr-code.png', {type: 'image/png'});

        if (navigator.share && navigator.canShare({files: [file]})) {
            try {
                const address = container.getAttribute('data-address') || container.getAttribute('data-qr-text');

                await navigator.share({
                    files: [file],
                    title: title,
                    // УБРАЛИ substring(0, 20). Теперь адрес в подписи будет полным.
                    text: address ? `Реквизиты: ${address}` : title
                });
            } catch (err) {
                console.log('Шеринг отменен');
            }
        } else {
            saveQRFromContainer(containerId);
        }
    }, 'image/png');
}


// Трекинг кликов (заглушка, если нужно)
function trackClick(linkId) {
    if (!linkId || linkId === 'None') return;
    // fetch(`/click/${linkId}`, { method: 'GET', keepalive: true }).catch(console.error);
}

// === ТРЕКИНГ ===
function trackDetailsClick(linkId) {
    if (!linkId || linkId === 'None') return;
    fetch(`/click/${linkId}`, {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({type: 'details'})
    }).catch(e => console.error('Stat error:', e));
}


// // base.js

// // base.js

function generateQRCode(containerId, text) {
    const container = document.getElementById(containerId);
    if (!container) return;

    // Очищаем контейнер перед новой отрисовкой
    container.innerHTML = '';

    try {
        new QRCode(container, {
            text: text,
            width: 160,
            height: 160,
            colorDark: "#000000",
            colorLight: "#ffffff",
            correctLevel: QRCode.CorrectLevel.H // Максимальная избыточность для сканирования с лого
        });
    } catch (e) {
        console.error("Ошибка генерации QR:", e);
    }
}


// ============================================================
// === МОДАЛЬНЫЕ ОКНА (ОТКРЫТИЕ / ЗАКРЫТИЕ) ===================
// ============================================================

// Функция открытия модалки
// Функция открытия модалки
// Переменная для хранения позиции скролла (глобально в файле)
let lastScrollY = 0;

window.openModal = function(modalId, event) {
    if (event) {
        if (typeof event.preventDefault === 'function') event.preventDefault();
        if (typeof event.stopPropagation === 'function') event.stopPropagation();
    }

    // Если ID битый или это системное исключение (86) — выходим
    if (!modalId || modalId === 'modal_86' || modalId.includes('undefined')) {
        return;
    }

    const modal = document.getElementById(modalId);

    // Если модалки нет в HTML — молча выходим без ошибок в консоли
    if (!modal) {
        return;
    }

    // Закрываем другие активные модалки перед открытием новой
    document.querySelectorAll('.modal-overlay.active').forEach(m => {
        m.classList.remove('active');
        // Ожидаем завершения анимации исчезновения (0.3s)
        setTimeout(() => { m.style.display = 'none'; }, 300);
    });

    // Блокируем скролл страницы
    document.body.classList.add('modal-open');

    // Сначала display, потом анимация через класс active
    modal.style.display = 'flex';

    setTimeout(() => {
        modal.classList.add('active');

        // Генерируем QR-коды, если внутри есть нужный контейнер
        const hasQR = modal.querySelector('.auto-qr');
        if (hasQR && typeof generateQRCodes === 'function') {
            generateQRCodes(modal);
        }
    }, 50);
}

window.closeModal = function(modalId) {
    // Если ID нет — закрываем текущую активную
    const modal = modalId ? document.getElementById(modalId) : document.querySelector('.modal-overlay.active');

    if (modal) {
        modal.classList.remove('active');

        // Ждем 300мс (время анимации), прежде чем скрыть элемент из видимости
        setTimeout(() => {
            modal.style.display = 'none';

            // Проверяем, не осталось ли других открытых окон
            const activeModals = document.querySelectorAll('.modal-overlay.active');

            if (activeModals.length === 0) {
                // Если всё закрыто — возвращаем скролл основной странице
                document.body.classList.remove('modal-open');
                document.body.style.overflow = '';
            }
        }, 300);
    }
}


function finishClose(modalElement) {
    modalElement.classList.remove('active');

    setTimeout(() => {
        modalElement.style.display = 'none';

        // Если больше нет активных модалок
        if (document.querySelectorAll('.modal-overlay.active').length === 0) {
            // 1. Достаем сохраненное число из style.top (убираем минус и "px")
            const scrollY = Math.abs(parseInt(document.body.style.top || '0'));

            // 2. Сбрасываем стили
            document.body.classList.remove('modal-open');
            document.body.style.top = '';

            // 3. Мгновенно возвращаем скролл на место
            window.scrollTo(0, scrollY);
        }
    }, 300);
}

// Закрытие по клику на фон
document.addEventListener('click', function(e) {
    if (e.target.classList.contains('modal-overlay')) {
        closeModal(e.target.id);
    }
});

window.copyText = function(text, event) {
    if (!text) return;

    // Останавливаем всплытие, чтобы клик не триггерил закрытие модалки или другие события
    if (event) {
        if (typeof event.preventDefault === 'function') event.preventDefault();
        if (typeof event.stopPropagation === 'function') event.stopPropagation();
    }

    const handleSuccess = () => {
        if (typeof window.showToast === 'function') {
            window.showToast(text, 'copy', event);
        }
    };

    if (navigator.clipboard && window.isSecureContext) {
        navigator.clipboard.writeText(text)
            .then(handleSuccess)
            .catch(() => fallbackCopy(text));
    } else {
        fallbackCopy(text);
    }

    function fallbackCopy(textToCopy) {
        const input = document.createElement('input');
        input.value = textToCopy;
        input.style.position = 'fixed';
        input.style.left = '-9999px';
        document.body.appendChild(input);
        input.select();
        try {
            document.execCommand('copy');
            handleSuccess();
        } catch (err) {
            console.error('Copy fallback failed', err);
        }
        document.body.removeChild(input);
    }
};


// Функция сохранения QR-кода как изображения
window.saveQR = function(canvasId) {
    // Находим canvas внутри блока с QR
    const container = document.getElementById(canvasId);
    const canvas = container ? container.querySelector('canvas') : null;

    if (!canvas) {
        showToast('QR-код еще не загружен', 'error');
        return;
    }

    const link = document.createElement('a');
    link.download = 'qr_code.png';
    link.href = canvas.toDataURL('image/png');
    link.click();

};

// Функция "Поделиться" (работает в мобильных браузерах и Safari)
window.shareLink = function(url, title) {
    if (navigator.share) {
        navigator.share({
            title: title,
            url: url
        }).catch(console.error);
    } else {
        // Если браузер не поддерживает Share API (например, старый Chrome на ПК)
        // Просто копируем ссылку и уведомляем юзера
        navigator.clipboard.writeText(url).then(() => {
            showToast('Ссылка скопирована (Share не поддерживается)', 'success');
        });
    }
};

function handleLinkClick(element, event) {
    const copyTextValue = element.getAttribute('data-copy-text');
    const linkId = element.getAttribute('data-link-id');

    if (copyTextValue) {
        // Если есть текст для копирования — копируем
        copyText(copyTextValue, element);
    } else if (linkId) {
        // Если нет текста для копирования — открываем модалку
        openModal('modal_' + linkId, event);
    }
}

// Исправленная функция: теперь имя совпадает с onclick="downloadQR(...)"
window.downloadQR = function(id) {
    // Добавляем префикс qr_, так как в HTML у тебя id="qr_39"
    const container = document.getElementById('qr_' + id);
    const canvas = container ? container.querySelector('canvas') : null;

    if (!canvas) {
        if (typeof showToast === 'function') {
            showToast('QR-код еще не готов', 'error');
        } else {
            alert('QR-код еще не загружен');
        }
        return;
    }

    const link = document.createElement('a');
    link.download = `qr_code_${id}.png`;
    link.href = canvas.toDataURL('image/png');
    document.body.appendChild(link); // Важно для некоторых браузеров
    link.click();
    document.body.removeChild(link);
};