import csv
import os
from wrapper import *
import time
from string import ascii_letters

##Configurable Items
API_TOKEN = "YOUR_API_TOKEN"
PLATE_COLUMNS = ["Plate Barcode", "Plate Name", "Well Position"]

labsheet = Labsheet("Cell Fraction(New)", API_TOKEN, verbose=True)
csv_name = "/Cell_Fractions.csv"
# Column to Labsheet name
connection_columns = {
    "Cell Type": "Cell Type",
    "Treatment Compound Stock ID": "Compound Stock",
}

barcode_prefix = "FRA"
has_plate_info = True
has_parent = False
parent_labsheet = Labsheet("Cell Culture Imported", API_TOKEN, verbose=True)


def strip_barcode(text):
    return text.lstrip(ascii_letters)


print("############################################")
print("| Loading Data...                          |")
print("############################################")
script_dir = os.path.dirname(__file__)
labsheet_data = []
plate_data = []
with open(script_dir + csv_name, newline="") as csvfile:
    reader = csv.reader(csvfile, delimiter=",", quotechar="|")
    headers = next(reader)
    plate_info_indices = [headers.index(name) for name in PLATE_COLUMNS]
    for row in reader:
        if has_plate_info:
            plate_data.append(row[plate_info_indices[0] :])
            labsheet_data.append(row[: plate_info_indices[0]])
        else:
            labsheet_data.append(row)
print(headers)
for connection_column in connection_columns:
    connection_column_index = headers.index(connection_column)
    connected_sheet = connection_columns[connection_column]
    for i in range(len(labsheet_data)):
        if labsheet_data[i][connection_column_index] != "":
            labsheet_data[i][connection_column_index] = (
                connected_sheet
                + "(ID_BARCODE|"
                + strip_barcode(labsheet_data[i][connection_column_index])
                + ")"
            )

inserted_uuids = labsheet.add_rows(labsheet_data)

print("UUIDs:")
print(inserted_uuids)
## Important Values: labsheet_data, plate_data, inserted_uuids

print("############################################")
print("| Waiting for Barcodes...                  |")
print("############################################")

## Checks when the last row added has a barcode
while True:
    time.sleep(10)
    print("Waiting for barcodes...")
    if (
        labsheet.find_row(inserted_uuids[-1], id_type="uuid")["row"][
            1
        ].removeprefix(barcode_prefix)
        != ""
    ):
        break
print("Barcodes Generated!")

print("############################################")
print("| Fetching Generated Barcodes...           |")
print("############################################")

## Assuming Barcode column is the first column
barcode_index = 1
res = labsheet.list_rows(len(inserted_uuids))
uuid_to_barcode = dict(
    zip(
        [row[0] for row in res["rows"]],
        [row[barcode_index] for row in res["rows"]],
    )
)


for i in range(len(plate_data)):
    if inserted_uuids[i] in uuid_to_barcode:
        plate_data[i].append(uuid_to_barcode[inserted_uuids[i]])
        labsheet_data[i][:0] = uuid_to_barcode[inserted_uuids[i]]
    else:  ## Failsafe branch
        barcode_value = labsheet.find_row(plate_data[i][1], id_type="uuid")[
            "row"
        ][barcode_index]
        plate_data[i].append(barcode_value)
        labsheet_data[i][:0] = barcode_value

print("############################################")
print("| Creating Parent Child Links...           |")
print("############################################")
print()

## Create mapping of parent to children barcodes
## labsheet_data holds all inserted rows(in the same format as add_rows).
if has_parent:
    ## NOTE: Only use the numerical value of the barcode
    ## TODO: Create mapping using labsheet_data, and some calls to parent_labsheet.
    # mapping = {"parent barcode id" : ["children barcode id1"],
    #           "parent barcode id1" : ["children barcode id1"]}

    mapping = {}
    create_parent_child(mapping, parent_labsheet, labsheet)

print()

# Create Manifest
print("############################################")
print("| Creating Manifest...                     |")
print("############################################")

if has_plate_info:
    formatted_plates = {}
    for row in plate_data:
        if row[0] in formatted_plates:
            if row[1] in formatted_plates[row[0]]["plate_name"]:
                formatted_plates[row[0]]["items"].append(
                    {
                        "name": row[3].removeprefix(barcode_prefix),
                        "well": row[2],
                    }
                )
            else:
                raise Exception(
                    "Two plates with the same barcode have different names"
                )
        else:
            formatted_plates[row[0]] = {
                "plate_name": row[1],
                "items": [
                    {
                        "name": row[3].removeprefix(barcode_prefix),
                        "well": row[2],
                    }
                ],
            }
    for plate in formatted_plates:
        create_manifest_payload = {
            "apiKey": API_TOKEN,
            "name": formatted_plates[plate]["plate_name"],
            "template": "96-well plate",
            "autoHrid": False,
            "hrid": plate,
            "plates": [
                {
                    "template": "96-well plate",
                    "wells": 96,
                    "labsheets": [
                        {
                            "idType": "ID_BARCODE",
                            "labsheet": labsheet.name,
                            "items": formatted_plates[plate]["items"],
                        }
                    ],
                }
            ],
        }
        req = requests.post(
            url=DEV_URL + "/manifest/create", json=create_manifest_payload
        )
        res = json.loads(req.text)
        if type(res) is dict:
            if not "success" in res:
                raise APIException(
                    "An error occured with this request",
                    "/manifest/create",
                    create_manifest_payload,
                    res,
                )
            if res["success"] == "false" or res["success"] == False:
                raise APIException(
                    "An error occured at endpoint ",
                    "/manifest/create",
                    create_manifest_payload,
                    res,
                )
        print(
            "successfully created manifest "
            + formatted_plates[plate]["plate_name"]
            + " with id "
            + plate
        )
else:
    print("No Plate Data, skipping manifest creation")


print("############################################")
print("| Done!                                    |")
print("############################################")
