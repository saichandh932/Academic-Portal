# -*- coding: utf-8 -*-
"""
model/train.py
--------------
Multi-Model Training — Student Performance Prediction
Trains & compares: Logistic Regression, Random Forest, SVM, Gradient Boosting
Auto-selects the best model by 5-fold cross-validation accuracy.
Saves the best model as best_model.pkl alongside the comparison report.
"""
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

import os
import json
import warnings
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import seaborn as sns
import joblib

from sklearn.model_selection import train_test_split, StratifiedKFold, cross_val_score
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.svm import SVC
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    ConfusionMatrixDisplay,
    f1_score,
)

warnings.filterwarnings("ignore")

# ─── Paths ────────────────────────────────────────────────────────────────────
BASE_DIR  = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_PATH = os.path.join(BASE_DIR, "data", "students.csv")
MODEL_DIR = os.path.join(BASE_DIR, "model")
os.makedirs(MODEL_DIR, exist_ok=True)

# ─── 1. Load & Prepare Data ───────────────────────────────────────────────────
print("=" * 65)
print("  STUDENT PERFORMANCE — MULTI-MODEL ML COMPARISON")
print("=" * 65)

df = pd.read_csv(DATA_PATH)
df.dropna(inplace=True)

FEATURE_COLS = ["study_hours", "attendance", "previous_score", "assignments", "internal_marks"]
TARGET_COL   = "performance"

X = df[FEATURE_COLS].values
y = df[TARGET_COL].values

le = LabelEncoder()
y_enc      = le.fit_transform(y)
class_names = le.classes_

print(f"\n[Data]  Shape   : {df.shape}")
print(f"[Data]  Classes : {list(class_names)}")
print(f"[Data]  Distribution:\n{pd.Series(y).value_counts().to_string()}\n")

# ─── 2. Train / Test Split ────────────────────────────────────────────────────
X_train, X_test, y_train, y_test = train_test_split(
    X, y_enc, test_size=0.20, random_state=42, stratify=y_enc
)

scaler  = StandardScaler()
X_train_s = scaler.fit_transform(X_train)
X_test_s  = scaler.transform(X_test)

# ─── 3. Define All Models ─────────────────────────────────────────────────────
MODELS = {
    "Logistic Regression": LogisticRegression(
        solver="lbfgs", max_iter=1000, C=1.0, random_state=42
    ),
    "Random Forest": RandomForestClassifier(
        n_estimators=200, max_depth=8, min_samples_split=5,
        random_state=42, n_jobs=-1
    ),
    "Gradient Boosting": GradientBoostingClassifier(
        n_estimators=150, learning_rate=0.1, max_depth=4, random_state=42
    ),
    "SVM (RBF)": SVC(
        kernel="rbf", C=1.0, gamma="scale",
        probability=True, random_state=42
    ),
}

# ─── 4. Train & Evaluate All Models ──────────────────────────────────────────
cv       = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
results  = {}
best_name = None
best_cv   = -1

print(f"\n{'Model':<25} {'Train Acc':>10} {'Test Acc':>10} {'CV Mean':>10} {'CV Std':>8}")
print("─" * 70)

for name, model in MODELS.items():
    # Logistic Regression and SVM use scaled features
    use_scaled = name in ("Logistic Regression", "SVM (RBF)")
    Xt = X_train_s if use_scaled else X_train
    Xv = X_test_s  if use_scaled else X_test

    model.fit(Xt, y_train)
    y_pred    = model.predict(Xv)
    train_acc = accuracy_score(y_train, model.predict(Xt))
    test_acc  = accuracy_score(y_test, y_pred)
    cv_scores = cross_val_score(model, Xt, y_train, cv=cv, scoring="accuracy")
    f1        = f1_score(y_test, y_pred, average="weighted")

    results[name] = {
        "model":       model,
        "use_scaled":  use_scaled,
        "train_acc":   round(train_acc, 4),
        "test_acc":    round(test_acc,  4),
        "cv_mean":     round(cv_scores.mean(), 4),
        "cv_std":      round(cv_scores.std(),  4),
        "f1_weighted": round(f1, 4),
        "y_pred":      y_pred,
    }

    print(f"{name:<25} {train_acc*100:>9.2f}% {test_acc*100:>9.2f}% "
          f"{cv_scores.mean()*100:>9.2f}% {cv_scores.std()*100:>7.2f}%")

    if cv_scores.mean() > best_cv:
        best_cv   = cv_scores.mean()
        best_name = name

