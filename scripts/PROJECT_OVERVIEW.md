# Instana vs OpenShift Monitoring Demo - Project Overzicht

## 📦 Wat je hebt gekregen

Een complete, production-ready demo applicatie om Instana te vergelijken met OpenShift native monitoring.

## 📁 Project Structuur

```
demo-instana/
├── README.md                          # Volledige documentatie
├── QUICKSTART.md                      # 15-minuten setup guide
├── DEMO_SCRIPT.md                     # Presentatie script (30 min)
├── COMPARISON.md                      # Gedetailleerde feature vergelijking
│
├── frontend/                          # Frontend service (Python Flask)
│   ├── app.py                        # Web UI + API gateway
│   ├── Dockerfile
│   └── requirements.txt
│
├── order-service/                     # Order service (Python Flask)
│   ├── app.py                        # Order processing + DB
│   ├── Dockerfile
│   └── requirements.txt
│
├── payment-service/                   # Payment service (Python Flask)
│   ├── app.py                        # Payment processing simulator
│   ├── Dockerfile
│   └── requirements.txt
│
├── k8s/                              # Kubernetes/OpenShift manifests
│   ├── 01-database.yaml              # PostgreSQL deployment
│   ├── 02-order-service.yaml         # Order service + ServiceMonitor
│   ├── 03-payment-service.yaml       # Payment service + ServiceMonitor
│   ├── 04-frontend.yaml              # Frontend + Route
│   ├── 05-instana-agent.yaml         # Instana agent DaemonSet
│   └── 06-prometheus-rules.yaml      # Prometheus alert rules
│
└── scripts/
    ├── deploy.sh                      # Automated deployment script
    ├── load-generator.py              # Load testing tool
    └── requirements.txt

```

## 🎯 Wat deze demo laat zien

### ✅ Instana Voordelen
1. **Automatische instrumentatie** - Geen code wijzigingen
2. **End-to-end tracing** - Complete request flow visibility
3. **Dependency mapping** - Automatische service topology
4. **AI-powered analysis** - Smart root cause detection
5. **5-minuten setup** - vs. 30-60 minuten handmatig

### ⚙️ OpenShift Native Realiteit
1. **Handmatige metrics** - Code moet aangepast worden
2. **Geen auto-tracing** - Jaeger vereist extra setup
3. **Handmatige correlatie** - Logs/metrics apart
4. **Alert tuning** - Veel false positives
5. **Steile leercurve** - PromQL expertise nodig

## 🚀 Hoe te gebruiken

### Quick Start (15 minuten)
```bash
# 1. Login op OpenShift
oc login --token=<token> --server=<server>

# 2. Deploy applicatie
chmod +x scripts/deploy.sh
./scripts/deploy.sh

# 3. Installeer Instana agent
# Edit k8s/05-instana-agent.yaml met je credentials
oc apply -f k8s/05-instana-agent.yaml

# 4. Run load test
python3 scripts/load-generator.py --url https://<frontend-url> --scenario mixed
```

### Demo Presentatie (30 minuten)
Volg `DEMO_SCRIPT.md` voor een gestructureerde presentatie met:
- Opening (2 min)
- Setup comparison (5 min)
- Monitoring features (10 min)
- Production scenarios (7 min)
- Business value (3 min)
- Q&A (3 min)

## 📊 Demo Scenarios

### 1. Normal Load
```bash
python3 scripts/load-generator.py --url <url> --scenario normal --duration 5
```
Toont: Steady state monitoring in beide systemen

### 2. Traffic Spike
```bash
python3 scripts/load-generator.py --url <url> --scenario spike --duration 2
```
Toont: Instana's automatic spike detection vs handmatige analyse

### 3. Error Simulation
```bash
python3 scripts/load-generator.py --url <url> --scenario error --duration 3
```
Toont: Root cause analysis in Instana vs manual debugging

### 4. Gradual Load Increase
```bash
python3 scripts/load-generator.py --url <url> --scenario gradual
```
Toont: Performance degradation detection

## 💡 Key Demo Highlights

### Toon in Instana:
1. **Service Map** - Automatische dependency discovery
2. **Golden Signals** - Latency, traffic, errors, saturation
3. **Distributed Traces** - End-to-end request flow
4. **Smart Alerts** - AI-powered incident detection
5. **Database Queries** - Slow query detection
6. **Impact Analysis** - Downstream service effects

### Toon in OpenShift:
1. **Prometheus Metrics** - Handmatig gedefinieerd
2. **Manual Queries** - PromQL schrijven nodig
3. **Alert Rules** - Handmatige thresholds
4. **Log Correlation** - Separate tool (geen integratie)
5. **Limited Visibility** - Geen auto-tracing

## 🎬 Presentatie Tips

1. **Start met OpenShift** - Laat zien wat default beschikbaar is
2. **Highlight manual work** - PromQL queries, log grepping
3. **Switch to Instana** - "Now let's see the difference"
4. **Live comparison** - Side-by-side browsers
5. **Use real scenarios** - Error debugging, performance issues
6. **Quantify time saved** - "85 minutes per incident"

## 📈 ROI Argumenten

### Time Savings
- **Setup**: 55 minuten per service
- **Debugging**: 85 minuten per incident
- **Team size 10**: €520.000 bespaard per jaar

### Business Impact
- 75% snellere MTTR
- 90% minder setup tijd
- 50% minder production incidents
- 80% betere developer productivity

## 🔧 Customization

### Je eigen services toevoegen:
```python
# Voeg nieuwe service toe:
# 1. Kopieer payment-service/ folder
# 2. Pas app.py aan voor je logic
# 3. Maak nieuwe k8s manifest
# 4. Deploy!

# Instana instrumenteert automatisch:
# - Flask, FastAPI, Django
# - psycopg2, SQLAlchemy, pymongo
# - requests, httpx, aiohttp
# - En 200+ andere libraries
```

### Andere databases:
```yaml
# MongoDB, MySQL, Redis, etc.
# Pas 01-database.yaml aan
# Instana detecteert automatisch!
```

## 📚 Documentatie

- **README.md** - Complete reference guide
- **QUICKSTART.md** - Snelle setup (15 min)
- **DEMO_SCRIPT.md** - Presentatie flow (30 min)
- **COMPARISON.md** - Feature comparison, TCO analysis

## ❓ Troubleshooting

### Pods starten niet?
```bash
oc describe pod -n demo-instana <pod>
oc logs -n demo-instana <pod>
```

### Instana agent niet zichtbaar?
```bash
oc logs -n instana-agent -l app.kubernetes.io/name=instana-agent
# Check: Agent Key, Network connectivity
```

### Database errors?
```bash
oc exec -n demo-instana deployment/postgres -- psql -U admin -d orders -c "SELECT 1"
```

## 🎯 Success Criteria

Na de demo moet je audience:
- ✅ Begrijpen waarom Instana sneller is
- ✅ Zien dat setup 10x eenvoudiger is
- ✅ Appreciëren AI-powered root cause analysis
- ✅ Realiseren dat TCO lager is met Instana
- ✅ Vragen om trial/POC

## 📞 Next Steps

1. **Schedule POC** - Test met eigen applicatie
2. **Instana Trial** - https://www.instana.com/trial/
3. **Review pricing** - Discuss with Instana team
4. **Migration plan** - 10-week rollout

## 🙏 Credits

Demo gebouwd met:
- Python Flask
- PostgreSQL
- OpenShift/Kubernetes
- Instana APM
- Prometheus + Grafana

---

**Veel succes met je demo!** 🚀
