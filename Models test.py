import pandas as pd
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, roc_auc_score
from sklearn.ensemble import RandomForestClassifier
from pyod.models.iforest import IForest
from pyod.models.ocsvm import OCSVM
from pyod.models.lof import LOF
from pyod.models.knn import KNN
from pyod.models.pca import PCA
from pyod.models.abod import ABOD
from pyod.models.cblof import CBLOF
from pyod.models.hbos import HBOS
from pyod.models.sod import SOD
import warnings
warnings.filterwarnings("ignore")

# === 1. Charger le dataset ===
df = pd.read_csv("metrics_dataset.csv")  # remplace par ton vrai fichier

# Encodage du label
df['label'] = df['label'].map({'normal': 0, 'anomaly': 1})

# Sélection des features utiles
features = ['restarts', 'cpu', 'memory', 'net_tx', 'net_rx']
X = df[features]
y = df['label']

# Normalisation
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)

# Séparation train / test
X_train, X_test, y_train, y_test = train_test_split(X_scaled, y, test_size=0.3, random_state=42)

# === 2. Définir les modèles ===
models = {
    "Isolation Forest": IForest(),
    "One-Class SVM": OCSVM(),
    "Local Outlier Factor": LOF(),
    "KNN": KNN(),
    "PCA": PCA(),
    "ABOD": ABOD(),
    "CBLOF": CBLOF(),
    "HBOS": HBOS(),
    "SOD": SOD(),
    "Random Forest (Supervised)": RandomForestClassifier(n_estimators=100, random_state=42)  # modèle supervisé
}

# === 3. Entraînement et évaluation ===
for name, model in models.items():
    model.fit(X_train, y_train if name == "Random Forest (Supervised)" else None)
    y_pred = model.predict(X_test)
    print(f"\n{name}")
    print(classification_report(y_test, y_pred, target_names=["Normal", "Anomaly"]))
    print("AUC:", roc_auc_score(y_test, y_pred))

# === 4. Bonus : AutoEncoder ===
try:
    from pyod.models.auto_encoder import AutoEncoder

    autoencoder = AutoEncoder(epochs=30, verbose=0)
    autoencoder.fit(X_train)
    y_pred = autoencoder.predict(X_test)
    print(f"\nAutoEncoder")
    print(classification_report(y_test, y_pred, target_names=["Normal", "Anomaly"]))
    print("AUC:", roc_auc_score(y_test, y_pred))
except Exception as e:
    print("\n TensorFlow ou AutoEncoder indisponible :", str(e))