print("─" * 70)
print(f"\n🏆 Best Model: {best_name}  (CV Accuracy: {best_cv*100:.2f}%)\n")

# ─── 5. Detailed Report for Best Model ───────────────────────────────────────
best = results[best_name]
best_model  = best["model"]
Xv_best     = X_test_s if best["use_scaled"] else X_test

print(f"[Report] Classification Report — {best_name}:\n")
print(classification_report(y_test, best["y_pred"], target_names=class_names))

# ─── 6. Save Comparison Report as JSON ───────────────────────────────────────
comparison_report = {
    "best_model":    best_name,
    "best_cv_acc":   round(best_cv * 100, 2),
    "models": {
        name: {
            "train_accuracy": round(r["train_acc"] * 100, 2),
            "test_accuracy":  round(r["test_acc"]  * 100, 2),
            "cv_mean":        round(r["cv_mean"]   * 100, 2),
            "cv_std":         round(r["cv_std"]    * 100, 2),
            "f1_weighted":    round(r["f1_weighted"]* 100, 2),
        }
        for name, r in results.items()
    }
}
report_path = os.path.join(MODEL_DIR, "model_comparison.json")
with open(report_path, "w", encoding="utf-8") as f:
    json.dump(comparison_report, f, indent=2)
print(f"[Save]  Comparison report → {report_path}")

# ─── 7. Visualisation ─────────────────────────────────────────────────────────
fig, axes = plt.subplots(2, 2, figsize=(18, 13))
fig.suptitle("Student Performance — Multi-Model ML Evaluation", fontsize=16,
             fontweight="bold", y=0.98)
plt.rcParams["font.family"] = "DejaVu Sans"

model_names_list = list(results.keys())
colors_map = {
    "Logistic Regression": "#4C72B0",
    "Random Forest":       "#55A868",
    "Gradient Boosting":   "#C44E52",
    "SVM (RBF)":           "#8172B2",
}

# ── 7a. Model Accuracy Comparison Bar Chart ───────────────────────────────────
ax = axes[0, 0]
x     = np.arange(len(model_names_list))
width = 0.28
test_accs  = [results[n]["test_acc"]  * 100 for n in model_names_list]
cv_means   = [results[n]["cv_mean"]   * 100 for n in model_names_list]
f1s        = [results[n]["f1_weighted"] * 100 for n in model_names_list]

bars1 = ax.bar(x - width, test_accs,  width, label="Test Acc",   color="#4C72B0", edgecolor="white")
bars2 = ax.bar(x,         cv_means,   width, label="CV Mean",    color="#55A868", edgecolor="white")
bars3 = ax.bar(x + width, f1s,        width, label="F1 (weighted)", color="#C44E52", edgecolor="white")

ax.set_xticks(x)
ax.set_xticklabels([n.replace(" ", "\n") for n in model_names_list], fontsize=9)
ax.set_ylim(0, 115)
ax.set_ylabel("Score (%)")
ax.set_title("Model Comparison: Accuracy & F1", fontweight="bold")
ax.legend(loc="lower right", fontsize=8)
for bar in [*bars1, *bars2, *bars3]:
    ax.text(bar.get_x() + bar.get_width() / 2,
            bar.get_height() + 1, f"{bar.get_height():.1f}%",
            ha="center", va="bottom", fontsize=7, fontweight="bold")

# ── 7b. Confusion Matrix for Best Model ──────────────────────────────────────
ax = axes[0, 1]
cm   = confusion_matrix(y_test, best["y_pred"])
disp = ConfusionMatrixDisplay(confusion_matrix=cm, display_labels=class_names)
disp.plot(ax=ax, colorbar=False, cmap="Blues")
ax.set_title(f"Confusion Matrix — {best_name}", fontweight="bold")
ax.set_xlabel("Predicted Label")
ax.set_ylabel("True Label")

