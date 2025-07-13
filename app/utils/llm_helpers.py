def make_output_instructions(pydantic_model):
    fields = []
    for name, field in pydantic_model.model_fields.items():
        typ = field.annotation
        typ_name = getattr(typ, "__name__", None) or str(typ)
        if typ_name == "bool":
            val = "true or false"
        elif typ_name in ("str", "builtins.str"):
            val = "string"
        elif "Optional" in typ_name or "NoneType" in typ_name:
            val = "string or null"
        elif typ_name.startswith(("list", "List", "typing.List")):
            val = "[...]"
        else:
            val = typ_name
        fields.append(f'  "{name}": {val}')
    json_example = "{\n" + ",\n".join(fields) + "\n}"
    return f"""
---

**Output instructions:**

Respond ONLY with a valid JSON object matching this schema:

{json_example}

- Do not include any extra explanation, greeting, or formatting—return ONLY the JSON.
- If you are unable to answer, still respond with all required fields using null or default values.

Note: If up-to-date info like news or stock prices is needed, feel free to use Google Search.
"""


def build_prompt_with_output_instructions(template, pydantic_model):
    if not isinstance(template, str):
        template = str(template)
    return template + make_output_instructions(pydantic_model)
