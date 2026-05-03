# Python Health Check Service

A simple, secure health check service using `httpx` for HTTP requests and `pydantic` for data validation.

## Features

- Asynchronous health checks using `httpx`
- Strong data validation with `pydantic`
- Concurrent endpoint checking
- Configurable timeouts and expected status codes
- Detailed error reporting
- Response time measurement

## Installation

```bash
pip install -r health_check_requirements.txt
```

## Usage

### Basic Example

```python
import asyncio
from health_check_service import HealthCheckService, HealthCheckTarget

async def check_services():
    targets = [
        HealthCheckTarget(
            name="My API",
            url="https://api.example.com/health",
            timeout=5,
            expected_status=200
        ),
        HealthCheckTarget(
            name="Database",
            url="https://db.example.com/ping",
            timeout=3,
            expected_status=200
        ),
    ]
    
    service = HealthCheckService(targets)
    results = await service.check_all()
    service.print_results(results)
    
    return results

asyncio.run(check_services())
```

### Running the Example

```bash
python health_check_service.py
```

## Configuration

### HealthCheckTarget Parameters

- `name` (str): Display name for the endpoint (1-100 characters)
- `url` (HttpUrl): Full URL to check (validated by pydantic)
- `timeout` (int): Request timeout in seconds (1-60, default: 5)
- `expected_status` (int): Expected HTTP status code (100-599, default: 200)

### HealthCheckResult Fields

- `target_name` (str): Name of the checked endpoint
- `url` (str): URL that was checked
- `status` (str): 'healthy', 'unhealthy', or 'error'
- `status_code` (int|None): HTTP status code received
- `response_time_ms` (float|None): Response time in milliseconds
- `error_message` (str|None): Error description if check failed
- `checked_at` (datetime): Timestamp of the check

## Security Notes

- All dependencies are pinned to exact versions
- Uses `httpx` for secure HTTP/HTTPS requests
- Input validation via `pydantic` prevents injection attacks
- Follows redirects safely with `follow_redirects=True`

## Dependencies

- `httpx==0.27.0` - Modern async HTTP client
- `pydantic==2.7.1` - Data validation using Python type annotations