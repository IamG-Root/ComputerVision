#!/usr/bin/env python3
"""Merge shared config assignments without executing either Python file."""
import argparse
import ast
import operator
import os
from pathlib import Path
import shutil
import tempfile

ROOT = Path(__file__).resolve().parents[1]
OPERATORS = {ast.Add: operator.add, ast.Sub: operator.sub,
             ast.Mult: operator.mul, ast.Div: operator.truediv}


def evaluate(node, values):
    try:
        return ast.literal_eval(node)
    except (ValueError, TypeError):
        pass
    if isinstance(node, ast.Name) and node.id in values:
        return values[node.id]
    if isinstance(node, ast.BinOp) and type(node.op) in OPERATORS:
        return OPERATORS[type(node.op)](evaluate(node.left, values), evaluate(node.right, values))
    if isinstance(node, (ast.List, ast.Tuple, ast.Set)):
        factory = {ast.List: list, ast.Tuple: tuple, ast.Set: set}[type(node)]
        return factory(evaluate(item, values) for item in node.elts)
    if isinstance(node, ast.Dict) and all(key is not None for key in node.keys):
        return {evaluate(k, values): evaluate(v, values) for k, v in zip(node.keys, node.values)}
    # Parse dict(key=value, ...) as data; never invoke a callable from the config.
    if (isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
            and node.func.id == 'dict' and not node.args
            and all(keyword.arg is not None for keyword in node.keywords)):
        return {keyword.arg: evaluate(keyword.value, values) for keyword in node.keywords}
    raise ValueError('Espressione non supportata: ' + ast.unparse(node))


def parse_config(text, filename):
    assignments, values = {}, {}
    for node in ast.parse(text, filename=filename).body:
        if isinstance(node, ast.Expr) and isinstance(node.value, ast.Constant) and isinstance(node.value.value, str):
            continue  # Module docstring.
        if isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
            name, value = node.targets[0].id, node.value
        elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name) and node.value is not None:
            name, value = node.target.id, node.value
        else:
            raise ValueError(f'{filename}:{node.lineno}: usare assegnazioni semplici; il file non viene eseguito')
        if name in assignments:
            raise ValueError(f'{filename}: parametro duplicato: {name}')
        try:
            values[name] = evaluate(value, values)
        except (ValueError, TypeError, ArithmeticError) as exc:
            raise ValueError(f'{filename}: parametro {name}: {exc}') from exc
        assignments[name] = value
    return assignments, values


def merge(source, destination):
    source_nodes, source_values = parse_config(source, 'sorgente')
    destination_nodes, _ = parse_config(destination, 'destinazione')
    shared = source_nodes.keys() & destination_nodes.keys()
    if not shared:
        raise ValueError('Nessun parametro in comune: destinazione invariata')
    # AST column offsets count UTF-8 bytes, not characters.
    data = destination.encode('utf-8')
    lines = data.splitlines(keepends=True)
    offsets = [0]
    for line in lines:
        offsets.append(offsets[-1] + len(line))
    edits = []
    for name in shared:
        expression = source_nodes[name]
        constructor_names = {n.func for n in ast.walk(expression)
                             if isinstance(n, ast.Call) and isinstance(n.func, ast.Name)
                             and n.func.id == 'dict'}
        references = {n.id for n in ast.walk(expression)
                      if isinstance(n, ast.Name) and n not in constructor_names}
        # Preserve dependencies such as TOPIC = "CV/" + MODULE_NAME when copied.
        replacement = (ast.unparse(expression)
                       if references <= shared else repr(source_values[name]))
        node = destination_nodes[name]
        edits.append((offsets[node.lineno - 1] + node.col_offset,
                      offsets[node.end_lineno - 1] + node.end_col_offset,
                      replacement.encode('utf-8')))
    for start, end, replacement in sorted(edits, reverse=True):
        data = data[:start] + replacement + data[end:]
    merged = data.decode('utf-8')
    _, merged_values = parse_config(merged, 'risultato')
    # Different declaration order must not silently change derived values.
    for name in shared:
        if merged_values[name] != source_values[name]:
            raise ValueError(f'Ordine/dipendenze incompatibili per {name}: destinazione invariata')
    return merged, sorted(shared), sorted(destination_nodes.keys() - shared), sorted(source_nodes.keys() - shared)


def copy_config(source, destination, dry_run=False):
    source, destination = source.resolve(strict=True), destination.resolve(strict=True)
    if source == destination or source.samefile(destination):
        raise ValueError('Sorgente e destinazione coincidono')
    original = destination.read_bytes()
    merged, copied, retained, skipped = merge(source.read_bytes().decode('utf-8-sig'),
                                              original.decode('utf-8-sig'))
    print('Parametri importati: ' + ', '.join(copied))
    print('Parametri solo nella destinazione, mantenuti: ' + (', '.join(retained) or 'nessuno'))
    print('Parametri solo nella sorgente, ignorati: ' + (', '.join(skipped) or 'nessuno'))
    if dry_run:
        print('Anteprima: nessun file modificato.')
        return None
    data = merged.encode('utf-8')
    if original.startswith(b'\xef\xbb\xbf'):
        data = b'\xef\xbb\xbf' + data
    if data == original:
        print('Configurazione gia aggiornata: nessuna modifica.')
        return None
    with tempfile.NamedTemporaryFile(prefix=destination.name + '.backup-', dir=destination.parent,
                                     delete=False) as out:
        backup = Path(out.name)
    shutil.copy2(destination, backup)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(prefix='.' + destination.name + '-', dir=destination.parent,
                                         delete=False) as out:
            temporary = Path(out.name)
            out.write(data)
            out.flush()
            os.fsync(out.fileno())
        shutil.copymode(destination, temporary)
        os.replace(temporary, destination)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)
    print(f'Configurazione aggiornata: {destination}')
    print(f'Backup: {backup}')
    return backup


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', default=os.environ.get('COPY_CONFIG_SOURCE'))
    parser.add_argument('--destination', type=Path, default=ROOT / 'module/config.py')
    parser.add_argument('--dry-run', action='store_true')
    args = parser.parse_args()
    if not args.source:
        parser.error('Specificare SOURCE: make copy_config_module SOURCE=../ComputerVision/module/config.py '
                     'oppure make copy_config_server SOURCE=../ComputerVision/server/config.py')
    try:
        copy_config(Path(args.source), args.destination, args.dry_run)
    except (OSError, ValueError, SyntaxError) as exc:
        parser.exit(1, f'Configurazione non copiata: {exc}\n')


if __name__ == '__main__':
    main()
