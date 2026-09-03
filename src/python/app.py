import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from src.python.main import data_load, cleaning, sliced_data, train_model, analysisData

st.set_page_config(page_title="Dashboard!!!")
st.title("Kim's dashboard")
st.markdown("This is my first dashboard **ever**. I've never done anything like this before.")
st.info("The whole project wouldn't be done without Lizzie's help" )

def load_and_clean() -> pd.DataFrame:
    data = data_load()
    data = cleaning(data)
    list_of_dfs = sliced_data(data)
    return list_of_dfs

def run(list_of_dfs: pd.DataFrame) -> tuple[list, list, list, list]:
    months = []
    maes = []
    predictions = []
    actuals = []


    for month_df in list_of_dfs:
        model, X_test, y_test = train_model(month_df)
        prediction, mae = analysisData(X_test, y_test, model=model)
        months.append(month_df["month"].iloc[0])
        maes.append(mae)
        predictions.append(prediction)
        actuals.append(y_test)

    months = [m.to_timestamp() for m in months]

    return months, maes, actuals, predictions


def plot_scatter(a, b):
    plot = plt.scatter(a, b)
    st.pyplot(plot)

def main():
    list_of_dfs = load_and_clean()
    months, maes, actuals, predictions = run(list_of_dfs)
    plot_scatter(months, maes)

main()