#! /usr/bin/evn python

import base64
import json
import sys

import requests


def get_wave(fname):
    with open(fname, 'rb') as infile:
        return base64.b64encode(infile.read())


endpoint = "http://localhost:8000/generate"

############# MODIFY THE FOLLOWING #############
token = "3a4961e07b2a0c38772ad0e8ae350c7a124182da02d6"
hotword_name = "testmodel"
language = "en"
age_group = "20_29"
gender = "M"
microphone = "??"  # e.g., macbook pro microphone
############### END OF MODIFY ##################

if __name__ == "__main__":
    try:
        [_, wav1, wav2, wav3, out] = sys.argv
    except ValueError:
        print("Usage: %s wave_file1 wave_file2 wave_file3 out_model_name", sys.argv[0])
        sys.exit()

    data = {
        "name": hotword_name,
        "language": language,
        "age_group": age_group,
        "gender": gender,
        "microphone": microphone,
        "token": token,
        "voice_samples": [
            {"wave": get_wave(wav1)},
            {"wave": get_wave(wav2)},
            {"wave": get_wave(wav3)}
        ]
    }
    print(json.dumps(data, indent=4, sort_keys=True, default=str))
    response = requests.post(endpoint, json=data)
    if response.ok:
        with open(out, "w") as outfile:
            outfile.write(response.content)
        print("Saved model to '%s'.", out)
    else:
        print("Request failed.")
        print(response.text)
