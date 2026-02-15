import yt_dlp

def get_playlist_info(playlist_url):

    options = {
        'extract_flat': True, 
        'dump_single_json': True  
    }
    
    with yt_dlp.YoutubeDL(options) as ydl:
        playlist_info = ydl.extract_info(playlist_url, download=False)
    
    return playlist_info

def download_song():

    pass
