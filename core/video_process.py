import os
import ffmpeg
from ffmpeg_streaming import Size, Bitrate
from typing import Dict, Optional
import logging


from collections import namedtuple

class StreamSettings:
    """Class to manage stream settings for different resolutions."""
    def __init__(self, width, height, video_bitrate, audio_bitrate):
        self.size = Size(width, height)
        self.bitrate = Bitrate(video_bitrate, audio_bitrate)
        self.total_bandwidth = video_bitrate + audio_bitrate  # Total bandwidth in bits/second

    @property
    def resolution_string(self):
        """Returns the resolution as a string (e.g., '1920x1080')."""
        return f"{self.size.width}x{self.size.height}"
    


class StreamProfiles:
    """Manages different streaming profiles."""
    PROFILES = {
        '240p':  StreamSettings(426, 240, 400_000, 128_000),    # 528 Kbps total
        '360p':  StreamSettings(640, 360, 800_000, 192_000),    # 992 Kbps total
        '480p':  StreamSettings(854, 480, 1_400_000, 256_000),  # 1.656 Mbps total
        '720p':  StreamSettings(1280, 720, 2_800_000, 320_000), # 3.12 Mbps total
        '1080p': StreamSettings(1920, 1080, 5_000_000, 320_000) # 5.32 Mbps total
    }

    @classmethod
    def get_settings(cls, resolution):
        """Retrieves settings for a specific resolution."""
        return cls.PROFILES.get(resolution)    




# Définition claire des types
Size = namedtuple('Size', ['width', 'height'])
Bitrate = namedtuple('Bitrate', ['video', 'audio'])

def get_representation_settings(resolution):
    """
    Retourne les paramètres de représentation pour une résolution donnée.
    
    Args:
        resolution (str): Résolution souhaitée
    
    Returns:
        dict: Paramètres de la résolution
    """
    settings = {
        '240p': {
            'size': Size(426, 240), 
            'bitrate': Bitrate(video=400 * 1024, audio=128 * 1024),
            'resolution': '426x240'
        },
        '360p': {
            'size': Size(640, 360), 
            'bitrate': Bitrate(video=800 * 1024, audio=192 * 1024),
            'resolution': '640x360'
        },
        '480p': {
            'size': Size(854, 480), 
            'bitrate': Bitrate(video=1400 * 1024, audio=256 * 1024),
            'resolution': '854x480'
        },
        '720p': {
            'size': Size(1280, 720), 
            'bitrate': Bitrate(video=2800 * 1024, audio=320 * 1024),
            'resolution': '1280x720'
        },
        '1080p': {
            'size': Size(1920, 1080), 
            'bitrate': Bitrate(video=5000 * 1024, audio=320 * 1024),
            'resolution': '1920x1080'
        }
    }
    return settings.get(resolution)

def create_hls_playlist(input_path, output_folder, resolution):
    """
    Crée une playlist HLS pour une résolution donnée.
    
    Args:
        input_path (str): Chemin du fichier vidéo source
        output_folder (str): Dossier de sortie principal
        resolution (str): Résolution cible
    
    Returns:
        str: Chemin du fichier playlist créé
    """
    # Vérifier les paramètres de la résolution
    settings = get_representation_settings(resolution)
    if not settings:
        logging.error(f"Résolution non valide : {resolution}")
        return None

    # Préparer les chemins de sortie
    res_folder = os.path.join(output_folder, resolution)
    os.makedirs(res_folder, exist_ok=True)
    
    # Chemins de sortie
    output_playlist = os.path.join(res_folder, 'playlist.m3u8')
    
    try:
        # Commande ffmpeg pour segmentation
        stream = (
            ffmpeg
            .input(input_path)
            .output(
                os.path.join(res_folder, 'segment_%03d.ts'),
                vcodec='libx264',
                acodec='aac',
                video_bitrate=f'{settings["bitrate"].video // 1024}k',
                audio_bitrate=f'{settings["bitrate"].audio // 1024}k',
                s=settings['resolution'],  # Ajout de la résolution
                map=0,
                f='segment',
                segment_time=10,
                segment_list=output_playlist,
                segment_list_type='m3u8'
            )
        )
        
        # Exécution de la commande ffmpeg
        ffmpeg_args = stream.compile()
        logging.info(f"Commande FFmpeg : {' '.join(ffmpeg_args)}")
        
        # Exécution de la commande
        stream.run(capture_stdout=True, capture_stderr=True)
        
        # Vérification de la création du fichier
        if not os.path.exists(output_playlist):
            raise RuntimeError("La création de la playlist a échoué")
        
        logging.info(f"Playlist HLS créée avec succès : {output_playlist}")
        return output_playlist
    
    except ffmpeg.Error as e:
        logging.error(f"Erreur FFmpeg pour {resolution}: {e.stderr.decode()}")
        return None
    except Exception as e:
        logging.error(f"Erreur de segmentation pour {resolution}: {e}")
        return None



