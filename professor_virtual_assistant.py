#!/usr/bin/env python3
import struct
import pyaudio
import pvporcupine
import subprocess
from pydub import AudioSegment
from pydub.playback import play
import speech_recognition       
from pixels import pixels
from grove.factory import Factory
from youtube_search import YoutubeSearch
import os
import webbrowser
import time

porcupine = None
pa = None
audio_stream = None

rec = speech_recognition.Recognizer()
speech = speech_recognition.Microphone(device_index=4)

chime = AudioSegment.from_wav("chime.wav")

pixels.off()

light = Factory.getGpioWrapper("Relay",24)

os.system("clear")

def execute_unix(text):
    command = 'espeak -ven+m3 -k5 -s150 --punct="<characters>" "%s" 2>>/dev/null' % text
    p = subprocess.Popen(command, stdout=subprocess.PIPE, shell=True)
    (output, err) = p.communicate()
    return output

def light_control(text):
    if any(word in text for word in ["on", "activate"]):
        light.on()
        execute_unix("The light is on!")
    elif any(word in text for word in ["off", "deactivate"]):
        light.off()
        execute_unix("The light is off!")
        
def play_youtube(text):
    links = list()
    keyword = text[text.find('for')+4:]
    results = YoutubeSearch(keyword).to_dict()
    for link in results: links.append('https://www.youtube.com' + link['url_suffix'])
    print("Playing '{}' on Youtube!".format(keyword))
    execute_unix("Playing {} on Youtube!".format(keyword))
    url = links[0]
    webbrowser.open(url=url)

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
            print("Professor wake word detected!\n")
            pixels.wakeup()
            with speech as source:
                audio = rec.adjust_for_ambient_noise(source)
                play(chime)
                execute_unix("Yes")
                audio = rec.listen(source)
            try:
                text = rec.recognize_google(audio, language = 'en-US')
                print("Command: {}\n".format(text))
            except speech_recognition.UnknownValueError:
                execute_unix("Sorry, I didn't quite hear you. Can you please repeat?")
                pixels.off()
            except speech_recognition.RequestError as error:
                # print("Could not request results from Google Speech Recognition service; {0}".format(error))
                execute_unix("Sorry, I am currently under maintenance. Please wait a momment!")
                pixels.off()
            else:
                if any(word in text for word in ["light", "lights", "bulb", "LED"]):
                    light_control(text=text)
                    pixels.off()
                    continue
                if any(word in text for word in ["YouTube"]):
                    play_youtube(text=text)
                    pixels.off()
                    continue
                
                pixels.off()
finally:
    if porcupine is not None:
        porcupine.delete()
        
    