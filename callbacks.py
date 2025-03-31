import numpy as np
import pandas as pd
import datetime
from datetime import timedelta
import pdfkit
from dash import dcc, html, Input, Output, State
import plotly.express as px
import plotly.graph_objects as go
import dash_bootstrap_components as dbc
from app.main import app
from app.utils import create_kpi_card, PALETTE_COLORI, genera_dati_simulati
import plotly.express as px
import pdfkit
import plotly.express as px
import base64
from io import BytesIO
import pandas as pd


# 1) Rigenerazione dati
@app.callback(
    Output("store-data", "data"),
    Input("btn-genera-dati", "n_clicks"),
    prevent_initial_call=True
)
def aggiorna_dati(n_clicks):
    new_df = genera_dati_simulati()
    return new_df.to_json(date_format="iso", orient="split")


# 2) Aggiornamento dashboard (grafici, KPI, alert)
@app.callback(
    Output('grafico-line', 'figure'),
    Output('grafico-scatter', 'figure'),
    Output('grafico-hist', 'figure'),
    Output('kpi-cards', 'children'),
    Output('lista-alert', 'children'),
    Output('grafico-box', 'figure'),
    Output('grafico-line-cp', 'figure'),  # <-- il nuovo Output
    Input('date-range', 'start_date'),
    Input('date-range', 'end_date'),
    Input('variabili-dropdown', 'value'),
    Input('slider-quality', 'value'),
    Input("store-data", "data"),
    Input('scatter-x-dropdown', 'value'),
    Input('scatter-y-dropdown', 'value'),
    Input('scatter-color-dropdown', 'value'),
)
def aggiorna_dashboard(start_date, end_date, variabili, quality_range, data_json, scatter_x, scatter_y, scatter_color):
    df = pd.read_json(data_json, orient="split")
    df['Data'] = pd.to_datetime(df['Data'], errors='coerce')
    start_date = pd.to_datetime(start_date)
    end_date = pd.to_datetime(end_date)

    # Filtro per le date
    mask = (df['Data'] >= start_date) & (df['Data'] <= end_date)
    df_filtrato = df.loc[mask]
    # Filtro per la qualità del suolo
    q_min, q_max = quality_range
    df_filtrato = df_filtrato[
        (df_filtrato['Qualità suolo (%)'] >= q_min) &
        (df_filtrato['Qualità suolo (%)'] <= q_max)
    ]
    # GRAFICO LINE
    fig_line = go.Figure()
    colori = list(PALETTE_COLORI.values())
    for idx, var in enumerate(variabili):
        fig_line.add_trace(go.Scatter(
            x=df_filtrato['Data'],
            y=df_filtrato[var],
            mode='lines+markers',
            name=var,
            marker=dict(size=6),
            line=dict(width=2, color=colori[idx % len(colori)])
        ))
    fig_line.update_layout(
        title='Andamento delle variabili selezionate',
        template='plotly_white',
        xaxis=dict(title='Data'),
        yaxis=dict(title='Valore'),
        legend=dict(orientation='h', y=-0.2, x=0.5, xanchor='center')
    )
    # GRAFICO SCATTER
    fig_scatter = px.scatter(
        df_filtrato,
        x=scatter_x,
        y=scatter_y,
        color=scatter_color,
        trendline="ols",
        template="plotly_white",
        title=f"Correlazione tra {scatter_x} e {scatter_y}"
    )
    # GRAFICO HISTOGRAMMA
    df_filtrato['Mese'] = df_filtrato['Data'].dt.strftime('%b')
    fig_hist = px.histogram(
        df_filtrato,
        x='Quantità raccolto (kg)',
        color='Mese',
        nbins=15,
        barmode='group',
        histnorm='percent',
        template='plotly_white',
        title='Distribuzione della Quantità raccolto (kg) per Mese'
    )
    fig_hist.update_layout(
        xaxis_title='Quantità raccolto (kg)',
        yaxis_title='Frequenza (%)',
        legend_title_text='Mese'
    )

    produzione_totale = df_filtrato['Quantità raccolto (kg)'].sum()
    profitto_totale = df_filtrato['Profitto stimato (€)'].sum()
    temperatura_media = df_filtrato['Temperatura (°C)'].mean()
    precipitazioni_medie = df_filtrato['Precipitazioni (mm)'].mean()
    qualita_media = df_filtrato['Qualità suolo (%)'].mean()

    kpi_cards_base = dbc.Row([
        dbc.Col(create_kpi_card("Produzione Totale", "fas fa-tractor", f"{produzione_totale:,.1f} kg",
                                PALETTE_COLORI["raccolto"],
                                tooltip_text="Somma totale della produzione nel periodo."), md=2),
        dbc.Col(create_kpi_card("Profitto Totale", "fas fa-euro-sign", f"{profitto_totale:,.2f} €",
                                PALETTE_COLORI["profitto"],
                                tooltip_text="Profitto totale stimato nel periodo."), md=2),
        dbc.Col(create_kpi_card("Temp. Media", "fas fa-thermometer-half", f"{temperatura_media:.1f} °C",
                                PALETTE_COLORI["temperatura"],
                                tooltip_text="Temperatura media nel periodo."), md=2),
        dbc.Col(create_kpi_card("Prec. Media", "fas fa-cloud-rain", f"{precipitazioni_medie:.1f} mm",
                                PALETTE_COLORI["precipitazioni"],
                                tooltip_text="Precipitazioni medie nel periodo."), md=2),
        dbc.Col(create_kpi_card("Qualità suolo Media", "fas fa-seedling", f"{qualita_media:.1f} %",
                                PALETTE_COLORI["qualita_suolo"],
                                tooltip_text="Qualità media del suolo nel periodo."), md=2)
    ], justify="center")

    # Calcolo costi e ricavi per margine netto
    if 'Costo produzione (€)' in df_filtrato.columns:
        costo_produzione_tot = df_filtrato['Costo produzione (€)'].sum()
    else:
        costo_produzione_tot = 0

    if 'Costo irrigazione (€)' in df_filtrato.columns:
        costo_irrigazione_tot = df_filtrato['Costo irrigazione (€)'].sum()
    else:
        costo_irrigazione_tot = 0

    costo_totale = costo_produzione_tot + costo_irrigazione_tot

    # Costo medio per kg
    if produzione_totale > 0:
        costo_medio_kg = costo_totale / produzione_totale
    else:
        costo_medio_kg = 0

    # Ricavi totali = Profitto + Costi
    ricavi_totali = profitto_totale + costo_totale
    if ricavi_totali != 0:
        margine_netto = (profitto_totale / ricavi_totali) * 100
    else:
        margine_netto = 0

    # Crea un secondo blocco di card
    kpi_cards_extra = dbc.Row([
        dbc.Col(
            create_kpi_card(
                "Margine Netto",
                "fas fa-percentage",
                f"{margine_netto:.1f} %",
                PALETTE_COLORI["margine_netto"],
                tooltip_text="Percentuale di profitto sui ricavi totali."
            ), md=2
        ),
        dbc.Col(
            create_kpi_card(
                "Costo Medio/kg",
                "fas fa-coins",
                f"{costo_medio_kg:.2f} €/kg",
                PALETTE_COLORI["costo_medio"],
                tooltip_text="Costo totale diviso per la quantità prodotta."
            ), md=2
        ),
    ], justify="center")

    # Unisci i due blocchi di card
    kpi_cards_final = html.Div([
        kpi_cards_base,
        html.Br(),
        kpi_cards_extra
    ])

    # Alert
    alert_df = df_filtrato[df_filtrato['Alert'] != "OK"]
    alert_items = [
        html.Li(
            f"{row['Data']:%Y-%m-%d}: {row['Alert']} (Temp: {row['Temperatura (°C)']}°C, "
            f"Prec: {row['Precipitazioni (mm)']} mm, Qualità: {row['Qualità suolo (%)']}%)",
            style={"color": "#e74c3c"}
        )
        for _, row in alert_df.iterrows()
    ]

    #  Distribuzione mensile con deviazione standard
    df_filtrato['MeseNum'] = df_filtrato['Data'].dt.month
    df_monthly = df_filtrato.groupby('MeseNum')['Quantità raccolto (kg)'].agg(['mean', 'std']).reset_index()

    fig_box = px.bar(
        df_monthly,
        x='MeseNum',
        y='mean',
        error_y='std',
        template='plotly_white',
        title='Media Mensile della Produzione con Barre di Errore (dev. standard)'
    )
    fig_box.update_layout(
        xaxis_title='Mese',
        yaxis_title='Produzione Media (kg)'
    )

    df_monthly_cp = df_filtrato.groupby('MeseNum')[
        ['Costo produzione (€)', 'Profitto stimato (€)']].mean().reset_index()
    df_melted = df_monthly_cp.melt(
        id_vars='MeseNum',
        value_vars=['Costo produzione (€)', 'Profitto stimato (€)'],
        var_name='Variabile',
        value_name='Valore'
    )
    fig_line_cp = px.line(
        df_melted,
        x='MeseNum',
        y='Valore',
        color='Variabile',
        markers=True,
        template='plotly_white',
        title='Andamento Mensile di Costi e Profitto (media mensile)'
    )
    fig_line_cp.update_layout(
        xaxis_title='Mese',
        yaxis_title='Valore (€)',
        legend_title_text='Variabile'
    )

    return (
        fig_line,
        fig_scatter,
        fig_hist,
        kpi_cards_final,
        alert_items,
        fig_box,
        fig_line_cp
    )


