import requests
import json

def add_new_samples(samples):
   session = requests.Session()
   url = 'https://api.scispot.io/tryingtofixcors/labsheets/add-rows'
   payload = {
     "apiKey": "3F4E0776-EFEF-4A5B-8479-01B7C2367090",
     "manager": "Sample Manager",
     "rows": samples
   }
   ret = session.post(url, json=payload)
   return json.loads(ret.text)

def add_new_proteins(proteins):
   session = requests.Session()
   url = 'https://api.scispot.io/tryingtofixcors/labsheets/add-rows'
   payload = {
     "apiKey": "3F4E0776-EFEF-4A5B-8479-01B7C2367090",
     "manager": "Protein Manager",
     "rows": proteins
   }
   ret = session.post(url, json=payload)
   return json.loads(ret.text)

samples_to_add = []
samples_to_add.append(['SAMPLE 01','','',1,'10:00','','','TEST','Fresh Cell','','','','None','None','Fail','12',''])
result = add_new_samples(samples_to_add)
#print(result)

# Result Sample Example
# [{'row': '1', 'success': 'true', 'uuid': 'ae8cafab-d5ba-4678-ae0e-b570262ebcc5'}]

## if you want to add this sample in the connection column "Sample ID"
## you should use 'ae8cafab-d5ba-4678-ae0e-b570262ebcc5' in the second position like this:
## ['PROTEIN 01', 'ae8cafab-d5ba-4678-ae0e-b570262ebcc5', ...]

## if you want to add this sample in the parent column "Parent"
## you should use 'ae8cafab-d5ba-4678-ae0e-b570262ebcc5' in the 14th position like this:
## ['PROTEIN 01', '', '', '01/02/2021', 'Collaborator', 'Test', 'Test', 2, 'Test', '', 'Test', 2, 'True', 'ae8cafab-d5ba-4678-ae0e-b570262ebcc5', '', '', '']

## to get the UUID of one register, you have two choices:
## 1) in the response of add-rows endpoint
## 2) the first column in list-rows endpoint

proteins_to_add = []
proteins_to_add.append(['PROTEIN 01', '', '', '01/02/2021', 'Collaborator', 'Test', 'Test', 2, 'Test', '', 'Test', 2, 'True', '', '', '', ''])
result = add_new_proteins(proteins_to_add)
print(result)
# Result Protein Example
# [{'row': '1', 'success': 'true', 'uuid': 'd35d0b70-76c5-4108-8495-e14d1f203749'}]