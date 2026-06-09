# Professional Chef Agent — API Contract Specification

**Version:** 1.0
**Date:** June 8, 2026
**Authors:** Backend Architect, Mobile Engineer
**Status:** Draft — Pending Stakeholder Review

---

## 1. Overview

This document defines the contract between the React Native (Expo) mobile client and the FastAPI backend. Both teams build against this spec — the backend implements it, the mobile app consumes it. Any changes require both teams to sign off.

**Base URL:**

```
Development:  http://localhost:8000/api/v1
Staging:      https://api-staging.chefagent.app/api/v1
Production:   https://api.chefagent.app/api/v1
```

**Admin Base URL (not consumed by mobile app):**

```
Development:  http://localhost:8000/admin/v1
Production:   https://api.chefagent.app/admin/v1 (authenticated)
```

---

## 2. Common Conventions

### 2.1 Request Headers

| Header | Required | Value | Notes |
|---|---|---|---|
| Content-Type | Yes | `application/json` or `multipart/form-data` | `multipart/form-data` for photo uploads only |
| X-Session-ID | Yes | UUID v4 | Generated client-side per user session, used for audit trail |
| X-Device-Platform | Yes | `ios` or `android` | Analytics and debugging |
| X-App-Version | Yes | Semver string (e.g., `1.0.0`) | Version gating |
| Authorization | Phase 2 | `Bearer <jwt_token>` | Required once user auth is implemented |

### 2.2 Standard Response Envelope

Every response follows a consistent envelope:

```json
{
  "success": true,
  "data": { ... },
  "error": null,
  "meta": {
    "request_id": "uuid-v4",
    "timestamp": "2026-06-08T14:30:00Z",
    "latency_ms": 1234
  }
}
```

**Error response:**

```json
{
  "success": false,
  "data": null,
  "error": {
    "code": "INGREDIENT_DETECTION_FAILED",
    "message": "Unable to detect ingredients from the provided image.",
    "details": "The image was too dark to process. Try taking the photo with better lighting."
  },
  "meta": {
    "request_id": "uuid-v4",
    "timestamp": "2026-06-08T14:30:00Z",
    "latency_ms": 523
  }
}
```

### 2.3 Standard Error Codes

| HTTP Status | Error Code | When |
|---|---|---|
| 400 | `VALIDATION_ERROR` | Request body fails schema validation |
| 400 | `INVALID_IMAGE_FORMAT` | Uploaded file is not JPEG/PNG/HEIC |
| 400 | `IMAGE_TOO_LARGE` | Image exceeds 10MB limit |
| 400 | `TOO_MANY_IMAGES` | More than 3 images in a single detect request |
| 400 | `INSUFFICIENT_INGREDIENTS` | Fewer than 2 confirmed ingredients for recipe generation |
| 404 | `RECIPE_NOT_FOUND` | Requested recipe ID does not exist |
| 404 | `SESSION_NOT_FOUND` | Referenced session ID does not exist |
| 408 | `LLM_TIMEOUT` | Ollama/LLM provider did not respond within timeout |
| 422 | `DETECTION_FAILED` | OpenAI Vision could not process the image |
| 429 | `RATE_LIMITED` | Too many requests — retry after header provided |
| 500 | `INTERNAL_ERROR` | Unexpected server error |
| 502 | `LLM_UNAVAILABLE` | Ollama/LLM provider is unreachable |
| 502 | `OPENAI_UNAVAILABLE` | OpenAI API is unreachable after retries |
| 503 | `SERVICE_DEGRADED` | One or more dependencies unhealthy |

### 2.4 Pagination (where applicable)

```json
{
  "data": [...],
  "pagination": {
    "page": 1,
    "per_page": 20,
    "total_items": 145,
    "total_pages": 8
  }
}
```

---

## 3. Endpoint Reference

---

### 3.1 Health Check

```
GET /api/v1/health
```

**Purpose:** Verify service health and dependency connectivity. Mobile app calls this on launch and after network recovery.

**Request:** No body or parameters.

**Response (200 OK):**

