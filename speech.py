import os
import subprocess

import pvorca


def speak(text):
    ORCA_ACCESS_KEY = os.getenv("ORCA_ACCESS_KEY")

    if not ORCA_ACCESS_KEY:
        raise ValueError("Please provide the Orca access key")

    # Initialize the Orca client
    orca = pvorca.create(access_key=ORCA_ACCESS_KEY)

    # Remove any invalid characters (e.g., *)
    text = (
        text.replace("*", "")
        .replace("$", "USD: ")
        .replace("=", "equals")
        .replace(" x ", " times ")
        .replace(" + ", " plus ")
    )

    # Synthesize speech using Orca and save to output.wav
    orca.synthesize_to_file(text, "output.wav")

    # Play the audio file using ffplay
    with open(os.devnull, "w") as devnull:
        subprocess.run(
            ["ffplay", "-nodisp", "-autoexit", "output.wav"],
            stdout=devnull,
            stderr=subprocess.STDOUT,
        )

    # Remove the temporary audio file
    os.remove("output.wav")
