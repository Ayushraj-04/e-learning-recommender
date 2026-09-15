# E-Learn — AI-Assisted Learning Resource Recommender

A Flask web application that searches YouTube and web resources for a learning topic, generates three prerequisite concepts with Gemini, and ranks resources using an explainable scoring layer.

## Architecture

```text
User
  │
  ▼
Flask
  │
  ├── Gemini → prerequisite generation
  │
  ├── YouTube Data API ──┐
  │                      ├── normalize → rank → render
  └── Google Custom Search┘
```

### Runtime resilience

- Small TTL cache reduces repeated external API calls within a server instance.
- Sliding-window rate limiting prevents a single client from flooding an instance.
- Provider failures are isolated so one failed API does not remove all results.

> Note: Vercel/serverless instances are ephemeral, so the in-memory cache and limiter are per instance. A production-scale deployment should move these controls to a shared store such as Redis/KV.

### Recommendation score

The current ranking is deliberately explainable:

- 50% — title/topic relevance
- 30% — quality/engagement signal
- 20% — requested duration match

This is a **rule-based recommendation/ranking system**, not a machine-learning recommender. That distinction is intentional and interview-safe.

## Important security setup

1. Rotate any API keys that were previously exposed.
2. Create `.env` locally from `.env.example`.
3. Never commit `.env`.
4. Keep `FLASK_DEBUG=0` in deployed environments.

## Run locally

```bash
cd backend
python -m venv .venv
# Windows:
.venv\Scripts\activate
# macOS/Linux:
# source .venv/bin/activate

pip install -r ../requirements.txt
python app.py
```

Open `http://127.0.0.1:5000`.

## Interview-ready talking points

- Why use an LLM? To generate topic-specific prerequisites dynamically.
- Why ranking? Raw API search order is not the same as application-level recommendation.
- Why concurrent fetching? YouTube and web search are independent I/O operations.
- Why fallback? External APIs are failure-prone; one provider should not take down the complete experience.
- Why rule-based scoring? It is transparent, deterministic, easy to explain and suitable for a small-scale recommender.
- Why not claim "highly rated"? The application only makes that claim when the underlying metadata actually supports a quality/engagement signal.

## Known limitations / future work

- Add caching to reduce repeated external API calls and latency.
- Add request rate limiting.
- Add automated tests for ranking, parsing and provider failures.
- Add a persistent database for search history/user preferences.
- Add richer web-resource metadata if a reliable source provides it.
- Replace lexical relevance with embeddings only if the project genuinely needs semantic matching.
