import os
import shutil
import PyPDF2

downloads_folder = os.path.join(os.path.expanduser("~"), "Downloads")
project_folder = os.getcwd()  # Use current project directory

# Ensure the project folder exists
os.makedirs(project_folder, exist_ok=True)

# Loop through all PDFs in Downloads
for file in os.listdir(downloads_folder):
    if file.endswith(".pdf"):
        source = os.path.join(downloads_folder, file)
        destination = os.path.join(project_folder, file)
        shutil.copy(source, destination)
        print(f"✅ Copied {file} to {project_folder}")

        # Convert PDF content to text
        with open(destination, "rb") as pdf_file:
            reader = PyPDF2.PdfReader(pdf_file)
            text = ""
            for page_num in range(len(reader.pages)):
                page = reader.pages[page_num]
                text += page.extract_text()

            # Save the extracted text to a .txt file
            text_filename = os.path.splitext(file)[0] + ".txt"
            text_filepath = os.path.join(project_folder, text_filename)
            with open(text_filepath, "w", encoding="utf-8") as text_file:
                text_file.write(text)
            print(f"✅ Extracted text from {file} and saved to {text_filepath}")


