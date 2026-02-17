"""
Payment Service - Simuleerd payment processing
Demonstreert externe API calls en distributed tracing
"""
# Added for Instana because no (full) auto-discovery for this application or related services
import instana

from flask import Flask, request, jsonify
import time
import random
import requests
from prometheus_client import Counter, Histogram, generate_latest, REGISTRY
from prometheus_flask_exporter import PrometheusMetrics

app = Flask(__name__)
metrics = PrometheusMetrics(app)

# Prometheus metrics
payment_counter = Counter(
    'payments_total',
    'Total number of payment attempts',
    ['status']
)
payment_duration = Histogram(
    'payment_processing_duration_seconds',
    'Time spent processing payments',
    buckets=[0.1, 0.3, 0.5, 1.0, 2.0, 5.0]
)
external_api_calls = Counter(
    'external_api_calls_total',
    'External payment gateway calls',
    ['gateway', 'status']
)

@app.route('/health', methods=['GET'])
def health():
    return jsonify({"status": "healthy", "service": "payment-service"}), 200

@app.route('/payments', methods=['POST'])
def process_payment():
    """
    Process payment
    Demonstreert:
    - External API calls (naar fictieve payment gateway)
    - Variable latency
    - Error scenarios
    """
    start_time = time.time()
    
    try:
        data = request.get_json()
        
        if not data or 'order_id' not in data or 'amount' not in data:
            payment_counter.labels(status='invalid').inc()
            return jsonify({"error": "Missing required fields"}), 400
        
        # Simuleer payment processing tijd (variabel)
        processing_time = random.uniform(0.1, 0.8)
        time.sleep(processing_time)
        
        # Simuleer external payment gateway call
        # Instana traceert deze call en toont in dependency map!
        gateway_success = simulate_external_gateway(data['amount'])
        
        # Simuleer failures (15% van de tijd)
        if random.random() < 0.15 or not gateway_success:
            payment_counter.labels(status='failed').inc()
            duration = time.time() - start_time
            payment_duration.observe(duration)
            return jsonify({
                "status": "failed",
                "order_id": data['order_id'],
                "reason": "Payment gateway declined",
                "processing_time": duration
            }), 402
        
        # Success
        duration = time.time() - start_time
        payment_duration.observe(duration)
        payment_counter.labels(status='success').inc()
        
        return jsonify({
            "status": "completed",
            "order_id": data['order_id'],
            "transaction_id": f"TXN-{random.randint(100000, 999999)}",
            "processing_time": duration
        }), 200
        
    except Exception as e:
        payment_counter.labels(status='error').inc()
        return jsonify({"error": str(e)}), 500

def simulate_external_gateway(amount):
    """
    Simuleer call naar externe payment gateway
    Instana traceert externe HTTP calls automatisch!
    """
    try:
        # In een echte situatie zou dit een call zijn naar Stripe, Mollie, etc.
        # Voor demo: simuleer met random success/failure
        
        # Simuleer gateway latency
        time.sleep(random.uniform(0.05, 0.2))
        
        # 10% failure rate
        if random.random() < 0.1:
            external_api_calls.labels(gateway='stripe', status='failed').inc()
            return False
        
        external_api_calls.labels(gateway='stripe', status='success').inc()
        return True
        
    except Exception as e:
        external_api_calls.labels(gateway='stripe', status='error').inc()
        print(f"Gateway error: {e}")
        return False

@app.route('/payments/<string:transaction_id>', methods=['GET'])
def get_payment_status(transaction_id):
    """Check payment status"""
    # Simuleer lookup
    time.sleep(random.uniform(0.05, 0.15))
    
    return jsonify({
        "transaction_id": transaction_id,
        "status": "completed"
    }), 200

@app.route('/metrics', methods=['GET'])
def metrics_endpoint():
    """Prometheus metrics endpoint"""
    return generate_latest(REGISTRY)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=False)
