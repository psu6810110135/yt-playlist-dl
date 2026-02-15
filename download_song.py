import yt_dlp
import asyncio
import re
import threading
from concurrent.futures import ThreadPoolExecutor

# Shared list and lock for results
results = []
lock = threading.Lock()

def get_playlist_info(playlist_url):
    # แปลง URL ให้เป็น playlist URL 
    if 'list=' in playlist_url:
        playlist_id = re.search(r'list=([^&]+)', playlist_url).group(1)
        playlist_url = f'https://www.youtube.com/playlist?list={playlist_id}'
    options = {
        'extract_flat': True, 
        'dump_single_json': True,
        'noplaylist': False
    }
    with yt_dlp.YoutubeDL(options) as ydl:
        playlist_info = ydl.extract_info(playlist_url, download=False)
    return playlist_info

def download_song(video_url):
    try:
        print(f"🧵 Thread {threading.current_thread().name}: Starting download for {video_url}")
        
        options = {
            'format': 'bestaudio/best',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
            'outtmpl': '%(title)s.%(ext)s',
            'quiet': True,
            'no_warnings': True,
        }
        with yt_dlp.YoutubeDL(options) as ydl:
            ydl.download([video_url])
        with lock:
            results.append({
                'url': video_url,
                'status': 'Success',
                'message': 'Download completed successfully'
            })
        return {'status': 'Success', 'message': 'Download completed successfully'}
        
    except Exception as e:
        error_msg = f"Download failed: {str(e)}"
        with lock:
            results.append({
                'url': video_url,
                'status': 'Fail',
                'message': error_msg
            })
        return {'status': 'Fail', 'message': error_msg}

async def main():
    playlist_url = input("Enter playlist URL: ")
    
    print("🔄 Using asyncio.to_thread() for playlist metadata extraction...")
    
    # Phase 1: Get playlist metadata
    playlist_info = await asyncio.to_thread(get_playlist_info, playlist_url)
    # Get songs from playlist
    songs = []
    for entry in playlist_info.get('entries', []):
        song_info = {
            'title': entry.get('title', 'Unknown'),
            'url': entry.get('url', entry.get('id', '')),
            'duration': entry.get('duration', 0)
        }
        songs.append(song_info)
    
    print(f"Found {len(songs)} songs in playlist:")
    for i, song in enumerate(songs, 1):
        print(f"{i}. {song['title']} - {song['url']} ({song['duration']}s)")
    
    # Phase 2: Download songs concurrently
    print("\n🔄 Using ThreadPoolExecutor(max_workers=5) for concurrent downloads...")
    
    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = []
        for song in songs:
            print(f"📤 Submitting download task: {song['title']}")
            future = executor.submit(download_song, song['url'])
            futures.append(future)
        
        print("⏳ Waiting for all download threads to complete...")
        for future in futures:
            await asyncio.to_thread(lambda f: f.result(), future)
    
    print(f"\nDownload Summary:")
    success_count = sum(1 for r in results if r['status'] == 'Success')
    fail_count = len(results) - success_count
    print(f"Successful: {success_count}")
    print(f"Failed: {fail_count}")
    
    if fail_count > 0:
        print("\nFailed downloads:")
        for result in results:
            if result['status'] == 'Fail':
                print(f"- {result['url']}: {result['message']}")

if __name__ == "__main__":
    asyncio.run(main())

