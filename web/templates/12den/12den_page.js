// D:\aRabota\TelegaBoom\030_botolinkpro\web\templates\base\base.js
let currentToastTimeout = null;
let currentModalId = null;

document.addEventListener('DOMContentLoaded', function() {
    // Закрытие модалок по клику на фон
    document.querySelectorAll('.modal-overlay').forEach(overlay => {
        overlay.addEventListener('click', function(e) {
            if (e.target === this) closeModal(this.id);
        });
    });

    // Кнопка "Назад"
    window.addEventListener('popstate', function() {
        if (currentModalId) closeModal(currentModalId);
    });

    // Трекинг кликов
    document.querySelectorAll('.track-link').forEach(link => {
        link.addEventListener('click', function() {
            const linkId = this.dataset.linkId;
            if (linkId && linkId !== 'None') trackClick(linkId);
        });
    });
});

function trackClick(linkId) {
    fetch(`/click/${linkId}`, { method: 'GET', keepalive: true });
}

function showToast(message, type = 'success') {
    const toast = document.getElementById('toast');
    if (!toast) return;
    if (currentToastTimeout) clearTimeout(currentToastTimeout);
    toast.textContent = message;
    toast.className = `toast ${type}`;
    currentToastTimeout = setTimeout(() => toast.classList.add('hidden'), 2000);
}

function copyText(text) {
    if (!text) return;
    navigator.clipboard.writeText(text).then(() => {
        showToast(`✨ Скопировано`);
    });
}

function openModal(modalId) {
    const modal = document.getElementById(modalId);
    if (!modal) return;
    modal.classList.add('active');
    document.body.style.overflow = 'hidden';
    currentModalId = modalId;
    history.pushState({ modal: modalId }, '');
}

function closeModal(modalId) {
    const modal = document.getElementById(modalId);
    if (!modal) return;
    modal.classList.remove('active');
    document.body.style.overflow = '';
    currentModalId = null;
}

// Функции для QR и табов оставляем тут же, они универсальны
function openQRModal(address, title, network, iconHtml) {
    const cleanAddress = address ? String(address).replace(/\+/g, '').trim() : '';
    const qrUrl = `https://api.qrserver.com/v1/create-qr-code/?size=250x250&data=${encodeURIComponent(cleanAddress)}`;
    const modal = document.getElementById('qr-modal-overlay');
    if (modal) {
        document.getElementById('qr-modal-img').src = qrUrl;
        document.getElementById('qr-modal-addr-text').textContent = cleanAddress;
        modal.classList.add('active');
    }
}