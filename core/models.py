# core/models.py


from sqlalchemy import (
    Column, Integer, String, BigInteger, Boolean, Text,
    DateTime, ForeignKey, JSON, Enum, ARRAY, Index,
    Numeric, CheckConstraint, UniqueConstraint, Text as TextColumn
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from datetime import datetime
from core.database import Base

# Перечисления (Enums)
class SubscriptionStatus(enum.Enum):
    TRIAL = "trial"
    ACTIVE = "active"
    EXPIRED = "expired"
    CANCELLED = "cancelled"

class PlanType(enum.Enum):
    MONTHLY = "monthly"
    YEARLY = "yearly"


class User(Base):
    """Модель пользователя Telegram"""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    telegram_id = Column(BigInteger, unique=True, nullable=False, index=True)
    username = Column(String, nullable=True)  # Telegram username (без @)
    first_name = Column(String, nullable=True)
    last_name = Column(String, nullable=True)
    language_code = Column(String, default="ru")

    # Метаданные
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    last_activity = Column(DateTime(timezone=True), onupdate=func.now())
    is_active = Column(Boolean, default=True)
    is_admin = Column(Boolean, default=False)
    
    # Добавь эти поля сюда, чтобы они соответствовали твоей базе
    is_pro = Column(Boolean, default=False)
    subscribe_until = Column(DateTime(timezone=True), nullable=True)
    pro_expires_at = Column(DateTime(timezone=True), nullable=True)
    last_pro_template_id = Column(Integer, nullable=True)
    custom_username = Column(String, nullable=True)

    # Связи
    page = relationship("Page", back_populates="user", uselist=False, cascade="all, delete-orphan")
    subscription = relationship("Subscription", back_populates="user", uselist=False, cascade="all, delete-orphan")

    def __repr__(self):
        return f"<User {self.telegram_id} {self.username}>"


class Page(Base):
    """Страница пользователя (одна на пользователя)"""
    __tablename__ = "pages"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)

    # URL страницы: /{username}
    username = Column(String, unique=True, nullable=False, index=True)

    # Контент страницы
    title = Column(String, default="Моя страница")  # Заголовок страницы
    description = Column(Text, nullable=True)  # Описание
    avatar_url = Column(String, nullable=True)  # URL аватарки

    # Дизайн
    template_id = Column(Integer, default=1)  # ID шаблона
    theme_colors = Column(JSON, default={
        "primary": "#3b82f6",
        "background": "#ffffff",
        "text": "#1f2937"
    })  # Цвета в JSON формате

    # Статистика
    view_count = Column(BigInteger, default=0)

    # Статус
    is_active = Column(Boolean, default=True)  # Активна ли страница (если подписка активна)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Связи
    user = relationship("User", back_populates="page")
    links = relationship("Link", back_populates="page", cascade="all, delete-orphan", order_by="Link.sort_order")

    __table_args__ = (
        Index('ix_pages_username_lower', func.lower(username)),  # Индекс для поиска без учета регистра
    )

    def __repr__(self):
        return f"<Page {self.username}>"


class Link(Base):
    """Самая важная модель - ссылки пользователя"""
    __tablename__ = "links"

    id = Column(Integer, primary_key=True, index=True)
    page_id = Column(Integer, ForeignKey("pages.id", ondelete="CASCADE"), nullable=False)

    # Контент ссылки
    title = Column(String, nullable=False)  # Название для отображения
    url = Column(Text, nullable=False)  # URL или текст (номер карты, адрес кошелька и т.д.)
    icon = Column(String, nullable=False)  # Код иконки (например: "instagram", "visa", "btc")

    # Порядок отображения
    sort_order = Column(Integer, default=0)

    # Статистика
    click_count = Column(BigInteger, default=0)

    # Статус
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Связи
    page = relationship("Page", back_populates="links")
    clicks = relationship("Click", back_populates="link", cascade="all, delete-orphan")

    __table_args__ = (
        Index('ix_links_page_id_sort', 'page_id', 'sort_order'),
    )

    def __repr__(self):
        return f"<Link {self.title} ({self.icon})>"


