import pandas as pd


class ShcSoftSensor:
    def transform(self, raw_data: pd.DataFrame) -> pd.DataFrame:
        return raw_data

    def calculate(self, transformed_data: pd.DataFrame) -> pd.DataFrame:
        return transformed_data