```json
{
  "success": true,
  "data": {
    "status": "healthy",
    "version": "1.0.0",
    "dependencies": {
      "postgres": { "status": "connected", "latency_ms": 2 },
      "redis": { "status": "connected", "latency_ms": 1 },
      "llm": {
        "status": "connected",
        "provider": "ollama",
        "model": "llama3.1:8b-instruct-q4_0",
        "latency_ms": 15
      },
      "openai": { "status": "reachable", "latency_ms": 120 }
    }
  }
}
```

**Response (503 Service Degraded):**

```json
{
  "success": false,
  "data": {
    "status": "degraded",
    "version": "1.0.0",
    "dependencies": {
      "postgres": { "status": "connected", "latency_ms": 2 },
      "redis": { "status": "connected", "latency_ms": 1 },
      "llm": { "status": "unreachable", "error": "Connection refused" },
      "openai": { "status": "reachable", "latency_ms": 120 }
    }
  }
}
```

---

### 3.2 Ingredient Detection

```
POST /api/v1/detect
```

**Purpose:** Upload 1–3 fridge photos and receive a list of detected ingredients with confidence scores and categories.

**Request (multipart/form-data):**

| Field | Type | Required | Constraints |
|---|---|---|---|
| images | File[] | Yes | 1–3 files, JPEG/PNG/HEIC, max 10MB each |

**Response (200 OK):**

```json
{
  "success": true,
  "data": {
    "session_id": "550e8400-e29b-41d4-a716-446655440000",
    "detected_ingredients": [
      {
        "name": "chicken breast",
        "confidence": "high",
        "category": "protein",
        "interchangeable": true,
        "interchangeable_group": "poultry"
      },
      {
        "name": "broccoli",
        "confidence": "high",
        "category": "produce",
        "interchangeable": false,
        "interchangeable_group": null
      },
      {
        "name": "soy sauce",
        "confidence": "medium",
        "category": "spice",
        "interchangeable": false,
        "interchangeable_group": null
      },
      {
        "name": "unknown item",
        "confidence": "low",
        "category": "unknown",
        "interchangeable": false,
        "interchangeable_group": null
      }
    ],
    "photo_count": 2,
    "processing_time_ms": 3200
  }
}
```

**Error Scenarios:**

| Scenario | Status | Error Code |
|---|---|---|
| No images uploaded | 400 | `VALIDATION_ERROR` |
| Image not JPEG/PNG/HEIC | 400 | `INVALID_IMAGE_FORMAT` |
| Image over 10MB | 400 | `IMAGE_TOO_LARGE` |
| More than 3 images | 400 | `TOO_MANY_IMAGES` |
| OpenAI API failure | 502 | `OPENAI_UNAVAILABLE` |
| Vision returned no results | 422 | `DETECTION_FAILED` |

**Performance Target:** < 5 seconds

---

### 3.3 Ingredient Confirmation

```
POST /api/v1/confirm
```

**Purpose:** Submit the user's edited ingredient list after reviewing detection results. This is the confirmed input for recipe generation.

**Request (application/json):**

```json
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "confirmed_ingredients": [
    {
      "name": "chicken breast",
      "category": "protein",
      "interchangeable": true,
      "interchangeable_group": "poultry"
    },
    {
      "name": "broccoli",
      "category": "produce",
      "interchangeable": false,
      "interchangeable_group": null
    },
    {
      "name": "garlic",
      "category": "produce",
      "interchangeable": true,
      "interchangeable_group": "allium"
    }
  ],
  "removed_ingredients": ["unknown item", "soy sauce"],
  "added_ingredients": [
    {
      "name": "garlic",
      "category": "produce",
      "interchangeable": true,
      "interchangeable_group": "allium"
    }
  ]
}
```

**Response (200 OK):**

```json
{
  "success": true,
  "data": {
    "session_id": "550e8400-e29b-41d4-a716-446655440000",
    "confirmed_count": 3,
    "removed_count": 2,
    "added_count": 1,
    "ready_for_generation": true
  }
}
```

**Validation Rules:**
- `session_id` must reference an existing detection session
- `confirmed_ingredients` must contain at least 2 items
- Each ingredient must have a valid `category` value

---

### 3.4 Recipe Generation

```
POST /api/v1/generate
```

**Purpose:** Generate 3–5 recipes from confirmed ingredients, skill level, and dietary restrictions. Returns cached results when available.

**Request (application/json):**

```json
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "skill_level": "intermediate",
  "dietary_restrictions": ["gluten_free"],
  "custom_restrictions": null,
  "force_fresh": false
}
```

