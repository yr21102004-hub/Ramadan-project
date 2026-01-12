# Test script to verify profile image setup
import os
from pathlib import Path

print("=" * 60)
print("Profile Image Setup Test")
print("=" * 60)

# 1. Check default avatar exists
default_avatar = Path("static/default_avatar.png")
if default_avatar.exists():
    size = default_avatar.stat().st_size
    print(f"OK - Default avatar exists: {size:,} bytes")
else:
    print("ERROR - Default avatar not found!")

# 2. Check user_images folder exists
user_images_dir = Path("static/user_images")
if user_images_dir.exists():
    files = list(user_images_dir.glob("*"))
    print(f"OK - user_images folder exists: {len(files)} files")
else:
    print("ERROR - user_images folder not found!")

# 3. Check user_dashboard.html has profile image section
dashboard_file = Path("templates/user_dashboard.html")
if dashboard_file.exists():
    content = dashboard_file.read_text(encoding='utf-8')
    if "Profile Image Section" in content:
        print("OK - Profile image section found in user_dashboard.html")
    else:
        print("ERROR - Profile image section not found!")
    
    if "profile-image-container" in content:
        print("OK - CSS class for image found")
    else:
        print("ERROR - CSS class not found!")
        
    if "default_avatar.png" in content:
        print("OK - Default avatar linked in code")
    else:
        print("ERROR - Default avatar not linked!")
else:
    print("ERROR - user_dashboard.html not found!")

# 4. Check app.py passes profile_image
app_file = Path("app.py")
if app_file.exists():
    content = app_file.read_text(encoding='utf-8')
    if "'profile_image': user_data.get('profile_image')" in content:
        print("OK - app.py passes profile_image correctly")
    else:
        print("ERROR - app.py doesn't pass profile_image!")
else:
    print("ERROR - app.py not found!")

print("=" * 60)
print("\nIf all checks are OK, the issue is browser cache!")
print("Solution: Press Ctrl + Shift + R in browser")
print("=" * 60)
