import os
import subprocess
from gtts import gTTS


def speak(text):
    # Synthesize speech using gTTS and save to output.mp3
    tts = gTTS(text=text, lang="en")
    tts.save("output.mp3")

    # Play the audio file using ffplay
    with open(os.devnull, "w") as devnull:
        subprocess.run(
            ["ffplay", "-nodisp", "-autoexit", "output.mp3"],
            stdout=devnull,
            stderr=subprocess.STDOUT,
        )

    # Remove the temporary audio file
    os.remove("output.mp3")
