"""
Order Service - Demonstratie voor Instana vs OpenShift Monitoring
Bevat zowel automatische Instana instrumentatie als handmatige Prometheus metrics
"""
# Added for Instana because no (full) auto-discovery for this application or related services
import instana

from flask import Flask, request, jsonify
import requests
import psycopg2
import os
import time
import random
from datetime import datetime

# Prometheus metrics (voor OpenShift native monitoring)
from prometheus_client import Counter, Histogram, Gauge, generate_latest, REGISTRY
from prometheus_flask_exporter import PrometheusMetrics


app = Flask(__name__)

# Prometheus metrics setup
metrics = PrometheusMetrics(app)

# Custom Prometheus metrics
order_counter = Counter(
    'orders_total', 
    'Total number of orders',
    ['status', 'payment_status']
)
order_duration = Histogram(
    'order_processing_duration_seconds',
    'Time spent processing orders',
    buckets=[0.1, 0.5, 1.0, 2.0, 5.0]
)
active_orders = Gauge(
    'active_orders',
    'Number of currently processing orders'
)
database_errors = Counter(
    'database_errors_total',
    'Total database errors'
)

# Database configuratie
DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'postgres'),
    'port': os.getenv('DB_PORT', '5432'),
    'database': os.getenv('DB_NAME', 'orders'),
    'user': os.getenv('DB_USER', 'admin'),
    'password': os.getenv('DB_PASSWORD', 'password123')
}

PAYMENT_SERVICE_URL = os.getenv('PAYMENT_SERVICE_URL', 'http://payment-service:8080')

def get_db_connection():
    """Database connectie - Instana traceert dit automatisch!"""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        return conn
    except Exception as e:
        database_errors.inc()
        print(f"Database error: {e}")
        raise

def init_db():
    """Initialiseer database schema"""
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS orders (
                id SERIAL PRIMARY KEY,
                customer_name VARCHAR(255),
                product VARCHAR(255),
                amount DECIMAL(10, 2),
                status VARCHAR(50),
                payment_status VARCHAR(50),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()
        cur.close()
        conn.close()
        print("Database initialized")
    except Exception as e:
        print(f"Failed to initialize database: {e}")

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({"status": "healthy", "service": "order-service"}), 200

@app.route('/ready', methods=['GET'])
def ready():
    """Readiness check - controleert database connectie"""
    try:
        conn = get_db_connection()
        conn.close()
        return jsonify({"status": "ready"}), 200
    except:
        return jsonify({"status": "not ready"}), 503

@app.route('/orders', methods=['POST'])
def create_order():
    """
    Create nieuwe order
    Demonstreert:
    - Instana: automatische tracing van HTTP request, DB queries, external calls
    - Prometheus: handmatige metrics
    """
    active_orders.inc()
    start_time = time.time()
    
    try:
        data = request.get_json()
        
        # Validatie
        if not data or 'customer_name' not in data or 'product' not in data or 'amount' not in data:
            order_counter.labels(status='failed', payment_status='none').inc()
            active_orders.dec()
            return jsonify({"error": "Missing required fields"}), 400
        
        # Simuleer wat processing tijd
        processing_delay = random.uniform(0.05, 0.3)
        time.sleep(processing_delay)
        
        # Simuleer errors (10% van de tijd)
        if random.random() < 0.1:
            order_counter.labels(status='failed', payment_status='none').inc()
            active_orders.dec()
            return jsonify({"error": "Random error occurred"}), 500
        
        # Maak order in database
        # Instana traceert deze query automatisch!
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO orders (customer_name, product, amount, status, payment_status)
            VALUES (%s, %s, %s, %s, %s) RETURNING id
            """,
            (data['customer_name'], data['product'], data['amount'], 'pending', 'pending')
        )
        order_id = cur.fetchone()[0]
        conn.commit()
        
        # Call payment service
        # Instana traceert deze external call automatisch en maakt dependency map!
        try:
            payment_response = requests.post(
                f"{PAYMENT_SERVICE_URL}/payments",
                json={
                    "order_id": order_id,
                    "amount": data['amount'],
                    "customer": data['customer_name']
                },
                timeout=5
            )
            
            payment_status = 'completed' if payment_response.status_code == 200 else 'failed'
            
            # Update order status
            cur.execute(
                "UPDATE orders SET status = %s, payment_status = %s WHERE id = %s",
                ('completed' if payment_status == 'completed' else 'failed', payment_status, order_id)
            )
            conn.commit()
            
        except requests.exceptions.Timeout:
            payment_status = 'timeout'
            cur.execute(
                "UPDATE orders SET status = %s, payment_status = %s WHERE id = %s",
                ('failed', payment_status, order_id)
            )
            conn.commit()
        except Exception as e:
            print(f"Payment service error: {e}")
            payment_status = 'error'
        
        cur.close()
        conn.close()
        
        # Metrics
        duration = time.time() - start_time
        order_duration.observe(duration)
        order_counter.labels(
            status='completed' if payment_status == 'completed' else 'failed',
            payment_status=payment_status
        ).inc()
        active_orders.dec()
        
        return jsonify({
            "order_id": order_id,
            "status": "completed" if payment_status == 'completed' else 'failed',
            "payment_status": payment_status,
            "processing_time": duration
        }), 201 if payment_status == 'completed' else 500
        
    except Exception as e:
        active_orders.dec()
        order_counter.labels(status='error', payment_status='error').inc()
        print(f"Error creating order: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/orders', methods=['GET'])
def get_orders():
    """Haal alle orders op - demonstreert database query tracing"""
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Instana traceert deze query!
        cur.execute("SELECT * FROM orders ORDER BY created_at DESC LIMIT 100")
        orders = cur.fetchall()
        
        cur.close()
        conn.close()
        
        return jsonify({
            "orders": [
                {
                    "id": o[0],
                    "customer_name": o[1],
                    "product": o[2],
                    "amount": float(o[3]),
                    "status": o[4],
                    "payment_status": o[5],
                    "created_at": o[6].isoformat() if o[6] else None
                }
                for o in orders
            ]
        }), 200
        
    except Exception as e:
        database_errors.inc()
        return jsonify({"error": str(e)}), 500

@app.route('/orders/<int:order_id>', methods=['GET'])
def get_order(order_id):
    """Haal specifieke order op"""
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT * FROM orders WHERE id = %s", (order_id,))
        order = cur.fetchone()
        cur.close()
        conn.close()
        
        if not order:
            return jsonify({"error": "Order not found"}), 404
        
        return jsonify({
            "id": order[0],
            "customer_name": order[1],
            "product": order[2],
            "amount": float(order[3]),
            "status": order[4],
            "payment_status": order[5],
            "created_at": order[6].isoformat() if order[6] else None
        }), 200
        
    except Exception as e:
        database_errors.inc()
        return jsonify({"error": str(e)}), 500

@app.route('/metrics', methods=['GET'])
def metrics_endpoint():
    """Prometheus metrics endpoint - alleen voor OpenShift native monitoring"""
    return generate_latest(REGISTRY)

if __name__ == '__main__':
    init_db()
    # Instana agent detecteert deze Flask app automatisch!
    app.run(host='0.0.0.0', port=8080, debug=False)
