import os
import csv
import glob
import json
from shutil import move

note_id_name = "noteID"

        
files = glob.glob("*TableD*.csv")

for file in files:
    with open(file,encoding="utf8") as f:
        reader = csv.DictReader(f, delimiter=',', quotechar='"')
        new_file = file+".tmp"
        with open(new_file,"w",encoding="utf8",newline='') as f_out:
            idx = reader.fieldnames.index("Note_en")
            new_fieldnames = reader.fieldnames[0:idx+1 ] + ["noteIDs",] + reader.fieldnames[idx+1:]
            writer = csv.DictWriter(f_out, delimiter=",", quotechar='"',fieldnames=new_fieldnames )
            writer.writeheader()
            for row in reader:
                try:
                    base = os.path.basename(file)
                    writer.writerow(row)
                except ValueError as ve:
                    print(ve)
                    print(row)
                    
    move(new_file,file)
