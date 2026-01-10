import shutil
import os
import datetime
import logging

# Setup Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def create_backup():
    """
    Creates a zip backup of the database and uploads directory.
    Saves it to the 'backups' directory.
    """
    try:
        # Define paths
        APP_ROOT = os.path.dirname(os.path.abspath(__file__))
        BACKUP_DIR = os.path.join(APP_ROOT, 'backups')
        
        # Ensure backup directory exists
        if not os.path.exists(BACKUP_DIR):
            os.makedirs(BACKUP_DIR)
            
        # Timestamp for the filename
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_filename = f"backup_{timestamp}"
        
        # Create a temporary folder to collect files
        temp_dir = os.path.join(BACKUP_DIR, f"temp_{timestamp}")
        if not os.path.exists(temp_dir):
            os.makedirs(temp_dir)
            
        # 1. Backup Database
        db_file = os.path.join(APP_ROOT, 'database.json')
        if os.path.exists(db_file):
            shutil.copy2(db_file, temp_dir)
            
        # 2. Backup Uploads (if exists)
        uploads_dir = os.path.join(APP_ROOT, 'uploads')
        if os.path.exists(uploads_dir):
            shutil.copytree(uploads_dir, os.path.join(temp_dir, 'uploads'))
            
        # 3. Zip the temp directory
        zip_path = os.path.join(BACKUP_DIR, backup_filename)
        shutil.make_archive(zip_path, 'zip', temp_dir)
        
        # Cleanup temp directory
        shutil.rmtree(temp_dir)
        
        logging.info(f"Backup created successfully: {zip_path}.zip")
        return f"Backup created successfully: {backup_filename}.zip"
    
    except Exception as e:
        logging.error(f"Backup failed: {e}")
        return f"Backup failed: {str(e)}"

if __name__ == "__main__":
    create_backup()
