#!/bin/bash
echo "================================================"
echo "Loading Fixtures untuk Kursus Online"
echo "================================================"

# Urutan loading yang benar
FIXTURES=(
    "users.json"
    "new_users.json"
    "subjects.json"
    "new_subjects.json"
    "courses.json"
    "new_courses.json"
    "modules.json"
    "new_modules.json"
    "texts.json"
    "new_texts.json"
    "videos.json"
    "new_videos.json"
    "contents.json"
    "new_contents.json"
    "content_items.json"
    "new_content_items.json"
    "course_enrollments.json"
    "new_enrollments.json"
    "content_progress.json"
    "new_content_progress.json"
    "learning_sessions.json"
    "new_learning_sessions.json"
)

for fixture in "${FIXTURES[@]}"; do
    echo ""
    echo "--- Loading $fixture ---"
    uv run manage.py loaddata "courses/fixtures/$fixture" --settings=ta3lem.settings.staging
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
uv run manage.py shell --settings=ta3lem.settings.staging -c "
from users.models import User
from courses.models import Subject, Course, Module, Content, ContentItem, Text, Video, CourseEnrollment, ContentProgress, LearningSession
print(f'  - Users: {User.objects.count()}')
print(f'  - Subjects: {Subject.objects.count()}')
print(f'  - Courses: {Course.objects.count()}')
print(f'  - Modules: {Module.objects.count()}')
print(f'  - Text Content: {Text.objects.count()}')
print(f'  - Video Content: {Video.objects.count()}')
print(f'  - Content: {Content.objects.count()}')
print(f'  - Content Items: {ContentItem.objects.count()}')
print(f'  - Enrollments: {CourseEnrollment.objects.count()}')
print(f'  - Progress Records: {ContentProgress.objects.count()}')
print(f'  - Learning Sessions: {LearningSession.objects.count()}')
"

echo ""
echo "Selesai!"
