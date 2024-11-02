# Dynamic Function Integration Examples

This guide demonstrates how to use the Dynamic Function Integration API to upload, execute, and manage custom functions.

## Basic Calculator Example

### Function Code
```python
def process(parameters):
    operation = parameters.get('operation', 'add')
    num1 = parameters.get('num1', 0)
    num2 = parameters.get('num2', 0)
    
    if operation == 'add':
        return num1 + num2
    elif operation == 'subtract':
        return num1 - num2
    elif operation == 'multiply':
        return num1 * num2
    elif operation == 'divide':
        if num2 == 0:
            return {'error': 'Division by zero'}
        return num1 / num2
    else:
        return {'error': 'Invalid operation'}
```

### Step-by-Step Guide

1. Upload the Function

```http
POST /api/functions/
Content-Type: application/json

{
  "name": "calculator",
  "code": "def process(parameters):\n    operation = parameters.get('operation', 'add')\n    num1 = parameters.get('num1', 0)\n    num2 = parameters.get('num2', 0)\n\n    if operation == 'add':\n        return num1 + num2\n    elif operation == 'subtract':\n        return num1 - num2\n    elif operation == 'multiply':\n        return num1 * num2\n    elif operation == 'divide':\n        if num2 == 0:\n            return {'error': 'Division by zero'}\n        return num1 / num2\n    else:\n        return {'error': 'Invalid operation'}",
  "description": "Basic calculator with add/subtract/multiply/divide operations",
  "parameters": {
    "operation": {
      "type": "string",
      "required": true,
      "description": "Operation to perform (add/subtract/multiply/divide)"
    },
    "num1": {
      "type": "float",
      "required": true,
      "description": "First number"
    },
    "num2": {
      "type": "float",
      "required": true,
      "description": "Second number"
    }
  }
}
```

2. Execute the Function

```http
POST /api/functions/calculator/execute
Content-Type: application/json

{
  "parameters": {
    "operation": "add",
    "num1": 5,
    "num2": 3
  }
}
```

Expected Response:
```json
{
  "result": 8
}
```

## Example Usage with curl

### Upload Function
```bash
curl -X POST http://localhost:5000/api/functions/ \
  -H "Content-Type: application/json" \
  -d '{
    "name": "calculator",
    "code": "def process(parameters):\n    operation = parameters.get('\''operation'\'', '\''add'\'')\n    num1 = parameters.get('\''num1'\'', 0)\n    num2 = parameters.get('\''num2'\'', 0)\n\n    if operation == '\''add'\'':\n        return num1 + num2\n    elif operation == '\''subtract'\'':\n        return num1 - num2\n    elif operation == '\''multiply'\'':\n        return num1 * num2\n    elif operation == '\''divide'\'':\n        if num2 == 0:\n            return {'\''error'\'': '\''Division by zero'\''}\n        return num1 / num2\n    else:\n        return {'\''error'\'': '\''Invalid operation'\''}",
    "description": "Basic calculator with add/subtract/multiply/divide operations",
    "parameters": {
      "operation": {
        "type": "string",
        "required": true,
        "description": "Operation to perform (add/subtract/multiply/divide)"
      },
      "num1": {
        "type": "float",
        "required": true,
        "description": "First number"
      },
      "num2": {
        "type": "float",
        "required": true,
        "description": "Second number"
      }
    }
  }'
```

### Execute Function
```bash
curl -X POST http://localhost:5000/api/functions/calculator/execute \
  -H "Content-Type: application/json" \
  -d '{
    "parameters": {
      "operation": "add",
      "num1": 5,
      "num2": 3
    }
  }'
```

## API Usage Notes

1. Function names must be unique
2. Functions must be named 'process' and accept a single 'parameters' argument
3. Parameters schema must specify type and whether they are required
4. Available parameter types: string, integer, float, boolean, list, dict
5. Functions are validated for security:
   - No imports allowed
   - No file operations
   - No dangerous built-ins (eval, exec)
   - Pure Python code only

## Error Handling

The API returns appropriate error responses:
- 400: Invalid parameters or function code
- 404: Function not found
- 500: Execution error (timeout, memory limit, runtime error)

## Execution Limits

- Timeout: 5 seconds
- Memory: 100 MB
- CPU: Limited by system resources
