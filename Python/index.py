# Ở bước này, các bạn import các thư viện cần thiết cho quá trình tạo nên con trợ lý ảo nhá. Các bạn nào chạy mà bị lỗi thì lên Google search cách tải thư viện cho python nha.
import datetime
import os
import re
import sys
import threading
import time
import webbrowser
from time import strftime

import pyttsx3
import speech_recognition as sr
import wikipedia
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from webdriver_manager.chrome import ChromeDriverManager

# Initialize offline TTS engine (pyttsx3). On Windows it uses SAPI5. Note: Vietnamese voice may not be installed on the system.
_tts_engine = pyttsx3.init()
try:
    _tts_engine.setProperty('rate', 160)
except Exception:
    pass

# Event to indicate the assistant is currently playing audio so we don't listen to ourselves
SPEAKING = threading.Event()

# Safe playsound import with non-blocking fallback
try:
    from playsound import playsound as _ps
    def playsound(path, block=True):
        if block:
            _ps(path)
        else:
            threading.Thread(target=_ps, args=(path,), daemon=True).start()
except Exception:
    def playsound(path, block=True):
        # Fallback: open with default app on Windows (non-blocking). For other OS, raise.
        if sys.platform.startswith("win"):
            if block:
                os.startfile(path)
            else:
                threading.Thread(target=os.startfile, args=(path,), daemon=True).start()
        else:
            raise RuntimeError("playsound not available and no fallback implemented for this platform")

# Khúc này là khai báo các biến cho quá trình làm con Alex
wikipedia.set_lang('vi')
language = 'vi'
path = ChromeDriverManager().install()


# Text - to - speech: Chuyển đổi văn bản thành giọng nói (offline using pyttsx3)
def speak(text):
    """Speak text using pyttsx3 (blocking). This avoids creating temp audio files and races."""
    print("Bot: {}".format(text))
    try:
        SPEAKING.set()
        _tts_engine.say(text)
        _tts_engine.runAndWait()
    finally:
        try:
            SPEAKING.clear()
        except Exception:
            pass


# Speech - to - text: Chuyển đổi giọng nói bạn yêu cầu vào thành văn bản hiện ra khi máy trả lại kết quả đã nghe
def get_audio():
    print("\nBot: \tĐang nghe \t --__-- \n")
    # If the assistant is currently speaking, wait until it's finished to avoid recording its own output
    wait_count = 0
    while SPEAKING.is_set():
        time.sleep(0.05)
        wait_count += 1
        # Safety: after a certain time, stop waiting to avoid infinite block
        if wait_count > 200:  # ~10 seconds
            break
    r = sr.Recognizer()
    try:
        with sr.Microphone() as source:
            # Calibrate to ambient noise for a short moment to avoid long blocking waits
            try:
                r.adjust_for_ambient_noise(source, duration=0.5)
            except Exception:
                # If calibration fails, continue without it
                pass
            print("Tôi: ", end='')
            try:
                # Use timeout so listen() raises a WaitTimeoutError if no speech starts
                audio = r.listen(source, timeout=3, phrase_time_limit=8)
                try:
                    text = r.recognize_google(audio, language="vi-VN")
                    print(text)
                    return text.lower()
                except sr.UnknownValueError:
                    print("...")
                    return 0
                except sr.RequestError:
                    speak("Không thể kết nối dịch vụ nhận dạng giọng nói.")
                    return 0
            except sr.WaitTimeoutError:
                # No speech detected within timeout window
                print("(Không nghe thấy tiếng nói)")
                return 0
            except KeyboardInterrupt:
                # If user interrupts (Ctrl+C), handle gracefully and return control
                print("\nNgắt bởi người dùng.")
                return 0
            except Exception as e:
                # Catch lower-level audio errors (PyAudio stream read errors, etc.) and fall back
                print(f"Lỗi audio: {e}")
                return 0
    except OSError:
        # Fallback to manual text input when microphone is unavailable
        print("Microphone không khả dụng, vui lòng nhập văn bản:")
        text = input("Bạn: ")
        return text.lower() if text else 0


def stop():
    speak("Hẹn gặp lại bạn sau!")
    time.sleep(2)


def get_text():
    for i in range(3):
        text = get_audio()
        if text:
            return text.lower()
        elif i < 2:
            speak("Máy không nghe rõ. Bạn nói lại được không!")
            time.sleep(3)
    time.sleep(2)
    stop()
    return 0


def hello(name):
    day_time = int(strftime('%H'))
    if day_time < 12:
        speak("Chào buổi sáng bạn {}. Chúc bạn một ngày tốt lành.".format(name))
    elif 12 <= day_time < 18:
        speak("Chào buổi chiều bạn {}. Bạn đã dự định gì cho chiều nay chưa.".format(name))
    else:
        speak("Chào buổi tối bạn {}. Bạn đã ăn tối chưa nhỉ.".format(name))
    time.sleep(5)


def get_time(text):
    now = datetime.datetime.now()
    if "giờ" in text:
        speak('Bây giờ là %d giờ %d phút %d giây' % (now.hour, now.minute, now.second))
    elif "ngày" in text:
        speak("Hôm nay là ngày %d tháng %d năm %d" %
              (now.day, now.month, now.year))
    else:
        speak("Bot chưa hiểu ý của bạn. Bạn nói lại được không?")
    time.sleep(4)


