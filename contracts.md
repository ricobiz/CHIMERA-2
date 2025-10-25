# API Contracts & Implementation Plan

## Current Mock Data (to be replaced)

### Frontend Mock Data (`mockData.js`)
- `mockProjects`: Static project list
- `samplePrompts`: Pre-defined prompt suggestions
- `mockGeneratedCode`: Hardcoded React component code
- Mock AI responses with simulated delays

## Backend API Endpoints

### 1. Code Generation Endpoint
**POST** `/api/generate-code`

**Request:**
```json
{
  "prompt": "string",
  "conversation_history": [
    {"role": "user|assistant", "content": "string"}
  ]
}
```

**Response:**
```json
{
  "code": "string (generated React/HTML/CSS code)",
  "message": "string (AI explanation)",
  "conversation_id": "string"
}
```

**Purpose:** 
- Send user prompt to OpenRouter API
- Use code-specialized model (e.g., `deepseek/deepseek-coder`, `anthropic/claude-3.7-sonnet`)
- Return generated code and explanation

### 2. Save Project Endpoint
**POST** `/api/projects`

**Request:**
```json
{
  "name": "string",
  "description": "string",
  "code": "string",
  "conversation_history": "array"
}
```

**Response:**
```json
{
  "id": "string",
  "name": "string",
  "created_at": "datetime"
}
```

### 3. Get Projects Endpoint
**GET** `/api/projects`

**Response:**
```json
{
  "projects": [
    {
      "id": "string",
      "name": "string",
      "description": "string",
      "last_accessed": "datetime",
      "icon": "string"
    }
  ]
}
```

### 4. Get Project Details
**GET** `/api/projects/{project_id}`

**Response:**
```json
{
  "id": "string",
  "name": "string",
  "code": "string",
  "conversation_history": "array",
  "created_at": "datetime"
}
```

## MongoDB Collections

### Projects Collection
```json
{
  "_id": "ObjectId",
  "name": "string",
  "description": "string",
  "code": "string",
  "conversation_history": [
    {"role": "user|assistant", "content": "string"}
  ],
  "created_at": "datetime",
  "updated_at": "datetime",
  "last_accessed": "datetime",
  "icon": "string"
}
```

## OpenRouter Integration

### Configuration
- Base URL: `https://openrouter.ai/api/v1`
- API Key: Provided by user (stored in `.env`)
- Model: `deepseek/deepseek-coder` or `anthropic/claude-3.7-sonnet`

### Prompt Engineering
System prompt for code generation:
```
You are an expert full-stack developer specializing in React, HTML, CSS, and JavaScript. 
Generate complete, production-ready code based on user requirements.
Return only valid React/JavaScript code that can be directly rendered.
Use modern React patterns with hooks.
Include Tailwind CSS for styling.
```

## Frontend-Backend Integration

### Steps:
1. **Remove Mock Delays**: Replace `setTimeout` with actual API calls
2. **Replace Mock Code**: Use backend-generated code instead of `mockGeneratedCode`
3. **API Integration Points**:
   - `ChatInterface.jsx` → Call `/api/generate-code` when user submits prompt
   - `Sidebar.jsx` → Call `/api/projects` to load real project list
   - `App.js` → Handle project state management with backend data

### Environment Variables
Backend `.env`:
```
OPENROUTER_API_KEY=sk-or-v1-...
OPENROUTER_MODEL=deepseek/deepseek-coder
```

## Error Handling
- API rate limiting
- Network failures
- Invalid code generation
- Database connection issues

## Testing Checklist
- [ ] OpenRouter API connection
- [ ] Code generation quality
- [ ] Live preview rendering
- [ ] Project save/load
- [ ] Conversation history persistence
- [ ] Error handling
