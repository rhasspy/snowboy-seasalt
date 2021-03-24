#! /usr/bin/env bash
ENDPOINT="http://localhost:8000/generate"

############# MODIFY THE FOLLOWING #############
TOKEN="3a4961e07b2a0c38772ad0e8ae350c7a124182da02d6"
NAME="testmodel"
LANGUAGE="en"
AGE_GROUP="20_29"
GENDER="M"
MICROPHONE="??" # e.g., PS3 Eye
############### END OF MODIFY ##################

if [[ "$#" != 4 ]]; then
    printf "Usage: %s wave_file1 wave_file2 wave_file3 out_model_name" $0
    exit
fi

WAV1=`base64 $1`
WAV2=`base64 $2`
WAV3=`base64 $3`
OUTFILE="$4"

cat <<EOF >data.json
{
    "name": "$NAME",
    "token": "$TOKEN",
    "voice_samples": [
        {"wave": "$WAV1"},
        {"wave": "$WAV2"},
        {"wave": "$WAV3"}
    ]
}
EOF

curl -H "Content-Type: application/json" -X POST -d @data.json $ENDPOINT > $OUTFILE
