# HR Specialist

A Telegram-based HR and recruitment automation platform built with Python and AIogram. The project is designed to streamline hiring workflows: collecting candidate applications, publishing vacancies, matching candidates with jobs, scheduling interviews, managing subscriptions, and syncing data to Google Sheets.

## Overview

HR Specialist is a full-featured bot that helps both job seekers and employers interact through Telegram. Candidates can submit resumes, employers can post vacancies, the bot matches relevant profiles, and administrators can monitor performance and manage premium access.

The project combines:

- Telegram bot interface with AIogram
- PostgreSQL for structured data storage
- Redis for FSM/session state management
- Google Sheets for reporting and synchronization
- APScheduler for background tasks
- Docker Compose for local environment orchestration

## Key Features

- Candidate application flow with structured resume form
- Employer vacancy management and posting
- Smart matching between profiles and job openings
- Interview coordination and workflow support
- Creator/admin control panel with system statistics
- Premium subscription and referral balance logic
- Google Sheets sync for applicants, vacancies, and interviews
- Dockerized setup for quick deployment

## Tech Stack

- Python 3.11+
- AIogram 3.x
- SQLAlchemy 2.x
- PostgreSQL
- Redis
- Google Sheets API
- APScheduler
- Pydantic Settings
- Docker / Docker Compose

## Project Structure

```text
hr-specialist/
├── .env
├── .gitattributes
├── docker-compose.yml
├── main.py
├── requirements.txt
├── config/
│   └── settings.py
├── database/
│   ├── db_helper.py
│   ├── models.py
│   └── __pycache__/
├── handlers/
│   ├── anketa.py
│   ├── creator.py
│   ├── interview.py
│   ├── payments.py
│   ├── start.py
│   └── __pycache__/
├── keyboards/
│   └── inline.py
├── middlewares/
│   └── admin.py
├── services/
│   ├── credentials.json
│   ├── google-sheets.py
│   ├── matching.py
│   └── scheduler.py
└── README.md
```

## Architecture

The application follows a modular Telegram bot architecture:

- `main.py` starts the bot and registers routers
- `handlers/` contains all command and callback handlers
- `database/` defines SQLAlchemy models and session configuration
- `services/` includes Google Sheets integration, matching logic, and scheduler
- `config/settings.py` loads environment variables from `.env`
- `docker-compose.yml` orchestrates PostgreSQL, Redis, and the bot container

## Environment Variables

Create a `.env` file in the project root with the following values:

```env
BOT_TOKEN=your_telegram_bot_token
DATABASE_URL=postgresql+asyncpg://postgres:postgres_password@db:5432/smart_chef
REDIS_URL=redis://redis:6379/0
GOOGLE_SHEET_ID=your_google_sheet_id
CREATOR_ID=your_telegram_user_id
```

Notes:

- `BOT_TOKEN` must be issued from Telegram BotFather.
- `CREATOR_ID` is used for admin/creator-only access control.
- `GOOGLE_SHEET_ID` links the project to the Google spreadsheet used for sync.
- Never commit real secrets to version control; keep them in local `.env` files or your deployment secret manager.

## Installation

### 1. Clone the repository

```bash
git clone https://github.com/Timaty7/hr-specialist.git
cd hr-specialist
```

### 2. Create a virtual environment

```bash
python -m venv venv
source venv/bin/activate   # Linux/macOS
# or
venv\Scripts\activate      # Windows
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment

Copy the sample values into `.env` and replace placeholders with your actual values.

## Running with Docker

This project includes `docker-compose.yml` to run PostgreSQL and Redis together with the bot service.

```bash
docker compose up --build
```

This will start:

- PostgreSQL database
- Redis cache/FSM state storage
- Telegram bot service

To stop the services:

```bash
docker compose down
```

## Local Execution

If you want to run the application directly without Docker:

```bash
python main.py
```

Make sure PostgreSQL and Redis are running and the environment variables are valid.

## Database Model

The project uses SQLAlchemy models for:

- `User` — user profiles, roles, subscription state, referral data
- `Resume` — candidate resumes and application details
- `Vacancy` — employer job posts
- `WithdrawalRequest` — payout requests and statuses

## Bot Workflow

Typical user flow:

1. User opens the Telegram bot.
2. User selects a role: candidate or employer.
3. Candidate fills out an application / resume form.
4. Employer posts a vacancy.
5. Matching service identifies relevant candidates.
6. Qualified matches receive interview invitations.
7. Admin can inspect stats and manage the platform.

## Google Sheets Integration

The service layer synchronizes data to a Google Sheet with worksheets such as:

- Applicants
- Vacancies
- Interviews

This supports reporting, candidate tracking, and operational visibility.

## Admin Capabilities

The creator/admin panel includes functions such as:

- `/admin` — display the admin panel
- `/stats` — view platform statistics
- `/give_sub <user_tg_id>` — grant subscription access
- `/add_balance <user_tg_id> <amount>` — adjust user balance
- `/ban <user_tg_id>` — restrict access
- `/broadcast <message>` — notify all users

## Security Notes

- Use `.env` for local credentials and secrets.
- Avoid committing production-level tokens or Google service credentials.
- Restrict admin commands to trusted users only.
- Validate all user input before persisting or executing actions.

## Contribution

Contributions are welcome. To contribute:

```bash
git checkout -b feature/your-feature
git commit -m "Add your feature"
git push origin feature/your-feature
```

Then open a pull request with a clear summary of what was changed.

## License

This project is currently distributed without a formal license declaration. If you plan to publish or reuse it commercially, add a license file and define the terms clearly.

## Contact

For inquiries or project collaboration, contact the repository maintainer via GitHub.

---

Built for recruitment automation in Telegram.
