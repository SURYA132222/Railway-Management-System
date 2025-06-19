import pandas as pd

df = pd.read_csv("stations.csv")
print("🧾 Available columns in stations.csv:")
print(list(df.columns))
