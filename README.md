# IoT Mag — IoT Device Management and Control

A Django-based IoT device management platform for registering devices, receiving telemetry, monitoring device health, and managing remote commands through HTTP APIs.

IoT Mag explores how embedded devices such as the ESP32 can communicate securely with a centralized backend for device monitoring and control.

> **Project status:** Under development. This project is intended for learning, experimentation, and continued development.

## Overview

IoT Mag provides a central backend through which IoT devices communicate with a web application. Devices authenticate with the backend, periodically send data, and retrieve commands issued through the platform.

The project focuses on device identity, HTTP API design, data ingestion, device health monitoring, command management, and containerized deployment.

## Features

- **Device verification:** Verify devices before they communicate with the backend.
- **Device authentication:** Issue individual access tokens to verified devices.
- **Heartbeat monitoring:** Receive periodic heartbeat requests from devices.
- **Telemetry collection:** Receive and store device telemetry.
- **Health reporting:** Accept device health information.
- **Remote command management:** Create commands, let devices retrieve pending commands, and track command completion.
- **Web application:** Manage and monitor IoT devices through the Django application.
- **Docker support:** Build and run the application in a container.
- **SQLite database:** Store application data using SQLite.

## Technology Stack

| Component | Technology |
|---|---|
| Backend | Python, Django |
| API | Django REST Framework |
| Database | SQLite |
| Device communication | HTTP |
| Embedded device | ESP32-compatible devices |
| Frontend | HTML, CSS, JavaScript |
| Containerization | Docker |
| Version control | Git and GitHub |

## Architecture

```text
┌────────────────────────┐
│      ESP32 Device      │
│   Sensors / Firmware   │
└────────────┬───────────┘
             │
             │ HTTP + JSON
             ▼
┌────────────────────────┐
│     Django Backend     │
│                        │
│  Device Verification   │
│  Authentication        │
│  Telemetry Ingestion   │
│  Health Reporting      │
│  Command Management    │
└────────────┬───────────┘
             │
             ▼
┌────────────────────────┐
│    SQLite Database     │
│                        │
│  Device Records        │
│  Telemetry             │
│  Health Data           │
│  Commands              │
└────────────────────────┘
             ▲
             │
┌────────────┴───────────┐
│    Django Web App      │
│ Device Management and  │
│ Monitoring Interface   │
└────────────────────────┘
```

This diagram illustrates the project's main communication flow. The exact behavior depends on the implemented API and application configuration.

## Project Structure

```text
IoTMag-Iot-Device-Managemnet-and-Control/
│
├── core/                 # Core application
├── device/               # Device-related functionality
├── IotMag/               # Django project configuration
├── Demo_images/          # Screenshots and project visuals
│
├── .dockerignore         # Docker build exclusions
├── .gitignore            # Git exclusions
├── Dockerfile             # Docker image configuration
├── LICENSE                # Apache License 2.0
├── CODE_OF_CONDUCT.md     # Community guidelines
├── CONTRIBUTING.md        # Contribution instructions
├── manage.py              # Django management utility
├── requirements.txt       # Python dependencies
└── README.md              # Project documentation
```

## Getting Started

### Prerequisites

- Python compatible with `requirements.txt`
- pip
- Git
- Docker Desktop (for containerized execution)

### Option 1: Run Locally

**1. Clone the repository**

```bash
git clone https://github.com/httpsanjay/IoTMag-Iot-Device-Managemnet-and-Control.git
cd IoTMag-Iot-Device-Managemnet-and-Control
```

The main repository is private, so GitHub access permissions are required.

**2. Create a virtual environment**

Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

**3. Install dependencies**

```bash
python -m pip install -r requirements.txt
```

**4. Apply database migrations**

```bash
python manage.py migrate
```

**5. Start the development server**

```bash
python manage.py runserver
```

Open http://127.0.0.1:8000/ in your browser.

### Option 2: Run with Docker

Docker support is configured in the project's `Dockerfile`.

**1. Build the image**

Run from the project root:

```bash
docker build -t iot-mag .
```

**2. Start the container**

If your Docker configuration serves Django on port `8000`:

```bash
docker run --rm -p 8000:8000 iot-mag
```

Open http://localhost:8000/ in your browser.

Use the port and startup configuration defined by your working Docker setup if they differ from these examples.

**Useful Docker commands**

```bash
# List running containers
docker ps

# View all containers
docker ps -a

# View application logs
docker logs <container_id>

# Stop a running container
docker stop <container_id>
```

