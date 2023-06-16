import os

def get_file_size(file_path):
    # Check if the file exists
    if os.path.exists(file_path):
        # Get the file size in bytes
        file_size = os.path.getsize(file_path)
        return file_size
    else:
        return None

# Example usage
file_path = '/home/mint/Downloads/videoplayback_4.docx'
size_in_bytes = get_file_size(file_path)

print(size_in_bytes<5242880)

if size_in_bytes is not None:
    print(f"File size: {size_in_bytes} bytes")
else:
    print("File not found or inaccessible.")
