import csv
from pathlib import Path
import requests
import json
from rdflib import Graph, Literal, RDF, URIRef, BNode
from rdflib.namespace import SKOS, DCTERMS, RDFS, OWL, Namespace, XSD, RDF

LDP = Namespace("http://www.w3.org/ns/ldp#")
REG = Namespace("http://purl.org/linked-data/registry#")
BUFR4 = Namespace("http://codes.wmo.int/def/bufr4/")
COMMON = Namespace("http://codes.wmo.int/def/common/")
SCHEMA = Namespace("http://schema.org/")
UNITS = Namespace("http://codes.wmo.int/common/unit/")
DCT = Namespace("http://purl.org/dc/terms/")
XSD = Namespace("http://www.w3.org/2001/XMLSchema#")

BASE = Path("./tables")

BUFR_B_CLASSES = ["00", "01", "02", "03", "04", "05", "06", "07", "08", "09",
                  "10", "11", "12", "13", "14", "15", "16", "17", "18", "19",
                  "20", "21", "22", "23", "24", "25", "26", "27", "28", "29",
                  "30", "31", "32", "33", "34", "35", "36", "37", "38", "39",
                  "40", "41", "42"]

BUFR_D_CATEGORIES = ["00", "01", "02", "03", "04", "05", "06", "07", "08", "09",
                     "10", "11", "12", "13", "14", "15", "16", "17", "18", "19",
                     "20", "21", "22", "23", "24", "25", "26", "27", "28", "29",
                     "30", "31", "32", "33", "34", "35", "36", "37", "38", "39",
                     "40"]

BASEPATH = Path("./../../")  # Repository root relative to this script
REGISTRY = "http://codes.wmo.int"
REGISTER = "bufr4-28-10-24-v2"

with open("units_map.json") as fh:
    UNITS_MAP = json.load(fh)

with open("units_cache.json") as fh:
    UNITS_CACHE = json.load(fh)

# Helper functions
def load_notes(table, basepath):
    """Function to load notes associated with specified table"""
    notes = {}
    crex = "CREX" if table in ("TableB","CodeFlag") else ""
    note_file = basepath / "notes" / f"BUFR{crex}_{table}_notes.csv"

    with open(note_file) as fh:
        rows = csv.DictReader(fh)
        for row in rows:
            notes[row['noteID']] = row['note']
    return notes


def get_units(units):
    uri = None
    # First replace power and spaces
    units = units.replace('^', '')
    units = units.replace(" ", "_")
    # next  apply corrections
    units = UNITS_MAP.get(units,units)
    if units in UNITS_CACHE:
        uri  = UNITS_CACHE[units]
    else:
        _url = f"{UNITS[units]}?_format=jsonld"
        try:
            response = requests.get(_url)
            if response.status_code == 200:
                jsonld = response.json()
                code_figure = jsonld.get(
                    "http://codes.wmo.int/def/common/code_figure")
                UNITS_CACHE[units] = code_figure
            else:
                raise RuntimeError
        except Exception as e:
            print(f"Error fetching units {units}")
            raise e

    return uri


def create_register():
    # Create register
    root = Graph()
    # add name spaces
    root.namespace_manager.bind("bufr4", BUFR4)
    root.namespace_manager.bind("cct", COMMON)
    root.namespace_manager.bind("sco", SCHEMA)
    return root


def create_collection(register, path, label, description):
    # Add namespaces specific to collection
    register.namespace_manager.bind("ldp", LDP)
    register.namespace_manager.bind("reg", REG)
    # Check we have description, if not set to label
    description = description if len(description) > 0 else label
    # Now create the collection object
    object_id = path
    obj = URIRef(object_id)
    register.add( (obj, RDF.type, SKOS.Collection))
    register.add((obj, RDF.type, LDP.Container))
    register.add((obj, RDF.type, REG.Register))
    register.add((obj, RDFS.label, Literal(label, lang="en")))
    register.add((obj, DCT.description, Literal(description, lang="en")))
    register.add((obj, LDP.membershipPredicate, SKOS.member))


