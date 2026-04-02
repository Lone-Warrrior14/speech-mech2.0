import asyncio
import edge_tts
import pygame
import os
import uuid
import time
import keyboard

VOICE = "en-US-AriaNeural"

pygame.mixer.init()


async def generate_audio(text, filename):
    communicate = edge_tts.Communicate(text, VOICE)
    await communicate.save(filename)


def speak(text):

    print("Assistant:", text)

    filename = f"temp_{uuid.uuid4().hex}.mp3"

    asyncio.run(generate_audio(text, filename))

    pygame.mixer.music.load(filename)
    pygame.mixer.music.play()

    # Wait until playback finishes
    while pygame.mixer.music.get_busy():
        if keyboard.is_pressed('space'):
            print("\n[Playback interrupted]")
            break
        pygame.time.Clock().tick(10)

    pygame.mixer.music.stop()

    # 🔹 IMPORTANT: release file handle
    pygame.mixer.music.unload()

    # Small delay to ensure Windows releases lock
    time.sleep(0.1)

    # Delete file safely
    if os.path.exists(filename):
        try:
            os.remove(filename)
        except:
            pass