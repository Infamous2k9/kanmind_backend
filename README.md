# KanMind – Backend

A Django REST Framework backend for a Kanban board application (boards, tasks, and comments), built as part of the Developer Akademie backend course.

## Tech Stack

- Python 3.x
- Django
- Django REST Framework
- Token Authentication (DRF authtoken)
- SQLite (development database)

## Features

- User registration and login via email/password (custom user model)
- Create, view, update, and delete Kanban boards
- Manage board members
- Create, update, and delete tasks within a board
- Assign tasks to a user (assignee) and a reviewer
- Comment on tasks
- "Assigned to me" and "Reviewing" task views
- Email existence/format check endpoint

## Setup

1. Clone this repository:

   ```bash
   git clone <your-repo-url>
   cd kanmind_backend
   ```

2. Create and activate a virtual environment:

   ```bash
   python -m venv env
   source env/bin/activate   # Windows: env\Scripts\activate
   ```

3. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

4. Apply migrations:

   ```bash
   python manage.py migrate
   ```

5. Create a superuser (for the admin panel):

   ```bash
   python manage.py createsuperuser
   ```

   Note: this project uses a custom User model authenticated by email, so you will be asked for `email`, `fullname`, and `password` instead of `username`.

6. Run the development server:
   ```bash
   python manage.py runserver
   ```

The API will be available at `http://127.0.0.1:8000/api/`.

## Project Structure

```
core/            # Project settings, main URL routing
auth_app/        # User model, registration, login
kanban_app/      # Boards, tasks, comments
```

Each app contains an `api/` folder with `serializers.py`, `views.py`, `urls.py`, and `permissions.py`.

## API Endpoints

**Note on trailing slashes:** all API endpoints in this project are defined **without** a trailing slash (e.g. `/api/boards/5`, not `/api/boards/5/`). `APPEND_SLASH` is disabled in `core/settings.py`. Requests with a trailing slash will return `404 Not Found`.

### Auth

| Method | Endpoint            | Auth required |
| ------ | ------------------- | ------------- |
| POST   | `/api/registration` | No            |
| POST   | `/api/login`        | No            |

### Boards

| Method | Endpoint                  | Auth required           |
| ------ | ------------------------- | ----------------------- |
| GET    | `/api/boards`             | Yes                     |
| POST   | `/api/boards`             | Yes                     |
| GET    | `/api/boards/{board_id}`  | Yes, board member/owner |
| PATCH  | `/api/boards/{board_id}`  | Yes, board member/owner |
| DELETE | `/api/boards/{board_id}`  | Yes, board owner only   |
| GET    | `/api/email-check?email=` | Yes                     |

### Tasks

| Method | Endpoint                                     | Auth required                         |
| ------ | -------------------------------------------- | ------------------------------------- |
| GET    | `/api/tasks/assigned-to-me`                  | Yes                                   |
| GET    | `/api/tasks/reviewing`                       | Yes                                   |
| POST   | `/api/tasks`                                 | Yes, board member                     |
| PATCH  | `/api/tasks/{task_id}`                       | Yes, board member                     |
| DELETE | `/api/tasks/{task_id}`                       | Yes, task creator or board owner only |
| GET    | `/api/tasks/{task_id}/comments`              | Yes, board member                     |
| POST   | `/api/tasks/{task_id}/comments`              | Yes, board member                     |
| DELETE | `/api/tasks/{task_id}/comments/{comment_id}` | Yes, comment author only              |

## Notable Design Decisions / Special Cases

- **Custom User model**: authentication is based on `email` instead of `username`, since the frontend expects email-based login. `AUTH_USER_MODEL` is set to `auth_app.User`.
- **No trailing slashes**: all API routes are registered without a trailing slash, and `APPEND_SLASH = False` is set to avoid automatic redirects (which can silently drop the request body on `POST`/`PATCH` requests in some clients).
- **Board responses differ by endpoint**:
  - `GET`/`POST /api/boards` return flat fields with computed counts (`member_count`, `ticket_count`, `tasks_to_do_count`, `tasks_high_prio_count`).
  - `GET /api/boards/{id}` returns nested `members` and `tasks` objects.
  - `PATCH /api/boards/{id}` returns `owner_data` and `members_data` (nested user objects) instead of `owner_id`/`members`.

  These shapes intentionally differ between endpoints to match the provided endpoint documentation.

- **`PATCH /api/boards/{id}`**: `title` and `members` can be updated independently — sending only `title` leaves the existing members untouched. Sending `members` replaces the full member list (not an incremental add).
- **Task `board` field**: writable and required on creation, but cannot be changed afterwards — attempting to change it via `PATCH` returns `400 Bad Request`.
- **Task assignee/reviewer validation**: a user can only be set as `assignee` or `reviewer` if they are a member (or the owner) of the task's board; otherwise the request returns `400 Bad Request`.
- **Task deletion** is restricted to the task's creator or the board owner.
- **Comment deletion** is restricted to the comment's author only; `author` is returned as a plain string (full name), not a nested object.
- **`/api/email-check`** validates the `email` query parameter before performing a lookup:
  - missing parameter → `400 Bad Request`
  - invalid email format → `400 Bad Request`
  - valid format, no matching user → `404 Not Found`
  - valid format, matching user → `200 OK` with the user's `id`, `email`, and `fullname`
- **CORS** is enabled for local frontend development (`django-cors-headers`).

## API Documentation

See the provided endpoint documentation for the full list of endpoints, request/response formats, and status codes.
