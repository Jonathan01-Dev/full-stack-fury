from flask import Flask, jsonify, request, render_template_string
from flask_cors import CORS
import threading
import os
import time
from werkzeug.utils import secure_filename

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Archipel P2P | Enterprise Node Dashboard</title>
    <link href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;700&family=Inter:wght@400;600;700&display=swap" rel="stylesheet">
    <style>
        :root { --bg: #0b0f19; --sidebar-bg: #111827; --card-bg: #1f2937; --accent: #06b6d4; --text: #f3f4f6; --text-muted: #9ca3af; --border: #374151; --success: #10b981; --danger: #ef4444; --warning: #f59e0b; }
        * { box-sizing: border-box; }
        body { font-family: 'Inter', sans-serif; background: var(--bg); color: var(--text); margin: 0; display: flex; height: 100vh; overflow: hidden; }
        
        /* Sidebar Navigation */
        .sidebar { width: 70px; background: var(--sidebar-bg); border-right: 1px solid var(--border); display: flex; flex-direction: column; align-items: center; padding: 20px 0; transition: width 0.3s; z-index: 100; }
        .sidebar:hover { width: 220px; align-items: flex-start; padding: 20px; }
        .sidebar-item { display: flex; align-items: center; width: 100%; padding: 12px; margin-bottom: 10px; cursor: pointer; border-radius: 8px; transition: 0.2s; white-space: nowrap; overflow: hidden; }
        .sidebar-item:hover { background: rgba(6, 182, 212, 0.1); color: var(--accent); }
        .sidebar-item.active { background: var(--accent); color: var(--bg); font-weight: bold; }
        .sidebar-item .icon { font-size: 1.5rem; min-width: 30px; text-align: center; }
        .sidebar-item .label { margin-left: 15px; opacity: 0; transition: 0.2s; font-size: 0.9rem; }
        .sidebar:hover .label { opacity: 1; }

        /* Main Content */
        .main { flex: 1; display: flex; flex-direction: column; overflow: hidden; position: relative; }
        .header { height: 60px; border-bottom: 1px solid var(--border); background: var(--sidebar-bg); display: flex; align-items: center; justify-content: space-between; padding: 0 30px; }
        .content-area { flex: 1; overflow-y: auto; padding: 30px; }
        .tab-content { display: none; height: 100%; }
        .tab-content.active { display: block; animation: fadeIn 0.3s; }
        
        /* Dashboard Layout */
        .dashboard-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px; margin-bottom: 30px; }
        .stat-card { background: var(--card-bg); padding: 20px; border-radius: 12px; border: 1px solid var(--border); }
        .stat-title { color: var(--text-muted); font-size: 0.8rem; text-transform: uppercase; letter-spacing: 1px; }
        .stat-value { font-size: 1.8rem; font-weight: 700; margin-top: 5px; font-family: 'JetBrains Mono', monospace; }
        
        /* Lists and Tables */
        .table-container { background: var(--card-bg); border-radius: 12px; border: 1px solid var(--border); overflow: hidden; }
        table { width: 100%; border-collapse: collapse; text-align: left; }
        th { background: rgba(0,0,0,0.2); padding: 15px; font-size: 0.8rem; color: var(--text-muted); border-bottom: 1px solid var(--border); }
        td { padding: 15px; border-bottom: 1px solid var(--border); font-size: 0.9rem; }
        tr:hover { background: rgba(255,255,255,0.02); }

        /* Chat System */
        .chat-container { display: flex; height: 100%; background: var(--card-bg); border-radius: 12px; border: 1px solid var(--border); overflow: hidden; }
        .chat-sidebar { width: 250px; border-right: 1px solid var(--border); background: rgba(0,0,0,0.1); }
        .chat-main { flex: 1; display: flex; flex-direction: column; }
        .chat-peers-list { padding: 10px; height: 100%; overflow-y: auto; }
        .chat-peer-item { padding: 12px; border-radius: 8px; cursor: pointer; margin-bottom: 5px; transition: 0.2s; display: flex; flex-direction: column; }
        .chat-peer-item:hover { background: rgba(255,255,255,0.05); }
        .chat-peer-item.active { background: rgba(6, 182, 212, 0.2); border: 1px solid var(--accent); }
        .peer-status { display: inline-block; width: 8px; height: 8px; border-radius: 50%; background: var(--success); margin-right: 8px; }

        .chat-messages { flex: 1; padding: 20px; overflow-y: auto; background: var(--bg); display: flex; flex-direction: column; gap: 10px; }
        .msg-bubble { max-width: 70%; padding: 12px 16px; border-radius: 12px; font-size: 0.9rem; line-height: 1.4; position: relative; }
        .msg-mine { align-self: flex-end; background: var(--accent); color: var(--bg); border-bottom-right-radius: 2px; }
        .msg-theirs { align-self: flex-start; background: var(--card-bg); border-bottom-left-radius: 2px; border: 1px solid var(--border); }
        .msg-ai { align-self: flex-start; background: var(--warning); color: #000; font-weight: 600; }
        .msg-meta { font-size: 0.7rem; margin-top: 5px; opacity: 0.7; }

        .chat-input-area { padding: 20px; border-top: 1px solid var(--border); display: flex; gap: 12px; }
        input[type="text"], select, textarea { flex: 1; background: var(--bg); border: 1px solid var(--border); color: white; padding: 12px; border-radius: 8px; outline: none; }
        input:focus { border-color: var(--accent); }
        button { background: var(--accent); color: var(--bg); border: none; padding: 10px 20px; border-radius: 8px; font-weight: 700; cursor: pointer; }
        button:hover { opacity: 0.9; }
        button.danger { background: var(--danger); color: white; }

        /* Logs */
        .log-area { font-family: 'JetBrains Mono', monospace; background: #000; padding: 20px; border-radius: 8px; height: 300px; overflow-y: auto; border: 1px solid var(--border); }
        .log-line { font-size: 0.8rem; margin-bottom: 4px; border-bottom: 1px solid #111; padding-bottom: 2px; }
        .log-time { color: var(--text-muted); }
        .log-text { color: var(--success); }

        @keyframes fadeIn { from { opacity: 0; } to { opacity: 1; } }
    </style>
</head>
<body>
    <div class="sidebar">
        <div class="sidebar-item active" onclick="switchTab('dashboard', this)">
            <span class="icon">📊</span><span class="label">Tableau de Bord</span>
        </div>
        <div class="sidebar-item" onclick="switchTab('chat', this)">
            <span class="icon">💬</span><span class="label">Messagerie</span>
        </div>
        <div class="sidebar-item" onclick="switchTab('files', this)">
            <span class="icon">📂</span><span class="label">Fichiers</span>
        </div>
        <div class="sidebar-item" onclick="switchTab('network', this)">
            <span class="icon">🌐</span><span class="label">Réseau</span>
        </div>
        <div style="flex: 1;"></div>
        <div class="sidebar-item" onclick="location.reload()">
            <span class="icon">🔄</span><span class="label">Actualiser</span>
        </div>
    </div>

    <div class="main">
        <div class="header">
            <div><span style="color:var(--text-muted)">Nœud:</span> <b id="node-id-display">...</b></div>
            <div id="uptime-display" style="font-family: 'JetBrains Mono', monospace; font-size: 0.8rem;">Uptime: 0s</div>
        </div>

        <div class="content-area">
            
            <!-- ONGLET DASHBOARD -->
            <div id="tab-dashboard" class="tab-content active">
                <div class="dashboard-grid">
                    <div class="stat-card">
                        <div class="stat-title">Pairs Actifs</div>
                        <div class="stat-value" id="stat-peers">0</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-title">Transferts en Cours</div>
                        <div class="stat-value" id="stat-transfers">0</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-title">Port Sécurisé</div>
                        <div class="stat-value" id="stat-port">...</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-title">IA Gemini</div>
                        <div class="stat-value" id="stat-ai">OFF</div>
                    </div>
                </div>

                <div class="card" style="margin-bottom: 20px;">
                    <h2 style="border:none">📡 Logs Système Récents</h2>
                    <div id="logs-area" class="log-area"></div>
                </div>
            </div>

            <!-- ONGLET MESSAGERIE -->
            <div id="tab-chat" class="tab-content">
                <div class="chat-container">
                    <div class="chat-sidebar">
                        <div style="padding:15px; border-bottom:1px solid var(--border); font-weight:bold; color:var(--accent)">Contacts P2P</div>
                        <div id="chat-peer-list" class="chat-peers-list"></div>
                    </div>
                    <div class="chat-main">
                        <div id="chat-header" style="padding:15px; border-bottom:1px solid var(--border); font-weight:bold;">Sélectionnez un pair</div>
                        <div id="chat-window" class="chat-messages"></div>
                        <div class="chat-input-area">
                            <input type="text" id="chat-input" placeholder="Ecrivez votre message (taguez l'IA avec @archipel-ai)..." onkeypress="if(event.key==='Enter') sendChatMessage()">
                            <button onclick="sendChatMessage()">Envoyer</button>
                        </div>
                    </div>
                </div>
            </div>

            <!-- ONGLET FICHIERS -->
            <div id="tab-files" class="tab-content">
                <div style="display:flex; gap:20px; margin-bottom:20px;">
                    <div class="card" style="flex:1">
                        <h2>📤 Partager un nouveau fichier</h2>
                        <div style="display:flex; gap:10px; align-items:center;">
                            <input type="file" id="file-upload-input" style="flex:1">
                            <select id="file-target-peer" style="width:200px"></select>
                            <button onclick="shareFile()">Partager</button>
                        </div>
                    </div>
                </div>

                <div class="card">
                    <h2>📥 Liste des fichiers disponibles sur le réseau</h2>
                    <div class="table-container">
                        <table>
                            <thead>
                                <tr>
                                    <th>Nom du Fichier</th>
                                    <th>Taille</th>
                                    <th>Chunks</th>
                                    <th>Source(s)</th>
                                    <th>Action</th>
                                </tr>
                            </thead>
                            <tbody id="files-table-body"></tbody>
                        </table>
                    </div>
                </div>
            </div>

            <!-- ONGLET RESEAU -->
            <div id="tab-network" class="tab-content">
                <div class="card">
                    <h2>🌐 Gestion de la Topologie Réseau</h2>
                    <div class="table-container">
                        <table>
                            <thead>
                                <tr>
                                    <th>ID du Pair</th>
                                    <th>Adresse IP</th>
                                    <th>Dernière Vue</th>
                                    <th>Statut de Confiance</th>
                                    <th>Actions</th>
                                </tr>
                            </thead>
                            <tbody id="peers-table-body"></tbody>
                        </table>
                    </div>
                </div>
            </div>

        </div>
    </div>

    <script>
        let selectedPeer = null;
        let lastMsgCount = 0;
        let lastLogCount = 0;

        function switchTab(tabId, el) {
            document.querySelectorAll('.tab-content').forEach(t => t.classList.remove('active'));
            document.querySelectorAll('.sidebar-item').forEach(i => i.classList.remove('active'));
            document.getElementById('tab-' + tabId).classList.add('active');
            el.classList.add('active');
        }

        async function updateData() {
            try {
                const [sRes, mRes, pRes, fRes, lRes] = await Promise.all([
                    fetch('/api/status'), fetch('/api/messages'), fetch('/api/peers'), fetch('/api/files'), fetch('/api/logs')
                ]);
                
                const status = await sRes.json();
                const messages = await mRes.json();
                const peers = await pRes.json();
                const files = await fRes.json();
                const logs = await lRes.json();

                // Dashboard
                document.getElementById('node-id-display').innerText = status.id.substring(0,12) + "...";
                document.getElementById('uptime-display').innerText = "Uptime: " + status.uptime + "s";
                document.getElementById('stat-peers').innerText = status.peers_count;
                document.getElementById('stat-transfers').innerText = status.transfers_active;
                document.getElementById('stat-port').innerText = status.port_secure;
                document.getElementById('stat-ai').innerText = status.ai_enabled ? "ON" : "OFF";
                document.getElementById('stat-ai').style.color = status.ai_enabled ? "var(--success)" : "var(--danger)";

                // Logs
                if(logs.length !== lastLogCount) {
                    lastLogCount = logs.length;
                    const logArea = document.getElementById('logs-area');
                    logArea.innerHTML = logs.map(l => `
                        <div class="log-line">
                            <span class="log-time">[${new Date(l.time*1000).toLocaleTimeString()}]</span>
                            <span class="log-text">${l.text}</span>
                        </div>
                    `).reverse().join('');
                }

                // Chat Peer List
                const chatList = document.getElementById('chat-peer-list');
                const selectPeerFile = document.getElementById('file-target-peer');
                chatList.innerHTML = peers.map(p => `
                    <div class="chat-peer-item ${selectedPeer === p.id ? 'active' : ''}" onclick="selectChatPeer('${p.id}')">
                        <span style="font-weight:bold"><span class="peer-status"></span> ${p.id.substring(0,10)}...</span>
                        <span style="font-size:0.7rem; color:var(--text-muted)">${p.ip} ${p.trusted ? '🔒' : ''}</span>
                    </div>
                `).join('');
                
                if(selectPeerFile.innerHTML === "") {
                    selectPeerFile.innerHTML = '<option value="">Cible...</option>' + peers.map(p => `<option value="${p.id}">${p.id.substring(0,8)}...</option>`).join('');
                }

                // Messages Filtered by selected peer or AI
                if(selectedPeer && messages.length !== lastMsgCount) {
                    lastMsgCount = messages.length;
                    renderMessages(messages);
                }

                // Files Table
                const filesTable = document.getElementById('files-table-body');
                filesTable.innerHTML = files.map(f => `
                    <tr>
                        <td><b>${f.file_name}</b></td>
                        <td>${(f.file_size/1024).toFixed(1)} KB</td>
                        <td>${f.total_chunks}</td>
                        <td><span class="peer-status"></span> ${f.owner.substring(0,10)}...</td>
                        <td><button class="small" onclick="downloadFile('${f.offer_id}')">Télécharger</button></td>
                    </tr>
                `).join('');

                // Peers Table
                const peersTable = document.getElementById('peers-table-body');
                peersTable.innerHTML = peers.map(p => `
                    <tr>
                        <td><code>${p.id}</code></td>
                        <td>${p.ip}</td>
                        <td>${Math.round(Date.now()/1000 - p.last_seen)}s</td>
                        <td>${p.trusted ? '<b style="color:var(--success)">Fiable 🔒</b>' : '<b style="color:var(--text-muted)">Inconnu</b>'}</td>
                        <td>
                            ${p.trusted 
                                ? `<button class="danger" style="padding:5px 10px" onclick="setTrust('${p.id}', false)">Bannir</button>` 
                                : `<button style="padding:5px 10px" onclick="setTrust('${p.id}', true)">Fier</button>`}
                        </td>
                    </tr>
                `).join('');

            } catch(e) { console.error("Update error", e); }
        }

        function selectChatPeer(id) {
            selectedPeer = id;
            document.getElementById('chat-header').innerText = "Chat avec " + id.substring(0,15) + "...";
            lastMsgCount = 0; // Force re-render
            updateData();
        }

        function renderMessages(allMsgs) {
            const window = document.getElementById('chat-window');
            // On affiche les messages entre MOI et le peer selectionné, OU les messages de l'IA adressés à MOI
            const filtered = allMsgs.filter(m => 
                (m.from === selectedPeer) || 
                (m.to === selectedPeer) ||
                (m.from === 'GEMINI' && selectedPeer !== null) // AI responses visible in active chat
            );
            
            window.innerHTML = filtered.map(m => {
                let cls = "msg-theirs";
                let sender = m.from.substring(0,8);
                if(m.from === 'VOUS (IA)') { cls = "msg-mine"; sender = "MOI"; }
                if(m.from.startsWith("MOI ->")) { cls = "msg-mine"; sender = "MOI"; }
                if(m.from === 'GEMINI') { cls = "msg-ai"; sender = "🤖 GEMINI"; }

                return `
                    <div class="msg-bubble ${cls}">
                        <div style="font-size:0.7rem; margin-bottom:4px; font-weight:bold">${sender}</div>
                        ${m.text}
                        <div class="msg-meta">${new Date(m.time*1000).toLocaleTimeString()}</div>
                    </div>
                `;
            }).join('');
            window.scrollTop = window.scrollHeight;
        }

        async function sendChatMessage() {
            const input = document.getElementById('chat-input');
            const text = input.value.trim();
            if(!text || !selectedPeer) return;

            if(text.includes('@archipel-ai') || text.startsWith('/ask')) {
                await fetch('/api/ai', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({query: text})
                });
            } else {
                await fetch('/api/msg', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({to: selectedPeer, text: text})
                });
            }
            input.value = '';
            setTimeout(updateData, 500);
        }

        async function setTrust(id, trust) {
            await fetch((trust ? '/api/trust/' : '/api/untrust/') + id, {method: 'POST'});
            updateData();
        }

        async function downloadFile(id) {
            await fetch('/api/download/' + id, {method: 'POST'});
            alert("Téléchargement lancé.");
        }

        async function shareFile() {
            const input = document.getElementById('file-upload-input');
            const target = document.getElementById('file-target-peer').value;
            if(!input.files[0] || !target) return alert("Sélectionnez un fichier et un destinataire.");

            const formData = new FormData();
            formData.append('file', input.files[0]);
            formData.append('peer_id', target);
            
            const res = await fetch('/api/upload', {method: 'POST', body: formData});
            const data = await res.json();
            if(data.status === 'ok') alert("Offre envoyée !");
        }

        setInterval(updateData, 2000);
        updateData();
    </script>
</body>
</html>
"""

def start_web_server(node, port=5000):
    app = Flask(__name__)
    CORS(app)
    
    UPLOAD_FOLDER = 'data/uploads_web'
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

    @app.route('/')
    def index(): return render_template_string(HTML_TEMPLATE)

    @app.route('/api/status')
    def status(): return jsonify(node.get_status())

    @app.route('/api/peers')
    def peers():
        peers_list = node.table.list_peers()
        for p in peers_list: p['trusted'] = node.trust_store.is_trusted(p['id'])
        return jsonify(peers_list)

    @app.route('/api/messages')
    def messages(): return jsonify(node.messages)

    @app.route('/api/logs')
    def logs(): return jsonify(node.logs)

    @app.route('/api/files')
    def files(): return jsonify(node.transfer.list_remote_offers())

    @app.route('/api/trust/<peer_id>', methods=['POST'])
    def trust(peer_id):
        node.trust_store.set_trusted(peer_id, True)
        node.log(f"Confiance accordée à {peer_id[:10]}")
        return jsonify({"status": "ok"})

    @app.route('/api/untrust/<peer_id>', methods=['POST'])
    def untrust(peer_id):
        node.trust_store.set_trusted(peer_id, False)
        node.log(f"Confiance retirée pour {peer_id[:10]}")
        return jsonify({"status": "ok"})

    @app.route('/api/download/<offer_id>', methods=['POST'])
    def download(offer_id):
        try:
            node.transfer.request_download(offer_id)
            node.log(f"Début du téléchargement: {offer_id}")
            return jsonify({"status": "ok"})
        except Exception as e: return jsonify({"error": str(e)}), 400

    @app.route('/api/msg', methods=['POST'])
    def send_msg():
        data = request.json
        try:
            node.secure.send_secure_message(data['to'], data['text'])
            node.add_message(f"MOI -> {data['to'][:8]}", data['text'], target=data['to'])
            return jsonify({"status": "ok"})
        except Exception as e: return jsonify({"error": str(e)}), 400

    @app.route('/api/ai', methods=['POST'])
    def ai():
        data = request.json
        raw_query = data.get('query', '')
        query = raw_query.replace('@archipel-ai', '').replace('/ask', '').strip()
        node.add_message("VOUS (IA)", raw_query)
        response = node.gemini.query(query)
        node.add_message("GEMINI", response)
        return jsonify({"response": response})

    @app.route('/api/upload', methods=['POST'])
    def upload_file():
        file = request.files['file']
        peer_id = request.form.get('peer_id')
        if file and peer_id:
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            manifest = node.transfer.offer_file(peer_id, filepath)
            node.log(f"Fichier '{filename}' partagé avec {peer_id[:10]}")
            return jsonify({'status': 'ok'})
        return jsonify({'error': 'invalid'}), 400

    threading.Thread(target=lambda: app.run(port=port, debug=False, use_reloader=False), daemon=True).start()
    print(f"Interface Web active sur http://localhost:{port}")
