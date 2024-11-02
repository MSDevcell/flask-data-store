# Flask Data Store API

A Flask-based data store with REST API and automatic Swagger documentation.

## Features

- RESTful API for CRUD operations on items
- Automatic Swagger documentation at `/docs`
- PostgreSQL database integration
- Data export functionality (CSV format)
- Dynamic function integration
- Smart device multimedia handling
- Input validation
- Error handling

## API Endpoints

### Items API
- GET `/api/items/` - List all items
- POST `/api/items/` - Create a new item
- GET `/api/items/<id>` - Get a specific item
- PUT `/api/items/<id>` - Update a specific item
- DELETE `/api/items/<id>` - Delete a specific item
- GET `/api/items/export` - Export all items as CSV

### Dynamic Functions API
- GET `/api/functions/` - List available functions
- POST `/api/functions/` - Upload new function
- POST `/api/functions/<name>/execute` - Execute a function
- DELETE `/api/functions/<name>` - Delete a function
- GET `/api/functions/<name>/versions` - Get function versions
- GET `/api/functions/<name>/executions` - Get execution history

### Media Files API
- POST `/api/media/` - Upload media file with metadata
- GET `/api/media/by-type/<type>` - Get media files by type
- GET `/api/media/by-timespan` - Get media files within timespan

## Documentation

- API documentation is available at `/docs` endpoint using Swagger UI
- Function integration examples and usage guide available in `FUNCTION_EXAMPLES.md`
- Detailed examples of function integration and execution in the documentation

## Security Features

The application implements several security measures:
- Input validation for all endpoints
- Safe function execution environment:
  - No imports allowed
  - No file operations
  - Memory and CPU limits
  - Execution timeout
- Automatic media file cleanup
- Database connection pooling and validation

## Function Integration

The Dynamic Function Integration API allows users to:
- Upload custom Python functions
- Execute functions with parameters
- Track execution history
- Version control for functions
- Resource usage monitoring

See `FUNCTION_EXAMPLES.md` for detailed examples and usage instructions.

## Media File Management

- Supports various file types (images, videos, audio, documents)
- Automatic file type detection
- Scheduled file cleanup
- Metadata management
- File size and type validation
