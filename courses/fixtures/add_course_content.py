"""
Script to add Content items linking modules to their learning materials.
Run this after loading the course fixtures.

Usage:
    python manage.py shell < add_course_content.py
"""

from django.contrib.contenttypes.models import ContentType

from courses.models import Module, Content, Text, Video, Image
from users.models import User

# Get ContentTypes
text_ct = ContentType.objects.get_for_model(Text)
video_ct = ContentType.objects.get_for_model(Video)
image_ct = ContentType.objects.get_for_model(Image)

# Get an owner for content items (assuming at least one user exists)
owner = User.objects.first()
if not owner:
    print("❌ No users found. Please create a user first.")
    exit()


# Add content to Module 1 (Introduction to Python)
module1 = Module.objects.get(pk=1)
Content.objects.create(module=module1, content_type=text_ct, object_id=1, order=0)  # What is Python?
Content.objects.create(module=module1, content_type=text_ct, object_id=2, order=1)  # Installing Python
Content.objects.create(module=module1, content_type=video_ct, object_id=1, order=2)  # Python Installation Tutorial
Content.objects.create(module=module1, content_type=text_ct, object_id=3, order=3)  # Your First Python Program
# New content for Module 1
image1 = Image.objects.create(owner=owner, title="Python Logo", file='images/python_logo.png')
Content.objects.create(module=module1, content_type=image_ct, object_id=image1.pk, order=4) # Python Logo

# Add content to Module 2 (Python Data Types and Variables)
module2 = Module.objects.get(pk=2)
Content.objects.create(module=module2, content_type=text_ct, object_id=4, order=0)  # Understanding Variables
Content.objects.create(module=module2, content_type=text_ct, object_id=5, order=1)  # Python Data Types
Content.objects.create(module=module2, content_type=video_ct, object_id=2, order=2)  # Python Variables and Data Types
# New content for Module 2
text11 = Text.objects.create(owner=owner, title="Advanced Data Structures", content="Beyond the basic lists and tuples, Python offers several advanced data structures that are crucial for efficient programming and problem-solving. Dictionaries, for instance, store data in key-value pairs, providing fast lookups and flexible ways to organize information. Sets, on the other hand, are unordered collections of unique elements, useful for membership testing and eliminating duplicate entries. Understanding these structures, their underlying implementations, and their typical use cases is vital for writing optimized and maintainable code. This section delves into the nuances of each, explores common operations, and discusses scenarios where one might be preferred over another, often with a focus on time and space complexity.")
Content.objects.create(module=module2, content_type=text_ct, object_id=text11.pk, order=3)
video4 = Video.objects.create(owner=owner, title="Python Lists and Tuples", url="https://www.youtube.com/watch?v=s_JpA-5o83Q")
Content.objects.create(module=module2, content_type=video_ct, object_id=video4.pk, order=4)

# Add content to Module 3 (Control Flow and Loops)
module3 = Module.objects.get(pk=3)
Content.objects.create(module=module3, content_type=text_ct, object_id=6, order=0)  # If Statements
Content.objects.create(module=module3, content_type=text_ct, object_id=7, order=1)  # Loops in Python
# New content for Module 3
text12 = Text.objects.create(owner=owner, title="Nested Loops", content="Nested loops involve placing one loop inside another, a common programming construct used to iterate over multi-dimensional data structures or perform operations that require multiple passes. While powerful, they can quickly lead to performance issues if not used judiciously, as the number of operations increases multiplicatively with each nested level. This section will cover the syntax and execution flow of nested loops, illustrate their application through various examples such as matrix traversal and pattern printing, and highlight crucial considerations like loop invariants, breaking early, and alternatives to nested loops for improving efficiency in certain algorithms.")
Content.objects.create(module=module3, content_type=text_ct, object_id=text12.pk, order=2)
image2 = Image.objects.create(owner=owner, title="Flowchart of If-Else", file='images/flowchart_if_else.png')
Content.objects.create(module=module3, content_type=image_ct, object_id=image2.pk, order=3)

