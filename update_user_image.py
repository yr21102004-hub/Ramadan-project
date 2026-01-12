"""
Script to update user profile image in database
"""
from tinydb import TinyDB, Query
import shutil
import os
from datetime import datetime

# Database setup
db = TinyDB('database.json')
users_table = db.table('users')

def update_user_image(username, image_path):
    """
    Update user profile image
    Args:
        username: Username to update
        image_path: Path to the image file
    """
    # Check if image exists
    if not os.path.exists(image_path):
        print(f"Error: Image not found at {image_path}")
        return False
    
    # Get file extension
    file_ext = image_path.split('.')[-1].lower()
    
    # Create unique filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    new_filename = f"{username}_{timestamp}.{file_ext}"
    
    # Copy image to user_images folder
    dest_folder = "static/user_images"
    if not os.path.exists(dest_folder):
        os.makedirs(dest_folder)
    
    dest_path = os.path.join(dest_folder, new_filename)
    shutil.copy2(image_path, dest_path)
    
    # Update database
    UserQuery = Query()
    users_table.update(
        {'profile_image': f'user_images/{new_filename}'}, 
        UserQuery.username == username
    )
    
    print(f"✅ Successfully updated profile image for user: {username}")
    print(f"   Image saved to: {dest_path}")
    print(f"   Database path: user_images/{new_filename}")
    return True

# Example usage:
# update_user_image('JO', 'path/to/image.jpg')

if __name__ == "__main__":
    print("=" * 60)
    print("User Profile Image Updater")
    print("=" * 60)
    print("\nTo update a user's image, use:")
    print("  update_user_image('username', 'path/to/image.jpg')")
    print("\nExample:")
    print("  update_user_image('JO', 'C:/Users/Youssef/Pictures/photo.jpg')")
    print("=" * 60)
