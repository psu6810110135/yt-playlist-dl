import yt_dlp
import asyncio
import re
import threading
import os
import time
from concurrent.futures import ThreadPoolExecutor

# Shared list and lock for results (removed - using return values instead)

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

def download_song(video_url, playlist_name):
    try:
        print(f"🧵 Thread {threading.current_thread().name}: Starting download for {video_url}")
        
        options = {
            'format': 'bestaudio/best',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
            'outtmpl': f'{playlist_name}/%(title)s.%(ext)s',
            'quiet': True,
            'no_warnings': True,
        }
        with yt_dlp.YoutubeDL(options) as ydl:
            ydl.download([video_url])
        
        return {'status': 'Success', 'message': 'Download completed successfully'}
        
    except Exception as e:
        error_msg = f"Download failed: {str(e)}"
        return {'status': 'Fail', 'message': error_msg}

async def main():
    playlist_url = input("Enter playlist URL: ")
    
    print("🔄 Using asyncio.to_thread() for playlist metadata extraction...")
    
    # Phase 1: Get playlist metadata
    playlist_info = await asyncio.to_thread(get_playlist_info, playlist_url)
    
    # Get playlist name and create folder
    playlist_name = playlist_info.get('title', 'Playlist').replace('/', '_').replace('\\', '_')
    os.makedirs(playlist_name, exist_ok=True)
    print(f"📁 Created folder: {playlist_name}")
    
    # Get songs from playlist
    songs = []
    for entry in playlist_info.get('entries', []):
        song_info = {
            'title': entry.get('title', 'Unknown'),
            'url': f"https://www.youtube.com/watch?v={entry.get('id', '')}",
            'duration': entry.get('duration', 0)
        }
        songs.append(song_info)
    
    print(f"Found {len(songs)} songs in playlist:")
    for i, song in enumerate(songs, 1):
        print(f"{i}. {song['title']} - {song['url']} ({song['duration']}s)")
    
    # Phase 2: Download songs concurrently
    print("\n🔄 Using ThreadPoolExecutor(max_workers=5) for concurrent downloads...")
    
    # Start timer for downloads
    download_start_time = time.time()
    
    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = []
        for song in songs:
            print(f"📤 Submitting download task: {song['title']}")
            future = executor.submit(download_song, song['url'], playlist_name)
            futures.append(future)
        
        print("⏳ Waiting for all download threads to complete...")
        # Convert concurrent.futures to asyncio futures and wait
        futures_async = [asyncio.wrap_future(f) for f in futures]
        results = await asyncio.gather(*futures_async)
    
    # Calculate and display download time
    download_end_time = time.time()
    total_download_time = download_end_time - download_start_time
    
    print(f"\nDownload Summary:")
    print(f"⏱️ Total download time: {total_download_time:.2f} seconds")
    success_count = sum(1 for r in results if r['status'] == 'Success')
    fail_count = len(results) - success_count
    print(f"Successful: {success_count}")
    print(f"Failed: {fail_count}")
    
    if success_count > 0:
        avg_time_per_song = total_download_time / success_count
        print(f"⏱️ Average time per song: {avg_time_per_song:.2f} seconds")
    
    if fail_count > 0:
        print("\nFailed downloads:")
        for i, result in enumerate(results):
            if result['status'] == 'Fail':
                song = songs[i]
                print(f"- {song['title']}: {result['message']}")

if __name__ == "__main__":
    asyncio.run(main())

