# dashboard/app.py
# App shell: load the analysis-ready dataset once, style the two page modules,
# and apply the shared Retention Analysis filters.

from pathlib import Path

import pandas as pd
from dash import Dash, Input, Output, dcc, html

from pages.executive import build_page as build_executive_page
from pages.retention import build_page as build_retention_page


# -----------------------------------------------------------------------------
# 1. Load the shared dataset and prepare display-ordered filter options.
# -----------------------------------------------------------------------------
project_root = Path(__file__).resolve().parents[1]
data_path = (
    project_root
    / "data"
    / "processed"
    / "BankChurners_analysis_ready.csv"
)

if not data_path.exists():
    raise FileNotFoundError(f"Dashboard data file not found: {data_path}")

df = pd.read_csv(data_path)


def _ordered_options(series, preferred_order):
    """Order known categories for easier scanning without dropping any labels."""
    available = series.dropna().astype(str).unique().tolist()
    ordered = [value for value in preferred_order if value in available]
    return ordered + [value for value in available if value not in ordered]


age_options = _ordered_options(
    df["Age_Band"],
    ["Under 35", "35–44", "45–54", "55+", "55–64", "65+"],
)
income_options = _ordered_options(
    df["Income_Category"],
    [
        "Less than $40K",
        "$40K - $60K",
        "$60K - $80K",
        "$80K - $120K",
        "$120K +",
        "Unknown",
    ],
)
card_options = _ordered_options(
    df["Card_Category"],
    ["Blue", "Silver", "Gold", "Platinum"],
)

total_customers = int(df["CLIENTNUM"].nunique())


# -----------------------------------------------------------------------------
# 2. Shared scope banner for the Retention Analysis filters.
# -----------------------------------------------------------------------------
def _scope_summary(customer_count, full_count):
    is_full_sample = customer_count == full_count
    return html.Div(
        [
            html.Div(
                [
                    html.Span("CURRENT VIEW", className="scope-summary__label"),
                    html.Strong(
                        f"{customer_count:,} customers",
                        className="scope-summary__count",
                    ),
                    html.Span(
                        "Full analysis sample"
                        if is_full_sample
                        else f"Filtered from {full_count:,} customers",
                        className="scope-summary__detail",
                    ),
                ],
                className="scope-summary__main",
            ),
        ],
        className="scope-summary",
    )


# -----------------------------------------------------------------------------
# 3. Create the app shell, header, navigation, and filter controls.
# -----------------------------------------------------------------------------
app = Dash(
    __name__,
    assets_folder=str(Path(__file__).resolve().parent / "assets"),
)
app.title = "Customer Retention Intelligence"

