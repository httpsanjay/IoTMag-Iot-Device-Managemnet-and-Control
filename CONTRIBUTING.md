# Contributing to IoT Mag

Thank you for your interest in contributing to **IoT Mag — IoT Device Management and Control**!

IoT Mag uses Django, SQLite, and HTTP APIs to exchange data between ESP32 devices and the backend.

## Getting Started

1. Fork this repository.
2. Clone your fork:

   ```bash
   git clone https://github.com/httpsanjay/IoTMag-Iot-Device-Managemnet-and-Control
   cd IoTMag-Iot-Device-Managemnet-and-Control
   ```

3. Create and activate a virtual environment:

   ```bash
   python -m venv .venv
   ```

4. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

5. Apply migrations and start the server:

   ```bash
   python manage.py migrate
   python manage.py runserver
   ```

## How to Contribute

- Report bugs with clear steps to reproduce them.
- Suggest improvements through GitHub Issues.
- Create a branch for your changes.
- Test your changes before submitting a pull request.
- Update documentation when necessary.

## Development Guidelines

- Follow the existing Django project structure and coding style.
- Validate incoming HTTP requests and handle errors properly.
- Protect device authentication credentials.
- Never commit passwords, API secrets, or private configuration files.
- Keep changes focused and document new features.

## Pull Requests

Before submitting a pull request:

- Test the affected functionality.
- Describe what you changed and why.
- Include relevant test results.
- Link any related issue.

## License

By contributing, you agree that your contributions will be licensed under the project's **Apache License 2.0**.

See the [`LICENSE`](LICENSE) file for details.

Thank you for helping improve IoT Mag!