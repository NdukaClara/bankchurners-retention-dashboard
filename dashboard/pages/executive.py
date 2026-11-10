# dashboard/pages/executive.py
# Builds the Executive Overview from the shared analysis-ready DataFrame.

from dash import dcc, html
import plotly.express as px


# -----------------------------------------------------------------------------
# 1. Shared visual tokens and chart formatting for this page.
# -----------------------------------------------------------------------------
INK = "#193247"
MUTED = "#627589"
GRID = "#E8EEF3"
TRANSPARENT = "rgba(0, 0, 0, 0)"
FONT_FAMILY = "Inter, -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif"
ACCENT_BAR = "#367B78"


def _style_bar_figure(figure, height=300):
    """Apply consistent, compact Plotly styling without changing chart data."""
    figure.update_layout(
        template="plotly_white",
        height=height,
        margin={"l": 54, "r": 16, "t": 54, "b": 48},
        font={"family": FONT_FAMILY, "size": 11, "color": INK},
        title={
            "font": {"family": FONT_FAMILY, "size": 15, "color": INK},
            "x": 0.03,
            "xanchor": "left",
            "y": 0.97,
            "yanchor": "top",
        },
        paper_bgcolor=TRANSPARENT,
        plot_bgcolor=TRANSPARENT,
        hoverlabel={
            "bgcolor": INK,
            "bordercolor": INK,
            "font": {"family": FONT_FAMILY, "size": 12, "color": "white"},
        },
    )
    figure.update_xaxes(
        showgrid=False,
        zeroline=False,
        showline=False,
        ticks="",
        automargin=True,
        tickfont={"size": 12, "color": MUTED},
        title_font={"size": 12, "color": MUTED},
    )
    figure.update_yaxes(
        showgrid=True,
        gridcolor=GRID,
        zeroline=False,
        showline=False,
        ticks="",
        automargin=True,
        tickfont={"size": 12, "color": MUTED},
        title_font={"size": 12, "color": MUTED},
    )
    return figure


def _make_kpi_card(label, value, note):
    """Create one compact, consistently styled portfolio KPI card."""
    return html.Div(
        [
            html.Div(label, className="kpi-label"),
            html.Div(value, className="kpi-value"),
            html.Div(note, className="kpi-note"),
        ],
        className="kpi-card",
    )

def _make_insight_metric(label, segment, rate, customers, tone):
    """Render one comparison value in the portfolio readout."""
    return html.Div(
        [
            html.Span(label, className="insight-metric__label"),
            html.Strong(f"{rate:.1f}%", className="insight-metric__rate"),
            html.Span(
                f"{segment} · n={customers:,}",
                className="insight-metric__detail",
            ),
        ],
        className=f"insight-metric insight-metric--{tone}",
    )

