"""Retrospective diagnostics only; target lentil history is not a model input."""
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
panel = pd.read_csv(ROOT/'data/panel_rendements.csv', dtype={'dep': str})
lentil = panel[(panel.culture == 'lentille') & panel.utilisable]
predictions = pd.read_csv(OUT/'predictions.csv', dtype={'dep': str})
rows = []
for _, row in predictions[predictions.model == 'transfer_qrf'].iterrows():
    past = lentil[(lentil.dep == row.dep) & (lentil.annee < row.year)]
    actual = lentil[(lentil.dep == row.dep) & (lentil.annee == row.year)]
    past_level = float(past.rendement_qha.mean())
    actual_yield = float(actual.rendement_qha.iloc[0])
    rows.append({'year': row.year, 'dep': row.dep, 'region': row.region,
                 'transferred_level_qha': row.transferred_level_qha,
                 'diagnostic_target_past_level_qha': past_level,
                 'transfer_to_past_level_ratio': row.transferred_level_qha/past_level,
                 'diagnostic_actual_yield_qha': actual_yield,
                 'actual_to_transferred_level_ratio': actual_yield/row.transferred_level_qha,
                 'donors': row.donors})
result = pd.DataFrame(rows)
result.to_csv(OUT/'level_diagnostics.csv', index=False)
regional = result.groupby('region').agg(
    n=('dep', 'size'),
    median_transfer_to_past_ratio=('transfer_to_past_level_ratio', 'median'),
    median_actual_to_transferred_ratio=('actual_to_transferred_level_ratio', 'median'))
regional.to_csv(OUT/'regional_level_diagnostics.csv')
print(regional.to_string())
