import io
import math
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog, ttk
import rawpy
from PIL import Image
from tkinterdnd2 import TkinterDnD, DND_FILES

ICONS = Path(__file__).parent / "icons"

def encode_jpeg(img, quality):
    buffer = io.BytesIO()
    img.save(buffer, format="JPEG", quality=quality)
    return buffer.getvalue()


def fit_to_size(img, target_bytes):
    data = encode_jpeg(img, 95)
    if len(data) <= target_bytes:
        return data

    while True:
        low, high = 5, 95
        best = None
        while low <= high:
            mid = (low + high) // 2
            data = encode_jpeg(img, mid)
            if len(data) <= target_bytes:
                best = data
                low = mid + 1
            else:
                high = mid - 1

        if best is not None:
            return best
        if img.width <= 16 or img.height <= 16:
            return encode_jpeg(img, 5)

        smallest = len(encode_jpeg(img, 5))
        scale = max(0.1, (target_bytes / smallest) ** 0.5 * 0.9)
        new_size = (max(1, int(img.width * scale)), max(1, int(img.height * scale)))
        img = img.resize(new_size, Image.LANCZOS)


def convert_image(nef_path, jpg_path, target_kb):
    with rawpy.imread(str(nef_path)) as raw:
        rgb = raw.postprocess(use_camera_wb=True)
    data = fit_to_size(Image.fromarray(rgb), target_kb * 1024)
    Path(jpg_path).write_bytes(data)

def jpg_name(nef, target_kb):
    tag = "_small" if target_kb < 6 else ""
    return Path(nef).stem + tag + ".jpg"

def file_size_text(path):
    try:
        return format_size(Path(path).stat().st_size)
    except OSError:
        return ""

def format_size(num_bytes):
    return f"{math.ceil(num_bytes / 1024):,} KB"

def convert_many(nef_files, out_folder, target_kb):
    out_folder = Path(out_folder)
    out_folder.mkdir(exist_ok=True)
    remembered = None

    for nef in nef_files:
        nef = Path(nef)
        jpg = out_folder / jpg_name(nef, target_kb)

        if jpg.exists():
            if remembered:
                choice = remembered
            else:
                choice, apply_all = ask_overwrite(jpg.name)
                if apply_all:
                    remembered = choice

            if choice.lower() == "cancel":
                print("Cancelled.")
                break
            if choice.lower() == "skip":
                print("Skipped:", nef.name)
                continue

        try:
            convert_image(nef, jpg, target_kb)
            print("Converted:", nef.name)
        except Exception as e:
            print("Failed:", nef.name, "-", e)

dropped_files = []

def on_drop(event):
    paths = window.tk.splitlist(event.data)
    for p in paths:
        if p.lower().endswith(".nef") and p not in dropped_files:
            dropped_files.append(p)
            file_list.insert("", "end", text=Path(p).name, image=file_icon, values=(file_size_text(p), ))

def ask_overwrite(file_name):
    dialog = tk.Toplevel(window)
    dialog.title("File already exists")
    dialog.resizable(False, False)
    dialog.transient(window)
    dialog.grab_set()

    result = {"choice": "cancel"}
    apply_all = tk.BooleanVar(value=False)

    message = f'"{file_name}" already exists.\nDo you want to replace it?'
    tk.Label(dialog, text=message, justify="left").pack(padx=20, pady=(15, 10))
    tk.Checkbutton(dialog, text="Do this for all remaining conflicts",
                   variable=apply_all).pack(padx=20, anchor="w")

    buttons = tk.Frame(dialog)
    buttons.pack(pady=15)

    def choose(choice):
        result["choice"] = choice
        dialog.destroy()

    tk.Button(buttons, text="Replace", width=10, 
              command=lambda: choose("replace")).pack(side="left", padx=5)
    tk.Button(buttons, text="Skip", width=10,
              command=lambda: choose("skip")).pack(side="left", padx=5)
    tk.Button(buttons, text="Cancel", width=10, 
              command=lambda: choose("cancel")).pack(side="left", padx=5)

    dialog.protocol("WM_DELETE_WINDOW", lambda: choose("cancel"))
    window.wait_window(dialog)

    return result["choice"], apply_all.get()

app_state = {"out_folder": None}


def on_select_folder():
    start = app_state["out_folder"] or Path.home() / "Pictures"
    folder = choose_folder(start)
    if folder:
        app_state["out_folder"] = folder
        folder_label.configure(text=str(folder), fg="black")
        convert_button.configure(state="normal")


def on_convert():
    if not dropped_files:
        messagebox.showinfo("Nothing to convert", "Drop some NEF files first.")
        return

    target_kb = ask_target_size()
    if target_kb is None:
        return

    out_folder = app_state["out_folder"]
    convert_many(dropped_files, out_folder, target_kb)
    messagebox.showinfo("Finished", f"Finished converting. Files saved to:\n{out_folder}")

