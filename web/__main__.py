#!/usr/bin/env python3
"""
Web server for recording Snowboy personal wake word.

See: https://github.com/seasalt-ai/snowboy
"""
import argparse
import asyncio
import base64
import logging
import os
import signal
import tempfile
import typing
import wave
from pathlib import Path
from uuid import uuid4

import hypercorn
import quart_cors
from quart import (
    Quart,
    Response,
    request,
    send_file,
    send_from_directory, abort,
)

from .utils import trim_silence

_LOGGER = logging.getLogger("snowboy-seasalt")
_LOOP = asyncio.get_event_loop()

web_dir = Path(__file__).parent

EXPECTED_API_TOKEN = os.getenv('SNOWBOY_API_TOKEN', '3a4961e07b2a0c38772ad0e8ae350c7a124182da02d6')


# -----------------------------------------------------------------------------


def parse_args():
    """Parse command-line arguments"""
    parser = argparse.ArgumentParser("snowboy-api")
    parser.add_argument(
        "--host", type=str, help="Host for web server", default="0.0.0.0"
    )
    parser.add_argument("--port", type=int, help="Port for web server", default=8000)
    parser.add_argument(
        "--audio-dir", help="Path to store recorded audio (default: temp dir)"
    )
    parser.add_argument(
        "--debug", action="store_true", help="Print DEBUG messages to console"
    )

    return parser.parse_args()


_ARGS = parse_args()

if _ARGS.debug:
    logging.basicConfig(level=logging.DEBUG)
else:
    logging.basicConfig(level=logging.INFO)

_LOGGER.debug(_ARGS)

# Determine where audio is saved
_TEMP_DIR_OBJ = None
if _ARGS.audio_dir:
    # Use user-supplied directory to store audio
    _TEMP_DIR = Path(_ARGS.audio_dir)
    _TEMP_DIR.mkdir(parents=True, exist_ok=True)
else:
    # Use temporary directory used to hold audio
    _TEMP_DIR_OBJ = tempfile.TemporaryDirectory()
    _TEMP_DIR = Path(_TEMP_DIR_OBJ.name)

# Path to personal model generation script
_GENERATE_PMDL = Path(__file__).parent.parent / "seasalt" / "generate_pmdl.sh"
assert _GENERATE_PMDL.is_file(), f"Missing {_GENERATE_PMDL}"

# -----------------------------------------------------------------------------
# Quart App
# -----------------------------------------------------------------------------

app = Quart("snowboy-api", template_folder=str(web_dir / "templates"))
app.config["TEMPLATES_AUTO_RELOAD"] = True

app.secret_key = str(uuid4())
app = quart_cors.cors(app)


# -----------------------------------------------------------------------------
# Template Functions
# -----------------------------------------------------------------------------

# -----------------------------------------------------------------------------


