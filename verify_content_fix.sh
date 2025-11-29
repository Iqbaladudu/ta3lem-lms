#!/bin/bash

# Content Display Fix Verification Script
echo "========================================="
echo "Content Display Fix Verification"
echo "========================================="
echo ""

# Check if django-embed-video is installed
echo "1. Checking django-embed-video installation..."
if grep -q "django-embed-video" pyproject.toml; then
    echo "   ✅ django-embed-video is in pyproject.toml"
else
    echo "   ❌ django-embed-video NOT found in pyproject.toml"
fi

# Check if embed_video is in INSTALLED_APPS
echo ""
echo "2. Checking INSTALLED_APPS configuration..."
if grep -q "'embed_video'" ta3lem/settings/base.py; then
    echo "   ✅ embed_video is in INSTALLED_APPS"
else
    echo "   ❌ embed_video NOT in INSTALLED_APPS"
fi

# Check if Video model has file field
echo ""
echo "3. Checking Video model..."
if grep -q "file = models.FileField" courses/models.py; then
    echo "   ✅ Video model has file field"
else
    echo "   ❌ Video model missing file field"
fi

# Check if content_type property exists
echo ""
echo "4. Checking content_type property..."
if grep -q "def content_type" courses/models.py; then
    echo "   ✅ content_type property exists"
else
    echo "   ❌ content_type property missing"
fi

# Check if templates use embed_video_tags
echo ""
echo "5. Checking template tags..."
if grep -q "embed_video_tags" courses/templates/courses/student/content_detail.html; then
    echo "   ✅ content_detail.html loads embed_video_tags"
else
    echo "   ❌ content_detail.html missing embed_video_tags"
fi

if grep -q "embed_video_tags" courses/templates/courses/content/video.html; then
    echo "   ✅ video.html loads embed_video_tags"
else
    echo "   ❌ video.html missing embed_video_tags"
fi

# Check media directories
echo ""
echo "6. Checking media directories..."
if [ -d "media/videos" ]; then
    echo "   ✅ media/videos directory exists"
else
    echo "   ⚠️  media/videos directory missing (will be created on first upload)"
fi

if [ -d "media/images" ]; then
    echo "   ✅ media/images directory exists"
else
    echo "   ⚠️  media/images directory missing"
fi

if [ -d "media/files" ]; then
    echo "   ✅ media/files directory exists"
else
    echo "   ⚠️  media/files directory missing"
fi

# Check migration
echo ""
echo "7. Checking migrations..."
if [ -f "courses/migrations/0006_video_file_alter_video_url.py" ]; then
    echo "   ✅ Migration 0006 exists"
else
    echo "   ❌ Migration 0006 missing - run: python manage.py makemigrations"
fi

echo ""
echo "========================================="
echo "Verification Complete!"
echo "========================================="
echo ""
echo "Next steps:"
echo "1. Run: python manage.py migrate"
echo "2. Start server: python manage.py runserver"
echo "3. Test content display in browser"
echo ""