| Field | Type | Required | Notes |
|---|---|---|---|
| session_id | UUID | Yes | Must have confirmed ingredients |
| skill_level | enum | Yes | `beginner`, `intermediate`, `advanced` |
| dietary_restrictions | string[] | No | From predefined enum list |
| custom_restrictions | string | No | Free-text, max 200 characters |
| force_fresh | boolean | No | Default `false`. Set `true` to bypass cache. |

**Response (200 OK):**

```json
{
  "success": true,
  "data": {
    "session_id": "550e8400-e29b-41d4-a716-446655440000",
    "cache_hit": false,
    "recipes": [
      {
        "id": "recipe-uuid-001",
        "title": "Garlic Chicken Stir-Fry with Broccoli",
        "cuisine": "Chinese",
        "difficulty": "intermediate",
        "prep_time_minutes": 10,
        "cook_time_minutes": 15,
        "total_time_minutes": 25,
        "servings": 2,
        "ingredients": [
          {
            "name": "chicken breast",
            "quantity": "2",
            "unit": "pieces",
            "from_detected": true,
            "assumed_available": false
          },
          {
            "name": "broccoli",
            "quantity": "2",
            "unit": "cups",
            "from_detected": true,
            "assumed_available": false
          },
          {
            "name": "garlic",
            "quantity": "4",
            "unit": "cloves",
            "from_detected": true,
            "assumed_available": false
          },
          {
            "name": "vegetable oil",
            "quantity": "2",
            "unit": "tablespoons",
            "from_detected": false,
            "assumed_available": true
          },
          {
            "name": "salt",
            "quantity": "1",
            "unit": "teaspoon",
            "from_detected": false,
            "assumed_available": true
          }
        ],
        "steps": [
          {
            "step_number": 1,
            "instruction": "Slice the chicken breast into thin strips against the grain. Season lightly with salt.",
            "duration_minutes": null,
            "technique": "knife skills"
          },
          {
            "step_number": 2,
            "instruction": "Cut the broccoli into bite-sized florets. Mince the garlic cloves.",
            "duration_minutes": null,
            "technique": "prep"
          },
          {
            "step_number": 3,
            "instruction": "Heat vegetable oil in a wok or large skillet over high heat until the oil shimmers.",
            "duration_minutes": 2,
            "technique": "sauté"
          },
          {
            "step_number": 4,
            "instruction": "Add the chicken strips in a single layer. Cook without stirring for 2 minutes until golden on one side, then flip and cook another 2 minutes.",
            "duration_minutes": 4,
            "technique": "sear"
          },
          {
            "step_number": 5,
            "instruction": "Add the broccoli and minced garlic. Stir-fry for 3-4 minutes until broccoli is bright green and tender-crisp.",
            "duration_minutes": 4,
            "technique": "stir-fry"
          },
          {
            "step_number": 6,
            "instruction": "Season with salt to taste. Serve immediately.",
            "duration_minutes": null,
            "technique": null
          }
        ],
        "missing_ingredients": ["vegetable oil", "salt"],
        "dietary_tags": ["gluten_free"]
      }
    ],
    "recipe_count": 3,
    "generation_time_ms": 12500
  }
}
```

**Notes:**
- `recipes` array contains 3–5 recipe objects (example above shows 1 for brevity)
- `cache_hit: true` means results came from Redis (generation_time_ms will be < 500)
- `missing_ingredients` will contain at most 2 items, all assumed pantry staples
- All recipes respect `dietary_restrictions` — hard constraint, never violated
- Recipes span at least 2 different cuisines when 3+ recipes returned

**Error Scenarios:**

| Scenario | Status | Error Code |
|---|---|---|
| Session has no confirmed ingredients | 400 | `VALIDATION_ERROR` |
| Fewer than 2 ingredients confirmed | 400 | `INSUFFICIENT_INGREDIENTS` |
| Invalid skill level | 400 | `VALIDATION_ERROR` |
| Ollama/LLM unreachable | 502 | `LLM_UNAVAILABLE` |
| LLM timeout (> 30s) | 408 | `LLM_TIMEOUT` |

**Performance Target:** < 500ms (cache hit), < 15s (cache miss — all 3–5 recipes generated in a single LLM call)

