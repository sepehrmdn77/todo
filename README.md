# ToDo App ✅

A full-stack ToDo application built with **FastAPI** for the backend, **Flet** for the UI, and **SQLite** as the database. The project is fully automated with **GitHub Actions** for CI/CD.

## Features

- ✅ Create, update, and delete tasks
- 📅 Mark tasks as completed or pending
- 🧑 User authentication and management
- 🖥️ Cross-platform GUI with Flet (Python-based Flutter)
- ⚙️ RESTful API with FastAPI
- 🗃️ Persistent storage using SQLite
- 🔄 CI/CD pipeline with GitHub Actions

## Tech Stack

- **Backend:** FastAPI
- **Frontend:** Flet
- **Database:** SQLite
- **ORM:** SQLAlchemy
- **Testing:** Pytest
- **CI/CD:** GitHub Actions

## Getting Started

### 1. Clone the repository

```bash
git clone https://github.com/sepehrmdn77/todo.git
cd todo
```

### 2. Setup a virtual environment

```bash
python -m venv venv
source venv/bin/activate  # or .\venv\Scripts\activate on Windows
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Run database migrations (optional)

```bash
alembic upgrade head
```

### 5. Run the FastAPI backend

```bash
uvicorn app.main:app --reload
```

### 6. Launch the Flet GUI

```bash
python ui/main.py
```

## API Endpoints

FastAPI automatically generates interactive docs at:

- Swagger: `http://127.0.0.1:8000/docs`
- Redoc: `http://127.0.0.1:8000/redoc`

## Environment Variables

Create a `.env` file in the root directory:

```
DATABASE_URL=sqlite:///./todo.db
SECRET_KEY=your-secret-key
```

## CI/CD

This project uses GitHub Actions for:

- Linting with `flake8`
- Testing with `pytest`
- Auto-deployment (if configured)

## License

This project is licensed under the [MIT License](LICENSE).

## Screenshots

#![App Screenshot](screenshots/todo_ui.png)
Soon...

---

Feel free to contribute or fork this repo!
