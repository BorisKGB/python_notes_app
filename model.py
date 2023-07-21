import json
import os.path
from datetime import datetime


# adapt custom parser solutions for datetime from
# https://stackoverflow.com/questions/8793448/how-to-convert-to-a-python-datetime-object-with-json-loads
class DateTimeEncoder(json.JSONEncoder):
    # Override the default method
    def default(self, obj):
        if isinstance(obj, datetime):
            return 'datetime_' + obj.isoformat()
        return json.JSONEncoder.default(self, obj)


def datetime_parser(dct: dict) -> dict:
    parsed_dct = {}
    for k, v in dct.items():
        if isinstance(v, str) and v.startswith('datetime_'):
            try:
                parsed_dct[k] = datetime.fromisoformat(v.split('_', 1)[1])
            except ValueError:
                parsed_dct[k] = v
        elif isinstance(k, str) and k.isdigit():
            parsed_dct[int(k)] = v
        else:
            parsed_dct[k] = v
    return parsed_dct


class JsonModel:
    def __init__(self, path: str = "notes.json"):
        self.path = path
        self.data = self.__load()

    def __load(self) -> dict:
        if os.path.isfile(self.path):
            with open(self.path, "r") as json_file:
                return json.load(json_file, object_hook=datetime_parser)
        else:
            return {}

    def __save(self) -> None:
        with open(self.path, "w") as json_file:
            json.dump(self.data, json_file, cls=DateTimeEncoder, indent=2)

    def __next_ident(self) -> int:
        all_ids = self.data.keys()
        if len(all_ids) > 0:
            return max(all_ids) + 1
        else:
            return 0

    def add(self, title: str, msg: str) -> None:
        dt_now = datetime.now()
        self.data[self.__next_ident()] = {
            'title': title,
            'msg': msg,
            'creation_time': dt_now,
            'modification_time': dt_now
        }
        self.__save()

    def delete(self, ident: int) -> None:
        if ident in self.data:
            del self.data[ident]
            self.__save()

    def update(self, ident, title: str | None = None, msg: str | None = None) -> None:
        if ident in self.data:
            if title is not None:
                self.data[ident]['title'] = title
            if msg is not None:
                self.data[ident]['msg'] = msg
            self.data[ident]['modification_time'] = datetime.now()
            self.__save()

    def get(self, ident: int) -> dict | None:
        if ident in self.data:
            return self.data[ident]
        else:
            return None

    def get_all(self) -> dict:
        return self.data


if __name__ == '__main__':
    print("This is internal class, do not run this")
    exit(1)
