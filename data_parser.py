import json
import pandas as pd


class DataFile:
    def __init__(self, path: str, file_type: str):
        self.path = path
        self.file_type = file_type
        self.data = None

    def parse(self):
        if self.file_type in ('txt', 'csv'):
            self.data = pd.read_csv(self.path)
        elif self.file_type in ('xls', 'xlsx'):
            self.data = pd.read_excel(self.path)
        else:
            raise ValueError(f"Unsupported file type: {self.file_type}")

    def to_json(self) -> str:
        if self.data is None:
            self.parse()
        return self.data.to_json(orient='records')


