import json
import secrets
import uuid
from datetime import timedelta
from django.contrib import messages
from django.contrib.auth import (
    authenticate,
    get_user_model, 
    login,
    logout,
    update_session_auth_hash,
)
from django.contrib.auth.decorators import login_required
from django.core.cache import cache
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone  
from django.views.decorators.cache import cache_page
from device.models import (
    Command,
    Device,
    DeviceFirmware,
    DeviceHealth,
    Firmware,
    Telemetry,
)

User = get_user_model()


# Pages
#This will cache the page for 15 Min
@cache_page(60 * 15)
def home(request):
    return render(request, 'index.html')


def login_view(request):
    error = None
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request,username=username,password=password)
        if user is not None:
            login(request, user)
            return redirect('dashboard')
        else:
            error = 'Account does not exist or invalid credentials'
    return render(request,'login.html',
        {
            'error': error
        }
    )


def logout_view(request):
    logout(request)
    return redirect('home')


def signup(request):
    if request.method == "POST":

        username = request.POST.get("username", "").strip()
        email = request.POST.get("email", "").strip().lower()
        name = request.POST.get("name", "").strip()
        password = request.POST.get("password", "")

        if not username or not email or not password:
            messages.error(request,"All required fields must be filled.")
            return redirect("signup")

        if User.objects.filter(email=email).exists():
            messages.error(request,"An account with this email already exists.")
            return redirect("signup")

        if User.objects.filter(username=username).exists():
            messages.error(request,"Username already taken.")
            return redirect("signup")

        user = User.objects.create_user(
            username=username,
            email=email,
            first_name=name,
            password=password
        )

        login(request, user)
        messages.success(request,f"Hlo, {user.username}!")
        return redirect("dashboard")
    
    return render(request, "signup.html")


@login_required
def dashboard(request):

    if request.method == "POST":
        # ADD device
        if request.POST.get("device_name"):

            Device.objects.create(
                owner=request.user,
                device_name=request.POST.get("device_name"),
                purpose=request.POST.get("purpose"),
                device_type = request.POST.get("device_type"),
                device_id=str(uuid.uuid4()),
                device_secret=secrets.token_hex(32)
            )

            return redirect("dashboard")

        # Edit device
        elif request.POST.get("device_name_edit"):
            device_pk = request.POST.get("device_id")
            device = Device.objects.get(id=device_pk,owner=request.user)
            device.device_name = request.POST.get("device_name_edit")
            device.save()

            return redirect("dashboard")

        # Send Command
        elif request.POST.get("command"):
            command = request.POST.get("command").strip()
            device_id = request.POST.get("device_id")
            device = Device.objects.get(device_id=device_id,owner=request.user)

            if ',' in command:
                Command.objects.create(device=device,multicommands=command)
                return redirect("dashboard")
            
            Command.objects.create(device=device,command=command)
            return redirect("dashboard")

    devices = Device.objects.filter(owner=request.user)

    commands = Command.objects.filter(device__owner=request.user).order_by("-timestamp")
    allowed_statuses = ["online", "critical", "error", "warning"]
    online_count = devices.filter(status__in=allowed_statuses).count()

    return render( request,"dashboard.html",
        {
            "devices": devices,
            "commands": commands,
            "online_count": online_count,
        }
    )


@login_required
def all_commands(request):

    devices = Device.objects.filter(owner=request.user)
    commands = Command.objects.filter(device__owner=request.user)

    completed_count = commands.filter(command_status="completed").count()
    pending_count = commands.filter(command_status="pending").count()
    failed_count = commands.filter(command_status="failed").count()
    recieved_count = commands.filter(command_status="received").count()

    command = commands.order_by("-timestamp")

    if request.method == "POST":
        search_query = request.POST.get("search", "").strip()
        device_filter = request.POST.get("device_filter", "")

        if search_query:
            command = command.filter(
                Q(command__icontains=search_query) |
                Q(command_id__icontains=search_query)
            )

        if device_filter:
            command = command.filter(device__id=device_filter)

    return render(request,"all_commands.html",
        {
            "commands": command,
            "devices": devices,
            "completed_count": completed_count,
            "pending_count": pending_count,
            "failed_count": failed_count,
            "recieved_count": recieved_count,
        },
    )


@login_required
def account_settings(request):
    if request.method == "POST":

        username = request.POST.get("username")
        name = request.POST.get("name")
        email = request.POST.get("email")
        password = request.POST.get("password")
        password_confirm = request.POST.get("password_confirm")

        if password and password != password_confirm:
            return render(request,"account_settings.html",
                {"error": "Passwords do not match"}
            )

        if User.objects.exclude(pk=request.user.pk).filter(username=username).exists():
            return render(request,"account_settings.html",
                          
                {"error": "Username already exists"}
            )

        user = request.user
        user.username = username
        user.first_name = name
        user.email = email

        if password:
            user.set_password(password)

        user.save()

        if password:
            update_session_auth_hash(request, user)

        return redirect("account_settings")

    return render(request, "account_settings.html")

def password_reset(request):
    #Under development
    return render(request, 'password_reset.html')


