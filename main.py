import json
from keyword import kwlist as reserved_words
from pathlib import Path

# Model types
BASIC_MODELS = "BasicModels"
COMPLEX_MODELS = "ComplexModels"

# Special detections
ENUM = "Enum"
DATETIME = "datetime"
REF = "$ref"
BASE_MODEL = "Base model"

# === File paths ===

# Output dir

# Enter path from root folder (root is implied, not stated)
# For example, [root] - Files - Models should be Path("Files") / "Models"
OUTPUT_DIR = Path("Files")

BASIC_MODELS_FILE = OUTPUT_DIR / f"{BASIC_MODELS}.py"
COMPLEX_MODELS_FILE = OUTPUT_DIR / f"{COMPLEX_MODELS}.py"

# Swagger from web
# TODO ! Тащить сваггер из сети

# Swagger input dir

# Enter path from root folder (root is implied, not stated)
# For example, [root] - Files should be Path("Files")
SWAGGER_DIR = Path("Files")

SWAGGER_FILE = SWAGGER_DIR / "known_swagger2.json"

# Type converter
TYPES = {"string": "str", "integer": "int", "number": "int", "boolean": "bool"}

# Required imports
IMPORTS = {
    BASIC_MODELS: {
        ENUM: "from enum import Enum\n",
        DATETIME: "from datetime import datetime\n",
        BASE_MODEL: "from pydantic import BaseModel, Field\n",
    },
    COMPLEX_MODELS: f"from {'.'.join(OUTPUT_DIR.parts)}.{BASIC_MODELS} import *\n",
}

# Misc
INDENT = "    "

# Custom model
NAME = "Name"
ATTRIBUTES = "Attributes"

CUSTOM_MODEL = {
    NAME: "CustomModel",
    ATTRIBUTES: {
        "allow_population_by_field_name": True,
        "arbitrary_types_allowed": True,
        "use_enum_values": True,
    },
}


class Application:
    def __init__(self):
        self.special_detections = {ENUM: False, DATETIME: False}
        self.model = []
        self.models = {BASIC_MODELS: [], COMPLEX_MODELS: []}
        self.swagger = self.open_swagger_file(SWAGGER_FILE)

        for schema_name, schema in self.swagger["components"]["schemas"].items():
            self.extract_model(schema_name, schema)

        self.record_models_to_files()

    # === PRIVATE METHODS ==============================================================

    @staticmethod
    def open_swagger_file(file_path):
        with open(file_path, "r") as f:
            return json.load(f)

    def extract_model(self, schema_name, schema):
        self.model = []
        self.get_class_definition(schema_name, schema)
        self.get_attributes(schema)
        self.send_model_to_proper_category()

    def get_class_definition(self, schema_name, schema):
        if "enum" in schema:
            definition = f"class {schema_name}({TYPES[schema['type']]}, Enum):"

            self.special_detections[ENUM] = True

        else:
            definition = f"class {schema_name}({CUSTOM_MODEL[NAME]}):"

        self.model.append(definition)

    def get_attributes(self, schema):
        need_reference = False

        attributes = []

        if "enum" in schema:

            for field in schema["enum"]:
                indices = [i for i, c in enumerate(field) if c.isupper() and i != 0]
                field_upper = enumerate(field.upper())
                n = [f"_{c}" if index in indices else c for index, c in field_upper]
                name = "".join(n)

                attributes.append(f'{INDENT}{name} = "{field}"')

            attributes = sorted(attributes)

        else:

            for attribute, p_value in schema["properties"].items():

                attribute_raw = None
                need_alias = []

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
                    data_type = DATETIME

                    self.special_detections[DATETIME] = True

                # A list of other models
                elif p_value["type"] == "array" and REF in p_value["items"]:
                    data_type = f'list[{p_value["items"][REF].split("/")[-1]}]'
                    need_reference = True

                # A list of some datatype
                elif p_value["type"] == "array":
                    data_type = f'list[{TYPES[p_value["items"]["type"]]}]'

                # Simple definition
                else:
                    data_type = TYPES[p_value["type"]]

                # Check if the model uses reserved words in Python
                if attribute in reserved_words:
                    attribute_raw = attribute
                    need_alias.append(attribute_raw)
                    attribute = f"{attribute}_"

                # Add attribute to the model
                attribute = f"    {attribute}: {data_type}"

                is_nullable = "nullable" in p_value
                is_read_only = "readOnly" in p_value

                if (is_nullable or is_read_only) and need_alias:
                    attribute = f'{attribute} = Field(None, alias="{attribute_raw}")'

                elif need_alias:
                    attribute = f'{attribute} = Field(alias="{attribute_raw}")'

                elif is_nullable or is_read_only:
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

        if not Path(proper_file).exists():
            Path(proper_file).touch()

        with open(proper_file, "w") as output:

            if category == BASIC_MODELS:
                self.write_required_imports(output, category)
                self.write_custom_model(output)

            else:
                output.write(IMPORTS[category])

            for model in self.models[category]:
                output.write("\n\n\n")
                output.writelines("\n".join(model))

    def write_required_imports(self, output, category):
        for import_name, import_required in self.special_detections.items():
            if import_required:
                output.write(IMPORTS[category][import_name])

        output.write(IMPORTS[category][BASE_MODEL])

    @staticmethod
    def write_custom_model(output):
        output.write(
            f"\n\nclass {CUSTOM_MODEL[NAME]}(BaseModel):" f"\n{INDENT}class Config:\n"
        )

        for attribute, attribute_value in CUSTOM_MODEL[ATTRIBUTES].items():
            output.write(f"{INDENT}{INDENT}{attribute} = {attribute_value}\n")


if __name__ == "__main__":
    Application()