# 3) Download dati filtrati in CSV
@app.callback(
    Output("download-dataframe-csv", "data"),
    Input("btn-download", "n_clicks"),
    State('date-range', 'start_date'),
    State('date-range', 'end_date'),
    State("store-data", "data"),
    prevent_initial_call=True,
)
def download_filtered_data(n_clicks, start_date, end_date, data_json):
    df = pd.read_json(data_json, orient="split")
    mask = (df['Data'] >= start_date) & (df['Data'] <= end_date)
    df_filtrato = df.loc[mask]
    return dcc.send_data_frame(df_filtrato.to_csv, "dati_filtrati.csv", index=False, sep=';', encoding='utf-8-sig')


# 4) Forecast: Previsione produzione per i prossimi 30 giorni
@app.callback(
    Output('grafico-forecast', 'figure'),
    Input('date-range', 'end_date'),
    Input("store-data", "data")
)
def aggiorna_forecast(end_date, data_json):
    df = pd.read_json(data_json, orient="split")
    df_forecast = df[df['Data'] <= end_date].copy()
    if len(df_forecast) < 2:
        return go.Figure()

    df_forecast['Data'] = pd.to_datetime(df_forecast['Data'], errors='coerce')
    df_forecast['Data_ord'] = df_forecast['Data'].map(datetime.datetime.toordinal)

    x = df_forecast['Data_ord'].values
    y = df_forecast['Quantità raccolto (kg)'].values

    coeffs = np.polyfit(x, y, 1)
    poly = np.poly1d(coeffs)

    last_date = pd.to_datetime(end_date)
    future_dates = [last_date + timedelta(days=i) for i in range(1, 31)]
    future_ord = [d.toordinal() for d in future_dates]
    forecast_values = poly(future_ord)

    df_forecast_pred = pd.DataFrame({
        'Data': future_dates,
        'Quantità raccolto (kg)': forecast_values
    })

    fig_forecast = go.Figure()
    fig_forecast.add_trace(go.Scatter(
        x=df_forecast['Data'],
        y=df_forecast['Quantità raccolto (kg)'],
        mode='markers',
        name='Storico',
        marker=dict(color=PALETTE_COLORI["raccolto"])
    ))
    fig_forecast.add_trace(go.Scatter(
        x=df_forecast_pred['Data'],
        y=df_forecast_pred['Quantità raccolto (kg)'],
        mode='lines+markers',
        name='Forecast',
        line=dict(dash='dash', color=PALETTE_COLORI["temperatura"])
    ))
    fig_forecast.update_layout(
        title="Previsione Produzione (30 giorni)",
        xaxis=dict(title="Data"),
        yaxis=dict(title="Quantità raccolto (kg)"),
        template="plotly_white"
    )
    return fig_forecast


