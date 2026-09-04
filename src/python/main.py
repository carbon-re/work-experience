import datetime as dt

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, r2_score, root_mean_squared_error
from sklearn.model_selection import train_test_split

# TODO: load the plant data.
#
from src.python.load_data.clickhouse import ClickHouseConfig, PlantDataLoader

features = [
    "g_k_pyro_temp",
    "p_k_torque",
    "p_c_grate_speed",
    "g_ph_cy4_gol_temp",
    "g_ph_cy3_gol_temp",
    "g_ph_gol_temp",
    "f_k_coal_tput",
    "g_pc_pyro_temp",
    "g_pc_wall_scc_temp4",
    "s_ph_sil_cao",
    "s_ph_sil_al2o3",
    "s_ph_sil_fe2o3",
    "s_ph_sil_sio2"
]
target = "p_k_power"
columns_to_load = features + [target]


DEFAULT_START = dt.datetime(year=2022, month=1, day=1)
DEFAULT_END = dt.datetime(year=2023, month=1, day=1)


def data_load(
    start: dt.datetime = DEFAULT_START,
    end: dt.datetime = DEFAULT_END,
) -> pd.DataFrame:
    loader = PlantDataLoader(ClickHouseConfig.from_environment())
    data = loader.load(
        table="mapped",
        features=columns_to_load,
        start=start,
        end=end,
    )

    return data


def cleaning(data: pd.DataFrame) -> pd.DataFrame:
    data = data.fillna(0)
    return data


def sliced_data(data: pd.DataFrame) -> list[pd.DataFrame]:
    data["month"] = data["timestamp"].dt.to_period("M")
    list_of_dataframes = [group for _, group in data.groupby("month")]
    return list_of_dataframes


def train_model(
    data: pd.DataFrame,
    test_size: float = 0.2,
    selected_features: list[str] | None = None,
) -> tuple[LinearRegression, pd.DataFrame, pd.Series]:
    X = data[selected_features or features]
    y = data[target]
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=test_size, shuffle=False)
    model = LinearRegression()
    model.fit(X_train, y_train)
    print(X_train.head())
    print(X_test.head())
    print(y_train.head())
    return model, X_test, y_test


def analysisData(X_test, y_test, model) -> tuple[np.ndarray, float]:
    predictions = model.predict(X_test)
    MAE = mean_absolute_error(y_test, predictions)
    print(f"Mean absolute error: {MAE} kcal/kg")
    print(f"RMSE: {root_mean_squared_error(y_test, predictions):.1f} kcal/kg")
    print(f"R squared: {r2_score(y_test, predictions):.2f}")
    print(type(predictions))
    print(len(predictions))

    # plt.scatter(data["f_k_coal_tput"], data["p_k_power"])
    # plt.xlabel("f_k_coal_tput")
    # plt.ylabel("p_k_power")
    # plt.title("f_k_coal_tput vs p_k_power")
    # plt.show()
    #
    # plt.scatter(y_test, predictions)
    # plt.xlabel("Actual")
    # plt.ylabel("Predicted")
    # plt.title("Actual vs Predicted")
    # plt.show()
    #
    # plt.hist(predictions, bins=50)
    # plt.xlabel("Predicted")
    # plt.ylabel("Frequency")
    # plt.show()
    #
    #
    # plt.boxplot(predictions)
    # plt.xlabel("Feature")
    # plt.ylabel("Target")
    # plt.show()

    return predictions, MAE


if __name__ == "__main__":
    data = data_load()
    data = cleaning(data)
    list_of_dataframes = sliced_data(data)

    list_of_months = []
    MAEs = []

    for data in list_of_dataframes:
        model, X_test, y_test = train_model(data)
        predictions, MAE = analysisData(X_test, y_test, model=model)
        MAEs.append(MAE)
        list_of_months.append(data["month"].iloc[0])

    x_values = [m.to_timestamp() for m in list_of_months]

    print(len(MAEs))
    print(len(list_of_months))

    plt.scatter(x_values, MAEs)
    plt.xlabel("Month")
    plt.ylabel("MAE")
    plt.title("MAEs vs Month")
    plt.show()
