import json
import requests

PROD_URL = "https://api.scispot.io/v2"


class APIException(Exception):
    def __init__(self, message, endpoint, payload, res):
        self.message = message + "\n"
        self.message += "Request: " + endpoint + "\n"
        self.message += str(json.dumps(payload, indent=4)) + "\n"
        self.message += "Response: " + str(json.dumps(res, indent=4)) + "\n"
        super().__init__(self.message)


class Labsheet:
    ADD_ROWS = "/labsheets/add-rows"
    UPDATE_ROWS = "/labsheets/update-rows"
    UPDATE_ROWS_BY_ID = "/labsheets/update-rows-by-id"
    FIND_ROW = "/labsheets/find-row"
    FIND_ROW_BY_ID = "/labsheets/find-row-by-id"
    LIST_ROWS = "/labsheets/list-rows"
    DELETE_ROWS = "/labsheets/delete-rows"
    CREATE = "/labsheets/create"
    UPDATE_PARENT = "/labsheets/update-parent"
    UPDATE_CHILDREN = "/labsheets/update-children"

    def __init__(self, name, api_key, verbose=False, base="dev"):
        self.name = name
        self.api_key = api_key
        self.verbose = verbose
        if base == "prod":
            self.BASE_URL = PROD_URL
        else:
            raise APIException("Incorrect base. Must be 'prod'")

    ## Supports limited column types.
    def create(self, header_names, header_types):
        columns = []
        for i in range(len(header_names)):
            columns.append(
                {
                    "position": i,
                    "name": header_names[i],
                    "type": header_types[i],
                }
            )
        payload = {"name": self.name, "columns": columns}
        res = self.make_request(self.CREATE, payload)
        self.error_check(res, payload, self.CREATE)
        print("successfully created labsheet.")
        return res

    def make_request(self, endpoint, payload):
        payload["apiKey"] = self.api_key
        payload["manager"] = self.name
        payload["labsheet"] = self.name
        if self.verbose:
            print(self.BASE_URL + endpoint)
            print(str(json.dumps(payload, indent=4)))
        req = requests.post(url=self.BASE_URL + endpoint, json=payload)
        res = json.loads(req.text)
        return res

    def error_check(self, res, payload, endpoint):
        if type(res) is dict:
            if not "success" in res:
                raise APIException(
                    "An error occured: ", endpoint, payload, res
                )
            if res["success"] == "false" or res["success"] == False:
                raise APIException(
                    "An error occured: ", endpoint, payload, res
                )
        elif type(res) is list:
            for row in res:
                if row["success"] == "false" or row["success"] == False:
                    raise APIException(
                        "An error occured: ", endpoint, payload, res
                    )

    def add_rows(self, rows):
        payload = {"rows": rows}
        res = self.make_request(self.ADD_ROWS, payload)
        print(res)
        self.error_check(res, payload, self.ADD_ROWS)
        print("successfully added rows.")
        return [row["uuid"] for row in sorted(res, key=lambda x: x["row"])]

    def get_headers(self):
        self.list_rows(0, 0)

    # Usually, the uuid, stays packaged with the rest of the rows
    def update_rows(self, rows):
        payload = {"rows": [{"uuid": row[0], "data": row[1:]} for row in rows]}
        res = self.make_request(self.UPDATE_ROWS, payload)
        self.error_check(res, payload, self.UPDATE_ROWS)
        print("successfully updated rows.")
        return res

    def find_row(self, id, id_type="uuid"):
        if id_type == "uuid":
            payload = {"uuid": id}
            res = self.make_request(self.FIND_ROW, payload)
            self.error_check(res, payload, self.FIND_ROW)
            print("successfully found row.")
            return res
        elif id_type == "id":
            payload = {"id": id}
        elif id_type == "barcode":
            payload = {"id": id, "idType": "ID_BARCODE"}
        else:
            raise APIException(
                "Incorrect ID type. Must be 'id', 'barcode', 'uuid'"
            )
        res = self.make_request(self.FIND_ROW_BY_ID, payload)
        self.error_check(res, payload, self.FIND_ROW)
        print("successfully found row.")
        return res

    def list_rows(self, pageSize, page=1):
        payload = {"pageSize": pageSize, "page": page}
        res = self.make_request(self.LIST_ROWS, payload)
        self.error_check(res, payload, self.LIST_ROWS)
        print("successfully listed rows.")
        return res

    def delete_rows(self, uuids):
        payload = {"uuids": uuids}
        res = self.make_request(self.DELETE_ROWS, payload)
        self.error_check(res, payload, self.DELETE_ROWS)

    # Supports the common operation of fetching for a certain row, applying some operations, and returning it.
    def find_then_update(self, callback, id, id_type="uuid"):
        data = self.find_row(id, id_type)
        ret = callback(data)
        self.update_rows(ret)

    ##ONLY BARCODES FOR NOW
    def update_parent(self, child_id, parent_id, parent_labsheet):
        payload = {
            "rows": {
                "barcode": child_id,
                "parent": {"labsheet": parent_labsheet, "barcode": parent_id},
            }
        }
        res = self.make_request(self.UPDATE_PARENT, payload)
        self.error_check(res, payload, self.UPDATE_PARENT)
        print("successfully updated parent.")

    def create_children(self, parent_barcode, child_ids):
        payload = {
            "idType": "ID_BARCODE",
            "parent": parent_barcode,
            "children": [{"ID": child, "quantity": 0} for child in child_ids],
        }
        res = self.make_request(self.UPDATE_CHILDREN, payload)
        self.error_check(res, payload, self.UPDATE_CHILDREN)
        print("successfully created children.")


# Give mapping of parent to children barcodes
def create_parent_child(mapping, parent_sheet, child_sheet):
    update_parent_rows = []
    update_child_rows = []
    for parent in mapping:
        children = mapping[parent]
        for child in children:
            update_parent_rows.append(
                {
                    "barcode": child,
                    "parent": {
                        "labsheet": parent_sheet.name,
                        "barcode": parent,
                    },
                }
            )
        update_child_rows.append(
            {
                "barcode": parent,
                "children": [
                    {"labsheet": child_sheet.name, "barcode": child}
                    for child in children
                ],
            }
        )
    res1 = parent_sheet.make_request(
        parent_sheet.UPDATE_CHILDREN, {"rows": update_child_rows}
    )
    time.sleep(1)
    res2 = child_sheet.make_request(
        parent_sheet.UPDATE_PARENT, {"rows": update_parent_rows}
    )
    parent_sheet.error_check(
        res1, {"rows": update_child_rows}, parent_sheet.UPDATE_PARENT
    )
    child_sheet.error_check(
        res2, {"rows": update_parent_rows}, child_sheet.UPDATE_CHILDREN
    )


def find_values_by_header(res, header):
    if "rows" in res and "headers" in res:
        values = []
        for row in res["rows"]:
            values.append(row[res["headers"].index(header)])
        return values
    else:
        raise APIException(
            "Incorrect response format. Must have 'rows' and 'headers' keys."
        )


def array_to_dict(header, data):
    return dict(zip(header, data))


def dict_to_array(data):
    if type(data) is list:
        return {
            "headers": list(data[0].keys()),
            "rows": [list(row.values()) for row in data],
        }
    return {"headers": list(data.keys()), "rows": list(data.values())}