def open_application(text):
    if "google" in text:
        speak("Mở Google Chrome")
        time.sleep(2)
        os.startfile(r'C:\Program Files\Google\Chrome\Application\chrome.exe')
    elif "word" in text:
        speak("Mở Microsoft Word")
        time.sleep(2)
        os.startfile(r'C:\Program Files\Microsoft Office\Office15\WINWORD.EXE')
    elif "excel" in text:
        speak("Mở Microsoft Excel")
        time.sleep(2)
        os.startfile(r'C:\Program Files\Microsoft Office\Office15\EXCEL.EXE')
    else:
        speak("Ứng dụng chưa được cài đặt. Bạn hãy thử lại!")
        time.sleep(3)


def open_website(text):
    reg_ex = re.search('mở (.+)', text)
    if reg_ex:
        domain = reg_ex.group(1).strip()
        url = 'https://www.' + domain
        webbrowser.open(url)
        speak("Trang web bạn yêu cầu đã được mở.")
        time.sleep(3)
        return True
    else:
        return False


def open_google_and_search(text):
    if "kiếm" not in text:
        speak("Xin lỗi, tôi không thấy từ khóa tìm kiếm.")
        return
    search_for = text.split("kiếm", 1)[1].strip()
    if not search_for:
        speak("Bạn muốn tìm gì?")
        return
    speak('Okay!')
    service = Service(path)
    driver = webdriver.Chrome(service=service)
    try:
        driver.get("https://www.google.com")
        que = driver.find_element(By.NAME, 'q')
        que.send_keys(str(search_for))
        que.send_keys(Keys.RETURN)
        time.sleep(3)
        # Try to read a short wikipedia summary about the query
        try:
            summary = wikipedia.summary(search_for, sentences=2)
            speak(summary.split(".")[0])
            time.sleep(2)
            # offer more
            more = get_text()
            if more and "có" in more:
                # speak full summary a bit more
                speak(summary)
        except Exception:
            # If no wiki summary, leave the google results open
            pass
    finally:
        try:
            driver.quit()
        except Exception:
            pass


def introduce():
    speak("Xin chào bạn. Rất hân hạnh được phục vụ bạn. Tôi là Alex... (phiên bản rút gọn).")


def send_email(text):
    speak("Gửi email tới ai?")
    time.sleep(2)
    recipient = get_text()
    if recipient:
        speak("Nội dung email là gì?")
        time.sleep(2)
        content = get_text()
        if content:
            speak("Email đã được gửi thành công")
            time.sleep(2)
        else:
            speak("Hủy gửi email")
            time.sleep(2)


def current_weather():
    speak("Chức năng dự báo thời tiết chưa được cài đặt")
    time.sleep(2)


def play_song():
    speak("Bạn muốn nghe nhạc gì?")
    time.sleep(2)
    song = get_text()
    if song:
        speak("Đang tìm kiếm bài hát {}".format(song))
        time.sleep(2)


def change_wallpaper():
    speak("Chức năng thay đổi hình nền chưa được cài đặt")
    time.sleep(2)


def read_news():
    speak("Chức năng đọc báo chưa được cài đặt")
    time.sleep(2)


def tell_me_about():
    speak("Bạn muốn biết về gì?")
    time.sleep(2)
    topic = get_text()
    if topic:
        speak("Đang tìm kiếm thông tin về {}".format(topic))
        time.sleep(2)


def help_me():
    speak("""Bot có thể giúp bạn thực hiện các câu lệnh sau đây:
    1. Chào hỏi
    2. Hiển thị giờ
    3. Mở website, application
    4. Tìm kiếm trên Google
    5. Gửi email
    6. Dự báo thời tiết
    7. Mở video nhạc
    8. Thay đổi hình nền máy tính
    9. Đọc báo hôm nay
    10. Kể bạn biết về thế giới """)
    time.sleep(5)


def assistant():
    speak("Xin chào, bạn tên là gì nhỉ?")
    time.sleep(2)
    name = get_text()
    if name:
        speak("Chào bạn {}".format(name))
        speak("Bạn cần Bot Alex có thể giúp gì ạ?")
        time.sleep(3)
        while True:
            text = get_text()
            if not text:
                break
            elif "dừng" in text or "tạm biệt" in text or "chào robot" in text or "ngủ thôi" in text:
                stop()
                break
            elif "có thể làm gì" in text:
                help_me()
            elif "chào" in text:
                hello(name)
            elif "giờ" in text or "ngày" in text:
                get_time(text)
            elif 'mở google và tìm kiếm' in text:
                open_google_and_search(text)
            elif "mở " in text:
                open_website(text)
            elif "ứng dụng" in text:
                speak("Tên ứng dụng bạn muốn mở là ")
                time.sleep(3)
                text1 = get_text()
                open_application(text1)
            elif "email" in text or "mail" in text or "gmail" in text:
                send_email(text)
            elif "thời tiết" in text:
                current_weather()
            elif "chơi nhạc" in text:
                play_song()
            elif "hình nền" in text:
                change_wallpaper()
            elif "đọc báo" in text:
                read_news()
            elif "định nghĩa" in text:
                tell_me_about()
            elif "giới thiệu" in text:
                introduce()
            else:
                speak("Bạn cần Bot giúp gì ạ?")
                time.sleep(2)


if __name__ == '__main__':
    assistant()