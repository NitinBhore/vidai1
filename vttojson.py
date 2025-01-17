import re
import json

def json_encoder(obj):
        if isinstance(obj, bytes):
            return obj.decode('utf-8')
        else:
            return obj

def vtt_to_json(vtt_file):
    with open(vtt_file, 'r',encoding='utf-8') as f:
        data = f.read()


    subtitles = data.strip().split('\n\n')


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


# def vtt_to_json(vtt_file):
    # with open(vtt_file, 'r', encoding='utf-8') as f:
        # vtt_data = f.read()
    # vtt_data = vtt_data.strip()
    # # remove WEBVTT header
    # vtt_data = re.sub(r'^WEBVTT[\s\S]*?(?=^\s*$)', '', vtt_data, flags=re.MULTILINE)
    # # remove newline characters
    # vtt_data = re.sub(r'\n', '', vtt_data)
    # # split into captions
    # captions = re.findall(r'(?P<start_time>\d+:\d+:\d+\.\d+) --> (?P<end_time>\d+:\d+:\d+\.\d+)(?P<caption_text>.*?)$', vtt_data, flags=re.MULTILINE|re.DOTALL)
    # # create JSON object
    # json_data = []
    # for caption in captions:
        # start_time = caption[0]
        # end_time = caption[1]
        # caption_text = caption[2].strip()
        # json_data.append({'start_time': start_time, 'end_time': end_time, 'caption_text': caption_text})
    # # write JSON object to file
    # with open(vtt_file[:-4] + '.json', 'w', encoding='utf-8') as f:
        # json.dump(json_data, f, default=json_encoder, ensure_ascii=False)


