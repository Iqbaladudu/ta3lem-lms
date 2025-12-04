## Migrate

```jsx
uv run manage.py migrate
```

## Create Super User

```jsx
uv run manage.py createsuperuser
```

## Install npm & build

```jsx
uv run manage.py vite install
uv run manage.py vite build
```

## Load Fixtures

```jsx
./load_all_fixtures.sh 
```

## Setup permission

```jsx
uv run manage.py setup_permissions
```

## Authentication routing

```jsx
/accounts # ==> root routing for auth
/../logout # ==> logout student || instructor
/../login # ==> Login student
/../register # ==> Register student
/../instructor # ==> Login instructor
/../enroll
/../courses
/../courses/<pk>
/../courses/<pk>/<module_id>
/../verify-email/<id>/<token>
/../resend-verification
```

## Course routing

```jsx
/course
/../mine => Instructor's course list

```
