import json
import os.path

from pathlib import Path

MODELS_FILE = os.path.join("Files", "models.py")
TYPES = {"string": "str"}


class Application:
    def __init__(self):
        with open(os.path.join("Files", "known_swagger1.json"), "r") as f:
            swagger = json.load(f)

        if not os.path.exists(MODELS_FILE):
            Path(MODELS_FILE).touch()

        schemas = swagger["components"]["schemas"]

        for schema, value in schemas.items():

            if "enum" in value:
                model = []

                # Get class definition
                definition = f"class {schema}({TYPES[value['type']]}, Enum):"
                model.append(definition)

                # Get class attributes
                attributes = []

                for field in value["enum"]:
                    indices = [i for i, c in enumerate(field) if c.isupper() and i != 0]
                    field_upper = enumerate(field.upper())
                    n = [f"_{c}" if index in indices else c for index, c in field_upper]
                    name = "".join(n)

                    attributes.append(f'    {name} = "{field}"')

                attributes = sorted(attributes)
                model += attributes

                # Write class to file
                with open(MODELS_FILE, "a") as output:
                    output.writelines("\n".join(model))
                    output.write("\n\n\n")

            else:
                a = 1

            a = 1

        a = 1


if __name__ == "__main__":
    Application()
