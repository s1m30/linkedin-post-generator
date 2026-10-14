# Linkedin Generator
## Objectives:
- To generate posts and carousel content giving a title (for carousel), web sources (optional), rough draft (optional), my previous posts (optional)

- To refine posts based on a rough draft I provide or the already generated post. (I should be able to refine until I am satisfied)

- To have a manual option or automatic (in this case the timeline will be set using a calendar.

- For automatic, it will be connected to windows notification to give me notificatio0ns when it is done.

- The carousel will be different from the posts because it will be in several numbered sections (defined by the user) and it's major goal is to share informative content on a particular topic.

Using a layered architecture with FastAPI, SQLite, APScheduler, and a premium glassmorphic frontend, the project implements a clean, domain-driven structure:

```
backend/
├── app/
│   ├── main.py                  # FastAPI app and background scheduler startup
│   ├── core/                    # Global configs and environment validation
│   │   └── config.py
│   ├── database/                # SQLite connection and session lifecycle
│   │   └── session.py
│   ├── static/                  # Single Page App (SPA) dashboard
│   │   ├── index.html           # Glassmorphic layout
│   │   ├── style.css            # Dark mode variables & animations
│   │   └── app.js               # Frontend visual state & API logic
│   └── modules/                 # Modular feature domains
│       ├── posts/
│       │   ├── router.py        # Post & Carousel API endpoints
│       │   ├── schemas.py       # Pydantic validation models
│       │   ├── models.py        # SQLAlchemy SQLite tables
│       │   └── service.py       # Post CRUD, LLM prompt orchestration, and url scraper
│       ├── ai/
│       │   ├── engine.py        # LangChain Google GenAI wrapper
│       │   └── prompts.py       # LinkedIn copywriting system templates
│       └── scheduler/
│           ├── tasks.py         # APScheduler background post runner
│           └── notifier.py      # Local Windows PowerShell Toast alerts
├── tests/
│   └── test_flow.py             # Integration test suite
├── .env.template                # Global environment settings template
└── requirements.txt             # Project requirements
```

## How to Run

1. **Setup Environment**:
   - Copy `backend/.env.template` to `backend/.env` (done automatically during setup).
   - Open `backend/.env` and insert your **`GEMINI_API_KEY`**.

2. **Start the FastAPI Server**:
   - Run the following command from the workspace root:
     ```bash
     python -m uvicorn backend.app.main:app --reload
     ```
   - Alternatively, navigate to the `backend/` directory and run:
     ```bash
     python -m uvicorn app.main:app --reload
     ```

3. **Open the App Dashboard**:
   - Open your browser and navigate to: [http://127.0.0.1:8000](http://127.0.0.1:8000)
   - Enjoy creating, scheduling, and refining posts!

## Running Tests

To run the integration test suite, execute:
```bash
pytest backend/tests/test_flow.py
```