# Dynamic Function Integration Examples

This guide demonstrates how to use the Dynamic Function Integration API to upload, execute, and manage custom functions.

## Example Functions

### 1. Square Number Function
```python
def process(parameters):
    # Simple example that squares a number
    number = parameters.get('number', 0)
    return number * number
```

**Upload Request:**
```http
POST /api/functions/
Content-Type: application/json

{
  "name": "square_number",
  "code": "def process(parameters):\n    number = parameters.get('number', 0)\n    return number * number",
  "description": "Squares a given number",
  "parameters": {"number": "integer"}
}
```

**Execute Request:**
```http
POST /api/functions/square_number/execute
Content-Type: application/json

{
  "parameters": {"number": 5}
}
```

**Expected Response:**
```json
{
  "result": 25
}
```

### 2. Temperature Converter Function
```python
def process(parameters):
    # Convert between Celsius and Fahrenheit
    celsius = parameters.get('celsius')
    if celsius is None:
        return {"error": "Temperature in Celsius is required"}
    fahrenheit = (celsius * 9/5) + 32
    return {"celsius": celsius, "fahrenheit": fahrenheit}
```

**Upload Request:**
```http
POST /api/functions/
Content-Type: application/json

{
  "name": "temp_converter",
  "code": "def process(parameters):\n    celsius = parameters.get('celsius')\n    if celsius is None:\n        return {\"error\": \"Temperature in Celsius is required\"}\n    fahrenheit = (celsius * 9/5) + 32\n    return {\"celsius\": celsius, \"fahrenheit\": fahrenheit}",
  "description": "Converts temperature from Celsius to Fahrenheit",
  "parameters": {"celsius": "float"}
}
```

**Execute Request:**
```http
POST /api/functions/temp_converter/execute
Content-Type: application/json

{
  "parameters": {"celsius": 25}
}
```

**Expected Response:**
```json
{
  "result": {
    "celsius": 25,
    "fahrenheit": 77
  }
}
```

## API Usage Guide

### List Available Functions
```http
GET /api/functions/
```

### Upload New Function
```http
POST /api/functions/
Content-Type: application/json

{
  "name": "function_name",
  "code": "function_code",
  "description": "function_description",
  "parameters": parameter_schema
}
```

### Execute Function
```http
POST /api/functions/{function_name}/execute
Content-Type: application/json

{
  "parameters": parameter_values
}
```

### Delete Function
```http
DELETE /api/functions/{function_name}
```

## Security Notes

The function validation system ensures:
1. No import statements are allowed
2. No file operations (read/write) are permitted
3. No dangerous built-in functions (eval, exec) can be used
4. Functions must be named 'process' and accept only 'parameters' argument
5. Only pure Python code is allowed (no system calls or external dependencies)