**Generation approach:** All recipes generated in one batch LLM request. Mobile shows a single loading state until the full set is returned.

---

### 3.5 Recipe Detail

```
GET /api/v1/recipes/{recipe_id}
```

**Purpose:** Retrieve full details for a specific recipe. Used when user taps a recipe card.

**Path Parameters:**

| Parameter | Type | Required |
|---|---|---|
| recipe_id | UUID | Yes |

**Response (200 OK):**

Same recipe object structure as in the `/generate` response, wrapped in the standard envelope.

**Error:** 404 `RECIPE_NOT_FOUND` if ID doesn't exist.

---

### 3.6 Cook Mode — Get Steps

```
GET /api/v1/cook/{recipe_id}/steps
```

**Purpose:** Retrieve recipe steps formatted for cook mode UI. Returns the same steps as the recipe detail but with additional cook-mode metadata.

**Path Parameters:**

| Parameter | Type | Required |
|---|---|---|
| recipe_id | UUID | Yes |

**Response (200 OK):**

```json
{
  "success": true,
  "data": {
    "recipe_id": "recipe-uuid-001",
    "recipe_title": "Garlic Chicken Stir-Fry with Broccoli",
    "total_steps": 6,
    "total_cook_time_minutes": 25,
    "steps": [
      {
        "step_number": 1,
        "instruction": "Slice the chicken breast into thin strips against the grain. Season lightly with salt.",
        "duration_minutes": null,
        "technique": "knife skills",
        "has_timer": false,
        "ingredients_used": [
          { "name": "chicken breast", "quantity": "2", "unit": "pieces" },
          { "name": "salt", "quantity": "1", "unit": "teaspoon" }
        ]
      },
      {
        "step_number": 3,
        "instruction": "Heat vegetable oil in a wok or large skillet over high heat until the oil shimmers.",
        "duration_minutes": 2,
        "technique": "sauté",
        "has_timer": true,
        "timer_seconds": 120,
        "ingredients_used": [
          { "name": "vegetable oil", "quantity": "2", "unit": "tablespoons" }
        ]
      }
    ],
    "cook_session_id": "cook-session-uuid-001"
  }
}
```

**Notes:**
- `has_timer: true` when `duration_minutes` is set — mobile app shows a tap-to-start timer
- `timer_seconds` is the pre-computed value for the timer UI
- `ingredients_used` per step lets the mobile app highlight relevant ingredients
- `cook_session_id` is generated server-side for tracking cook completion

---

### 3.7 Submit Feedback

```
POST /api/v1/feedback
```

**Purpose:** Submit user feedback on a cooked recipe. Links to the full audit chain for governance and future fine-tuning.

**Request (application/json):**

```json
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "recipe_id": "recipe-uuid-001",
  "cook_session_id": "cook-session-uuid-001",
  "rating": "thumbs_up",
  "feedback_text": "Great recipe, family loved it!",
  "cook_completed": true
}
```

| Field | Type | Required | Notes |
|---|---|---|---|
| session_id | UUID | Yes | Original detection session |
| recipe_id | UUID | Yes | Recipe that was cooked |
| cook_session_id | UUID | Yes | From cook mode initiation |
| rating | enum | Yes | `thumbs_up` or `thumbs_down` |
| feedback_text | string | No | Max 500 characters |
| cook_completed | boolean | Yes | Did user finish all steps? |

**Response (200 OK):**

```json
{
  "success": true,
  "data": {
    "feedback_id": "feedback-uuid-001",
    "recorded": true
  }
}
```

---

### 3.8 Safety Flag

```
POST /api/v1/safety-flag
```

**Purpose:** Report a recipe as dangerous, incorrect, or containing allergens that should have been filtered.

**Request (application/json):**

```json
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "recipe_id": "recipe-uuid-001",
  "severity": "high",
  "reason": "allergen_violation",
  "description": "Recipe contains peanuts but I selected nut-free dietary restriction."
}
```

| Field | Type | Required | Notes |
|---|---|---|---|
| session_id | UUID | Yes | Original session |
| recipe_id | UUID | Yes | Flagged recipe |
| severity | enum | Yes | `low`, `medium`, `high`, `critical` |
| reason | enum | Yes | `allergen_violation`, `dangerous_instruction`, `incorrect_quantities`, `inedible_combination`, `other` |
| description | string | Yes | User description of the issue, max 1000 characters |

