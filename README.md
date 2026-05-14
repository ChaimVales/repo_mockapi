# Zchat Mock API

A mock FastAPI server that simulates the Zchat backend API for local frontend development. Responses are hardcoded — no real logic is implemented.

## Stack

- **Python** + **FastAPI**
- **Uvicorn** (ASGI server)
- **Pydantic** (request/response validation)

## Project Structure

```
app/
├── main.py           # App factory, CORS, router registration
├── mocks/
│   └── scenarios.py  # Mock scenarios and keyword matching
├── models/
│   └── schemas.py    # Pydantic models (ChatRequest, ChatResponse, Entity)
└── routers/
    └── chat.py       # POST /chat endpoint
requirements.txt
run.py                # Entry point
```

## Getting Started

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Run the server

```bash
python run.py
```

The API will be available at `http://localhost:8000`.  
Interactive docs at `http://localhost:8000/docs`.

---

## Endpoint

### `POST /chat`

#### Headers

| Header | Required |
|--------|----------|
| `api-key` | ✅ — any non-empty string is accepted |
| `user-personal-number` | ✅ — any non-empty string is accepted |

#### Request Body

```json
{
  "message": "string",
  "session_id": "string | null",
  "unit": "string | null",
  "reality": "string | null",
  "module": "string | null",
  "role": "string | null",
  "plan": "string | null",
  "case": "string | null"
}
```

#### Response Body

```json
{
  "response": "string",
  "session_id": "string",
  "needs_clarification": "bool",
  "clarify_for": "string | null",
  "reasoning_content": "string | null",
  "entities": [
    {
      "layer": "string | null",
      "entity_id": "string | null",
      "geometry": "string | null"
    }
  ]
}
```

#### Notes

- `session_id` is optional on the first request — a new one will be generated automatically. Pass it back on subsequent requests to maintain conversation context.
- `entities` contains map entities to be rendered on the frontend.
- `geometry` is a **WKT string** using **lat/lon (WGS84)** coordinates in the order `latitude longitude`. Supported geometry types:

| Type | Example |
|------|---------|
| Point | `POINT (32.0853 34.7818)` |
| Line | `LINESTRING (32.08 34.77, 32.09 34.78)` |
| Polygon | `POLYGON ((32.08 34.77, 32.09 34.77, 32.09 34.78, 32.08 34.77))` |

---

## Mock Scenarios

The mock matches keywords in the message and returns a relevant scenario:

| Keywords | Scenario |
|----------|----------|
| `איפה`, `מיקום` | Single point entity (location question) |
| `קרוב`, `קרובים`, `ליד` | Multiple point entities with distances (proximity question) |
| `רשימה`, `כוחות`, `גזרה` | Multiple point entities (list question) |
| `סטטוס`, `מצב` | Single entity with status info |
| `מנחת`, `נחיתה` | Landing pad recommendation with alternatives |
| `אזור`, `פוליגון`, `גבול` | Polygon entity |
| `מסלול`, `דרך`, `קו` | LineString entity |
| *(anything else)* | Default mock response |

---

## CORS

All origins are allowed (`*`) for local development.
