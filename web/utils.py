"""Utility methods for snowboy recorder."""
from rhasspysilence import WebRtcVadRecorder

# -----------------------------------------------------------------------------


def trim_silence(
    audio_bytes: bytes,
    ratio_threshold: float = 20.0,
    chunk_size: int = 960,
    skip_first_chunk=True,
) -> bytes:
    """Trim silence from start and end of audio using ratio of max/current energy."""
    first_chunk = False
    energies = []
    max_energy = None
    while len(audio_bytes) >= chunk_size:
        chunk = audio_bytes[:chunk_size]
        audio_bytes = audio_bytes[chunk_size:]

        if skip_first_chunk and (not first_chunk):
            first_chunk = True
            continue

        energy = max(1, WebRtcVadRecorder.get_debiased_energy(chunk))
        energies.append((energy, chunk))

        if (max_energy is None) or (energy > max_energy):
            max_energy = energy

    # Determine chunks below threshold
    assert max_energy is not None, "No maximum energy"
    start_index = None
    end_index = None

    for i, (energy, chunk) in enumerate(energies):
        ratio = max_energy / energy
        if ratio < ratio_threshold:
            end_index = None
            if start_index is None:
                start_index = i
        elif end_index is None:
            end_index = i

    if start_index is None:
        start_index = 0

    if end_index is None:
        end_index = len(energies) - 1

    start_index = max(0, start_index - 1)
    end_index = min(len(energies) - 1, end_index + 1)

    keep_bytes = bytes()
    for _, chunk in energies[start_index : end_index + 1]:
        keep_bytes += chunk

    return keep_bytes
