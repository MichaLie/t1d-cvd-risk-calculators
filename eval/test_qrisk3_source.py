"""Offline equivalence checks against the bundled, unmodified ClinRisk C source.

Requires a C compiler and Node.js. The shared library exists only in a temporary
folder. Integer-age tests reflect the C API; fractional ages are a documented
continuous-age extension checked separately by extended_parity.
"""
import ctypes
import hashlib
import json
import math
from pathlib import Path
import random
import re
import subprocess
import sys
import tempfile
from eval.models.qrisk3 import qrisk3_risk

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'third_party/qrisk3/qrisk3-2017.c'
SHA256 = '98bb0cd7071d49fca2d4620f1d447313838f55253616110d3888b3df0cc02aa4'
TOL = 1e-9  # absolute percentage points


def main():
    assert hashlib.sha256(SOURCE.read_bytes()).hexdigest() == SHA256
    source = SOURCE.read_text()
    rng = random.Random(20260912)
    records = []
    maximum = 0.0
    comparisons = 0
    with tempfile.TemporaryDirectory(prefix='qrisk3-source-') as directory:
        folder = Path(directory)
        wrapper = '#include <math.h>\n#include "' + str(SOURCE) + '"\n'
        signatures = {}
        for sex in ('female', 'male'):
            signature = re.search(r'static double cvd_' + sex + r'_raw\((.*?)\)', source, re.S)[1]
            fields = [part.strip().split() for part in signature.split(',')]
            signatures[sex] = fields
            wrapper += 'double reference_' + sex + '(' + signature + '){return cvd_' + sex + '_raw(' + ','.join(name for _, name in fields) + ');}\n'
        (folder / 'wrapper.c').write_text(wrapper)
        library = folder / ('reference.dylib' if sys.platform == 'darwin' else 'reference.so')
        flags = ['-dynamiclib'] if sys.platform == 'darwin' else ['-shared', '-fPIC']
        subprocess.run(['cc', *flags, '-O2', str(folder / 'wrapper.c'), '-lm', '-o', str(library)], check=True)
        lib = ctypes.CDLL(str(library))
        for female in (False, True):
            sex = 'female' if female else 'male'
            fields = signatures[sex]
            reference = getattr(lib, 'reference_' + sex)
            reference.argtypes = [ctypes.c_int if kind == 'int' else ctypes.c_double for kind, _ in fields]
            reference.restype = ctypes.c_double
            # Cross all ethnicity and smoking categories, both sexes and age extremes.
            for i in range(900):
                p = dict(age=[25,40,60,84][i%4], ethrisk=1+(i%9), smoke_cat=(i//9)%5,
                         bmi=rng.uniform(18,40), rati=rng.uniform(1.5,8), sbp=rng.uniform(95,200),
                         sbps5=rng.uniform(0,30), town=rng.uniform(-6,10), surv=10)
                for _, name in fields:
                    if name.startswith('b_') or name == 'fh_cvd':
                        p[name] = int(rng.random() < .25)
                # Diabetes types are mutually exclusive in real profiles.
                p['b_type1'], p['b_type2'] = [(0,0),(1,0),(0,1)][i%3]
                expected = reference(*(p[name] for _, name in fields))
                py = qrisk3_risk(female=female, **{k:v for k,v in p.items() if k!='surv'})
                assert math.isfinite(py) and abs(py-expected)<TOL, (sex,p,py,expected)
                maximum = max(maximum, abs(py-expected)); comparisons += 1
                # Independent C reference for precisely the browser's restricted adapter.
                for name in ['b_atypicalantipsy','b_corticosteroids','b_impotence2','b_migraine','b_ra','b_semi','b_sle']:
                    if name in p:p[name]=0
                expected = reference(*(p[name] for _, name in fields))
                js = dict(female=female, age=p['age'], ethrisk=p['ethrisk'], smoke_cat=p['smoke_cat'],
                          bmi=p['bmi'], tc_hdl_ratio=p['rati'], sbp=p['sbp'], sbps5=p['sbps5'], town=p['town'],
                          af=bool(p['b_AF']), egfr=45 if p['b_renal'] else 100,
                          on_bp_treatment=bool(p['b_treatedhyp']), b_type1=bool(p['b_type1']),
                          b_type2=bool(p['b_type2']), family_history_cvd=bool(p['fh_cvd']))
                records.append(dict(patient=js, expected=expected))
    script = r'''
const qrisk3=require('./metatool/qrisk3.js');let data='';
process.stdin.on('data',s=>data+=s);process.stdin.on('end',()=>{
 let max=0;const records=JSON.parse(data);
 for(const {patient,expected} of records){const got=qrisk3(patient);
  if(!Number.isFinite(got)||Math.abs(got-expected)>1e-9)throw Error(JSON.stringify({patient,got,expected}));
  max=Math.max(max,Math.abs(got-expected));}
 console.log(JSON.stringify({comparisons:records.length,max_abs_difference_pp:max}));
});'''
    result = subprocess.run(['node','-e',script],cwd=ROOT,input=json.dumps(records),text=True,capture_output=True,check=True)
    browser = json.loads(result.stdout)
    print(json.dumps(dict(status='PASS',python_vs_original_c=comparisons,
                         browser_vs_original_c=browser['comparisons'],
                         max_abs_difference_pp=max(maximum,browser['max_abs_difference_pp']),tolerance_pp=TOL)))

if __name__ == '__main__':
    main()