# 5) Download forecast in CSV
@app.callback(
    Output("download-forecast-csv", "data"),
    Input("btn-download-forecast", "n_clicks"),
    State('date-range', 'end_date'),
    State("store-data", "data"),
    prevent_initial_call=True,
)
def download_forecast_data(n_clicks, end_date, data_json):
    df = pd.read_json(data_json, orient="split")
    df_forecast = df[df['Data'] <= end_date].copy()
    if len(df_forecast) < 2:
        return

    df_forecast['Data'] = pd.to_datetime(df_forecast['Data'], errors='coerce')
    df_forecast['Data_ord'] = df_forecast['Data'].map(datetime.datetime.toordinal)

    x = df_forecast['Data_ord'].values
    y = df_forecast['Quantità raccolto (kg)'].values
    coeffs = np.polyfit(x, y, 1)
    poly = np.poly1d(coeffs)

    last_date = pd.to_datetime(end_date)
    future_dates = [last_date + timedelta(days=i) for i in range(1, 31)]
    future_ord = [d.toordinal() for d in future_dates]
    forecast_values = poly(future_ord)

    df_forecast_pred = pd.DataFrame({
        'Data': future_dates,
        'Quantità raccolto (kg)': forecast_values
    })

    return dcc.send_data_frame(df_forecast_pred.to_csv, "forecast_dati.csv", index=False)


