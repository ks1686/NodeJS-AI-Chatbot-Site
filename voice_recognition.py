import os
import subprocess

import speech_recognition as sr
from gtts import gTTS


# Function to record audio and save it as a WAV file using ffmpeg
def record_audio(output_file="output.wav", duration=10):
    print("Recording audio for 10 seconds...")
    # Using ffmpeg to record audio from the default microphone
    command = [
        "ffmpeg",
        "-f",
        "avfoundation",  # For macOS, use 'dshow' for Windows
        "-i",
        ":0",  # :0 is the default audio input device
        "-t",
        str(duration),
        "-acodec",
        "pcm_s16le",
        "-ar",
        "16000",  # Sample rate
        "-ac",
        "2",  # Number of audio channels
        output_file,
    ]
    subprocess.run(command)


# Function to convert the recorded audio to text
def voice_to_text():
    record_audio()
    r = sr.Recognizer()

    # Load the audio file
    audio_file = "output.wav"
    with sr.AudioFile(audio_file) as source:
        audio_data = r.record(source)  # Read the entire audio file

    try:
        print("Converting audio to text...")
        return r.recognize_sphinx(audio_data)  # Recognize speech using Sphinx
    except sr.UnknownValueError:
        print("Could not understand the audio")
    except sr.RequestError as e:
        print("Error: {0}".format(e))
    finally:
        # Clean up: delete the temporary audio file
        os.remove(audio_file)


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