**Response (200 OK):**

```json
{
  "success": true,
  "data": {
    "flag_id": "flag-uuid-001",
    "recorded": true,
    "message": "Thank you for reporting this. Your feedback helps us improve recipe safety."
  }
}
```

---

## 4. Admin API Endpoints

These endpoints are consumed by internal tools and the QLoRA fine-tuning pipeline. They are not consumed by the mobile app.

---

### 4.1 Audit Logs

```
GET /admin/v1/audit-logs
```

**Query Parameters:**

| Parameter | Type | Required | Default | Notes |
|---|---|---|---|---|
| page | int | No | 1 | Page number |
| per_page | int | No | 20 | Max 100 |
| start_date | ISO 8601 | No | 7 days ago | Filter start |
| end_date | ISO 8601 | No | now | Filter end |
| session_id | UUID | No | — | Filter by specific session |
| cache_hit | boolean | No | — | Filter by cache hit/miss |

**Response (200 OK):**

```json
{
  "success": true,
  "data": {
    "logs": [
      {
        "session_id": "550e8400-e29b-41d4-a716-446655440000",
        "timestamp": "2026-06-08T14:30:00Z",
        "photo_hashes": ["sha256-abc123", "sha256-def456"],
        "detection_model": "gpt-4o-2024-08-06",
        "detection_prompt_version": "v1.0",
        "detected_ingredient_count": 8,
        "confirmed_ingredient_count": 6,
        "removed_count": 3,
        "added_count": 1,
        "skill_level": "intermediate",
        "dietary_restrictions": ["gluten_free"],
        "generation_model": "llama3.1:8b-instruct-q4_0",
        "generation_provider": "ollama",
        "generation_prompt_version": "v1.0",
        "cache_hit": false,
        "recipe_count": 4,
        "recipe_selected": "recipe-uuid-001",
        "cook_completed": true,
        "user_feedback": "thumbs_up",
        "flagged_safety": false
      }
    ]
  },
  "pagination": {
    "page": 1,
    "per_page": 20,
    "total_items": 145,
    "total_pages": 8
  }
}
```

---

### 4.2 Training Data Export

```
GET /admin/v1/training-data
```

**Purpose:** Export feedback-linked input/output pairs for QLoRA fine-tuning pipeline.

**Query Parameters:**

| Parameter | Type | Required | Default | Notes |
|---|---|---|---|---|
| feedback_filter | enum | No | `thumbs_up` | `thumbs_up`, `thumbs_down`, `all` |
| limit | int | No | 100 | Max 1000 per request |
| offset | int | No | 0 | For pagination |
| min_date | ISO 8601 | No | — | Filter start |
| model_version | string | No | — | Filter by specific model version |

**Response (200 OK):**

```json
{
  "success": true,
  "data": {
    "training_samples": [
      {
        "session_id": "550e8400-e29b-41d4-a716-446655440000",
        "input": {
          "confirmed_ingredients": ["chicken breast", "broccoli", "garlic"],
          "skill_level": "intermediate",
          "dietary_restrictions": ["gluten_free"],
          "prompt_version": "v1.0",
          "prompt_template": "You are a professional chef..."
        },
        "output": {
          "recipes": [{ "...full recipe objects..." }],
          "raw_llm_response": "..."
        },
        "feedback": {
          "rating": "thumbs_up",
          "text": "Great recipe!",
          "cook_completed": true
        },
        "model": {
          "name": "llama3.1:8b-instruct-q4_0",
          "provider": "ollama"
        },
        "timestamp": "2026-06-08T14:30:00Z"
      }
    ],
    "total_available": 342,
    "exported": 100
  }
}
```

---

### 4.3 Safety Flags

```
GET /admin/v1/safety-flags
```

**Query Parameters:**

| Parameter | Type | Required | Default |
|---|---|---|---|
| page | int | No | 1 |
| per_page | int | No | 20 |
| severity | enum | No | — |
| reason | enum | No | — |
| resolved | boolean | No | — |

**Response:** List of safety flag records with full audit chain references.

---

### 4.4 Cache Statistics

```
GET /admin/v1/cache-stats
```

**Response (200 OK):**

