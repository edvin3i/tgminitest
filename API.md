# 🚀 API Documentation - Telegram Quiz NFT Platform

Complete REST API for quiz management with Telegram authentication.

---

## 📋 Base URL

```
Local: http://localhost:8000
Production: https://your-domain.com
```

---

## 🔐 Authentication

All protected endpoints require Telegram WebApp `initData` in the header:

```http
X-Telegram-Init-Data: query_id=...&user=...&auth_date=...&hash=...
```

### How to Get initData

In your Telegram WebApp:
```javascript
const initData = window.Telegram.WebApp.initData;
```

---

## 📚 API Endpoints

### 🎯 Quizzes

#### List Quizzes
```http
GET /api/v1/quizzes/
```

**Query Parameters:**
- `skip` (int, default=0) - Number of records to skip
- `limit` (int, default=100) - Max records to return
- `active_only` (bool, default=true) - Only return active quizzes

**Response:**
```json
[
  {
    "id": 1,
    "title": "Which Hogwarts House Are You?",
    "description": "Discover your Hogwarts house!",
    "image_url": "https://...",
    "is_active": true,
    "created_at": "2025-11-19T12:00:00Z",
    "question_count": 6
  }
]
```

#### Get Quiz Details
```http
GET /api/v1/quizzes/{quiz_id}
```

**Response:**
```json
{
  "id": 1,
  "title": "Which Hogwarts House Are You?",
  "description": "...",
  "image_url": "...",
  "is_active": true,
  "created_at": "...",
  "updated_at": "...",
  "questions": [
    {
      "id": 1,
      "text": "What's your favorite color?",
      "order_index": 0,
      "answers": [
        {
          "id": 1,
          "text": "Red & Gold",
          "result_type": "gryffindor",
          "weight": 3,
          "order_index": 0
        }
      ]
    }
  ],
  "result_types": [
    {
      "id": 1,
      "type_key": "gryffindor",
      "title": "Gryffindor",
      "description": "You are brave and daring!",
      "image_url": "..."
    }
  ]
}
```

#### Create Quiz (Admin Only)
```http
POST /api/v1/quizzes/
Headers: X-Telegram-Init-Data: <admin-initData>
```

**Request Body:**
```json
{
  "title": "My Quiz",
  "description": "Quiz description",
  "image_url": "https://...",
  "questions": [
    {
      "text": "Question 1?",
      "order_index": 0,
      "answers": [
        {
          "text": "Answer A",
          "result_type": "type_a",
          "weight": 2,
          "order_index": 0
        }
      ]
    }
  ],
  "result_types": [
    {
      "type_key": "type_a",
      "title": "Type A",
      "description": "You are Type A!",
      "image_url": "..."
    }
  ]
}
```

**Response:** `201 Created` with quiz details

#### Update Quiz (Admin Only)
```http
PATCH /api/v1/quizzes/{quiz_id}
Headers: X-Telegram-Init-Data: <admin-initData>
```

**Request Body (all fields optional):**
```json
{
  "title": "Updated Title",
  "description": "Updated description",
  "image_url": "...",
  "is_active": false
}
```

**Response:** `200 OK` with updated quiz

#### Delete Quiz (Admin Only)
```http
DELETE /api/v1/quizzes/{quiz_id}
Headers: X-Telegram-Init-Data: <admin-initData>
```

**Response:** `204 No Content`

#### Submit Quiz Answers
```http
POST /api/v1/quizzes/{quiz_id}/submit
Headers: X-Telegram-Init-Data: <initData>
```

**Request Body:**
```json
{
  "answer_ids": [1, 3, 5, 7, 9, 11]
}
```

**Response:**
```json
{
  "result_id": 42,
  "result_type": "gryffindor",
  "result_title": "Gryffindor",
  "result_description": "You are brave and daring!",
  "score": 18,
  "nft_minted": false
}
```

#### Get Quiz Results
```http
GET /api/v1/quizzes/{quiz_id}/results
Headers: X-Telegram-Init-Data: <initData>
```

**Query Parameters:**
- `limit` (int, default=10) - Max results to return

**Response:** Array of quiz results

---

### 👤 Users

#### Get Current User Profile
```http
GET /api/v1/users/me
Headers: X-Telegram-Init-Data: <initData>
```

**Response:**
```json
{
  "id": 1,
  "telegram_id": 123456789,
  "username": "john_doe",
  "first_name": "John",
  "last_name": "Doe",
  "is_admin": false,
  "created_at": "2025-11-19T12:00:00Z"
}
```