def create_object(register, path, label, description, notation,
                  additional_properties):
    object_id = path
    obj = URIRef(object_id)
    register.add((obj, RDF.type, SKOS.Concept))
    register.add((obj, RDFS.label, Literal(label, lang="en")))
    register.add((obj, DCT.description, Literal(description, lang="en")))
    register.add((obj, SKOS.notation, Literal(notation)))
    nproperties = len(additional_properties)
    for  idx in range(nproperties):
        item = additional_properties[idx]
        try:
            register.add((obj, item['attribute'], item['value']))
        except Exception as e:
            print(f"{e}")
            print(json.dumps(item))




# First load notes
notes = {table: load_notes(table, BASEPATH) for table in
         ("TableB", "TableC", "TableD", "CodeFlag")}

# Now create Table B entries
infile = BASEPATH / "BUFRCREX_TableB_en.csv"
bufr_class_names = {}
with open(infile) as fh:
    rows = csv.DictReader(fh)
    for row in rows:
        F = row.get("F")
        XX = row.get("X")
        bufr_class_names[XX] = row.get("CLASS")
        _id = f"{REGISTRY}/{REGISTER}/descriptors/{F}/{XX}"
        register = create_register()
        create_collection(register, _id, row.get("CLASS"), row.get("COMMENTS"))
        turtle_file = BASEPATH / "ttl" / "descriptors" / f"{F}" / f"{XX}.ttl"
        turtle_file.parent.mkdir(parents=True, exist_ok=True)
        register.serialize(destination=turtle_file)

# Now sub tables in Table B
for XX in BUFR_B_CLASSES:
    F = "0"
    infile = BASEPATH / f"BUFRCREX_TableB_en_{XX}.csv"
    if infile.is_file():
        rows = csv.DictReader(open(infile))
        for row in rows:
            if row.get('FXY','') == "020003":
                continue
            YYY = row.get('FXY')[3:6]
            label = row.get("ElementName_en")
            description = label
            attributes = [
                {
                    "attribute": BUFR4.dataWidth_bits,
                    "value": Literal(int(row.get('BUFR_DataWidth_Bits')))},
                {
                    "attribute": BUFR4.fxy,
                    "value": Literal(row.get('FXY'))
                },
                {
                    "attribute": BUFR4.referenceValue,
                    "value": Literal(int(row.get('BUFR_ReferenceValue')))
                },
                {
                    "attribute": BUFR4.scale,
                    "value": Literal(int(row.get('BUFR_Scale')))
                }
            ]
            noteIDs = row.get('noteIDs','')
            if len(noteIDs) > 0:
                for idx in noteIDs.split(","):
                    note = notes["TableB"][idx]
                    attributes.append({
                        "attribute": SKOS.note,
                        "value": Literal(note, lang="en")
                    })

            units = row.get("BUFR_Unit")
            # Now type of object
            if "code table" in units.lower():
                table_uri = URIRef(
                    f'{REGISTRY}/{REGISTER}/code_tables/0/{XX}/{YYY}')
                attributes.append({"attribute": DCT.references, "value": table_uri})
            elif "flag table" in units.lower():
                table_uri = URIRef(
                    f'{REGISTRY}/{REGISTER}/flag_tables/0/{XX}/{YYY}')
                attributes.append({"attribute": DCT.references, "value": table_uri})
            elif units.lower() == "numeric":
                pass
            elif units.upper() == "CCITT IA5":
                attributes.append({"attribute": RDFS.range, "value": XSD.string})
            else:
                code_figure = get_units(units)
                attributes.append({"attribute": COMMON.unit, "value": UNITS[code_figure]})

#                print(units)
            _id = f"{REGISTRY}/{REGISTER}/descriptors/{F}/{XX}/{YYY}"
            register = create_register()
            create_object(register, _id, label,
                          description, YYY, attributes)
            turtle_file = BASEPATH / "ttl" / "descriptors" / f"{F}" / \
                          f"{XX}" / f"{YYY}.ttl"
            turtle_file.parent.mkdir(parents=True, exist_ok=True)
            register.serialize(destination=turtle_file)

