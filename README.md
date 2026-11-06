# NEF to JPG Converter

A small desktop app for converting Nikon raw photos (`.NEF`) to JPG. Drag your photos into the window, pick a folder, choose how big each JPG may be, and convert them all at once.

Built with Python and Tkinter.

## Features

- **Drag and drop** NEF files from File Explorer into the app
- **File list** with name and size (KB)
- **Folder chooser** that shows the files already in a folder, with a button to create new folders
- **Maximum file size** for the JPGs, from 1 KB to 70,000 KB, set with a slider or by typing a number
- **Overwrite protection**: if a JPG with the same name already exists, choose Replace, Skip or Cancel, with an option to apply the choice to all remaining files
- Files converted to **under 6 KB** get `_small` added to their name (for example `GER_2660_small.jpg`)

## Requirements

- Python 3 (developed and tested with Python 3.13 on Windows)
- The libraries listed in `requirements.txt`:
  - [rawpy](https://pypi.org/project/rawpy/) – reads NEF raw files
  - [Pillow](https://pypi.org/project/pillow/) – creates the JPG files
  - [tkinterdnd2](https://pypi.org/project/tkinterdnd2/) – adds drag and drop to Tkinter

## Installation

1. **Download the project.** Either click **Code → Download ZIP** on GitHub and unzip it, or clone it with Git:

   ```bash
   git clone https://github.com/YOUR-USERNAME/YOUR-REPOSITORY.git
   cd YOUR-REPOSITORY
   ```

2. **Create a virtual environment** (recommended, keeps the libraries inside this project):

   ```bash
   python -m venv .venv
   ```

3. **Activate it.**

   Windows (PowerShell):
   ```powershell
   .\.venv\Scripts\Activate.ps1
   ```

   macOS / Linux:
   ```bash
   source .venv/bin/activate
   ```

   If PowerShell says running scripts is disabled, skip this step and use `.\.venv\Scripts\python` instead of `python` in the next steps.

4. **Install the libraries:**

   ```bash
   python -m pip install -r requirements.txt
   ```

## Usage

Start the app:

```bash
python convert_image.py
```

Then:

1. **Drop your NEF files** into the list. Other file types are ignored, and dropping the same file twice adds it only once.
2. Click **Select Folder** and choose where the JPGs should be saved. You can create a new folder from the chooser.
3. Click **Convert**.
4. Set the **maximum size** for each JPG with the slider or the number box.
5. Click **Proceed**.

When it's done, a message shows where the files were saved.

### About the file size setting

A JPG doesn't have a fixed size setting, so the app works it out for each photo:

- It first tries high quality. If the file already fits, it's saved as is.
- Otherwise it lowers the quality step by step until the file fits.
- For very small sizes, it also reduces the picture's dimensions.

The number you choose is a **maximum**. A photo can't be made bigger than its best-quality version, so if you choose a very large size, the JPG will usually come out smaller than that.

Converting takes a few seconds per photo, and the window doesn't respond while it works.

## Project structure

```
├── icons/
│   ├── file-icon.png
│   └── folder-icon.png
├── convert_image.py
├── requirements.txt
└── README.md
```

## Credits

- File icon: TODO – add the icon's source, author and license here
- Folder icon: TODO – add the icon's source, author and license here

## License

TODO – choose a license (see "Adding a license" in the setup notes).
