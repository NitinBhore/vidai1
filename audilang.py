import wave
import json
import whisper_timestamped as whisper
from langdetect import detect_langs
import pycountry
import moviepy.editor as mp
from pydub import AudioSegment
import wave
import sys
import whisper
import numpy as np
import io
import librosa
from paths import*
from scipy.io import wavfile as wav
import time
import shutil
from vidtoaudi import *

# Load the Whisper model outside the function
#model = whisper.load_model("medium", device="cpu")

def detect_language(input_file, model=models):
    # define the output directory path
    output_dir = os.path.splitext(input_file)[0] + "_temp"

    # create the output directory if it doesn't exist
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # load the audio file
    sample_rate, audio_data = wav.read(input_file)

    # Cut the first 10 minutes of audio
    ten_minutes = 10 * 60 * sample_rate
    audio_10min = audio_data[:ten_minutes]

    # Slice the 10-minute audio into 30-second chunks
    chunk_size = 30 * sample_rate
    chunks = [audio_10min[i:i+chunk_size] for i in range(0, len(audio_10min), chunk_size)]

    # detect the language of each chunk and print the detected languages
    detected_languages = []

    start_time = time.time()

    for i, chunk in enumerate(chunks):
        # write the chunk to a temporary file
        chunk_file = os.path.join(output_dir, f"chunk{i+1}.wav")
        wav.write(chunk_file, sample_rate, chunk)

        # load audio and pad/trim it to fit 30 seconds
        audio = whisper.load_audio(chunk_file)
        audio = whisper.pad_or_trim(audio)

        # make log-Mel spectrogram and move to the same device as the model
        mel = whisper.log_mel_spectrogram(audio).to(model.device)

        # detect the spoken language
        _, probs = model.detect_language(mel)
        majority_lang = max(probs, key=probs.get)
        detected_languages.append(majority_lang)

        # delete the chunk file
        os.remove(chunk_file)

    # calculate the final detected language
    final_detected_language = max(set(detected_languages), key=detected_languages.count)

    # delete the output directory
    shutil.rmtree(output_dir)

    end_time = time.time()

    return final_detected_language

