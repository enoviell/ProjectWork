from dash import html, dcc, dash_table
import dash_bootstrap_components as dbc
import pandas as pd
from app.utils import genera_dati_simulati, PALETTE_COLORI, create_kpi_card

# Dati iniziali simulati
df_iniziale = genera_dati_simulati()



# dcc.Store per mantenere i dati nel browser
store_data = dcc.Store(id="store-data", data=df_iniziale.to_json(date_format="iso", orient="split"))

# Navbar con header e sottotitolo
navbar = dbc.Navbar(
    dbc.Container([
        dbc.Row([
            dbc.Col([
                dbc.NavbarBrand("Dashboard Prestazioni Aziendali", style={"fontWeight": "bold"}),
            ], width="auto"),
        ], align="center", className="g-0"),
    ], fluid=True),
    color="dark",
    dark=True,
    className="mb-4"
)
# Definizione dello scatter options
scatter_options = dbc.Row([
    dbc.Col([
        html.Label("Asse X:"),
        dcc.Dropdown(
            id='scatter-x-dropdown',
            options=[{'label': col, 'value': col} for col in df_iniziale.columns if col not in ['Data', 'Alert']],
            value='Temperatura (°C)'
        )
    ], width=2),
    dbc.Col([
        html.Label("Asse Y:"),
        dcc.Dropdown(
            id='scatter-y-dropdown',
            options=[{'label': col, 'value': col} for col in df_iniziale.columns if col not in ['Data', 'Alert']],
            value='Quantità raccolto (kg)'
        )
    ], width=2),
    dbc.Col([
        html.Label("Colorazione per:"),
        dcc.Dropdown(
            id='scatter-color-dropdown',
            options=[{'label': col, 'value': col} for col in df_iniziale.columns if col not in ['Data', 'Alert']],
            value='Temperatura (°C)'
        )
    ], width=2)
])

# -----------------------------------------
# Colonne della prima riga: Periodo, Qualità
# -----------------------------------------
date_picker = dbc.Col([
    html.Label("Periodo analisi:", style={"fontWeight": "bold"}),
    dcc.DatePickerRange(
        id='date-range',
        min_date_allowed=df_iniziale['Data'].min(),
        max_date_allowed=df_iniziale['Data'].max(),
        start_date=df_iniziale['Data'].min(),
        end_date=df_iniziale['Data'].max(),
        display_format='DD/MM/YYYY',
        style={"width": "100%"}
    )
], width=4)

quality_slider = dbc.Col([
    html.Label("Filtra per Qualità del suolo (%):", style={"fontWeight": "bold"}),
    dcc.RangeSlider(
        id='slider-quality',
        min=70,
        max=100,
        step=1,
        value=[70, 100],
        marks={70: "70%", 80: "80%", 90: "90%", 100: "100%"},
    )
], width=3)

# Bottone per scaricare CSV
button_download_csv = dbc.Button("Scarica dati filtrati", id="btn-download", color="primary", className="shadow-sm")

# Bottone per scaricare Report PDF
button_download_pdf = dbc.Button("Scarica Report PDF", id="btn-download-pdf", color="primary", className="shadow-sm")

# Container per le KPI Cards
kpi_cards_container = dbc.Row(id='kpi-cards', justify="center", className="mb-0")

# Pulsante “Genera Nuovi Dati” (riga separata, centrata)
pulsante_genera_dati = dbc.Row(
    [
        dbc.Col(
            dbc.Button("Genera Nuovi Dati", id="btn-genera-dati", color="secondary", className="mt-4",style={"borderRadius": "10px"} ),
            width="auto"

        )
    ],
    justify="center",
    className="mb-4"
)

# Grafici
graph_line = dcc.Graph(id='grafico-line', style={"backgroundColor": "#fff", "borderRadius": "10px"})
graph_scatter = dcc.Graph(id='grafico-scatter', style={"backgroundColor": "#fff", "borderRadius": "10px"})
graph_hist = dcc.Graph(id='grafico-hist', style={"backgroundColor": "#fff", "borderRadius": "10px"})
graph_box = dcc.Graph(id='grafico-box', style={"backgroundColor": "#fff", "borderRadius": "10px"})
graph_forecast = dcc.Graph(id='grafico-forecast', style={"backgroundColor": "#fff", "borderRadius": "10px"})
graph_line_cp = dcc.Graph( id='grafico-line-cp', style={"backgroundColor": "#fff", "borderRadius": "10px"})


# Container Alert
alert_list = html.Div(id='lista-alert', style={"maxHeight": "200px", "overflowY": "auto"})

# Tabella dati simulati
data_table = dash_table.DataTable(
    id='table-dati',
    columns=[{"name": i, "id": i} for i in df_iniziale.columns],
    data=df_iniziale.to_dict('records'),
    page_size=10,
    style_table={'overflowX': 'auto'},
    style_cell={'textAlign': 'center', 'fontFamily': 'Arial'},
    style_header={'fontWeight': 'bold'},
    style_data={'whiteSpace': 'normal', 'height': 'auto'}
)

