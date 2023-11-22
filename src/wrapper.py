from typing import List, Literal

import json
import requests
import time

PROD_URL = "https://api.scispot.io/v2"


class APIException(Exception):
    def __init__(self, message, endpoint, payload, res):
        self.message = message + "\n"
        self.message += "Request: " + endpoint + "\n"
        annonimized_payload = {
            k: v if "api" not in k else "*" * len(v)
            for k, v in payload.items()
        }
        self.message += str(json.dumps(annonimized_payload, indent=2)) + "\n"
        self.message += "Response: " + str(json.dumps(res, indent=2)) + "\n"
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
    ## Q: What are the non supported column types? - JSP
    def create(self, header_names, header_types):
        """Creates a labsheet."""
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
        """Makes a request to the API.

        This is meant to be internal, for most cases you should use the
        other methods (e.g. add_rows, update_rows, etc).
        """
        payload["apiKey"] = self.api_key
        payload["manager"] = self.name
        payload["labsheet"] = self.name
        if self.verbose:
            print(self.BASE_URL + endpoint)
            # This will print the api key in plaintext...
            # which is a security vulnerability ... so lets not do that ...
            # print(str(json.dumps(payload, indent=4)))
            public_payload = {
                k: "*" * len(v) if "api" in k else v
                for k, v in payload.items()
            }

            print(str(json.dumps(public_payload, indent=4)))
        req = requests.post(url=self.BASE_URL + endpoint, json=payload)
        res = json.loads(req.text)
        return res

    def error_check(self, res, payload, endpoint) -> None:
        """Checks for errors in the response.

        It reads the response and raises a python error if an API
        error is detected.
        """
        if isinstance(res, dict):
            if "success" not in res:
                raise APIException(
                    "An error occured: ", endpoint, payload, res
                )

            # When would this happen?
            # why is this not consistent?
            if res["success"] == "false" or not res["success"]:
                raise APIException(
                    "An error occured: ", endpoint, payload, res
                )
        elif isinstance(res, list):
            """
            Example response from the update_rows endpoint:
            [
            {
                "ID": "98",
                "updatedRows": [
                {
                    "uuid": "50738ad7-c7e0-44da-9a29-3c0dec898075",
                    "success": "true"
                }
                ]
            }
            ]
            """
            for row in res:
                if "updatedRows" in row:
                    for updated_row in row["updatedRows"]:
                        if "success" not in updated_row:
                            raise APIException(
                                "An error occured: ", endpoint, payload, res
                            )

                        if (
                            updated_row["success"] == "false"
                            or not updated_row["success"]
                        ):
                            raise APIException(
                                "An error occured: ",
                                endpoint,
                                payload,
                                res,
                            )
                    return

                if "success" not in row:
                    raise APIException(
                        "An error occured: ", endpoint, payload, res
                    )

                if row["success"] == "false" or not row["success"]:
                    raise APIException(
                        "An error occured: ", endpoint, payload, res
                    )

    def add_rows(self, rows: List[List[str]]):
        """Adds rows to the table (labsheet).

        Parameters
        ----------
        rows : list of lists
            List of rows to add. Each row is a list of values.
            For example:
            --data '{
                "apiKey": "12345678-abcd-9012-efgh-345678901234",
                "manager": "Elisa Data",
                "rows": [
                    [
                        "ID-15",
                        "Standard",
                        "50mL",
                        "A",
                        "09/03/2022",
                        "Hazardous",
                        "Unknown",
                        "North Lab > Well Plate 23",
                        "134-amf"
                    ]
                ]}'

        Notes
        -----
        The column order is determined by the order of the columns in the labsheet.
        Which can be queried using the get_headers()["headers"] method.
        Having said that there are some oddities with the API, where the first column
        is skipped (thus not passed when adding rows), I am not sure what other columns
        are generated.
        """
        payload = {"rows": rows}
        res = self.make_request(self.ADD_ROWS, payload)
        print(res)
        self.error_check(res, payload, self.ADD_ROWS)
        print("successfully added rows.")
        return [row["uuid"] for row in sorted(res, key=lambda x: x["row"])]

    def get_headers(self) -> List[str]:
        """Returns the headers of the labsheet."""
        res = self.list_rows(0, 0)
        return res["headers"]

    # Usually, the uuid, stays packaged with the rest of the rows
    def update_rows(self, rows):
        payload = {"rows": [{"uuid": row[0], "data": row[1:]} for row in rows]}
        res = self.make_request(self.UPDATE_ROWS, payload)
        self.error_check(res, payload, self.UPDATE_ROWS)
        print("successfully updated rows.")
        return res

    def update_rows_by_id(self, rows: List[dict]):
        """Updates rows by id.

        Parameters
        ----------
        rows : list of dicts
            List of rows to update. Each row is a dict of values.
            For example (from the scispot docs):
            [{}, {"ID": "20c20", "Quantity": "78", "Comp": "c24"}]

        Notes from the docs
        -------------------
        curl --location 'https://api.scispot.io/v2/labsheets/update-rows-by-id' \
            --header 'Content-Type: application/json' \
            --data '{
            "apiKey": "12345678-abcd-9012-efgh-345678901234",
            "manager": "Materials Manager",
            "rows": [
                {
                "ID": "20c20",
                "Quantity": "78",
                "Comp": "c24"
                }
            ]
            }'
        """
        payload = {"rows": rows}
        res = self.make_request(self.UPDATE_ROWS_BY_ID, payload)
        self.error_check(res, payload, self.UPDATE_ROWS_BY_ID)
        print("successfully updated rows.")
        return res

    def find_row(self, id, id_type: Literal["uuid", "id", "barcode"] = "uuid"):
        """Finds a row by id.

        Examples
        --------
        >>> ls.find_row("b543a089-dee2-42f0-a750-91effe49841c", id_type="uuid")
        {"headers": [...], "row": [...], "success": "true"}
        >>> ls.find_row("1102", id_type="barcode")
        {"rows": [[...]], "headers": [...], "success": True}
        # Note that the response from uuid is a single list,
        # whilst the response from barcode is a list of lists.
        """
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
        # Q: What is the max page size? - JSP
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
