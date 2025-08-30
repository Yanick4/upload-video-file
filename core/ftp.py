import os
from ftplib import FTP
from config import config
from tqdm import tqdm

def upload_file(ftp, local_path, remote_path):
    """Télécharge un fichier local vers un chemin distant sur le serveur FTP."""
    with open(local_path, 'rb') as f:
        # Créer une barre de progression avec tqdm
        with tqdm(total=len(f.read()), unit='B', unit_scale=True, desc=local_path) as pbar:
            f.seek(0)  # Revenir au début du fichier après avoir lu sa taille
            # Transférer le fichier avec une fonction de callback pour la barre de progression
            ftp.storbinary(f"STOR {remote_path}", f, 1024, callback=lambda block: pbar.update(len(block)))
        os.remove(local_path)

    #with open(local_path, 'rb') as f:
    #    ftp.storbinary(f"STOR {remote_path}", f)

def create_remote_dir(ftp, remote_dir):
    """Crée un répertoire distant si ce n'est pas déjà fait."""
    try:
        ftp.mkd(remote_dir)
    except Exception as e:
        # Si le répertoire existe déjà, on ignore l'erreur.
        pass

def upload_directory(ftp, local_dir, remote_dir):
    """Télécharge un répertoire local en profondeur vers le serveur FTP."""
    # Change de répertoire sur le serveur distant
    print(f"-----------{local_dir}:-{remote_dir}")
    create_remote_dir(ftp, remote_dir)
    #ftp.cwd(remote_dir)

    for item in os.listdir(local_dir):
        local_item = os.path.join(local_dir, item)
        remote_item = os.path.join(remote_dir, item).replace("\\", "/")
        print(f"-----------local_item:{local_item}")
        print(f"-----------remote_item:{remote_item}")

        if os.path.isdir(local_item):
            # Si c'est un sous-répertoire, appel récursif
            upload_directory(ftp, local_item, remote_item)
        else:
            # Si c'est un fichier, on le télécharge
            upload_file(ftp, local_item, remote_item)

def connect_ftp():
    """Create and return a new FTP connection"""
    ftp = FTP(config['ftp_server'])
    ftp.login(user=config['ftp_username'], passwd=config['ftp_password'])
    return ftp
