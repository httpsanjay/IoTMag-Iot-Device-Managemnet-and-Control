from django.urls import path
from . import views


urlpatterns =[
    path('', views.home, name='home'),
    path('login/', views.login_view, name='login'),
    path('signup/', views.signup, name='signup'),
    path('logout/', views.logout_view, name='logout'),
    path('delete_account/', views.delete_account, name='delete_account'),
    path('iotmag_api_docs/', views.api_doc_page, name='api_doc_page'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('dashboard/account_settings/', views.account_settings, name='account_settings'),
    path('dashboard/delete_device/', views.delete_device, name='delete_device'),
    path('dashboard/all_commands/', views.all_commands, name='all_commands'),
    path('password_reset/', views.password_reset, name='password_reset'),
    path('dashboard/telemetry_page/', views.telemetry_page, name='telemetry_page'),
    path('dashboard/device_config/', views.device_config, name='device_config'),
    path("dashboard/firmware/upload/",views.firmware_upload,name="firmware_upload"),
    
]


