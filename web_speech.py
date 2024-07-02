import os

import speech_recognition as sr


# Function to convert the recorded audio to text
def speech_to_text(audio_file):
    r = sr.Recognizer()

    # Load the audio file
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
