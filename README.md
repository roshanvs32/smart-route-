# SmartRoute — AI-Powered Logistics Route Optimizer

> **FAR AWAY Hackathon 2026** — Theme: Logistics & Transit

## 🚀 What It Does

SmartRoute is a full-stack web application that uses AI optimization algorithms to:
- **Minimize delivery route distance** (2-opt TSP algorithm)
- **Reduce CO₂ emissions** by picking efficient paths and eco-friendly vehicles
- **Cut operational costs** with smart routing vs naive ordering
- **Visualize routes** on an interactive dark-mode map

Designed for last-mile delivery companies, e-commerce logistics, and municipal transit planning.

---

## 🧠 How the AI Works

1. **Nearest Neighbour Heuristic** — builds an initial route greedily
2. **2-opt Local Search** — iteratively swaps route segments to find shorter paths
3. **Multi-metric scoring** — compares naive vs optimized route on distance, cost, and CO₂
4. **Vehicle-aware costing** — different emission factors and rates per vehicle type

---

## 🌍 Real-World Impact

| Metric | Example (Mumbai, 7 stops) |
|---|---|
| Distance saved | ~12–25 km |
| Cost saved | ₹100–300 per run |
| CO₂ reduced | 2–5 kg per run |
| Time saved | 15–30 minutes |

At scale (1000 deliveries/day), this is **tons of CO₂ saved annually**.

---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| Backend | Python 3.11, Flask |
| Optimization | OR-Tools (Google), 2-opt TSP |
| Frontend | Vanilla JS, Leaflet.js |
| Maps | OpenStreetMap + CartoCDN |
| Distance | Haversine formula |

---

## 📦 Setup & Run

```bash
# 1. Clone / unzip project
cd smartroute

# 2. Install dependencies
pip install -r requirements.txt

# 3. Run
python app.py

# 4. Open browser
# http://localhost:5000
```

---

## 📁 Project Structure

```
smartroute/
├── app.py                  # Flask backend + optimization logic
├── requirements.txt        # Python dependencies
├── README.md
└── templates/
    └── index.html          # Full frontend (map + UI)
```

---

## 🎯 Features

- **3 preset city scenarios** — Mumbai, Bengaluru, Delhi NCR
- **Click-to-add stops** on the map
- **4 vehicle types** — EV Van, Petrol Van, Diesel Truck, Motorcycle
- **Savings dashboard** — shows exactly how much was saved vs naive routing
- **Route visualization** — animated path with per-segment distances
- **Responsive, dark-mode UI**

---

## 🔮 Future Roadmap (Round 2)

- Real-time traffic integration (Google Maps API)
- Multi-vehicle fleet optimization (VRP with capacity constraints)
- Time-window constraints per delivery
- Driver mobile app with turn-by-turn navigation
- ML model to predict optimal delivery windows based on historical data
- Integration with ERP/WMS systems

---

## 📊 Algorithm Complexity

- Nearest Neighbour: O(n²)
- 2-opt: O(n²) per iteration, typically converges in O(n) iterations
- Total: O(n³) worst case, fast in practice for n < 50 stops

---

## 👤 Team

Built for FAR AWAY 2026 Hackathon — India's Biggest International Hackathon.

Theme: **Logistics & Transit** — Transform how goods and services move through smarter solutions.
