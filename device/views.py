import uuid
import secrets

from django.shortcuts import render , get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse

from rest_framework.decorators import api_view, permission_classes
from django.utils import timezone
from .models import Command, Device, Telemetry, DeviceHealth, Firmware, DeviceFirmware

import json

from django.core.cache import cache
from rest_framework.permissions import AllowAny 
from django.db import IntegrityError, transaction



# This is the redis helper function
def is_device_valid(device_id, access_token):
    cache_key = f"auth:{device_id}:{access_token}"
    auth = cache.get(cache_key)
    if auth :
        return True
    try :
        device = Device.objects.get(device_id=device_id, access_token=access_token)
        cache.set(cache_key,True, timeout=86400)
        return True
    except Device.DoesNotExist:
            return False


@api_view(["POST"])

#This verify the device ID and Device Secret and assigns an access token
def device_verify(request):
    device_id = request.data.get("device_id")
    device_secret = request.data.get("device_secret")

    try:
        device = Device.objects.get(device_id=device_id,device_secret=device_secret)
        token = secrets.token_hex(32)
        device.access_token = token
        device.save()

        return JsonResponse({
            "success": True,
            "message": "Device verified successfully",
            "access_token": token
        })

    except Device.DoesNotExist:

        return JsonResponse({
            "success": False,
            "message": "Invalid device credentials"
        })


@api_view(["POST"])

#This verify the device ID and access token and stores the telemetry 
def telemetry_data(request):

    device_id = request.data.get("device_id")
    access_token = request.data.get("access_token")
    telemetry_payload = request.data.get("telemetry") 

    if not device_id or not access_token or telemetry_payload is None:
        return JsonResponse({
            "success": False,
            "message": "Missing required fields"
        }, status=400)
    
    if not isinstance(telemetry_payload, dict):
        return JsonResponse({
            "success": False,
            "message": "Telemetry data must be a JSON object"
        }, status=400)

    if not is_device_valid(device_id, access_token):
        return JsonResponse({
            "success": False,
            "message": "Invalid device credentials"
        }, status=401)

    try:
        device = Device.objects.get(device_id=device_id, access_token=access_token)
        Telemetry.objects.create(device=device,data=telemetry_payload)

        return JsonResponse({
            "success": True,
            "message": "Telemetry stored successfully"
        }, status=201)

    except Device.DoesNotExist:
        return JsonResponse({
            "success": False,
            "message": "Invalid access token"
        }, status=401)


@api_view(["POST"])

#The device will send the heartbeat in an interval
def device_heartbeat(request):

    device_id = request.data.get("device_id")
    access_token = request.data.get("access_token")
    status = request.data.get("status")
    uptime = request.data.get("uptime")

    if status not in dict(Device.STATUS_CHOICES):
        return JsonResponse({
            "success": False,
            "message": "Invalid status value"
        }, status=400)

    if not is_device_valid(device_id, access_token):
        return JsonResponse({
            "success": False,
            "message": "Invalid device credentials"
        }, status=401)
    
    try:
        device = Device.objects.get(device_id=device_id,access_token=access_token)
        device.status = status
        device.last_seen = timezone.now()
        device.uptime = int(uptime)
        device.save(update_fields=["status", "last_seen", "uptime"])

    except Device.DoesNotExist:
        return JsonResponse({
            "success": False,
            "message": "Invalid device credentials"
        }, status = 401)
    
    return JsonResponse({
        "success": True,
        "message": "Heartbeat received successfully"
    })



def clean_numeric(value, expected_type=float):
    if value is None or value == "":
        return None
    try:
        return expected_type(value)
    except (ValueError, TypeError):
        return None

@api_view(["POST"])

def device_health(request):
    device_id = request.data.get("device_id")
    access_token = request.data.get("access_token")

    if not device_id or not access_token:
        return JsonResponse({
            "success": False,
            "message": "Missing required authentication fields"
        }, status=400)

    if not is_device_valid(device_id, access_token):
        return JsonResponse({
            "success": False,
            "message": "Invalid device credentials"
        }, status=401)

    # Clean the input telemetry data
    health_data = {
        "cpu_usage": clean_numeric(request.data.get("cpu_usage"), float),
        "memory_usage": clean_numeric(request.data.get("memory_usage"), float),
        "storage_usage": clean_numeric(request.data.get("storage_usage"), float),
        "temperature": clean_numeric(request.data.get("temperature"), float),
        "battery_percentage": clean_numeric(request.data.get("battery_percentage"), int),
        "rssi": clean_numeric(request.data.get("rssi"), int),
    }

    try:
        device = Device.objects.only("id").get(device_id=device_id)
        
        # 1. Wrap in atomic block to enforce clean transaction rollback on SQLite
        try:
            with transaction.atomic():
                # Only look up by 'device'. Put fluctuating telemetry inside 'defaults'.
                DeviceHealth.objects.update_or_create(
                    device=device,
                    defaults=health_data
                )
        except IntegrityError:
            # 2. Fallback: If a concurrent request created it simultaneously, catch it & update
            DeviceHealth.objects.filter(device=device).update(**health_data)

        return JsonResponse({
            "success": True,
            "message": "Device health logs stored successfully"
        }, status=201)

    except Device.DoesNotExist:
        return JsonResponse({
            "success": False,
            "message": "Invalid device credentials"
        }, status=401)


    


