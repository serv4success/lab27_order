# Instana vs OpenShift Native Monitoring - Demo

Deze demo laat het verschil zien tussen **Instana** (IBM's APM platform) en **OpenShift Native Monitoring** (Prometheus + Grafana).

## 📋 Overzicht

### Applicatie Architectuur
```
┌─────────────┐
│  Frontend   │ (Python Flask)
│  Port 3000  │
└──────┬──────┘
       │
       ▼
┌─────────────────┐      ┌──────────────────┐
│  Order Service  │─────▶│ Payment Service  │
│    Port 8080    │      │    Port 8080     │
└────────┬────────┘      └──────────────────┘
         │
         ▼
    ┌──────────┐
    │PostgreSQL│
    │ Port 5432│
    └──────────┘
```

### Services
- **Frontend**: Web interface voor orders plaatsen
- **Order Service**: Verwerkt orders, communiceert met database en payment service
- **Payment Service**: Simuleert payment processing
- **PostgreSQL**: Database voor order opslag

## 🎯 Demo Doelen

Deze demo laat zien:

### Instana Voordelen
✅ **Automatische instrumentatie** - Geen code wijzigingen nodig
✅ **End-to-end tracing** - Volledige request flow door alle services
✅ **Dependency mapping** - Automatische visualisatie van service dependencies
✅ **AI-powered analysis** - Automatische root cause analysis
✅ **Instant setup** - Agent installeren en klaar (< 5 minuten)

### OpenShift Native
⚙️ **Handmatige setup** - Metrics moeten handmatig worden toegevoegd
⚙️ **Geen auto-tracing** - Distributed tracing vereist Jaeger setup
⚙️ **Handmatige correlatie** - Logs, metrics en traces zijn gescheiden
⚙️ **Setup tijd** - 30-60 minuten configuratie

## 🚀 Quick Start

### Vereisten
- OpenShift 4.12+ cluster (of gebruik CodeReady Containers voor lokaal)
- `oc` CLI geïnstalleerd en ingelogd
- Docker of Podman
- Python 3.9+
- Instana account (trial: https://www.instana.com/trial/)

### Stap 1: Clone en Deploy

```bash
# Clone deze repository
cd demo-instana

# Login op OpenShift
oc login --web

# Deploy applicatie 
-> to avoid problems with docker builds on my MACOS ARM for the AMD target patform, I build the images on openshift (S2I) and pushed them in the local registry
-> for the progres database, I created a working deployment taking into account security context of openshift 


chmod +x scripts/deploy.sh
./scripts/deploy.sh
```

Het script vraagt om je image registry (bijv. `quay.io/username`).

### Stap 2: Instana Agent Installeren

```bash
# Edit het bestand met je Instana credentials
vim k8s/05-instana-agent.yaml

# Vervang:
# - VERVANG_MET_JE_INSTANA_AGENT_KEY
# - VERVANG_MET_JE_DOWNLOAD_KEY

# Deploy Instana agent
oc apply -f k8s/05-instana-agent.yaml

# Check status
oc get pods -n instana-agent
```

**Instana credentials vind je:**
1. Login op Instana: https://instana.io
2. Settings → Team Settings → Agent Keys

### Stap 3: Verificatie

```bash
# Check of alle services draaien
oc get pods -n demo-instana

# Haal frontend URL op
oc get route frontend -n demo-instana

# Open in browser
https://frontend-demo-instana.apps.ocp02.llab27.be

## 📊 Demo Scenario's

### Scenario 1: Basis Monitoring Vergelijking

#### OpenShift Native
```bash
# Bekijk Prometheus metrics
oc port-forward -n demo-instana svc/frontend 3000:80
# Open http://localhost:3000/metrics

# Bekijk OpenShift monitoring
# OpenShift Console → Monitoring → Metrics
```

**Wat zie je:**
- Raw Prometheus metrics
- Handmatig queries schrijven nodig
- Geen automatic correlation
- Basic CPU/Memory grafieken

#### Instana
```bash
# Open Instana dashboard
# Login op https://instana.io
```

**Wat zie je:**
- Automatische service discovery
- Live dependency map
- Golden signals (latency, traffic, errors, saturation)
- Request flow visualization

### Scenario 2: Load Testing

```bash
# Installeer dependencies
cd /Users/dannyroefflaer/Git/serv4success/lab27_order
pip3 install -r scripts/requirements.txt

# Run mixed load scenario (10 minuten)
cd /Users/dannyroefflaer/Git/serv4success/lab27_order
python3 scripts/load-generator.py \
  --url https://frontend-demo-instana.apps.ocp02.llab27.be \
  --scenario mixed \
  --duration 10

# Of run spike traffic (2 minuten)
python3 scripts/load-generator.py \
  --url https://frontend-demo-instana.apps.ocp02.llab27.be \
  --scenario spike \
  --duration 2 \
  --concurrency 25
```

**Vergelijk:**

| Feature | Instana | OpenShift Native |
|---------|---------|------------------|
| **Latency spikes detecteren** | Automatisch gemarkeerd in timeline | Handmatig query schrijven |
| **Error correlation** | Automatisch linked naar traces | Handmatig logs correleren |
| **Impact analysis** | Toont welke services affected zijn | Niet beschikbaar |
| **Root cause** | AI suggests waarschijnlijke oorzaak | Handmatige analyse |

### Scenario 3: Distributed Tracing

**Test een order flow:**
```bash
# Maak een order via UI of API
curl -X POST https://frontend-demo-instana.apps.ocp02.llab27.be>/api/orders \
  -H "Content-Type: application/json" \
  -d '{
    "customer_name": "Jan de Vries",
    "product": "MacBook Pro",
    "amount": 1499.99
  }'
```

#### In Instana:
1. Ga naar **Analytics** → **Calls**
2. Filter op `service.name:frontend`
3. Klik op een trace
4. Zie complete flow:
   - Frontend → Order Service → Payment Service
   - Database queries
   - Latency per hop
   - Error details (als applicable)

#### In OpenShift:
1. Prometheus metrics tonen alleen aggregated data
2. Voor tracing moet je Jaeger handmatig installeren:
```bash
# Niet included in deze demo, maar zou extra setup vereisen:
# - Jaeger Operator installeren
# - Applications instrumenteren met OpenTelemetry
# - Jaeger collector configureren
# - 30-60 minuten werk
```

### Scenario 4: Error Debugging

**Simuleer errors:**
```bash
# Run error scenario
python3 scripts/load-generator.py \
  --url https://frontend-demo-instana.apps.ocp02.llab27.be \
  --scenario error \
  --duration 3
```

#### OpenShift Native Approach:
```bash
# Check Prometheus alerts
oc get prometheusrule -n demo-instana

# View logs manually
oc logs -n demo-instana -l app=order-service --tail=100

# Check metrics
# Moet handmatig correleren tussen:
# - Logs
# - Metrics
# - Events
```

#### Instana Approach:
1. Open Instana → **Events**
2. Zie automatisch gegenereerde incidents
3. Klik op incident voor:
   - Root cause suggestion
   - Affected services
   - Related traces
   - Timeline van events

### Scenario 5: Database Performance

**Check database queries:**

#### OpenShift Native:
```bash
# PostgreSQL queries zijn niet zichtbaar tenzij:
# - Handmatig logging enabled
# - Query metrics geëxporteerd
# - Extra tooling (pg_stat_statements)
```

#### Instana:
- Automatisch alle queries getraceerd
- Slow query detection
- Query parameters zichtbaar
- Execution time per query

## 📈 Demo Presentatie Outline

### Slide 1: Setup Comparison
```
Instana Setup:
└─ Agent installeren (5 min)
└─ Klaar! ✓

OpenShift Native Setup:
├─ Prometheus metrics toevoegen aan code
├─ ServiceMonitors configureren
├─ Alert rules schrijven
├─ Grafana dashboards bouwen
├─ (Optioneel) Jaeger installeren voor tracing
└─ 30-60 minuten ⏱️
```

### Slide 2: Feature Comparison

| Feature | Instana | OpenShift Native |
|---------|---------|------------------|
| Auto-discovery | ✅ Automatisch | ❌ Handmatig |
| Distributed Tracing | ✅ Out-of-box | ⚠️ Vereist Jaeger |
| Code changes | ✅ Geen | ❌ Metrics library |
| Dependency Map | ✅ Real-time | ❌ Niet beschikbaar |
| Root Cause Analysis | ✅ AI-powered | ❌ Handmatig |
| Database queries | ✅ Automatisch | ❌ Extra setup |
| Learning curve | 🟢 Laag | 🔴 Hoog |

### Slide 3: Use Cases

**Kies Instana wanneer:**
- Snelle time-to-value belangrijk is
- Microservices architectuur
- Developers moeten zelf debuggen
- Enterprise support nodig
- Full-stack visibility vereist

**Kies OpenShift Native wanneer:**
- Budget constraints
- Simpele applicaties
- Team heeft Prometheus expertise
- Custom metrics belangrijk
- On-premise only (geen SaaS)

## 🔍 Monitoring Vergelijking Details

### Request Tracing

**OpenShift Prometheus:**
```promql
# Handmatige query voor latency
histogram_quantile(0.95,
  sum(rate(order_processing_duration_seconds_bucket[5m])) by (le)
)

# Separate query voor errors
sum(rate(orders_total{status="failed"}[5m]))
```

**Instana:**
- Klik op een service
- Zie p50, p95, p99 latency automatisch
- Filter op errors met één klik
- Drill down naar individuele traces

### Dependency Mapping

**OpenShift:**
- Geen automatische dependency map
- Kan handmatig worden gebouwd met Kiali (Service Mesh vereist)
- Vereist Istio installatie

**Instana:**
- Automatische dependency map
- Live updates
- Shows external dependencies (databases, APIs)
- Click to zoom into service

### Alerting

**OpenShift Prometheus Rules:**
```yaml
# Handmatig alert rule schrijven
- alert: HighErrorRate
  expr: rate(orders_total{status="failed"}[5m]) > 0.15
  for: 5m
  annotations:
    summary: "High error rate"
```

**Instana:**
- Smart Alerts: Automatisch anomaly detection
- Built-in alerts voor common issues
- Alert correlation
- Reduce alert noise

## 🛠️ Troubleshooting

### Pods starten niet
```bash
# Check events
oc get events -n demo-instana --sort-by='.lastTimestamp'

# Check pod logs
oc logs -n demo-instana <pod-name>

# Check resources
oc describe pod -n demo-instana <pod-name>
```

### Database connectie issues
```bash
# Check if postgres is running
oc get pods -n demo-instana -l app=postgres

# Test connection
oc exec -n demo-instana deployment/order-service -- \
  python -c "import psycopg2; psycopg2.connect(host='postgres', database='orders', user='admin', password='password123')"
```

### Instana agent niet zichtbaar
```bash
# Check agent logs
oc logs -n instana-agent -l app.kubernetes.io/name=instana-agent

# Verify agent key
oc get secret -n instana-agent instana-agent -o yaml
```

## 📚 Aanvullende Resources

### Instana Documentatie
- [Instana Docs](https://www.ibm.com/docs/en/instana-observability)
- [Python Sensor](https://www.ibm.com/docs/en/instana-observability/current?topic=sensors-monitoring-python)
- [Kubernetes Monitoring](https://www.ibm.com/docs/en/instana-observability/current?topic=platforms-monitoring-kubernetes)

### OpenShift Monitoring
- [OpenShift Monitoring](https://docs.openshift.com/container-platform/latest/monitoring/monitoring-overview.html)
- [Prometheus Operator](https://github.com/prometheus-operator/prometheus-operator)

## 🧹 Cleanup

```bash
# Verwijder applicatie
oc delete project demo-instana

# Verwijder Instana agent
oc delete project instana-agent

# Verwijder ClusterRole en ClusterRoleBinding
oc delete clusterrole instana-agent
oc delete clusterrolebinding instana-agent
```

## 📝 Code Highlights

### Automatische Instana Instrumentatie

De Python code bevat **geen** Instana-specifieke code in de main logic:

```python
# Dit is alles wat nodig is!
from flask import Flask
import psycopg2
import requests

app = Flask(__name__)

@app.route('/orders', methods=['POST'])
def create_order():
    # Database call - Instana traceert automatisch!
    conn = psycopg2.connect(...)
    
    # HTTP call - Instana traceert automatisch!
    response = requests.post(payment_url, ...)
    
    return jsonify(result)
```

Instana detecteert:
- Flask framework
- psycopg2 (PostgreSQL)
- requests (HTTP calls)
- En 200+ andere libraries automatisch!

### Handmatige Prometheus Metrics

Voor OpenShift native monitoring moet je:

```python
from prometheus_client import Counter, Histogram

# Metrics handmatig definiëren
order_counter = Counter('orders_total', 'Total orders', ['status'])
order_duration = Histogram('order_processing_duration_seconds', ...)

@app.route('/orders', methods=['POST'])
def create_order():
    start_time = time.time()
    
    # ... business logic ...
    
    # Metrics handmatig updaten
    duration = time.time() - start_time
    order_duration.observe(duration)
    order_counter.labels(status='success').inc()
```

## 🎬 Demo Checklist

- [ ] Deploy applicatie naar OpenShift
- [ ] Installeer Instana agent
- [ ] Open beide monitoring dashboards (Instana + OpenShift Console)
- [ ] Run normal load scenario
- [ ] Show automatic service discovery in Instana
- [ ] Run spike scenario
- [ ] Compare error detection in both systems
- [ ] Show distributed trace in Instana
- [ ] Explain manual correlation needed in OpenShift
- [ ] Run error scenario
- [ ] Show root cause analysis in Instana
- [ ] Compare setup complexity

## 💡 Demo Tips

1. **Start met OpenShift native** - Laat zien wat er "out of the box" is
2. **Toon de complexity** - Prometheus queries, manual correlation
3. **Switch naar Instana** - "Let's see hoe Instana dit aanpakt"
4. **Focus op time-to-value** - Hoeveel tijd bespaar je?
5. **Real scenarios** - Use production-like load patterns
6. **Q&A prep** - Wees voorbereid op vragen over pricing, security, data retention

Succes met je demo! 🚀
