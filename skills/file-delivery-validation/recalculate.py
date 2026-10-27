"""Recalculate a working copy and render evidence; never resave final XLSX in openpyxl."""
import argparse
import json
from pathlib import Path
import subprocess
import tempfile


def convert(source, destination):
    source, destination = Path(source).resolve(), Path(destination).resolve()
    destination.mkdir(parents=True, exist_ok=True)
    if source.parent == destination:
        raise ValueError('Use a separate final-output directory.')
    with tempfile.TemporaryDirectory() as profile:
        common = ['libreoffice', '-env:UserInstallation=' + Path(profile).as_uri(), '--headless']
        commands = [common + ['--convert-to', 'xlsx', '--outdir', str(destination), str(source)]]
        for cmd in commands:
            subprocess.run(cmd, check=True, capture_output=True, timeout=120)
        final = destination / source.with_suffix('.xlsx').name
        if not final.is_file():
            raise RuntimeError('LibreOffice did not produce the final workbook.')
        subprocess.run(common + ['--convert-to', 'pdf', '--outdir', str(destination), str(final)],
                       check=True, capture_output=True, timeout=120)
        pdf = final.with_suffix('.pdf')
        if not pdf.is_file():
            raise RuntimeError('Missing print-layout evidence.')
        subprocess.run(['pdftoppm', '-scale-to', '1600', '-png', str(pdf), str(destination / 'page')],
                       check=True, capture_output=True, timeout=120)
    import openpyxl
    formulas, values = openpyxl.load_workbook(final), openpyxl.load_workbook(final, data_only=True)
    for sheet in formulas:
        for row in sheet:
            for cell in row:
                if cell.data_type == 'f' and (values[sheet.title][cell.coordinate].value is None or
                                             values[sheet.title][cell.coordinate].data_type == 'e'):
                    raise RuntimeError(f'Missing/error cached formula value: {sheet.title}!{cell.coordinate}')
    report = {'file':final.name,'formula_caches':'present','rendered_pages':len(list(destination.glob('page-*.png'))),
              'visual_review':'pending owner review'}
    formulas.close(); values.close()
    (destination / 'recalculation.json').write_text(json.dumps(report, indent=2))
    return report


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('source'); p.add_argument('destination')
    a = p.parse_args()
    print(json.dumps(convert(a.source,a.destination)))
