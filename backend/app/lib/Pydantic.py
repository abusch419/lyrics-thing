from pydantic import ConfigDict
from pydantic.alias_generators import to_camel


# Because we convert our fields to camel case when serializing, Pydantic generates incorrect titles, for example, `Rawname`.
# The tool we use to generate typescript type definitions uses those titles to generate type aliases, so instead of our `rawName` field having the type string it has the type `Rawname` which is an alias for string.
# However, if we delete all the titles, we don't end up with incorrectly formatted type aliases.
def remove_titles(schema):
    if isinstance(schema, dict):
        # Create a copy to avoid modifying the dictionary during iteration
        keys_to_check = list(schema.keys())
        for key in keys_to_check:
            if key == "title":
                del schema[key]
            else:
                remove_titles(schema[key])
    elif isinstance(schema, list):
        # Recurse into each item in the list
        for item in schema:
            remove_titles(item)


standard_model_config = ConfigDict(
    alias_generator=to_camel, populate_by_name=True, json_schema_extra=remove_titles
)
