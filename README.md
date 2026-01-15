# Ta3lem LMS - API

A RESTful API for a Learning Management System built with Django and Django REST Framework.

## Features

- **User Management**: Registration, authentication (JWT), and role-based access (students, instructors)
- **Course Management**: Create, update, and manage courses with modules and content
- **Enrollment System**: Course enrollment with multiple pricing types (free, subscription, one-time purchase)
- **Progress Tracking**: Track student progress through courses, modules, and content
- **Subscription System**: Subscription plans with trial support
- **Payment System**: Order management and payment processing

## API Documentation

After running the server, visit:
- **Swagger UI**: `/api/docs/`
- **ReDoc**: `/api/redoc/`
- **OpenAPI Schema**: `/api/schema/`

## Setup

### Install Dependencies

```bash
uv sync
```

### Database Migration

```bash
uv run manage.py migrate
```

### Create Super User

```bash
uv run manage.py createsuperuser
```

### Load Fixtures

```bash
./load_all_fixtures.sh 
```

### Setup Permissions

```bash
uv run manage.py setup_permissions
```

### Run Development Server

```bash
uv run manage.py runserver
```

## API Endpoints

### Authentication
- `POST /api/v1/auth/register/` - User registration
- `POST /api/v1/auth/login/` - Get JWT tokens
- `POST /api/v1/auth/refresh/` - Refresh access token
- `POST /api/v1/auth/logout/` - Logout (blacklist token)

### Users
- `GET /api/v1/users/me/` - Current user profile
- `PATCH /api/v1/users/me/` - Update profile

### Courses
- `GET /api/v1/courses/` - List courses
- `GET /api/v1/courses/{id}/` - Course detail
- `POST /api/v1/courses/` - Create course (instructor)
- `PUT /api/v1/courses/{id}/` - Update course (owner)
- `DELETE /api/v1/courses/{id}/` - Delete course (owner)

### Enrollments
- `GET /api/v1/enrollments/` - List enrollments
- `POST /api/v1/enrollments/` - Enroll in course

### Progress
- `GET /api/v1/progress/` - Get progress
- `POST /api/v1/progress/complete/` - Mark content complete

### Subscriptions
- `GET /api/v1/subscriptions/plans/` - List subscription plans
- `POST /api/v1/subscriptions/subscribe/` - Subscribe to plan
- `GET /api/v1/subscriptions/my-subscription/` - Current subscription

### Payments
- `GET /api/v1/payments/orders/` - List orders
- `POST /api/v1/payments/checkout/` - Create order

## Environment Variables

```env
DJANGO_SETTINGS_MODULE=ta3lem.settings.development
DJANGO_SECRET_KEY=your-secret-key
DB_NAME=ta3lem_db
DB_USER=ta3lem
DB_PASSWORD=ta3lem123
DB_HOST=localhost
DB_PORT=5432
REDIS_URL=redis://localhost:6379
```

## License

MIT
