import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from src.python.main import data_load, cleaning, sliced_data, train_model, analysisData
from sklearn.metrics import r2_score, mean_absolute_error, mean_squared_error


st.set_page_config(page_title="Dashboard!!!")
st.title("Kim's dashboard")
st.markdown("This is my first dashboard **ever**. I've never done anything like this before.")
st.info("The whole project wouldn't be done without Lizzie's help" )




def load_and_clean() -> pd.DataFrame:
    data = data_load()
    data = cleaning(data)
    return data

def slice(data):
    dfs_grouped_by_month = sliced_data(data)
    return dfs_grouped_by_month

def run(dfs_grouped_by_month: pd.DataFrame) -> tuple[list, list, list, list]:
    months = []
    maes = []
    predictions: list[list] = []
    actuals: list[pd.DataFrame] = []


    for month_df in dfs_grouped_by_month:
        model, X_test, y_test = train_model(month_df)
        prediction, mae = analysisData(X_test, y_test, model=model)
        months.append(month_df["month"].iloc[0])
        maes.append(mae)
        predictions.append(prediction)
        actuals.append(y_test)

    months = [m.to_timestamp() for m in months]

    return months, maes, actuals, predictions


def plot_scatter(a, b, a_label, b_label, alpha=0.5, color='red'):
    fig, ax = plt.subplots()
    ax.scatter(a, b, alpha=alpha, color=color)
    ax.set_xlabel(a_label)
    ax.set_ylabel(b_label)
    fig.autofmt_xdate()
    st.pyplot(fig)

def plot_line(actuals, predictions):
    actuals = list(actuals)
    predictions = list(predictions)

    if len(actuals) != len(predictions):
        st.error(
            f"Actuals and predictions have different lengths: "
            f"{len(actuals)} vs {len(predictions)}"
        )
        return
    x = range(len(actuals))

    fig, ax = plt.subplots(figsize=(10, 5))
    ax.plot(
        x,
        actuals,
        label='Actual values',
        color='blue',
        linewidth=1
    )
    ax.plot(
        x,
        predictions,
        label='Predicted values',
        color='red',
        linewidth=1
    )
    ax.set_xlabel('Test sample')
    ax.set_ylabel('Values')
    ax.set_title('Actual values vs predicted values')
    ax.legend()
    ax.grid(True, alpha=0.3)
    st.pyplot(fig)


def run_actuals_predictions(data):
    model, X_test, y_test = train_model(data)
    prediction, mae = analysisData(X_test, y_test, model=model)
    return prediction, y_test, mae

def calculate_metrics(actuals, predictions):
    r2 = r2_score(actuals, predictions)
    mae = mean_absolute_error(actuals, predictions)
    rmse = mean_squared_error(actuals, predictions) ** 0.5

    return r2, mae, rmse

def main():

    data = load_and_clean()

    dfs_grouped_by_month = slice(data)


    # ------------------------------------
    # FIRST GRAPH: MAE VS MONTH
    # ------------------------------------

    st.subheader("A fancy diagram")

    st.markdown(
        "This diagram represents MAEs vs months"
    )

    months, maes, actuals, list_of_predictions = run(
        dfs_grouped_by_month
    )

    plot_scatter(
        months,
        maes,
        'Months',
        'MAEs'
    )


    # ------------------------------------
    # SECOND GRAPH: ACTUAL VS PREDICTED
    # ------------------------------------

    st.subheader("A fancy diagram No.2!!!")

    st.markdown(
        "This diagram represents actual results vs predicted values"
    )
    predictions, y_test, mae = run_actuals_predictions(data)

    # Plot the two lines
    plot_line(
        y_test,
        predictions
    )
    # Calculate R² and RMSE
    r2 = r2_score(y_test, predictions)
    rmse = mean_squared_error(y_test, predictions) ** 0.5

    # Display metrics
    st.subheader('Some accuracy stats')
    st.markdown('R² is the fraction of the variation the model explains. 1 is perfect, 0 means that this model is not better than guessing the average. ')
    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric(
            "R²",
            f"{r2:.2f}"
        )

    with col2:
        st.metric(
            "MAE",
            f"{mae:.2f} kcal/kg"
        )

    with col3:
        st.metric(
            "RMSE",
            f"{rmse:.2f}x kcal/kgx"
        )
main()
