// D:\aRabota\TelegaBoom\030_mylinkspace\templates\base\base.js

let currentToastTimeout = null;
let currentModalId = null;

// Инициализация при загрузке страницы
document.addEventListener('DOMContentLoaded', function () {
    console.log('base.js loaded');

    // Добавляем обработчики для закрытия модальных окон по клику на фон
    document.querySelectorAll('.modal-overlay').forEach(overlay => {
        overlay.addEventListener('click', function (e) {
            if (e.target === this) {
                closeModal(this.id);
            }
        });
    });

    // Обработчик для кнопки "Назад" браузера
    window.addEventListener('popstate', function (event) {
        if (currentModalId) {
            closeModal(currentModalId);
        }
    });

    // Обработчик для клавиши Escape
    document.addEventListener('keydown', function (e) {
        if (e.key === 'Escape' && currentModalId) {
            closeModal(currentModalId);
        }
    });
});

// === ФУНКЦИИ ДЛЯ МОДАЛЬНЫХ ОКОН ===
function openModal(event, id) {
    if (event) event.preventDefault();

    const modalId = 'modal_' + id;
    const modal = document.getElementById(modalId);

    if (!modal) {
        console.log('Модалка не найдена:', modalId);
        return;
    }

    modal.classList.add('active');

    // ВЫЗОВ ГЕНЕРАЦИИ QR-КОДОВ
    generateQRCodes(modal);

    document.body.style.overflow = 'hidden';
    currentModalId = modalId;

    // Добавляем в историю браузера
    history.pushState({modal: modalId}, '');

    // Отправляем статистику просмотра модалки
    trackDetailsClick(id);
}


// === ГЕНЕРАЦИЯ И СОХРАНЕНИЕ АВТО-QR ===
// ГДЕ: Добавь эти две функции в самый конец файла base.js

function generateQRCodes(modalElement) {
    // Ищем все блоки с классом auto-qr внутри открытой модалки
    const qrContainers = modalElement.querySelectorAll('.auto-qr');

    qrContainers.forEach(container => {
        const address = container.getAttribute('data-address');

        // Генерируем только если есть адрес и контейнер еще пустой
        if (address && address.trim() !== '' && container.innerHTML.trim() === '') {
            try {
                new QRCode(container, {
                    text: address,
                    width: 160,
                    height: 160,
                    colorDark: "#000000",
                    colorLight: "#ffffff",
                    correctLevel: QRCode.CorrectLevel.H
                });
                console.log('QR generated for:', address);
            } catch (err) {
                console.error('QR Generation error:', err);
            }
        }
    });
}

function saveQRFromContainer(containerId) {
    const container = document.getElementById(containerId);
    if (!container) return;

    // QRCode.js создает либо <img> либо <canvas> внутри контейнера
    const img = container.querySelector('img');
    const canvas = container.querySelector('canvas');

    let dataUrl = '';

    if (img && img.src) {
        dataUrl = img.src;
    } else if (canvas) {
        dataUrl = canvas.toDataURL("image/png");
    }

    if (dataUrl) {
        const link = document.createElement('a');
        link.href = dataUrl;
        link.download = `qr-code-${containerId}.png`;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        showToast('✅ QR-код сохранен');
    } else {
        showToast('❌ Не удалось сохранить QR');
    }
}

function closeModal(modalId) {
    const modal = document.getElementById(modalId);
    if (!modal) return;

    modal.classList.remove('active');
    document.body.style.overflow = '';
    currentModalId = null;

    // Если это последнее состояние в истории, возвращаемся назад
    if (history.state && history.state.modal === modalId) {
        history.back();
    }
}

