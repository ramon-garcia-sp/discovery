from datetime import datetime

def deserialized(data: list, keys: list) -> list:
    response = []
    for item in data:
        response_item = {}
        for key in keys:
            try:
                value = getattr(item, key)
                if isinstance(value, datetime):
                    value = value.isoformat()
                response_item[key] = getattr(item, key)
            except (AttributeError, TypeError) as error:
                raise(f"Missing key {key} expected in item {item}: {error}")
        response.append(response_item)
    return response