"""Exercise four seeded defects against a numerically passing real delivery copy."""
import argparse
import json
from pathlib import Path
from grade_excel_benchmark import grade
from seed_excel_defects import seed


def check(source, destination):
    control = grade(source)
    if not control.get('numeric_pass'):
        raise ValueError('A numerically passing positive control is required before seeding defects.')
    seed(source, destination)
    expected = {'wrong-net-income': 'incorrect: Net income',
                'missing-sheet': 'Required four sheets/order not present',
                'no-formula-cache': 'Missing/error cache',
                'altered-input': 'Source changed or missing: source.csv'}
    results = {}
    for name, message in expected.items():
        result = grade(Path(destination) / name)
        results[name] = {'rejected': not result.get('numeric_pass', False),
                         'intended_failure_detected': any(message in e for e in result['errors']),
                         'errors': result['errors']}
    return {'positive_control': control, 'mutations': results,
            'pass': all(v['rejected'] and v['intended_failure_detected'] for v in results.values()),
            'limitations': 'The missing-sheet mutation also clears caches; its sheet error is checked separately. The numeric mutation changes only its designated formula/cache. Positive control is numerical only; it is not a layout or end-to-end trial pass.'}


if __name__ == '__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('source',type=Path);p.add_argument('destination',type=Path);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();report=check(a.source,a.destination);a.output.write_text(json.dumps(report,indent=2));print(a.output);raise SystemExit(0 if report['pass'] else 1)
