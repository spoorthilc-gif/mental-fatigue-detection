import os
import random
import csv
import pandas as pd
import numpy as np
import matplotlib
# Use a non-interactive backend for matplotlib to avoid GUI thread errors when running asynchronously
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime, timedelta
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder

# Define absolute paths
BASE_DIR = r"C:\Users\spooa\Downloads\mental-fatigue-detection"
CSV_PATH = os.path.join(BASE_DIR, "dataset", "behavioral_data", "live_behavior_dataset.csv")
RESULTS_DIR = os.path.join(BASE_DIR, "results")
GRAPHS_DIR = os.path.join(RESULTS_DIR, "graphs")
REPORTS_DIR = os.path.join(RESULTS_DIR, "reports")
METRICS_DIR = os.path.join(RESULTS_DIR, "metrics")
MODELS_DIR = os.path.join(RESULTS_DIR, "trained_models")

def create_dirs():
    """Ensure results folders requested for reports/graphs exist."""
    for d in [GRAPHS_DIR, REPORTS_DIR, METRICS_DIR, MODELS_DIR]:
        os.makedirs(d, exist_ok=True)
    print("[OK] Verification directories established under /results.")

def check_and_seed_dataset():
    """Check if the behavioral dataset exists and has sufficient records. If not, seed with realistic baseline samples."""
    os.makedirs(os.path.dirname(CSV_PATH), exist_ok=True)
    
    row_count = 0
    if os.path.exists(CSV_PATH):
        try:
            with open(CSV_PATH, 'r', newline='', encoding='utf-8') as f:
                # Deduct 1 for header
                row_count = max(0, sum(1 for _ in f) - 1)
        except Exception:
            row_count = 0

    if row_count < 100:
        print(f"[SEED] Dataset has only {row_count} rows. Generating 200 realistic behavior samples for baseline...")
        now = datetime.now()
        samples = []

        # Seeding realistic typing profiles:
        # - Low Fatigue: High WPM, low errors, high productivity
        # - Medium Fatigue: Medium WPM, medium errors, medium productivity
        # - High Fatigue: Low WPM, high errors, low productivity, long session duration
        for i in range(200):
            level = random.choices(["Low", "Medium", "High"], weights=[0.45, 0.35, 0.20])[0]
            
            if level == "Low":
                wpm = round(random.uniform(45.0, 75.0), 1)
                errors = random.randint(0, 2)
                duration = round(random.uniform(10.0, 300.0), 1)
                # Formula matches typical low fatigue patterns
                productivity_score = round(max(0.0, min(100.0, (wpm * 2.2) - (errors * 3.5) + random.uniform(5, 10))), 1)
                fatigue_score = random.randint(10, 35)
            elif level == "Medium":
                wpm = round(random.uniform(30.0, 45.0), 1)
                errors = random.randint(3, 5)
                duration = round(random.uniform(150.0, 900.0), 1)
                productivity_score = round(max(0.0, min(100.0, (wpm * 2.2) - (errors * 3.5) + random.uniform(0, 5))), 1)
                fatigue_score = random.randint(40, 65)
            else: # High
                wpm = round(random.uniform(12.0, 29.9), 1)
                errors = random.randint(6, 12)
                duration = round(random.uniform(300.0, 1800.0), 1)
                productivity_score = round(max(0.0, min(100.0, (wpm * 2.2) - (errors * 3.5) - random.uniform(5, 15))), 1)
                fatigue_score = random.randint(70, 95)
                
            timestamp = (now - timedelta(seconds=10 * (200 - i))).strftime('%Y-%m-%d %H:%M:%S')
            samples.append([timestamp, wpm, errors, duration, fatigue_score, level, productivity_score])
            
        with open(CSV_PATH, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['timestamp', 'wpm', 'errors', 'session_duration', 'fatigue_score', 'fatigue_level', 'productivity_score'])
            writer.writerows(samples)
        print(f"[OK] Successfully seeded {len(samples)} realistic records to {CSV_PATH}.")

