#!/usr/bin/env python
"""
Test script to verify content display functionality
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ta3lem.settings.development')
django.setup()

from courses.models import Video, Image, File, Text

def test_content_types():
    print("Testing Content Types...")
    print("=" * 50)

    # Test Video model
    print("\n1. Testing Video Model:")
    videos = Video.objects.all()[:3]
    for video in videos:
        print(f"   - {video.title}")
        print(f"     URL: {video.url}")
        print(f"     File: {video.file}")
        print(f"     Content Type: {video.content_type}")

    # Test Image model
    print("\n2. Testing Image Model:")
    images = Image.objects.all()[:3]
    for image in images:
        print(f"   - {image.title}")
        print(f"     File: {image.file}")
        print(f"     Content Type: {image.content_type}")

    # Test File model
    print("\n3. Testing File Model:")
    files = File.objects.all()[:3]
    for file in files:
        print(f"   - {file.title}")
        print(f"     File: {file.file}")
        print(f"     Content Type: {file.content_type}")

    # Test Text model
    print("\n4. Testing Text Model:")
    texts = Text.objects.all()[:3]
    for text in texts:
        print(f"   - {text.title}")
        print(f"     Content Type: {text.content_type}")

    print("\n" + "=" * 50)
    print("All tests completed successfully!")

if __name__ == '__main__':
    test_content_types()

