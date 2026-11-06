# ⏱️ Clocker

Un tracker passif et autonome du temps de travail actif sur macOS.

Clocker se loge discrètement dans la barre des menus de macOS. Il se met automatiquement en pause dès que votre Mac se verrouille, passe en veille ou que l'écran s'éteint.

## 🚀 Installation & Utilisation

### Option A : Application macOS (.dmg)
Téléchargez la dernière version `Clocker-macOS.dmg` depuis l'onglet **Releases** de ce dépôt, ouvrez le fichier et glissez `Clocker.app` dans votre dossier `/Applications`.

### Option B : Depuis les sources (Python)
```bash
# 1. Cloner le repo
git clone [https://github.com/VOTRE_UTILISATEUR/clocker.git](https://github.com/VOTRE_UTILISATEUR/clocker.git)
cd clocker

# 2. Créer et activer l'environnement
python3 -m venv .venv
source .venv/bin/activate

# 3. Installer les dépendances
python -m pip install pyobjc-framework-Cocoa rumps

# 4. Lancer l'application
python clocker_app.py