# Now Table D categories
infile = BASEPATH / "BUFR_TableD_en.csv"
with open(infile) as fh:
    reader = csv.DictReader(fh)
    for row in reader:
        F = row.get("F")
        XX = row.get("X")
        _id = f"{REGISTRY}/{REGISTER}/descriptors/{F}/{XX}"
        register = create_register()
        create_collection(register, _id, row.get("CATEGORY"), row.get("CATEGORY"))
        turtle_file = BASEPATH / "ttl" / "descriptors" / f"{F}" / f"{XX}.ttl"
        turtle_file.parent.mkdir(parents=True, exist_ok=True)
        register.serialize(destination=turtle_file)

for XX in BUFR_D_CATEGORIES:
    F = '3'
    infile = BASEPATH / f"BUFR_TableD_en_{XX}.csv"
    # First we need to extract the sequences
    sequences = {}
    if infile.is_file():
        with open(infile) as fh:
            reader = csv.DictReader(fh)
            idx = 0
            for row in reader:
                idx+=1
                FXXYYY1 = row.get("FXY1")  # The sequence ID
                FXXYYY2 = row.get("FXY2")  # The descriptor contained in FXXYYY1
                _id = f"{REGISTRY}/{REGISTER}/descriptors/{FXXYYY2[0]}/{FXXYYY2[1:3]}/{FXXYYY2[3:6]}"
                # check if we have any notes
                noteIDs = row.get('noteIDs')
                applicable_notes = []
                if len(noteIDs) > 0:
                    for nid in noteIDs.split(","):
                        note = notes["TableD"][nid]
                        applicable_notes.append(note)
                item = {
                    "fxy": FXXYYY2,
                    "uri": _id,
                    "name": row.get("ElementName_en"),
                    "description": row.get("ElementDescription_en"),
                    "notes": applicable_notes
                }
                if FXXYYY1 not in sequences:
                    sequences[FXXYYY1] = {
                        'label': row.get('Title_en'),
                        'description': row.get('SubTitle_en'),
                        'items': []
                    }
                sequences[FXXYYY1]['items'].append(item)
    # now build objects
    for k, v in sequences.items():
        register = create_register()
        YYY = k[3:6]
        _id = f"{REGISTRY}/{REGISTER}/descriptors/{F}/{XX}/{YYY}"
        attributes = []
        create_object(register, _id, v.get('label'),
                          v.get('description'), YYY, attributes)
        # Add items to object
        seq = BNode()
        register.add((seq,RDF.type,RDF.Seq))
        nitems = len(v['items'])
        for idx in range(nitems):
            item = BNode()
            register.add((seq, RDF[f"_{idx+1:03d}"], item))
            register.add((item, RDF.value, URIRef(v['items'][idx]['uri'])))
            register.add((item, RDFS.label,Literal(v['items'][idx]['name'], lang="en")))
            if len(v['items'][idx]['description']) > 0:
                register.add((item, DCT.description,Literal(v['items'][idx]['description'], lang="en")))
            register.add((item, BUFR4.fxy, Literal(v['items'][idx]['fxy'])))

        register.add((URIRef(_id), DCT.hasPart, seq))

        turtle_file = BASEPATH / "ttl" / "descriptors" / f"{F}" / \
                      f"{XX}" / f"{YYY}.ttl"
        turtle_file.parent.mkdir(parents=True, exist_ok=True)
        register.serialize(destination=turtle_file)

