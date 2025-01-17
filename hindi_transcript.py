import os
from vosk import Model, KaldiRecognizer
from ai4bharat.transliteration import XlitEngine
import wave
import json
import datetime
from paths import *


#Function to change the time format    
def format_time(seconds):
    if isinstance(seconds, datetime.timedelta):
        seconds = seconds.total_seconds()

    if seconds >= 3600:  # For durations greater than one hour
        return str(datetime.timedelta(seconds=seconds))
    else:  # For durations less than one hour
        dt = datetime.datetime(1, 1, 1) + datetime.timedelta(seconds=seconds)
        return dt.strftime("%M:%S")

def vtt_to_json(vtt_data):
    subtitles = vtt_data.strip().split('\n\n')

    results = []
    for subtitle in subtitles:
        lines = subtitle.split('\n')
        try:
            start_time, end_time = lines[0].split(' --> ')
        except ValueError:
            continue
        text = ' '.join(lines[1:])
        result = {
            'start_time': start_time,
            'end_time': end_time,
            'text': text
        }
        results.append(result)

    return results

#Use when the language translation is required
def transliterate_text(text):
    def convert_hi_to_eng(word):
        transliterate = e.translit_word(word, lang_code="hi", topk=1)
        if transliterate:
            return transliterate[0]
        else:
            return ""
    
    # Convert the input text to string if it's not already
    text = str(text)
    
    e = XlitEngine(src_script_type="indic", beam_width=10, rescore=False)
    # Split the text into words
    words = text.split()
    # Transliterate each word and concatenate the results with a space
    result = ""
    for word in words:
        transliterated_word = convert_hi_to_eng(word)
        result += transliterated_word + " "
    # Remove the trailing space
    result = result.strip()
    return result

def hindi_transcribe(input_file, model_path=MODEL_PATH,interval=interval):
    # Check if file exists
    if not os.path.exists(model_path):
        raise FileNotFoundError(
            f"Model not found at {model_path}. Please download the model from https://alphacephei.com/vosk/models and unpack as {model_path}")
    if not os.path.exists(input_file):
        raise FileNotFoundError(f"File '{input_file}' doesn't exist")

    with wave.open(input_file, "rb") as wf:
        if wf.getnchannels() != 1 or wf.getsampwidth() != 2 or wf.getcomptype() != "NONE":
            raise ValueError("Audio file must be WAV format mono PCM.")

        model = Model(model_path)
        rec = KaldiRecognizer(model, wf.getframerate())
        rec.SetWords(True)
        results = []
        words = []

        # Recognize speech using vosk model
        while True:
            data = wf.readframes(4000)
            if len(data) == 0:
                break
            if rec.AcceptWaveform(data):
                part_result = json.loads(rec.Result())
                if 'result' in part_result:
                    for word in part_result['result']:
                        result = {'word': word['word'], 'start': word['start'], 'end': word['end']}
                        results.append(result)
                        words.append(word['word'])

        # Group the words into one-second intervals
        grouped_words = []
        current_group = {'start': results[0]['start'], 'words': []}
        for result in results:
            if result['start'] - current_group['start'] >= interval:
                grouped_words.append(current_group)
                current_group = {'start': result['start'], 'words': [result['word']]}
            else:
                current_group['words'].append(result['word'])
        grouped_words.append(current_group)

        # Convert grouped words to VTT format
        vtt_data = "WEBVTT\n\n"
        for i, group in enumerate(grouped_words):
            start_time = format_time(group['start'])
            end_time = format_time(grouped_words[i + 1]['start']) if i < len(grouped_words) - 1 else format_time(
                group['start'] + interval)
            vtt_data += f"{start_time} --> {end_time}\n"
            # Transliterate and add the words
            words_transliterated = [transliterate_text(word) for word in group['words']]
            vtt_data += f"{' '.join(words_transliterated)}\n\n"            

        # Convert VTT to JSON
        json_results = vtt_to_json(vtt_data)
        
        # Create a transcription of the text
        transcription = transliterate_text(" ".join(words))
        return json_results, vtt_data, transcription

