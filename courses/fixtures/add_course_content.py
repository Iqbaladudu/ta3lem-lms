"""
Script to add Content items linking modules to their learning materials.
Run this after loading the course fixtures.

Usage:
    python manage.py shell < add_course_content.py
"""

from django.contrib.contenttypes.models import ContentType

from courses.models import Module, Content, Text, Video

# Get ContentTypes
text_ct = ContentType.objects.get_for_model(Text)
video_ct = ContentType.objects.get_for_model(Video)

# Add content to Module 1 (Introduction to Python)
module1 = Module.objects.get(pk=1)
Content.objects.create(module=module1, content_type=text_ct, object_id=1, order=0)  # What is Python?
Content.objects.create(module=module1, content_type=text_ct, object_id=2, order=1)  # Installing Python
Content.objects.create(module=module1, content_type=video_ct, object_id=1, order=2)  # Python Installation Tutorial
Content.objects.create(module=module1, content_type=text_ct, object_id=3, order=3)  # Your First Python Program

# Add content to Module 2 (Python Data Types and Variables)
module2 = Module.objects.get(pk=2)
Content.objects.create(module=module2, content_type=text_ct, object_id=4, order=0)  # Understanding Variables
Content.objects.create(module=module2, content_type=text_ct, object_id=5, order=1)  # Python Data Types
Content.objects.create(module=module2, content_type=video_ct, object_id=2, order=2)  # Python Variables and Data Types

# Add content to Module 3 (Control Flow and Loops)
module3 = Module.objects.get(pk=3)
Content.objects.create(module=module3, content_type=text_ct, object_id=6, order=0)  # If Statements
Content.objects.create(module=module3, content_type=text_ct, object_id=7, order=1)  # Loops in Python

# Add content to Module 6 (Django Setup and Project Structure)
module6 = Module.objects.get(pk=6)
Content.objects.create(module=module6, content_type=text_ct, object_id=8, order=0)  # What is Django?
Content.objects.create(module=module6, content_type=video_ct, object_id=3, order=1)  # Django Tutorial for Beginners

# Add content to Module 7 (Models and Database Design)
module7 = Module.objects.get(pk=7)
Content.objects.create(module=module7, content_type=text_ct, object_id=9, order=0)  # Django Models

# Add content to Module 12 (JavaScript Fundamentals)
module12 = Module.objects.get(pk=12)
Content.objects.create(module=module12, content_type=text_ct, object_id=10, order=0)  # JavaScript Introduction

print("✅ Content items created successfully!")
print(f"Total content items: {Content.objects.count()}")
