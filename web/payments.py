import stripe

def create_checkout_session(user_id, price_id):
    # user_id — это ID пользователя из твоей базы или из Telegram
    # Мы просто кладем его в параметр client_reference_id
    
    session = stripe.checkout.Session.create(
        payment_method_types=['card'],
        line_items=[{
            'price': price_id,  # ID товара из панели Stripe
            'quantity': 1,
        }],
        mode='payment',
        # Сюда мы пишем ID, чтобы Stripe его запомнил на время оплаты
        client_reference_id=str(user_id),
        
        success_url='https://botolink.pro/success?session_id={CHECKOUT_SESSION_ID}',
        cancel_url='https://botolink.pro/guide',
    )
    
    # Эту ссылку ты даешь пользователю (кнопка в боте или на сайте)
    return session.url