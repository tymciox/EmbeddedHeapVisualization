import dash
from dash import dcc, html
import dash_table
from dash.dependencies import Input, Output
import pandas as pd
import base64
from plotly import graph_objects as go
import io
from plotly.subplots import make_subplots

# ... (your existing imports)

# Create the main app
app = dash.Dash(__name__)

# Define the app layout
app.layout = html.Div([
    html.H1("Unreleased Memory Over Time"),
    dcc.Upload(
        id='upload-data',
        children=html.Button('Select File'),
        multiple=False
    ),
    html.Div(id='graph-table-container', children=[]),
])

# Callback to update the layout with graphs and tables
@app.callback(
    Output('graph-table-container', 'children'),
    [Input('upload-data', 'contents')]
)
def update_layout(contents):
    if contents:
        # Extracting the data from the uploaded file
        content_type, content_string = contents.split(',')
        decoded = base64.b64decode(content_string)
        file_path = io.StringIO(decoded.decode('utf-8'))

        data = {'time': [], 'size': [], 'source_file': [], 'line': [], 'thread': []}

        for line in file_path:
            parts = line.strip().split(',')

            # Check if there are enough parts in the line
            if len(parts) == 5:
                time = int(parts[0])
                size = int(parts[1])
                src = parts[2]
                line_number = int(parts[3])
                thread = parts[4]

                data['time'].append(time)
                data['size'].append(size)
                data['source_file'].append(src)
                data['line'].append(line_number)
                data['thread'].append(thread)
            else:
                print(f"Ignored line: {line.strip()} - Wrong format")

        df = pd.DataFrame(data)

        # Create subplots with shared x-axis
        graphs_and_tables = []
        for thread in df['thread'].unique():
            thread_data = df[df['thread'] == thread]

            # Create a graph for each thread
            fig = make_subplots(rows=1, cols=1)
            fig.add_trace(
                go.Scatter(
                    x=thread_data['time'],
                    y=thread_data['size'].cumsum(),
                    mode='markers+lines',
                    name=thread,
                    hovertext=f"src:{thread_data['source_file']}<br>line:{thread_data['line']}",  # Include comments as hover text
                    hoverinfo='text'  # Show hover text
                )
            )
            fig.update_layout(
                title_text=f"Unreleased Memory Over Time ({thread})",
                xaxis_title="Time",
                yaxis_title="Cumulative Unreleased Memory Usage"
            )

            # Create data for the table
            table_data = thread_data.to_dict('records')

            # Create a table for each graph
            table = dash_table.DataTable(
                id={'type': 'table', 'index': thread},
                data=table_data,
                style_table={'maxHeight': '300px', 'overflowY': 'auto'},
                fixed_rows={'headers': True, 'data': 0},
                selected_rows=[],
            )

            graphs_and_tables.append(
                html.Div([
                    dcc.Graph(figure=fig),
                    table
                ])
            )

        return graphs_and_tables

    # If no contents, return an empty list
    return []


# Run the application
if __name__ == '__main__':
    app.run_server(debug=True)
