#!/usr/bin/python3
import os
import shutil
from pathlib import Path
from datetime import datetime

# Define target directories and their associated file extensions
TARGET_DIRS = {
    'documents': ['.pdf', '.docx', '.txt', '.pptx', '.xlsx', '.csv', '.doc', '.odt'],
    'pictures': ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.svg', '.webp', '.heic'],
    'videos': ['.mp4', '.avi', '.mkv', '.mov', '.wmv', '.flv', '.webm'],
    'audio': ['.mp3', '.wav', '.flac', '.aac', '.ogg', '.m4a'],
    'archives': ['.zip', '.rar', '.7z', '.tar', '.gz', '.bz2'],
    'code': ['.py', '.js', '.html', '.css', '.java', '.cpp', '.c', '.h', '.json', '.xml'],
    'executables': ['.exe', '.msi', '.app', '.dmg', '.deb', '.rpm']
}

class FileOrganizer:
    def __init__(self, base_dir=None, dry_run=False, recursive=True):
        """
        Initialize the file organizer.
        
        Args:
            base_dir: Base directory to organize (defaults to Downloads)
            dry_run: If True, only shows what would be moved without moving files
            recursive: If True, searches subdirectories
        """
        if base_dir is None:
            # Default to Downloads folder
            base_dir = str(Path.home() / 'Downloads')
        
        self.base_dir = Path(base_dir).resolve()
        self.dry_run = dry_run
        self.recursive = recursive
        self.stats = {'moved': 0, 'skipped': 0, 'errors': 0}
        
        # Create log directory
        self.log_dir = self.base_dir / '.organizer_logs'
        self.log_dir.mkdir(exist_ok=True)
        
    def setup_directories(self):
        """Create target directories if they don't exist."""
        for folder in TARGET_DIRS.keys():
            target_path = self.base_dir / folder
            target_path.mkdir(exist_ok=True)
            print(f"✓ Ensured directory exists: {target_path}")
    
    def is_target_directory(self, path):
        """Check if a path is one of our target directories."""
        try:
            return path.name in TARGET_DIRS.keys()
        except:
            return False
    
    def handle_duplicate(self, dest_path):
        """Handle file name conflicts by adding a counter."""
        if not dest_path.exists():
            return dest_path
        
        counter = 1
        stem = dest_path.stem
        suffix = dest_path.suffix
        parent = dest_path.parent
        
        while True:
            new_name = f"{stem}_{counter}{suffix}"
            new_path = parent / new_name
            if not new_path.exists():
                return new_path
            counter += 1
    
    def log_operation(self, operation, src, dest, success=True, error=None):
        """Log file operations to a file."""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        log_file = self.log_dir / f"organize_{datetime.now().strftime('%Y%m%d')}.log"
        
        status = "SUCCESS" if success else "ERROR"
        log_entry = f"[{timestamp}] {status} - {operation}: {src} -> {dest}"
        if error:
            log_entry += f" | Error: {error}"
        
        with open(log_file, 'a', encoding='utf-8') as f:
            f.write(log_entry + '\n')
    
    def organize_files(self):
        """Main function to organize files."""
        print(f"\n{'='*60}")
        print(f"File Organizer {'(DRY RUN)' if self.dry_run else ''}")
        print(f"{'='*60}")
        print(f"Base directory: {self.base_dir}")
        print(f"Recursive: {self.recursive}")
        print(f"{'='*60}\n")
        
        if not self.base_dir.exists():
            print(f"❌ Error: Directory {self.base_dir} does not exist!")
            return
        
        self.setup_directories()
        print()
        
        # Choose walk method based on recursive setting
        if self.recursive:
            files_to_process = []
            for root, dirs, files in os.walk(self.base_dir):
                root_path = Path(root)
                # Skip target directories and hidden folders
                if self.is_target_directory(root_path) or root_path.name.startswith('.'):
                    continue
                for file in files:
                    files_to_process.append((root_path, file))
        else:
            # Only process files in the base directory
            files_to_process = [(self.base_dir, f.name) for f in self.base_dir.iterdir() if f.is_file()]
        
        # Process files
        for root_path, filename in files_to_process:
            # Skip hidden files and the script itself
            if filename.startswith('.') or filename.endswith('.py'):
                continue
            
            file_path = root_path / filename
            file_ext = file_path.suffix.lower()
            
            # Find matching category
            matched_category = None
            for category, extensions in TARGET_DIRS.items():
                if file_ext in extensions:
                    matched_category = category
                    break
            
            if not matched_category:
                continue
            
            # Determine destination
            dest_dir = self.base_dir / matched_category
            dest_path = dest_dir / filename
            
            # Handle duplicates
            if dest_path.exists() and dest_path != file_path:
                dest_path = self.handle_duplicate(dest_path)
            
            # Skip if source and destination are the same
            if file_path == dest_path:
                continue
            
            # Move or simulate move
            try:
                if self.dry_run:
                    print(f"[DRY RUN] Would move: {file_path} → {dest_path}")
                    self.stats['moved'] += 1
                else:
                    print(f"Moving: {file_path.name} → {matched_category}/")
                    shutil.move(str(file_path), str(dest_path))
                    self.log_operation("MOVE", file_path, dest_path, success=True)
                    self.stats['moved'] += 1
            except Exception as e:
                print(f"❌ Error moving {file_path}: {e}")
                self.log_operation("MOVE", file_path, dest_path, success=False, error=str(e))
                self.stats['errors'] += 1
        
        # Print summary
        print(f"\n{'='*60}")
        print("Summary:")
        print(f"  Files moved: {self.stats['moved']}")
        print(f"  Errors: {self.stats['errors']}")
        print(f"{'='*60}\n")
        
        if not self.dry_run and self.stats['moved'] > 0:
            print(f"Log saved to: {self.log_dir}")

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Organize files into categorized folders')
    parser.add_argument('directory', nargs='?', help='Directory to organize (default: ~/Downloads)')
    parser.add_argument('--dry-run', action='store_true', help='Show what would be moved without moving')
    parser.add_argument('--no-recursive', action='store_true', help='Only organize files in the base directory')
    
    args = parser.parse_args()
    
    organizer = FileOrganizer(
        base_dir=args.directory,
        dry_run=args.dry_run,
        recursive=not args.no_recursive
    )
    
    organizer.organize_files()

if __name__ == "__main__":
    main()
