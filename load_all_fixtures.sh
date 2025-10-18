#!/bin/bash

# Script untuk load semua fixtures kursus
# Author: Auto-generated
# Description: Load fixtures dalam urutan yang benar

echo "================================================"
echo "Loading Fixtures untuk Kursus Online"
echo "================================================"

echo ""
echo "1. Loading Subjects..."
uv run manage.py loaddata courses/fixtures/subjects.json
if [ $? -eq 0 ]; then
    echo "✓ Subjects berhasil di-load"
else
    echo "✗ Error loading subjects"
    exit 1
fi

echo ""
echo "2. Loading Courses..."
uv run manage.py loaddata courses/fixtures/courses.json
if [ $? -eq 0 ]; then
    echo "✓ Courses berhasil di-load"
else
    echo "✗ Error loading courses"
    exit 1
fi

echo ""
echo "3. Loading Modules..."
uv run manage.py loaddata courses/fixtures/modules.json
if [ $? -eq 0 ]; then
    echo "✓ Modules berhasil di-load"
else
    echo "✗ Error loading modules"
    exit 1
fi

echo ""
echo "4. Loading Text Content..."
uv run manage.py loaddata courses/fixtures/texts.json
if [ $? -eq 0 ]; then
    echo "✓ Text content berhasil di-load"
else
    echo "✗ Error loading text content"
    exit 1
fi

echo ""
echo "5. Loading Video Content..."
uv run manage.py loaddata courses/fixtures/videos.json
if [ $? -eq 0 ]; then
    echo "✓ Video content berhasil di-load"
else
    echo "✗ Error loading video content"
    exit 1
fi

echo ""
echo "6. Loading Content Items..."
uv run manage.py loaddata courses/fixtures/contents.json
if [ $? -eq 0 ]; then
    echo "✓ Content items berhasil di-load"
else
    echo "✗ Error loading content items"
    exit 1
fi

echo ""
echo "================================================"
echo "✓ Semua fixtures berhasil di-load!"
echo "================================================"
echo ""
echo "Ringkasan:"
uv run manage.py shell -c "
from courses.models import Subject, Course, Module, Content, Text, Video
print(f'  - Subjects: {Subject.objects.count()}')
print(f'  - Courses: {Course.objects.count()}')
print(f'  - Modules: {Module.objects.count()}')
print(f'  - Text Content: {Text.objects.count()}')
print(f'  - Video Content: {Video.objects.count()}')
print(f'  - Content Items: {Content.objects.count()}')
"

echo ""
echo "Selesai!"

