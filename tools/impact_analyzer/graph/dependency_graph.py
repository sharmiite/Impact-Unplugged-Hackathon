# graph/dependency_graph.py
import os
import glob
from collections import defaultdict

def find_python_modules(root_snapshot):
    """
    Return mapping: module_path -> list of python files in that module folder
    (Expected each country folder contains module_a.py ... module_d.py)
    """
    modules = {}
    for country_dir in glob.glob(os.path.join(root_snapshot, "*")):
        if os.path.isdir(country_dir):
            # collect python files directly under this folder
            py_files = [os.path.join(country_dir, f) for f in os.listdir(country_dir) if f.endswith(".py")]
            modules[os.path.basename(country_dir)] = py_files
    return modules

def build_reader_map(modules, code_analysis_results):
    """
    Map which module (country/module folder) reads which shared filenames.
    Returns { module_name: set(shared_filename, ...) }
    code_analysis_results: { module_name: { file: analysis } }
    """
    reader_map = {}
    for module_name, analyses in code_analysis_results.items():
        files = set()
        for fpath, analysis in analyses.items():
            for fr in analysis.get("file_reads", []):
                # fr = (lineno, "path")
                fname = fr[1]
                # Normalize shared file names only; remove ../ and folder prefix
                simple = os.path.basename(fname)
                files.add(simple)
        reader_map[module_name] = files
    return reader_map
