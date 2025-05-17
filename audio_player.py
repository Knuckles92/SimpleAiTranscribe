import pygame
import logging
import os

class StoppableAudio:
    def __init__(self):
        self.playing = False
        self.initialized = False
        
        # Ensure res directory exists
        os.makedirs('res', exist_ok=True)
        self.temp_file = os.path.join("res", "temp_audio.wav")

        self._init_pygame()

    def _init_pygame(self):
        if not self.initialized:
            try:
                pygame.mixer.init()
                self.initialized = True
                logging.info("Using pygame for audio playback")
            except Exception as e:
                logging.error(f"Failed to initialize pygame mixer: {e}")
                # Try again with different parameters
                try:
                    pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=4096)
                    self.initialized = True
                    logging.info("Using pygame for audio playback (with fallback parameters)")
                except Exception as e2:
                    logging.error(f"Failed to initialize pygame mixer with fallback parameters: {e2}")

    def play(self, audio_segment):
        if not self.initialized:
            self._init_pygame()

        if not self.initialized:
            logging.error("Cannot play audio: pygame mixer could not be initialized")
            return False

        try:
            audio_segment.export(self.temp_file, format="wav")

            pygame.mixer.music.stop()

            pygame.mixer.music.load(self.temp_file)
            pygame.mixer.music.play()

            self.playing = True
            return True
        except Exception as e:
            logging.error(f"Error playing audio with pygame: {e}")
            return False

    def stop(self):
        self.playing = False

        if self.initialized:
            try:
                pygame.mixer.music.stop()
                return True
            except Exception as e:
                logging.error(f"Error stopping pygame playback: {e}")

        return False  # Couldn't stop playback
