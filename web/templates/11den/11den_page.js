// 11den_page.js
let currentToastTimeout = null;
let currentModalId = null;

// Инициализация при загрузке страницы
document.addEventListener('DOMContentLoaded', function () {
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

    // Добавляем обработчики для трекинга кликов по ссылкам
    document.querySelectorAll('.track-link').forEach(link => {
        link.addEventListener('click', function (e) {
            const linkId = this.dataset.linkId;
            if (linkId) {
                trackClick(linkId);
            }
        });
    });
});

// === ФУНКЦИИ ДЛЯ МОДАЛЬНЫХ ОКОН ===
function openModal(modalId) {
    const modal = document.getElementById(modalId);
    if (!modal) return;

    modal.classList.add('active');
    document.body.style.overflow = 'hidden';
    currentModalId = modalId;

    // Добавляем в историю браузера
    history.pushState({modal: modalId}, '');
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
// bot/static/templates/11den/11den_page.js

function copyText(text) {
    navigator.clipboard.writeText(text).then(() => {
        // Передаем текст в тост для отображения
        showToast(`✨ Скопировано: ${text}`);
    }).catch(err => {
        // Fallback для старых браузеров
        const textarea = document.createElement('textarea');
        textarea.value = text;
        document.body.appendChild(textarea);
        textarea.select();
        document.execCommand('copy');
        document.body.removeChild(textarea);
        showToast(`✨ Скопировано: ${text}`);
    });
}

function copyAllDetails(linkId) {
    const modal = document.getElementById(`modal_${linkId}`);
    if (!modal) return;

    let allText = '';

    // Собираем все текстовые значения из деталей
    modal.querySelectorAll('.detail-value code, .detail-value span:not(.copy-btn)').forEach(el => {
        const text = el.textContent.trim();
        if (text) {
            const detailRow = el.closest('.detail-row');
            const label = detailRow?.querySelector('.detail-label')?.textContent;
            if (label) {
                allText += `${label}: ${text}\n`;
            } else {
                allText += `${text}\n`;
            }
        }
    });

    // Добавляем UID для крипты
    modal.querySelectorAll('.tab-pane.active .detail-value code').forEach(el => {
        const text = el.textContent.trim();
        if (text) {
            allText += `${text}\n`;
        }
    });

    if (allText) {
        copyText(allText.trim());
    } else {
        showToast('Нет данных для копирования');
    }
}

// === НОВАЯ ФУНКЦИЯ ДЛЯ BINANCE ===
function copyAllBinanceDetails(linkId) {
    // Находим модальное окно
    const modal = document.getElementById(`modal_${linkId}`);

    // Собираем данные
    const address = modal.querySelector('.detail-value code')?.textContent || '';
    const network = modal.querySelector('.network-badge')?.textContent || '';
    const currency = modal.querySelector('.detail-label')?.textContent.match(/\((.*?)\)/)?.[1] || 'USDT';

    // Формируем текст
    const details = `Адрес (${currency}): ${address}\nСеть: ${network}`;

    // Копируем
    copyText(details);
}

// === ФУНКЦИИ ДЛЯ ТАБОВ ===
function switchTab(modalId, tabName, index) {
    const modal = document.getElementById(`modal_${modalId}`);
    if (!modal) return;

    // Преобразуем index в число
    const tabIndex = parseInt(index);

    // Переключаем активные классы у кнопок табов
    const tabButtons = modal.querySelectorAll('.tab-btn');
    tabButtons.forEach((btn, i) => {
        if (i === tabIndex) {
            btn.classList.add('active');
        } else {
            btn.classList.remove('active');
        }
    });

    // Переключаем содержимое табов
    const tabPanes = modal.querySelectorAll('.tab-pane');
    tabPanes.forEach((pane, i) => {
        if (i === tabIndex) {
            pane.classList.add('active');
        } else {
            pane.classList.remove('active');
        }
    });
}

function switchSberTab(tabType) {
    if (tabType === 'phone') {
        showToast('📱 Доступна только оплата по карте');
    }
}

// === ФУНКЦИИ ДЛЯ QR-КОДОВ ===
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
            // Fallback - открываем в новой вкладке
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

// === TOAST УВЕДОМЛЕНИЯ С ПОДДЕРЖКОЙ ЦВЕТОВ ===
function showToast(message, type = 'success') {
    const toast = document.getElementById('toast');
    if (!toast) return;

    // 1. Сбрасываем таймеры, если тост уже был вызван
    if (currentToastTimeout) {
        clearTimeout(currentToastTimeout);
    }

    // 2. Подготовка: убираем старое
    toast.classList.remove('success', 'error', 'hidden');

    // 3. Установка новых данных
    toast.textContent = message;
    toast.classList.add(type);

    // 4. Устанавливаем таймер на скрытие
    currentToastTimeout = setTimeout(() => {
        toast.classList.add('hidden');
        currentToastTimeout = null;

        // Очищаем цвета только после того, как закончится анимация скрытия (0.3с)
        setTimeout(() => {
            toast.classList.remove('success', 'error');
        }, 300);

    }, 2000);
}

// Для обычных переходов по ссылке (GET)
function trackClick(linkId) {
    if (!linkId || linkId === 'None') return;
    fetch(`/click/${linkId}`, {
        method: 'GET',
        keepalive: true
    }).catch(error => console.error('Error tracking click:', error));
}

function trackDetailsClick(linkId) {
    if (!linkId || linkId === 'None') return;

    fetch(`/click/${linkId}`, {  // убрал ?type=details
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({type: 'details'})
    }).catch(error => console.error('Error:', error));
}


function switchCurrencyTab(linkId, tabIndex) {
    const modal = document.getElementById(`modal_${linkId}`);
    if (!modal) return;

    // Переключаем табы
    const tabs = modal.querySelectorAll('.currency-tab');
    const contents = modal.querySelectorAll('.currency-tab-content');

    tabs.forEach((tab, i) => {
        if (i === tabIndex) {
            tab.classList.add('active');
        } else {
            tab.classList.remove('active');
        }
    });

    contents.forEach((content, i) => {
        if (i === tabIndex) {
            content.classList.add('active');
        } else {
            content.classList.remove('active');
        }
    });
}


// Функция специально для виджета кошелька
// Функция специально для виджета кошелька (ИСПРАВЛЕННАЯ)
function copyWalletAddr(address, btnElement) {
    if (!address) return;

    // 1. Вызываем стандартное копирование и тост
    copyText(address);

    // 2. Визуальный фидбек БЕЗ изменения размеров и иконок
    // Находим саму кнопку, если кликнули по блоку
    const btn = btnElement.classList.contains('wallet-btn') ? btnElement : btnElement.querySelector('.wallet-btn');

    if (btn) {
        btn.style.transition = '0.2s';
        btn.style.opacity = '0.5';
        btn.style.transform = 'scale(0.95)'; // Легкое уменьшение (нажатие), а не увеличение

        setTimeout(() => {
            btn.style.opacity = '1';
            btn.style.transform = 'scale(1)';
        }, 200);
    }
}


function openQRModal(address, title, network, iconHtml) {
    // Убираем плюс из адреса/номера перед использованием
    const cleanAddress = address ? String(address).replace(/\+/g, '').trim() : '';

    // API для генерации QR (используем cleanAddress)
    const qrUrl = `https://api.qrserver.com/v1/create-qr-code/?size=250x250&data=${encodeURIComponent(cleanAddress)}`;

    let modal = document.getElementById('qr-modal-overlay');

    if (!modal) {
        const modalHtml = `
            <div id="qr-modal-overlay" class="qr-modal-overlay" onclick="closeQRModal()">
                <div class="qr-modal-card" onclick="event.stopPropagation()">
                    <div class="qr-modal-header">
                        <span id="qr-modal-title"></span>
                        <button class="qr-close-btn" onclick="closeQRModal()">&times;</button>
                    </div>
                    <div class="qr-modal-body">
                        <div style="display: flex; align-items: center; justify-content: center; gap: 10px; margin-bottom: 15px;">
                            <div id="qr-modal-icon-container"></div>
                            <span id="qr-modal-title-display" style="color: #fff; font-size: 18px; font-weight: 600;"></span>
                        </div>

                        <div class="wallet-network-info" style="display: inline-flex; align-items: center; gap: 6px; background: rgba(255,255,255,0.05); padding: 4px 12px; border-radius: 30px; margin-bottom: 15px;">
                            <span>🌐</span>
                            <span class="network-label" style="color: rgba(255,255,255,0.5);">Сеть:</span>
                            <span class="network-value" id="qr-network-value" style="color: #00ff88; font-weight: 600;"></span>
                        </div>
                        
                        <div class="qr-img-container" style="background: white; padding: 10px; border-radius: 12px; display: inline-block; margin-bottom: 15px;">
                           <img id="qr-modal-img" src="" alt="QR Code" style="display: block; width: 200px; height: 200px;">
                        </div>
                        
                        <div class="qr-modal-address" onclick="copyFromModal(this)" style="display: flex; align-items: center; justify-content: space-between; background: rgba(255,255,255,0.07); padding: 12px 16px; border-radius: 12px; cursor: pointer;">
                            <span id="qr-modal-addr-text" style="font-family: monospace; font-size: 11px; color: #00ff88; word-break: break-all; text-align: left; flex: 1; margin-right: 15px;"></span>
                            <i class="fa-regular fa-copy" style="color: #fff; opacity: 0.7; font-size: 16px;"></i>
                        </div>
                        
                        <p style="font-size: 10px; color: #666; margin-top: 12px;">Нажмите на адрес, чтобы скопировать</p>
                    </div>
                </div>
            </div>`;
        document.body.insertAdjacentHTML('beforeend', modalHtml);
        modal = document.getElementById('qr-modal-overlay');
    }

    // Обновляем контент модалки перед показом
    const imgElement = document.getElementById('qr-modal-img');
    const titleDisplay = document.getElementById('qr-modal-title-display');
    const addrElement = document.getElementById('qr-modal-addr-text');
    const networkValue = document.getElementById('qr-network-value');
    const iconContainer = document.getElementById('qr-modal-icon-container');

    imgElement.src = qrUrl;
    titleDisplay.textContent = title;
    // Вставляем очищенный адрес в текстовое поле
    addrElement.textContent = cleanAddress;

    // Вставляем логотип
    if (iconContainer) {
        if (iconHtml) {
            iconContainer.innerHTML = iconHtml;
        } else {
            iconContainer.innerHTML = ''; // Пусто, если нет логотипа
        }
    }

    // Показываем сеть если есть
    if (networkValue) {
        networkValue.textContent = network || '';
        // Если сети нет, прячем блок
        const networkBlock = networkValue.closest('.wallet-network-info');
        if (networkBlock) {
            networkBlock.style.display = network ? 'inline-flex' : 'none';
        }
    }

    // Плавное появление
    modal.classList.add('active');
    document.body.style.overflow = 'hidden';
}

function closeQRModal() {
    const modal = document.getElementById('qr-modal-overlay');
    if (modal) modal.classList.remove('active');
    document.body.style.overflow = '';
}

function copyFromModal(el) {
    const text = document.getElementById('qr-modal-addr-text').textContent;

    navigator.clipboard.writeText(text).then(() => {
        // Делаем "красивый" короткий адрес для уведомления (например, 0x123...abc)
        const shortAddr = text.length > 12
            ? text.substring(0, 6) + '...' + text.substring(text.length - 4)
            : text;

        // Передаем текст в тост
        showToast(`✨ Скопировано: ${shortAddr}`);
    }).catch(err => {
        console.error('Ошибка копирования:', err);
    });
}


// === ФУНКЦИЯ ДЛЯ КОПИРОВАНИЯ ВСЕХ РЕКВИЗИТОВ АМЕРИКАНСКОЙ КАРТЫ ===
function copyAllUSACardDetails(linkId) {
    const modal = document.getElementById(`modal_${linkId}`);
    if (!modal) return;

    let textToCopy = '';

    // Банк - ищем по тексту в label
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
        // Если не нашли структурированные данные, копируем весь текст модалки
        copyText(modal.innerText.trim());
    }
}

// === УНИВЕРСАЛЬНАЯ ФУНКЦИЯ ДЛЯ КОПИРОВАНИЯ ЛЮБЫХ БАНКОВСКИХ РЕКВИЗИТОВ ===
function copyAllBankDetails(linkId) {
    const modal = document.getElementById(`modal_${linkId}`);
    if (!modal) return;

    let textToCopy = '';

    // Заголовок
    const title = modal.querySelector('.modal-content span[style*="font-size:1.2rem"]');
    if (title) {
        textToCopy += title.textContent + '\n';
        textToCopy += '─'.repeat(20) + '\n\n';
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


