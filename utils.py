import dash_bootstrap_components as dbc
from dash import html
import numpy as np
import pandas as pd
import time


# Palette colori centralizzata
PALETTE_COLORI = {
    "raccolto": "#27ae60",       # Verde
    "profitto": "#2980b9",       # Blu
    "temperatura": "#e74c3c",    # Rosso
    "precipitazioni": "#8e44ad",    # Viola
    "qualita_suolo": "#16a085",  # Verde scuro
    "margine_netto":  "#00939e",    # giallo ocra
    "costo_medio": "#a78b00"
}




def genera_dati_simulati(seed=None):
    if seed is None:
        seed = int(time.time())
    np.random.seed(seed)
    # 1) Range di date per un anno
    date_range = pd.date_range(start='2024-01-01', periods=365, freq='D')
    day_of_year = date_range.dayofyear.to_numpy()
    month_of_year = date_range.month
    # 2) Temperature con effetto stagionale (inCampania)
    temperature_base = 16 + 8 * np.sin(2 * np.pi * (day_of_year - 80) / 365)
    temperature_noise = np.random.normal(0, 2, len(date_range))
    temperatura = np.round(temperature_base + temperature_noise, 1)
    # Umidità
    umidita_base = 60 + 10 * np.sin(2 * np.pi * (day_of_year - 150) / 365)
    umidita_noise = np.random.normal(0, 5, len(date_range))
    umidita = np.round(np.clip(umidita_base + umidita_noise, 40, 80), 1)
    # Precipitazioni stagionalita
    precipitazioni_base = np.random.exponential(2, len(date_range))  # media ~2 mm
    seasonal_factor = 1 + 0.6 * np.sin(2 * np.pi * (day_of_year - 110) / 365)
    precipitazioni = np.round(precipitazioni_base * seasonal_factor, 1)
    #  Ore di sole (5–12 ore)
    sole_base = 7 + 5 * np.sin(2 * np.pi * (day_of_year - 80) / 365)
    ore_sole = np.round(sole_base + np.random.normal(0, 1, len(date_range)), 1)
    ore_sole = np.clip(ore_sole, 5, 12)
    # Qualità del suolo
    qualita_suolo = np.round(np.random.uniform(70, 100, len(date_range)), 1)
    # pH del suolo
    ph_suolo = np.round(np.random.normal(loc=6.5, scale=0.3, size=len(date_range)), 1)
    #  Velocità  vento
    velocita_vento = np.round(np.random.normal(loc=3, scale=1, size=len(date_range)), 1)
    velocita_vento = np.clip(velocita_vento, 0, None)
    #giugno-settembre si ricorre a irrigazione se precipitazion < 3 mm
    irrigazione = np.where(
        (precipitazioni < 3) & ((month_of_year >= 6) & (month_of_year <= 9)),
        np.random.uniform(5, 15, len(date_range)),
        0
    )
    irrigazione = np.round(irrigazione, 1)
    # evento estremo < 2°C o > 35°C, pH fuori range, vento > 8 m/s
    evento_estremo = np.where(
        (temperatura < 2) | (temperatura > 35) |
        (ph_suolo < 5.8) | (ph_suolo > 7.8) |
        (velocita_vento > 8),
        1, 0
    )
    # Raccolta estiva-autunnale (giugno-ottobre), ridotta in altri mesi.
    fattore_raccolta_mensile = {
        1: 0.2, 2: 0.2, 3: 0.2, 4: 0.2, 5: 0.4,
        6: 0.8, 7: 1.0, 8: 1.0, 9: 0.8, 10: 0.6,
        11: 0.2, 12: 0.0
    }
    raccolta_factor = np.array([fattore_raccolta_mensile[m] for m in month_of_year])
    # Fattore temperatura
    temperatura_ottimale = 20
    temp_factor = 1 - np.abs(temperatura - temperatura_ottimale) / 20
    # fattore pH: ottimale intorno a 6.5
    ph_factor = 1 - np.abs(ph_suolo - 6.5) / 10
    # Fattore vento
    vento_factor = np.where(velocita_vento > 6, 0.8, 1)
    #  se non piove e non si irriga abbastanza, resa ridotta
    irrigazione_factor = np.where((precipitazioni < 3) & (irrigazione < 5), 0.7, 1)
    # Fattore casuale
    random_factor = np.random.uniform(0.9, 1.1, len(date_range))
    # kg al giorno
    produzione_base = 15  # fattore di scala per un frutteto medio
    produzione = (ore_sole * temp_factor * (qualita_suolo / 100) * random_factor * produzione_base -
                  precipitazioni * np.random.uniform(0.2, 0.7, len(date_range)))
    # Applica i fattori aggiuntivi e la stagionalità di raccolta
    produzione *= ph_factor * vento_factor * irrigazione_factor * raccolta_factor
    quantita_raccolto = np.round(np.clip(produzione, 0, None), 1)
    # Costo di produzione base: 0.40–1.20 €/kg (manodopera, fertilizzanti, trattamenti)
    costo_produzione = np.round(np.random.uniform(0.40, 1.20, len(date_range)) * quantita_raccolto, 2)
    # Costo irrigazione aggiuntivo in base ai mm d'acqua
    costo_irrigazione = np.round(irrigazione * np.random.uniform(0.1, 0.3, len(date_range)), 2)
    costo_totale = costo_produzione + costo_irrigazione
    # Prezzo di vendita medio
    prezzo_vendita = np.random.uniform(1.5, 3.0, len(date_range))
    ricavi = quantita_raccolto * prezzo_vendita
    profitto_stimato = np.round(ricavi - costo_totale, 2)
    alert = np.where(
        (evento_estremo == 1) |
        (qualita_suolo < 70) |
        (temperatura < 10) |
        (temperatura > 35) |
        (umidita < 45),
        'Attenzione',
        'OK'
    )
    # ---- DataFrame Finale ----
    data = pd.DataFrame({
        'Data': date_range,
        'Temperatura (°C)': temperatura,
        'Umidità suolo (%)': umidita,
        'Precipitazioni (mm)': precipitazioni,
        'Ore sole (h)': ore_sole,
        'Qualità suolo (%)': qualita_suolo,
        'pH suolo': ph_suolo,
        'Velocità vento (m/s)': velocita_vento,
        'Irrigazione (mm)': irrigazione,
        'Quantità raccolto (kg)': quantita_raccolto,
        'Costo produzione (€)': costo_produzione,
        'Costo irrigazione (€)': costo_irrigazione,
        'Profitto stimato (€)': profitto_stimato,
        'Alert': alert
    })

    return data


