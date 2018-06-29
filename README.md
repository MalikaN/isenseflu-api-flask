# fludetector-api-flask

## Background

### API Specification

OpenAPI 3.0.1 Definition Document: https://github.com/UCL/fludetector-openapi

## Requirements

- Python 3.6
- Pip
- SQLite

## Installation

### Python/Flask

```commandline
python3 -m venv ./venv
. venv/bin/activate
pip install -r requirements.txt
```

### Database

```commandline
python manage.py db init
python manage.py db migrate
python manage.py db upgrade
```

## Testing

```
APP_CONFIG=testing python manage.py test
```