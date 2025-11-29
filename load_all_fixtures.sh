#!/bin/bash
echo "================================================"
echo "Loading Fixtures untuk Kursus Online"
echo "================================================"

# Urutan loading yang benar
FIXTURES=(
    "users.json"
    "subjects.json"
    "courses.json"
    "modules.json"
    "texts.json"
    "videos.json"
    "contents.json"
    "course_enrollments.json"
    "content_progress.json"
    "learning_sessions.json"
)

for fixture in "${FIXTURES[@]}"; do
    echo ""
    echo "--- Loading $fixture ---"
    uv run manage.py loaddata "courses/fixtures/$fixture" --settings=ta3lem.settings.development
    if [ $? -ne 0 ]; then
        echo "✗ Error loading $fixture"
        exit 1
    fi
    echo "✓ $fixture berhasil di-load"
done

echo ""
echo "================================================"
echo "✓ Semua fixtures berhasil di-load!"
echo "================================================"
echo ""
echo "Ringkasan:"
uv run manage.py shell --settings=ta3lem.settings.development -c "
from users.models import User
from courses.models import Subject, Course, Module, Content, Text, Video, CourseEnrollment, ContentProgress, LearningSession
print(f'  - Users: {User.objects.count()}')
print(f'  - Subjects: {Subject.objects.count()}')
print(f'  - Courses: {Course.objects.count()}')
print(f'  - Modules: {Module.objects.count()}')
print(f'  - Text Content: {Text.objects.count()}')
print(f'  - Video Content: {Video.objects.count()}')
print(f'  - Content Items: {Content.objects.count()}')
print(f'  - Enrollments: {CourseEnrollment.objects.count()}')
print(f'  - Progress Records: {ContentProgress.objects.count()}')
print(f'  - Learning Sessions: {LearningSession.objects.count()}')
"

echo ""
echo "Selesai!"
