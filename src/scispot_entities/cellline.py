from typing import List
from dataclasses import dataclass
from pydantic import BaseModel, Field
import datetime

# I will use this in the future to make the arrey from the
# model. (the array is what I need to add rows to the labsheet)
CELL_CULTURE_HEADER = [
    "UUID",
    "Registry ID",
    "Cell Type",
    "Name",
    "Culture State",
    "Stock Type",
    "Mycoplasma Test",
    "Passage",
    "Supplier",
    "Supplier Batch ID",
    "Received Date",
    "Parent Culture",
    "Seeding Cell Viability",
    "Number of Cells Seeded",
    "Volume (mL)",
    "Experiment Condition",
    "Treatment Compound Stock ID",
    "Treatment Dose",
    "Treatment Dose Unit",
    "Child Cultures",
    "Freezing Media",
    "Freezing Protocol ID",
    "Culture Protocol ID",
    "Treatment Protocol ID",
    "Prepared By",
    "Preparation Date",
    "Storage Location",
    "Record Creator",
    "Record Created",
]


class CellCulture(BaseModel):
    """A cell culture.

    Right now the python representation maintains just the
    scispot representation (where everything is a string).

    In the near future my idea is to make represent multiple
    elements correctly (e.g. date, datetime, integers, validate
    units... that kind of stuff).
    """

    uuid: str = Field(str, alias="UUID")
    record_created: str = Field(str, alias="Record Created")
    registry_id: str = Field(alias="Registry ID")
    cell_type: str = Field(alias="Cell Type")
    name: str = Field(alias="Name")
    culture_state: str = Field(alias="Culture State")
    stock_type: str = Field(alias="Stock Type")
    mycoplasma_test: str = Field(alias="Mycoplasma Test")
    passage: str = Field(alias="Passage")
    supplier: str = Field(alias="Supplier")
    supplier_batch_id: str = Field(alias="Supplier Batch ID")
    received_date: str = Field(alias="Received Date")
    parent_culture: str = Field(alias="Parent Culture")
    seeding_cell_viability: str = Field(alias="Seeding Cell Viability")
    number_of_cells_seeded: str = Field(alias="Number of Cells Seeded")
    volume: str = Field(alias="Volume (mL)")
    experiment_condition: str = Field(alias="Experiment Condition")
    treatment_compound_stock_id: str = Field(
        alias="Treatment Compound Stock ID"
    )
    treatment_dose: str = Field(alias="Treatment Dose")
    treatment_dose_unit: str = Field(alias="Treatment Dose Unit")
    child_cultures: str = Field(alias="Child Cultures")
    freezing_media: str = Field(alias="Freezing Media")
    freezing_protocol_id: str = Field(alias="Freezing Protocol ID")
    culture_protocol_id: str = Field(alias="Culture Protocol ID")
    treatment_protocol_id: str = Field(alias="Treatment Protocol ID")
    prepared_by: str = Field(alias="Prepared By")
    preparation_date: str = Field(alias="Preparation Date")
    storage_location: str = Field(alias="Storage Location")
    record_creator: str = Field(alias="Record Creator")

    class Config:
        allow_population_by_field_name = True

    @classmethod
    def from_response(cls, response) -> List["CellCultureResponse"]:
        """Create a list of CellCulture from a response.

        This uses the response from the labsheet wrapper
        to create a list of CellCulture objects.

        Usage
        -----
        >>> # ls = Labsheet(
        >>> #     name="Cell Culture",
        >>> #     api_key=os.environ.get("SCISPOT_KEY"),
        >>> #     verbose=True,
        >>> #     base="prod",
        >>> # )
        >>> # response = ls.list_rows(2, 2)
        >>> # CellCulture.from_response(response)
        """

        # The response has the form:
        # {
        #     'headers': [...],
        #     'rows': [[...], [...]],
        #     'success': 'true'
        # }

        data = [
            {k: v for k, v in zip(response["headers"], row)}
            for row in response["rows"]
        ]
        return [CellCulture(**row) for row in data]
