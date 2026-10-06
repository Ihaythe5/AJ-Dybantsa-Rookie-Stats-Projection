"""
AJ Dybantsa NBA Rookie-Season Projection Model
Approach: Age-cohort percentile model.


We don't have college stats or draft position for the historical rookies
(only NBA rookie-season debut stats), so instead of a college->NBA regression,
we build the distribution of rookie outcomes for players who debuted
at the SAME AGE as Dybantsa (19), then position him within that distribution:
  - #1 overall pick 
  - Historically dominant, efficient college production (28.1 PER, 60% TS)
  - Walking into a rebuilding team (Wizards) likely high usage/minutes as a rookie
"""

from pathlib import Path

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt


# Load & clean the three files
project_dir = Path(__file__).resolve().parent
files = {
    '2023-24': project_dir / 'rookieStats_23-24.csv',
    '2024-25': project_dir / 'rookieStats_24-25.csv',
    '2025-26': project_dir / 'rookieStats_25-26.csv',
}

dfs = []
for season, path in files.items():
    if not path.exists():
        raise FileNotFoundError(f"Could not find rookie stats file: {path}")
    df = pd.read_csv(path, skiprows=1, encoding='latin1')
    df['season'] = season
    dfs.append(df)

master = pd.concat(dfs, ignore_index=True)

# Rename the duplicated "per game" columns (pandas auto-suffixes them .1)
master = master.rename(columns={
    'MP.1': 'MPG', 'PTS.1': 'PPG', 'TRB.1': 'RPG', 'AST.1': 'APG',
    'STL.1': 'SPG', 'BLK.1': 'BPG'
})

# Drop rows with missing essential data
master = master.dropna(subset=['Player', 'Age', 'G'])
master['Age'] = pd.to_numeric(master['Age'], errors='coerce')
master = master.dropna(subset=['Age'])
master['Age'] = master['Age'].astype(int)

# Filter out extremely low-sample noise
qualified = master[master['G'] >= 10].copy()

print(f"Loaded {len(master)} total rookie entries ({len(qualified)} with 10+ games played)")
print(f"Seasons: {sorted(master['season'].unique())}")


# Build the age-19-20 cohort (Dybantsa's draft age)

cohort_19_20 = qualified[qualified['Age'].isin([19, 20])]

print(f"Age 19-20 cohort: {len(cohort_19_20)} players")

stat_cols = ['PPG', 'RPG', 'APG', 'SPG', 'BPG']

# GENERAL CONTEXT:
# Dybantsa is the #1 overall pick with elite, efficient college production
# and projects into a high-usage role on a rebuilding team.
# We anchor his projection at the 80th-90th percentile of the age cohort
# for volume stats (PPG), and a slightly wider band for RPG/APG since
# rookie role/opportunity varies more team-to-team.

PROJECTION_PERCENTILES = {
    'PPG': (75, 92),   # scoring is his clearest translatable skill
    'RPG': (65, 85),
    'APG': (60, 85),
    'SPG': (55, 80),
    'BPG': (40, 65),   # bpg is his weakest college indicator (0.3 bpg at BYU)
}

cohort = cohort_19_20  # combined 19-20 sample
cohort_label = "19-20"
print(f"\nUsing cohort: Age {cohort_label} combined (n={len(cohort)})")

projections = {}
for stat in stat_cols:
    low_pct, high_pct = PROJECTION_PERCENTILES[stat]
    low_val = np.percentile(cohort[stat], low_pct)
    high_val = np.percentile(cohort[stat], high_pct)
    median_val = np.percentile(cohort[stat], 50)
    projections[stat] = {
        'low': round(low_val, 1),
        'high': round(high_val, 1),
        'cohort_median': round(median_val, 1),
        'cohort_max': round(cohort[stat].max(), 1),
    }

print("\n--- AJ Dybantsa Rookie-Season Projection (Age 19-20 Cohort Percentile Model) ---")
for stat, vals in projections.items():
    print(f"{stat}: {vals['low']}-{vals['high']}  "
          f"(cohort median: {vals['cohort_median']}, cohort max: {vals['cohort_max']})")


# Who are the top comps in this cohort?

top_scorers = cohort.nlargest(8, 'PPG')[['Player', 'season', 'Age', 'G', 'MPG', 'PPG', 'RPG', 'APG', 'FG%', '3P%']]
print("\nTop 8 scorers in the age cohort (context for where Dybantsa's projection sits):")
print(top_scorers.to_string(index=False))


# Visualization

fig, axes = plt.subplots(2, 3, figsize=(15, 8))
axes = axes.flatten()

colors = {'hist': '#4A5568', 'band': '#ED8936', 'median': '#2D3748'}

for i, stat in enumerate(stat_cols):
    ax = axes[i]
    ax.hist(cohort[stat], bins=15, color=colors['hist'], alpha=0.7, edgecolor='white')
    low, high = projections[stat]['low'], projections[stat]['high']
    ax.axvspan(low, high, color=colors['band'], alpha=0.3, label='Dybantsa projected range')
    ax.axvline(projections[stat]['cohort_median'], color=colors['median'],
               linestyle='--', linewidth=1, label='Cohort median')
    ax.set_title(f'{stat}', fontsize=12, fontweight='bold')
    ax.set_xlabel(stat)
    ax.set_ylabel('# of rookies')
    if i == 0:
        ax.legend(fontsize=8, loc='upper right')

axes[-1].axis('off')  
fig.suptitle(f'AJ Dybantsa Rookie Projection vs. Age-{cohort_label} '
             f'Rookie Cohort (n={len(cohort)}, seasons 2023-24 to 2025-26)',
             fontsize=13, fontweight='bold')
plt.tight_layout()
plt.savefig(r'C:\Users\Isaiah\Desktop\Data Analytics\dybantsa_projection_v2.png', dpi=150, bbox_inches='tight')
print("\nChart saved.")


# Export as CSV

summary_df = pd.DataFrame(projections).T
summary_df.index.name = 'stat'
summary_df.to_csv(r'C:\Users\Isaiah\Desktop\Data Analytics\dybantsa_projection_summary_v2.csv')
print("Summary CSV saved.")
