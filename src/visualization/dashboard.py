import dash
from dash import dcc, html, Input, Output
import dash_bootstrap_components as dbc
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import numpy as np
import os

from pathlib import Path

# Production = running on Railway (WSGI mount), strips /analytics prefix
# Local = standalone Dash server on :8050, Vite proxies /analytics/ to it
IS_PRODUCTION = os.environ.get("RAILWAY_ENVIRONMENT") is not None

# ==========================================
# 1. DATA LOADING & MAPPING
# ==========================================
BASE_DIR = Path(__file__).resolve().parents[2]
csv_path = BASE_DIR / "data" / "raw" / "KPC___Despatch_Details_260924.csv"

try:
    df_raw = pd.read_csv(csv_path)
    column_mapping = {
        'INV DATE': 'Date', 'REGION': 'Region', 'MODEL': 'Model',
        'CUSTOMER NAME': 'Customer', 'TRANSPORTER': 'Transporter',
        'ITEM DESCRIPTION': 'Item_Description', 'QTY': 'QTY',
        'UNIT PRICE': 'Unit_Price', 'GROSS VALUE': 'Gross_Value',
        'TAX VALUE': 'Tax', 'OA DATE': 'Order_Date', 'PROMISE DATE': 'Promise_Date'
    }
    df = df_raw.rename(columns=column_mapping)
    df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
    df['Promise_Date'] = pd.to_datetime(df['Promise_Date'], errors='coerce')
    df['Order_Date'] = pd.to_datetime(df['Order_Date'], errors='coerce')
    df = df.dropna(subset=['Date'])
    
    # Metrics
    df['Lead_Time'] = (df['Date'] - df['Order_Date']).dt.days.fillna(0)
    df['OnTime'] = np.where(df['Date'] <= df['Promise_Date'], 1, 0)
    df['Year'] = df['Date'].dt.year
    print("Data loaded successfully.")
except Exception as e:
    print(f"Error: {e}")
    df = pd.DataFrame()

# ==========================================
# 2. BRAND COLOR PALETTE & STYLING
# ==========================================
K_TEAL = '#1A9988'
K_CLAY = '#C27E5F'
K_DARK = '#0D4D44'
K_BG = '#EBF7F6'

app = dash.Dash(
    __name__, 
    external_stylesheets=[dbc.themes.FLATLY],
    requests_pathname_prefix='/analytics/',
    routes_pathname_prefix='/' if IS_PRODUCTION else '/analytics/'
)

app.index_string = f'''
<!DOCTYPE html>
<html>
    <head>
        {{%metas%}}
        <title>Kirloskar Analytics</title>
        {{%favicon%}}
        {{%css%}}
        <style>
            body {{ margin: 0; padding: 0; background-color: {K_BG}; font-family: 'Segoe UI', sans-serif; }}
            .pbi-card {{ 
                background-color: white; border-radius: 15px; 
                box-shadow: 0 2px 4px rgba(0,0,0,0.08); padding: 15px; 
                height: 100%; border: 1px solid #d1d5db;
            }}
            .kpi-title {{ color: #666; font-size: 0.75rem; font-weight: 600; text-transform: uppercase; }}
            .kpi-value {{ color: {K_TEAL}; font-size: 1.6rem; font-weight: 700; }}
            .custom-tabs .nav-link {{ border: none !important; color: #555 !important; font-weight: 600; }}
            .custom-tabs .nav-link.active {{ border-bottom: 4px solid {K_TEAL} !important; color: {K_TEAL} !important; background: transparent !important; }}
            .filter-label {{ color: {K_CLAY}; font-weight: bold; font-size: 0.7rem; }}
        </style>
    </head>
    <body>{{%app_entry%}}<footer>{{%config%}}{{%scripts%}}{{%renderer%}}</footer></body>
</html>
'''

# ==========================================
# 3. GLOBAL HEADER & FILTERS
# ==========================================
header = dbc.Row([
    dbc.Col(html.H2("Spare Parts Performance Dashboard", style={'color': K_TEAL, 'fontWeight': 'bold'}), width=9),
    dbc.Col(html.Img(src="https://www.kirloskarlimitless.com/image/layout_set_logo?img_id=497324", height="55px"), width=3, className="text-end")
], className="mx-0 my-3 px-3 align-items-center")

filters = html.Div(className="pbi-card mx-3 mb-3", children=[
    dbc.Row([
        dbc.Col([html.Div("Region", className="filter-label"), dcc.Dropdown(id='reg', options=sorted([str(x) for x in df['Region'].dropna().unique()]) if not df.empty else [], multi=True, placeholder="All")], width=3),
        dbc.Col([html.Div("Model", className="filter-label"), dcc.Dropdown(id='mod', options=sorted([str(x) for x in df['Model'].dropna().unique()]) if not df.empty else [], multi=True, placeholder="All")], width=2),
        dbc.Col([html.Div("Customer", className="filter-label"), dcc.Dropdown(id='cus', options=sorted([str(x) for x in df['Customer'].dropna().unique()]) if not df.empty else [], multi=True, placeholder="Search...")], width=4),
        dbc.Col([html.Div("Order Date Range", className="filter-label"), dcc.DatePickerRange(id='dt', min_date_allowed=df['Order_Date'].min() if not df.empty else None, max_date_allowed=df['Order_Date'].max() if not df.empty else None, start_date=df['Order_Date'].min() if not df.empty else None, end_date=df['Order_Date'].max() if not df.empty else None, display_format='DD-MM-YYYY')], width=3),
    ])
])