```json
{
  "success": true,
  "data": {
    "total_entries": 234,
    "memory_usage_mb": 12.5,
    "hit_rate_24h": 0.42,
    "hit_rate_7d": 0.38,
    "avg_ttl_remaining_hours": 48.2,
    "most_cached_ingredients": [
      { "name": "chicken breast", "appearances": 89 },
      { "name": "rice", "appearances": 76 },
      { "name": "onion", "appearances": 71 }
    ]
  }
}
```

---

### 4.5 Cache Flush

```
DELETE /admin/v1/cache
```

**Purpose:** Flush cache entries. Used when deploying new model versions or QLoRA adapters.

**Query Parameters:**

| Parameter | Type | Required | Notes |
|---|---|---|---|
| scope | enum | No | `all` (default), `expired`, `by_model` |
| model_version | string | No | Required when scope is `by_model` |

**Response (200 OK):**

```json
{
  "success": true,
  "data": {
    "flushed_entries": 234,
    "scope": "all"
  }
}
```

---

## 5. Pydantic Schema Reference

All request/response schemas are implemented as Pydantic v2 models. Below is the definitive list of shared enums and models.

### 5.1 Enums

```python
class SkillLevel(str, Enum):
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"

class DietaryRestriction(str, Enum):
    VEGETARIAN = "vegetarian"
    VEGAN = "vegan"
    GLUTEN_FREE = "gluten_free"
    DAIRY_FREE = "dairy_free"
    NUT_FREE = "nut_free"
    SHELLFISH_FREE = "shellfish_free"
    HALAL = "halal"
    KOSHER = "kosher"

class IngredientCategory(str, Enum):
    PROTEIN = "protein"
    PRODUCE = "produce"
    SPICE = "spice"
    DAIRY = "dairy"
    GRAIN = "grain"
    PANTRY_STAPLE = "pantry"
    UNKNOWN = "unknown"

class Confidence(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"

class FeedbackRating(str, Enum):
    THUMBS_UP = "thumbs_up"
    THUMBS_DOWN = "thumbs_down"

class SafetyFlagSeverity(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class SafetyFlagReason(str, Enum):
    ALLERGEN_VIOLATION = "allergen_violation"
    DANGEROUS_INSTRUCTION = "dangerous_instruction"
    INCORRECT_QUANTITIES = "incorrect_quantities"
    INEDIBLE_COMBINATION = "inedible_combination"
    OTHER = "other"
```

### 5.2 Core Models

```python
class DetectedIngredient(BaseModel):
    name: str
    confidence: Confidence
    category: IngredientCategory
    interchangeable: bool = False
    interchangeable_group: Optional[str] = None

class ConfirmedIngredient(BaseModel):
    name: str
    category: IngredientCategory
    interchangeable: bool = False
    interchangeable_group: Optional[str] = None

class RecipeIngredient(BaseModel):
    name: str
    quantity: str
    unit: str
    from_detected: bool
    assumed_available: bool

class RecipeStep(BaseModel):
    step_number: int
    instruction: str
    duration_minutes: Optional[int] = None
    technique: Optional[str] = None

class CookModeStep(RecipeStep):
    has_timer: bool = False
    timer_seconds: Optional[int] = None
    ingredients_used: list[RecipeIngredient] = []

class Recipe(BaseModel):
    id: str
    title: str
    cuisine: str
    difficulty: SkillLevel
    prep_time_minutes: int
    cook_time_minutes: int
    total_time_minutes: int
    servings: int
    ingredients: list[RecipeIngredient]
    steps: list[RecipeStep]
    missing_ingredients: list[str]
    dietary_tags: list[DietaryRestriction]
```

### 5.3 Request Models

```python
class ConfirmRequest(BaseModel):
    session_id: str
    confirmed_ingredients: list[ConfirmedIngredient]  # min 2
    removed_ingredients: list[str] = []
    added_ingredients: list[ConfirmedIngredient] = []

class GenerateRequest(BaseModel):
    session_id: str
    skill_level: SkillLevel
    dietary_restrictions: list[DietaryRestriction] = []
    custom_restrictions: Optional[str] = Field(None, max_length=200)
    force_fresh: bool = False

class FeedbackRequest(BaseModel):
    session_id: str
    recipe_id: str
    cook_session_id: str
    rating: FeedbackRating
    feedback_text: Optional[str] = Field(None, max_length=500)
    cook_completed: bool

class SafetyFlagRequest(BaseModel):
    session_id: str
    recipe_id: str
    severity: SafetyFlagSeverity
    reason: SafetyFlagReason
    description: str = Field(..., max_length=1000)
```