def preprocess_data():
    """Load, clean, encode labels, create splits, and output visualization graphs."""
    print("[START] Starting Phase 1 Data Preprocessing...")
    
    # 1. Read CSV
    df = pd.read_csv(CSV_PATH)
    print(f"  - Loaded raw dataset with shape: {df.shape}")
    
    # 2. Check for missing values
    null_counts = df.isnull().sum()
    print("  - Missing values check:")
    for col, nulls in null_counts.items():
        print(f"    * {col}: {nulls} missing values")
        
    if null_counts.sum() > 0:
        df = df.dropna()
        print(f"  - Dropped missing values. Cleaned shape: {df.shape}")
        
    # 3. Label Encoding
    # High=0, Low=1, Medium=2 alphabetically via standard LabelEncoder.
    le = LabelEncoder()
    df['fatigue_level_encoded'] = le.fit_transform(df['fatigue_level'])
    print(f"  - Encoded target 'fatigue_level' categories: {dict(zip(le.classes_, le.transform(le.classes_)))}")
    
    # 4. Generate Visualizations for Research
    print("[PLOT] Creating professional visualizations...")
    sns.set_theme(style="darkgrid")
    
    # Chart 1: Class Distribution
    plt.figure(figsize=(7, 5))
    sns.countplot(x='fatigue_level', data=df, hue='fatigue_level', palette='viridis', legend=False, order=['Low', 'Medium', 'High'])
    plt.title('Fatigue Level Class Distribution (Training Target)', fontsize=13, fontweight='bold', pad=15)
    plt.xlabel('Fatigue Level Class')
    plt.ylabel('Sample Count')
    plt.tight_layout()
    class_dist_path = os.path.join(GRAPHS_DIR, 'class_distribution.png')
    plt.savefig(class_dist_path, dpi=300)
    plt.close()
    print(f"  - Saved Class Distribution chart to {class_dist_path}")

    # Chart 2: Correlation Heatmap
    plt.figure(figsize=(8, 6))
    numeric_cols = ['wpm', 'errors', 'session_duration', 'fatigue_score', 'productivity_score', 'fatigue_level_encoded']
    corr = df[numeric_cols].corr()
    sns.heatmap(corr, annot=True, cmap='coolwarm', fmt='.2f', linewidths=0.5, annot_kws={"size": 10})
    plt.title('Feature Correlation Matrix', fontsize=13, fontweight='bold', pad=15)
    plt.tight_layout()
    corr_path = os.path.join(GRAPHS_DIR, 'correlation_heatmap.png')
    plt.savefig(corr_path, dpi=300)
    plt.close()
    print(f"  - Saved Correlation Heatmap to {corr_path}")

    # Chart 3: Feature Distributions
    fig, axes = plt.subplots(2, 2, figsize=(11, 9))
    features = ['wpm', 'errors', 'session_duration', 'productivity_score']
    colors = ['#6c63ff', '#ff6b9d', '#ffd166', '#00e5a0']
    
    for i, (feature, color) in enumerate(zip(features, colors)):
        ax = axes[i // 2, i % 2]
        sns.histplot(df[feature], kde=True, ax=ax, color=color, bins=15)
        ax.set_title(f'{feature.upper()} Distribution', fontweight='semibold')
        ax.set_xlabel(feature)
        ax.set_ylabel('Density')
    
    plt.suptitle('Behavioral Feature Distributions', fontsize=14, fontweight='bold', y=0.98)
    plt.tight_layout()
    dist_path = os.path.join(GRAPHS_DIR, 'feature_distributions.png')
    plt.savefig(dist_path, dpi=300)
    plt.close()
    print(f"  - Saved Feature Distributions to {dist_path}")

    # 5. Train/Test Split (80/20)
    X = df[['wpm', 'errors', 'session_duration', 'productivity_score']]
    y = df['fatigue_level_encoded']
    
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)
    print(f"[OK] Train/Test split complete:")
    print(f"  * Total training records (80%): {X_train.shape[0]}")
    print(f"  * Total testing records (20%):  {X_test.shape[0]}")
    
    # Save descriptive statistics report
    stats_report_path = os.path.join(REPORTS_DIR, 'dataset_summary.txt')
    with open(stats_report_path, 'w', encoding='utf-8') as f:
        f.write("=== DATASET DESCRIPTIVE STATISTICS ===\n\n")
        f.write(df[numeric_cols].describe().to_string())
        f.write("\n\n=== CLASS VALUE COUNTS ===\n")
        f.write(df['fatigue_level'].value_counts().to_string())
    print(f"[OK] Exported dataset summary stats text report to {stats_report_path}")
    print("[COMPLETE] Phase 1 Preprocessing Complete! Ready for Model Training.")
    
    return X_train, X_test, y_train, y_test, le

if __name__ == "__main__":
    create_dirs()
    check_and_seed_dataset()
    preprocess_data()
