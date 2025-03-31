import dash
import dash_bootstrap_components as dbc
from app.components import layout
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.LUX, dbc.icons.FONT_AWESOME])
app.title = "Dashboard Azienda Ortofrutticola"

app.layout = layout

# Importa i callbacks (che a loro volta importano app)
from  .callbacks import *

if __name__ == '__main__':
    app.run_server(debug=False)
