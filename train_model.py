import pandas as pd, numpy as np, pickle
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import classification_report, confusion_matrix
import matplotlib.pyplot as plt
import seaborn as sns

FEATURES = ["mag_mean","mag_std","mag_range","std_x","std_y","std_z"]

df = pd.read_csv("movement_data.csv", header=None, names=FEATURES+["label"])
print(df["label"].value_counts(), "\n")

X, y = df[FEATURES], df["label"]
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, stratify=y, random_state=42)

model = RandomForestClassifier(n_estimators=100, random_state=42)
model.fit(X_train, y_train)

scores = cross_val_score(model, X, y, cv=5)
print(f"✅ Accuracy CV-5: {scores.mean():.3f} ± {scores.std():.3f}\n")
print(classification_report(y_test, model.predict(X_test)))

# Matriz de confusión
labels = sorted(y.unique())
cm = confusion_matrix(y_test, model.predict(X_test), labels=labels)
plt.figure(figsize=(5,4))
sns.heatmap(cm, annot=True, fmt="d", cmap="Greens",
            xticklabels=labels, yticklabels=labels)
plt.title("Matriz de Confusión"); plt.tight_layout()
plt.savefig("confusion_matrix.png"); plt.show()

with open("model.pkl","wb") as f: pickle.dump(model, f)
print("✅ Modelo guardado en model.pkl")