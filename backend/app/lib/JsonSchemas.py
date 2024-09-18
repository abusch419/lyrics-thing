import json
from pydantic import BaseModel
from app.lib.Pydantic import standard_model_config


# We include all of our API types in this class so that we can generate a JSON schema for them.
class HelloWorldResponse(BaseModel):
    message: str

    model_config = standard_model_config


class ApiTypes(BaseModel):
    hello_world_response: HelloWorldResponse

    model_config = standard_model_config


def save_all():
    model_schema = ApiTypes.model_json_schema()
    file_name = "../frontend/src/lib/ApiTypes.json"
    with open(file_name, "w") as f:
        json.dump(model_schema, f, indent=2)