# Now code tables
# 1) iterate over rows to get all entries in a code table
# 2) for each identified code table create TTL
# 3) create sub registers for each code table
for XX in BUFR_B_CLASSES:
    F = "0"
    infile = BASEPATH / f"BUFRCREX_CodeFlag_en_{XX}.csv"
    _id = f'{REGISTRY}/{REGISTER}/code_tables/{F}/{XX}'
    register = create_register()
    label = f"Code tables associated with BUFR class {XX}"
    desc = f"Code tables associated with BUFR class {XX}"
    if XX in bufr_class_names:
        desc += f" ({bufr_class_names[XX]})"
    create_collection(register, _id, label, desc)

    turtle_file = BASEPATH / "ttl" / "code_tables" / f"{F}" / f"{XX}.ttl"
    turtle_file.parent.mkdir(parents=True, exist_ok=True)
    register.serialize(destination=turtle_file)

    if infile.is_file():
        code_tables = {}
        rows = csv.DictReader(open(infile))
        # 1
        for row in rows:
            # exclude 'Reserved' entries
            if row.get('EntryName_en','') == 'Reserved':
                continue

            cf = row.get('CodeFigure')
            if f"{cf}" == "":
                continue
            fxy = row.get('FXY')
            if fxy == "020003":  # skip 0-20-003 for now as issues with the registry
                continue
            noteIDs = row.get('noteIDs')
            applicable_notes = []
            flag_table = False
            if 'All' in f"{cf}":
                flag_table = True

            if len(noteIDs) > 0:
                for nid in noteIDs.split(","):
                    note = notes["CodeFlag"][nid]
                    applicable_notes.append(note)

            item = {
                        'code_figure': cf,
                        'label': row.get('EntryName_en'),
                        'description': row.get('EntryName_en'),
                        'notes': applicable_notes
                    }
            if fxy in code_tables:
                code_tables[fxy]['items'].append(item)
            else:
                code_tables[fxy] = {
                    'fxy': fxy,
                    'label': row.get('ElementName_en'),
                    'items': [item],
                    'flag_table': False
                }
            if flag_table:
                code_tables[fxy]['flag_table'] = flag_table

        # 2
        for k, v in code_tables.items():
            if v['flag_table']:
                continue
            fxy = k
            xx = fxy[1:3]
            yyy = fxy[3:6]
            # first create code table
            _id = f'{REGISTRY}/{REGISTER}/code_tables/0/{xx}/{yyy}'
            register = create_register()
            create_collection(register, _id, v.get('label',''), v.get('description',''))
            turtle_file = BASEPATH / "ttl" / "code_tables" / "0" / f"{xx}" / f"{yyy}.ttl"
            turtle_file.parent.mkdir(parents=True, exist_ok=True)
            register.serialize(destination=turtle_file)
            # next add items
            for item in v['items']:
                cf = item['code_figure']
                register = create_register()
                _id = f'{REGISTRY}/{REGISTER}/code_tables/0/{xx}/{yyy}/{cf}'
                properties = []
                memberOf = f'{REGISTRY}/{REGISTER}/code_tables/0/{xx}/{yyy}'
                properties.append({
                    'attribute': SKOS.inScheme,
                    'value': URIRef(memberOf)
                })
                for note in item['notes']:
                    properties.append({
                        'attribute': SKOS.note,
                        'value': Literal(note, lang="en")
                    })
                create_object(register, _id, item['label'], item['label'], cf, properties)
                turtle_file = BASEPATH / "ttl" / "code_tables" / "0" / f"{xx}" / f"{yyy}" / f"{cf}.ttl"
                turtle_file.parent.mkdir(parents=True, exist_ok=True)
                register.serialize(destination=turtle_file)


# create sub-registers
registers = {
    'code_tables/0' : {'label': 'Code tables associated with BUFR/CREX Table B', 'description': 'Code tables associated with BUFR/CREX Table B'},
    'descriptors/0' : {'label': 'BUFR/CREX Table B', 'description': 'BUFR tables relative to Section 3 (BUFR/CREX Table B)'},
    'descriptors/3' : {'label': 'BUFR/CREX Table D', 'description': 'BUFR/CREX Table D - List of common sequences'},
    'code_tables' : {'label': 'Code tables associated with BUFR/CREX Table B', 'description':'Code tables associated with BUFR/CREX Table B'},
    'descriptors' : {'label': 'BUFR descriptors (Tables B, C, and D)', 'description':'BUFR descriptors (Tables B, C, and D)'}
}

for _id, attributes in registers.items():
    p = _id.split("/")
    _id = f"{REGISTRY}/{REGISTER}/{_id}"
    register = create_register()
    create_collection(register, _id,attributes.get('label'), attributes.get('description'))
    turtle_file = BASEPATH.joinpath("ttl").joinpath(*p).with_suffix(".ttl")
    turtle_file.parent.mkdir(parents=True, exist_ok=True)
    register.serialize(destination=turtle_file)








