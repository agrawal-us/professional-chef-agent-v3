# Professional Chef Agent

An AI-powered mobile cooking assistant that transforms your fridge contents into actionable, skill-appropriate recipes. Photograph your ingredients, confirm what's detected, set your skill level and dietary preferences, and get 3–5 curated recipes you can cook right now — with a guided step-by-step cook mode.

## Core Loop

```
Photo fridge → Detect ingredients (GPT-4o Vision) → Confirm list →
Set skill level + dietary restrictions → Generate 3–5 recipes (Llama 3.1 8B) →
Step-by-step cook mode
```

## Tech Stack

| Layer | Technology |
|---|---|
| Mobile | React Native + Expo (iOS 16+ / Android 12+) |
| Backend | FastAPI (Docker) |
| Cache | Redis (Docker) — recipe result cache with 72h TTL |
| Database | PostgreSQL (Docker) — audit trail, session logs, prompt registry |
| Vision AI | OpenAI GPT-4o — ingredient detection from photos |
| Generation AI | Ollama + Llama 3.1 8B (local dev) → AWS ECS/SageMaker (prod) |

## Project Documentation

All specification documents live in [`docs/`](./docs/):

| File | Description |
|---|---|
| [01-PRD.md](./docs/01-PRD.md) | Product Requirements Document — features, user flows, acceptance criteria |
| [02-system-architecture.md](./docs/02-system-architecture.md) | System architecture, component inventory, data models, Docker setup |
| [03-api-contract.md](./docs/03-api-contract.md) | API contract — all endpoints, request/response schemas, error codes |
| [04-wireframes.html](./docs/04-wireframes.html) | Interactive wireframes — 10 screens, open in browser |
| [05-ml-spec.md](./docs/05-ml-spec.md) | AI/ML specification — prompts, cache similarity algorithm, QLoRA roadmap |
| [06-test-strategy.md](./docs/06-test-strategy.md) | Test strategy — unit, integration, E2E, performance, device matrix |

## Iteration Plan

| Iteration | Scope | Status |
|---|---|---|
| 1 | Infrastructure: Docker + FastAPI + Redis + PostgreSQL connectivity | 🔜 Up next |
| 2 | Ingredient detection: OpenAI GPT-4o endpoint + audit logging | ⬜ |
| 3 | Recipe generation: Ollama integration + structured output + cache | ⬜ |
| 4 | Cook mode: step-by-step API + session management + governance trail | ⬜ |
| 5–6 | React Native (Expo) frontend — iOS + Android | ⬜ |
| 7 | QA + polish + audit verification | ⬜ |
| 8 | Internal beta — TestFlight distribution | ⬜ |
