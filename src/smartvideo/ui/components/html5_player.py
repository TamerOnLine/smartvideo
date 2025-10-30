import streamlit as st
import streamlit.components.v1 as components

def html5_player(url: str, height: int = 360):
    """
    Embed an HTML5 video player with keyboard shortcuts.

    Keyboard shortcuts:
    - J/L: Skip ±10 seconds
    - K: Play/Pause
    - ←/→: Skip ±5 seconds
    - [/]: Adjust playback speed ±0.25x

    Args:
        url (str): URL of the video file.
        height (int, optional): Height of the player in pixels. Defaults to 360.
    """
    html = f"""
    <video id=\"vid\" src=\"{url}\" controls style=\"width:100%; height:auto; outline:none;\"></video>
    <script>
    const v = document.getElementById('vid');
    document.addEventListener('keydown', (e) => {{
        if (!v) return;
        switch(e.key) {{
            case 'k': v.paused ? v.play() : v.pause(); break;
            case 'j': v.currentTime = Math.max(0, v.currentTime - 10); break;
            case 'l': v.currentTime = v.currentTime + 10; break;
            case 'ArrowLeft': v.currentTime = Math.max(0, v.currentTime - 5); break;
            case 'ArrowRight': v.currentTime = v.currentTime + 5; break;
            case '[': v.playbackRate = Math.max(0.25, v.playbackRate - 0.25); break;
            case ']': v.playbackRate = v.playbackRate + 0.25; break;
        }}
    }});
    </script>
    """
    components.html(html, height=height + 40, scrolling=False)