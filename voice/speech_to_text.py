import speech_recognition as sr
import audioop
import os
import time
from colorama import Style,Fore,init
from googletrans import Translator

init(autoreset=True, strip=True, convert=False)

_status_callback = None
_level_callback = None


def set_voice_callbacks(status_callback=None, level_callback=None):
    global _status_callback, _level_callback
    _status_callback = status_callback
    _level_callback = level_callback


def report_status(phase, message=None, level=None):
    if _status_callback:
        _status_callback(phase=phase, message=message, mic_level=level)


def report_level(level):
    if _level_callback:
        _level_callback(level)

########################################################################################################################

def translate_hi_to_en(text):
    # english_text=translate(text,"EN-IN")
    try:
        english_text=Translator().translate(text,dest='en')
        return english_text.text
    except Exception as error:
        print(Fore.YELLOW + f"Translation failed, using original text: {error}")
        return text

def on_takecommand():
    r=sr.Recognizer()
    r.dynamic_energy_threshold=True
    r.energy_threshold = 400
    r.dynamic_energy_adjustment_damping=0.0012
    r.dynamic_energy_ratio=1.0
    r.pause_threshold=0.4
    r.operation_timeout=10
    r.pause_threshold=0.4
    r.non_speaking_duration=0.4
    try:
        with sr.Microphone() as source:
            print(Fore.LIGHTBLUE_EX + "Microphone opened", flush=True)
            report_status("listening", "Listening...", 8)
            r.adjust_for_ambient_noise(source, duration=0.3)
            while True:
                print(Fore.LIGHTBLUE_EX + "Listning.......", end="", flush=True)
                report_status("listening", "Listening...", 18)
                try:
                    audio=capture_audio(r, source, timeout=5, phrase_time_limit=8)
                    level = min(100, max(10, int(audioop_rms_percent(audio))))
                    report_level(level)
                    report_status("recognizing", "Recognizing...", level)
                    print("\r"+Fore.LIGHTGREEN_EX+"Recognising........" ,end="", flush=True)
                    query=r.recognize_google(audio).lower()
                    if query:
                        query=translate_hi_to_en(query)
                        report_status("heard", f"Heard: {query}", level)
                        print("\r"+Fore.GREEN+f"Query :{query}")
                        return query
                    else:
                        report_status("listening", "Listening...", 8)
                        return ""
                except sr.WaitTimeoutError:
                    report_status("listening", "Listening...", 4)
                    report_level(4)
                    return ""
                except sr.UnknownValueError:
                    report_status("listening", "Listening...", 8)
                    report_level(8)
                    return ""
                except sr.RequestError as error:
                    report_status("error", f"Recognition error: {error}", 0)
                    print(Fore.RED + f"Speech recognition request failed: {error}")
                    return ""
                finally:
                    print("\r",end="",flush=True)
    except OSError as error:
        report_status("error", f"Microphone error: {error}", 0)
        print(Fore.RED + f"Microphone error: {error}", flush=True)
        return ""


# Public name used by the application entry point.
def listen():
    return on_takecommand()


def capture_audio(recognizer, source, timeout=5, phrase_time_limit=8):
    seconds_per_buffer = float(source.CHUNK) / source.SAMPLE_RATE
    pause_buffer_count = max(1, int(recognizer.pause_threshold / seconds_per_buffer))
    non_speaking_buffer_count = max(1, int(recognizer.non_speaking_duration / seconds_per_buffer))
    elapsed_time = 0
    phrase_started_at = None
    pause_count = 0
    frames = []

    while True:
        elapsed_time += seconds_per_buffer
        if timeout and elapsed_time > timeout:
            raise sr.WaitTimeoutError("listening timed out while waiting for phrase to start")

        buffer = source.stream.read(source.CHUNK)
        energy = audioop.rms(buffer, source.SAMPLE_WIDTH)
        report_level(rms_to_percent(energy))

        if energy > recognizer.energy_threshold:
            phrase_started_at = time.time()
            frames.append(buffer)
            break

    while True:
        buffer = source.stream.read(source.CHUNK)
        frames.append(buffer)

        energy = audioop.rms(buffer, source.SAMPLE_WIDTH)
        report_level(rms_to_percent(energy))

        if energy > recognizer.energy_threshold:
            pause_count = 0
        else:
            pause_count += 1

        if pause_count > pause_buffer_count:
            break

        if phrase_time_limit and phrase_started_at and time.time() - phrase_started_at > phrase_time_limit:
            break

    for _ in range(non_speaking_buffer_count):
        if frames:
            frames.pop()

    frame_data = b"".join(frames)
    return sr.AudioData(frame_data, source.SAMPLE_RATE, source.SAMPLE_WIDTH)


def rms_to_percent(rms):
    return min(100, max(0, int((rms / 5000) * 100)))


def audioop_rms_percent(audio):
    try:
        raw = audio.get_raw_data()
        rms = audioop.rms(raw, audio.sample_width)
        # Human speech on 16-bit mic input usually sits well below 32767.
        return rms_to_percent(rms)
    except Exception:
        return 18
