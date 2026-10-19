
import subprocess
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from pathlib import Path
import threading


class GPGEncryptionApp:
    def __init__(self, root):
        self.root = root
        self.root.title("GPG File Encryption")
        self.root.geometry("650x530")
        self.root.minsize(580, 490)
        self.root.configure(bg="#f4f6f9")

        self.input_file = tk.StringVar()
        self.public_key = tk.StringVar()
        self.recipient = tk.StringVar()
        self.output_file = tk.StringVar()
        self.status = tk.StringVar(value="Ready to encrypt your file.")

        self.build_ui()

    def build_ui(self):
        # Header
        header = tk.Frame(self.root, bg="#172554", height=105)
        header.pack(fill="x")
        header.pack_propagate(False)

        tk.Label(
            header,
            text="GPG FILE ENCRYPTION",
            font=("Segoe UI", 19, "bold"),
            fg="white",
            bg="#172554"
        ).pack(anchor="w", padx=28, pady=(22, 4))

        tk.Label(
            header,
            text="Secure your ZIP and CSV files using a public key",
            font=("Segoe UI", 10),
            fg="#cbd5e1",
            bg="#172554"
        ).pack(anchor="w", padx=29)

        # Main form
        form = tk.Frame(self.root, bg="#f4f6f9")
        form.pack(fill="both", expand=True, padx=28, pady=20)

        self.add_file_field(
            form, "File to encrypt", self.input_file,
            self.select_input, 0
        )
        self.add_file_field(
            form, "Recipient's public key (.asc)",
            self.public_key, self.select_key, 1
        )

        tk.Label(
            form, text="Recipient email or key ID",
            font=("Segoe UI", 10, "bold"),
            bg="#f4f6f9", fg="#334155"
        ).grid(row=4, column=0, sticky="w", pady=(13, 6))

        ttk.Entry(
            form, textvariable=self.recipient
        ).grid(row=5, column=0, columnspan=2, sticky="ew", ipady=6)

        self.add_file_field(
            form, "Save encrypted file as",
            self.output_file, self.select_output, 6
        )

        form.columnconfigure(0, weight=1)

        # Encrypt button
        self.encrypt_button = tk.Button(
            form,
            text="ENCRYPT FILE",
            command=self.start_encryption,
            font=("Segoe UI", 11, "bold"),
            bg="#2563eb",
            fg="white",
            activebackground="#1d4ed8",
            activeforeground="white",
            relief="flat",
            cursor="hand2",
            pady=12
        )
        self.encrypt_button.grid(
            row=8, column=0, columnspan=2,
            sticky="ew", pady=(22, 12)
        )

        self.progress = ttk.Progressbar(
            form, mode="indeterminate"
        )
        self.progress.grid(
            row=9, column=0, columnspan=2, sticky="ew"
        )

        tk.Label(
            form,
            textvariable=self.status,
            font=("Segoe UI", 9),
            bg="#f4f6f9",
            fg="#475569",
            wraplength=570,
            justify="left"
        ).grid(row=10, column=0, columnspan=2, sticky="w", pady=12)

        tk.Label(
            self.root,
            text="GPG Encryption Tool • ZIP / CSV",
            font=("Segoe UI", 8),
            bg="#e2e8f0",
            fg="#64748b",
            pady=8
        ).pack(fill="x", side="bottom")

    def add_file_field(self, parent, label, variable, command, row):
        tk.Label(
            parent,
            text=label,
            font=("Segoe UI", 10, "bold"),
            bg="#f4f6f9",
            fg="#334155"
        ).grid(row=row, column=0, columnspan=2,
               sticky="w", pady=(4, 6))

        entry_row = row + 1

        ttk.Entry(
            parent, textvariable=variable
        ).grid(row=entry_row, column=0, sticky="ew", ipady=6)

        tk.Button(
            parent,
            text="Browse",
            command=command,
            font=("Segoe UI", 9),
            bg="#e2e8f0",
            fg="#1e293b",
            relief="flat",
            cursor="hand2",
            padx=14,
            pady=5
        ).grid(row=entry_row, column=1, padx=(8, 0))

    def select_input(self):
        filename = filedialog.askopenfilename(
            title="Select a file to encrypt",
            filetypes=[
                ("ZIP and CSV files", "*.zip *.csv"),
                ("All files", "*.*")
            ]
        )
        if filename:
            self.input_file.set(filename)
            self.output_file.set(filename + ".gpg")

    def select_key(self):
        filename = filedialog.askopenfilename(
            title="Select recipient's public key",
            filetypes=[
                ("Public key files", "*.asc *.gpg *.pub"),
                ("All files", "*.*")
            ]
        )
        if filename:
            self.public_key.set(filename)

    def select_output(self):
        source = self.input_file.get()
        default_name = (
            Path(source).name + ".gpg"
            if source else "encrypted_file.gpg"
        )

        filename = filedialog.asksaveasfilename(
            title="Save encrypted file",
            defaultextension=".gpg",
            initialfile=default_name,
            filetypes=[
                ("GPG encrypted files", "*.gpg"),
                ("All files", "*.*")
            ]
        )
        if filename:
            self.output_file.set(filename)

    def start_encryption(self):
        source = Path(self.input_file.get().strip())
        key = Path(self.public_key.get().strip())
        recipient = self.recipient.get().strip()
        output = Path(self.output_file.get().strip())

        if not source.is_file():
            messagebox.showerror(
                "Missing file", "Please select a valid ZIP or CSV file."
            )
            return

        if source.suffix.lower() not in (".zip", ".csv"):
            messagebox.showerror(
                "Unsupported file",
                "Please choose a ZIP or CSV file."
            )
            return

        if not key.is_file():
            messagebox.showerror(
                "Missing public key",
                "Please select a valid public key file."
            )
            return

        if not recipient:
            messagebox.showerror(
                "Missing recipient",
                "Enter the recipient's email or key ID."
            )
            return

        if not str(output):
            messagebox.showerror(
                "Missing output", "Choose where to save the encrypted file."
            )
            return

        if source.resolve() == output.resolve():
            messagebox.showerror(
                "Invalid output",
                "The output must not overwrite the original file."
            )
            return

        if output.exists():
            if not messagebox.askyesno(
                "Confirm overwrite",
                "The output file already exists. Replace it?"
            ):
                return

        self.encrypt_button.config(state="disabled")
        self.progress.start(10)
        self.status.set("Encrypting file. Please wait...")

        threading.Thread(
            target=self.encrypt_file,
            args=(source, key, recipient, output),
            daemon=True
        ).start()

    def encrypt_file(self, source, key, recipient, output):
        try:
            # Check whether GPG is installed and available.
            subprocess.run(
                ["gpg", "--version"],
                check=True,
                capture_output=True,
                text=True
            )

            # Import the recipient's public key.
            subprocess.run(
                ["gpg", "--batch", "--import", str(key)],
                check=True,
                capture_output=True,
                text=True
            )

            # Encrypt the selected file for the specified recipient.
            result = subprocess.run(
                [
                    "gpg",
                    "--batch",
                    "--yes",
                    "--trust-model", "always",
                    "--output", str(output),
                    "--encrypt",
                    "--recipient", recipient,
                    str(source)
                ],
                check=True,
                capture_output=True,
                text=True
            )

            if output.is_file() and output.stat().st_size > 0:
                self.root.after(
                    0, lambda: self.finish_success(output)
                )
            else:
                raise RuntimeError("The encrypted output file is empty.")

        except FileNotFoundError:
            self.root.after(
                0,
                lambda: self.finish_error(
                    "GPG is not installed or is not available in PATH."
                )
            )

        except subprocess.CalledProcessError as error:
            details = (error.stderr or error.stdout or "").strip()
            self.root.after(
                0,
                lambda msg=details: self.finish_error(
                    msg or "GPG encryption failed."
                )
            )

        except Exception as error:
            self.root.after(
                0, lambda msg=str(error): self.finish_error(msg)
            )

    def finish_success(self, output):
        self.progress.stop()
        self.encrypt_button.config(state="normal")
        self.status.set("Encryption completed successfully.")

        messagebox.showinfo(
            "Encryption successful",
            f"Your file has been encrypted successfully.\n\n"
            f"Output file:\n{output}"
        )

    def finish_error(self, message):
        self.progress.stop()
        self.encrypt_button.config(state="normal")
        self.status.set("Encryption failed. See the error message.")

        messagebox.showerror("Encryption failed", message)


if __name__ == "__main__":
    root = tk.Tk()
    app = GPGEncryptionApp(root)
    root.mainloop()
