#!/bin/bash
# Test Script untuk Navigasi Pembelajaran yang Disederhanakan

echo "=========================================="
echo "Testing Simplified Navigation Features"
echo "=========================================="
echo ""

# 1. Check Django configuration
echo "1. Checking Django configuration..."
python manage.py check
if [ $? -eq 0 ]; then
    echo "   ✅ Django check passed"
else
    echo "   ❌ Django check failed"
    exit 1
fi
echo ""

# 2. Check if template exists
echo "2. Checking template files..."
if [ -f "courses/templates/courses/student/content_detail.html" ]; then
    echo "   ✅ content_detail.html exists"
else
    echo "   ❌ content_detail.html not found"
    exit 1
fi

if [ -f "courses/templates/courses/student/course_detail.html" ]; then
    echo "   ✅ course_detail.html exists"
else
    echo "   ❌ course_detail.html not found"
    exit 1
fi
echo ""

# 3. Check if custom template tags exist
echo "3. Checking custom template tags..."
if grep -q "def mul" courses/templatetags/course.py; then
    echo "   ✅ mul filter exists"
else
    echo "   ❌ mul filter not found"
    exit 1
fi

if grep -q "def div" courses/templatetags/course.py; then
    echo "   ✅ div filter exists"
else
    echo "   ❌ div filter not found"
    exit 1
fi
echo ""

# 4. Check if view has required context data
echo "4. Checking StudentContentView..."
if grep -q "modules_data" courses/views.py; then
    echo "   ✅ modules_data context exists"
else
    echo "   ❌ modules_data context not found"
    exit 1
fi

if grep -q "contents_with_progress" courses/views.py; then
    echo "   ✅ contents_with_progress context exists"
else
    echo "   ❌ contents_with_progress context not found"
    exit 1
fi
echo ""

# 5. Check template has sidebar
echo "5. Checking template has sidebar..."
if grep -q "courseSidebar" courses/templates/courses/student/content_detail.html; then
    echo "   ✅ Sidebar element exists"
else
    echo "   ❌ Sidebar element not found"
    exit 1
fi

if grep -q "toggleModule" courses/templates/courses/student/content_detail.html; then
    echo "   ✅ JavaScript toggle function exists"
else
    echo "   ❌ JavaScript toggle function not found"
    exit 1
fi
echo ""

# 6. Check template loads custom filters
echo "6. Checking template loads custom filters..."
if grep -q "{% load course %}" courses/templates/courses/student/content_detail.html; then
    echo "   ✅ Template loads course filters"
else
    echo "   ❌ Template doesn't load course filters"
    exit 1
fi
echo ""

echo "=========================================="
echo "✅ ALL AUTOMATED TESTS PASSED!"
echo "=========================================="
echo ""
echo "MANUAL TESTING CHECKLIST:"
echo "------------------------"
echo "1. Start the development server:"
echo "   python manage.py runserver"
echo ""
echo "2. Navigate to a course as a student:"
echo "   http://localhost:8000/course/student/<course_id>/"
echo ""
echo "3. Click on any content in the sidebar"
echo ""
echo "4. Verify the following:"
echo "   [ ] Sidebar appears on the left"
echo "   [ ] All modules are listed in sidebar"
echo "   [ ] Current module is auto-expanded"
echo "   [ ] Current content is highlighted (blue-purple)"
echo "   [ ] Progress bars show correct percentages"
echo "   [ ] Completed contents have green checkmarks"
echo "   [ ] Click on different content navigates correctly"
echo "   [ ] Collapse button (<) minimizes sidebar"
echo "   [ ] Expand button (>) restores sidebar"
echo "   [ ] Previous/Next buttons work"
echo "   [ ] Mark Complete button works"
echo "   [ ] Page is mobile responsive"
echo ""
echo "5. Test navigation flow:"
echo "   [ ] Can jump to any content from sidebar"
echo "   [ ] Auto-advances to next module if needed"
echo "   [ ] Breadcrumb shows correct path"
echo "   [ ] Sidebar state persists during navigation"
echo ""
echo "=========================================="

