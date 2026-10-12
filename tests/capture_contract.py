"""Generate fixtures from the untouched baseline, before refactoring."""
import json, os, sys, time
from pathlib import Path
os.environ['TZ'] = 'UTC'
time.tzset()
sys.path.insert(0, str(Path(__file__).parent / 'baseline'))
from processing import DataProcessing
import config
cases = [[], [{'id': 1, 'class': 'person', 'position': [1.25, 2.5], 'last_update': 1700000000}, {'id': 999, 'class': 'pallet', 'position': [-1.0, 0.0], 'last_update': 1700000001}]]
result = {'commit': 'e057a1199069d1468dd8ccd7824ae5f5570052f9', 'topics': [config.LOCAL_PUB_TOPIC, config.FIWARE_PUB_TOPIC], 'cases': []}
for entities in cases:
    result['cases'].append({'input': entities, 'unity': DataProcessing.format_array_for_unity(entities), 'fiware': DataProcessing.format_array_for_fiware(entities)})
Path('tests/fixtures/contract.json').write_text(json.dumps(result, indent=2))
print('Baseline fixtures generated from original serializers')
