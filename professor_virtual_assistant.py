#!/usr/bin/env python3
import struct
import pyaudio
import pvporcupine
import subprocess
from pydub import AudioSegment
from pydub.playback import play
import speech_recognition
from pixels import pixels

porcupine = None
pa = None
audio_stream = None

rec = speech_recognition.Recognizer()
speech = speech_recognition.Microphone(device_index=4)

chime = AudioSegment.from_wav("chime.wav")

def execute_unix(text):
    command = 'espeak -ven+m3 -k5 -s150 --punct="<characters>" "%s" 2>>/dev/null' % text
    p = subprocess.Popen(command, stdout=subprocess.PIPE, shell=True)
    (output, err) = p.communicate()
    return output

try:
    porcupine = pvporcupine.create(access_key='OBarq6+nQZjftCadhlX1ZR1WulknlRl2PzkUEmxYU7RBZLYTP2g6QQ==',
                                   keyword_paths=['Professor_en_raspberry-pi_v2_1_0.ppn'])

    pa = pyaudio.PyAudio()

    audio_stream = pa.open(
                    rate=porcupine.sample_rate,
                    channels=1,
                    format=pyaudio.paInt16,
                    input=True,
                    frames_per_buffer=porcupine.frame_length)

    while True:
        pcm = audio_stream.read(porcupine.frame_length)
        pcm = struct.unpack_from("h" * porcupine.frame_length, pcm)

        keyword_index = porcupine.process(pcm)

        if keyword_index == 0:
            print("Hotword Detected")
            pixels.wakeup()
            play(chime)
            # execute_unix("Yes")
            with speech as source:
                audio = rec.adjust_for_ambient_noise(source)
                audio = rec.listen(source)
            try:
                text = rec.recognize_google(audio, language = 'en-US')
                print(text)
            except speech_recognition.UnknownValueError:
                print("Google Speech Recognition could not understand audio")
            except speech_recognition.RequestError as error:
                print("Could not request results from Google Speech Recognition service; {0}".format(error))
finally:
    if porcupine is not None:
        porcupine.delete()
    