# 6) Generazione e download Report PDF
@app.callback(
    Output("download-pdf", "data"),
    Input("btn-download-pdf", "n_clicks"),
    State('date-range', 'start_date'),
    State('date-range', 'end_date'),
    State("store-data", "data"),
    prevent_initial_call=True,
)
def genera_report_pdf(n_clicks, start_date, end_date, data_json):

    # Converte i dati dal JSON in DataFrame
    df = pd.read_json(data_json, orient="split")
    mask = (df['Data'] >= start_date) & (df['Data'] <= end_date)
    df_filtrato = df.loc[mask]

    # Calcolo dei KPI principali
    produzione_totale = df_filtrato['Quantità raccolto (kg)'].sum()
    profitto_totale = df_filtrato['Profitto stimato (€)'].sum()
    temperatura_media = df_filtrato['Temperatura (°C)'].mean()
    prec_media = df_filtrato['Precipitazioni (mm)'].mean()

    # Generazione di un grafico esempio: Andamento della produzione nel tempo
    fig = px.line(df_filtrato, x='Data', y='Quantità raccolto (kg)',
                  title="Andamento della Produzione nel Tempo",
                  template="plotly_white")
    # Converti il grafico in immagine PNG usando Kaleido
    img_bytes = fig.to_image(format="png")
    img_base64 = base64.b64encode(img_bytes).decode('utf-8')

    # Costruzione del report HTML con sezioni e grafico incluso
    html_report = f"""
    <html>
    <head>
      <meta charset="utf-8">
      <title>Report Dashboard</title>
      <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        h1, h2, h3 {{ color: #2c3e50; }}
        table {{ width: 100%; border-collapse: collapse; margin-bottom: 20px; }}
        th, td {{ padding: 8px 12px; border: 1px solid #ccc; }}
        th {{ background-color: #ecf0f1; }}
        .section {{ margin-bottom: 40px; }}
        ul {{ list-style-type: none; padding: 0; }}
        li {{ margin-bottom: 5px; }}
        .grafico {{ text-align: center; margin-top: 20px; }}
      </style>
    </head>
    <body>
      <h1>Report Dashboard</h1>
      <div class="section">
        <h2>Periodo di Analisi</h2>
        <p><strong>Inizio:</strong> {start_date}</p>
        <p><strong>Fine:</strong> {end_date}</p>
      </div>
      <div class="section">
        <h2>Riepilogo KPI</h2>
        <ul>
          <li><strong>Produzione Totale:</strong> {produzione_totale:,.1f} kg</li>
          <li><strong>Profitto Totale:</strong> {profitto_totale:,.2f} €</li>
          <li><strong>Temperatura Media:</strong> {temperatura_media:.1f} °C</li>
          <li><strong>Precipitazioni Medie:</strong> {prec_media:.1f} mm</li>
        </ul>
      </div>
      <div class="section">
        <h2>Grafico: Andamento della Produzione</h2>
        <div class="grafico">
          <img src="data:image/png;base64,{img_base64}" alt="Grafico Produzione" style="max-width:100%; height:auto;">
        </div>
      </div>
      <div class="section">
        <h2>Anteprima Dati</h2>
        {df_filtrato.head(10).to_html(index=False)}
      </div>
      <div class="section">
        <h2>Analisi e Commenti</h2>
        <p>
          Il report evidenzia un andamento stagionale coerente con le attese per il settore primario.
          Si osservano variazioni significative nei KPI che potrebbero suggerire opportunità di miglioramento
          nella gestione delle risorse e nella pianificazione della produzione.
        </p>
      </div>
      <div class="section">
        <h2>Metodologia</h2>
        <p>
          I dati sono stati simulati considerando variabili ambientali e produttive quali temperatura, umidità, 
          precipitazioni, ore di sole, qualità del suolo, pH, velocità del vento e irrigazione. Il modello applica 
          fattori correttivi basati su condizioni ideali, introducendo variabilità tramite un fattore casuale, 
          per stimare la quantità di raccolto e il profitto. Questo approccio consente di analizzare scenari e supportare 
          le decisioni strategiche.
        </p>
      </div>
    </body>
    </html>
    """
    pdf = pdfkit.from_string(html_report, False)
    return dcc.send_bytes(pdf, "report_dashboard.pdf")



