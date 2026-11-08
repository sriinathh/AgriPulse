import os, pandas as pd
path = os.path.join('..', 'ml', 'irrigation_dataset_cleaned.csv')
print('Loading dataset from', path)
df = pd.read_csv(path)
print('Shape:', df.shape)
print('Columns:', list(df.columns))
print('Target column stats:')
if 'irrigation_mm' in df.columns:
    print('irrigation_mm min, max, mean, std:', df['irrigation_mm'].min(), df['irrigation_mm'].max(), df['irrigation_mm'].mean(), df['irrigation_mm'].std())
else:
    print('Target column irrigation_mm not found')
