# parsers/code_parser.py
import ast
import os

def read_py_source(path):
    with open(path, "r", encoding="utf-8") as f:
        return f.read()

class CodeAnalyzer(ast.NodeVisitor):
    def __init__(self):
        self.positional_unpack_sites = []   # (lineno, count, src)
        self.dictreader_sites = []         # (lineno, src)
        self.csv_reader_sites = []         # (lineno, src)
        self.file_reads = []               # (lineno, filename_or_var)
        self.file_writes = []              # (lineno, filename_or_var)
        self.var_string_values = {}        # var -> resolved path (when possible)
        self.var_list_values = {}          # var -> list of string constants (candidate headers)
        self.header_writes = []            # (lineno, header_list_or_var)
        self.source = ""

    def _resolve_join_call(self, call_node):
        try:
            func = call_node.func
            if isinstance(func, ast.Attribute) and func.attr == "join":
                args = []
                for a in call_node.args:
                    if isinstance(a, ast.Constant) and isinstance(a.value, str):
                        args.append(a.value)
                    else:
                        return None
                return os.path.join(*args)
        except Exception:
            return None
        return None

    def _extract_list_of_constants(self, node):
        # return list of string constants if node is List of Constant strings, else None
        if isinstance(node, ast.List):
            vals = []
            for elt in node.elts:
                if isinstance(elt, ast.Constant) and isinstance(elt.value, str):
                    vals.append(elt.value)
                else:
                    return None
            return vals
        # also handle tuple literals
        if isinstance(node, ast.Tuple):
            vals = []
            for elt in node.elts:
                if isinstance(elt, ast.Constant) and isinstance(elt.value, str):
                    vals.append(elt.value)
                else:
                    return None
            return vals
        return None

    def visit_Assign(self, node):
        # capture string assignments (PATH vars) and list-of-strings (header-like) assignments
        try:
            value = node.value
            resolved_path = None
            if isinstance(value, ast.Constant) and isinstance(value.value, str):
                resolved_path = value.value
            elif isinstance(value, ast.Call):
                resolved_path = self._resolve_join_call(value)
            # record var string values
            if resolved_path:
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        self.var_string_values[target.id] = resolved_path
                        # also mark as potential write-read path
                        self.file_writes.append((node.lineno, resolved_path))

            # list-of-strings assignment detection (header candidate)
            list_vals = self._extract_list_of_constants(value)
            if list_vals:
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        self.var_list_values[target.id] = list_vals

            # detect tuple/list unpacking like: a,b,c = row
            if isinstance(node.targets[0], (ast.Tuple, ast.List)):
                target_len = len(node.targets[0].elts)
                seg = ast.get_source_segment(self.source, node) or ""
                if seg and ("= row" in seg or "= r" in seg or "= data" in seg or "= next" in seg):
                    self.positional_unpack_sites.append((node.lineno, target_len, seg.strip()))
        except Exception:
            pass
        self.generic_visit(node)

    def visit_Call(self, node):
        func = node.func
        name = ""
        if isinstance(func, ast.Attribute):
            base = getattr(func.value, "id", "")
            name = f"{base}.{func.attr}"
        elif isinstance(func, ast.Name):
            name = func.id

        seg = ast.get_source_segment(self.source, node) or ""

        # DictReader or csv.reader detection
        if "DictReader" in name or "csv.DictReader" in seg:
            self.dictreader_sites.append((node.lineno, seg.strip()))
        if "csv.reader" in seg or ("reader" in name and "csv" in seg):
            self.csv_reader_sites.append((node.lineno, seg.strip()))

        # file read/write detection through open(...)
        if isinstance(func, ast.Name) and func.id == "open" and node.args:
            arg0 = node.args[0]
            # resolve Constant string
            if isinstance(arg0, ast.Constant) and isinstance(arg0.value, str):
                self.file_reads.append((node.lineno, arg0.value))
            elif isinstance(arg0, ast.Name):
                varname = arg0.id
                resolved = self.var_string_values.get(varname)
                if resolved:
                    self.file_reads.append((node.lineno, resolved))
                else:
                    self.file_reads.append((node.lineno, varname))
            # attempt to detect mode 'w' to mark writes (second arg)
            if len(node.args) >= 2:
                mode = node.args[1]
                if isinstance(mode, ast.Constant) and isinstance(mode.value, str) and "w" in mode.value:
                    # mark as write to same path
                    if isinstance(arg0, ast.Constant) and isinstance(arg0.value, str):
                        self.file_writes.append((node.lineno, arg0.value))
                    elif isinstance(arg0, ast.Name):
                        varname = arg0.id
                        resolved = self.var_string_values.get(varname)
                        if resolved:
                            self.file_writes.append((node.lineno, resolved))
                        else:
                            self.file_writes.append((node.lineno, varname))

        # pandas read_csv detection
        if isinstance(func, ast.Attribute) and func.attr == "read_csv" and node.args:
            a0 = node.args[0]
            if isinstance(a0, ast.Constant) and isinstance(a0.value, str):
                self.file_reads.append((node.lineno, a0.value))
            elif isinstance(a0, ast.Name):
                varname = a0.id
                resolved = self.var_string_values.get(varname)
                if resolved:
                    self.file_reads.append((node.lineno, resolved))
                else:
                    self.file_reads.append((node.lineno, varname))

        # detect writer.writerow(...) - capture header writes
        if isinstance(func, ast.Attribute) and func.attr == "writerow" and node.args:
            a0 = node.args[0]
            # if argument is a name and we have var_list_values for it
            if isinstance(a0, ast.Name):
                v = a0.id
                hdr = self.var_list_values.get(v)
                self.header_writes.append((node.lineno, v if hdr is None else hdr))
            else:
                # if argument is list literal, extract
                hdr = self._extract_list_of_constants(a0)
                if hdr:
                    self.header_writes.append((node.lineno, hdr))
                else:
                    # unknown arg (could be variable built earlier); store source snippet
                    self.header_writes.append((node.lineno, seg.strip()))

        self.generic_visit(node)

def analyze_python_file(path):
    if not os.path.exists(path):
        return {}
    try:
        src = read_py_source(path)
    except Exception:
        return {}
    try:
        tree = ast.parse(src, filename=path)
    except Exception:
        return {}
    analyzer = CodeAnalyzer()
    analyzer.source = src
    analyzer.visit(tree)
    return {
        "positional_unpack_sites": analyzer.positional_unpack_sites,
        "dictreader_sites": analyzer.dictreader_sites,
        "csv_reader_sites": analyzer.csv_reader_sites,
        "file_reads": analyzer.file_reads,
        "file_writes": analyzer.file_writes,
        "var_string_values": analyzer.var_string_values,
        "var_list_values": analyzer.var_list_values,
        "header_writes": analyzer.header_writes
    }
