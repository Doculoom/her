def make_output_instructions(model):
    fields = []
    for name, field in model.model_fields.items():
        typ = field.annotation
        if hasattr(typ, "__name__"):
            typ_str = typ.__name__
        else:
            typ_str = str(typ)
        if typ_str == "bool":
            val = "true or false"
        elif typ_str in ["str", "Optional[str]"]:
            val = "string or null"
        elif typ_str.startswith("List") or typ_str.startswith("list"):
            val = "[...]"
        else:
            val = typ_str
        fields.append(f'  "{name}": {val}')
    json_example = "{\n" + ",\n".join(fields) + "\n}"
    return f"""
---

**Output instructions:**

Respond ONLY with a valid JSON object matching this schema:

{json_example}

- Do not include any extra explanation, greeting, or formatting—return ONLY the JSON.
- If you are unable to answer, still respond with all required fields using null or default values.

Note: If recent information is needed, use search to provide an accurate answer
"""


def build_prompt_with_output_instructions(template: str, pydantic_model):
    instructions = make_output_instructions(pydantic_model)
    return template + instructions
