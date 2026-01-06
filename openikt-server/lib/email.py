from django.core.mail import send_mail
from settings import settings

def send_email(msg, user_email):
        send_mail(
            subject='Openikt Notification',
            message='',
            html_message=f'<b>Congratulate!</b><br>'
                         f'{msg}<br>'
                         f'--OpenIKT',
            recipient_list=[user_email],
            from_email=settings.EMAIL_FROM_USER
        )