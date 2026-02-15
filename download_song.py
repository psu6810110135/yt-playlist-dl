import yt_dlp
import asyncio
import re

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

async def main():

    playlist_url = input("Enter playlist URL: ")
    
    playlist_info = await asyncio.to_thread(get_playlist_info, playlist_url)
    
    # Debug: ดูว่าได้ข้อมูลอะไรมา
    # print(f"Extracted type: {playlist_info.get('_type', 'unknown')}")
    # print(f"Entries count: {len(playlist_info.get('entries', []))}")
    
    # Get songs from playlist
    songs = []
    for entry in playlist_info.get('entries', []):
        song_info = {
            'title': entry.get('title', 'Unknown'),
            'url': entry.get('url', entry.get('id', '')),
            'duration': entry.get('duration', 0)
        }
        songs.append(song_info)
    
    # Print songs
    print(f"Found {len(songs)} songs in playlist:")
    for i, song in enumerate(songs, 1):
        print(f"{i}. {song['title']} - {song['url']} ({song['duration']}s)")

if __name__ == "__main__":
    asyncio.run(main())

