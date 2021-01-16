import json
import os
import csv
import subprocess
import wave
import argparse
from deepspeech import Model, version
import numpy as np
import shlex
import sys
import uuid

try:
    from shhlex import quote
except ImportError:
    from pipes import quote



def metadata_to_string(metadata):
    return ''.join(token.text for token in metadata.tokens)

def words_from_candidate_transcript(metadata):
    word = ""
    word_list = []
    word_start_time = 0
    # Loop through each character
    for i, token in enumerate(metadata.tokens):
        # Append character to word if it's not a space
        if token.text != " ":
            if len(word) == 0:
                # Log the start time of the new word
                word_start_time = token.start_time

            word = word + token.text
        # Word boundary is either a space or the last character in the array
        if token.text == " " or i == len(metadata.tokens) - 1:
            word_duration = token.start_time - word_start_time

            if word_duration < 0:
                word_duration = 0

            each_word = dict()
            each_word["word"] = word
            each_word["start_time"] = round(word_start_time, 4)
            each_word["duration"] = round(word_duration, 4)

            word_list.append(each_word)
            # Reset
            word = ""
            word_start_time = 0

    return word_list

def metadata_json_output(metadata):
    json_result = dict()
    json_result["transcripts"] = [{
        "confidence": transcript.confidence,
        "words": words_from_candidate_transcript(transcript),
    } for transcript in metadata.transcripts]
    return json.dumps(json_result, indent=2)

def convert_samplerate(audio_path, desired_sample_rate):
    sox_cmd = 'sox {} --type raw --bits 16 --channels 1 --rate {} --encoding signed-integer --endian little --compression 0.0 --no-dither - '.format(quote(audio_path), desired_sample_rate)
    try:
        output = subprocess.check_output(shlex.split(sox_cmd), stderr=subprocess.PIPE)
    except subprocess.CalledProcessError as e:
        raise RuntimeError('SoX returned non-zero status: {}'.format(e.stderr))
    except OSError as e:
        raise OSError(e.errno, 'SoX not found, use {}hz files or install it: {}'.format(desired_sample_rate, e.strerror))

    return desired_sample_rate, np.frombuffer(output, np.int16)

def extract_word_wav(wordinfo):
  word = wordinfo['word']
  word = word.replace("'", "")
  try:
    os.mkdir("words/" + word)
  except:
    pass
  outwave = "words/" + word + "/" + word + "_" + str(uuid.uuid4()) + ".wav"
  start_time = wordinfo['start_time'] - 0.175
  duration = wordinfo['duration'] + 0.15
  sox_cmd = 'sox {} {} trim {} {}'.format(quote(wavefile), outwave, start_time , duration)
  try:
      output = subprocess.check_output(shlex.split(sox_cmd), stderr=subprocess.PIPE)
  except subprocess.CalledProcessError as e:
      raise RuntimeError('SoX returned non-zero status: {}'.format(e.stderr))
  except OSError as e:
      raise OSError(e.errno, 'SoX not found, use {}hz files or install it: {}'.format(desired_sample_rate, e.strerror))  
  
  return word, start_time, duration
  
dmodel = "deepspeech-0.9.3-models.pbmm"
dscorer = "deepspeech-0.9.3-models.scorer"
try:
  os.mkdir("words/")
except:
    pass

model = Model(dmodel)

model.enableExternalScorer(dscorer)
lm_alpha = 0.75
lm_beta = 1.85
model.setScorerAlphaBeta(lm_alpha, lm_beta)
beam_width = 500
model.setBeamWidth(beam_width)
desired_sample_rate = model.sampleRate()
wordlist = []
dataset = []
data_folder="/home/stuart/Downloads/northern_english_male/"
with open(data_folder + "line_index.csv") as csvfile:
    reader = csv.reader(csvfile) 
    for row in reader: # each row is a list
        dataset.append(row)

        #print(row)
        wavefile = str(row[1]) 
        wavefile = data_folder + wavefile.strip() + ".wav"
        #print(wavefile)

        fin = wave.open(wavefile, 'rb')
        fs_orig = fin.getframerate()
        if fs_orig != desired_sample_rate:
          print('Warning: original sample rate ({}) is different than {}hz. Resampling might produce erratic speech recognition.'.format(fs_orig, desired_sample_rate), file=sys.stderr)
          fs_new, audio = convert_samplerate(wavefile, desired_sample_rate)
        else:
          audio = np.frombuffer(fin.readframes(fin.getnframes()), np.int16)

          audio_length = fin.getnframes() * (1/fs_orig)
          fin.close()

        x = 0
        sentence = str(row[2]).lower()
        print(sentence)
        wordsin = sentence.split()
        wordsout = words_from_candidate_transcript(model.sttWithMetadata(audio,1).transcripts[0])

        for w in wordsin:
          plusone = False
          if x > len(wordsout) - 1:
            break
          wordinfo = wordsout[x]
          word = wordinfo['word']
          if w == word:
            if len(w) > 4:  
              print(extract_word_wav(wordinfo))
          else:
            if x > len(wordsout):
              wordinfo = wordsout[x + 1]
              word = wordinfo['word']
              if w == word:
                if len(w) > 4:
                  print(extract_word_wav(wordinfo))
                x = x + 1
                plusone = True
            if plusone == False:
              if x > 0:
                 wordinfo = wordsout[x - 1]
                 word = wordinfo['word']
                 if w == word:
                   if len(w) > 4:
                     print(extract_word_wav(wordinfo))
                   x = x - 1
          x = x +1
          
          
            
              
        #print(len(wordsout), len(wordsin))
        #print(metadata_json_output(model.sttWithMetadata(audio, 1)))


