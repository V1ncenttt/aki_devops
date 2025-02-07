import os
import pandas as pd

if __name__ == '__main__':
    test_file = os.path.join('data', 'complete_test.csv')
    df = pd.read_csv(test_file)
    test_results = df['aki']
    df = df.drop(columns='aki')
    df.to_csv('data/test.csv', index=False)