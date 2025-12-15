import tempfile
import os
import time
import sys

try:
    from gtts import gTTS
except Exception as e:
    print('gTTS not installed:', e)
    sys.exit(1)

# Try to import playsound
ps = None
try:
    from playsound import playsound as ps
    print('playsound available')
except Exception:
    ps = None
    print('playsound not available, will fallback to os.startfile')

text = 'Đây là thử nghiệm phát âm thanh.'
fd, tmpname = tempfile.mkstemp(suffix='.mp3')
os.close(fd)
try:
    tts = gTTS(text=text, lang='vi', slow=False)
    tts.save(tmpname)
    print('Saved temp tts file:', tmpname)
    if ps:
        try:
            print('Playing with playsound (blocking)')
            ps(tmpname)
            print('playsound finished')
        except Exception as e:
            print('playsound error:', e)
    else:
        if sys.platform.startswith('win'):
            print('Opening with os.startfile, waiting 3 seconds before cleanup')
            os.startfile(tmpname)
            time.sleep(3)
        else:
            print('Opening with webbrowser, waiting 3 seconds')
            import webbrowser
            webbrowser.open(tmpname)
            time.sleep(3)
finally:
    try:
        if os.path.exists(tmpname):
            os.remove(tmpname)
            print('Removed temp file')
    except Exception as e:
        print('Could not remove temp file:', e)

