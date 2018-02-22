import json


string = "{'a':123"

try:
    string_dump = json.dumps(string)
except Exception as e:
    print(e)

try:
    string_load = json.loads(string_dump)
except Exception as e:
    print(e)


print(string_dump)
print(string_load)