app.layout = html.Div(
    [
        html.Header(
            html.Div(
                [
                    html.Div(
                        [
                            html.Div("RI", className="brand-mark"),
                            html.Div(
                                [
                                    html.P(
                                        "MIT 8339  /  BUSINESS INTELLIGENCE & DECISION SUPPORT",
                                        className="app-overline",
                                    ),
                                    html.H1(
                                        "Customer Retention & Performance Intelligence",
                                        className="app-title",
                                    ),
                                ],
                                className="brand-copy",
                            ),
                        ],
                        className="brand-lockup",
                    ),
                ],
                className="app-header__inner",
            ),
            className="app-header",
        ),
        html.Main(
            dcc.Tabs(
                id="dashboard-tabs",
                value="executive",
                className="dashboard-tabs",
                parent_className="dashboard-tabs-shell",
                colors={
                    "border": "#E3EAF0",
                    "primary": "#167A73",
                    "background": "#EEF2F6",
                },
                children=[
                    dcc.Tab(
                        label="Executive Overview",
                        value="executive",
                        className="dashboard-tab",
                        selected_className="dashboard-tab--selected",
                        children=build_executive_page(df),
                    ),
                    dcc.Tab(
                        label="Retention Analysis",
                        value="retention",
                        className="dashboard-tab",
                        selected_className="dashboard-tab--selected",
                        children=html.Div(
                            [
                                html.Div(
                                    [
                                        html.Div(
                                            [
                                                html.H2(
                                                    "Retention analysis",
                                                    className="page-title",
                                                ),
                                            ],
                                            className="page-heading",
                                        ),
                                        html.Section(
                                            [
                                                html.Div(
                                                    [
                                                        html.Div(
                                                            [
                                                                html.Span(
                                                                    "FILTERS",
                                                                    className="filter-panel__title",
                                                                ),
                                                                html.P(
                                                                    "Blank = all categories · filters apply to all charts",
                                                                    className="filter-panel__caption",
                                                                ),
                                                            ]
                                                        ),
                                                        html.Button(
                                                            "Reset filters",
                                                            id="reset-retention-filters",
                                                            n_clicks=0,
                                                            type="button",
                                                            className="reset-button",
                                                        ),
                                                    ],
                                                    className="filter-panel__header",
                                                ),
                                                html.Div(
                                                    [
                                                        html.Div(
                                                            [
                                                                html.Label(
                                                                    "Age band",
                                                                    htmlFor="age-band-filter",
                                                                    className="filter-label",
                                                                ),
                                                                dcc.Dropdown(
                                                                    id="age-band-filter",
                                                                    options=[
                                                                        {"label": band, "value": band}
                                                                        for band in age_options
                                                                    ],
                                                                    value=[],
                                                                    multi=True,
                                                                    clearable=True,
                                                                    placeholder="All age bands",
                                                                    className="filter-dropdown",
                                                                ),
                                                            ],
                                                            className="filter-control",
                                                        ),
                                                        html.Div(
                                                            [
                                                                html.Label(
                                                                    "Income category",
                                                                    htmlFor="income-category-filter",
                                                                    className="filter-label",
                                                                ),
                                                                dcc.Dropdown(
                                                                    id="income-category-filter",
                                                                    options=[
                                                                        {"label": category, "value": category}
                                                                        for category in income_options
                                                                    ],
                                                                    value=[],
                                                                    multi=True,
                                                                    clearable=True,
                                                                    placeholder="All income categories",
                                                                    className="filter-dropdown",
                                                                ),
                                                            ],
                                                            className="filter-control",
                                                        ),
                                                        html.Div(
                                                            [
                                                                html.Label(
                                                                    "Card category",
                                                                    htmlFor="card-category-filter",
                                                                    className="filter-label",
                                                                ),
                                                                dcc.Dropdown(
                                                                    id="card-category-filter",
                                                                    options=[
                                                                        {"label": category, "value": category}
                                                                        for category in card_options
                                                                    ],
                                                                    value=[],
                                                                    multi=True,
                                                                    clearable=True,
                                                                    placeholder="All card categories",
                                                                    className="filter-dropdown",
                                                                ),
                                                            ],
                                                            className="filter-control",
                                                        ),
                                                    ],
                                                    className="filter-grid",
                                                ),
                                            ],
                                            className="filter-panel",
                                        ),
                                        html.Div(
                                            _scope_summary(total_customers, total_customers),
                                            id="filter-scope-summary",
                                        ),
                                        html.Div(
                                            id="retention-page-content",
                                            children=build_retention_page(df),
                                        ),
                                    ],
                                    className="retention-page",
                                ),
                            ],
                            className="tab-page",
                        ),
                    ),
                ],
            ),
            className="app-main",
        ),
    ],
    className="app-shell",
)


# -----------------------------------------------------------------------------
# 4. Rebuild Retention Analysis for the selected segment combination.
# -----------------------------------------------------------------------------
@app.callback(
    Output("retention-page-content", "children"),
    Output("filter-scope-summary", "children"),
    Input("age-band-filter", "value"),
    Input("income-category-filter", "value"),
    Input("card-category-filter", "value"),
)
def update_retention_page(
    selected_age_bands,
    selected_income_categories,
    selected_card_categories,
):
    # Empty selections mean all categories; this keeps reset/clear intuitive.
    selected_ages = selected_age_bands or age_options
    selected_incomes = selected_income_categories or income_options
    selected_cards = selected_card_categories or card_options

    filtered_df = df.loc[
        df["Age_Band"].astype(str).isin(selected_ages)
        & df["Income_Category"].astype(str).isin(selected_incomes)
        & df["Card_Category"].astype(str).isin(selected_cards)
    ].copy()

    selected_customer_count = int(filtered_df["CLIENTNUM"].nunique())
    return (
        build_retention_page(filtered_df),
        _scope_summary(selected_customer_count, total_customers),
    )


# Reset all three controls to their blank = all-categories state.
@app.callback(
    Output("age-band-filter", "value"),
    Output("income-category-filter", "value"),
    Output("card-category-filter", "value"),
    Input("reset-retention-filters", "n_clicks"),
    prevent_initial_call=True,
)
def reset_retention_filters(_click_count):
    return [], [], []


# Run locally from the project root with: python dashboard/app.py
# Hide the development toolbar for a clean presentation while retaining debug logs.
if __name__ == "__main__":
    app.run(debug=True, port=8050, dev_tools_ui=False)
