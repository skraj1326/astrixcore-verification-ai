# AstrixCore Verification AI

**AI-assisted verification from RTL to coverage closure.**

## Overview

AstrixCore Verification AI is an AI-native verification engineering platform designed to help semiconductor engineers verify RTL. It implements a complete verification loop:

```
RTL → Design Understanding → Verification Planning → Assertion Generation → Test Generation → Simulation → Log Analysis → Failure Analysis → Coverage Analysis → Coverage Gap Detection → Targeted Test Generation → Regression → Traceability → Verification Closure
```

## Features

### Core Capabilities
- **RTL Analysis**: Parse SystemVerilog/Verilog, extract modules, ports, signals, clocks, resets, FSMs, FIFOs, protocols
- **Verification Planning**: Auto-generate traceable verification plans (RTL-derived, Spec-derived, AI-inferred)
- **SVA Generation**: Generate SystemVerilog Assertions with evidence, confidence levels, false-positive warnings
- **Test Generation**: Directed, constrained-random, UVM tests with stated verification objectives
- **Simulation**: Verilator adapter (Icarus fallback), real compilation & execution
- **Log Analysis**: Deterministic parser for errors, warnings, assertion failures, UVM issues
- **Failure Analysis**: Root cause hypotheses with FACT/HYPOTHESIS separation
- **Coverage Intelligence**: Line/branch/toggle/FSM/functional/assertion coverage with gap classification
- **Closed-Loop AI**: Coverage gaps → targeted tests → simulate → measure → repeat until closure
- **Traceability**: Requirement → Plan → Assertion → Test → Simulation → Failure → Coverage

### AI Integration
- Provider abstraction (Mock, OpenAI-compatible)
- Works offline with mock provider
- Modular AI agents for RTL analysis, planning, assertions, tests, debug, coverage

## Quick Start

### Using Docker (Recommended)
```bash
docker compose up --build
```
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

### Local Development

#### Backend
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
# Edit .env as needed
uvicorn app.main:app --reload --port 8000
```

#### Frontend
```bash
cd frontend
npm install
npm run dev
```

## FIFO Demo

The platform includes a parameterized synchronous FIFO example (`examples/fifo/fifo.sv`) with:
- Built-in SVA assertions
- Cover properties
- Full verification flow demonstration

Click **"Analyze FIFO Demo"** on the dashboard to run the complete flow:
1. Load FIFO RTL
2. Create project
3. Analyze RTL
4. Generate verification plan (12 items VP-001 through VP-012)
5. Generate SVA assertions (8+ assertions)
6. Generate directed tests (12 test scenarios)
7. Generate UVM testbench structure
8. Update dashboard with all artifacts

## Architecture

```
astrixcore-verification-ai/
├── backend/
│   ├── app/
│   │   ├── api/v1/           # FastAPI endpoints
│   │   ├── engines/          # Core verification engines
│   │   │   ├── rtl.py              # RTL parser
│   │   │   ├── verification_planner.py
│   │   │   ├── assertion_generator.py
│   │   │   ├── test_generator.py
│   │   │   ├── simulation.py       # Verilator adapter
│   │   │   ├── logs.py             # Log analyzer
│   │   │   ├── coverage.py         # Coverage engine
│   │   │   └── traceability.py
│   │   ├── orchestrator/     # VerificationOrchestrator
│   │   ├── ai/               # AI providers & agents
│   │   ├── models/           # SQLAlchemy models
│   │   ├── schemas/          # Pydantic schemas
│   │   └── main.py           # FastAPI app
│   ├── tests/                # Pytest tests
│   └── requirements.txt
├── frontend/
│   ├── app/                  # Next.js 14 App Router pages
│   ├── components/           # React components
│   └── lib/                  # Utilities & API client
├── examples/fifo/            # FIFO demo RTL
└── docker-compose.yml
```

## API Endpoints

| Endpoint | Description |
|----------|-------------|
| `GET /api/v1/health` | Health check |
| `POST /api/v1/projects/` | Create project |
| `GET /api/v1/projects/` | List projects |
| `POST /api/v1/rtl/analyze` | Analyze RTL |
| `GET /api/v1/rtl/examples/fifo` | Get FIFO example |
| `POST /api/v1/verification/plan` | Generate verification plan |
| `POST /api/v1/verification/assertions` | Generate SVA assertions |
| `POST /api/v1/verification/tests` | Generate tests |
| `POST /api/v1/verification/uvm` | Generate UVM components |
| `POST /api/v1/verification/full-flow` | Complete verification flow |
| `POST /api/v1/simulation/run` | Run simulation |
| `POST /api/v1/simulation/analyze-log` | Analyze simulation log |
| `POST /api/v1/failures/analyze` | Analyze failure |
| `POST /api/v1/coverage/analyze` | Analyze coverage |
| `POST /api/v1/coverage/generate-targeted-tests` | Generate targeted tests |
| `POST /api/v1/traceability/link` | Create traceability link |
| `GET /api/v1/traceability/` | Get traceability matrix |
| `POST /api/v1/regression/run` | Run regression |

## Technology Stack

### Backend
- Python 3.11+
- FastAPI 0.95, Pydantic 1.10, SQLAlchemy 2.0
- SQLite (dev) / PostgreSQL (prod)
- Verilator / Icarus Verilog
- Pytest for testing

### Frontend
- Next.js 14, React 18, TypeScript
- Tailwind CSS
- Zustand (state management)
- React CodeMirror (RTL editor)
- Recharts (coverage charts)
- Lucide React (icons)

## Security

- Filename sanitization
- File size limits (10MB)
- Safe subprocess execution
- Environment variable secrets
- No API key logging
- CORS configuration

## Testing

```bash
# Backend tests
cd backend
python -m pytest tests/ -v

# Frontend build (requires Node.js)
cd frontend
npm install
npm run build
```

## Limitations (V0.1)

- Single clock domain FIFO example
- Mock AI provider for offline use
- SQLite database (PostgreSQL for production)
- Verilator required for real simulation
- No waveform viewer (planned)
- No formal verification integration (planned)

## Roadmap

- [ ] Multi-clock domain support
- [ ] Formal verification integration (Jasper, VC Formal)
- [ ] Waveform viewer (VCD/FST)
- [ ] RAG-based specification ingestion
- [ ] Multi-agent AI orchestration
- [ ] Commercial simulator adapters (Questa, VCS, Xcelium)
- [ ] Coverage database integration (UCIS)
- [ ] CI/CD pipeline integration
- [ ] Team collaboration features

## License

Proprietary - AstrixCore Semiconductors