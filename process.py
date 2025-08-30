import os 
from core.video_process import VideoProcessor
from core.ftp import connect_ftp,upload_directory
import shutil
import uuid

def upload(s3_key: str, temp_dir: str):
    """Process a video and upload results"""
    ftp = None
    try:
        ftp = connect_ftp()
        upload_directory(ftp, temp_dir, s3_key)
        print(f"Successfully processed and uploaded {s3_key}")

    except Exception as e:
        raise e
    finally:
        if ftp:
            try:
                ftp.quit()
            except Exception as e:
                print(f"Error closing FTP connection: {e}")
        
        # Nettoyer le dossier temporaire
        if temp_dir and os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)

def process_and_upload(s3_key: str, base_temp_dir: str, filename: str,local_file:str):
    """Process a video and upload results"""
    temp_dir = None
    try:
        
        temp_dir = os.path.join(base_temp_dir, filename)
        os.makedirs(temp_dir,exist_ok=True)
        shutil.copy(s3_key,local_file)

        resolutions = ['240p','360p','480p','720p','1080p']
        processor = VideoProcessor(local_file, temp_dir)
        results = processor.process_video(
            rename_original=True,
            compress_segment=True,
            resolutions=resolutions,
        )
        upload(s3_key=filename, temp_dir=temp_dir)

    except Exception as e:
        raise e


def upload_file_to_bunny(base_dir,final_temp_path,ep_number,bunny_path):
    base=os.path.join(bunny_path,str(uuid.uuid4()).replace("-","")+f"_EP_{ep_number}")
    local_file=os.path.join(base_dir,base,os.path.basename(final_temp_path))
    process_and_upload(final_temp_path,base_dir,base,local_file)
    link_file=os.path.join('link.md')
    with open(link_file,"a+", encoding="utf-8") as f:
        f.write(f"Episode {ep_number}\n")
        f.write(f"https://cinaftvmovies.b-cdn.net/{base}/master.m3u8")
        f.write(f"https://cinaftvmovies.b-cdn.net/{base}/original.mp4")
        f.write("\n")

