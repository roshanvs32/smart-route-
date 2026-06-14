from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import math
import random
import json
from itertools import permutations

app = Flask(__name__)
CORS(app)

# --- Haversine distance (km) ---
def haversine(lat1, lon1, lat2, lon2):
    R = 6371
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dlambda/2)**2
    return 2 * R * math.asin(math.sqrt(a))

# --- Nearest Neighbour heuristic TSP ---
def nearest_neighbour_tsp(nodes):
    """nodes: list of dicts with id, name, lat, lon. First node is depot."""
    if len(nodes) <= 1:
        return nodes, 0
    n = len(nodes)
    visited = [False] * n
    route = [0]
    visited[0] = True
    total_dist = 0
    for _ in range(n - 1):
        last = route[-1]
        best_dist = float('inf')
        best_next = -1
        for j in range(n):
            if not visited[j]:
                d = haversine(nodes[last]['lat'], nodes[last]['lon'],
                              nodes[j]['lat'], nodes[j]['lon'])
                if d < best_dist:
                    best_dist = d
                    best_next = j
        route.append(best_next)
        visited[best_next] = True
        total_dist += best_dist
    # return to depot
    total_dist += haversine(nodes[route[-1]]['lat'], nodes[route[-1]]['lon'],
                            nodes[0]['lat'], nodes[0]['lon'])
    route.append(0)
    return [nodes[i] for i in route], round(total_dist, 2)

# --- 2-opt improvement ---
def two_opt(nodes, route_indices):
    """Improve TSP route with 2-opt swaps."""
    n = len(route_indices)
    improved = True
    best = route_indices[:]
    best_dist = route_distance(nodes, best)
    while improved:
        improved = False
        for i in range(1, n - 2):
            for j in range(i + 1, n - 1):
                new_route = best[:i] + best[i:j+1][::-1] + best[j+1:]
                new_dist = route_distance(nodes, new_route)
                if new_dist < best_dist - 1e-10:
                    best = new_route
                    best_dist = new_dist
                    improved = True
    return best, round(best_dist, 2)

def route_distance(nodes, indices):
    total = 0
    for i in range(len(indices) - 1):
        a, b = nodes[indices[i]], nodes[indices[i+1]]
        total += haversine(a['lat'], a['lon'], b['lat'], b['lon'])
    return total

# --- Emissions calculation ---
def calc_emissions(distance_km, vehicle_type):
    factors = {
        'petrol_van': 0.21,    # kg CO2 per km
        'diesel_truck': 0.27,
        'ev_van': 0.05,
        'motorcycle': 0.10,
        'bicycle': 0.0,
    }
    return round(distance_km * factors.get(vehicle_type, 0.21), 2)

# --- Cost calculation ---
def calc_cost(distance_km, vehicle_type, num_stops):
    rates = {
        'petrol_van': 8,    # INR per km
        'diesel_truck': 12,
        'ev_van': 4,
        'motorcycle': 4,
        'bicycle': 1,
    }
    base = distance_km * rates.get(vehicle_type, 8)
    stop_cost = num_stops * 15  # handling cost per stop
    return round(base + stop_cost, 2)

# --- Estimated time ---
def calc_time(distance_km, vehicle_type, num_stops):
    speeds = {
        'petrol_van': 40,
        'diesel_truck': 35,
        'ev_van': 40,
        'motorcycle': 45,
        'bicycle': 15,
    }
    speed = speeds.get(vehicle_type, 40)
    drive_time = distance_km / speed * 60  # minutes
    stop_time = num_stops * 8  # 8 minutes per stop
    return round(drive_time + stop_time, 1)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/optimize', methods=['POST'])
def optimize():
    data = request.json
    stops = data.get('stops', [])
    vehicle = data.get('vehicle', 'petrol_van')
    optimize_for = data.get('optimize_for', 'distance')  # distance | cost | emissions

    if len(stops) < 2:
        return jsonify({'error': 'Need at least 2 stops (depot + 1 delivery)'}), 400

    # Validate
    for s in stops:
        if not all(k in s for k in ['lat', 'lon', 'name']):
            return jsonify({'error': f'Stop missing lat/lon/name: {s}'}), 400

    # Add ids
    for i, s in enumerate(stops):
        s['id'] = i

    # Nearest neighbour to get initial route
    nn_route, nn_dist = nearest_neighbour_tsp(stops)

    # 2-opt on the NN route (excluding the last duplicate depot)
    indices = [stops.index(n) for n in nn_route[:-1]]
    try:
        opt_indices, opt_dist = two_opt(stops, indices)
    except Exception:
        opt_indices = indices
        opt_dist = nn_dist

    # Add depot at end
    opt_indices_full = opt_indices + [0]
    opt_route = [stops[i] for i in opt_indices_full]

    # Metrics
    num_deliveries = len(stops) - 1
    emissions = calc_emissions(opt_dist, vehicle)
    cost = calc_cost(opt_dist, vehicle, num_deliveries)
    time_min = calc_time(opt_dist, vehicle, num_deliveries)

    # Naive (original order) for comparison
    naive_order = list(range(len(stops))) + [0]
    naive_dist = round(route_distance(stops, naive_order), 2)
    naive_emissions = calc_emissions(naive_dist, vehicle)
    naive_cost = calc_cost(naive_dist, vehicle, num_deliveries)

    # Segment breakdown
    segments = []
    for i in range(len(opt_route) - 1):
        a, b = opt_route[i], opt_route[i+1]
        d = haversine(a['lat'], a['lon'], b['lat'], b['lon'])
        segments.append({
            'from': a['name'],
            'to': b['name'],
            'distance_km': round(d, 2),
            'from_coords': [a['lat'], a['lon']],
            'to_coords': [b['lat'], b['lon']],
        })

    return jsonify({
        'optimized_route': opt_route,
        'segments': segments,
        'metrics': {
            'total_distance_km': opt_dist,
            'total_cost_inr': cost,
            'co2_emissions_kg': emissions,
            'estimated_time_min': time_min,
            'num_stops': num_deliveries,
        },
        'comparison': {
            'naive_distance_km': naive_dist,
            'naive_cost_inr': naive_cost,
            'naive_emissions_kg': naive_emissions,
            'saved_distance_km': round(naive_dist - opt_dist, 2),
            'saved_cost_inr': round(naive_cost - cost, 2),
            'saved_emissions_kg': round(naive_emissions - emissions, 2),
            'improvement_pct': round((naive_dist - opt_dist) / naive_dist * 100, 1) if naive_dist > 0 else 0,
        },
        'vehicle': vehicle,
    })