def choose_folder(start_folder):
    dialog = tk.Toplevel(window)
    dialog.title("Choose where to save the JPGs")
    dialog.geometry("500x420")
    dialog.transient(window)
    dialog.grab_set()

    current = {"folder": Path(start_folder).resolve()}
    result = {"folder": None}
    rows = {}

    top = tk.Frame(dialog)
    top.pack(fill="x", padx=10, pady=(10, 5))
    tk.Button(top, text="Up", width=6, command=lambda: go_up()).pack(side="left")
    path_label = tk.Label(top, anchor="w")
    path_label.pack(side="left", fill="x", expand=True, padx=8)    

    listing = ttk.Treeview(dialog, columns=("size",), show="tree headings", selectmod="browse")
    listing.heading("#0", text="Name", anchor="w")
    listing.heading("size", text="Size", anchor="e")
    listing.column("#0", width=330, stretch=True)
    listing.column("size", width=100, anchor="e", stretch=False)

    listing.pack(fill="both", expand=True, padx=10)
    listing.tag_configure("file", foreground="gray")

    def show(folder):
        try:
            items = sorted(folder.iterdir(), key=lambda p: (not p.is_dir(), p.name.lower()))
        except PermissionError:
            messagebox.showwarning("No access", f"You can't open:\n{folder}", parent=dialog)
            return

        current["folder"] = folder
        path_label.configure(text=str(folder))
        listing.delete(*listing.get_children())
        rows.clear()

        if not items:
            listing.insert("", "end", text="(This folder is empty)", tags=("file",))

        for item in items:
            if item.is_dir():
                row = listing.insert("", "end", text=item.name, image=folder_icon, values=("",))
            else:
                row = listing.insert("", "end", text=item.name, image=file_icon, 
                                     values=(file_size_text(item),), tags=("file",))
            rows[row] = item

    def open_folder(event):
        item = rows.get(listing.focus())
        if item is not None and item.is_dir():
            show(item)

    def ignore_files(event):
        for row in listing.selection():
            item = rows.get(row)
            if item is None or not item.is_dir():
                listing.selection_remove(row)

    def go_up():
        parent = current["folder"].parent
        if parent != current["folder"]:
            show(parent)

    def new_folder():
        name = simpledialog.askstring("New folder", "Folder name:", parent=dialog)
        if not name:
            return
        try:
            (current["folder"] / name).mkdir()
        except FileExistsError:
            messagebox.showwarning("Already exists", f'"{name}" already exists.', parent=dialog)
        except OSError as e:
            messagebox.showerror("Can't create folder", str(e), parent=dialog)
        show(current["folder"])

    def select():
        result["folder"] = current["folder"]
        dialog.destroy()

    listing.bind("<Double-Button-1>", open_folder)
    listing.bind("<<TreeviewSelect>>", ignore_files)

    buttons = tk.Frame(dialog)
    buttons.pack(pady=10)
    tk.Button(buttons, text="New folder", width=12, command=new_folder).pack(side="left", padx=5)
    tk.Button(buttons, text="Select this folder", width=16, command=select).pack(side="left", padx=5)
    tk.Button(buttons, text="Cancel", width=10, command=dialog.destroy).pack(side="left", padx=5)

    show(current["folder"])
    window.wait_window(dialog)
    return result["folder"]

def ask_target_size():
    dialog = tk.Toplevel(window)
    dialog.title("JPG size")
    dialog.resizable(False, False)
    dialog.transient(window)
    dialog.grab_set()

    size_kb = tk.IntVar(value=500)
    result = {"size": None}

    tk.Label(dialog, text="Maximum size of each JPG:").pack(anchor="w", padx=15, pady=(15, 5))

    row = tk.Frame(dialog)
    row.pack(fill="x", padx=15)
    tk.Scale(row, from_=1, to=70000, orient="horizontal", variable=size_kb,
             length=300, showvalue=False).pack(side="left")
    tk.Spinbox(row, from_=1, to=70000, textvariable=size_kb, width=7).pack(side="left", padx=(8, 2))
    tk.Label(row, text="KB").pack(side="left")

    note = tk.Label(dialog, text="", fg="gray")
    note.pack(anchor="w", padx=15, pady=(5, 15))

    def update_note(*args):
        try:
            value = size_kb.get()
        except tk.TclError:
            value = 0
        if 1 <= value < 6:
            note.configure(text='Files will be saved with "_small" at the end of the name.')
        else:
            note.configure(text="")

    def proceed():
        try:
            value = size_kb.get()
        except tk.TclError:
            messagebox.showerror("Invalid size", "Please enter a whole number.", parent=dialog)
            return
        if not 1 <= value <= 70000:
            messagebox.showerror("Invalid size", "Choose a size from 1 to 70,000 KB.", parent=dialog)
            return
        result["size"] = value
        dialog.destroy()

    tk.Button(row, text="Proceed", width=10, command=proceed).pack(side="left", padx=(12, 0))

    size_kb.trace_add("write", update_note)
    dialog.protocol("WM_DELETE_WINDOW", dialog.destroy)
    window.wait_window(dialog)
    return result["size"]

window = TkinterDnD.Tk()
window.title("NEF to JPG Converter")
window.geometry("500x400")

folder_icon = tk.PhotoImage(file=str(ICONS / "folder-icon.png"))
file_icon = tk.PhotoImage(file=str(ICONS / "file-icon.png"))

style = ttk.Style()
style.configure("Treeview", rowheight=30)

label = tk.Label(window, text="Drop NEF files here")
label.pack(pady=10)

bottom = tk.Frame(window)
bottom.pack(side="bottom", fill="x", padx=10, pady=10)

tk.Button(bottom, text="Select Folder", command=on_select_folder).pack(side="left")
folder_label = tk.Label(bottom, text="No folder selected", fg="gray", anchor="w")
folder_label.pack(side="left", fill="x", expand=True, padx=8)
convert_button = tk.Button(bottom, text="Convert", command=on_convert, state="disabled")
convert_button.pack(side="right")

file_list = ttk.Treeview(window, columns=("size",), show="tree headings", selectmode="extended")
file_list.heading("#0", text="Name", anchor="w")
file_list.heading("size", text="Size", anchor="e")
file_list.column("#0", width=330, stretch=True)
file_list.column("size", width=100, anchor="e", stretch=False)

file_list.pack(fill="both", expand=True, padx=10, pady=10)
file_list.drop_target_register(DND_FILES)
file_list.dnd_bind("<<Drop>>", on_drop)

window.mainloop()