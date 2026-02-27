const API_BASE = "http://127.0.0.1:8000";

// --- Router ---
const router = {
    views: ['landing', 'login', 'signup', 'dashboard', 'face', 'book', 'register-face', 'admin', 'menu', 'navigation', 'flight'],
    currentView: 'landing',

    navigate(viewName) {
        document.querySelectorAll('.view').forEach(v => v.classList.remove('active'));
        const view = document.getElementById(`${viewName}-view`);
        if (view) {
            view.classList.add('active');
            this.currentView = viewName;
            this.onViewChange(viewName);
        }
        this.updateNav();
    },

    onViewChange(viewName) {
        if (viewName === 'dashboard') {
            loungeManager.fetchLounges();
            loungeManager.initSeatGrid();
        }
        if (viewName === 'menu') loungeManager.fetchMenu();
        if (viewName === 'navigation') loungeManager.initMapHotspots();

        if (viewName === 'face') cameraManager.init('webcam');
        else if (viewName === 'register-face') cameraManager.init('register-webcam');
        else cameraManager.stop();

        if (viewName === 'book') loungeManager.populateLoungeSelect();
        if (viewName === 'admin') adminManager.loadStats();
    },

    updateNav() {
        const nav = document.getElementById('nav-links');
        const token = localStorage.getItem('token');
        if (token) {
            const role = localStorage.getItem('role');
            let links = `<button onclick="router.navigate('dashboard')">Dashboard</button>`;
            if (role === 'admin') links += `<button onclick="router.navigate('admin')">Admin</button>`;
            links += `<button onclick="authManager.logout()">Logout</button>`;
            nav.innerHTML = links;
        } else {
            nav.innerHTML = `
                <button onclick="router.navigate('landing')">Home</button>
                <button onclick="router.navigate('login')">Login</button>
                <button onclick="router.navigate('signup')">Sign Up</button>
            `;
        }
    }
};

// --- Auth Manager ---
const authManager = {
    async login(username, password) {
        try {
            const response = await fetch(`${API_BASE}/auth/login`, {
                method: 'POST',
                body: new URLSearchParams({ username, password }),
            });
            const data = await response.json();
            if (response.ok) {
                localStorage.setItem('token', data.access_token);
                localStorage.setItem('role', data.role);
                localStorage.setItem('username', data.username);
                showNotification(`Welcome, ${data.username}! ✅`);
                router.navigate('dashboard');
            } else {
                showNotification(data.detail || "Login failed", 'error');
            }
        } catch (e) {
            showNotification('Server connection failed', 'error');
        }
    },

    async signup(username, password, role) {
        try {
            const response = await fetch(`${API_BASE}/auth/signup`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ username, password, role }),
            });
            const data = await response.json();
            if (response.ok) {
                showNotification('Account created! Login to continue.');
                router.navigate('login');
            } else {
                showNotification(data.detail || "Signup failed", 'error');
            }
        } catch (e) {
            showNotification('Server connection failed', 'error');
        }
    },

    logout() {
        localStorage.clear();
        router.navigate('landing');
        showNotification('Logged out successfully');
    }
};

// --- Camera Manager ---
const cameraManager = {
    stream: null,
    async init(videoId) {
        try {
            this.stream = await navigator.mediaDevices.getUserMedia({ video: true });
            const video = document.getElementById(videoId);
            if (video) video.srcObject = this.stream;
        } catch (e) {
            showNotification('Camera access denied', 'error');
        }
    },
    stop() {
        if (this.stream) {
            this.stream.getTracks().forEach(track => track.stop());
            this.stream = null;
        }
    },
    async capture(videoId) {
        const video = document.getElementById(videoId);
        const canvas = document.createElement('canvas');
        canvas.width = video.videoWidth;
        canvas.height = video.videoHeight;
        canvas.getContext('2d').drawImage(video, 0, 0);
        return canvas.toDataURL('image/jpeg');
    }
};

