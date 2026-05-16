# RoadSoS
**Road Safety Hackathon 2026 — IIT Madras**
AI-powered emergency services chatbot for road accident victims.

---

## Run with Docker (recommended)

```bash
# 1. Clone / unzip the project
cd roadsos

# 2. Build and start
docker-compose up --build

# 3. Open in browser
http://localhost:5000
```

## Run without Docker

```bash
pip install -r requirements.txt
python app.py
```

## API Endpoints

| Endpoint | Method | Description |
|---|---|---|
| `/health` | GET | Health check |
| `/api/emergency-numbers?country=IN&state=TG` | GET | Emergency numbers |
| `/api/nearby?lat=17.38&lon=78.48&type=hospital` | GET | Nearby services |
| `/api/chat` | POST | Chatbot message |

## Project Structure

```
roadsos/
├── app.py                  # Flask entry point
├── config.py               # All configuration
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
├── data/
│   ├── emergency_numbers.json   # 30 countries, 24 Indian states
│   └── roadsos.db               # SQLite offline cache
├── modules/
│   ├── emergency_numbers.py     # Step 1 — done
│   ├── location_finder.py       # Step 2
│   ├── overpass_client.py       # Step 2
│   ├── cache_manager.py         # Step 3
│   ├── cache_seeder.py          # Step 3
│   ├── intent_parser.py         # Step 4
│   └── response_builder.py      # Step 4
├── templates/
│   └── index.html               # Step 6
└── static/
    ├── css/style.css            # Step 6
    └── js/
        ├── map.js               # Step 6
        └── chat.js              # Step 6
```
