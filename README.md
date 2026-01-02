# Tyre Pyrolysis Manufacturing ERP

A comprehensive 360° ERP system for tyre pyrolysis plants.

![Dashboard](https://img.shields.io/badge/Status-Demo%20Ready-brightgreen)

## 🚀 Live Demo

**Login Credentials:**
- Username: `admin`
- Password: `admin123`

## ✨ Features

- **Procurement**: Vendors, Purchase Orders, GRN with deduction handling
- **Production**: Reactor management, batch tracking, FIFO inventory
- **Tank Farm**: Oil storage tanks, level monitoring, transfers
- **Sales**: Quotations → Orders → Dispatches → Invoices
- **Maintenance**: Preventive schedules, request ticketing, spare parts
- **Reports**: Financial analytics, vendor yield, production metrics
- **Dashboard**: Real-time KPIs, alerts, activity feed

## 🛠️ Tech Stack

| Layer | Technology |
|-------|------------|
| Backend | FastAPI (Python 3.9+) |
| Database | SQLite + SQLAlchemy ORM |
| Frontend | Vue 3 + Vite |
| Auth | JWT with role-based access |

## 📦 Local Development

### Backend
```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

### Frontend
```bash
cd frontend
npm install
npm run dev
```

Access:
- Frontend: http://localhost:5173
- Backend API: http://localhost:8000/docs

## 📚 Documentation

- [AI Agent Context](docs/AI_CONTEXT.md) - For AI coding assistants
- [Developer Guide](docs/DEVELOPER_GUIDE.md) - Full architecture & API reference
- [Architecture](docs/architecture.md) - System design

## 📄 License

Proprietary - Demo purposes only
