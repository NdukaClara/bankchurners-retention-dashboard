# Customer retention and performance intelligence

A Dash application that reports observed customer attrition for a Nigerian commercial bank scenario, built on the BankChurners credit-card dataset. Two tabs, six KPI cards, seven charts, three filters.

This repository is the reporting layer of a larger piece of coursework. A Jupyter notebook profiles the raw file, prepares an analysis-ready table, derives three segment bands, and applies a two-flag retention-priority rule. The application reads the notebook's final export. The written report and its appendices are submitted separately and are not part of this repository.

## Contents

- [Repository layout](#repository-layout)
- [Data](#data)
- [Setup and run](#setup-and-run)
- [What the pages show](#what-the-pages-show)
- [Metrics and thresholds](#metrics-and-thresholds)
- [Reading the numbers](#reading-the-numbers)
- [Optional: export the dashboard pages](#optional-export-the-dashboard-pages)
- [Troubleshooting](#troubleshooting)
- [Attribution](#attribution)

## Repository layout

```
.
├── dashboard/
│   ├── app.py                   app shell, dataset load, tab wiring, filter callbacks
│   ├── pages/
│   │   ├── executive.py         Executive Overview page builder
│   │   └── retention.py         Retention Analysis page builder
│   ├── assets/style.css         layout and styling
│   └── export_dashboard_pdf.py  optional: full-page captures to PDF
├── data/
│   ├── raw/BankChurners.csv
│   └── processed/
│       ├── BankChurners_clean.csv
│       └── BankChurners_analysis_ready.csv
├── BankChurners_analysis.ipynb  notebook, Cells 1 to 18
├── requirements.txt
└── README.md
```

`app.py` loads the data once, builds the tab shell, and holds the two Retention Analysis callbacks. The two page modules return each tab's layout. The stylesheet sets the layout rules and uses no external fonts, scripts, or images.

## Data

| File | Shape | Produced by |
|---|---|---|
| `data/raw/BankChurners.csv` | 10,127 × 23 | Kaggle download |
| `data/processed/BankChurners_clean.csv` | 10,127 × 24 | Notebook Cell 8 |
| `data/processed/BankChurners_analysis_ready.csv` | 10,127 × 28 | Notebook Cell 18 |

Source: Credit Card Customers (BankChurners), published on Kaggle by Sakshi Goyal, https://www.kaggle.com/datasets/sakshigoyal7/credit-card-customers

The two precomputed `Naive_Bayes_Classifier` columns in the raw file are excluded throughout and reach neither processed file.

### Lineage

`BankChurners.csv`, 10,127 × 23 → exclude the two classifier columns → add `Age_Band`, `Utilization_Band`, `Transaction_Frequency_Band` → `BankChurners_clean.csv`, 10,127 × 24 → add `Low_Transaction_Flag`, `Low_Utilization_Flag`, `Retention_Priority_Score`, `Retention_Priority_Band` → `BankChurners_analysis_ready.csv`, 10,127 × 28.

No rows are removed at any stage. Explicit `Unknown` categories in education, marital status, and income are retained rather than imputed. The 1.5×IQR screen in Cell 3 flags plausible high values in credit limit, open-to-buy, transaction amount, and contact count; none is winsorised or dropped.

### Columns

The 21 retained source fields are `CLIENTNUM`, `Attrition_Flag`, `Customer_Age`, `Gender`, `Dependent_count`, `Education_Level`, `Marital_Status`, `Income_Category`, `Card_Category`, `Months_on_book`, `Total_Relationship_Count`, `Months_Inactive_12_mon`, `Contacts_Count_12_mon`, `Credit_Limit`, `Total_Revolving_Bal`, `Avg_Open_To_Buy`, `Total_Amt_Chng_Q4_Q1`, `Total_Trans_Amt`, `Total_Trans_Ct`, `Total_Ct_Chng_Q4_Q1`, `Avg_Utilization_Ratio`.

The three derived bands are `Age_Band` (Under 35, 35–44, 45–54, 55+), `Utilization_Band` (Low, Middle, High), and `Transaction_Frequency_Band` (Low, Middle, High).

The four rule fields are the two 0/1 flags, their sum, and the band label. Band values are `High`, `Medium`, and `Low`.

`Attrition_Flag` is the outcome field and takes `Existing Customer` or `Attrited Customer`. `CLIENTNUM` is an identifier for audit and counting only; it is never a predictor or a display field.

## Setup and run

Requires Python 3.13. Pinned dependencies: dash 4.4.1, pandas 3.0.6, numpy 2.5.4, plotly 7.1.0.

```bash
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python dashboard/app.py            # http://127.0.0.1:8050
```

To regenerate the data instead of using the included CSVs, run the notebook from Cell 1 to Cell 18. Cell 8 writes the clean file and Cell 18 writes the analysis-ready file.

The app reads `data/processed/BankChurners_analysis_ready.csv` once at start-up and raises `FileNotFoundError` if the file is absent, so the notebook must run before the app.

### Notebook map

| Cells | Work |
|---|---|
| 1 | Imports, library versions, file paths |
| 2 | Raw file profile: shape, types, nulls, duplicates, label whitespace |
| 3 | Label, range, IQR, and domain checks |
| 4–6 | `Age_Band`, `Utilization_Band`, `Transaction_Frequency_Band` |
| 7 | Analytical table, 10,127 × 24, classifier columns excluded |
| 8 | Clean CSV export and reload check |
| 9 | Full-sample KPI baseline |
| 10 | Attrited versus existing comparison |
| 11–15 | Segment rates by age, utilisation, frequency, income, and card category |
| 16 | Joint utilisation × frequency table |
| 17 | Two-flag priority rule and band evaluation |
| 18 | Analysis-ready export, 10,127 × 28, and reload check |

## What the pages show

**Executive Overview.** Six KPI cards: customer count, observed attrition, attrited count, mean transaction count, mean utilisation, mean product relationships. Three charts: customer-status mix, observed attrition by priority band, observed attrition by age band.

**Retention Analysis.** Three filters for age band, income category, and card category. A blank filter means all categories; a Reset control clears all three. Every chart on the tab rebuilds for the selected combination, and a scope summary reports the filtered customer count against the full 10,127. Four charts: attrition by transaction frequency, attrition by utilisation × frequency heatmap, attrition by income category, attrition by card category.

Filters affect the Retention Analysis tab only. The Executive Overview stays at portfolio level.

## Metrics and thresholds

| Metric | Definition | Full-sample value |
|---|---|---|
| Unique customers | Distinct `CLIENTNUM` | 10,127 |
| Attrited customers | Count labelled `Attrited Customer` | 1,627 |
| Existing customers | Count labelled `Existing Customer` | 8,500 |
| Existing customer ratio | Existing ÷ all customers | 83.93% |
| Observed attrition rate | Attrited ÷ all customers | 16.07% |
| Mean transaction count | Mean `Total_Trans_Ct` | 64.86 |
| Mean utilisation | Mean `Avg_Utilization_Ratio` | 27.49% |
| Mean relationships | Mean `Total_Relationship_Count` | 3.81 |
| Mean credit limit | Mean `Credit_Limit`, source units | 8,631.95 |
| Total transaction amount | Sum of `Total_Trans_Amt`, source units | 44,600,182 |

Band cut-points are quartiles of this file:

| Band | Low | Middle | High |
|---|---|---|---|
| Transaction frequency | ≤ 45 transactions | 46 to 81 | > 81 |
| Utilisation | ≤ 0.023 | 0.024 to 0.503 | > 0.503 |

Priority rule: one point for `Transaction_Frequency_Band` equal to `Low`, one point for `Utilization_Band` equal to `Low`. Two points is High priority, one point Medium, none Low. Both flags test the band columns, which is why the High band holds exactly the same 764 customers as the low-utilisation/low-frequency cell.

| Band | Customers | Attrited | Observed rate |
|---|---:|---:|---:|
| High | 764 | 559 | 73.17% |
| Medium | 3,624 | 780 | 21.52% |
| Low | 5,739 | 288 | 5.02% |

## Reading the numbers

The priority bands describe this sample retrospectively. The High band's 73.17% is a historical rate among customers already labelled attrited; it is not a churn probability and does not estimate what an intervention would achieve.

Band thresholds come from this file alone and are not policy values. The dataset carries no date field, so no trend, no time-ordered validation, and no out-of-time test is possible. Income is categorical, currency units are unverified, and there is no geography field, so the data's representativeness for a Nigerian bank is unknown. No confounder adjustment was performed, and causal effects remain undetermined. The file holds no intervention outcomes or campaign costs.

The Platinum card category rests on 20 customers, so its 25.00% rate is unstable and should not drive stand-alone targeting.

## Optional: export the dashboard pages

`dashboard/export_dashboard_pdf.py` captures both tabs at 1600 px and writes a three-page PDF, useful for a report appendix. It needs two extra packages:

```bash
pip install playwright pillow
playwright install chromium
```

## Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| `FileNotFoundError: Dashboard data file not found` | The analysis-ready CSV is missing | Run Cells 1–18, or copy `BankChurners_analysis_ready.csv` into `data/processed/` |
| `ModuleNotFoundError: No module named 'dash'` | Virtual environment not active | `source .venv/bin/activate`, then `pip install -r requirements.txt` |
| `Address already in use` on port 8050 | Another Dash instance is running | Stop it, or start with `python dashboard/app.py` after closing the other process |
| Filters return an empty view | A combination with no customers | Use the Reset control, or clear the dropdowns |
| Charts render but labels are cut off | Window narrower than the desktop layout | Widen the browser window to about 1500 px or more |

## Attribution

Dataset: Goyal, S. (n.d.). *Credit card customers* [Data set]. Kaggle. https://www.kaggle.com/datasets/sakshigoyal7/credit-card-customers

Dashboard: Plotly Dash. Analysis: Python, pandas, Plotly.

Coursework: MIT 8339, Business Intelligence and Decision Support Systems.

No licence is attached. This is coursework, and the dataset remains under the publisher's terms.
