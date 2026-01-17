import pyautogui
from ctypes import windll
import win32gui
import json
import asyncio
import os
import sys
import json
import shutil
import requests
import zipfile
from pathlib import Path

stop_event = asyncio.Event()

pyautogui.FAILSAFE = True
hdc = windll.user32.GetDC(0)

hwnd = win32gui.FindWindow(None, "Farmland")

stop = False

point: dict
with open("point.json") as file:
  point = json.load(file)

async def press(key, time):
    pyautogui.keyDown(key)
    await asyncio.sleep(time)
    pyautogui.keyUp(key)

def coo(x, y):
    rect = win32gui.GetWindowRect(hwnd)
    pos = rect[0], rect[1] + 90
    taille = rect[2] - pos[0], rect[3] - pos[1]
    return x*taille[0]+pos[0], y*taille[1]+pos[1]

# def getColor(x, y, save_img=False):
#     color: int = windll.gdi32.GetPixel(hdc, x, y)
#     r, g, b = color & 0xFF, (color >> 8) & 0xFF, (color >> 16) & 0xFF
#     if save_img:
#         a = Image.new("P", (10, 11), (r, g, b))
#         a.save("img.png")
#     return color

async def click_map():
    pyautogui.click(coo(*point["gui"]["map"]))

async def swip_map():
    pyautogui.dragTo(coo(0.9, 0.5))
    pyautogui.dragRel(-300, 0, 0.2)
    await asyncio.sleep(0.3)

async def click_recolt():
    pyautogui.click(coo(0.5, 0.85))
    await asyncio.sleep(3)

async def tp_spawn(name):
    await click_map()
    await swip_map()
    pyautogui.click(coo(*point["tp"][name]))

async def recolt(name):
    await tp_spawn(point["recolt"][name]["tp"])
    await asyncio.sleep(0.3)
    for x, y in point["recolt"][name]["move"]:
        await press(x, y)
    await click_recolt()

class GitHubUpdater:
    def __init__(self, owner, repo, current_version):
        """
        Système de mise à jour depuis GitHub

        Args:
            owner: Propriétaire du dépôt (ex: "microsoft")
            repo: Nom du dépôt (ex: "vscode")
            current_version: Version actuelle de l'app (ex: "1.0.0")
        """
        self.owner = owner
        self.repo = repo
        self.current_version = current_version
        self.api_url = f"https://api.github.com/repos/{owner}/{repo}/releases/latest"

    def check_update(self):
        """Vérifie si une mise à jour est disponible"""
        try:
            print("🔍 Vérification des mises à jour...")
            response = requests.get(self.api_url)

            if response.status_code == 200:
                data = response.json()
                latest_version = data['tag_name'].replace('v', '')

                print(f"📦 Version actuelle: {self.current_version}")
                print(f"🆕 Dernière version: {latest_version}")

                if latest_version != self.current_version:
                    print(f"✅ Mise à jour disponible!")
                    return {
                        'available': True,
                        'version': latest_version,
                        'download_url': data.get('zipball_url'),
                        'notes': data.get('body', 'Pas de notes')
                    }
                else:
                    print("✅ Vous avez déjà la dernière version")
                    return {'available': False}
            elif response.status_code == 404:
                print("⚠️  Aucune release publiée sur ce dépôt")
                print("💡 Le propriétaire doit créer une release sur GitHub")
                return {'available': False, 'error': 'no_releases'}
            else:
                print(f"❌ Erreur API: {response.status_code}")
                return {'available': False, 'error': response.status_code}

        except Exception as e:
            print(f"❌ Erreur: {str(e)}")
            return {'available': False, 'error': str(e)}

    def download_update(self, download_url, save_path="update.zip"):
        """Télécharge la mise à jour"""
        try:
            print(f"⬇️  Téléchargement de la mise à jour...")
            response = requests.get(download_url, stream=True)
            total_size = int(response.headers.get('content-length', 0))

            with open(save_path, 'wb') as f:
                downloaded = 0
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        # Afficher progression
                        percent = (downloaded / total_size) * 100 if total_size > 0 else 0
                        print(f"\r   Progression: {percent:.1f}%", end='')

            print(f"\n✅ Téléchargement terminé: {save_path}")
            return save_path

        except Exception as e:
            print(f"❌ Erreur lors du téléchargement: {str(e)}")
            return None

    def install_update(self, zip_path, install_dir="."):
        """Extrait et installe la mise à jour"""
        try:
            print(f"📂 Installation de la mise à jour...")

            # Créer un backup
            backup_dir = "backup_old_version"
            if os.path.exists(install_dir):
                print(f"💾 Création d'un backup dans '{backup_dir}'...")
                if os.path.exists(backup_dir):
                    shutil.rmtree(backup_dir)
                shutil.copytree(install_dir, backup_dir, dirs_exist_ok=True)

            # Extraire le zip
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall("temp_update")

            # Déplacer les fichiers
            temp_contents = os.listdir("temp_update")
            if len(temp_contents) == 1:
                # Si un seul dossier, on prend son contenu
                source_dir = os.path.join("temp_update", temp_contents[0])
            else:
                source_dir = "temp_update"

            # Copier les nouveaux fichiers
            for item in os.listdir(source_dir):
                s = os.path.join(source_dir, item)
                d = os.path.join(install_dir, item)
                if os.path.isdir(s):
                    if os.path.exists(d):
                        shutil.rmtree(d)
                    shutil.copytree(s, d)
                else:
                    shutil.copy2(s, d)

            # Nettoyage
            shutil.rmtree("temp_update")
            os.remove(zip_path)

            print("✅ Installation terminée!")
            print(f"📌 Un backup a été créé dans '{backup_dir}'")
            return True

        except Exception as e:
            print(f"❌ Erreur lors de l'installation: {str(e)}")
            return False

    def run(self):
        """Exécute le processus complet de mise à jour"""
        print("=" * 50)
        print(f"  Système de Mise à Jour - {self.owner}/{self.repo}")
        print("=" * 50)

        # Vérifier la mise à jour
        update_info = self.check_update()

        if not update_info.get('available'):
            return

        # Afficher les notes
        print(f"\n📝 Notes de version:")
        print(update_info.get('notes', 'N/A'))

        # Demander confirmation
        choice = input(f"\n❓ Voulez-vous installer la version {update_info['version']}? (o/n): ")

        if choice.lower() == 'o':
            # Télécharger
            zip_file = self.download_update(update_info['download_url'])

            if zip_file:
                # Installer
                if self.install_update(zip_file):
                    print("\n🎉 Mise à jour réussie!")
                    print("🔄 Veuillez redémarrer l'application")
        else:
            print("❌ Mise à jour annulée")


# ============================================
# EXEMPLE D'UTILISATION
# ============================================


# Configuration
GITHUB_OWNER = "Thorin-56.fr"  # Exemple: propriétaire du repo
GITHUB_REPO = "farmland"  # Exemple: nom du repo
CURRENT_VERSION = "0.1"  # Version actuelle de votre app

# Créer l'updater
updater = GitHubUpdater(GITHUB_OWNER, GITHUB_REPO, CURRENT_VERSION)

# Lancer la vérification et mise à jour
updater.run()


if __name__ == '__main__':

    async def main():
        while True:
            win32gui.SetForegroundWindow(hwnd)
            await recolt("farm")
            await recolt("animals")
            await recolt("tree")
            await recolt("sell")
            await asyncio.sleep(60*2)

    asyncio.run(main())