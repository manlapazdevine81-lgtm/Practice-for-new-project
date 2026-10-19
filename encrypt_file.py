
import subprocess
from pathlib import Path

def run_command(command):
    return subprocess.run(
        command,
        check=True,
        text=True,
        capture_output=True
    )

def main():
    print("=== GPG File Encryption ===")

    input_path = Path(input("Enter the ZIP or CSV file path: ").strip().strip('"'))
    public_key_path = Path(input("Enter the public key file path (.asc/.gpg): ").strip().strip('"'))

    if not input_path.is_file():
        print("ERROR: Input file not found.")
        return

    if not public_key_path.is_file():
        print("ERROR: Public key file not found.")
        return

    recipient = input("Enter the recipient email or key ID: ").strip()

    if not recipient:
        print("ERROR: Recipient is required.")
        return

    output_path = Path(str(input_path) + ".gpg")

    try:
        # Import the recipient's public key.
        run_command([
            "gpg",
            "--batch",
            "--import",
            str(public_key_path)
        ])

        # Encrypt the original file for the recipient.
        run_command([
            "gpg",
            "--batch",
            "--yes",
            "--output",
            str(output_path),
            "--encrypt",
            "--recipient",
            recipient,
            str(input_path)
        ])

        if output_path.is_file() and output_path.stat().st_size > 0:
            print("\nSUCCESS: Encryption completed.")
            print(f"Input:  {input_path}")
            print(f"Output: {output_path}")
        else:
            print("ERROR: Output file was not created correctly.")

    except FileNotFoundError:
        print("ERROR: GPG is not installed or is not available in PATH.")
    except subprocess.CalledProcessError as error:
        print("ERROR: GPG encryption failed.")
        if error.stderr:
            print(error.stderr)
        if error.stdout:
            print(error.stdout)

if __name__ == "__main__":
    main()