#### Get My Quiz Results
```http
GET /api/v1/users/me/results
Headers: X-Telegram-Init-Data: <initData>
```

**Query Parameters:**
- `limit` (int, default=20) - Max results to return

**Response:**
```json
[
  {
    "id": 1,
    "quiz_id": 1,
    "quiz_title": "Which Hogwarts House Are You?",
    "result_type": "gryffindor",
    "score": 18,
    "nft_minted": false,
    "nft_address": null,
    "completed_at": "2025-11-19T12:30:00Z"
  }
]
```

#### Get My Statistics
```http
GET /api/v1/users/me/stats
Headers: X-Telegram-Init-Data: <initData>
```

**Response:**
```json
{
  "total_quizzes_taken": 5,
  "total_nfts_minted": 2,
  "recent_results": [...]
}
```

---

## 🔧 Health Check

```http
GET /health
```

**Response:**
```json
{
  "status": "healthy",
  "database": "healthy",
  "environment": "development"
}
```

---

## 📖 Interactive Documentation

### Swagger UI
```
http://localhost:8000/api/docs
```

### ReDoc
```
http://localhost:8000/api/redoc
```

---

## ⚠️ Error Responses

### 400 Bad Request
```json
{
  "detail": "Invalid initData format"
}
```

### 401 Unauthorized
```json
{
  "detail": "Missing authentication header"
}
```

### 403 Forbidden
```json
{
  "detail": "Admin access required"
}
```

### 404 Not Found
```json
{
  "detail": "Quiz 123 not found"
}
```

### 422 Validation Error
```json
{
  "detail": [
    {
      "loc": ["body", "title"],
      "msg": "field required",
      "type": "value_error.missing"
    }
  ]
}
```

---

## 🧪 Testing the API

### Using cURL

```bash
# List quizzes
curl http://localhost:8000/api/v1/quizzes/

# Get quiz details
curl http://localhost:8000/api/v1/quizzes/1

# With authentication (requires valid initData)
curl -H "X-Telegram-Init-Data: ..." \
  http://localhost:8000/api/v1/users/me
```

### Using Python

```python
import httpx

async def test_api():
    async with httpx.AsyncClient() as client:
        # List quizzes
        response = await client.get("http://localhost:8000/api/v1/quizzes/")
        quizzes = response.json()

        # Get quiz details
        response = await client.get(f"http://localhost:8000/api/v1/quizzes/1")
        quiz = response.json()

        # With authentication
        headers = {"X-Telegram-Init-Data": "..."}
        response = await client.get(
            "http://localhost:8000/api/v1/users/me",
            headers=headers
        )
        user = response.json()
```

### Using JavaScript (Telegram WebApp)

```javascript
// In your Telegram WebApp
const initData = window.Telegram.WebApp.initData;

// Get user profile
fetch('https://api.your-domain.com/api/v1/users/me', {
  headers: {
    'X-Telegram-Init-Data': initData
  }
})
.then(res => res.json())
.then(user => console.log(user));

// Submit quiz
fetch('https://api.your-domain.com/api/v1/quizzes/1/submit', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'X-Telegram-Init-Data': initData
  },
  body: JSON.stringify({
    answer_ids: [1, 3, 5, 7, 9, 11]
  })
})
.then(res => res.json())
.then(result => console.log('Result:', result));
```

---

## 🚀 Running the API

### Development

```bash
# Start the API
make run-api

# Or manually
cd backend
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Production

```bash
uv run uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

---

## 📊 API Versioning

Current version: **v1**

All endpoints are prefixed with `/api/v1/`

Future versions will use `/api/v2/`, etc.

---

## 🔒 Security Notes

- All admin endpoints require `is_admin=true` in user profile
- Telegram signature is verified using HMAC-SHA256
- initData must be fresh (check `auth_date` timestamp)
- CORS is configured for allowed origins only
- Rate limiting recommended for production

---

## 📈 Rate Limits (Recommended for Production)

- `/api/v1/quizzes/` - 100 requests/minute
- `/api/v1/quizzes/{id}/submit` - 10 requests/minute
- `/api/v1/users/me/*` - 60 requests/minute

---

## 🎯 Coming in Phase 3

- `POST /api/v1/nft/mint` - Mint NFT for quiz result
- `GET /api/v1/nft/{address}` - Get NFT details
- `GET /api/v1/users/me/nfts` - List user's NFTs
- `POST /api/v1/webhooks/ton` - TON payment webhook

---

For more details, visit the interactive docs at `/api/docs` 🚀
