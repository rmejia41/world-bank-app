from dash import Dash, html, dcc, Input, Output, State
import plotly.express as px
import dash_bootstrap_components as dbc
import pandas as pd
from pandas_datareader import wb


app = Dash(__name__, external_stylesheets=[dbc.themes.CERULEAN])
server = app.server

indicators = {
    "SH.TBS.INCD": "Incidence of tuberculosis (per 100,000 people)",
    "EN.URB.MCTY.TL.ZS": "Population in urban agglomerations of more than 1 million (% of total population)",
    "EG.ELC.ACCS.ZS": "Access to electricity (% of population)",
}

# get country name and ISO id for mapping on choropleth
countries = wb.get_countries()
countries["capitalCity"].replace({"": None}, inplace=True)
countries.dropna(subset=["capitalCity"], inplace=True)
countries = countries[["name", "iso3c"]]
countries = countries[countries["name"] != "Kosovo"]
countries = countries.rename(columns={"name": "country"})


def update_wb_data():
    # Retrieve specific world bank data from API
    df = wb.download(
        indicator=(list(indicators)), country=countries["iso3c"], start=2016, end=2021
    )
    df = df.reset_index()
    df.year = df.year.astype(int)

    # Add country ISO3 id to main df
    df = pd.merge(df, countries, on="country")
    df = df.rename(columns=indicators)
    return df


app.layout = dbc.Container(
    [
        dbc.Row(
            dbc.Col(
                [
                    html.H1(
                        "Comparison of World Bank Country Data",
                        style={"textAlign": "center"},
                    ),
                    dcc.Graph(id="my-choropleth", figure={}),
                ],
                width=12,
            )
        ),
        dbc.Row(
            dbc.Col(
                [
                    dbc.Label(
                        "Select Data Set:",
                        className="fw-bold",
                        style={"textDecoration": "underline", "fontSize": 20},
                    ),
                    dcc.RadioItems(
                        id="radio-indicator",
                        options=[{"label": i, "value": i} for i in indicators.values()],
                        value=list(indicators.values())[0],
                        inputClassName="me-2",
                    ),
                ],
                width=6,
            )
        ),
        dbc.Row(
            [
                dbc.Col(
                    [
                        dbc.Label(
                            "Select Years:",
                            className="fw-bold",
                            style={"textDecoration": "underline", "fontSize": 20},
                        ),
                        dcc.RangeSlider(
                            id="years-range",
                            min=2016,
                            max=2021,
                            step=1,
                            value=[2016, 2017],
                            marks={
                                2016: "2016",
                                2017: "17",
                                2018: "18",
                                2019: "19",
                                2020: "20",
                                2021: "2021"
                            },
                        ),
                        dbc.Button(
                            id="my-button",
                            children="Submit",
                            n_clicks=0,
                            color="primary",
                            className="mt-4",
                            size="md ",
                        ),
                    ],
                    width=6,
                ),
            ]
        ),
        dcc.Store(id="storage", storage_type="session", data={}),
        dcc.Interval(id="timer", interval=1000 * 60, n_intervals=0),
    ]
)


@app.callback(Output("storage", "data"), Input("timer", "n_intervals"))
def store_data(n_time):
    dataframe = update_wb_data()
    return dataframe.to_dict("records")


@app.callback(
    Output("my-choropleth", "figure"),
    Input("my-button", "n_clicks"),
    Input("storage", "data"),
    State("years-range", "value"),
    State("radio-indicator", "value"),
)
def update_graph(n_clicks, stored_dataframe, years_chosen, indct_chosen):
    dff = pd.DataFrame.from_records(stored_dataframe)
    print(years_chosen)

    if years_chosen[0] != years_chosen[1]:
        dff = dff[dff.year.between(years_chosen[0], years_chosen[1])]
        dff = dff.groupby(["iso3c", "country"])[indct_chosen].mean()
        dff = dff.reset_index()

        fig = px.choropleth(
            data_frame=dff,
            locations="iso3c",
            color=indct_chosen,
            scope="world",
            hover_data={"iso3c": False, "country": True},
            labels={
                indicators["SH.TBS.INCD"]: "Incidence of tuberculosis (per 100,000)",
                indicators["EN.URB.MCTY.TL.ZS"]: "% Urban agglomerations",
            },
        )
        fig.update_layout(
            geo={"projection": {"type": "natural earth"}},
            margin=dict(l=50, r=50, t=50, b=50),
        )
        return fig

    if years_chosen[0] == years_chosen[1]:
        dff = dff[dff["year"].isin(years_chosen)]
        fig = px.choropleth(
            data_frame=dff,
            locations="iso3c",
            color=indct_chosen,
            scope="world",
            hover_data={"iso3c": False, "country": True},
            labels={
                indicators["SH.TBS.INCD"]: "Incidence of tuberculosis (per 100,000)",
                indicators["EN.URB.MCTY.TL.ZS"]: "% Urban agglomerations",
            },
        )
        fig.update_layout(
            geo={"projection": {"type": "natural earth"}},
            margin=dict(l=50, r=50, t=50, b=50),
        )
        return fig


if __name__ == "__main__":
    app.run_server(debug=True)
