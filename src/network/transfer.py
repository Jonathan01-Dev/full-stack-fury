import socket
import threading
import os
import sys

class FileTransfer:
    def __init__(self, port=6001, save_dir="data/shared"):
        self.port = port
        self.save_dir = save_dir
        if not os.path.exists(self.save_dir):
            os.makedirs(self.save_dir)

    def start_server(self):
        """Lance le serveur TCP pour recevoir les fichiers."""
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server.bind(('', self.port))
        server.listen(5)
        
        while True:
            client, addr = server.accept()
            threading.Thread(target=self._handle_receive, args=(client, addr), daemon=True).start()

    def _handle_receive(self, client_socket, addr):
        try:
            # 1. Lire l'en-tête (Nom | Taille)
            header = client_socket.recv(1024).decode().strip()
            if not header: return
            
            filename, filesize = header.split('|')
            filesize = int(filesize)
            print(f"\n[📥] Réception de : {filename} ({filesize} octets)")

            # 2. Lire le contenu avec barre de progression
            file_path = os.path.join(self.save_dir, filename)
            received_bytes = 0
            
            with open(file_path, "wb") as f:
                while received_bytes < filesize:
                    chunk = client_socket.recv(4096)
                    if not chunk: break
                    f.write(chunk)
                    received_bytes += len(chunk)
                    self._draw_progress(received_bytes, filesize)
            
            print(f"\n✅ Terminé ! Sauvegardé dans {self.save_dir}")

        except Exception as e:
            print(f"\n❌ Erreur réception : {e}")
        finally:
            client_socket.close()

    def send_file(self, target_ip, file_path):
        """Envoie un fichier avec barre de progression."""
        if not os.path.exists(file_path):
            print(f"❌ Fichier introuvable.")
            return

        try:
            filename = os.path.basename(file_path)
            filesize = os.path.getsize(file_path)
            client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client.connect((target_ip, self.port))

            # 1. Envoyer l'en-tête (Format: Nom|Taille)
            header = f"{filename}|{filesize}".ljust(1024)
            client.send(header.encode())

            # 2. Envoyer le contenu avec barre de progression
            sent_bytes = 0
            with open(file_path, "rb") as f:
                print(f"📤 Envoi de {filename} à {target_ip}...")
                while sent_bytes < filesize:
                    data = f.read(4096)
                    if not data: break
                    client.sendall(data)
                    sent_bytes += len(data)
                    self._draw_progress(sent_bytes, filesize)
            
            print(f"\n✨ Envoi terminé !")
            client.close()
        except Exception as e:
            print(f"\n❌ Échec de l'envoi : {e}")

    def _draw_progress(self, current, total):
        """Affiche une barre de progression simple dans la console."""
        width = 40
        percent = float(current) / total
        filled = int(width * percent)
        bar = "█" * filled + "-" * (width - filled)
        sys.stdout.write(f"\r|{bar}| {percent:.1%}")
        sys.stdout.flush()