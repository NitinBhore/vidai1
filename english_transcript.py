import datetime
import os
import whisper
from vttojson import *
from scipy.io import wavfile as wav
from paths import *
import json 
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

#English Transcribe Function
def english_transcribe(input_file, model=model,interval=interval):
    # Load the audio file
    audio = whisper.load_audio(input_file)

    # Transcribe the audio
    result = whisper.transcribe(model, audio)

    # Group transcribed text into 1-second chunks with start times
    transcript_with_time = []
    for i, segment in enumerate(result['segments']):
        start_time = round(segment['start'], 3)
        end_time = round(segment['end'], 3)
        text = segment['text']
        if i == 0:
            prev_end_time = 0
        else:
            prev_end_time = round(result['segments'][i - 1]['end'], 3)
        while prev_end_time + interval <= start_time:
            transcript_with_time.append({'start': prev_end_time, 'end': prev_end_time + interval, 'text': ''})
            prev_end_time += interval
        if prev_end_time < start_time:
            transcript_with_time.append({'start': prev_end_time, 'end': start_time, 'text': ''})

        # Split the text into words
        words = text.split()

        # Initialize the current chunk with the first word
        current_chunk = words.pop(0)

        # Iterate over the remaining words
        while words:
            # Check if adding the next word would exceed the chunk length limit
            if len(current_chunk) + len(words[0]) + interval > 30:
                # If so, add the current chunk to the transcript and start a new chunk
                transcript_with_time.append({'start': start_time, 'end': start_time + interval, 'text': current_chunk})
                start_time += interval
                current_chunk = ''
            else:
                # Otherwise, add the next word to the current chunk
                current_chunk += ' ' + words.pop(0)

        # Add any remaining text as the final chunk
        if current_chunk:
            transcript_with_time.append({'start': start_time, 'end': end_time, 'text': current_chunk})

    # Convert the transcript to VTT format
    vtt_data = "WEBVTT\n\n"
    for segment in transcript_with_time:
        start_time = format_time(segment['start'])
        end_time = format_time(segment['end'])
        text = segment['text']
        vtt_data += f"{start_time} --> {end_time}\n"
        vtt_data += f"{text}\n\n"

    # Create a transcription of the text
    transcription = " ".join([segment['text'] for segment in transcript_with_time])

    # Convert VTT to JSON
    json_results = vtt_to_json(vtt_data)
    return json_results, vtt_data, transcription
