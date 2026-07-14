import pyttsx3
import threading

_engine = None
_engine_lock = threading.Lock()

def get_engine():
    global _engine
    if _engine is None:
        _engine = pyttsx3.init()
        _engine.setProperty('rate',140)  # talk speed increase or decrease
    return _engine

def say(text):
    try:
        with _engine_lock:
            engine=get_engine()
            engine.say(text)
            engine.runAndWait()
    except Exception as error:
        print(f"Speech output failed: {error}", flush=True)


# Public name used by the application entry point.
def speak(text):
    say(str(text))
    

