import csv
import sox
import os

marvdir = "/home/stuart/simple_audio_tensorflow/data/speech_commands_v0.02/marvin/"
heydir = "/home/stuart/Downloads/cv-corpus-6.1-singleword/en/Hey/"
heymarvindir ="/home/stuart/Downloads/heymarvin/"


def marvtrim(marvline, start, end):
  # create transformer
  tfm = sox.Transformer()
  # Normalise default -3db
  #tfm.set_globals( False, False, False, False, 0)
  tfm.reverse()
  tfm.trim(0.02)
  tfm.reverse()
  tfm.trim(0.02)
  tfm.norm(db_level=-3.0)
  # apply silence
  tfm.silence(1, start, 0.04, True)
  # apply a fade in and fade out
  #tfm.reverse()
  tfm.silence(-1, end, 0.04, True)
  tfm.fade(fade_in_len=0.08, fade_out_len=0.8)
  # apply rate  
  tfm.rate(16000)
  # Output file
  tfm.build_file(marvdir + marvline, heymarvindir + "marv/" + marvline, None, None, None, False)
  is_silent = sox.file_info.silent(heymarvindir + "marv/" + marvline, 0.005)
  duration = sox.file_info.duration(heymarvindir + "marv/" + marvline)
  return is_silent, duration
  
def heytrim(heyline, start, end):
  # create transformer
  tfm = sox.Transformer()
  # Normalise default -3db
  #tfm.set_globals( False, False, False, False, 0)
  tfm.reverse()
  tfm.trim(0.02)
  tfm.reverse()
  tfm.trim(0.02)
  tfm.norm(db_level=-3.0)
  # apply silence
  tfm.silence(1, start, 0.02, True)
  # apply a fade in and fade out
  #tfm.reverse()
  tfm.silence(-1, end, 0.02, True)
  tfm.fade(fade_in_len=0.08, fade_out_len=0.8)
  # apply rate  
  tfm.rate(16000)
  # Output file
  tfm.build_file(heydir + heyline, heymarvindir + "hey/" + heyline, None, None, None, False)
  is_silent = sox.file_info.silent(heymarvindir + "hey/" + heyline, 0.005)
  duration = sox.file_info.duration(heymarvindir + "hey/" + heyline)
  return is_silent, duration

def heymarvin(marvline, heyline):
  cbn = sox.Combiner()
  cbn.convert(samplerate=16000, n_channels=1)
  cbn.build([heymarvindir + "hey/" + heyline, heymarvindir + "marv/" + marvline], heymarvindir +  marvline, 'concatenate')
  
  duration1 = sox.file_info.duration(heymarvindir + "hey/" + heyline)
  duration2 = sox.file_info.duration(heymarvindir + "marv/" + marvline)
  padduration = 1 - duration1 - duration2
  if padduration > 0:
    tfm = sox.Transformer()
    tfm.pad(end_duration=padduration)
    tfm.build_file(heymarvindir + "hey/" + heyline, heymarvindir + "hey/" + "2-" + heyline)
    cbn.build([heymarvindir + "hey/" + "2-" + heyline, heymarvindir + "marv/" + marvline], heymarvindir +  "2-" + marvline, 'concatenate')
    padduration = padduration / 2
    tfm2 = sox.Transformer()
    tfm2.pad(start_duration=padduration, end_duration=padduration)
    tfm2.build_file(heymarvindir +  marvline, heymarvindir +  "1-" + marvline)
    os.remove(heymarvindir +  marvline)
  return True
  

count = 0
silentcount = 0
durationcount = 0

with open(marvdir + "rfreq.csv") as marvfile:
  marvreader = csv.reader(marvfile, delimiter=",")
  for marvline in marvreader:
    #print(marvline[0], marvline[1])
    badmarv = False
    result = marvtrim(marvline[1], 5, 1)
    if result[0] == True:
      #silentcount = silentcount + 1
      #print(marvline[1])
      badmarv = True
    if result[1] == None:
      #durationcount = durationcount + 1
      #print(marvline[1])
      badmarv = True
    else:  
      if result[1] < 0.40:
        #durationcount = durationcount + 1
        #print(marvline[1])
        badmarv = True
      if result[1] > 0.7:
        badmarv = True
    if badmarv == True:
      os.remove(heymarvindir + "marv/" + marvline[1])
      #print(marvline[1])
      #count = count + 1
      #print(result[1])
    else:
      with open(heydir + "rfreq.csv") as heyfile:
        heyreader = csv.reader(heyfile, delimiter=",")
        for heyline in heyreader:
          if int(heyline[0]) > int(marvline[0]):
            #print(heyline[0], heyline[1])
            badhey = False
            result = heytrim(heyline[1], 5, 3)
            if result[0] == True:
              silentcount = silentcount + 1
              #print(heyline[1])
              badhey = True
            if result[1] == None:
              durationcount = durationcount + 1
              #print(heyline[1])
              badhey = True
            else:  
              if result[1] < 0.2:
                durationcount = durationcount + 1
                #print(heyline[1])
                badhey = True
              if result[1] > 0.45:
                badhey = True
            if badhey == True:
              os.remove(heymarvindir + "hey/" + heyline[1])
              #print(heyline[1])
            else:
              count = count + 1
              heymarvin(marvline[1], heyline[1])
              print(result[1])
              break
            
  print(silentcount, durationcount, count)
             
