from datetime import timedelta
from django.utils import timezone
from django.db import models
from django.conf import settings
import secrets
import uuid 

def generate_device_token():
    return secrets.token_hex(32)

def generate_command_id():
    return str(uuid.uuid4())

class DeviceGroup(models.Model):
    owner = models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)


class Device(models.Model):
    @property
    def is_online(self):
        if not self.last_seen:
            return False

        return self.last_seen > (
            timezone.now() - timedelta(minutes=2)
        )

    STATUS_CHOICES = (
        ('online', 'Online'),
        ('offline', 'Offline'),
        ('error', 'Error'),
        ('warning', 'Warning'),
        ('critical', 'Critical'),
        ('unknown', 'Unknown'),
    )
    group = models.ForeignKey(
        DeviceGroup,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="devices"
    )

    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='devices')
    access_token = models.CharField(max_length=64, blank=False, editable=False)
    device_id = models.CharField(max_length=100, editable=False, unique=True)
    device_name = models.CharField(max_length=100)
    device_secret = models.CharField(max_length=128, unique=True,editable=False)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='offline')
    last_seen = models.DateTimeField(null=True,blank=True)
    ip_address = models.GenericIPAddressField(null=True,blank=True)
    mac_address = models.CharField(max_length=17,blank=True)
    hardware_version = models.CharField(max_length=50,blank=True)
    manufacturer = models.CharField(max_length=100,blank=True)
    purpose = models.CharField(max_length=100,blank=True)
    device_type = models.CharField(max_length=100,blank=True)
    uptime = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


    def __str__(self):
        return f"{self.device_name} - {self.device_id}"
    

class Telemetry(models.Model):
    device = models.ForeignKey(Device, on_delete=models.CASCADE, related_name='telemetry')
    data = models.JSONField()
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Telemetry for {self.device.device_name} at {self.timestamp}"


class Command(models.Model):
    device = models.ForeignKey(Device, on_delete=models.CASCADE, related_name='commands')
    command = models.CharField(max_length=255)
    multicommands = models.JSONField(blank=True, null=True)
    command_id = models.CharField(max_length=100, unique=True, editable=False, default=generate_command_id)
    command_status = models.CharField(max_length=20, default='pending',)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Command for {self.device.device_name} at {self.timestamp}"
    
class DeviceHealth(models.Model):
    device = models.OneToOneField(Device,on_delete=models.CASCADE,related_name="health")
    cpu_usage = models.FloatField(default=0)
    memory_usage = models.FloatField(default=0)
    storage_usage = models.FloatField(default=0)
    temperature = models.FloatField(default=0)
    battery_percentage = models.IntegerField(default=0)
    rssi = models.IntegerField(default=0)
    uptime = models.BigIntegerField(default=0)
    updated_at = models.DateTimeField(auto_now=True)
    def __str__(self):
        return f"Health for {self.device.device_name} at {self.updated_at}"
    
class Firmware(models.Model):
    version = models.CharField(max_length=50, unique=True)
    firmware_file = models.FileField(upload_to="firmware/")
    release_notes = models.TextField(blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.version
    

class DeviceFirmware(models.Model):
    STATUS_CHOICES = (
        ("pending", "Pending"),
        ("downloading", "Downloading"),
        ("installing", "Installing"),
        ("success", "Success"),
        ("failed", "Failed"),
    )
    device = models.ForeignKey(Device,on_delete=models.CASCADE)
    firmware = models.ForeignKey(Firmware,on_delete=models.CASCADE)
    status = models.CharField(max_length=20,choices=STATUS_CHOICES,default="pending")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

