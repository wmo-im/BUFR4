import os
import csv
import glob
import json
from shutil import move

note_id_name = "noteID"

files = glob.glob("*.csv")

for file in files:
    #print("processing {}".format(file))
    with open(file,encoding="utf8") as f:
        reader = csv.DictReader(f, delimiter=',', quotechar='"')
        new_file = file+".tmp"
        with open(new_file,"w",encoding="utf8",newline='') as f_out:
            idx = reader.fieldnames.index("Note_en")
            new_fieldnames = reader.fieldnames[0:idx+1 ] + ["noteIDs",] + reader.fieldnames[idx+1:]
            writer = csv.DictWriter(f_out, delimiter=",", quotechar='"',fieldnames=new_fieldnames )
            writer.writeheader()
                    
    move(new_file,file)
