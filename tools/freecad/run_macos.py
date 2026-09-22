#!/usr/bin/env python3
"""Use the already-installed FreeCAD runtime without changing app preferences.
SPDX-License-Identifier: GPL-3.0-or-later
"""
import os
import subprocess
import sys
from pathlib import Path
app=Path('/Applications/FreeCAD.app/Contents/Resources')
target=Path(sys.argv[1]).resolve()
# The optional flatmesh unfolding extension crashes in this app-bundled Python
# on import. It is unrelated to solid/mesh CAD and is disabled only in this
# subprocess; no installed module or application preference is modified.
code='import sys,runpy;sys.path.insert(0,sys.argv[1]);sys.modules["flatmesh"]=None;runpy.run_path(sys.argv[2],run_name="__main__")'
environment=dict(os.environ,QT_QPA_PLATFORM=os.environ.get('FILO_QT_PLATFORM','offscreen'),FILO_FREECAD_SUBPROCESS='1')
raise SystemExit(subprocess.call([str(app/'bin/python'),'-c',code,str(app/'lib'),str(target),*sys.argv[2:]],env=environment))
