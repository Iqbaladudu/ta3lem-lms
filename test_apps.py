#!/usr/bin/env python
"""Test script to verify no duplicate apps during Django setup."""
import os
import sys

# Add project to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Simulate Django setup
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ta3lem.settings')

import django
django.setup()

from django.apps import apps

# Get all app labels
labels = [app.label for app in apps.get_app_configs()]

print(f"✓ Total apps loaded: {len(labels)}")

# Check for duplicates
duplicates = [label for label in set(labels) if labels.count(label) > 1]

if duplicates:
    print(f"✗ ERROR: Duplicate app labels found: {duplicates}")
    sys.exit(1)
else:
    print("✓ No duplicate app labels")
    print("✓ All apps loaded successfully:")
    for label in labels:
        print(f"  - {label}")
    sys.exit(0)
