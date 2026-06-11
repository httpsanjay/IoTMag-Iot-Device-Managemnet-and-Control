from django.urls import path
from . import views

urlpatterns = [
    path("verify/", views.device_verify, name="device_verify"),
    path("heartbeat/", views.device_heartbeat, name="device_heartbeat"),
    path("telemetry/", views.telemetry_data, name="telemetry_data"),
    path("health/", views.device_health, name="device_health"),
    path("commands-create/", views.command_create, name="command_create"),
    path("commands-get/", views.command_get, name="command_get"),
    path("commands-mark/", views.command_mark, name="command_mark"),
    path("commands-status/<str:command_id>/", views.command_status, name="command_status"),
    path("firmware/deploy/", views.deploy_firmware, name="deploy_firmware"),
    path("firmware/status/", views.firmware_status, name="firmware_status"),

]