# -----------------------------------------------------------------------------
# 2. Build the Executive Overview page.
# -----------------------------------------------------------------------------
def build_page(df):
    # Keep the established KPI definitions and sample-level calculations.
    total_customers = df["CLIENTNUM"].nunique()
    attrited_customers = int(
        df["Attrition_Flag"].eq("Attrited Customer").sum()
    )
    overall_attrition_pct = attrited_customers / total_customers * 100

    mean_transactions = df["Total_Trans_Ct"].mean()
    mean_utilization = df["Avg_Utilization_Ratio"].mean()
    mean_relationships = df["Total_Relationship_Count"].mean()

    # Summarise observed attrition by the existing retention-priority bands.
    priority_order = ["High", "Medium", "Low"]
    priority_summary = (
        df.groupby("Retention_Priority_Band")
        .agg(
            customers=("CLIENTNUM", "nunique"),
            attrited=(
                "Attrition_Flag",
                lambda values: values.eq("Attrited Customer").sum(),
            ),
        )
    )
    priority_summary["attrition_rate_pct"] = (
        priority_summary["attrited"]
        / priority_summary["customers"]
        * 100
    )
    priority_summary = (
        priority_summary.reindex(priority_order).reset_index()
    )

    # Build two compact comparison metrics from the existing priority summary.
    valid_priority = priority_summary.dropna(
        subset=["attrition_rate_pct", "customers"]
    )
    if not valid_priority.empty:
        highest_priority = valid_priority.loc[
            valid_priority["attrition_rate_pct"].idxmax()
        ]
        lowest_priority = valid_priority.loc[
            valid_priority["attrition_rate_pct"].idxmin()
        ]
        priority_metrics = html.Div(
            [
                _make_insight_metric(
                    "Highest",
                    f"{highest_priority['Retention_Priority_Band']} priority",
                    highest_priority["attrition_rate_pct"],
                    int(highest_priority["customers"]),
                    "high",
                ),
                _make_insight_metric(
                    "Lowest",
                    f"{lowest_priority['Retention_Priority_Band']} priority",
                    lowest_priority["attrition_rate_pct"],
                    int(lowest_priority["customers"]),
                    "low",
                ),
            ],
            className="insight-metrics",
        )
    else:
        priority_metrics = html.Span(
            "No priority-band records",
            className="insight-panel__empty",
        )

    # Main overview chart: the retrospective priority-band comparison.
    priority_fig = px.bar(
        priority_summary,
        x="Retention_Priority_Band",
        y="attrition_rate_pct",
        text="attrition_rate_pct",
        custom_data=["customers", "attrited"],
        category_orders={"Retention_Priority_Band": priority_order},
        title="Observed attrition by retention-priority band",
        color="Retention_Priority_Band",
        color_discrete_map={
            "High": "#B5473C",
            "Medium": "#D79A3B",
            "Low": "#2C8178",
        },
    )
    priority_fig.update_traces(
        marker_line_width=0,
        texttemplate="%{y:.1f}%",
        textposition="outside",
        cliponaxis=False,
        hovertemplate=(
            "<b>%{x} priority</b><br>"
            "Observed attrition rate: %{y:.2f}%<br>"
            "Customers: %{customdata[0]:,.0f}<br>"
            "Attrited: %{customdata[1]:,.0f}"
            "<extra></extra>"
        ),
    )
    _style_bar_figure(priority_fig)
    priority_fig.update_layout(showlegend=False, bargap=0.42)
    priority_fig.update_xaxes(title_text="Priority band")
    priority_fig.update_yaxes(
        title_text="Attrition rate (%)",
        range=[0, 85],
    )

    # Summarise observed attrition by the existing age bands.
    age_order = ["Under 35", "35–44", "45–54", "55+"]
    age_summary = (
        df.groupby("Age_Band")
        .agg(
            customers=("CLIENTNUM", "nunique"),
            attrited=(
                "Attrition_Flag",
                lambda values: values.eq("Attrited Customer").sum(),
            ),
        )
    )
    age_summary["attrition_rate_pct"] = (
        age_summary["attrited"]
        / age_summary["customers"]
        * 100
    )
    age_summary = age_summary.reindex(age_order).reset_index()

    # Supporting chart: age-band rates, with denominator detail on hover.
    age_fig = px.bar(
        age_summary,
        x="Age_Band",
        y="attrition_rate_pct",
        text="attrition_rate_pct",
        custom_data=["customers", "attrited"],
        category_orders={"Age_Band": age_order},
        title="Observed attrition by age band",
        color_discrete_sequence=[ACCENT_BAR],
    )
    age_fig.update_traces(
        marker_line_width=0,
        texttemplate="%{y:.1f}%",
        textposition="outside",
        cliponaxis=False,
        hovertemplate=(
            "<b>%{x}</b><br>"
            "Observed attrition rate: %{y:.2f}%<br>"
            "Customers: %{customdata[0]:,.0f}<br>"
            "Attrited: %{customdata[1]:,.0f}"
            "<extra></extra>"
        ),
    )
    _style_bar_figure(age_fig)
    age_fig.update_layout(showlegend=False, bargap=0.42)
    age_fig.update_xaxes(title_text="Age band")
    age_fig.update_yaxes(
        title_text="Attrition rate (%)",
        range=[0, 20],
    )

    # Status mix provides portfolio context; it is not a churn forecast.
    status_order = ["Existing Customer", "Attrited Customer"]
    status_summary = (
        df["Attrition_Flag"]
        .value_counts()
        .reindex(status_order, fill_value=0)
        .rename_axis("Customer_Status")
        .reset_index(name="Customers")
    )
    status_fig = px.pie(
        status_summary,
        names="Customer_Status",
        values="Customers",
        title="Customer status mix",
        color="Customer_Status",
        color_discrete_map={
            "Existing Customer": "#258C83",
            "Attrited Customer": "#D96C5F",
        },
        hole=0.66,
    )
    status_fig.update_traces(
        textinfo="percent",
        textposition="inside",
        marker={"line": {"color": "#FFFFFF", "width": 3}},
        hovertemplate=(
            "<b>%{label}</b><br>"
            "Customers: %{value:,.0f}<br>"
            "Share of dataset: %{percent}"
            "<extra></extra>"
        ),
    )
    status_fig.update_layout(
        template="plotly_white",
        height=300,
        margin={"l": 12, "r": 12, "t": 54, "b": 44},
        font={"family": FONT_FAMILY, "size": 10, "color": INK},
        title={
            "font": {"family": FONT_FAMILY, "size": 14, "color": INK},
            "x": 0.03,
            "xanchor": "left",
            "y": 0.97,
            "yanchor": "top",
        },
        paper_bgcolor=TRANSPARENT,
        plot_bgcolor=TRANSPARENT,
        showlegend=True,
        legend={
            "orientation": "h",
            "yanchor": "bottom",
            "y": -0.12,
            "xanchor": "center",
            "x": 0.5,
            "font": {"size": 9, "color": MUTED},
        },
        hoverlabel={
            "bgcolor": INK,
            "bordercolor": INK,
            "font": {"family": FONT_FAMILY, "size": 12, "color": "white"},
        },
        annotations=[
            {
                "text": f"<b>{total_customers:,}</b><br>customers",
                "x": 0.5,
                "y": 0.5,
                "showarrow": False,
                "font": {"family": FONT_FAMILY, "size": 13, "color": INK},
            }
        ],
    )

    # Six metrics now form a responsive, balanced KPI strip.
    kpi_cards = html.Div(
        [
            _make_kpi_card(
                "Unique customers",
                f"{total_customers:,}",
                "Distinct customer IDs",
            ),
            _make_kpi_card(
                "Observed attrition",
                f"{overall_attrition_pct:.2f}%",
                "Share labelled as attrited",
            ),
            _make_kpi_card(
                "Attrited customers",
                f"{attrited_customers:,}",
                "Records labelled as attrited",
            ),
            _make_kpi_card(
                "Mean transaction count",
                f"{mean_transactions:.2f}",
                "Average count per customer",
            ),
            _make_kpi_card(
                "Mean utilisation",
                f"{mean_utilization:.2%}",
                "Mean of customer-level ratios",
            ),
            _make_kpi_card(
                "Mean product relationships",
                f"{mean_relationships:.2f}",
                "Not customer lifetime value",
            ),
        ],
        className="kpi-grid",
    )

    # -------------------------------------------------------------------------
    # 3. Assemble the page in a clear heading -> KPI -> evidence hierarchy.
    # -------------------------------------------------------------------------
    return html.Div(
        [
            html.Div(
                [
                    html.H2("Executive overview", className="page-title"),
                ],
                className="page-heading",
            ),
            kpi_cards,
                        html.Div(
                [
                    html.Div(
                        [
                            html.Span(
                                "PRIORITY BANDS",
                                className="insight-panel__label",
                            ),
                            priority_metrics,
                        ],
                        className="insight-panel__copy",
                    ),
                ],
                className="insight-panel",
            ),
            html.Div(
                [
                    html.Section(
                        dcc.Graph(
                            figure=priority_fig,
                            config={"displayModeBar": False, "responsive": True},
                            className="dashboard-graph",
                            style={"height": "300px", "width": "100%"},
                        ),
                        className="chart-card chart-card--priority",
                    ),
                    html.Section(
                        dcc.Graph(
                            figure=age_fig,
                            config={"displayModeBar": False, "responsive": True},
                            className="dashboard-graph",
                            style={"height": "300px", "width": "100%"},
                        ),
                        className="chart-card chart-card--age",
                    ),
                    html.Section(
                        dcc.Graph(
                            figure=status_fig,
                            config={"displayModeBar": False, "responsive": True},
                            className="dashboard-graph",
                            style={"height": "300px", "width": "100%"},
                        ),
                        className="chart-card chart-card--status",
                    ),
                ],
                className="executive-chart-grid",
            ),
        ],
        className="page-section",
    )
