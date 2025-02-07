import pandas as pd
import os


if __name__=="__main__":
    
    ground_truth_file = "simulation/aki.csv"
    predictions = "simulation/aki_predictions.csv"

    gt =  pd.read_csv(ground_truth_file)
    preds = pd.read_csv(predictions)

    matches = gt.merge(preds, on=["mrn", "date"], how="inner")
    
    TP = len(matches)
    FP = len(preds) - TP
    FN = len(gt) - TP

    precision = TP / (TP + FP) if (TP + FP) > 0 else 0
    recall = TP / (TP + FN) if (TP + FN) > 0 else 0

    # use beta value from cw1
    beta = 3
    F3_score = (1 + beta**2) * (precision * recall) / ((beta**2 * precision) + recall) if (precision + recall) > 0 else 0

    # write results to results.txt
    print(f"True Positives (TP): {TP}")
    print(f"False Positives (FP): {FP}")
    print(f"False Negatives (FN): {FN}")
    print(f"Precision: {precision:.4f}")
    print(f"Recall: {recall:.4f}")
    print(f"F3 Score: {F3_score:.4f}")

    # also write results
    with open("results.txt", "w") as file:
        file.write(f"True Positives (TP): {TP}\n")
        file.write(f"False Positives (FP): {FP}\n")
        file.write(f"False Negatives (FN): {FN}\n")
        file.write(f"Precision: {precision:.4f}\n")
        file.write(f"Recall: {recall:.4f}\n")
        file.write(f"F3 Score: {F3_score:.4f}\n")
    print("Results saved in results.txt")

        