// --- Lounge Manager ---
const loungeManager = {
    lounges: [],

    async fetchLounges() {
        try {
            const response = await fetch(`${API_BASE}/lounges/`, {
                headers: { 'Authorization': `Bearer ${localStorage.getItem('token')}` }
            });
            this.lounges = await response.json();
            this.renderLounges();
            this.populateLoungeSelect();
        } catch (e) { }
    },

    renderLounges() {
        const list = document.getElementById('lounge-list');
        if (!list) return;
        list.innerHTML = this.lounges.map(l => `
            <div class="lounge-item glass-card" style="margin-bottom: 1rem; padding: 1.5rem; transform: none !important; border: 1px solid var(--glass-border);">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <div>
                        <h4 style="color: var(--accent-color);">${l.name}</h4>
                        <p style="font-size: 0.8rem; opacity: 0.7;">${l.airport}</p>
                    </div>
                    <div style="text-align: right;">
                        <span class="value">${l.occupancy}/${l.total_seats} Seats</span>
                        <div style="width: 120px; height: 6px; background: rgba(255,255,255,0.1); border-radius: 3px; margin-top: 5px; overflow:hidden;">
                            <div style="width: ${(l.occupancy / l.total_seats) * 100}%; height: 100%; background: var(--success); border-radius: 3px;"></div>
                        </div>
                    </div>
                </div>
            </div>
        `).join('');

        // Crowd Prediction Logic
        const totalOcc = this.lounges.reduce((acc, l) => acc + (l.occupancy / l.total_seats), 0) / (this.lounges.length || 1);
        const crowdEl = document.getElementById('crowd-level');
        if (crowdEl) {
            if (totalOcc < 0.4) { crowdEl.innerText = "Optimal"; crowdEl.style.color = "var(--success)"; }
            else if (totalOcc < 0.7) { crowdEl.innerText = "Moderate"; crowdEl.style.color = "var(--accent-color)"; }
            else { crowdEl.innerText = "Crowded"; crowdEl.style.color = "var(--error)"; }
        }
    },

    populateLoungeSelect() {
        const select = document.getElementById('book-lounge-id');
        if (!select) return;
        select.innerHTML = '<option value="">Select Lounge</option>' +
            this.lounges.map(l => `<option value="${l.id}">${l.name}</option>`).join('');
    },

    async fetchMenu() {
        const loungeId = 1;
        try {
            const response = await fetch(`${API_BASE}/lounges/menu/${loungeId}`, {
                headers: { 'Authorization': `Bearer ${localStorage.getItem('token')}` }
            });
            const menu = await response.json();
            const grid = document.getElementById('menu-items-grid');
            if (grid) {
                grid.innerHTML = menu.map(item => `
                    <div class="menu-item-card">
                        <img src="${item.image_url || 'https://via.placeholder.com/300x180'}" alt="${item.name}">
                        <div class="menu-item-info">
                            <div style="display: flex; justify-content: space-between;">
                                <h5>${item.name}</h5>
                                <span style="color: var(--accent-color); font-weight: 700;">$${item.price}</span>
                            </div>
                            <p style="font-size: 0.8rem; opacity: 0.7; margin: 5px 0 15px 0;">${item.description}</p>
                            <button onclick="loungeManager.placeOrder(${item.id})" class="btn-primary" style="width: 100%; font-size: 0.8rem; padding: 10px;">Pre-Order</button>
                        </div>
                    </div>
                `).join('');
            }
        } catch (e) { }
    },

    placeOrder(itemId) {
        showNotification("Dish Pre-Ordered! WhatsApp Confirmation Sent. 📲", "success");
    },

    async syncFlight() {
        const flightNum = document.getElementById('flight-input').value;
        if (!flightNum) return showNotification("Enter flight number", "error");

        try {
            const response = await fetch(`${API_BASE}/lounges/flight/${flightNum}`);
            const data = await response.json();
            document.getElementById('flight-result').style.display = 'block';
            document.getElementById('f-num').innerText = data.flight_number;
            document.getElementById('f-status').innerText = data.status;
            document.getElementById('f-dest').innerText = data.destination;
            document.getElementById('f-gate').innerText = data.gate;
            document.getElementById('f-time').innerText = new Date(data.departure_time).toLocaleTimeString();
            showNotification("Flight Linked! Status alerts active. ✈️", "success");
        } catch (e) { showNotification("Flight info unavailable", "error"); }
    },

    initOverstayTimer() {
        if (this.timerInterval) clearInterval(this.timerInterval);
        let seconds = 2 * 59 * 59;
        const timerEl = document.getElementById('stay-countdown');
        if (!timerEl) return;

        this.timerInterval = setInterval(() => {
            seconds--;
            if (seconds <= 0) {
                clearInterval(this.timerInterval);
                return;
            }
            const h = Math.floor(seconds / 3600).toString().padStart(2, '0');
            const m = Math.floor((seconds % 3600) / 60).toString().padStart(2, '0');
            const s = (seconds % 60).toString().padStart(2, '0');
            timerEl.innerText = `${h}:${m}:${s}`;

            if (seconds === 300) {
                showNotification("Lounge access expiring in 5 mins! Alert sent to WhatsApp.", "error");
            }
        }, 1000);

        this.initSeatGrid();
    },

    initSeatGrid() {
        // Phase 3: Smart Seat Detection (YOLO) Simulation
        const grid = document.getElementById('seat-grid');
        if (!grid) return;

        const seats = Array.from({ length: 15 }, (_, i) => ({
            id: i + 1,
            occupied: Math.random() > 0.6
        }));

        grid.innerHTML = seats.map(s => `
            <div class="seat ${s.occupied ? 'occupied' : 'free'}"
                 title="Seat ${s.id}: ${s.occupied ? 'Occupied (Detected)' : 'Available'}"
                 style="height: 30px; border-radius: 6px; background: ${s.occupied ? 'rgba(255,60,60,0.4)' : 'rgba(0,255,136,0.3)'}; border: 1px solid ${s.occupied ? 'var(--error)' : 'var(--success)'}; cursor: help;">
            </div>
        `).join('');
    },

    initMapHotspots() {
        // Phase 4: Indoor Navigation Interactivity
        const container = document.querySelector('.map-container');
        if (!container || container.querySelector('.hotspot')) return;

        const zones = [
            { name: "Spa & Massage", top: "20%", left: "30%" },
            { name: "Gourmet Buffet", top: "45%", left: "60%" },
            { name: "Resting Pods", top: "70%", left: "25%" },
            { name: "VVIP Cabin", top: "15%", left: "80%" }
        ];

        zones.forEach(z => {
            const el = document.createElement('div');
            el.className = 'hotspot';
            el.style.cssText = `position: absolute; top: ${z.top}; left: ${z.left}; width: 25px; height: 25px; background: var(--accent-color); border-radius: 50%; cursor: pointer; box-shadow: 0 0 15px var(--accent-color); animation: pulse 2s infinite;`;
            el.onclick = () => showNotification(`Navigating to: ${z.name}. Walking time: 2 mins.`, 'success');
            container.appendChild(el);
        });
    }
};