# 7) Comparazione periodica: confronto tra due periodi
@app.callback(
    Output('grafico-comparazione', 'figure'),
    Output('kpi-comparazione', 'children'),
    Input('date-range-1', 'start_date'),
    Input('date-range-1', 'end_date'),
    Input('date-range-2', 'start_date'),
    Input('date-range-2', 'end_date'),
    Input("store-data", "data")
)
def aggiorna_comparazione(start1, end1, start2, end2, data_json):
    df = pd.read_json(data_json, orient="split")

    # Filtro per i due periodi
    mask1 = (df['Data'] >= start1) & (df['Data'] <= end1)
    mask2 = (df['Data'] >= start2) & (df['Data'] <= end2)
    df1 = df.loc[mask1]
    df2 = df.loc[mask2]

    # Calcolo KPI per i due periodi
    produzione1 = df1['Quantità raccolto (kg)'].sum()
    produzione2 = df2['Quantità raccolto (kg)'].sum()
    variazione = ((produzione2 - produzione1) / produzione1 * 100) if produzione1 != 0 else 0

    # KPI comparazione
    kpi_comparazione = dbc.Row([
        dbc.Col(create_kpi_card("Produzione Periodo 1", "fas fa-tractor", f"{produzione1:,.1f} kg",
                                PALETTE_COLORI["raccolto"]), md=3),
        dbc.Col(create_kpi_card("Produzione Periodo 2", "fas fa-tractor", f"{produzione2:,.1f} kg",
                                PALETTE_COLORI["raccolto"]), md=3),
        dbc.Col(
            create_kpi_card("Variazione (%)", "fas fa-chart-line", f"{variazione:+.1f} %",
                            PALETTE_COLORI["profitto"]),
            md=3)
    ], justify="center")

    # Grafico comparativo (es. trend della produzione nei due periodi)
    df1['Periodo'] = 'Periodo 1'
    df2['Periodo'] = 'Periodo 2'
    df_comp = pd.concat([df1, df2])
    fig_comp = px.line(df_comp, x='Data', y='Quantità raccolto (kg)', color='Periodo',
                       template="plotly_white",
                       title="Confronto Produzione tra i due Periodi Scelti ")

    return fig_comp, kpi_comparazione
@app.callback(
    Output("table-dati", "data"),      # la proprietà "data" della dash_table
    Input("store-data", "data")        # quando cambia il contenuto di store-data
)
def aggiorna_tabella(data_json):
    # Leggi il DataFrame dal JSON
    df = pd.read_json(data_json, orient="split")
    # Convertilo in records e ritornalo
    return df.to_dict("records")

#controllare arima per evitare una semplixe regressione lineare e inserire arima per calcolare regressione lineare particolare con previsione dati accurata