@app.route('/api/demo', methods=['GET'])
def demo():
    """Return a preset demo scenario around Mumbai."""
    scenario = {
        'stops': [
            {'name': 'Warehouse (Andheri)', 'lat': 19.1136, 'lon': 72.8697},
            {'name': 'Bandra Kurla Complex', 'lat': 19.0596, 'lon': 72.8656},
            {'name': 'Colaba', 'lat': 18.9067, 'lon': 72.8147},
            {'name': 'Dadar Market', 'lat': 19.0178, 'lon': 72.8478},
            {'name': 'Ghatkopar East', 'lat': 19.0864, 'lon': 72.9081},
            {'name': 'Thane City', 'lat': 19.2183, 'lon': 72.9781},
            {'name': 'Mulund West', 'lat': 19.1726, 'lon': 72.9561},
        ],
        'vehicle': 'ev_van',
        'optimize_for': 'emissions',
    }
    return jsonify(scenario)

@app.route('/api/demo_scenarios', methods=['GET'])
def demo_scenarios():
    return jsonify([
        {
            'name': '🏙️ Mumbai Metro Deliveries',
            'description': '7 stops across Mumbai — warehouse in Andheri',
            'vehicle': 'ev_van',
            'stops': [
                {'name': 'Warehouse (Andheri)', 'lat': 19.1136, 'lon': 72.8697},
                {'name': 'Bandra Kurla Complex', 'lat': 19.0596, 'lon': 72.8656},
                {'name': 'Colaba Market', 'lat': 18.9067, 'lon': 72.8147},
                {'name': 'Dadar Phule Market', 'lat': 19.0178, 'lon': 72.8478},
                {'name': 'Ghatkopar East', 'lat': 19.0864, 'lon': 72.9081},
                {'name': 'Thane City Centre', 'lat': 19.2183, 'lon': 72.9781},
                {'name': 'Mulund West', 'lat': 19.1726, 'lon': 72.9561},
            ],
        },
        {
            'name': '🌿 Bengaluru Last-Mile',
            'description': '6 stops in Bengaluru — eco delivery by EV',
            'vehicle': 'ev_van',
            'stops': [
                {'name': 'Hub (Peenya Industrial)', 'lat': 13.0284, 'lon': 77.5147},
                {'name': 'Malleshwaram', 'lat': 13.0034, 'lon': 77.5684},
                {'name': 'Indiranagar', 'lat': 12.9784, 'lon': 77.6408},
                {'name': 'Koramangala', 'lat': 12.9352, 'lon': 77.6245},
                {'name': 'Whitefield', 'lat': 12.9698, 'lon': 77.7500},
                {'name': 'Electronic City', 'lat': 12.8399, 'lon': 77.6770},
            ],
        },
        {
            'name': '📦 Delhi NCR Express',
            'description': '8 stops across Delhi NCR — diesel truck',
            'vehicle': 'diesel_truck',
            'stops': [
                {'name': 'Depot (Okhla Phase II)', 'lat': 28.5355, 'lon': 77.2666},
                {'name': 'Connaught Place', 'lat': 28.6315, 'lon': 77.2167},
                {'name': 'Karol Bagh', 'lat': 28.6520, 'lon': 77.1908},
                {'name': 'Laxmi Nagar', 'lat': 28.6317, 'lon': 77.2768},
                {'name': 'Noida Sector 18', 'lat': 28.5696, 'lon': 77.3218},
                {'name': 'Gurugram Cyber City', 'lat': 28.4950, 'lon': 77.0878},
                {'name': 'Dwarka Sector 12', 'lat': 28.5921, 'lon': 77.0460},
                {'name': 'Rohini Sector 3', 'lat': 28.7229, 'lon': 77.1096},
            ],
        },
    ])

if __name__ == '__main__':
    app.run(debug=True, port=5000)
