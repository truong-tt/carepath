# CarePath Interpreter

Live Vietnamese <-> English medical interpreter MVP.

This app is a translation-and-verification aid. It must not generate medical advice,
diagnoses, or drug recommendations.

## Backend

```powershell
cd backend
python -m pip install -e ".[dev]"
uvicorn app.main:app --reload
pytest
```

Health check: `GET /api/health`.

## Frontend

```powershell
cd frontend
npm.cmd install
npm.cmd run dev
npm.cmd test
```

## Mock Mode

Copy `.env.example` to `.env` and keep:

```env
PROVIDER_MODE=mock
```

Mock mode must run without API keys.

## Eval

```powershell
python eval\run_eval.py --set eval\fixtures\eval_starter.tsv --providers mock
```
