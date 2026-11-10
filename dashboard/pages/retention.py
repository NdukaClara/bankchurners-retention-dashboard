# dashboard/pages/retention.py
# Builds the Retention Analysis charts from the DataFrame passed in by app.py.

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from dash import dcc, html


# -----------------------------------------------------------------------------
# 1. Shared visual tokens and compact chart styling.
# -----------------------------------------------------------------------------
INK = "#193247"
MUTED = "#627589"
GRID = "#E8EEF3"
TRANSPARENT = "rgba(0, 0, 0, 0)"
FONT_FAMILY = "Inter, -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif"
ACCENT_BAR = "#367B78"


def _style_bar_figure(figure, height=330):
    """Standardise plot presentation while leaving its measures unchanged."""
    figure.update_layout(
        template="plotly_white",
        height=height,
        margin={"l": 56, "r": 18, "t": 56, "b": 54},
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


def _keep_present_segments(summary):
    """Avoid blank category slots when a dashboard filter removes a segment."""
    return summary.loc[
        summary["customers"].notna() & summary["customers"].gt(0)
    ].copy()

def _make_signal_metric(label, segment, rate, customers, tone):
    """Render one current-view segment rate in the readout strip."""
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
# 2. Build the Retention Analysis page.
# -----------------------------------------------------------------------------
def build_page(df):
    # Summarise observed attrition by transaction-frequency band.
    frequency_order = ["Low (≤Q1)", "Middle (Q1–Q3)", "High (>Q3)"]
    frequency_summary = (
        df.groupby("Transaction_Frequency_Band")
        .agg(
            customers=("CLIENTNUM", "nunique"),
            attrited=(
                "Attrition_Flag",
                lambda values: values.eq("Attrited Customer").sum(),
            ),
        )
    )
    frequency_summary["attrition_rate_pct"] = (
        frequency_summary["attrited"]
        / frequency_summary["customers"]
        * 100
    )
    frequency_summary = (
        frequency_summary.reindex(frequency_order).reset_index()
    )
    frequency_summary = _keep_present_segments(frequency_summary)
    frequency_summary["rate_label"] = frequency_summary.apply(
        lambda row: (
            f"{row['attrition_rate_pct']:.1f}%<br>"
            f"n={int(row['customers']):,}"
        ),
        axis=1,
    )

    if not frequency_summary.empty:
        highest_frequency = frequency_summary.loc[
            frequency_summary["attrition_rate_pct"].idxmax()
        ]
        lowest_frequency = frequency_summary.loc[
            frequency_summary["attrition_rate_pct"].idxmin()
        ]
        if (
            highest_frequency["Transaction_Frequency_Band"]
            == lowest_frequency["Transaction_Frequency_Band"]
        ):
            frequency_metrics = html.Div(
                [
                    _make_signal_metric(
                        "Only segment",
                        highest_frequency["Transaction_Frequency_Band"],
                        highest_frequency["attrition_rate_pct"],
                        int(highest_frequency["customers"]),
                        "high",
                    )
                ],
                className="insight-metrics insight-metrics--single",
            )
        else:
            frequency_metrics = html.Div(
                [
                    _make_signal_metric(
                        "Highest",
                        highest_frequency["Transaction_Frequency_Band"],
                        highest_frequency["attrition_rate_pct"],
                        int(highest_frequency["customers"]),
                        "high",
                    ),
                    _make_signal_metric(
                        "Lowest",
                        lowest_frequency["Transaction_Frequency_Band"],
                        lowest_frequency["attrition_rate_pct"],
                        int(lowest_frequency["customers"]),
                        "low",
                    ),
                ],
                className="insight-metrics",
            )
    else:
        frequency_metrics = html.Span(
            "No matching customers",
            className="insight-panel__empty",
        )
        
    # Main retention chart: observed rates across activity-frequency bands.
    frequency_fig = px.bar(
        frequency_summary,
        x="Transaction_Frequency_Band",
        y="attrition_rate_pct",
        text="rate_label",
        custom_data=["customers", "attrited"],
        category_orders={
            "Transaction_Frequency_Band": frequency_order,
        },
        title="Observed attrition rate by transaction frequency",
        color_discrete_sequence=[ACCENT_BAR],
    )
    frequency_fig.update_traces(
        marker_line_width=0,
        texttemplate="%{text}",
        textfont={"size": 9, "color": INK},
        textposition="outside",
        cliponaxis=False,
        hovertemplate=(
            "<b>%{x}</b><br>"
            "Observed attrition rate: %{y:.2f}%<br>"
            "Customers in band: %{customdata[0]:,.0f}<br>"
            "Attrited customers: %{customdata[1]:,.0f}"
            "<extra></extra>"
        ),
    )
    _style_bar_figure(frequency_fig)
    frequency_fig.update_layout(showlegend=False, bargap=0.42)
    frequency_fig.update_xaxes(title_text="Transaction-frequency band")
    frequency_fig.update_yaxes(
        title_text="Attrition rate (%)",
        range=[0, 45],
    )

    # Set consistent row and column orders for the joint-segment heatmap.
    utilisation_order = ["Low (≤Q1)", "Middle (Q1–Q3)", "High (>Q3)"]

    # Count customers and attrited customers in each combined segment.
    joint_customers = pd.crosstab(
        df["Utilization_Band"],
        df["Transaction_Frequency_Band"],
    ).reindex(
        index=utilisation_order,
        columns=frequency_order,
        fill_value=0,
    )
    is_attrited = df["Attrition_Flag"].eq("Attrited Customer").astype(int)
    joint_attrited = pd.crosstab(
        df["Utilization_Band"],
        df["Transaction_Frequency_Band"],
        values=is_attrited,
        aggfunc="sum",
    ).reindex(
        index=utilisation_order,
        columns=frequency_order,
        fill_value=0,
    )

    # Calculate the same within-cell attrition rates and preserve hover counts.
    joint_rates = (
        joint_attrited
        .div(joint_customers.where(joint_customers.ne(0)))
        * 100
    )
    joint_customdata = np.stack(
        [joint_customers.to_numpy(), joint_attrited.to_numpy()],
        axis=-1,
    )
    # Put the segment denominator in each heatmap cell, not only on hover.
    joint_rate_values = joint_rates.to_numpy(dtype=float)
    joint_customer_values = joint_customers.to_numpy(dtype=int)
    joint_cell_labels = np.empty(joint_rate_values.shape, dtype=object)
    for row_index, column_index in np.ndindex(joint_rate_values.shape):
        rate = joint_rate_values[row_index, column_index]
        customers = joint_customer_values[row_index, column_index]
        joint_cell_labels[row_index, column_index] = (
            f"{rate:.1f}%<br>n={customers:,}"
            if np.isfinite(rate) and customers > 0
            else "—<br>n=0"
        )

    # A single-hue-to-warm scale makes low-to-high rates easy to read.
    joint_heatmap_fig = go.Figure(
        data=go.Heatmap(
            z=joint_rates.to_numpy(),
            x=frequency_order,
            y=utilisation_order,
            text=joint_cell_labels,
            texttemplate="%{text}",
            textfont={"size": 10},
            customdata=joint_customdata,
            colorscale="YlOrRd",
            zmin=0,
            zmax=75,
            xgap=4,
            ygap=4,
            colorbar={
                "title": "Attrition rate (%)",
                "thickness": 12,
                "len": 0.82,
                "tickfont": {"size": 9, "color": MUTED},
            },
            hovertemplate=(
                "<b>Utilisation: %{y}</b><br>"
                "Transaction frequency: %{x}<br>"
                "Observed attrition rate: %{z:.2f}%<br>"
                "Customers in cell: %{customdata[0]:,.0f}<br>"
                "Attrited customers: %{customdata[1]:,.0f}"
                "<extra></extra>"
            ),
        )
    )
    joint_heatmap_fig.update_layout(
        template="plotly_white",
        height=330,
        margin={"l": 72, "r": 22, "t": 56, "b": 52},
        title={
            "text": "Attrition rate: utilisation × transaction frequency",
            "font": {"family": FONT_FAMILY, "size": 14, "color": INK},
            "x": 0.03,
            "xanchor": "left",
            "y": 0.97,
            "yanchor": "top",
        },
        font={"family": FONT_FAMILY, "size": 10, "color": INK},
        paper_bgcolor=TRANSPARENT,
        plot_bgcolor=TRANSPARENT,
        xaxis_title="Transaction-frequency band",
        yaxis_title="Utilisation band",
        hoverlabel={
            "bgcolor": INK,
            "bordercolor": INK,
            "font": {"family": FONT_FAMILY, "size": 12, "color": "white"},
        },
    )
    joint_heatmap_fig.update_xaxes(
        showgrid=False,
        zeroline=False,
        ticks="",
        automargin=True,
        tickfont={"size": 9, "color": MUTED},
        title_font={"size": 11, "color": MUTED},
    )
    joint_heatmap_fig.update_yaxes(
        autorange="reversed",
        showgrid=False,
        zeroline=False,
        ticks="",
        automargin=True,
        tickfont={"size": 9, "color": MUTED},
        title_font={"size": 11, "color": MUTED},
    )

    # Summarise observed attrition by source income category.
    income_order = [
        "Less than $40K",
        "$40K - $60K",
        "$60K - $80K",
        "$80K - $120K",
        "$120K +",
        "Unknown",
    ]
    income_summary = (
        df.groupby("Income_Category")
        .agg(
            customers=("CLIENTNUM", "nunique"),
            attrited=(
                "Attrition_Flag",
                lambda values: values.eq("Attrited Customer").sum(),
            ),
        )
    )
    income_summary["attrition_rate_pct"] = (
        income_summary["attrited"]
        / income_summary["customers"]
        * 100
    )
    income_summary = income_summary.reindex(income_order).reset_index()
    income_summary = _keep_present_segments(income_summary)

    # Show source-category rates; keep group sizes available in the tooltip.
    income_fig = px.bar(
        income_summary,
        x="Income_Category",
        y="attrition_rate_pct",
        text="attrition_rate_pct",
        custom_data=["customers", "attrited"],
        category_orders={"Income_Category": income_order},
        title="Observed attrition rate by source income category",
        color_discrete_sequence=[ACCENT_BAR],
    )
    income_fig.update_traces(
        marker_line_width=0,
        texttemplate="%{y:.1f}%",
        textposition="outside",
        cliponaxis=False,
        hovertemplate=(
            "<b>%{x}</b><br>"
            "Observed attrition rate: %{y:.2f}%<br>"
            "Customers in category: %{customdata[0]:,.0f}<br>"
            "Attrited customers: %{customdata[1]:,.0f}"
            "<extra></extra>"
        ),
    )
    _style_bar_figure(income_fig)
    income_fig.update_layout(showlegend=False, bargap=0.38)
    income_fig.update_xaxes(
        title_text="Income category as supplied in the dataset",
        tickangle=-18,
    )
    income_fig.update_yaxes(
        title_text="Attrition rate (%)",
        range=[0, 20],
    )

    # Summarise observed attrition by card category.
    card_order = ["Blue", "Silver", "Gold", "Platinum"]
    card_summary = (
        df.groupby("Card_Category")
        .agg(
            customers=("CLIENTNUM", "nunique"),
            attrited=(
                "Attrition_Flag",
                lambda values: values.eq("Attrited Customer").sum(),
            ),
        )
    )
    card_summary["attrition_rate_pct"] = (
        card_summary["attrited"]
        / card_summary["customers"]
        * 100
    )
    card_summary = card_summary.reindex(card_order).reset_index()
    card_summary = _keep_present_segments(card_summary)

    # Drop absent groups after filtering to avoid empty bars/labels.
    card_fig = px.bar(
        card_summary,
        x="Card_Category",
        y="attrition_rate_pct",
        text="attrition_rate_pct",
        custom_data=["customers", "attrited"],
        category_orders={"Card_Category": card_order},
        title="Observed attrition rate by card category",
        color_discrete_sequence=[ACCENT_BAR],
    )
    card_fig.update_traces(
        marker_line_width=0,
        texttemplate="%{y:.1f}%",
        textposition="outside",
        cliponaxis=False,
        hovertemplate=(
            "<b>%{x}</b><br>"
            "Observed attrition rate: %{y:.2f}%<br>"
            "Customers in category: %{customdata[0]:,.0f}<br>"
            "Attrited customers: %{customdata[1]:,.0f}"
            "<extra></extra>"
        ),
    )
    _style_bar_figure(card_fig)
    card_fig.update_layout(showlegend=False, bargap=0.42)
    card_fig.update_xaxes(title_text="Card category")
    card_fig.update_yaxes(
        title_text="Attrition rate (%)",
        range=[0, 30],
    )

    # -------------------------------------------------------------------------
    # 3. Present the charts as a responsive grid with notes beside their evidence.
    # -------------------------------------------------------------------------
    return html.Div(
        [
            html.Div(
                [
                    html.Div(
                        [
                            html.Span(
                                "TRANSACTION FREQUENCY",
                                className="insight-panel__label",
                            ),
                            frequency_metrics,
                        ],
                        className="insight-panel__copy",
                    ),
                ],
                className="insight-panel insight-panel--retention",
            ),
            html.Div(
                [
                    html.Section(
                        dcc.Graph(
                            figure=frequency_fig,
                            config={"displayModeBar": False, "responsive": True},
                            className="dashboard-graph",
                            style={"height": "340px", "width": "100%"},
                        ),
                        className="chart-card retention-card--frequency",
                    ),
                    html.Section(
                        dcc.Graph(
                            figure=joint_heatmap_fig,
                            config={"displayModeBar": False, "responsive": True},
                            className="dashboard-graph",
                            style={"height": "350px", "width": "100%"},
                        ),
                        className="chart-card retention-card--heatmap",
                    ),
                    html.Section(
                        [
                            dcc.Graph(
                                figure=income_fig,
                                config={"displayModeBar": False, "responsive": True},
                                className="dashboard-graph",
                                style={"height": "340px", "width": "100%"},
                            ),
                            html.P(
                                "Source income labels; no Nigerian-currency interpretation applied.",
                                className="chart-note",
                            ),
                        ],
                        className="chart-card retention-card--income",
                    ),
                    html.Section(
                        [
                            dcc.Graph(
                                figure=card_fig,
                                config={"displayModeBar": False, "responsive": True},
                                className="dashboard-graph",
                                style={"height": "340px", "width": "100%"},
                            ),
                            html.P(
                                "Platinum n = 20; interpret its observed rate cautiously.",
                                className="chart-note",
                            ),
                        ],
                        className="chart-card retention-card--card",
                    ),
                ],
                className="retention-chart-grid",
            ),
        ],
        className="page-section",
    )