def create_master_playlist(output_folder, available_resolutions):
    """
    Crée un fichier master.m3u8 avec des références directes vers playlist.m3u8.
    
    Args:
        output_folder (str): Dossier de sortie principal
        available_resolutions (dict): Résolutions disponibles
    
    Returns:
        str: Chemin du fichier master playlist
    """
    master_playlist_path = os.path.join(output_folder, 'master.m3u8')
    
    try:
        with open(master_playlist_path, 'w') as master_playlist:
            master_playlist.write("#EXTM3U\n")
            master_playlist.write("#EXT-X-VERSION:3\n\n")
            
            for resolution, settings in available_resolutions.items():
                master_playlist.write(
                    f'#EXT-X-STREAM-INF:'
                    f'BANDWIDTH={settings["bandwidth"]},'
                    f'RESOLUTION={settings["resolution"]},'
                    f'CODECS="avc1.640015,mp4a.40.2"\n'
                    f'{resolution}/playlist.m3u8\n\n'
                )
        
        logging.info(f"Master playlist créé : {master_playlist_path}")
        return master_playlist_path
    
    except Exception as e:
        logging.error(f"Erreur de création du master playlist : {e}")
        raise




class VideoProcessor:
    def __init__(self, input_path: str, output_folder: str):
        """
        Initialize VideoProcessor with input video path and output folder
        
        Args:
            input_path (str): Path to the input video file
            output_folder (str): Destination folder for processed files
        """
        self.input_path = input_path
        self.caption_folder=os.path.join(output_folder,"captions")
        self.output_folder = output_folder
        os.makedirs(self.output_folder, exist_ok=True)
        
        # Configure logging
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s: %(message)s')
        self.logger = logging.getLogger(__name__)

    def rename_to_original(self) -> Optional[str]:
        try:
            directory = os.path.dirname(self.input_path)
            filename = os.path.basename(self.input_path)
            _, extension = os.path.splitext(filename)
            new_filename = f"original{extension}"
            new_path = os.path.join(directory, new_filename)

            if os.path.isfile(self.input_path) and not os.path.isfile(new_path):
                os.rename(self.input_path, new_path)
                self.input_path = new_path  # Met à jour le chemin
                self.logger.info(f"Vidéo renommée avec succès : {new_path}")
                return new_path

            self.logger.warning("Le fichier original existe déjà ou le fichier source est introuvable.")
            return new_path
        except Exception as e:
            self.logger.error(f"Erreur lors du renommage de la vidéo : {e}")
            return None

    def compress_and_segment(self,resolutions):
        """
        Compresse et segmente une vidéo en plusieurs résolutions et crée une master playlist.
        
        Args:
            input_path (str): Chemin vers la vidéo source.
            output_folder (str): Chemin vers le dossier de sortie.
            resolutions (list): Liste des résolutions à générer.
        
        Returns:
            dict: Dictionnaire contenant les chemins vers les playlists générées.
        """
        if not os.path.exists(self.input_path):
            raise FileNotFoundError(f"Le fichier vidéo d'entrée n'existe pas : {self.input_path}")

        os.makedirs(self.output_folder, exist_ok=True)
        logging.info(f"Création du dossier de sortie : {self.output_folder}")

        try:
            playlists = {}
            available_resolutions = {}
            
            # Générer les playlists pour chaque résolution
            for resolution in resolutions:
                stream_settings = StreamProfiles.get_settings(resolution)
                
                if not stream_settings:
                    logging.warning(f"Résolution non supportée ignorée : {resolution}")
                    continue
                
                try:
                    playlist_path = create_hls_playlist(self.input_path, self.output_folder, resolution)
                    
                    if playlist_path:
                        playlists[resolution] = playlist_path
                        available_resolutions[resolution] = {
                            'bandwidth': stream_settings.total_bandwidth,
                            'resolution': stream_settings.resolution_string,
                            
                        }
                
                except Exception as e:
                    logging.error(f"Erreur lors de la création de la playlist {resolution} : {e}")
            
            # Si aucune résolution n'est générée, lever une exception
            if not available_resolutions:
                raise ValueError("Aucune résolution n'a pu être générée.")
            
            # Créer la master playlist
            master_playlist_path = create_master_playlist(self.output_folder, available_resolutions)
            playlists['master'] = master_playlist_path
            
            logging.info("Processus terminé avec succès.")
            return playlists
        
        except Exception as e:
            logging.error(f"Erreur lors du traitement de la vidéo : {e}")
            raise


    def process_video(self, 
                    rename_original: bool,
                    compress_segment: bool, 
                    resolutions=['240p', '480p', '720p', '1080p'],
                ) -> Dict[str, str]:
        """Process the video with all selected operations"""
        results = {}
        
        try:
            if rename_original:
                results['original'] = self.rename_to_original()
            
            if compress_segment:
                results['playlists'] = self.compress_and_segment(resolutions)
            
           
            return results
            
        except Exception as e:
            self.logger.error(f"Error processing video: {e}")
            raise
