import requests
from bs4 import BeautifulSoup as bs
import pandas as pd
import glob
import dash
from dash import dcc
from dash import html
from dash import Dash, dash_table
from dash.dependencies import Input, Output
import plotly.express as px

"""
Dashboard Creation
"""

stylesheet = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

### pandas dataframe to html table
def generate_table(dataframe, max_rows=10):
    return html.Table([
        html.Thead(
            html.Tr([html.Th(col) for col in dataframe.columns])
        ),
        html.Tbody([
            html.Tr([
                html.Td(dataframe.iloc[i][col]) for col in dataframe.columns
            ]) for i in range(min(len(dataframe), max_rows))
        ])
    ])

app = dash.Dash(__name__, external_stylesheets=stylesheet)
server = app.server

df = pd.read_csv("./data/books2.csv")

app = Dash(__name__)

df['rating_count'] = [i.replace(',','') for i in df.rating_count]
df['num_reviews'] = [i.replace(',','') for i in df.num_reviews]

df['avg_rating'] = df['avg_rating'].astype(float)
df['rating_count'] = pd.to_numeric(df.rating_count, errors="ignore")
df['num_reviews'] = pd.to_numeric(df.num_reviews, errors="ignore")

fig = px.scatter(df, x="rating_count", y="avg_rating",
                 size="num_reviews",color="title", hover_name="avg_rating",
                 log_x=True, labels={
                     "rating_count": "Rating Count",
                     "avg_rating": "Average Rating",
                     "num_reviews": "Number of Reviews",
                     "title": "Title"
                 },
                title="Interactive scatter plot of Average Rating, Rating Count, filter by Number of Reviews and Title")

fig.update_layout(xaxis_range=[1,10])

app.layout = html.Div(children = [
    html.H1(children = 'Goodreads Dashboard',
            style={'textAlign' : 'center'}),
    html.P(['This Dashboard contains a Table of 300 books from Goodreads website.',html.Br(),
            'The Dashboard was created to help user find the book they need with affiliated information.',html.Br(),
            'At the same time, a scatterplot was created to look into the relationship between average ratings and rating count of each book']),
    html.H2('Goodreads Book Look Up Table',
            style={'textAlign' : 'center'}),
    html.P(['This Table has information of 300 books from Goodreads website']),
    html.H3('How to use:'),
    html.P(['Simply type in the "filter data..." box of the column you want to search and press enter. To reset, delete the text and press enter again. You can use a combination of filter across different columns. Also, the columns are case sensitive and make sure you are on the first page of the table when you type in the filter to get the full result', html.Br(), 
            'For example, "Blood" in the Title column and "J.K." in the Author column will give us "Harry Porter and the Half-Blood Prince', html.Br(),
            'At the same time, if you want to check whether or not a word shows up in a book''s description, you can type that word in the Description column filter and press enter. All books that have that word in theirs description will show up']),
    dash_table.DataTable(
        columns=[
            {'name': 'Book ID', 'id': 'book_id', 'type': 'numeric'},
            {'name': 'Title', 'id': 'title', 'type': 'text'},
            {'name': 'Author', 'id': 'author', 'type': 'text'},
            {'name': 'Average Rating', 'id': 'avg_rating', 'type': 'numeric'},
            {'name': 'Rating Count', 'id': 'rating_count', 'type': 'numeric'},
            {'name': 'Description', 'id': 'description', 'type': 'text'},
            {'name': 'Number of Reviews', 'id': 'num_reviews', 'type': 'numeric'}
        ],
        
        page_current=0,
        page_size=20,
        #data=df.to_dict('records'),
        id = 'table-sorting-filtering',
        page_action='custom',
        filter_action='custom',
        filter_query = '',
        sort_action='custom',
        sort_mode='multi',
        sort_by=[],

        
        style_data={
            'width': '150px', 'minWidth': '150px', 'maxWidth': '200px',
            'overflow': 'hidden',
            'textOverflow': 'ellipsis',
        }
    ),
    html.Div([
    html.P(['This scatterplot explores the relationship between Average Rating and Rating Count. The size of the bubble is determined by the number of total reviews']),
    html.H3('How to use:'),
    html.P(['Click and drag an area in the graph to zoom in. Hover over a bubble to see the details of that bubble.', html.Br(),
            'Double click a title in the legend to show only the buble corresponding to that title, click another title to add it in the graph. double click the legend again to reset']),
    html.H3('Hypothesis that prompt this scatter plot:'),
    html.P(['The higher the rating count and number of reviews, the higher the average rating']),
    dcc.Graph(id="scatter-plot",
    figure = fig),
    html.H3('Insights:'),
    html.P(['High rating count does not correlate to high average rating.', html.Br(),
            'High number of reviews have some positive relation ship with average rating', html.Br(),
            'High number of reviews correlates to high rating count']),
    html.H3('Limitations:'),
    html.P(['There are only 300 books in the data set', html.Br(),
            'the legend of the scatterplot does not have a filter, limiting the efficiency of the plot', html.Br(),
            'Cannot scrape the genre of the books, limitting how much we can analyze the data'])
    
])
    ])

operators = [['ge ', '>='],
             ['le ', '<='],
             ['lt ', '<'],
             ['gt ', '>'],
             ['ne ', '!='],
             ['eq ', '='],
             ['contains '],
             ['datestartswith ']]


def split_filter_part(filter_part):
    for operator_type in operators:
        for operator in operator_type:
            if operator in filter_part:
                name_part, value_part = filter_part.split(operator, 1)
                name = name_part[name_part.find('{') + 1: name_part.rfind('}')]

                value_part = value_part.strip()
                v0 = value_part[0]
                if (v0 == value_part[-1] and v0 in ("'", '"', '`')):
                    value = value_part[1: -1].replace('\\' + v0, v0)
                else:
                    try:
                        value = float(value_part)
                    except ValueError:
                        value = value_part

                # word operators need spaces after them in the filter string,
                # but we don't want these later
                return name, operator_type[0].strip(), value

    return [None] * 3


@app.callback(
    Output('table-sorting-filtering', 'data'),
    Input('table-sorting-filtering', "page_current"),
    Input('table-sorting-filtering', "page_size"),
    Input('table-sorting-filtering', 'sort_by'),
    Input('table-sorting-filtering', 'filter_query'))

def update_table(page_current, page_size, sort_by, filter):
    filtering_expressions = filter.split(' && ')
    dff = df
    for filter_part in filtering_expressions:
        col_name, operator, filter_value = split_filter_part(filter_part)

        if operator in ('eq', 'ne', 'lt', 'le', 'gt', 'ge'):
            # these operators match pandas series operator method names
            dff = dff.loc[getattr(dff[col_name], operator)(filter_value)]
        elif operator == 'contains':
            dff = dff.loc[dff[col_name].str.contains(filter_value)]
        elif operator == 'datestartswith':
            # this is a simplification of the front-end filtering logic,
            # only works with complete fields in standard format
            dff = dff.loc[dff[col_name].str.startswith(filter_value)]

    if len(sort_by):
        dff = dff.sort_values(
            [col['column_id'] for col in sort_by],
            ascending=[
                col['direction'] == 'asc'
                for col in sort_by
            ],
            inplace=False
        )

    page = page_current
    size = page_size
    return dff.iloc[page * size: (page + 1) * size].to_dict('records')

if __name__ == '__main__':
    app.run_server(debug=True)