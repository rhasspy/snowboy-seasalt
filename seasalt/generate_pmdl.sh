#!/usr/bin/env bash

# Directory of *this* script
this_dir="$( cd "$( dirname "$0" )" && pwd )"

venv="${this_dir}/.venv"

if [[ -d "${venv}" ]]; then
    echo "Using virtual environment at ${venv}" >&2
    source "${venv}/bin/activate"
fi

python2.7 "${this_dir}/generate_pmdl.py" "$@"
