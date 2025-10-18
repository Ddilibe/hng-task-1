# HNG Stage 1 Task: User Info and Cat Fact API 🐱

This project is a simple API built using **FastAPI** that serves personal information alongside a fun, random cat fact fetched from an external third-party API. It serves as the solution for the HNG Stage 1 task.

## ✨ Features

* **User Information:** Returns pre-defined personal details (email, name, stack).
* **Real-time Timestamp:** Provides a UTC timestamp in ISO 8601 format (e.g., `2025-10-15T12:34:56.789Z`).
* **External Data Fetch:** Integrates with the `catfact.ninja` API to include a random cat fact in the response.
* **CORS Enabled:** Configured with open CORS settings (`allow_origins=["*"]`) for easy access from any frontend application.

---

## 🛠️ Technology Stack

| Component Type | Component | Description |
| :--- | :--- | :--- |
| **Framework** | **FastAPI** | High-performance, easy-to-learn, modern framework for building APIs with Python. |
| **Server** | **Uvicorn** | Lightning-fast ASGI server, used to run the FastAPI application. |
| **HTTP Requests** | **`requests`** | Library for making simple and reliable HTTP requests to the external Cat Fact API. |
| **Data Structure** | **`dataclasses`** | Used for defining clean, type-hinted data models (`User`, `MeResponse`). |

---

## 🚀 Setup and Run Locally

Follow these steps to get the API running on your local machine.

### 1. Installation

Install all necessary Python packages:

```bash
uv sync
```

### 2. Run the server

The application code is saved in a file named main.py

```bash
uv run uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

The server will be accessible at `http://127.0.0.1:8000`. The reload flag is optional

## 🌐Api Endpoint

The application exposes a single endpoint:

`GET /me`

Returns structured personal data and a random cat fact.

* **URL**: `http://127.0.0.1:8000/me`
* **Method**: `GET`

### ✅ Example Success Response
```json
{
    "status": "success",
    "user": {
        "email": "franklinfidelugwuowo@gmail.com",
        "name": "Fidelugwuowo Dilibe",
        "stack": "Python/FastAPI",
    },
    "timestamp": "2025-10-17T20:00:00.123Z",
    "fact": "Cats dislike citrus scent"
}
```
### ❎ Example Error Response (if the Cat Fact API fails)
```json
{
    "detail": "Random cat server is down. Try again after a while"
}
```

## 🧠 Author

**Fidelugwuowo Dilibe**

