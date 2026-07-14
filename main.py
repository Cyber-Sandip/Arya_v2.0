"""Interactive entry point for the Arya desktop assistant."""

import argparse
import sys
import traceback

from config import ASSISTANT_NAME, PROJECT_NAME, VERSION
from ai.gemini import detect_intent
from router import execute
from voice.speech_to_text import listen
from voice.text_to_speech import speak


HELP_TEXT = """Try one of these:
  - open notepad                 - search for Python tutorials
  - open youtube.com             - create folder projects/demo
  - take screenshot              - increase volume
  - pause music                  - lock pc

Say or type 'help' to see this again, 'history' for recent commands,
or 'exit' to close Arya."""

EXIT_COMMANDS = {"exit", "quit", "close", "goodbye", "stop", "stop assistant"}


class AryaAssistant:
    def __init__(self, input_mode="voice", voice_enabled=True):
        self.running = True
        self.input_mode = input_mode
        self.voice_enabled = voice_enabled
        self.history = []

        print(f"\n{'=' * 60}\n{PROJECT_NAME}  |  Version {VERSION}\n{'=' * 60}")

    def respond(self, message, speak_response=True):
        print(f"\n{ASSISTANT_NAME}: {message}")
        if self.voice_enabled and speak_response:
            speak(message)

    def startup(self):
        greeting = f"Hello. I am {ASSISTANT_NAME}. How can I help you today?"
        self.respond(greeting)
        print(HELP_TEXT)

    def shutdown(self):
        self.respond("Goodbye. Have a nice day.")
        self.running = False

    def _text_command(self):
        try:
            return input("\nYou (type a command): ").strip()
        except (EOFError, KeyboardInterrupt):
            return "exit"

    def get_command(self):
        if self.input_mode == "text":
            return self._text_command()

        print("\nListening… (say your command)")
        command = listen().strip()
        if command:
            return command
        print("I did not catch that. Press Enter to try voice again, or type a command.")
        return self._text_command()

    def _local_command(self, command):
        lower = command.lower().strip()
        if lower in {"help", "commands", "what can you do"}:
            self.respond(HELP_TEXT)
            return True
        if lower == "history":
            recent = self.history[-10:]
            self.respond("Your recent commands:\n" + ("\n".join(f"  - {item}" for item in recent) or "  No commands yet."), False)
            return True
        if lower in {"voice mode", "use voice"}:
            self.input_mode = "voice"
            self.respond("Voice mode enabled.")
            return True
        if lower in {"text mode", "type mode"}:
            self.input_mode = "text"
            self.respond("Text mode enabled.")
            return True
        return False

    def process_command(self, command):
        command = command.strip()
        if not command:
            return
        if command.lower() in EXIT_COMMANDS:
            self.shutdown()
            return
        if self._local_command(command):
            return

        self.history.append(command)
        print(f"\nYou: {command}\n{ASSISTANT_NAME}: Thinking…")
        try:
            data = detect_intent(command)
            intent = data.get("intent", "chat")
            params = data.get("params") or {}
            if intent == "send_whatsapp":
                recipient = params.get("contact", "the recipient")
                message = params.get("message", "")
                prompt = f"Send this WhatsApp message to {recipient}: {message!r}? Type yes to confirm: "
                if input(prompt).strip().lower() not in {"yes", "y"}:
                    self.respond("Message cancelled.")
                    return
                params["confirmed"] = True
            if intent == "send_email":
                recipient = params.get("recipient", "the recipient")
                subject = params.get("subject", "")
                body = params.get("body", "")
                prompt = f"Send email to {recipient}, subject {subject!r}, body {body!r}? Type yes to confirm: "
                if input(prompt).strip().lower() not in {"yes", "y"}:
                    self.respond("Email cancelled.")
                    return
                params["confirmed"] = True
            result = execute(intent, params)
            message = result.get("message", "Done.") if isinstance(result, dict) else str(result)
            self.respond(message)
        except Exception:
            traceback.print_exc()
            self.respond("Sorry, something went wrong while handling that command.")

    def run(self):
        self.startup()
        while self.running:
            self.process_command(self.get_command())


def main():
    parser = argparse.ArgumentParser(description="Arya desktop assistant")
    parser.add_argument("--text", action="store_true", help="Use typed commands instead of microphone input (CLI mode)")
    parser.add_argument("--silent", action="store_true", help="Disable spoken responses (CLI mode)")
    parser.add_argument("--gui", action="store_true", help="Launch the Arya desktop GUI (default)")
    parser.add_argument("--cli", action="store_true", help="Use the terminal assistant instead of the GUI")
    args = parser.parse_args()
    try:
        if not args.cli:
            from gui_app import run_gui
            run_gui()
            return
        AryaAssistant("text" if args.text else "voice", not args.silent).run()
    except KeyboardInterrupt:
        print("\nArya stopped.")
    except Exception:
        traceback.print_exc()


if __name__ == "__main__":
    main()