class Subscription(Base):
    """Подписка пользователя"""
    __tablename__ = "subscriptions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)

    # Статус подписки
    status = Column(Enum(SubscriptionStatus), default=SubscriptionStatus.TRIAL, nullable=False)

    # Даты пробного периода
    trial_start = Column(DateTime(timezone=True), server_default=func.now())
    trial_end = Column(DateTime(timezone=True), nullable=True)  # trial_start + 7 дней

    # Даты платной подписки
    subscription_start = Column(DateTime(timezone=True), nullable=True)
    subscription_end = Column(DateTime(timezone=True), nullable=True)

    # Тип плана (месячный/годовой)
    plan_type = Column(Enum(PlanType), nullable=True)

    # Платежная информация
    payment_provider = Column(String, nullable=True)  # stripe, yookassa и т.д.
    payment_id = Column(String, nullable=True)  # ID платежа в системе
    auto_renew = Column(Boolean, default=True)  # Автопродление

    # Метаданные
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Связи
    user = relationship("User", back_populates="subscription")

    @property
    def is_trial_active(self):
        """Проверка, активен ли пробный период"""
        if not self.trial_end:
            return False
        return self.status == SubscriptionStatus.TRIAL and datetime.now() < self.trial_end

    @property
    def is_subscription_active(self):
        """Проверка, активна ли платная подписка"""
        if not self.subscription_end:
            return False
        return self.status == SubscriptionStatus.ACTIVE and datetime.now() < self.subscription_end

    @property
    def can_access(self):
        """Может ли пользователь пользоваться сервисом"""
        return self.is_trial_active or self.is_subscription_active

    def __repr__(self):
        return f"<Subscription user:{self.user_id} status:{self.status}>"


class Click(Base):
    """Статистика кликов по ссылкам"""
    __tablename__ = "clicks"

    id = Column(Integer, primary_key=True, index=True)
    link_id = Column(Integer, ForeignKey("links.id", ondelete="CASCADE"), nullable=True)  # Может быть NULL если ссылка удалена
    page_id = Column(Integer, ForeignKey("pages.id", ondelete="CASCADE"), nullable=False)

    # Данные о клике
    ip_address = Column(String, nullable=True)  # IP адрес (может быть захеширован для GDPR)
    user_agent = Column(Text, nullable=True)  # User-Agent
    referer = Column(Text, nullable=True)  # Откуда пришел

    # Аналитика
    country = Column(String, nullable=True)  # Страна по IP
    device = Column(String, nullable=True)  # mobile/desktop/tablet
    browser = Column(String, nullable=True)  # chrome/firefox/etc
    os = Column(String, nullable=True)  # windows/mac/ios/android

    # Время клика
    clicked_at = Column(DateTime(timezone=True), server_default=func.now())

    # Связи
    link = relationship("Link", back_populates="clicks")
    page = relationship("Page")

    __table_args__ = (
        Index('ix_clicks_clicked_at', 'clicked_at'),
        Index('ix_clicks_link_id', 'link_id'),
        Index('ix_clicks_page_id_clicked', 'page_id', 'clicked_at'),
    )

    def __repr__(self):
        return f"<Click {self.id} link:{self.link_id}>"


class Icon(Base):
    """Библиотека иконок"""
    __tablename__ = "icons"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)  # Название на русском (например: "Instagram")
    icon_code = Column(String, nullable=False, unique=True)  # Код иконки (например: "instagram", "visa")
    category = Column(String, nullable=False)  # Категория: "social", "payment", "crypto", "bank", "messenger"
    keywords = Column(ARRAY(String), nullable=True)  # Для поиска: ["insta", "photo", "social"]

    # Отображение
    svg_icon = Column(Text, nullable=True)  # SVG код иконки (опционально)
    font_awesome_class = Column(String, nullable=True)  # Класс Font Awesome (например: "fab fa-instagram")

    # Статус
    is_active = Column(Boolean, default=True)
    sort_order = Column(Integer, default=0)

    __table_args__ = (
        Index('ix_icons_category', 'category'),
        Index('ix_icons_keywords', 'keywords', postgresql_using='gin'),
    )

    def __repr__(self):
        return f"<Icon {self.name} ({self.category})>"


class Template(Base):
    """Шаблоны дизайна страниц"""
    __tablename__ = "templates"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)  # Название шаблона
    description = Column(Text, nullable=True)

    # Файлы шаблона
    html_template = Column(Text, nullable=False)  # HTML шаблон Jinja2
    css_template = Column(Text, nullable=True)  # CSS переменные/стили
    preview_url = Column(String, nullable=True)  # URL превью

    # Настройки
    is_default = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    sort_order = Column(Integer, default=0)

    def __repr__(self):
        return f"<Template {self.name}>"