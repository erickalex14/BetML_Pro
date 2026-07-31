from backend.pipeline import api_client

data = api_client.get('/leagues', params={'country': 'Ecuador', 'season': 2024})
for r in data.get('response', []):
    l = r['league']
    print(f"ID: {l['id']} | Nombre: {l['name']} | Tipo: {l['type']}")