import os
import shutil
import re
import logging
import time
import glob
import send2trash
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# Define your directories
source_dir = "/Users/luck/Downloads"
dest_dir_pdfs = "/Users/luck/PDFs"
dest_dir_images = "/Users/luck/IMGs"
dest_dir_zip = "/Users/luck/Zip"
dest_dir_text = "/Users/luck/Random"

# Ensure destination directories exist
os.makedirs(dest_dir_pdfs, exist_ok=True)
os.makedirs(dest_dir_images, exist_ok=True)
os.makedirs(dest_dir_zip, exist_ok=True)
os.makedirs(dest_dir_text, exist_ok=True)


def move_file(file_path):
    filename = os.path.basename(file_path)
    dest_dir = None

    if filename.endswith('.pdf'):
        dest_dir = dest_dir_pdfs
    elif filename.endswith(('.png', '.jpg', '.HEIC', '.jpeg', '.svg', '.webp', '.avif', '.mov', '.dmg', '.gif')):
        dest_dir = dest_dir_images
    elif filename.endswith('.zip'):
        dest_dir = dest_dir_zip
    elif filename.endswith(('.txt', '.circ', '.html', '.docx')):
        dest_dir = dest_dir_text

    if dest_dir:
        dest_path = os.path.join(dest_dir, filename)
        if os.path.exists(dest_path):
            base, ext = os.path.splitext(filename)
            new_filename = f"{base} (1){ext}"
            dest_path = os.path.join(dest_dir, new_filename)

        try:
            shutil.move(file_path, dest_path)
            logging.info(f"Moved {filename} to {dest_path}")
            remove_outdated_duplicates(dest_dir)
        except PermissionError as e:
            logging.error(f"PermissionError: {e}")
        except FileNotFoundError as e:
            logging.error(f"FileNotFoundError: {e}")
        except Exception as e:
            logging.error(f"Error: {e}")


def remove_outdated_duplicates(directory, pattern="*.pdf"):
    file_paths = glob.glob(os.path.join(directory, pattern))
    logging.info(f"Found {len(file_paths)} files matching the pattern {pattern} in {directory}")

    files_by_base_name = {}
    for file_path in file_paths:
        filename = os.path.basename(file_path)
        base_name, iteration = get_base_name_and_iteration(filename)
        logging.info(f"Base name: {base_name}, Iteration: {iteration} for filename: {filename}")
        if base_name not in files_by_base_name:
            files_by_base_name[base_name] = []
        files_by_base_name[base_name].append((file_path, iteration))

    for base_name, files in files_by_base_name.items():
        logging.info(f"Files for base name {base_name}: {files}")

        if len(files) > 1:
            logging.info(f"Processing duplicates for base name {base_name}")

            files.sort(key=lambda x: x[1], reverse=True)
            logging.info(f"Sorted files: {files}")

            newest_file = files[0][0]
            new_file_path = os.path.join(directory, f"{base_name} updt.pdf")
            if newest_file != new_file_path:
                try:
                    os.rename(newest_file, new_file_path)
                    logging.info(f"Renamed {newest_file} to {new_file_path}")
                except FileNotFoundError as e:
                    logging.error(f"FileNotFoundError during rename: {e}")
                    continue

            for file, _ in files[1:]:
                try:
                    send2trash.send2trash(file)
                    logging.info(f"Moved outdated file to Trash: {file}")
                except FileNotFoundError as e:
                    logging.error(f"FileNotFoundError during move to Trash: {e}")

    for file_path in glob.glob(os.path.join(directory, "* updt.pdf")):
        base_name = file_path.replace(" updt.pdf", ".pdf")
        if not os.path.exists(base_name):
            try:
                os.rename(file_path, base_name)
                logging.info(f"Renamed {file_path} to {base_name}")
            except FileNotFoundError as e:
                logging.error(f"FileNotFoundError during final rename: {e}")
        else:
            logging.warning(f"File with base name already exists: {base_name}. Skipping renaming of {file_path}.")


def get_base_name_and_iteration(filename):
    match = re.match(r"(.*?)(?:\s*\((\d+)\))?\.pdf$", filename)
    if match:
        base_name = match.group(1)
        iteration = int(match.group(2)) if match.group(2) else 0
        return base_name, iteration
    return filename, 0


def process_existing_files():
    for dirpath, dirnames, filenames in os.walk(source_dir):
        for filename in filenames:
            file_path = os.path.join(dirpath, filename)
            move_file(file_path)

    remove_outdated_duplicates(dest_dir_pdfs)
    remove_outdated_duplicates(dest_dir_images, pattern="*")
    remove_outdated_duplicates(dest_dir_zip, pattern="*.zip")
    remove_outdated_duplicates(dest_dir_text, pattern="*")


class MoverHandler(FileSystemEventHandler):
    def on_modified(self, event):
        logging.info(f"Event detected: {event}")
        if event.is_directory:
            logging.info(f"Ignoring directory: {event.src_path}")
            return
        logging.info(f"Processing file: {event.src_path}")
        move_file(event.src_path)

    def on_created(self, event):
        logging.info(f"Event detected: {event}")
        if event.is_directory:
            logging.info(f"Ignoring directory: {event.src_path}")
            return
        logging.info(f"Processing file: {event.src_path}")
        move_file(event.src_path)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO,
                        format='%(asctime)s - %(message)s',
                        datefmt='%Y-%m-%d %H:%M:%S')
    logging.info("Starting observer...")

    # Process existing files in the Downloads directory
    process_existing_files()

    path = source_dir
    event_handler = MoverHandler()
    observer = Observer()
    observer.schedule(event_handler, path, recursive=True)
    observer.start()
    try:
        while True:
            logging.info("Observer is running...")
            time.sleep(10)
    except KeyboardInterrupt:
        logging.info("Stopping observer...")
        observer.stop()
    observer.join()
