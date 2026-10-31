import os,sys,json,hashlib
from pathlib import Path
import numpy as np
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT / 'pipeline'))
from benchmark_advanced import load_data, feature_columns
from multicrop_models import YieldModel
from advanced_models import AdvancedYieldModel
from numpy._core._multiarray_umath import __cpu_features__
def sha(a):return hashlib.sha256(np.asarray(a).tobytes()).hexdigest()
raw,weather,_=load_data(ROOT / 'data')
h=raw[(raw.culture=='pois')&(raw.annee<2018)]
test=raw[(raw.culture=='pois')&(raw.annee==2018)].sort_values('dep')
out={}
for name,group in [('legacy','seasonal'),('advanced','soil')]:
 columns,static=feature_columns('pois',group)
 m=YieldModel('qrf',42,1).fit(h,columns) if name=='legacy' else AdvancedYieldModel({'family':'qrf'},42,1).fit(h,columns,static)
 t=test[test.dep.isin(m.levels.index)]
 trees=m.model.estimators_
 q=m.predict_quantiles(t)
 out[name]={'X':sha(m.prepared.X),'y':sha(m.prepared.y),'tree_nodes':sha(np.concatenate([e.tree_.__getstate__()['nodes'].view(np.uint8) for e in trees])), 'leaf_assignments':sha(m.model.apply(m.prepared.X)), 'sorter':sha(m.model.sorter_), 'predictions':sha(q),'max_samples_leaf':m.model.max_samples_leaf,'n':len(m.prepared.y)}
 np.savez(sys.argv[1]+'-'+name+'.npz',X=m.prepared.X,y=m.prepared.y,leaf=m.model.apply(m.prepared.X),q=q,sorter=m.model.sorter_)
out['cpu_features']=[k for k,v in __cpu_features__.items() if v]
out['disable']=os.environ.get('NPY_DISABLE_CPU_FEATURES')
Path(sys.argv[1]+'.json').write_text(json.dumps(out,indent=2))
print(json.dumps(out,indent=2))