# ── 7c. Feature Importance (best model) ──────────────────────────────────────
ax = axes[1, 0]
if hasattr(best_model, "feature_importances_"):
    importances = best_model.feature_importances_
    ax.barh(FEATURE_COLS, importances * 100,
            color=[colors_map.get(best_name, "#4C72B0")] * len(FEATURE_COLS),
            edgecolor="white")
    ax.set_xlabel("Importance (%)")
    ax.set_title(f"Feature Importance — {best_name}", fontweight="bold")
    for i, v in enumerate(importances * 100):
        ax.text(v + 0.5, i, f"{v:.1f}%", va="center", fontsize=10, fontweight="bold")
elif hasattr(best_model, "coef_"):
    # For LR/SVM: show mean abs coefficient per feature
    mean_coef = np.abs(best_model.coef_).mean(axis=0)
    mean_coef_pct = (mean_coef / mean_coef.sum()) * 100
    ax.barh(FEATURE_COLS, mean_coef_pct, color="#4C72B0", edgecolor="white")
    ax.set_xlabel("Mean |Coefficient| Weight (%)")
    ax.set_title(f"Feature Influence — {best_name}", fontweight="bold")
    for i, v in enumerate(mean_coef_pct):
        ax.text(v + 0.5, i, f"{v:.1f}%", va="center", fontsize=10, fontweight="bold")

# ── 7d. Per-Class F1 for Best Model ──────────────────────────────────────────
ax = axes[1, 1]
per_class_f1 = f1_score(y_test, best["y_pred"], average=None)
bar_colors   = ["#4C72B0", "#DD8452", "#55A868"]
ax.barh(class_names, per_class_f1 * 100,
        color=bar_colors[:len(class_names)], edgecolor="white")
ax.set_xlim(0, 115)
ax.set_xlabel("F1-Score (%)")
ax.set_title(f"Per-Class F1-Score — {best_name}", fontweight="bold")
for i, v in enumerate(per_class_f1 * 100):
    ax.text(v + 1.5, i, f"{v:.1f}%", va="center", fontsize=11, fontweight="bold")

plt.tight_layout(rect=[0, 0, 1, 0.96])
out_path = os.path.join(MODEL_DIR, "evaluation.png")
plt.savefig(out_path, dpi=150, bbox_inches="tight")
print(f"[Plot]  Evaluation chart saved → {out_path}")

# ─── 8. Save Best Model Artefacts ────────────────────────────────────────────
# Always save as the canonical names so backend needs no changes
joblib.dump(best_model, os.path.join(MODEL_DIR, "logistic_model.pkl"))
joblib.dump(scaler,     os.path.join(MODEL_DIR, "scaler.pkl"))
joblib.dump(le,         os.path.join(MODEL_DIR, "label_encoder.pkl"))

# Also save under best_model.pkl for clarity
joblib.dump(best_model, os.path.join(MODEL_DIR, "best_model.pkl"))

print(f"[Save]  Best model ({best_name}) → logistic_model.pkl + best_model.pkl")
print(f"[Save]  Scaler    → scaler.pkl")
print(f"[Save]  Encoder   → label_encoder.pkl")

# ─── 9. Feature Importance Summary ───────────────────────────────────────────
print("\n[Feature Impact Summary]")
if hasattr(best_model, "feature_importances_"):
    for feat, imp in sorted(zip(FEATURE_COLS, best_model.feature_importances_),
                            key=lambda x: -x[1]):
        print(f"  {feat:<20}: {imp*100:.2f}%")
elif hasattr(best_model, "coef_"):
    mean_abs = np.abs(best_model.coef_).mean(axis=0)
    for feat, val in sorted(zip(FEATURE_COLS, mean_abs), key=lambda x: -x[1]):
        print(f"  {feat:<20}: {val:.4f} (mean |coef|)")

print("\n" + "=" * 65)
print(f"  Training complete. Best: {best_name} @ {best_cv*100:.2f}% CV")
print("=" * 65)
