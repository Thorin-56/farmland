import requests
import os
import zipfile
import shutil

class GitHubUpdater:
    def __init__(self, owner, repo, current_version):
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

    @staticmethod
    def download_update(download_url, save_path="update.zip"):
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

    @staticmethod
    def install_update(zip_path, install_dir="."):
        """Extrait et installe la mise à jour"""
        try:
            print(f"📂 Installation de la mise à jour...")

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

        # Télécharger
        zip_file = self.download_update(update_info['download_url'])

        if zip_file:
            # Installer
            if self.install_update(zip_file):
                print("\n🎉 Mise à jour réussie!")