// --- Admin Manager ---
const adminManager = {
    async loadStats() {
        const token = localStorage.getItem('token');
        try {
            const resStats = await fetch(`${API_BASE}/admin/stats`, {
                headers: { 'Authorization': `Bearer ${token}` }
            });
            const stats = await resStats.json();
            document.getElementById('admin-total-users').innerText = stats.total_users;
            document.getElementById('admin-total-entries').innerText = stats.total_entries;
            document.getElementById('admin-total-revenue').innerText = `$${stats.revenue}`;

            const resLogs = await fetch(`${API_BASE}/admin/logs`, {
                headers: { 'Authorization': `Bearer ${token}` }
            });
            const logs = await resLogs.json();
            const list = document.getElementById('admin-logs-list');
            list.innerHTML = logs.map(log => `
                <div class="log-item" style="padding: 1rem; border-bottom: 1px solid var(--glass-border); font-size: 0.9rem;">
                    <div style="display:flex; justify-content:space-between;">
                         <strong>${log.username}</strong>
                         <span style="color: ${log.status.includes('Granted') ? 'var(--success)' : 'var(--error)'}">${log.status}</span>
                    </div>
                    <div style="color: var(--text-secondary); font-size: 0.8rem; margin-top:5px;">
                        Lounge ID: ${log.lounge} | ${new Date(log.timestamp).toLocaleString()}
                    </div>
                </div>
            `).join('');
        } catch (e) {
            showNotification("Admin sync failed", "error");
        }
    }
};

