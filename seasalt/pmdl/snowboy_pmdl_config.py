import os

CHANNELS = 1
SAMPLE_RATE = 16000
BITS_PER_SAMPLE = 16

COMPTYPE = 'NONE'
COMPNAME = 'not compressed'

RES_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../resources/pmdl')

DEFAULT_LANG = 'en'
VAD_RESOURCE = os.path.join(RES_DIR, DEFAULT_LANG, 'personal_enroll.res')


def get_enroll_resource(lang=DEFAULT_LANG):
    res = os.path.join(RES_DIR, lang, 'personal_enroll.res')
    if not os.path.isfile(res):
        res = os.path.join(RES_DIR, DEFAULT_LANG, 'personal_enroll.res')

    return str(res)


def get_detect_resource(lang=DEFAULT_LANG):
    res = os.path.join(RES_DIR, lang, 'common.res')
    if not os.path.isfile(res):
        res = os.path.join(RES_DIR, DEFAULT_LANG, 'common.res')

    return str(res)
