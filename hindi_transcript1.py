import os
import json
import subprocess
import datetime
import base64
from paths import *
from hindi_transcript import *
from english_transcript import *
from audilang import *
from vidtoaudi import *
from vttojson import *
from datetime import datetime
import streamlit as st

UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'mp4', 'avi'}
OUTPUT_FOLDER = output_path

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Extract metadata from videos
def extract_video_metadata(video_path):
    # Run ExifTool command to extract metadata
    exiftool_cmd = [r"C:\streamlit12\exiftool(-k).exe", '-j', video_path]
    result = subprocess.run(exiftool_cmd, capture_output=True, text=True)
    if result.returncode == 0:
        # Parse the output JSON
        metadata = json.loads(result.stdout)[0]
        # Extract desired metadata fields with fallback to 'NA'
        creation_date = metadata.get('CreateDate', 'NA')
        creation_time = metadata.get('MediaCreateDate', 'NA')
        video_format = metadata.get('FileType', 'NA')
        video_length = metadata.get('Duration', 'NA')
        location = metadata.get('Location', {'latitude': 'NA', 'longitude': 'NA'})
        # Extract only date from creation_date
        creation_date = datetime.strptime(creation_date, '%Y:%m:%d %H:%M:%S').date().strftime('%Y-%m-%d')
        # Extract only time from creation_time
        creation_time = datetime.strptime(creation_time, '%Y:%m:%d %H:%M:%S').time().strftime('%H:%M:%S')
        return creation_date, creation_time, video_format, video_length, location
    else:
        print(f"Error extracting metadata: {result.stderr}")
        return 'NA', 'NA', 'NA', 'NA', 'NA'

@json_encoder
def process_video(input_file):
    if input_file is None:
        return {"error": "No file selected"}
    asset_type = "Video"
    filename = os.path.splitext(os.path.basename(input_file))[0]
    start_time = datetime.now()
    asset_id = filename
    creation_date, creation_time, video_format, video_length, location = extract_video_metadata(input_file)

    # Convert video to audio
    audio_file = video_path(input_file)

    # Detect language of audio
    language = detect_language(audio_file)
    print('Language',language)

    # Transcribe audio based on language
    if language == "hi" or language == "ur":
        json_results, vtt_data, transcription = hindi_transcribe(audio_file)
    elif language == "en":
        json_results, vtt_data, transcription = english_transcribe(audio_file)
    else:
        return {"error": "Skipping transcription due to unknown language"}
    end_time = datetime.now()
    final_results = {
        'asset_type': 'Video',
        "assetId": filename,
        "date": creation_date,
        "time": creation_time,
        "location": location,
        "format": video_format,
        "length": video_length,
        'transcript': transcription,
        "details": json_results
    }

    # Save JSON file
    json_filename = f"{filename}_mono.json"
    json_path = os.path.join(OUTPUT_FOLDER, json_filename)
    with open(json_path, "w") as f:
        json.dump(final_results, f, indent=4)

    # Save VTT file
    vtt_filename = f"{filename}_mono.vtt"
    vtt_path = os.path.join(OUTPUT_FOLDER, vtt_filename)
    with open(vtt_path, "w") as f:
        f.write(vtt_data)

    return [filename, asset_type, video_format, start_time, end_time, "SUCCESS", final_results, "NULL"]

def file_download(file_path, file_name):
    with open(file_path, "r") as f:
        data = f.read()
    b64 = base64.b64encode(data.encode()).decode()
    href = f'<a href="data:application/json;base64,{b64}" download="{file_name}">Download {file_name}</a>'
    return href

def main():
    st.title("VidAI")
    st.write("Upload a video file to transcribe its audio")

    uploaded_file = st.file_uploader("Choose a file", type=ALLOWED_EXTENSIONS)
    if uploaded_file is not None:
        file_details = {"FileName": uploaded_file.name, "FileType": uploaded_file.type}
        st.write(file_details)

        if allowed_file(uploaded_file.name):
            with open(os.path.join(UPLOAD_FOLDER, uploaded_file.name), "wb") as f:
                f.write(uploaded_file.getbuffer())
            video_path = os.path.join(UPLOAD_FOLDER, uploaded_file.name)
            st.video(video_path)
            transcription_result = process_video(video_path)
            if transcription_result:
                if "error" in transcription_result:
                    st.error(transcription_result["error"])
                else:
                    st.success("Transcription complete!")

                    final_results = transcription_result[6]
                    json_data_string = json.dumps(final_results, indent=4)
                    st.json(json_data_string)
                    json_filename = f"{uploaded_file.name}_mono.json"
                    st.download_button("Download JSON", data=json_data_string, file_name=json_filename)                    
            else:
                st.error("Error occurred during transcription. Please try again.")

if __name__ == "__main__":
    main()