# Add content to Module 6 (Django Setup and Project Structure)
module6 = Module.objects.get(pk=6)
Content.objects.create(module=module6, content_type=text_ct, object_id=8, order=0)  # What is Django?
Content.objects.create(module=module6, content_type=video_ct, object_id=3, order=1)  # Django Tutorial for Beginners
# New content for Module 6
text13 = Text.objects.create(owner=owner, title="Django Project Best Practices", content="Building scalable and maintainable Django applications requires adherence to certain best practices. This includes organizing your project into modular apps, each responsible for a distinct set of functionalities, to promote reusability and separation of concerns. Proper management of settings, often using environment variables or dedicated settings files for different deployment environments (development, staging, production), is paramount for flexibility and security. Additionally, effective dependency management, consistent code styling, robust testing strategies, and thoughtful deployment considerations (like using Gunicorn/uWSGI and Nginx) are critical for delivering high-quality web applications that can evolve and scale over time.")
Content.objects.create(module=module6, content_type=text_ct, object_id=text13.pk, order=2)
video5 = Video.objects.create(owner=owner, title="Setting up Django with Docker", url="https://www.youtube.com/watch?v=p_yA1K7Qd4U")
Content.objects.create(module=module6, content_type=video_ct, object_id=video5.pk, order=3)

# Add content to Module 7 (Models and Database Design)
module7 = Module.objects.get(pk=7)
Content.objects.create(module=module7, content_type=text_ct, object_id=9, order=0)  # Django Models
# New content for Module 7
text14 = Text.objects.create(owner=owner, title="Database Relationships", content="Understanding how different pieces of data relate to each other is fundamental to effective database design. In relational databases, three primary types of relationships exist: One-to-Many, Many-to-Many, and One-to-One. A One-to-Many relationship, such as an author having multiple books, is very common. Many-to-Many relationships, like students enrolling in multiple courses, require an intermediary table. One-to-One relationships, where a single instance of an entity is linked to a single instance of another, are used for extending a model without denormalizing it. This section will dive into practical examples of each, demonstrating how to define and interact with these relationships using Django's powerful Object-Relational Mapper (ORM), ensuring data integrity and simplifying complex queries.")
Content.objects.create(module=module7, content_type=text_ct, object_id=text14.pk, order=1)
image3 = Image.objects.create(owner=owner, title="ER Diagram Example", file='images/er_diagram.png')
Content.objects.create(module=module7, content_type=image_ct, object_id=image3.pk, order=2)

# Add content to Module 12 (JavaScript Fundamentals)
module12 = Module.objects.get(pk=12)
Content.objects.create(module=module12, content_type=text_ct, object_id=10, order=0)  # JavaScript Introduction
# New content for Module 12
text15 = Text.objects.create(owner=owner, title="Asynchronous JavaScript", content="Asynchronous programming is a cornerstone of modern web development, allowing applications to perform long-running operations without blocking the main thread and freezing the user interface. This section explores the evolution of asynchronous patterns in JavaScript, starting with traditional callback functions, which handle operations once they complete but can lead to 'callback hell' in complex scenarios. We then move to Promises, a more structured way to manage asynchronous operations, providing clearer error handling and chaining capabilities. Finally, we delve into Async/Await, a syntactic sugar built on Promises that allows asynchronous code to be written in a synchronous-like style, significantly improving readability and maintainability, making complex concurrent tasks much more manageable.")
Content.objects.create(module=module12, content_type=text_ct, object_id=text15.pk, order=1)
video6 = Video.objects.create(owner=owner, title="Working with the DOM", url="https://www.youtube.com/watch?v=0ik66FAgX_4")
Content.objects.create(module=module12, content_type=video_ct, object_id=video6.pk, order=2)


print("✅ Content items created successfully!")
print(f"Total content items: {Content.objects.count()}")