**Database note:** SQLite stores data in a database file. If the database is stored inside a container, deleting that container may also remove its data unless the database file is stored in a persistent volume or mounted directory. Configure persistence appropriately for your deployment.

## API Workflow

IoT Mag uses HTTP requests to exchange data between devices and the backend.

### 1. Verify a Device

Send a `POST` request to `/verify/` with the device credentials.

Example request:

```http
POST /verify/
Content-Type: application/json
```

```json
{
  "device_id": "YOUR_DEVICE_ID",
  "device_secret": "YOUR_DEVICE_SECRET"
}
```

A successful verification returns an access token. Save it securely for subsequent requests.

Example response:

```json
{
  "success": true,
  "message": "Device verified successfully",
  "access_token": "YOUR_ACCESS_TOKEN"
}
```

Use the actual field names and response format implemented by your backend.

### 2. Authenticate Requests

Include the device's access token in the `Authorization` header:

```http
Authorization: Bearer YOUR_ACCESS_TOKEN
```

Each device should use its own token. Never commit real tokens or device secrets to GitHub.

### 3. Send Heartbeats and Device Data

Once authenticated, a device can send periodic heartbeat requests and submit telemetry or health information to the corresponding API endpoints.

This allows the backend to receive device updates and maintain records for monitoring.

### 4. Retrieve and Execute Commands

The backend provides command-related endpoints for creating commands, retrieving pending commands, marking commands as completed, and checking command status.

A device can periodically poll for commands, execute supported operations, and report completion.

## API Reference

The following endpoints are documented in the public project README. Confirm the request payloads and response schemas against the current implementation before integrating a device.

### Device APIs

| Method | Endpoint | Purpose |
|---|---|---|
| `POST` | `/verify/` | Verify a device and obtain an access token |
| `POST` | `/heartbeat/` | Submit a heartbeat |
| `POST` | `/telemetry/` | Submit telemetry data |
| `POST` | `/health/` | Submit device health information |

### Command APIs

| Method | Endpoint | Purpose |
|---|---|---|
| `POST` | `/command-create/` | Create a command |
| `GET` | `/command-get/` | Retrieve pending commands |
| `POST` | `/command-mark/` | Mark a command as completed |
| `GET` | `/command-status/<command_id>/` | Retrieve command status |

All endpoint paths are relative to your configured server address. The exact authentication requirements, query parameters, and request bodies should follow the current backend implementation.

## Security Considerations

IoT device management involves communicating with devices over a network. Follow these practices when developing or deploying IoT Mag:

- Keep Django's secret key, device secrets, and access tokens out of source control.
- Validate incoming HTTP requests and payloads.
- Authenticate device requests and restrict privileged operations.
- Use HTTPS when communicating over untrusted networks.
- Set `DEBUG=False` and configure `ALLOWED_HOSTS` appropriately in production.
- Protect the SQLite database file and any stored device credentials.
- Avoid using real personal information in demonstrations or test environments.

## Testing

Run the Django test suite with:

```bash
python manage.py test
```

Recommended areas to test:

- Device verification with valid and invalid credentials.
- Authentication of protected API requests.
- Valid and malformed heartbeat, telemetry, and health payloads.
- Database persistence and error handling.
- Command creation, retrieval, and completion.
- HTTP failures and unavailable devices.
- Application startup and database migrations in Docker.

## Screenshots

Project screenshots are maintained in the `Demo_images/` directory.

Add screenshots here using the actual filenames, for example:

```markdown
![IoT Mag Dashboard](Demo_images/dashboard.png)
```

Recommended screenshots include the dashboard, device list, telemetry view, and command-management interface, where available.

## Roadmap

Potential future improvements include:

- [ ] Expand automated API tests.
- [ ] Improve device authentication and error handling.
- [ ] Improve device availability and heartbeat monitoring.
- [ ] Add clearer API documentation and ESP32 integration examples.
- [ ] Improve telemetry visualization and analytics.
- [ ] Strengthen production deployment and database persistence.
- [ ] Improve logging and operational diagnostics.

## Contributing

Contributions, bug reports, and suggestions are welcome.

Please read [CONTRIBUTING.md](CONTRIBUTING.md) before submitting changes and follow the guidelines in [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md).

## License

This project is licensed under the **Apache License 2.0**. See [LICENSE](LICENSE) for the full license text.

## Author

**Sri Sanjay K**

GitHub: [@httpsanjay](https://github.com/httpsanjay)

## Acknowledgment

IoT Mag is a learning-oriented project exploring backend development, embedded-device communication, HTTP APIs, and IoT device management.

Feedback and constructive suggestions are welcome.
