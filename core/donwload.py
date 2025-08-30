import os
from ftplib import FTP
import logging
from config import config
logging.basicConfig(level=logging.INFO)

def verifier_dossier_ftp(hote, utilisateur, mot_de_passe, chemin_ftp):
    """
    Vérifie si un dossier existe sur un serveur FTP.
    
    Args:
        hote (str): Adresse du serveur FTP (ex. 'ftp.humatiris.com').
        utilisateur (str): Nom d'utilisateur FTP.
        mot_de_passe (str): Mot de passe FTP.
        chemin_ftp (str): Chemin du dossier à vérifier (ex. '/uploads/hum/episode_1').
    
    Returns:
        bool: True si le dossier existe, False sinon.
    """
    try:
        # Connexion au serveur FTP
        ftp = FTP(hote)
        ftp.login(user=utilisateur, passwd=mot_de_passe)
        
        # Normaliser le chemin pour FTP (utiliser '/')
        chemin_ftp = chemin_ftp.replace('\\', '/')
        
        # Tenter de naviguer dans le dossier
        try:
            ftp.cwd(chemin_ftp)
            logging.info(f"Le dossier '{chemin_ftp}' existe sur le FTP.")
            return True
        except:
            # Si cwd échoue, vérifier via la liste des dossiers
            # Extraire le répertoire parent et le nom du dossier
            parent_dir = os.path.dirname(chemin_ftp).replace('\\', '/')
            nom_dossier = os.path.basename(chemin_ftp)
            
            if parent_dir:
                ftp.cwd(parent_dir)
            else:
                ftp.cwd('/')  # Racine du FTP si parent_dir est vide
                
            # Lister les dossiers
            dossiers = []
            ftp.retrlines('LIST', lambda x: dossiers.append(x))
            for ligne in dossiers:
                if nom_dossier in ligne and ligne.startswith('d'):
                    logging.info(f"Le dossier '{chemin_ftp}' existe sur le FTP.")
                    return True
            logging.info(f"Le dossier '{chemin_ftp}' n'existe pas sur le FTP.")
            return False
            
    except Exception as e:
        logging.info(f"Erreur lors de la connexion ou de la vérification : {e}")
        return False
        
    finally:
        # Fermer la connexion
        try:
            ftp.quit()
        except:
            pass

def verify_if_ftp_or_local_dir_exist(base, serie=True):
    logging.info(base)
    base_dir=os.path.join(config.get("root_dir"), base)
    result = {"local": False, "remote": False, 'base_dir': base_dir}
    if os.path.isdir(base_dir):
        result["local"] = True

    ftp = FTP(config['ftp_server'])
    ftp.login(user=config['ftp_username'], passwd=config['ftp_password'])
    if verifier_dossier_ftp(
        config['ftp_server'],
        config['ftp_username'],
        config['ftp_password'],base):
        result["remote"] = True

    return result
