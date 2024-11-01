# Flask Data Store API

A Flask-based data store with REST API and automatic Swagger documentation.

## Features

- RESTful API for CRUD operations on items
- Automatic Swagger documentation at `/docs`
- PostgreSQL database integration
- Data export functionality (CSV format)
- Input validation
- Error handling

## API Endpoints

- GET `/api/items/` - List all items
- POST `/api/items/` - Create a new item
- GET `/api/items/<id>` - Get a specific item
- PUT `/api/items/<id>` - Update a specific item
- DELETE `/api/items/<id>` - Delete a specific item
- GET `/api/items/export` - Export all items as CSV

## Documentation

API documentation is available at `/docs` endpoint using Swagger UI.
