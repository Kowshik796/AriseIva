"""
arise-iva | Phase 6: Text-to-Speech Module
==========================================
Converts gesture label strings into spoken audio using pyttsx3 (offline).

Design decisions
----------------
* Speech runs in a **background thread** so it never blocks the video loop.
* A threading.Event gate ensures only one utterance is in-flight at a time —
  if a new gesture arrives while speaking, it is queued and replaces the
  pending word (no build-up of a long backlog).
* The engine is re-initialised per utterance (runAndWait approach) because
  pyttsx3 is not thread-safe across calls when using a persistent engine on
  Windows — fresh init per thread is the most reliable cross-platform pattern.
"""

from __future__ import annotations

import threading
from typing import Optional


class TextToSpeech:
    """
    Non-blocking, offline text-to-speech using pyttsx3.

    Usage::

        tts = TextToSpeech(rate=150, volume=1.0)
        tts.speak("Hello")          # returns immediately; audio plays in background
        tts.speak("Yes")            # replaces any pending utterance
        tts.shutdown()              # call on exit to join the worker thread
    """

    def __init__(self, rate: int = 150, volume: float = 1.0) -> None:
        """
        Args:
            rate:   Words per minute for the speech engine (default 150).
            volume: Output volume, 0.0 – 1.0 (default 1.0).
        """
        self._rate   = rate
        self._volume = volume

        # Pending utterance — replaced (not queued) on rapid gesture changes
        self._pending_text: Optional[str] = None
        self._lock         = threading.Lock()
        self._speaking     = threading.Event()   # set while TTS thread is active
        self._shutdown     = threading.Event()

        print(f"[TextToSpeech] Initialised — rate={rate} wpm, volume={volume}")

    # ── Public API ─────────────────────────────────────────────────────────────

    def speak(self, text: str) -> None:
        """
        Speak *text* asynchronously.

        If the engine is already speaking, the new text is stored as the
        next utterance (replacing any previously queued word). This prevents
        spam without silently dropping gestures that change mid-sentence.

        Args:
            text: The word or phrase to speak (e.g. ``"Hello"``).
        """
        if not text or text.strip() == "":
            return

        with self._lock:
            self._pending_text = text.strip()

        # Only spawn a new worker if one isn't already running
        if not self._speaking.is_set():
            t = threading.Thread(target=self._worker, daemon=True)
            t.start()

    def shutdown(self) -> None:
        """Signal the worker to stop after the current utterance finishes."""
        self._shutdown.set()
        print("[TextToSpeech] Shutdown requested.")

    # ── Private helpers ────────────────────────────────────────────────────────

    def _worker(self) -> None:
        """
        Background thread: consume pending text until there is nothing left.
        Re-initialises the pyttsx3 engine each iteration for thread safety.
        """
        self._speaking.set()
        try:
            while True:
                with self._lock:
                    text = self._pending_text
                    self._pending_text = None

                if text is None or self._shutdown.is_set():
                    break

                self._say(text)

                # After speaking, check if a new word arrived while we were talking
                with self._lock:
                    if self._pending_text is None:
                        break   # nothing queued — let thread exit
                # else: loop again and say the next pending word

        finally:
            self._speaking.clear()

    def _say(self, text: str) -> None:
        """Initialise a fresh pyttsx3 engine, speak *text*, then teardown."""
        try:
            import pyttsx3
            engine = pyttsx3.init()
            engine.setProperty("rate",   self._rate)
            engine.setProperty("volume", self._volume)
            engine.say(text)
            engine.runAndWait()
            engine.stop()
        except Exception as exc:
            print(f"[TextToSpeech] Speech error: {exc}")