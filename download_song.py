import yt_dlp
import asyncio
import re
import threading
import os
import time
from concurrent.futures import ThreadPoolExecutor

# ANSI color codes for better CLI appearance
class Colors:
    RESET = '\033[0m'
    BOLD = '\033[1m'
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    MAGENTA = '\033[95m'
    CYAN = '\033[96m'
    WHITE = '\033[97m'
    UNDERLINE = '\033[4m'

def print_header():
    """Print a nice header"""
    print(f"{Colors.CYAN}{Colors.BOLD}")
    print("╔══════════════════════════════════════════════════════════════╗")
    print("║                    YouTube Playlist Downloader             ║")
    print("║                      Async + Threading                      ║")
    print("╚══════════════════════════════════════════════════════════════╝")
    print(f"{Colors.RESET}")

def print_section(title):
    """Print a section header"""
    print(f"\n{Colors.YELLOW}{Colors.BOLD}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{Colors.RESET}")
    print(f"{Colors.CYAN}{Colors.BOLD}  {title}{Colors.RESET}")
    print(f"{Colors.YELLOW}{Colors.BOLD}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{Colors.RESET}")

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

def download_song(video_url, playlist_name, format_type):
    try:
        print(f"{Colors.MAGENTA}🧵 Thread {threading.current_thread().name}: Starting download for {video_url}{Colors.RESET}")
        
        if format_type == 'mp3':
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
        else:  # mp4
            options = {
                'format': 'best[ext=mp4]/best',
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
    print_header()
    
    print_section("📥 Playlist Input")
    playlist_url = input(f"{Colors.WHITE}Enter playlist URL: {Colors.RESET}")
    
    print_section("🎵 Format Selection")
    print(f"{Colors.WHITE}Select download format:{Colors.RESET}")
    print(f"{Colors.CYAN}1.{Colors.RESET} MP3 (Audio only)")
    print(f"{Colors.CYAN}2.{Colors.RESET} MP4 (Video + Audio)")
    format_choice = input(f"{Colors.WHITE}Enter choice (1 or 2): {Colors.RESET}").strip()
    
    if format_choice not in ['1', '2']:
        print(f"{Colors.YELLOW}⚠️  Invalid choice. Defaulting to MP3.{Colors.RESET}")
        format_choice = '1'
    
    format_type = 'mp3' if format_choice == '1' else 'mp4'
    print(f"{Colors.GREEN}✅ Selected format: {format_type.upper()}{Colors.RESET}")
    
    print_section("🔍 Extracting Playlist Metadata")
    print(f"{Colors.BLUE}🔄 Using asyncio.to_thread() for playlist metadata extraction...{Colors.RESET}")
    
    # Phase 1: Get playlist metadata
    playlist_info = await asyncio.to_thread(get_playlist_info, playlist_url)
    
    # Get playlist name and create folder
    playlist_name = playlist_info.get('title', 'Playlist').replace('/', '_').replace('\\', '_')
    os.makedirs(playlist_name, exist_ok=True)
    print(f"{Colors.GREEN}📁 Created folder: {playlist_name}{Colors.RESET}")
    
    # Get songs from playlist
    songs = []
    for entry in playlist_info.get('entries', []):
        song_info = {
            'title': entry.get('title', 'Unknown'),
            'url': f"https://www.youtube.com/watch?v={entry.get('id', '')}",
            'duration': entry.get('duration', 0)
        }
        songs.append(song_info)
    
    print_section("📋 Playlist Contents")
    print(f"{Colors.WHITE}Found {len(songs)} songs in playlist:{Colors.RESET}")
    for i, song in enumerate(songs, 1):
        print(f"{Colors.CYAN}{i:2d}.{Colors.RESET} {Colors.MAGENTA}{song['title']}{Colors.RESET} - {Colors.BLUE}{song['url']}{Colors.RESET} ({Colors.YELLOW}{song['duration']}s{Colors.RESET})")
    
    print_section("⚡ Concurrent Downloads")
    print(f"{Colors.BLUE}🔄 Using ThreadPoolExecutor(max_workers=5) for concurrent downloads...{Colors.RESET}")
    
    # Start timer for downloads
    download_start_time = time.time()
    
    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = []
        for song in songs:
            print(f"{Colors.CYAN}📤 Submitting download task:{Colors.RESET} {Colors.MAGENTA}{song['title']}{Colors.RESET}")
            future = executor.submit(download_song, song['url'], playlist_name, format_type)
            futures.append(future)
        
        print(f"{Colors.YELLOW}⏳ Waiting for all download threads to complete...{Colors.RESET}")
        # Convert concurrent.futures to asyncio futures and wait
        futures_async = [asyncio.wrap_future(f) for f in futures]
        results = await asyncio.gather(*futures_async)
    
    # Calculate and display download time
    download_end_time = time.time()
    total_download_time = download_end_time - download_start_time
    
    print_section("📊 Download Summary")
    print(f"{Colors.GREEN}⏱️  Total download time: {total_download_time:.2f} seconds{Colors.RESET}")
    success_count = sum(1 for r in results if r['status'] == 'Success')
    fail_count = len(results) - success_count
    print(f"{Colors.GREEN}✅ Successful: {success_count}{Colors.RESET}")
    print(f"{Colors.RED}❌ Failed: {fail_count}{Colors.RESET}")
    
    if success_count > 0:
        avg_time_per_song = total_download_time / success_count
        print(f"{Colors.BLUE}⏱️  Average time per song: {avg_time_per_song:.2f} seconds{Colors.RESET}")
    
    if fail_count > 0:
        print(f"\n{Colors.RED}Failed downloads:{Colors.RESET}")
        for i, result in enumerate(results):
            if result['status'] == 'Fail':
                song = songs[i]
                print(f"{Colors.RED}  • {song['title']}: {result['message']}{Colors.RESET}")

if __name__ == "__main__":
    asyncio.run(main())