@login_required
#For this it will not authenticate the device, it will send the url of the firmware
def deploy_firmware(request):

    if request.method != "POST":
        return JsonResponse(
            {"success": False, "message": "POST required"},
            status=405
        )

    device_id = request.POST.get("device_id")
    firmware_id = request.POST.get("firmware_id")

    device = get_object_or_404(Device,device_id=device_id,owner=request.user)

    firmware = get_object_or_404(
        Firmware,
        id=firmware_id
    )

    deployment = DeviceFirmware.objects.create(device=device,firmware=firmware,status="pending")

    payload = {
        "action": "ota_update",
        "deployment_id": deployment.id,
        "version": firmware.version,
        "firmware_url": firmware.firmware_file.url
    }

    Command.objects.create(
        device=device,
        command=json.dumps(payload)
    )

    return JsonResponse({
        "success": True,
        "message": "Firmware deployment queued",
        "deployment_id": deployment.id
    })


@api_view(["POST"])

#Updates the firmware status
def firmware_status(request):

    deployment_id = request.data.get("deployment_id")
    status = request.data.get("status")

    try:
        deployment = DeviceFirmware.objects.get(id=deployment_id)
        deployment.status = status
        deployment.save()

        if status == "success":
            deployment.device.current_firmware = deployment.firmware
            deployment.device.save()

        return JsonResponse({
            "success": True
        })

    except DeviceFirmware.DoesNotExist:
        return JsonResponse(
            {
                "success": False,
                "message": "Deployment not found"
            },
            status=404
        )
    



#Remote command execution

@api_view(["POST"])
#Creates a new command from dashboard or device config page
def command_create(request):

    device_id = request.data.get("device_id")
    command = request.data.get("command")
    multicommands = request.data.get("multicommands")
    payload = request.data.get("payload", {})

    if not device_id:
        return JsonResponse({
            "success": False,
            "message": "device_id is required"
        }, status=400)

    if not command and not multicommands:
        return JsonResponse({
            "success": False,
            "message": "command or multicommands is required"
        }, status=400)

    try:

        device = Device.objects.get(device_id=device_id)

        # Multiple commands
        if multicommands:

            cmd = Command.objects.create(
                device=device,
                command="multiple",
                multicommands=multicommands,
                command_status="pending"
            )

        # Single command
        else:

            cmd = Command.objects.create(
                device=device,
                command=command,
                multicommands=payload,
                command_status="pending"
            )

        return JsonResponse({
            "success": True,
            "message": "Command queued successfully",
            "command_id": cmd.command_id
        })

    except Device.DoesNotExist:

        return JsonResponse({
            "success": False,
            "message": "Device not found"
        }, status=404)


@api_view(["POST"])

#The device will fetch the pending commands
def command_get(request):

    device_id = request.data.get("device_id")
    access_token = request.data.get("access_token")

    if not device_id or not access_token:
        return JsonResponse({
            "success": False,
            "message": "Missing credentials"
        }, status=400)

    try:

        device = Device.objects.get(device_id=device_id,access_token=access_token)

        commands = Command.objects.filter(
            device=device,
            command_status="pending"
        ).order_by("timestamp")

        command_list = []

        for cmd in commands:

            # Mark command as received once sent to ESP
            cmd.command_status = "received"
            cmd.save(update_fields=["command_status"])

            command_list.append({
                "command_id": cmd.command_id,
                "command": cmd.command,
                "multicommands": cmd.multicommands
            })

        return JsonResponse({
            "success": True,
            "commands": command_list
        })

    except Device.DoesNotExist:

        return JsonResponse({
            "success": False,
            "message": "Invalid device credentials"
        }, status=401)


@api_view(["POST"])

def command_mark(request):
    device_id = request.data.get("device_id")
    access_token = request.data.get("access_token")
    command_id = request.data.get("command_id")
    command_status = request.data.get("command_status")

    if not device_id or not access_token or not command_id or not command_status:
        return JsonResponse({
            "success": False,
            "message": "device_id, access_token, command_id and command_status are required"
        }, status=400)

    VALID_STATUSES = ["completed", "failed", "received"]
    if command_status not in VALID_STATUSES:
        return JsonResponse({
            "success": False,
            "message": f"Invalid status value. Must be one of: {', '.join(VALID_STATUSES)}"
        }, status=400)

    try:
        device = Device.objects.get(device_id=device_id, access_token=access_token)
        command = Command.objects.get(device=device, command_id=command_id)

        if command.command_status == "completed":
            return JsonResponse({
                "success": False,
                "message": "Cannot modify a command that is already marked as completed"
            }, status=400)

        command.command_status = command_status
        command.save(update_fields=["command_status"])

        return JsonResponse({
            "success": True,
            "message": f"Command status updated to '{command_status}' successfully"
        })

    except Device.DoesNotExist:
        return JsonResponse({
            "success": False,
            "message": "Invalid device credentials"
        }, status=401)

    except Command.DoesNotExist:
        return JsonResponse({
            "success": False,
            "message": "Command not found"
        }, status=404)



@api_view(["GET"])

def command_status(request, command_id):

    try:

        cmd = Command.objects.get(command_id=command_id)

        return JsonResponse({
            "success": True,
            "command_id": cmd.command_id,
            "command": cmd.command,
            "status": cmd.command_status,
            "timestamp": cmd.timestamp
        })

    except Command.DoesNotExist:

        return JsonResponse({
            "success": False,
            "message": "Command not found"
        }, status=404)




