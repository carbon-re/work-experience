import typing
import pandas as pd


class SoftSensor(typing.Protocol):
    def transform(self, raw_data: pd.DataFrame) -> pd.DataFrame: ...

    def calculate(self, transformed_data: pd.DataFrame) -> pd.DataFrame: ...