import dash_bootstrap_components as dbc
from dash import html

def create_kpi_card(title, icon_class, value, color="#27ae60", tooltip_text=None):
    # 1) Crea una lista di figli per la card
    card_children = []

    # 2) CardBody principale
    card_body = dbc.CardBody([
        html.Div([
            html.I(className=icon_class, style={"fontSize": "2.2rem"}),
            # Aggiungi un id per poter collegare il tooltip
            html.H6(title, className="mt-3", style={"fontWeight": "600"}, id=title.replace(" ", "").lower()),
            html.H2(value, style={"color": color, "fontWeight": "700", "fontSize": "22px"}),
        ], style={"textAlign": "center"}),
    ])

    # Aggiungi il CardBody ai figli
    card_children.append(card_body)

    # 3) Se c'è un testo tooltip, aggiungi un dbc.Tooltip come ulteriore figlio
    if tooltip_text:
        card_children.append(
            dbc.Tooltip(
                tooltip_text,
                target=title.replace(" ", "").lower()
            )
        )

    # 4) Crea la Card con la lista di figli
    style_card = {
        "borderRadius": "15px",
        "boxShadow": "0 4px 10px rgba(0,0,0,0.1)",
        "border": "none",
        "backgroundColor": "#ffffff",
        "height": "140px",
        "display": "flex",
        "flexDirection": "column",
        "justifyContent": "center",
        "width": "100%",
    }

    card = dbc.Card(
        card_children,
        style=style_card,
        className="p-2 mb-4"
    )

    return card

