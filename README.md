# Birthday RSVP Application

A simple RSVP application for a birthday celebration built with FastAPI and MySQL.

## Features

- Modern, responsive UI using Tailwind CSS
- RSVP form with guest name, number of guests, and attendance response
- MySQL database integration
- Docker deployment support

## Prerequisites

- Docker
- Docker Compose

## Getting Started

1. Clone the repository:

```bash
git clone <repository-url>
cd birthday-rsvp
```

2. Start the application using Docker Compose:

```bash
docker-compose up --build
```

3. Access the application:

- Frontend: http://localhost:44018
- API Documentation: http://localhost:44018/docs

## Environment Variables

The application uses the following environment variables:

- DB_HOST: MySQL host (default: mysql)
- DB_USER: MySQL user (default: dp)
- DB_PASSWORD: MySQL password (default: MyPass)
- DB_DATABASE: MySQL database name (default: rsvp_db)

## Development

To run the application locally without Docker:

1. Create a virtual environment:

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Run the application:

```bash
uvicorn main:app --reload
```

## License

MIT