// --- Utils ---
function showNotification(msg, type = 'success') {
    const n = document.getElementById('notification');
    n.innerText = msg;
    n.className = `notification show ${type}`;
    setTimeout(() => n.classList.remove('show'), 3000);
}

// --- Form Listeners ---
document.getElementById('login-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    const [u, p] = e.target.querySelectorAll('input');
    await authManager.login(u.value, p.value);
});

document.getElementById('signup-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    const [u, p] = e.target.querySelectorAll('input');
    const r = document.getElementById('signup-role').value;
    await authManager.signup(u.value, p.value, r);
});

document.getElementById('book-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    const loungeId = document.getElementById('book-lounge-id').value;
    const inputs = e.target.querySelectorAll('input');
    const slot = inputs[0].value;
    const card = inputs[1].value;

    try {
        const response = await fetch(`${API_BASE}/lounges/book`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${localStorage.getItem('token')}`
            },
            body: JSON.stringify({ lounge_id: parseInt(loungeId), slot, card_number: card, expiry: '12/26', cvv: '123' })
        });
        if (response.ok) {
            showNotification("Booking Confirmed! QR Receipt sent to WhatsApp. 🎫", "success");
            router.navigate('dashboard');
        }
    } catch (e) { showNotification("Booking failed", "error"); }
});

document.getElementById('register-snap-btn').addEventListener('click', async () => {
    const imgData = await cameraManager.capture('register-webcam');
    try {
        const response = await fetch(`${API_BASE}/face/register`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${localStorage.getItem('token')}`
            },
            body: JSON.stringify({ image_data: imgData })
        });
        const data = await response.json();
        if (response.ok && data.success) {
            showNotification('Biometrics Enrolled Successfully! ✅', 'success');
            document.getElementById('register-status').innerText = 'Enrollment successful';
            document.getElementById('register-status').style.color = 'var(--success)';
            router.navigate('dashboard');
        } else {
            const msg = data.detail || 'Biometric enrollment failed';
            showNotification(msg, 'error');
            document.getElementById('register-status').innerText = msg;
            document.getElementById('register-status').style.color = 'var(--error)';
        }
    } catch (e) {
        showNotification('Biometric enrollment failed (network)', 'error');
    }
});

document.getElementById('snap-btn').addEventListener('click', async () => {
    const imgData = await cameraManager.capture('webcam');
    const statusEl = document.getElementById('scan-status');
    statusEl.innerText = 'Authenticating Biometrics...';
    try {
        const response = await fetch(`${API_BASE}/face/verify-entry/1`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${localStorage.getItem('token')}`
            },
            body: JSON.stringify({ image_data: imgData })
        });
        const data = await response.json();
        if (data.access) {
            statusEl.innerText = 'ACCESS GRANTED';
            statusEl.style.color = 'var(--success)';
            showNotification('Welcome to the lounge! ✅', 'success');
            loungeManager.initOverstayTimer();
        } else {
            const msg = data.reason || 'Verification Error';
            statusEl.innerText = 'DENIED: ' + msg;
            statusEl.style.color = 'var(--error)';
            showNotification(msg, 'error');
        }
    } catch (e) {
        // Fallback for demo
        statusEl.innerText = 'ACCESS GRANTED (Simulated)';
        statusEl.style.color = 'var(--success)';
        loungeManager.initOverstayTimer();
    }
});

// --- 3D Interactions ---
const ui3d = {
    init() {
        const toggle = document.getElementById('lamp-toggle');
        if (toggle) {
            toggle.addEventListener('click', () => {
                toggle.classList.add('active');
                setTimeout(() => toggle.classList.remove('active'), 200);
                document.body.classList.toggle('lights-off');
            });
        }

        document.addEventListener('mousemove', (e) => {
            const cards = document.querySelectorAll('.glass-card');
            const x = (window.innerWidth / 2 - e.pageX) / 60;
            const y = (window.innerHeight / 2 - e.pageY) / 60;
            cards.forEach(card => {
                card.style.transform = `rotateY(${x}deg) rotateX(${y}deg)`;
            });
        });
    }
};

// Init
router.updateNav();
router.navigate('landing');
ui3d.init();
