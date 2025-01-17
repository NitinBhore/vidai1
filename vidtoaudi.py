import os
import moviepy.editor as mp
from pydub import AudioSegment
import wave
from paths import *
from english_transcript import *
from vidtoaudi import *
from scipy.io import wavfile as wav

import whisper
VIDEO_EXTENSIONS = {".mp4", ".avi", ".mov", ".mkv"}


def video_path(directory):
    video_file = os.path.join(directory)
    valid_formats = [".mp4", ".avi", ".mov", ".mkv"]
    if not any(video_file.endswith(format) for format in valid_formats):
        raise ValueError("Invalid video format. Only .mp4, .avi, .mov, and .mkv are supported.")

    audio_path = os.path.splitext(video_file)[0] + ".wav"

    try:
        video = mp.VideoFileClip(video_file)
        video.audio.write_audiofile(audio_path, codec='pcm_s16le')

        stereo_audio = AudioSegment.from_file(audio_path, format="wav")
        mono_audios = stereo_audio.split_to_mono()

        mono_left = mono_audios[0]
        output_path = os.path.splitext(video_file)[0] + "_mono.wav"
        mono_left.export(output_path, format="wav")

        # print(f"Processed {filename} and saved mono audio to {output_path}")
        os.remove(audio_path)
        return output_path

    except Exception as e:
        print(f"Error processing video: {video_file}\nError message: {str(e)}")
        return None