@login_required
def telemetry_page(request):
    devices = Device.objects.filter(owner=request.user)
    device_id = request.GET.get('device_id')
    device = None
    telemetry_list = []
    telemetry_json = '[]'

    if device_id:
        device = devices.filter(device_id=device_id).first()
        if device:
            telemetry_list = (
                Telemetry.objects
                .filter(device=device)
                .order_by('-timestamp')[:50]
            )
            telemetry_json = json.dumps([
                {
                    "timestamp": str(t.timestamp),
                    "data": t.data
                }
                for t in telemetry_list
            ])

    return render(request, 'telemetry_page.html', {
        'devices': devices,
        'device': device,
        'telemetry_list': telemetry_list,
        'telemetry_json': telemetry_json,
    })

@login_required
def device_config(request):

    devices = Device.objects.filter(owner=request.user).order_by("device_name")
    selected_device_id = request.GET.get("device")

    if selected_device_id:
        device = devices.filter(device_id=selected_device_id).first()
    else:
        device = devices.first()
    if request.method == "POST":
        device_id = request.POST.get("device_id")
        action = request.POST.get("action")

        device = Device.objects.filter(owner=request.user,device_id=device_id).first()

        if not device:
            return redirect("device_config")

        # This is for custom command
        if action == "custom_command":

            Command.objects.create(
                device=device,
                command=request.POST.get("command"),
                command_status="pending"
            )

        # Update intervals for Heartbeat and Telemetry
        elif action == "update_intervals":

            Command.objects.create(
                device=device,
                command="update_intervals",
                multicommands={
                    "heartbeat_interval": request.POST.get(
                        "heartbeat_interval"
                    ),
                    "telemetry_interval": request.POST.get(
                        "telemetry_interval"
                    ),
                },
                command_status="pending"
            )

        # This command gets the device info
        elif action == "device_info":

            Command.objects.create(
                device=device,
                command="device_info",
                command_status="pending"
            )

        # Reboot
        elif action == "reboot":

            Command.objects.create(
                device=device,
                command="reboot",
                command_status="pending"
            )

        # Factory Reset
        elif action == "factory_reset":

            Command.objects.create(
                device=device,
                command="factory_reset",
                command_status="pending"
            )

        # OTA Update
        elif action == "ota_update":
            
            firmware_id = request.POST.get("firmware_id")
            firmware = Firmware.objects.filter(id=firmware_id,is_active=True).first()

            if firmware:

                DeviceFirmware.objects.create(
                    device=device,
                    firmware=firmware,
                    status="pending"
                )

                Command.objects.create(
                    device=device,
                    command="ota_update",
                    multicommands={
                        "version": firmware.version,
                        "firmware_url": firmware.firmware_file.url,
                    },
                    command_status="pending"
                )

        return redirect(
            f"{request.path}?device={device.device_id}"
        )

    recent_commands = []
    firmware_history = []

    if device:

        recent_commands = (device.commands.order_by("-timestamp")[:20])

        firmware_history = (
            DeviceFirmware.objects.filter(device=device)
            .select_related("firmware")
            .order_by("-created_at")[:20]
        )
    is_online = device.is_online

    return render(request,"device_config.html",
        {
            "devices": devices,
            "device": device,
            "firmwares": Firmware.objects.filter(
                is_active=True
            ),
            "recent_commands": recent_commands,
            "firmware_history": firmware_history,
        }
    )


@login_required
def firmware_upload(request):
    #Upload your .bin file in this page
    if request.method == "POST":

        Firmware.objects.create(
            version=request.POST.get("version"),
            firmware_file=request.FILES.get("firmware_file"),
            release_notes=request.POST.get("release_notes"),
            is_active=True
        )

        return redirect("firmware_upload")

    return render(request,"firmware_upload.html")

# ------------------------------------------------------------------------------------------




# ------------------------------------------------------------------------------------------

@login_required
def delete_device(request):
    if request.method == "POST":
        device_id = request.POST.get("device_id")
        try:
            device = Device.objects.get(id=device_id, owner=request.user)
            cache.delete(f"auth:{device_id}:{device.access_token}")
            device.delete()
            return redirect("dashboard")
        except Device.DoesNotExist:
            pass
    return redirect("dashboard")


@login_required
def delete_account(request):
    if request.method == "POST":
        request.user.delete()
        return redirect('home')

    return redirect('dashboard')

# ------------------------------------------------------------------------------------------





# This is for custom error page
# ------------------------------------------------------------------------------------------

def unified_error_view(request, exception=None, status_code=500):
    error_mapping = {
        400: (
            "Bad Request",
            "The server could not understand your request parameters."
        ),
        403: (
            "Permission Denied",
            "You do not have administrative clearance to access this resource."
        ),
        404: (
            "Page Not Found",
            "The tracking layer or resource link you requested does not exist."
        ),
        500: (
            "Server Error",
            "An internal system anomaly occurred. We are fixing it right now."
        ),
    }

    title, message = error_mapping.get(
        status_code,
        ("Unexpected Error", "An unknown error has occurred.")
    )

    return render(request,"error.html",
        {
            "status_code": status_code,
            "title": title,
            "message": message,
        },
        status=status_code,
    )


def handler400(request, exception):
    return unified_error_view(request, exception, 400)


def handler403(request, exception):
    return unified_error_view(request, exception, 403)


def handler404(request, exception):
    return unified_error_view(request, exception, 404)


def handler500(request):
    return unified_error_view(request, status_code=500)

# ------------------------------------------------------------------------------------------

