import pandas as pd

data = {
    "Market: A": ['', '', '', 111, 100],
    "'a'": [130, 125, 120, '', ''],
    ".": ['|', '|', '|', '|', '|'],
    "Market B": ['', '', '', 111, 100],
    "'b'": [130, 125, 120, '', ''],
}

df = pd.DataFrame(data=data)

print(df.to_string())