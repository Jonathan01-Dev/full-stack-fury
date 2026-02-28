
# 🏝️ ARCHIPEL - Nœud de Communication P2P Souverain

## 📌 Présentation

Archipel est un protocole de communication Peer-to-Peer décentralisé, conçu pour fonctionner en mode **"Zéro-Connexion"** Internet. Ce projet garantit la survie des échanges sur un réseau local ad-hoc grâce à un chiffrement de bout en bout et une architecture inspirée de BitTorrent.
🛠️ Choix Technologiques (Sprint 0)

Conformément aux objectifs du **Sprint 0**, nous avons arrêté les choix suivants :

Langage : **Python 3.10+**.

Justification* : Rapidité de prototypage critique pour un hackathon de 24h et accès à des bibliothèques cryptographiques de haut niveau (`PyNaCl`).




Transport Découverte: UDP Multicas sur l'adresse `239.255.42.99:6000`.


Transport Transfert : TCP Sockets** sur le port `7777` (défaut).


Identité & Signature : **Ed25519** (Courbe Elliptique) pour une authentification sans autorité centrale (CA).



 🏗️ Architecture du Protocole (v1)

Chaque paquet circulant sur le réseau respecte la spécification binaire **ARCHIPEL PACKET v1**:

| Champ | Taille | Type | Description |
| --- | --- | --- | --- |
| **MAGIC** | 4 octets | `char[4]` | Identifiant : `ARCH` 

 |
| **TYPE** | 1 octet | `uint8` | Type de message (ex: `0x01` HELLO) 

 |
| **NODE ID** | 32 octets | `bytes` | Clé publique Ed25519 (ID unique) 

 |
| **PAYLOAD LEN** | 4 octets | `uint32_BE` | Taille du contenu 

 |
| **PAYLOAD** | Variable | `bytes` | Données chiffrées (AES-256-GCM) 

 |
| **SIGNATURE** | 32 octets | `bytes` | HMAC-SHA256 pour l'intégrité 

 |

 Implémentation de la Sécurité

Authentification : Utilisation de signatures Ed25519 pour prouver l'identité de l'émetteur sans serveur central.


Confidentialité : Chiffrement des transferts via AES-256-GCM après un handshake X25519.


Zéro Clé en clair : Les clés privées sont stockées localement dans `data/keys/` et sont exclues du dépôt Git via le fichier `.gitignore`.



## 📦 Structure du Projet

```text
Archipel/
[cite_start]├── README.md              # Documentation et spécifications (S0) [cite: 447]
[cite_start]├── main.py                # Point d'entrée et orchestrateur [cite: 686]
├── src/
[cite_start]│   ├── crypto/            # PKI, signatures (Ed25519) [cite: 686]
[cite_start]│   ├── network/           # Discovery (UDP) & Transfert (TCP) [cite: 686]
[cite_start]│   └── protocol/          # Sérialisation binaire des paquets [cite: 686]
└── data/
    [cite_start]├── keys/              # Clés privées (Ignorées par git) [cite: 686]
    [cite_start]└── shared/            # Dossier de réception des fichiers [cite: 686]

```

## 🚀 Installation & Lancement

1. **Prérequis** :
```bash
[cite_start]pip install pynacl pycryptodome [cite: 683]

```


2. **Lancement du nœud** :
```bash
python main.py

```


 👥 Équipe: full stack fury


