# -*- coding: utf-8 -*-
"""
Phase 2 - ML Model Training
Multinomial Logistic Regression on Student Performance Dataset
Train/Test Split | Model Training | Evaluation
"""
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

import os
import warnings
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")          # non-interactive backend
import matplotlib.pyplot as plt
import seaborn as sns
import joblib

from sklearn.model_selection import train_test_split, StratifiedKFold, cross_val_score
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    ConfusionMatrixDisplay,
)

warnings.filterwarnings("ignore")

# ─── Paths ───────────────────────────────────────────────────────────────────
BASE_DIR   = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_PATH  = os.path.join(BASE_DIR, "data", "students.csv")
MODEL_DIR  = os.path.join(BASE_DIR, "model")
os.makedirs(MODEL_DIR, exist_ok=True)

# ─── 1. Load Data ─────────────────────────────────────────────────────────────
print("=" * 60)
print("  STUDENT PERFORMANCE — MULTINOMIAL LOGISTIC REGRESSION")
print("=" * 60)

df = pd.read_csv(DATA_PATH)
df.dropna(inplace=True)

print(f"\n[Data]  Shape  : {df.shape}")
print(f"[Data]  Columns: {list(df.columns)}")
print(f"[Data]  Class distribution:\n{df['performance'].value_counts()}\n")

# ─── 2. Feature / Target Split ────────────────────────────────────────────────
FEATURE_COLS = ["study_hours", "attendance", "previous_score",
                "assignments", "internal_marks"]
TARGET_COL   = "performance"

X = df[FEATURE_COLS].values
y = df[TARGET_COL].values

# Encode target labels  (High → 0, Low → 1, Medium → 2  by alphabetical sort)
le = LabelEncoder()
y_enc = le.fit_transform(y)
class_names = le.classes_          # ['High', 'Low', 'Medium']

print(f"[Prep]  Features : {FEATURE_COLS}")
print(f"[Prep]  Classes  : {list(class_names)}")

# ─── 3. Train / Test Split (80 / 20, stratified) ─────────────────────────────
X_train, X_test, y_train, y_test = train_test_split(
    X, y_enc, test_size=0.20, random_state=42, stratify=y_enc
)
print(f"\n[Split] Train samples : {len(X_train)}")
print(f"[Split] Test  samples : {len(X_test)}")

# ─── 4. Feature Scaling ───────────────────────────────────────────────────────
scaler  = StandardScaler()
X_train = scaler.fit_transform(X_train)
X_test  = scaler.transform(X_test)

# ─── 5. Multinomial Logistic Regression ──────────────────────────────────────
model = LogisticRegression(
    solver="lbfgs",      # uses multinomial (softmax) loss by default in sklearn ≥ 1.7
    max_iter=1000,
    C=1.0,
    random_state=42,
)
model.fit(X_train, y_train)
print("\n[Model] Multinomial Logistic Regression trained successfully.")

# ─── 6. Evaluation ────────────────────────────────────────────────────────────
y_pred       = model.predict(X_test)
test_acc     = accuracy_score(y_test, y_pred)
train_acc    = accuracy_score(y_train, model.predict(X_train))

# 5-fold stratified cross-validation on the full training set
cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
cv_scores = cross_val_score(model, X_train, y_train, cv=cv, scoring="accuracy")

print(f"\n{'─'*40}")
print(f"  Training Accuracy  : {train_acc * 100:.2f}%")
print(f"  Test Accuracy      : {test_acc  * 100:.2f}%")
print(f"  CV Accuracy (5-fold): {cv_scores.mean()*100:.2f}% ± {cv_scores.std()*100:.2f}%")
print(f"{'─'*40}")

print("\n[Report] Classification Report:\n")
print(classification_report(y_test, y_pred, target_names=class_names))

# ─── 7. Visualisation ─────────────────────────────────────────────────────────
fig, axes = plt.subplots(1, 3, figsize=(18, 5))
fig.suptitle("Student Performance — Model Evaluation", fontsize=15, fontweight="bold", y=1.02)

# ── 7a. Confusion Matrix ──────────────────────────────────────────────────────
cm = confusion_matrix(y_test, y_pred)
disp = ConfusionMatrixDisplay(confusion_matrix=cm, display_labels=class_names)
disp.plot(ax=axes[0], colorbar=False, cmap="Blues")
axes[0].set_title("Confusion Matrix", fontsize=13, fontweight="bold")
axes[0].set_xlabel("Predicted Label", fontsize=11)
axes[0].set_ylabel("True Label", fontsize=11)

# ── 7b. Accuracy Bar Chart ────────────────────────────────────────────────────
labels  = ["Train", "Test", "CV Mean"]
values  = [train_acc * 100, test_acc * 100, cv_scores.mean() * 100]
colors  = ["#4C72B0", "#55A868", "#C44E52"]
bars    = axes[1].bar(labels, values, color=colors, width=0.5, edgecolor="white", linewidth=1.2)
axes[1].set_ylim(0, 110)
axes[1].set_ylabel("Accuracy (%)", fontsize=11)
axes[1].set_title("Accuracy Summary", fontsize=13, fontweight="bold")
axes[1].axhline(y=100, color="grey", linestyle="--", linewidth=0.8, alpha=0.5)
for bar, val in zip(bars, values):
    axes[1].text(bar.get_x() + bar.get_width() / 2,
                 bar.get_height() + 1.5,
                 f"{val:.1f}%",
                 ha="center", va="bottom", fontsize=11, fontweight="bold")

# ── 7c. Per-class F1-Score ─────────────────────────────────────────────────────
from sklearn.metrics import f1_score
f1_scores = f1_score(y_test, y_pred, average=None)
axes[2].barh(class_names, f1_scores * 100,
             color=["#4C72B0", "#DD8452", "#55A868"], edgecolor="white", linewidth=1.2)
axes[2].set_xlim(0, 110)
axes[2].set_xlabel("F1-Score (%)", fontsize=11)
axes[2].set_title("Per-Class F1-Score", fontsize=13, fontweight="bold")
for i, (cls, val) in enumerate(zip(class_names, f1_scores * 100)):
    axes[2].text(val + 1.5, i, f"{val:.1f}%",
                 va="center", fontsize=11, fontweight="bold")

plt.tight_layout()
out_path = os.path.join(MODEL_DIR, "evaluation.png")
plt.savefig(out_path, dpi=150, bbox_inches="tight")
print(f"\n[Plot]  Evaluation chart saved → {out_path}")

# ─── 8. Save Artefacts ────────────────────────────────────────────────────────
joblib.dump(model,  os.path.join(MODEL_DIR, "logistic_model.pkl"))
joblib.dump(scaler, os.path.join(MODEL_DIR, "scaler.pkl"))
joblib.dump(le,     os.path.join(MODEL_DIR, "label_encoder.pkl"))

print(f"[Save]  Model   saved → {os.path.join(MODEL_DIR, 'logistic_model.pkl')}")
print(f"[Save]  Scaler  saved → {os.path.join(MODEL_DIR, 'scaler.pkl')}")
print(f"[Save]  Encoder saved → {os.path.join(MODEL_DIR, 'label_encoder.pkl')}")

# ─── 9. Feature Importance (coefficients) ─────────────────────────────────────
coef_df = pd.DataFrame(
    model.coef_,
    index=class_names,
    columns=FEATURE_COLS
)
print("\n[Coeff] Log-odds coefficients per class:")
print(coef_df.round(4).to_string())

print("\n" + "=" * 60)
print("  Training complete.")
print("=" * 60)
