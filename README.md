# SIMCO

**Gas Scrubbing & Mass-transfer Calculator** — a robust chemical and mechanical simulation tool for scrubbing, stripping, and chemical absorption processes.

## Overview

SIMCO provides rigorous thermodynamic and mass-transfer calculations for gas absorption/stripping column design. Built for process engineers, students, and consultants who need accurate results without the overhead of full-suite process simulators.

## Core Capabilities

- **VLE (Vapor-Liquid Equilibrium)**: Antoine equation, NRTL activity coefficients, ideal gas law, Henry's law
- **Column Design**: Packed column sizing (HTU/NTU), tray column design (coming soon)
- **Chemical Database**: Built-in SQLite database with Antoine coefficients, NRTL binary parameters, Henry's law constants, and packing characteristics
- **Project Files**: Save/load simulation configurations as `.smc` files

## Tech Stack

- **Engine**: Python (thermodynamics, mass transfer, database)
- **Frontend**: Electron + React (desktop UI)
- **Database**: SQLite (chemical properties)
- **IPC Bridge**: Electron ↔ Python communication layer

## Project Structure

```
SIMCO/
├── engine/                 # Python calculation engine
│   ├── thermo/             # Thermodynamic models
│   ├── database/           # Chemical property database
│   ├── api/routes/         # API endpoints
│   └── tests/              # Test suite
├── ui/                     # Electron + React frontend
│   ├── src/
│   │   ├── components/     # Reusable UI components
│   │   ├── pages/          # Application pages
│   │   ├── assets/         # Icons, images
│   │   └── utils/          # Frontend utilities
│   └── public/
├── tasks/                  # Project management
│   ├── architecture.md     # System architecture
│   ├── todo.md             # Current sprint tasks
│   └── lessons.md          # Patterns & lessons learned
└── docs/                   # Documentation
```

## Getting Started

### Prerequisites
- Python 3.10+
- Node.js 18+

### Engine Setup
```bash
cd engine
pip install -r requirements.txt
python -m pytest tests/ -v
```

## License

MIT
