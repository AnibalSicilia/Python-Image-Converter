from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog

import rawpy
from PIL import Image
from tkinterdnd2 import TkinterDnD, DND_FILES

def convert_image(nef_path, jpg_path, quality=92):
    with rawpy.imread(str(nef_path)) as raw:
        rgb = raw.postprocess(use_camera_wb=True)
    Image.fromarray(rgb).save(jpg_path, quality=quality)

#convert_image("GER_2660.NEF", "yourphoto.jpg")

def convert_many(nef_files, out_folder):
    out_folder = Path(out_folder)
    out_folder.mkdir(exist_ok=True)
    remembered = None

    for nef in nef_files:
        nef = Path(nef)
        jpg = out_folder / (nef.stem + ".jpg")

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
            convert_image(nef, jpg)
            print("Converted:", nef.name)
        except Exception as e:
            print("Failed:", nef.name, "-", e)

#files = list(Path(".").glob("*.NEF"))
#convert_many(files, "jpg_converted")
#print("Done!") 

dropped_files = []

def on_drop(event):
    paths = window.tk.splitlist(event.data)
    for p in paths:
        if p.lower().endswith(".nef") and p not in dropped_files:
            dropped_files.append(p)
            file_list.insert("end", Path(p).name)

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

def on_convert():
    if not dropped_files:
        messagebox.showinfo("Nothing to convert", "Drop some NEF files first.")
        return
    #out_folder = filedialog.askdirectory(title="Choose where to save the JPGs")
    #if not out_folder:
    #    return

    out_folder = choose_folder(Path.home() / "Pictures")

    convert_many(dropped_files, out_folder)
    messagebox.showinfo("Finished",  f"Finished converting. Files saved to:\n{out_folder}")

def choose_folder(start_folder):
    dialog = tk.Toplevel(window)
    dialog.title("Choose where to save the JPGs")
    dialog.geometry("500x420")
    dialog.transient(window)
    dialog.grab_set()

    current = {"folder": Path(start_folder)} 
    result = {"folder": None}
    entries = []

    top = tk.Frame(dialog)
    top.pack(fill='x', padx=10, pady=(10, 5))
    tk.Button(top, text="Up", width=6, command=lambda: go_up()).pack(side="left")
    path_label = tk.Label(top, anchor="w")
    path_label.pack(side="left", fill="x", expand=True, padx=8)
    
    listing = tk.Listbox(dialog)
    listing.pack(fill="both", expand=True, padx=10)

    def show(folder):
        try:
            items = sorted(folder.iterdir(), key=lambda p: (not p.is_dir(), p.name.lower()))
        except PermissionError:
            messagebox.showwarning("No access", f"You can't open:\n{folder}", parent=dialog)
            return

        current["folder"] = folder
        path_label.configure(text=str(folder))
        listing.delete(0, "end")
        entries.clear()

        if not items:
            listing.insert("end", "(This folder is empty)")
            listing.itemconfig(0, fg="gray")
            entries.append(None)

        for item in items:
            if item.is_dir():
                listing.insert("end", f"[Folder] {item.name}")
            else:
                listing.insert("end", f"    {item.name}")
                listing.itemconfig(listing.size() - 1, fg="gray")
            entries.append(item)

    def open_folder(event):
        selected = listing.curselection()
        if not selected:
            return
        item = entries[selected[0]]
        if item is not None and item.is_dir():
            show(item)

    def ignore_files(event):
        selected = listing.curselection()
        if not selected:
            return
        item = entries[selected[0]]
        if item is None or not item.is_dir():
            listing.selection_clear(0, "end")

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
    listing.bind("<<ListBoxSelect>>", ignore_files)

    buttons = tk.Frame(dialog)
    buttons.pack(pady=10) 
    tk.Button(buttons, text="New folder", width=12, command=new_folder).pack(side="left", padx=5)
    tk.Button(buttons, text="Select this folder", width=16, command=select).pack(side="left", padx=5)
    tk.Button(buttons, text="Cancel", width=10, command=dialog.destroy).pack(side="left", padx=5)   

    show(current["folder"])
    window.wait_window(dialog)
    return result["folder"]

window = TkinterDnD.Tk()
window.title("NEF to JPG Converter")
window.geometry("500x400")

label = tk.Label(window, text="Drop NEF files here")
label.pack(pady=10)

file_list = tk.Listbox(window)
file_list.pack(fill="both", expand=True, padx=10, pady=10)
file_list.drop_target_register(DND_FILES)
file_list.dnd_bind("<<Drop>>", on_drop)

convert_button = tk.Button(window, text="Convert", command=on_convert)
convert_button.pack(pady=10)
window.mainloop()