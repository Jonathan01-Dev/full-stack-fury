# Archipel P2P - Hackathon Fury

Archipel est un nœud de communication P2P décentralisé, sécurisé et intelligent. Il permet l'échange de messages chiffrés et de fichiers volumineux sans serveur central.

## 🚀 Fonctionnalités
- **Découverte Automatique (UDP Multicast)** : Les nœuds se découvrent sur le réseau local sans configuration.
- **Canal Sécurisé (NaCL/ChaCha20)** : Echange de clés Diffie-Hellman éphémères pour un chiffrement de bout en bout.
- **Web of Trust (TOFU)** : Un pair est marqué comme fiable dès le premier échange (Trust On First Use) et peut être approuvé manuellement.
- **Transfert de Fichiers Robuste** : Fichiers découpés en chunks, avec vérification par hash SHA-256.
- **Intégration Gemini AI** : Assistant IA intégré au chat via `@archipel-ai` ou `/ask`.
- **Double Interface** : CLI interactif et Tableau de bord Web local.

## 🏗️ Architecture
```text
[ CLI / Web UI ] <----> [ Node Controller ]
                           |
       +-------------------+-------------------+
       |                   |                   |
 [ Discovery ]      [ SecureChannel ]   [ FileTransfer ]
 (UDP 6000)         (UDP 6001)          (Chunks & Manifest)
```

### Primitives Cryptographiques
- **nacl.public.Box** : Pour l'échange de clés asymétriques (Curve25519).
- **nacl.secret.SecretBox** : Chiffrement symétrique (XSalsa20-Poly1305) pour les messages et chunks.
- **SHA-256** : Pour l'intégrité des fichiers et des chunks.
- **HMAC-SHA256** : Pour l'authentification des messages chiffrés.

## 📦 Installation
1. Clonez le projet.
2. Installez les dépendances :
   ```bash
   pip install -r requirements.txt
   ```
3. Créez un fichier `.env` avec votre clé Gemini API :
   ```bash
   GEMINI_API_KEY=votre_cle_ici
   ```

## 🎮 Guide de la Démo
### Cas 1 : Démarrage et Découverte
1. Lancez le nœud sur le PC 1 : `python main.py --port 7000`
2. Lancez le nœud sur le PC 2 : `python main.py --port 7000`
3. Tapez `peers` pour voir les deux nœuds s'identifier.

### Cas 2 : Chat et IA
1. Sur le PC 1, envoyez un message au PC 2 : `msg <node_id> "Salut Archipel !"`
2. Posez une question à l'IA : `/ask "Comment fonctionne le Web of Trust ?"`

### Cas 3 : Transfert de Fichier
1. Sur le PC 1, proposez un fichier : `send <node_id> chemin/vers/image.jpg`
2. Sur le PC 2, listez les offres : `receive`
3. Sur le PC 2, téléchargez le fichier : `download <offer_id>`

### Cas 4 : Interface Web
1. Ouvrez votre navigateur sur `http://localhost:5000`.
2. Suivez l'état du réseau et gérez la confiance des pairs graphiquement.

## ⚠️ Limitations & Améliorations
- **NAT Traversal** : Actuellement optimisé pour le réseau local. Support STUN/TURN à ajouter.
- **Historique de Chat** : Non persistant entre les sessions.
- **Vérification de Confiance** : Ajouter une signature cryptographique des approbations de pairs.

## 👥 Équipe
- Développé par **Archipel Team** (Gemini CLI Enhanced).
