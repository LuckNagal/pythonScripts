import os
import re
import glob
import logging
import send2trash  # Ensure you have this package installed: pip install send2trash

# Define your directory and file pattern
dest_dir_pdfs = "/Users/luck/PDFs"
file_pattern = os.path.join(dest_dir_pdfs, "*.pdf")

# Ensure the destination directory exists
os.makedirs(dest_dir_pdfs, exist_ok=True)

def get_base_name_and_iteration(filename):
    # Extract the base name and iteration number if present
    match = re.match(r"(.*?)(?:\s*\((\d+)\))?\.pdf$", filename)
    if match:
        base_name = match.group(1)
        iteration = int(match.group(2)) if match.group(2) else 0
        return base_name, iteration
    return filename, 0

def remove_outdated_duplicates(directory, pattern):
    # Get the list of files matching the pattern
    file_paths = glob.glob(pattern)
    logging.info(f"Found {len(file_paths)} files matching the pattern {pattern}")

    # Group files by their base names and iterations
    files_by_base_name = {}
    for file_path in file_paths:
        filename = os.path.basename(file_path)
        base_name, iteration = get_base_name_and_iteration(filename)
        logging.info(f"Base name: {base_name}, Iteration: {iteration} for filename: {filename}")
        if base_name not in files_by_base_name:
            files_by_base_name[base_name] = []
        files_by_base_name[base_name].append((file_path, iteration))

    # Log the grouped files
    for base_name, files in files_by_base_name.items():
        logging.info(f"Files for base name {base_name}: {files}")

    # Remove outdated duplicates, keeping only the newest version
    for base_name, files in files_by_base_name.items():
        if len(files) > 1:
            logging.info(f"Processing duplicates for base name {base_name}")

            # Sort files by iteration number
            files.sort(key=lambda x: x[1], reverse=True)
            logging.info(f"Sorted files: {files}")

            # Rename the newest file by appending 'updt'
            newest_file = files[0][0]
            new_file_path = os.path.join(directory, f"{base_name} updt.pdf")
            if newest_file != new_file_path:
                os.rename(newest_file, new_file_path)
                logging.info(f"Renamed {newest_file} to {new_file_path}")

            # Move the older files to the Trash
            for file, _ in files[1:]:
                send2trash.send2trash(file)
                logging.info(f"Moved outdated file to Trash: {file}")

    # Final renaming of 'updt' files back to their base names
    for file_path in glob.glob(os.path.join(directory, "* updt.pdf")):
        base_name = file_path.replace(" updt.pdf", ".pdf")
        if not os.path.exists(base_name):
            os.rename(file_path, base_name)
            logging.info(f"Renamed {file_path} to {base_name}")
        else:
            logging.warning(f"File with base name already exists: {base_name}. Skipping renaming of {file_path}.")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO,
                        format='%(asctime)s - %(message)s',
                        datefmt='%Y-%m-%d %H:%M:%S')
    logging.info("Starting duplicate removal process based on modification time...")

    # Remove outdated duplicates in the PDFs directory
    remove_outdated_duplicates(dest_dir_pdfs, file_pattern)

    logging.info("Duplicate removal process completed.")