// === ФУНКЦИИ ДЛЯ КОПИРОВАНИЯ ===
function copyText(text) {
    navigator.clipboard.writeText(text).then(() => {
        showToast(`✨ Скопировано: ${text.substring(0, 30)}${text.length > 30 ? '...' : ''}`);
    }).catch(err => {
        // Fallback для старых браузеров
        const textarea = document.createElement('textarea');
        textarea.value = text;
        document.body.appendChild(textarea);
        textarea.select();
        document.execCommand('copy');
        document.body.removeChild(textarea);
        showToast(`✨ Скопировано: ${text.substring(0, 30)}${text.length > 30 ? '...' : ''}`);
    });
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

function copyAllUSACardDetails(linkId) {
    const modal = document.getElementById(`modal_${linkId}`);
    if (!modal) return;

    let textToCopy = '';

    const rows = modal.querySelectorAll('div[style*="justify-content:space-between"]');

    rows.forEach(row => {
        const labelSpan = row.querySelector('span[style*="color:#6c757d"]');
        if (!labelSpan) return;

        const label = labelSpan.textContent.trim();
        const valueDiv = row.querySelector('div[style*="justify-content:flex-end"]');
        const valueSpan = valueDiv ? valueDiv.querySelector('span[style*="color:#003366"]') : null;

        if (!valueSpan || valueSpan.textContent === 'не указано') return;

        if (label.includes('Банк:')) {
            textToCopy += 'Банк: ' + valueSpan.textContent + '\n';
        } else if (label.includes('Владелец:')) {
            textToCopy += 'Владелец: ' + valueSpan.textContent + '\n';
        } else if (label.includes('Номер:')) {
            textToCopy += 'Номер карты: ' + valueSpan.textContent + '\n';
        } else if (label.includes('ZIP')) {
            textToCopy += 'ZIP код: ' + valueSpan.textContent + '\n';
        }
    });

    if (textToCopy) {
        copyText(textToCopy);
    } else {
        copyText(modal.innerText.trim());
    }
}

// // base.js

// === ФУНКЦИИ ДЛЯ ТАБОВ ===
// D:\aRabota\TelegaBoom\030_botolinkpro\web\templates\base\base.js

function switchCurrencyTab(linkId, tabIndex) {
    const modal = document.getElementById(`modal_${linkId}`);
    if (!modal) return;

    // Превращаем в число на случай, если пришла строка
    const targetIdx = parseInt(tabIndex);

    // Переключаем кнопки табов
    const tabs = modal.querySelectorAll('.currency-tab');
    tabs.forEach((tab, i) => {
        if (i === targetIdx) {
            tab.classList.add('active');
        } else {
            tab.classList.remove('active');
        }
    });

    // Переключаем контент табов
    const contents = modal.querySelectorAll('.currency-tab-content');
    contents.forEach((content, i) => {
        if (i === targetIdx) {
            content.classList.add('active');
        } else {
            content.classList.remove('active');
        }
    });

    // Генерируем QR код для активного таба, если он еще не создан
    const activeContent = document.getElementById(`currency-tab-${linkId}-${targetIdx}`);
    if (activeContent) {
        // Вызываем генерацию именно внутри этого контейнера
        generateQRCodes(activeContent);
    }
}

// === TOAST УВЕДОМЛЕНИЯ ===
function showToast(message, type = 'success') {
    const toast = document.getElementById('toast');
    if (!toast) return;

    if (currentToastTimeout) {
        clearTimeout(currentToastTimeout);
    }

    toast.classList.remove('success', 'error', 'hidden');
    toast.textContent = message;
    toast.classList.add(type);

    currentToastTimeout = setTimeout(() => {
        toast.classList.add('hidden');
        currentToastTimeout = null;

        setTimeout(() => {
            toast.classList.remove('success', 'error');
        }, 300);
    }, 2000);
}

// === ТРЕКИНГ ===
function trackClick(linkId) {
    if (!linkId || linkId === 'None') return;
    fetch(`/click/${linkId}`, {
        method: 'GET',
        keepalive: true
    }).catch(error => console.error('Error tracking click:', error));
}

function trackDetailsClick(linkId) {
    if (!linkId || linkId === 'None') return;

    fetch(`/click/${linkId}`, {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({type: 'details'})
    }).catch(error => console.error('Error:', error));
}

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

// Для обратной совместимости с onclick в HTML
function openModalOld(modalId) {
    const modal = document.getElementById(modalId);
    if (!modal) return;

    modal.classList.add('active');
    document.body.style.overflow = 'hidden';
    currentModalId = modalId;
    history.pushState({modal: modalId}, '');
}

// ГДЕ: В этом же файле base.js (обычно выше или ниже switchCurrencyTab)

function generateQRCodes(modalElement) {
    // Если ничего не передали, ищем по всему документу (но лучше передавать)
    const scope = modalElement || document;
    const qrContainers = scope.querySelectorAll('.auto-qr');

    qrContainers.forEach(container => {
        const address = container.getAttribute('data-address');
        // Генерируем только если есть адрес и если QR еще не нарисован
        if (address && address.length > 3 && container.innerHTML.trim() === '') {
            new QRCode(container, {
                text: address,
                width: 160,
                height: 160,
                colorDark: "#000000",
                colorLight: "#ffffff",
                correctLevel: QRCode.CorrectLevel.H
            });
        }
    });
}

// Сохранение QR как картинки
function saveQRFromContainer(containerId) {
    const container = document.getElementById(containerId);
    const canvas = container.querySelector('canvas');
    if (!canvas) return;

    const link = document.createElement('a');
    link.href = canvas.toDataURL("image/png");
    link.download = 'qr-code.png';
    link.click();
    showToast('✅ Сохранено в загрузки');
}

// РАБОЧАЯ функция "Поделиться" для сгенерированного QR
async function shareQRFromContainer(containerId, title) {
    const container = document.getElementById(containerId);
    const canvas = container.querySelector('canvas');
    if (!canvas) {
        showToast('❌ QR не готов');
        return;
    }

    // Превращаем canvas в файл blob
    canvas.toBlob(async (blob) => {
        const file = new File([blob], 'qr-code.png', {type: 'image/png'});

        // Проверяем, поддерживает ли браузер отправку файлов
        if (navigator.canShare && navigator.canShare({files: [file]})) {
            try {
                await navigator.share({
                    files: [file],
                    title: title,
                    text: 'Адрес для оплаты: ' + container.getAttribute('data-address')
                });
            } catch (err) {
                if (err.name !== 'AbortError') showToast('❌ Ошибка отправки');
            }
        } else {
            // Если браузер не умеет в файлы (старый ПК) - просто копируем адрес
            copyText(container.getAttribute('data-address'));
            showToast('🔗 Адрес скопирован (Share недоступен)');
        }
    }, 'image/png');
}


// D:\aRabota\TelegaBoom\030_botolinkpro\web\templates\base\base.js

function generateQRCodes(scopeElement) {
    const container = scopeElement || document;
    const qrElements = container.querySelectorAll('.auto-qr');

    qrElements.forEach(qrBox => {
        const address = qrBox.getAttribute('data-address');
        if (address && address.length > 3 && qrBox.innerHTML.trim() === '') {
            // Генерируем QR
            const qrcode = new QRCode(qrBox, {
                text: address,
                width: 180,
                height: 180,
                colorDark: "#000000",
                colorLight: "#ffffff",
                correctLevel: QRCode.CorrectLevel.H // Высокий уровень коррекции, чтобы иконка не ломала чтение
            });

            // Небольшая задержка, чтобы QR успел отрисоваться перед тем, как мы наложим лого (опционально для canvas)
        }
    });
}