import os
import pandas as pd
from sklearn.preprocessing import LabelEncoder

def add_padding(df):
    """Ensures the dataframe has a constant length of 50."""
    for i in range(((len(df.columns) - 2) // 2), 50):
        df[f'creatinine_date_{i}'] = 0
        df[f'creatinine_result_{i}'] = 0
    return df


def process_dates(df):
    """Converts timestamps to seconds relative to the first measurement."""
    date_cols = [col for col in df.columns if "creatinine_date" in col]
    for col in date_cols:
        df[col] = pd.to_datetime(df[col], errors='coerce')
    df['ref_date'] = df[date_cols].min(axis=1)
    for col in date_cols:
        df[col] = (df[col] - df['ref_date']).dt.total_seconds()
    df = df.drop(columns=['ref_date']).fillna(0)
    return df

def process_features(df):
    """Feature engineering for AKI prediction."""
    results_cols = [col for col in df.columns if "creatinine_result" in col]

    df = process_dates(df)
    df = add_padding(df)

    df['creatinine_mean'] = df[results_cols].mean(axis=1)
    df['creatinine_median'] = df[results_cols].median(axis=1, skipna=True)
    df['creatinine_max'] = df[results_cols].max(axis=1)
    df['creatinine_min'] = df[results_cols].min(axis=1)
    df["creatinine_max_delta"] = df[results_cols].diff(axis=1).max(axis=1).fillna(0)
    df['creatinine_std'] = df[results_cols].std(axis=1)
    df['most_recent'] = df[results_cols].apply(lambda row: row.dropna().iloc[-1] if not row.dropna().empty else None, axis=1)
    df['rv1_ratio'] = df['most_recent'] / df['creatinine_min']
    df['rv2_ratio'] = df['most_recent'] / df['creatinine_median']

    return df

def preprocess(df, train):
        """Prepares data for model training or inference."""
        le = LabelEncoder()
        df['sex'] = le.fit_transform(df['sex'])
        if train:
            x_train = process_features(df.drop(columns='aki'))
            df['aki'] = le.fit_transform(df['aki'])
            y_train = df['aki']
            return x_train, y_train
        else:
            return process_features(df)
        
