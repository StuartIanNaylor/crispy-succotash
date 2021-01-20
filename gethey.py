import os
import csv
import shutil
with open("validated.tsv") as tsvfile:
    tsvreader = csv.reader(tsvfile, delimiter="\t")
    for line in tsvreader:
        if line[2] == "Hey":
          fname1 = line[1]  
          print(fname)
          fname2 = fname.replace(".mp3", ".wav")
          print(fname)
          os.system('sox ' + 'clips/' + fname1 + ' ' + 'Hey/' + fname2)
