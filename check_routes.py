from app import create_app

app = create_app()
print("Registered routes:")
for rule in app.url_map.iter_rules():
    if rule.rule == '/' or 'root' in rule.endpoint:
        print(f'{rule.endpoint}: {rule.rule} -> {rule.methods}')