# --- Tab per la Comparazione Periodica ---
comparazione_tab = dbc.Container([
    dbc.Row([
        dbc.Col([
            html.Label("Periodo 1:", style={"fontWeight": "bold"}),
            dcc.DatePickerRange(
                id='date-range-1',
                min_date_allowed=df_iniziale['Data'].min(),
                max_date_allowed=df_iniziale['Data'].max(),
                start_date=df_iniziale['Data'].min(),
                end_date=df_iniziale['Data'].iloc[182],
                display_format='DD/MM/YYYY',
                style={"width": "100%"}
            )
        ], width=6),
        dbc.Col([
            html.Label("Periodo 2:", style={"fontWeight": "bold"}),
            dcc.DatePickerRange(
                id='date-range-2',
                min_date_allowed=df_iniziale['Data'].min(),
                max_date_allowed=df_iniziale['Data'].max(),
                start_date=df_iniziale['Data'].iloc[183],
                end_date=df_iniziale['Data'].max(),
                display_format='DD/MM/YYYY',
                style={"width": "100%"}
            )
        ], width=6)
    ], className="mb-3"),
    dbc.Row([
        dbc.Col(
            dcc.Graph(id='grafico-comparazione', style={"backgroundColor": "#fff", "borderRadius": "10px"}),
            width=12
        )
    ], className="mb-4"),
    dbc.Row(id='kpi-comparazione', justify="center")
], fluid=True)

# --- Layout delle varie Tabs ---

# Tab "Dashboard"
dashboard_tab = dbc.Container([
    # RIGA 1: Periodo, Variabili, Qualità
    dbc.Row([date_picker, quality_slider], className="mb-3"),

    # RIGA 2: KPI Cards
    kpi_cards_container,

    # RIGA 3: Pulsante Genera Dati
    pulsante_genera_dati,
dbc.Row([
        dbc.Col([
            html.Label("Variabili da visualizzare:", style={"fontWeight": "bold"}),
            dcc.Dropdown(
                id='variabili-dropdown',
                options=[
                    {'label': col, 'value': col}
                    for col in df_iniziale.columns if col not in ['Data', 'Alert']
                ],
                value=['Quantità raccolto (kg)', 'Profitto stimato (€)'],
                multi=True
            )
        ], width=4)
    ], className="mb-2"),
    # GRAFICO LINE
    dbc.Row([graph_line], className="mb-4"),
    dbc.Row([scatter_options], className="mb-3"),

    # SCATTER E HIST
    dbc.Row([
        dbc.Col(graph_scatter, width=6),
        dbc.Col(graph_hist, width=6)
    ], className="mb-4"),


    # BOX PLOT + line chart costi/profitto
    dbc.Row([
        dbc.Col(graph_box, width=6),
        dbc.Col(graph_line_cp, width=6)
    ], className="mb-4"),

    # ALERT
    dbc.Row([
        dbc.Col([
            html.H5("Alert - Giorni con condizioni estreme:", style={"fontWeight": "bold"}),
            alert_list
        ], width=12)
    ], className="mb-4"),

    # DOWNLOAD BUTTONS
    dbc.Row([
        dbc.Col(button_download_csv, width={"size": 2, "offset": 4}),
        dbc.Col(button_download_pdf, width=2)
    ], className="mb-4"),

    dcc.Download(id="download-dataframe-csv"),
    dcc.Download(id="download-pdf")
], fluid=True)

# Tab "Forecast"
forecast_tab = dbc.Container([
    dbc.Row([dbc.Col(html.H4("Previsione Produzione (30 giorni)"), width=12)], className="mb-4"),
    dbc.Row([dbc.Col(graph_forecast, width=12)], className="mb-4"),
    dbc.Row([
        dbc.Col(
            dbc.Button("Scarica Previsione", id="btn-download-forecast", color="primary", className="shadow-sm"),
            width={"size": 2, "offset": 5}
        )
    ]),
    dcc.Download(id="download-forecast-csv")
], fluid=True)

# Tab "Dati Simulati"
data_tab = dbc.Container([
    dbc.Row([dbc.Col(html.H4("Tabella Dati Simulati"), width=12)], className="mb-4"),
    data_table
], fluid=True)

# Definizione TABS globali
tabs = dbc.Tabs([
    dbc.Tab(dashboard_tab, label="Dashboard", tab_id="dashboard"),
    dbc.Tab(forecast_tab, label="Forecast", tab_id="forecast"),
    dbc.Tab(data_tab, label="Dati Simulati", tab_id="data"),
    dbc.Tab(comparazione_tab, label="Confronto di produzione tra i  periodi", tab_id="comparazione"),
], id="tabs", active_tab="dashboard", className="mb-5")

# Layout generale
layout = html.Div(
    style={
        "minHeight": "100vh",
        "background": "linear-gradient(135deg, #ECF3F9 0%, #F5FFFA 100%)",
    },
    children=[
        store_data,
        navbar,
        dbc.Container([tabs], fluid=True),
        html.Footer(
            "Realizzato da Emanuele Noviello Matricola: 0312302207 ",
            style={
                'textAlign': 'center',
                'padding': '15px',
                'color': '#1c1c1c',
                'backgroundColor': '#fff',
                'marginTop': 'auto',
                'boxShadow': '0 -2px 5px rgba(0,0,0,0.1)',
                'font-weight': 'bold'
            }
        )
    ]
)
