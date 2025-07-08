# CrawlChat Centralized UI

This directory contains the centralized UI components for all CrawlChat services.

## Structure

```
ui/
├── templates/          # HTML templates for all pages
│   ├── login.html      # Login page
│   ├── register.html   # Registration page
│   ├── chat.html       # Chat interface
│   ├── crawler.html    # Crawler interface
│   ├── confirm_email.html  # Email confirmation
│   └── test_mobile.html    # Mobile responsiveness test
├── static/             # Static assets
│   ├── css/            # Stylesheets
│   ├── js/             # JavaScript files
│   ├── images/         # Images and icons
│   └── fonts/          # Font files
└── README.md           # This file
```

## Usage

All services should reference this centralized UI directory instead of maintaining their own copies:

### In Dockerfiles:
```dockerfile
# Copy centralized UI
COPY ../ui/templates/ ${LAMBDA_TASK_ROOT}/templates/
COPY ../ui/static/ ${LAMBDA_TASK_ROOT}/static/
```

### In Python code:
```python
# Use centralized templates
templates = Jinja2Templates(directory="/var/task/templates")
```

## Benefits

1. **Single Source of Truth**: All UI changes are made in one place
2. **Consistency**: All services use the same UI components
3. **Maintainability**: Easier to update and maintain UI
4. **Reduced Duplication**: No more duplicate template files
5. **Version Control**: Better tracking of UI changes

## Services Using This UI

- `crawler-service/` - Crawler Lambda function
- `lambda-service/` - Main API Lambda function
- Future services can easily adopt this UI

## Development

When making UI changes:
1. Update files in this `ui/` directory
2. All services will automatically use the updated UI
3. No need to update multiple service directories 