import os
import socket
import sys
import threading

from src.crypto.keys import sign_file, verify_file


class FileTransfer:
    def __init__(self, port=6001, save_dir="data/shared"):
        self.port = port
        self.save_dir = save_dir
        if not os.path.exists(self.save_dir):
            os.makedirs(self.save_dir)

    def start_server(self):
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server.bind(("", self.port))
        server.listen(5)

        while True:
            client, addr = server.accept()
            threading.Thread(
                target=self._handle_receive, args=(client, addr), daemon=True
            ).start()

    def _handle_receive(self, client_socket, addr):
        try:
            header = client_socket.recv(2048).decode().strip()
            if not header:
                return

            filename, filesize, signature_hex, sender_id = header.split("|")
            filesize = int(filesize)

            print(f"\n[RECV] {filename} ({filesize} octets)")
            print(f"[AUTH] Origine declaree : {sender_id[:10]}...")

            file_data = b""
            received_bytes = 0
            while received_bytes < filesize:
                chunk = client_socket.recv(4096)
                if not chunk:
                    break
                file_data += chunk
                received_bytes += len(chunk)
                self._draw_progress(received_bytes, filesize)

            if verify_file(file_data, signature_hex, sender_id):
                file_path = os.path.join(self.save_dir, filename)
                with open(file_path, "wb") as f:
                    f.write(file_data)
                print("\n[OK] Fichier authentique et sauvegarde.")
            else:
                print("\n[ALERTE] Signature invalide. Fichier rejete.")

        except Exception as e:
            print(f"\n[ERREUR] Reception: {e}")
        finally:
            client_socket.close()

    def send_file(self, target_ip, file_path, my_id):
        if not os.path.exists(file_path):
            print("[ERREUR] Fichier introuvable.")
            return

        try:
            filename = os.path.basename(file_path)
            with open(file_path, "rb") as f:
                file_data = f.read()

            filesize = len(file_data)
            signature_hex = sign_file(file_data)

            client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client.connect((target_ip, self.port))

            header = f"{filename}|{filesize}|{signature_hex}|{my_id}".ljust(2048)
            client.send(header.encode())

            print(f"[SEND] Envoi de {filename} a {target_ip}...")
            client.sendall(file_data)
            self._draw_progress(filesize, filesize)
            print("\n[OK] Envoi termine et signe.")
            client.close()
        except Exception as e:
            print(f"\n[ERREUR] Envoi: {e}")

    def _draw_progress(self, current, total):
        width = 40
        percent = float(current) / total
        filled = int(width * percent)
        bar = "#" * filled + "-" * (width - filled)
        sys.stdout.write(f"\r|{bar}| {percent:.1%}")
        sys.stdout.flush()