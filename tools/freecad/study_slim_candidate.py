"""Run one unchanged slim-study recipe in a separate process.

Set FLAN36_STUDY_RECIPE to a recipe ID and FLAN36_STUDY_OUT to an empty
output directory. This partitions the same checks; it does not relax them.
SPDX-License-Identifier: GPL-3.0-or-later
"""
from pathlib import Path
import hashlib,json,os,sys,traceback
sys.path.insert(0,str(Path(__file__).parent))
import study_slim_mounts as study
recipe=os.environ.get('FLAN36_STUDY_RECIPE','')
selected=[c for c in study.CANDIDATES if c[0]==recipe]
if len(selected)!=1:raise ValueError('Select exactly one known FLAN36_STUDY_RECIPE')
study.CANDIDATES=selected
status=0
try:
    study.main()
    path=study.OUT/'report.json';report=json.loads(path.read_text())
    report['execution_partition']={'recipe':recipe,'runner':'tools/freecad/study_slim_candidate.py',
        'runner_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        'checks':'Unmodified study functions; only the candidate list is partitioned.'}
    path.write_text(json.dumps(report,indent=2)+'\n')
except Exception:
    traceback.print_exc(file=sys.__stderr__);status=1
sys.__stdout__.flush();sys.__stderr__.flush();os._exit(status)
