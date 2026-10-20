#!/usr/bin/env python3
"""
GPG File Encryptor GUI
Requirements:
  - Python 3
  - GnuPG installed and available as `gpg` on PATH
Use a PUBLIC key file (.asc or .gpg). Do not select a private-key file.
"""
import os
import shutil
import subprocess
import tempfile
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

APP_TITLE = "GPG File Encryptor"


def find_gpg():
    return shutil.which("gpg") or shutil.which("gpg.exe")


class GPGEncryptor:
    def __init__(self, root):
        self.root = root
        self.root.title(APP_TITLE)
        self.root.geometry("720x520")
        self.root.minsize(650, 470)

        self.key_path = tk.StringVar()
        self.recipient = tk.StringVar()
        self.output_dir = tk.StringVar()
        self.selected_files = []

        main = ttk.Frame(root, padding=16)
        main.pack(fill="both", expand=True)

        ttk.Label(main, text="GPG File Encryptor", font=("Segoe UI", 17, "bold")).pack(anchor="w")
        ttk.Label(
            main,
            text="Encrypt files or ZIP archives with a recipient's public key.",
            wraplength=660
        ).pack(anchor="w", pady=(2, 14))

        key_frame = ttk.LabelFrame(main, text="1. Public key", padding=10)
        key_frame.pack(fill="x", pady=5)
        ttk.Entry(key_frame, textvariable=self.key_path).pack(side="left", fill="x", expand=True)
        ttk.Button(key_frame, text="Browse…", command=self.choose_key).pack(side="left", padx=(8, 0))
        ttk.Button(key_frame, text="Import / Read key", command=self.load_key).pack(side="left", padx=(8, 0))

        rec_frame = ttk.LabelFrame(main, text="2. Encryption recipient", padding=10)
        rec_frame.pack(fill="x", pady=5)
        ttk.Label(rec_frame, text="Key ID / email / fingerprint:").pack(side="left")
        self.recipient_entry = ttk.Entry(rec_frame, textvariable=self.recipient)
        self.recipient_entry.pack(side="left", fill="x", expand=True, padx=(8, 0))

        files_frame = ttk.LabelFrame(main, text="3. Files to encrypt", padding=10)
        files_frame.pack(fill="both", expand=True, pady=5)
        buttons = ttk.Frame(files_frame)
        buttons.pack(fill="x", pady=(0, 8))
        ttk.Button(buttons, text="Add files…", command=self.add_files).pack(side="left")
        ttk.Button(buttons, text="Remove selected", command=self.remove_selected).pack(side="left", padx=8)
        ttk.Button(buttons, text="Clear list", command=self.clear_files).pack(side="left")
        self.file_list = tk.Listbox(files_frame, selectmode=tk.EXTENDED, height=7)
        self.file_list.pack(fill="both", expand=True)

        out_frame = ttk.LabelFrame(main, text="4. Output folder (optional)", padding=10)
        out_frame.pack(fill="x", pady=5)
        ttk.Entry(out_frame, textvariable=self.output_dir).pack(side="left", fill="x", expand=True)
        ttk.Button(out_frame, text="Browse…", command=self.choose_output).pack(side="left", padx=(8, 0))

        bottom = ttk.Frame(main)
        bottom.pack(fill="x", pady=(12, 0))
        self.status = tk.StringVar(value="Ready. Select a public key and files.")
        ttk.Label(bottom, textvariable=self.status, wraplength=490).pack(side="left", fill="x", expand=True)
        ttk.Button(bottom, text="Encrypt to .gpg", command=self.encrypt, style="Accent.TButton").pack(side="right")

        self.gpg = find_gpg()
        if not self.gpg:
            self.status.set("GnuPG was not found. Install Gpg4win, then restart this app.")

    def choose_key(self):
        p = filedialog.askopenfilename(
            title="Select PUBLIC key file",
            filetypes=[("OpenPGP key files", "*.asc *.gpg *.pgp *.key"), ("All files", "*.*")]
        )
        if p:
            self.key_path.set(p)

    def run_gpg(self, args, home):
        return subprocess.run(
            [self.gpg, "--batch", "--no-tty", "--homedir", home] + args,
            capture_output=True, text=True, encoding="utf-8", errors="replace"
        )

    def load_key(self):
        if not self.gpg:
            messagebox.showerror("GnuPG missing", "Install GnuPG / Gpg4win first.")
            return
        key = self.key_path.get().strip()
        if not key or not os.path.isfile(key):
            messagebox.showwarning("Choose key", "Choose your recipient's PUBLIC key file first.")
            return
        try:
            with open(key, "rb") as f:
                header = f.read(100).upper()
            if b"PRIVATE KEY BLOCK" in header:
                messagebox.showerror(
                    "Private key selected",
                    "This file appears to be a PRIVATE key, not a public key.\n\n"
                    "For safety, do not use or share it here. Ask the key owner to export "
                    "their public key and select that public .asc file instead."
                )
                return
        except OSError as e:
            messagebox.showerror("Cannot read key", str(e))
            return

        with tempfile.TemporaryDirectory(prefix="gpg_gui_") as home:
            os.chmod(home, 0o700)
            result = self.run_gpg(["--import", key], home)
            if result.returncode != 0:
                messagebox.showerror("Key import failed", result.stderr or result.stdout)
                return
            listing = self.run_gpg(
                ["--with-colons", "--list-keys", "--fingerprint"], home
            )
            if listing.returncode != 0:
                messagebox.showerror("Key listing failed", listing.stderr or listing.stdout)
                return
            keys = []
            current_uid = ""
            for line in listing.stdout.splitlines():
                parts = line.split(":")
                if parts[0] == "uid" and len(parts) > 9:
                    current_uid = parts[9].replace("\\x3a", ":")
                elif parts[0] == "pub" and len(parts) > 4:
                    keys.append((parts[4], current_uid))
                elif parts[0] == "fpr" and len(parts) > 9 and keys:
                    keys[-1] = (parts[9], keys[-1][1])
            if not keys:
                messagebox.showerror("No public key found", "The selected file did not provide a usable public key.")
                return
            if len(keys) == 1:
                self.recipient.set(keys[0][0])
                messagebox.showinfo(
                    "Public key ready",
                    "Public key imported for this encryption session.\n"
                    f"Recipient: {keys[0][1] or '(no user ID)'}\nFingerprint: {keys[0][0]}\n\n"
                    "The key will be imported again into a temporary keyring when encrypting."
                )
            else:
                options = "\n".join(f"{fp}  {uid}" for fp, uid in keys)
                messagebox.showinfo("Public keys found", "Copy the fingerprint for the intended recipient into the recipient field:\n\n" + options)

    def add_files(self):
        paths = filedialog.askopenfilenames(
            title="Choose files or ZIP archives",
            filetypes=[("All files", "*.*")]
        )
        for p in paths:
            if p not in self.selected_files:
                self.selected_files.append(p)
                self.file_list.insert(tk.END, p)

    def remove_selected(self):
        indexes = list(self.file_list.curselection())
        for i in reversed(indexes):
            self.file_list.delete(i)
            del self.selected_files[i]

    def clear_files(self):
        self.selected_files.clear()
        self.file_list.delete(0, tk.END)

    def choose_output(self):
        p = filedialog.askdirectory(title="Choose output folder")
        if p:
            self.output_dir.set(p)

    def encrypt(self):
        if not self.gpg:
            messagebox.showerror("GnuPG missing", "Install GnuPG / Gpg4win first.")
            return
        key = self.key_path.get().strip()
        recipient = self.recipient.get().strip()
        if not key or not os.path.isfile(key):
            messagebox.showwarning("Public key required", "Select the recipient's PUBLIC key file.")
            return
        if not recipient:
            messagebox.showwarning("Recipient required", "Click Import / Read key, or enter the recipient fingerprint.")
            return
        if not self.selected_files:
            messagebox.showwarning("No files", "Add at least one file to encrypt.")
            return

        outdir = self.output_dir.get().strip() or os.path.dirname(self.selected_files[0])
        if not os.path.isdir(outdir):
            messagebox.showerror("Output folder", "The output folder does not exist.")
            return

        # Avoid accidentally using a private key file.
        try:
            with open(key, "rb") as f:
                header = f.read(100).upper()
            if b"PRIVATE KEY BLOCK" in header:
                messagebox.showerror("Private key selected", "Select a PUBLIC key file, not a private key file.")
                return
        except OSError as e:
            messagebox.showerror("Cannot read key", str(e))
            return

        success, failures = [], []
        self.status.set("Encrypting…")
        self.root.update_idletasks()
        with tempfile.TemporaryDirectory(prefix="gpg_encrypt_") as home:
            os.chmod(home, 0o700)
            imp = self.run_gpg(["--import", key], home)
            if imp.returncode != 0:
                messagebox.showerror("Key import failed", imp.stderr or imp.stdout)
                self.status.set("Key import failed.")
                return

            for src in self.selected_files:
                if not os.path.isfile(src):
                    failures.append(f"{src}: file not found")
                    continue
                dest = os.path.join(outdir, os.path.basename(src) + ".gpg")
                if os.path.abspath(src) == os.path.abspath(dest):
                    failures.append(f"{src}: output would overwrite the input")
                    continue
                cmd = [
                    "--yes", "--trust-model", "always",
                    "--output", dest, "--encrypt", "--recipient", recipient, src
                ]
                result = self.run_gpg(cmd, home)
                if result.returncode == 0 and os.path.isfile(dest) and os.path.getsize(dest) > 0:
                    success.append(dest)
                else:
                    try:
                        if os.path.exists(dest):
                            os.remove(dest)
                    except OSError:
                        pass
                    failures.append(f"{os.path.basename(src)}: {(result.stderr or result.stdout).strip()}")

        self.status.set(f"Finished. Encrypted {len(success)} file(s); {len(failures)} failed.")
        report = ""
        if success:
            report += "Encrypted files:\n" + "\n".join(success)
        if failures:
            report += ("\n\nFailed:\n" if report else "Failed:\n") + "\n".join(failures)
        if success and not failures:
            messagebox.showinfo("Encryption complete", report)
        elif success:
            messagebox.showwarning("Partially complete", report)
        else:
            messagebox.showerror("Encryption failed", report or "No files were encrypted.")


def main():
    root = tk.Tk()
    try:
        ttk.Style().theme_use("vista" if os.name == "nt" else "clam")
    except tk.TclError:
        pass
    GPGEncryptor(root)
    root.mainloop()


if __name__ == "__main__":
    main()