---

## 6. Rate Limiting

| Endpoint Group | Rate Limit | Window | Notes |
|---|---|---|---|
| /api/v1/detect | 10 requests | per minute | OpenAI token cost protection |
| /api/v1/generate | 20 requests | per minute | LLM compute protection |
| /api/v1/* (other) | 60 requests | per minute | General API protection |
| /admin/v1/* | 30 requests | per minute | Admin endpoints |

Rate limit headers included in every response:

```
X-RateLimit-Limit: 10
X-RateLimit-Remaining: 7
X-RateLimit-Reset: 1717858200
```

When rate limited, response includes `Retry-After` header with seconds to wait.

---

## 7. Generation Strategy — Batch, Not Streaming

### 7.1 Batch Generation (MVP — Confirmed)

All 3–5 recipes are generated in a single LLM call and returned together as one complete response. The mobile app shows a loading state until the full set is ready, then presents all recipe cards simultaneously for browsing.

**Why batch is correct here:**
- Users need to see all options before choosing — partial results create a confusing browsing experience
- A single loading state → full reveal is a cleaner, more intentional UX pattern
- The LLM generates better cuisine diversity when producing all recipes in one prompt context
- Simpler mobile implementation — no partial state management required

```
User taps Generate
       ↓
Loading state (single spinner)
       ↓
All 3–5 recipes arrive together
       ↓
Full recipe browse UI revealed
```

### 7.2 Streaming (Future Enhancement — Community Features)

Streaming is reserved for ambient content features where progressive loading is natural — for example a public "Favorite Recipe of the Week" board or a community discovery feed. In that context, users are browsing passively and recipes can populate incrementally without forcing a decision.

Reserved endpoint namespace:

```
WS /api/v1/community/stream
```

Not implemented in MVP or Phase 2 core features. Relevant only when community/social features are introduced in Phase 3.

---

## 8. Versioning Strategy

- API version in URL path: `/api/v1/`, `/api/v2/`
- Breaking changes increment the version number
- Old versions supported for minimum 6 months after deprecation notice
- `X-API-Deprecated: true` header added to deprecated version responses
- Mobile app checks `X-App-Version` minimum on health check response

---

## 9. Mobile Client Implementation Notes

### 9.1 Session Management

The mobile app generates a `X-Session-ID` (UUID v4) when the user taps "Scan Ingredients." This session ID is used across all subsequent requests in that cooking flow (detect → confirm → generate → cook → feedback). A new session starts when the user returns to the home screen and taps "Scan Ingredients" again.

### 9.2 Offline Cook Mode

Once `/cook/{recipe_id}/steps` returns successfully, the mobile app caches the full step data locally. Cook mode continues to function without network connectivity. Feedback submission is queued locally and sent when connectivity resumes.

### 9.3 Error Handling Strategy

| Error Type | Mobile App Behavior |
|---|---|
| Network unreachable | Show offline indicator, retry with exponential backoff |
| 400 Validation | Show user-friendly error message from `error.details` |
| 408 LLM Timeout | Show "Recipes are taking longer than usual" with retry button |
| 429 Rate Limited | Show "Please wait a moment" with countdown from `Retry-After` |
| 502 Service Down | Show "Service temporarily unavailable" with retry button |
| 500 Internal | Log error, show generic "Something went wrong" with retry |

### 9.4 Image Optimization

Before uploading, the mobile app should:
- Compress to JPEG at 80% quality
- Resize to max 2048px on longest edge
- Strip EXIF metadata (privacy)
- Target < 2MB per image after compression

---

## Approvals

| Role | Name | Status |
|---|---|---|
| Backend Architect | — | ✅ Author |
| Mobile Engineer | — | ✅ Co-author |
| Product Manager | — | ⬜ Pending |
| ML/AI Engineer | — | ⬜ Pending |
| QA Engineer | — | ⬜ Pending |
| CI/CD Engineer | — | ⬜ Pending |
