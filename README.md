# ToDo App ✅

A full-stack ToDo application built with **FastAPI** for the backend, **Flet** (web UI) for the frontend, and **PostgreSQL** as the database. The project is fully automated with **GitHub Actions** for CI/CD.

## Features

- ✅ Create, update, and delete tasks
- 📅 Mark tasks as completed or pending
- 🧑 User authentication and management
- 🖥️ Cross-platform GUI with Flet (Python-based Flutter)
- ⚙️ RESTful API with FastAPI
- 🗃️ Persistent storage using PostgreSQL
- 🔄 CI/CD pipeline with GitHub Actions

## Tech Stack

- **Backend:** FastAPI
- **Frontend:** Flet
- **Database:** PostgreSQL
- **ORM:** SQLAlchemy
- **Testing:** Pytest
- **CI/CD:** GitHub Actions

## Quick start

```bash
cp .env.example .env          # edit the secrets
docker compose up -d --build
# open http://localhost:3000
```

See [docs/architecture/system-overview.md](docs/architecture/system-overview.md) for how the pieces fit together.

## Mock data for test

- **data_gen.py:** Using Faker to generate mock users and tasks to test the DB and functionality
