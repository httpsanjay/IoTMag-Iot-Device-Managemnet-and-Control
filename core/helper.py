import os
from django.core.mail import send_mail
from django.http import HttpResponse

def welcome_email(request, recipient, user_name):
    message_content = (
        f"Welcome to IOT_MAG, {user_name}\n\n"
        "Your IoT fleet management platform. We're excited to have you on board!\n\n"
        "Best regards,\n"
        "IoT_MAG Team\n\n"
        "Please do not reply to this email. If you have any questions, "
        "please contact us at sanjay2904sri@gmail.com.\n"
        "Thank you for choosing IOT_MAG!"
    )

    send_mail(
        subject="Welcome to IOT_MAG",
        message=message_content,
        from_email= os.environ.get("FROM_EMAIL") ,
        recipient_list=[recipient],  
        fail_silently=False,
    )
    
    return HttpResponse("Email sent successfully!")


def password_reset_mail(request, recipient,temp_passsword ):
    send_mail(
        subject = 'Password Reset Request',
        message = 'Use this temporary password to reset your password: ' + temp_passsword,
        from_email = 'sanjay2904sri@gmail.com',
        recipient = recipient,
        fail_silently = False
    )
    return HttpResponse("Email sent successfully!")

def account_delete(request,recipient):
    send_mail(
        subject = 'Account Deletion',
        message = 'Your account has been deleted.' \
        '\n\nWe regret to inform you that your account has been permanently deleted.' \
        '\n\nWe are sorry to see you go' \
        '\n\nIf you have any questions, please contact us at sanjay2904sri@gmail.com.',
        from_email = 'sanjay2904sri@gmail.com',
        recipient = recipient,
        fail_silently = False
    )