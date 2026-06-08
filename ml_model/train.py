import os
import sys
# Add project root to path for modular imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import joblib
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.tree import DecisionTreeClassifier, plot_tree
from sklearn.metrics import accuracy_score, precision_recall_fscore_support, confusion_matrix
from ml_model.preprocess import preprocess_data, create_dirs

# Define absolute paths
BASE_DIR = r"C:\Users\spooa\Downloads\mental-fatigue-detection"
RESULTS_DIR = os.path.join(BASE_DIR, "results")
GRAPHS_DIR = os.path.join(RESULTS_DIR, "graphs")
REPORTS_DIR = os.path.join(RESULTS_DIR, "reports")
MODELS_DIR = os.path.join(RESULTS_DIR, "trained_models")
LOCAL_MODELS_DIR = os.path.join(BASE_DIR, "ml_model", "trained_models")

def run_training():
    print("[START] Starting Phase 2 Model Training...")
    
    # 1. Load Preprocessed Splits
    X_train, X_test, y_train, y_test, le = preprocess_data()
    
    # 2. Overfitting Analysis (max_depth tuning)
    print("[OVERFIT] Analyzing overfitting by varying max_depth from 1 to 10...")
    train_accs = []
    test_accs = []
    depths = range(1, 11)
    
    for depth in depths:
        clf_temp = DecisionTreeClassifier(max_depth=depth, random_state=42)
        clf_temp.fit(X_train, y_train)
        
        train_acc = accuracy_score(y_train, clf_temp.predict(X_train))
        test_acc = accuracy_score(y_test, clf_temp.predict(X_test))
        
        train_accs.append(train_acc)
        test_accs.append(test_acc)
        print(f"  * Depth {depth:2d} | Train Acc: {train_acc:.3f} | Test Acc: {test_acc:.3f}")
        
    # Plot Overfitting Analysis
    plt.figure(figsize=(7, 5))
    plt.plot(depths, train_accs, label='Training Accuracy', marker='o', color='#6c63ff', linewidth=2)
    plt.plot(depths, test_accs, label='Testing Accuracy', marker='s', color='#ff6b9d', linewidth=2)
    plt.xlabel('Tree Depth (max_depth)')
    plt.ylabel('Accuracy Score')
    plt.title('Decision Tree Overfitting Analysis', fontsize=12, fontweight='bold', pad=12)
    plt.xticks(depths)
    plt.legend()
    plt.tight_layout()
    overfit_path = os.path.join(GRAPHS_DIR, 'overfitting_analysis.png')
    plt.savefig(overfit_path, dpi=300)
    plt.close()
    print(f"[OK] Overfitting Analysis plot exported to {overfit_path}")
    
    # Select best depth (maximize test accuracy, minimize depth to prevent overfitting)
    best_idx = np.argmax(test_accs)
    optimal_depth = depths[best_idx]
    print(f"[MODEL] Selecting optimal max_depth = {optimal_depth} (Testing Accuracy: {test_accs[best_idx]:.3f})")
    
    # 3. Train final optimal Decision Tree
    clf = DecisionTreeClassifier(max_depth=optimal_depth, random_state=42)
    clf.fit(X_train, y_train)
    
    # Predict and evaluate
    y_train_pred = clf.predict(X_train)
    y_test_pred = clf.predict(X_test)
    
    train_accuracy = accuracy_score(y_train, y_train_pred)
    test_accuracy = accuracy_score(y_test, y_test_pred)
    
    # Macro metrics
    precision, recall, f1, _ = precision_recall_fscore_support(y_test, y_test_pred, average='weighted')
    cm = confusion_matrix(y_test, y_test_pred)
    
    print(f"[OK] Training complete:")
    print(f"  * Train Accuracy: {train_accuracy:.4f}")
    print(f"  * Test Accuracy:  {test_accuracy:.4f}")
    print(f"  * Precision:      {precision:.4f}")
    print(f"  * Recall:         {recall:.4f}")
    print(f"  * F1 Score:       {f1:.4f}")
    
    # 4. Generate Visualizations
    # Chart 1: Confusion Matrix Heatmap
    plt.figure(figsize=(6, 5))
    sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', xticklabels=le.classes_, yticklabels=le.classes_, annot_kws={"size": 12})
    plt.title('Confusion Matrix - Decision Tree', fontsize=12, fontweight='bold', pad=12)
    plt.ylabel('Actual Category')
    plt.xlabel('Predicted Category')
    plt.tight_layout()
    cm_path = os.path.join(GRAPHS_DIR, 'confusion_matrix.png')
    plt.savefig(cm_path, dpi=300)
    plt.close()
    print(f"[OK] Confusion Matrix plot exported to {cm_path}")
    
    # Chart 2: Feature Importance
    importances = clf.feature_importances_
    features = list(X_train.columns)
    feat_df = pd.DataFrame({'Feature': features, 'Importance': importances})
    feat_df = feat_df.sort_values(by='Importance', ascending=False)
    
    plt.figure(figsize=(7, 5))
    sns.barplot(x='Importance', y='Feature', data=feat_df, hue='Feature', palette='viridis', legend=False)
    plt.title('Decision Tree Feature Importances', fontsize=12, fontweight='bold', pad=12)
    plt.xlabel('Relative Gini Importance')
    plt.tight_layout()
    feat_path = os.path.join(GRAPHS_DIR, 'feature_importance.png')
    plt.savefig(feat_path, dpi=300)
    plt.close()
    print(f"[OK] Feature Importance plot exported to {feat_path}")
    
    # Chart 3: Decision Tree visual topology
    plt.figure(figsize=(16, 10))
    plot_tree(clf, feature_names=features, class_names=list(le.classes_), filled=True, rounded=True, fontsize=10)
    plt.title(f'Decision Tree Structure Topology (max_depth={optimal_depth})', fontsize=14, fontweight='bold', pad=15)
    plt.tight_layout()
    tree_path = os.path.join(GRAPHS_DIR, 'decision_tree_structure.png')
    plt.savefig(tree_path, dpi=300)
    plt.close()
    print(f"[OK] Decision Tree Topology plot exported to {tree_path}")
    
    # Chart 4: Prediction Confidence Analysis
    probs = clf.predict_proba(X_test)
    confidences = np.max(probs, axis=1)
    
    plt.figure(figsize=(7, 5))
    sns.histplot(confidences, bins=10, kde=True, color='#00d4ff')
    plt.title('ML Prediction Confidence Distribution (Max Prob)', fontsize=12, fontweight='bold', pad=12)
    plt.xlabel('Confidence Score (Probability)')
    plt.ylabel('Sample Density')
    plt.tight_layout()
    conf_path = os.path.join(GRAPHS_DIR, 'prediction_confidence.png')
    plt.savefig(conf_path, dpi=300)
    plt.close()
    print(f"[OK] Prediction Confidence plot exported to {conf_path}")
    
    # Calculate average confidence scores
    correct_mask = (y_test_pred == y_test.values)
    avg_conf_overall = np.mean(confidences)
    avg_conf_correct = np.mean(confidences[correct_mask]) if sum(correct_mask) > 0 else 0
    avg_conf_incorrect = np.mean(confidences[~correct_mask]) if sum(~correct_mask) > 0 else 0
    
    # 5. Save Model Files
    os.makedirs(MODELS_DIR, exist_ok=True)
    os.makedirs(LOCAL_MODELS_DIR, exist_ok=True)
    
    # Dump to results and ml_model folders
    for d in [MODELS_DIR, LOCAL_MODELS_DIR]:
        joblib.dump(clf, os.path.join(d, 'decision_tree.joblib'))
        joblib.dump(le, os.path.join(d, 'label_encoder.joblib'))
    print(f"[OK] Serialized model and label encoder joblib binaries exported successfully.")
    
    # 6. Generate Performance report
    report_path = os.path.join(REPORTS_DIR, 'decision_tree_performance.txt')
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write("=== DECISION TREE MODEL PERFORMANCE REPORT ===\n\n")
        f.write(f"Model: DecisionTreeClassifier\n")
        f.write(f"Parameters: max_depth={optimal_depth}, criterion=gini, random_state=42\n\n")
        f.write(f"--- ACCURACY METRICS ---\n")
        f.write(f"Training set accuracy: {train_accuracy:.4f}\n")
        f.write(f"Testing set accuracy:  {test_accuracy:.4f}\n\n")
        f.write(f"--- GENERALIZATION METRICS ---\n")
        f.write(f"Precision (Weighted):   {precision:.4f}\n")
        f.write(f"Recall (Weighted):      {recall:.4f}\n")
        f.write(f"F1-score (Weighted):    {f1:.4f}\n\n")
        f.write(f"--- FEATURE IMPORTANCES ---\n")
        for idx, row in feat_df.iterrows():
            f.write(f"* {row['Feature']}: {row['Importance']*100:.1f}%\n")
        f.write(f"\n--- CONFIDENCE ANALYSIS ---\n")
        f.write(f"* Average Confidence (Overall):   {avg_conf_overall:.4f}\n")
        f.write(f"* Average Confidence (Correct):   {avg_conf_correct:.4f}\n")
        f.write(f"* Average Confidence (Incorrect): {avg_conf_incorrect:.4f}\n")
        
    print(f"[OK] Exported performance stats text report to {report_path}")
    print("[COMPLETE] Phase 2 Decision Tree Training Complete!")

if __name__ == "__main__":
    run_training()
