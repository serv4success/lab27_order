"""
Frontend Service - Entry point voor de applicatie
Demonstreert end-to-end tracing door meerdere services
"""
from flask import Flask, request, jsonify, render_template_string
import requests
import os
import time
import random
from prometheus_client import Counter, Histogram, generate_latest, REGISTRY
from prometheus_flask_exporter import PrometheusMetrics

app = Flask(__name__)
metrics = PrometheusMetrics(app)

ORDER_SERVICE_URL = os.getenv('ORDER_SERVICE_URL', 'http://order-service:8080')

# Prometheus metrics
request_counter = Counter(
    'frontend_requests_total',
    'Total frontend requests',
    ['endpoint', 'method', 'status']
)
request_duration = Histogram(
    'frontend_request_duration_seconds',
    'Frontend request duration',
    buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0]
)

# Simple HTML template voor demo
HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Instana Demo - Order System</title>
    <style>
        body { 
            font-family: Arial, sans-serif; 
            max-width: 800px; 
            margin: 50px auto; 
            padding: 20px;
            background: #f5f5f5;
        }
        .container {
            background: white;
            padding: 30px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        h1 { color: #333; }
        .form-group {
            margin-bottom: 15px;
        }
        label {
            display: block;
            margin-bottom: 5px;
            font-weight: bold;
        }
        input {
            width: 100%;
            padding: 8px;
            border: 1px solid #ddd;
            border-radius: 4px;
        }
        button {
            background: #007bff;
            color: white;
            padding: 10px 20px;
            border: none;
            border-radius: 4px;
            cursor: pointer;
        }
        button:hover {
            background: #0056b3;
        }
        .result {
            margin-top: 20px;
            padding: 15px;
            background: #e7f3ff;
            border-radius: 4px;
            display: none;
        }
        .error {
            background: #ffe7e7;
            color: #d00;
        }
        .monitoring-info {
            margin-top: 30px;
            padding: 15px;
            background: #f0f0f0;
            border-radius: 4px;
            font-size: 0.9em;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🛍️ Instana Demo - Order System</h1>
        <p>This application shows observability with <strong>Instana</strong> vs <strong>OpenShift Native</strong></p>
        
        <form id="orderForm">
            <div class="form-group">
                <label>Customer Name:</label>
                <input type="text" id="customer_name" required>
            </div>
            <div class="form-group">
                <label>Product:</label>
                <input type="text" id="product" required>
            </div>
            <div class="form-group">
                <label>Amount (€):</label>
                <input type="number" id="amount" step="0.01" required>
            </div>
            <button type="submit">Place Order</button>
        </form>
        
        <div id="result" class="result"></div>
        
        <div class="monitoring-info">
            <h3>📊 Monitoring Details:</h3>
            <ul>
                <li><strong>Instana:</strong> Automatische tracing, dependency mapping, geen code wijzigingen nodig</li>
                <li><strong>OpenShift:</strong> Handmatige metrics, zie /metrics endpoint</li>
                <li><strong>Services:</strong> Frontend → Order Service → Payment Service → Database</li>
            </ul>
            <p><a href="/orders">View all orders</a> | <a href="/metrics">Prometheus metrics</a></p>
        </div>
    </div>
    
    <script>
        document.getElementById('orderForm').addEventListener('submit', async (e) => {
            e.preventDefault();
            
            const resultDiv = document.getElementById('result');
            resultDiv.style.display = 'block';
            resultDiv.className = 'result';
            resultDiv.innerHTML = 'Processing order...';
            
            const data = {
                customer_name: document.getElementById('customer_name').value,
                product: document.getElementById('product').value,
                amount: parseFloat(document.getElementById('amount').value)
            };
            
            try {
                const response = await fetch('/api/orders', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify(data)
                });
                
                const result = await response.json();
                
                if (response.ok) {
                    resultDiv.innerHTML = `
                        ✅ <strong>Order created successfully!</strong><br>
                        Order ID: ${result.order_id}<br>
                        Status: ${result.status}<br>
                        Payment: ${result.payment_status}<br>
                        Processing time: ${result.processing_time.toFixed(3)}s
                    `;
                } else {
                    resultDiv.className = 'result error';
                    resultDiv.innerHTML = `❌ <strong>Order failed:</strong> ${result.error || 'Unknown error'}`;
                }
            } catch (error) {
                resultDiv.className = 'result error';
                resultDiv.innerHTML = `❌ <strong>Error:</strong> ${error.message}`;
            }
        });
    </script>
</body>
</html>
"""

@app.route('/', methods=['GET'])
def index():
    """Serve simple web interface"""
    return render_template_string(HTML_TEMPLATE)

@app.route('/health', methods=['GET'])
def health():
    return jsonify({"status": "healthy", "service": "frontend"}), 200

@app.route('/api/orders', methods=['POST'])
def create_order_api():
    """
    Frontend API endpoint - routes naar order service
    Instana traceert deze hele chain automatisch:
    Frontend → Order Service → Payment Service → Database
    """
    start_time = time.time()
    
    try:
        data = request.get_json()
        
        # Call order service
        # Instana creëert automatisch distributed trace!
        response = requests.post(
            f"{ORDER_SERVICE_URL}/orders",
            json=data,
            timeout=10
        )
        
        duration = time.time() - start_time
        request_duration.observe(duration)
        
        status_label = 'success' if response.status_code < 400 else 'error'
        request_counter.labels(
            endpoint='/api/orders',
            method='POST',
            status=status_label
        ).inc()
        
        return response.json(), response.status_code
        
    except requests.exceptions.Timeout:
        request_counter.labels(endpoint='/api/orders', method='POST', status='timeout').inc()
        return jsonify({"error": "Order service timeout"}), 504
    except Exception as e:
        request_counter.labels(endpoint='/api/orders', method='POST', status='error').inc()
        return jsonify({"error": str(e)}), 500

@app.route('/orders', methods=['GET'])
def get_orders():
    """Haal alle orders op via order service"""
    try:
        response = requests.get(f"{ORDER_SERVICE_URL}/orders", timeout=10)
        
        if response.status_code == 200:
            orders = response.json().get('orders', [])
            
            # Render simple HTML table
            html = """
            <html>
            <head>
                <title>All Orders</title>
                <style>
                    body { font-family: Arial; max-width: 1200px; margin: 20px auto; padding: 20px; }
                    table { width: 100%; border-collapse: collapse; }
                    th, td { padding: 10px; text-align: left; border-bottom: 1px solid #ddd; }
                    th { background: #007bff; color: white; }
                    .completed { color: green; }
                    .failed { color: red; }
                    a { color: #007bff; }
                </style>
            </head>
            <body>
                <h1>All Orders</h1>
                <p><a href="/">← Back to home</a></p>
                <table>
                    <tr>
                        <th>ID</th>
                        <th>Customer</th>
                        <th>Product</th>
                        <th>Amount</th>
                        <th>Status</th>
                        <th>Payment</th>
                        <th>Created</th>
                    </tr>
            """
            
            for order in orders:
                status_class = 'completed' if order['status'] == 'completed' else 'failed'
                html += f"""
                    <tr>
                        <td>{order['id']}</td>
                        <td>{order['customer_name']}</td>
                        <td>{order['product']}</td>
                        <td>€{order['amount']:.2f}</td>
                        <td class="{status_class}">{order['status']}</td>
                        <td class="{status_class}">{order['payment_status']}</td>
                        <td>{order['created_at']}</td>
                    </tr>
                """
            
            html += """
                </table>
            </body>
            </html>
            """
            
            return html
        else:
            return f"Error fetching orders: {response.text}", response.status_code
            
    except Exception as e:
        return f"Error: {str(e)}", 500

@app.route('/metrics', methods=['GET'])
def metrics_endpoint():
    """Prometheus metrics endpoint"""
    return generate_latest(REGISTRY)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=3000, debug=False)
