import json
import os.path

from pathlib import Path

# Model types
BASIC_MODELS = "Basic models"
COMPLEX_MODELS = "Complex models"

# Special detections
ENUM = "Enum"
DATETIME = "datetime"
REF = "$ref"

# File paths
BASIC_MODELS_FILE = os.path.join("Files", "BasicModels.py")
COMPLEX_MODELS_FILE = os.path.join("Files", "ComplexModels.py")

SWAGGER_FILE = os.path.join("Files", "known_swagger1.json")

# Type converter
TYPES = {"string": "str", "integer": "int", "number": "int", "boolean": "bool"}

# Required imports
# TODO !!!!!!!!!


class Application:
    def __init__(self):
        self.special_detections = {ENUM: False, DATETIME: False}
        self.model = []
        self.models = {BASIC_MODELS: [], COMPLEX_MODELS: []}
        self.swagger = self.open_swagger_file(SWAGGER_FILE)

        for schema_name, schema in self.swagger["components"]["schemas"].items():

            self.extract_model(schema_name, schema)

        self.record_models_to_files()

    def extract_model(self, schema_name, schema):
        self.model = []
        self.get_class_definition(schema_name, schema)
        self.get_attributes(schema)
        self.send_model_to_proper_category()

    @staticmethod
    def open_swagger_file(file_path):
        with open(file_path, "r") as f:
            return json.load(f)

    def get_class_definition(self, schema_name, schema):
        if "enum" in schema:
            definition = f"class {schema_name}({TYPES[schema['type']]}, Enum):"

            self.special_detections[ENUM] = True

        else:
            definition = f"class {schema_name}(BaseModel):"  # TODO CustomModel?

        self.model.append(definition)

    def get_attributes(self, schema):
        attributes = []

        if "enum" in schema:

            for field in schema["enum"]:
                indices = [i for i, c in enumerate(field) if c.isupper() and i != 0]
                field_upper = enumerate(field.upper())
                n = [f"_{c}" if index in indices else c for index, c in field_upper]
                name = "".join(n)

                attributes.append(f'    {name} = "{field}"')

            attributes = sorted(attributes)

        else:

            need_reference = False

            for attribute, p_value in schema["properties"].items():

                # Reference to a different model
                if REF in p_value:
                    data_type = p_value[REF].split("/")[-1]

                    need_reference = True

                # String, but really a datetime
                elif (
                    p_value["type"] == "string"
                    and "format" in p_value
                    and p_value["format"] == "date-time"
                ):
                    data_type = "datetime"

                    self.special_detections[DATETIME] = True

                # A list of other models
                elif p_value["type"] == "array" and REF in p_value["items"]:
                    data_type = f'list[{p_value["items"][REF].split("/")[-1]}]'

                # A list of some datatype
                elif p_value["type"] == "array":
                    data_type = f'list[{TYPES[p_value["items"]["type"]]}]'

                # Simple definition
                else:
                    data_type = TYPES[p_value["type"]]

                attribute = f"    {attribute}: {data_type}"

                if "nullable" in p_value:
                    attribute = f"{attribute} = None"

                attributes.append(attribute)

            if need_reference:
                attributes.append(REF)

        self.model += attributes

    def send_model_to_proper_category(self):
        category = BASIC_MODELS

        if self.model[-1] == REF:
            category = COMPLEX_MODELS
            del self.model[-1]

        self.models[category].append(self.model.copy())

    def record_models_to_files(self):
        self.record_base_models()
        self.record_complex_models()

    def record_base_models(self):
        self.record_model_category_to_file(BASIC_MODELS)

    def record_complex_models(self):
        self.record_model_category_to_file(COMPLEX_MODELS)

    def record_model_category_to_file(self, category):
        file = {BASIC_MODELS: BASIC_MODELS_FILE, COMPLEX_MODELS: COMPLEX_MODELS_FILE}
        proper_file = file[category]

        if not os.path.exists(proper_file):
            Path(proper_file).touch()

        for import_name, import_required in self.special_detections:
            if import_required:
                a = 1

        for model in self.models[category]:
            a = 1

        # with open(MODELS_FILE, "a") as output:
        #     output.writelines("\n".join(model))
        #     output.write("\n\n\n")


if __name__ == "__main__":
    Application()