@app.route("/generate", methods=["POST"])
async def api_generate() -> Response:
    """Generate personal model from submitted audio"""
    payload = await request.get_json()

    if not payload:
        abort(400)

    if payload.get('token', '') != EXPECTED_API_TOKEN:
        abort(401)

    model_name = payload.get("name")
    assert model_name, "No model name"
    lang = payload.get("lang") or ""

    # If true, silence is not trimmed
    no_trim = False

    # Create directory to store submitted audio
    model_dir = _TEMP_DIR / model_name
    model_dir.mkdir(parents=True, exist_ok=True)

    voice_samples = payload.get('voice_samples', [])
    files = []
    for i, sample in enumerate(voice_samples):
        print(i)
        print(sample)
        file_name = f'{model_dir}_{i}.wav'
        with open(file_name, 'wb') as f:
            f.write(base64.b64decode(sample['wave']))

        if os.path.exists(file_name):
            files.append(file_name)

    assert len(files) > 2, f"3 voice samples are required (got {len(files)})"

    # Paths to 16 Khz 16-bit mono WAV files
    wav_paths = []

    for file_name in files:
        _LOGGER.debug("Processing %s for %s", file_name, model_name)
        with open(file_name, 'rb') as file_data:
            with tempfile.NamedTemporaryFile(mode="wb+") as original_audio_file:
                # Original audio should be webm or wav
                original_audio_file.write(file_data.read().strip())

                # Rewind
                original_audio_file.seek(0)
                with tempfile.NamedTemporaryFile(
                        mode="wb+", dir=model_dir, suffix=".wav", delete=False
                ) as wav_file:
                    # Convert to 16Khz 16-bit mono WAV
                    ffmpeg_cmd = [
                        "ffmpeg",
                        "-y",
                        "-i",
                        str(file_name),
                        "-acodec",
                        "pcm_s16le",
                        "-ar",
                        "16000",
                        "-ac",
                        "1",
                        "-f",
                        "s16le",
                        "-",
                    ]

                    _LOGGER.debug(ffmpeg_cmd)
                    proc = await asyncio.create_subprocess_exec(
                        *ffmpeg_cmd,
                        stdout=asyncio.subprocess.PIPE,
                        stderr=asyncio.subprocess.PIPE,
                    )
                    audio_bytes, stderr = await proc.communicate()
                    if stderr:
                        _LOGGER.error(stderr)

                    if not no_trim:
                        audio_bytes = trim_silence(audio_bytes)

                    # Write final WAV file
                    wav_io: wave.Wave_write = wave.open(wav_file.name, "wb")
                    with wav_io:
                        wav_io.setframerate(16000)
                        wav_io.setsampwidth(2)
                        wav_io.setnchannels(1)
                        wav_io.writeframes(audio_bytes)

                    wav_file.seek(0)
                    wav_paths.append(wav_file.name)

    if len(wav_paths) > 3:
        _LOGGER.warning(
            "Not all examples will be used for %s (need 3, got %s)",
            model_name,
            len(wav_paths),
        )

    # Generate pmdl
    model_path = model_dir / "model.pmdl"
    generate_cmd = [
        str(_GENERATE_PMDL),
        "-r1",
        str(wav_paths[0]),
        "-r2",
        str(wav_paths[1]),
        "-r3",
        str(wav_paths[2]),
        "-n",
        str(model_path),
    ]
    if lang:
        generate_cmd.extend(["-lang", str(lang)])

    _LOGGER.debug(generate_cmd)
    proc = await asyncio.create_subprocess_exec(*generate_cmd)
    await proc.communicate()

    return await send_file(model_path, as_attachment=True)


# @app.route("/delete", methods=["POST"])
# async def api_delete() -> Response:
#     """Delete audio for a model"""
#     model_name = request.args.get("modelName")
#     if model_name:
#         model_dir = _TEMP_DIR / model_name
#         if model_dir.is_dir():
#             _LOGGER.debug("Deleting %s", model_dir)
#             shutil.rmtree(model_dir)
#
#     return model_name


# ---------------------------------------------------------------------
# Static Routes
# ---------------------------------------------------------------------

css_dir = web_dir / "css"
js_dir = web_dir / "js"
img_dir = web_dir / "img"
webfonts_dir = web_dir / "webfonts"


@app.route("/css/<path:filename>", methods=["GET"])
async def css(filename) -> Response:
    """CSS static endpoint."""
    return await send_from_directory(css_dir, filename)


@app.route("/js/<path:filename>", methods=["GET"])
async def js(filename) -> Response:
    """Javascript static endpoint."""
    return await send_from_directory(js_dir, filename)


@app.route("/img/<path:filename>", methods=["GET"])
async def img(filename) -> Response:
    """Image static endpoint."""
    return await send_from_directory(img_dir, filename)


@app.route("/webfonts/<path:filename>", methods=["GET"])
async def webfonts(filename) -> Response:
    """Webfonts static endpoint."""
    return await send_from_directory(webfonts_dir, filename)


@app.errorhandler(Exception)
async def handle_error(err) -> typing.Tuple[str, int]:
    """Return error as text."""
    _LOGGER.exception(err)
    return (f"{err.__class__.__name__}: {err}", 500)


# -----------------------------------------------------------------------------
# Run Web Server
# -----------------------------------------------------------------------------

hyp_config = hypercorn.config.Config()
hyp_config.bind = [f"{_ARGS.host}:{_ARGS.port}"]

# Create shutdown event for Hypercorn
shutdown_event = asyncio.Event()


def _signal_handler(*_: typing.Any) -> None:
    """Signal shutdown to Hypercorn"""
    shutdown_event.set()


_LOOP.add_signal_handler(signal.SIGTERM, _signal_handler)

try:
    # Need to type cast to satisfy mypy
    shutdown_trigger = typing.cast(
        typing.Callable[..., typing.Awaitable[None]], shutdown_event.wait
    )

    _LOOP.run_until_complete(
        hypercorn.asyncio.serve(app, hyp_config, shutdown_trigger=shutdown_trigger)
    )
except KeyboardInterrupt:
    _LOOP.call_soon(shutdown_event.set)
finally:
    if _TEMP_DIR_OBJ:
        _TEMP_DIR_OBJ.cleanup()
