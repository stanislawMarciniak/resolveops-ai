# ResolveOps AI

ResolveOps AI is a production-oriented multi-agent platform for
investigating and resolving enterprise support cases across CRM,
legacy billing systems and internal policies.

## Development

### Backend

```bash
python -m venv .venv
source .venv/bin/activate

pip install --upgrade pip
pip install -e ".[dev]"

uvicorn app.main:app --reload
```