app.layout = html.Div([
    header, filters,
    html.Div(style={'padding': '0 15px'}, children=[
        dcc.Tabs(id="tabs", value='s1', className="custom-tabs mb-3", children=[
            dcc.Tab(label='OVERVIEW & REVENUE', value='s1'),
            dcc.Tab(label='LOGISTICS & PERFORMANCE', value='s2'),
        ]),
        html.Div(id='content')
    ])
])

# ==========================================
# 4. CALLBACKS & VISUALS
# ==========================================
@app.callback(
    Output('content', 'children'), 
    [Input('tabs', 'value'), Input('reg', 'value'), Input('mod', 'value'), 
     Input('cus', 'value'), Input('dt', 'start_date'), Input('dt', 'end_date')]
)
def update_view(tab, r, m, c, start, end):
    try:
        if df.empty: return html.Div("Data not loaded correctly.")
        
        # Initial filtering
        dff = df.copy()
        if start and end:
            dff = dff[(dff['Order_Date'] >= start) & (dff['Order_Date'] <= end)]
        
        if r: dff = dff[dff['Region'].isin(r)]
        if m: dff = dff[dff['Model'].isin(m)]
        if c: dff = dff[dff['Customer'].isin(c)]

        if dff.empty:
            return html.Div(className="p-5 text-center text-muted", children="No data found for the selected filters.")

        pbi_layout = dict(
            plot_bgcolor='white', paper_bgcolor='white', font=dict(family='Segoe UI', size=11),
            margin=dict(t=40, b=40, l=40, r=40), legend=dict(orientation="h", yanchor="bottom", y=-0.3, xanchor="center", x=0.5)
        )

        if tab == 's1':
            # SHEET 1 Visuals
            # 1. Donut Chart (Region)
            reg_data = dff.groupby('Region')['QTY'].sum().reset_index()
            if not reg_data.empty:
                reg_data['Region'] = reg_data.apply(lambda x: x['Region'] if (x['QTY']/reg_data['QTY'].sum()) > 0.03 else 'Others', axis=1)
                fig_donut = px.pie(reg_data.groupby('Region')['QTY'].sum().reset_index(), values='QTY', names='Region', hole=.5, color_discrete_sequence=px.colors.sequential.Tealgrn)
            else:
                fig_donut = go.Figure()
            fig_donut.update_layout(pbi_layout, title="Sum of QTY by REGION")

            # 2. Pareto Chart
            p_data = dff.groupby('Customer')['Gross_Value'].sum().sort_values(ascending=False).reset_index()
            fig_pareto = go.Figure()
            if not p_data.empty:
                p_data['cum'] = 100 * p_data['Gross_Value'].cumsum() / p_data['Gross_Value'].sum()
                fig_pareto.add_trace(go.Bar(x=p_data['Customer'][:10], y=p_data['Gross_Value'][:10], name='Gross Value', marker_color=K_TEAL))
                fig_pareto.add_trace(go.Scatter(x=p_data['Customer'][:10], y=p_data['cum'][:10], name='Cum %', yaxis='y2', line=dict(color=K_CLAY, width=3)))
            fig_pareto.update_layout(pbi_layout, title="80/20 Rule for Spare Parts", yaxis2=dict(overlaying='y', side='right', range=[0, 110]))

            return html.Div([
                dbc.Row([
                    dbc.Col(html.Div(className="pbi-card text-center", children=[html.Div("Total Revenue", className="kpi-title"), html.Div(f"₹{dff['Gross_Value'].sum()/1e7:.2f} Cr", className="kpi-value")]), width=3),
                    dbc.Col(html.Div(className="pbi-card text-center", children=[html.Div("Total Tax", className="kpi-title"), html.Div(f"₹{dff['Tax'].sum()/1e5:.2f} L", className="kpi-value")]), width=3),
                    dbc.Col(html.Div(className="pbi-card text-center", children=[html.Div("Avg Order Value", className="kpi-title"), html.Div(f"₹{dff['Gross_Value'].mean():,.0f}", className="kpi-value")]), width=3),
                    dbc.Col(html.Div(className="pbi-card text-center", children=[html.Div("Total Parts Sold", className="kpi-title"), html.Div(f"{dff['QTY'].sum():,.0f}", className="kpi-value")]), width=3),
                ], className="g-3 mb-3"),
                dbc.Row([
                    dbc.Col(html.Div(className="pbi-card", children=dcc.Graph(figure=px.area(dff.groupby('Date')['Gross_Value'].sum().reset_index(), x='Date', y='Gross_Value', title="Total Revenue Trend", color_discrete_sequence=[K_TEAL]).update_layout(pbi_layout))), width=8),
                    dbc.Col(html.Div(className="pbi-card", children=dcc.Graph(figure=fig_donut)), width=4),
                ], className="g-3 mb-3"),
                dbc.Row([
                    dbc.Col(html.Div(className="pbi-card", children=dcc.Graph(figure=px.bar(dff.groupby('Customer')['QTY'].sum().nlargest(10).reset_index(), x='QTY', y='Customer', orientation='h', title="Top Customers", color_discrete_sequence=[K_DARK]).update_layout(pbi_layout))), width=5),
                    dbc.Col(html.Div(className="pbi-card", children=dcc.Graph(figure=fig_pareto)), width=7),
                ], className="g-3")
            ])

        else:
            # SHEET 2 Visuals
            # 1. Price vs Quantity Scatter
            fig_scatter = px.scatter(dff, x='Unit_Price', y='QTY', color='Model', title="Price vs Quantity", color_discrete_sequence=[K_TEAL, K_CLAY, K_DARK])
            fig_scatter.update_layout(pbi_layout)

            # 2. Count of Item Code by Model
            fig_model_bar = px.bar(dff.groupby('Model').size().reset_index(name='count'), x='Model', y='count', title="Count of ITEM_CODE by MODEL", color_discrete_sequence=[K_TEAL])
            fig_model_bar.update_layout(pbi_layout)

            # 3. Sum of QTY and Sum of Gross Value by Transporter (Grouped Bar)
            trans_data = dff.groupby('Transporter')[['QTY', 'Gross_Value']].sum().reset_index()
            fig_trans = go.Figure()
            if not trans_data.empty:
                fig_trans.add_trace(go.Bar(y=trans_data['Transporter'], x=trans_data['QTY'], name='Sum of QTY', orientation='h', marker_color=K_TEAL))
                fig_trans.add_trace(go.Bar(y=trans_data['Transporter'], x=trans_data['Gross_Value'], name='Sum of Gross Value', orientation='h', marker_color=K_DARK))
            fig_trans.update_layout(pbi_layout, barmode='group', title="Sum of QTY and GROSS_VALUE by TRANSPORTER")

            return html.Div([
                dbc.Row([
                    dbc.Col(html.Div(className="pbi-card text-center", children=[html.Div("Total Invoices", className="kpi-title"), html.Div(f"{len(dff):,}", className="kpi-value")]), width=3),
                    dbc.Col(html.Div(className="pbi-card text-center", children=[html.Div("Unique Customers", className="kpi-title"), html.Div(f"{dff['Customer'].nunique()}", className="kpi-value")]), width=3),
                    dbc.Col(html.Div(className="pbi-card text-center", children=[html.Div("Avg Lead Time (Days)", className="kpi-title"), html.Div(f"{dff['Lead_Time'].mean():.1f}", className="kpi-value")]), width=3),
                    dbc.Col(html.Div(className="pbi-card text-center", children=[html.Div("On-Time Dispatch %", className="kpi-title"), html.Div(f"{dff['OnTime'].mean()*100:.1f}%", className="kpi-value")]), width=3),
                ], className="g-3 mb-3"),
                dbc.Row([
                    dbc.Col(html.Div(className="pbi-card", children=dcc.Graph(figure=fig_scatter)), width=4),
                    dbc.Col(html.Div(className="pbi-card", children=dcc.Graph(figure=fig_model_bar)), width=4),
                    dbc.Col(html.Div(className="pbi-card", children=dcc.Graph(figure=fig_trans)), width=4),
                ], className="g-3 mb-3"),
                dbc.Row([
                    dbc.Col(html.Div(className="pbi-card", children=dcc.Graph(figure=px.bar(dff.groupby('Transporter')['QTY'].sum().nlargest(10).reset_index(), x='QTY', y='Transporter', orientation='h', title="Top Transporters", color_discrete_sequence=[K_TEAL]).update_layout(pbi_layout))), width=4),
                    dbc.Col(html.Div(className="pbi-card", children=dcc.Graph(figure=px.bar(dff.groupby('Item_Description')['QTY'].sum().nlargest(5).reset_index(), x='QTY', y='Item_Description', orientation='h', title="Top Ordered Items", color_discrete_sequence=[K_TEAL]).update_layout(pbi_layout))), width=4),
                    dbc.Col(html.Div(className="pbi-card", children=dcc.Graph(figure=px.line(dff.groupby('Year')['QTY'].sum().reset_index(), x='Year', y='QTY', title="Year Wise Sales", color_discrete_sequence=[K_TEAL]).update_layout(pbi_layout))), width=4),
                ], className="g-3")
            ])
    except Exception as e:
        import traceback
        traceback.print_exc()
        return html.Div(f"Error in Callback: {str(e)}")

if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=8050)
