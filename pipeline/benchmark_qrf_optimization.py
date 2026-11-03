"""QRF distribution ablations and past-only tuning, with a fixed wheat model.

The baseline reproduces the completed Colab run. Dense variants use 101 empirical
quantiles; all historical leaf samples and tree regularization are separate knobs.
"""
import argparse
import hashlib
import importlib.metadata
import json
from pathlib import Path
import time

import numpy as np
import pandas as pd
from quantile_forest import RandomForestQuantileRegressor

from benchmark_models import RollingCalibrated, read_data, quantile_loss, summarize
from benchmark_checkpoint import atomic_json
from common import DATA, hypotheses
from model import hyp_values, sample_quantile

GRID = np.linspace(0, 1, 101).round(2)
CONFIGS = {
    'base': {'min_samples_leaf': 5, 'max_depth': 5, 'max_samples_leaf': 1},
    'all_leaf': {'min_samples_leaf': 5, 'max_depth': 5, 'max_samples_leaf': None},
    'smooth': {'min_samples_leaf': 10, 'max_depth': 3, 'max_samples_leaf': None},
    'flexible': {'min_samples_leaf': 3, 'max_depth': 7, 'max_samples_leaf': None},
}
VARIANTS = {
    'qrf_sparse': ('base', False), 'qrf_dense': ('base', True),
    'qrf_sparse_all_leaf': ('all_leaf', False), 'qrf_dense_all_leaf': ('all_leaf', True),
    'qrf_dense_smooth': ('smooth', True), 'qrf_dense_flexible': ('flexible', True),
}


def dense_sample(q, indexes, uniforms):
    """Inverse empirical CDF interpolation; endpoints are observed leaf bounds."""
    values = np.empty(len(indexes))
    for i in np.unique(indexes):
        mask = indexes == i
        values[mask] = np.interp(uniforms[mask], GRID, q[i])
    return np.clip(values, .02, None)


def choose_from_past(detail, year):
    past = detail[(detail.year < year) & (detail.year >= year - 3)]
    if past.empty:
        return 'qrf_sparse'
    scores = past.groupby(['model', 'year']).contract_loss.mean().groupby('model').mean()
    return str(scores.idxmin())


def main(args):
    root = Path(__file__).resolve().parents[1]
    args.output.mkdir(parents=True, exist_ok=True)
    files = [Path(__file__), root/'pipeline/benchmark_models.py', root/'pipeline/model.py',
             root/'pipeline/common.py', root/'pipeline/01_agreste.py'] + [DATA/n for n in
             ['panel_rendements.csv','meteo_dept.csv','prix_ble.csv','hypotheses.yaml']]
    spec = {'configs': CONFIGS, 'variants': VARIANTS, 'samples': args.samples, 'seed': 42,
            'grid': GRID.tolist(), 'files': {p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in files},
            'packages':{n:importlib.metadata.version(n) for n in ['numpy','pandas','scikit-learn','quantile-forest']}}
    signature = hashlib.sha256(json.dumps(spec, sort_keys=True).encode()).hexdigest()
    manifest = args.output/'manifest.json'
    if manifest.exists() and json.loads(manifest.read_text())['signature'] != signature:
        raise ValueError('Sources or options changed: choose another output folder')
    atomic_json(manifest, {'signature':signature,'spec':spec})
    raw, weather = read_data()
    L, W = raw[raw.culture=='lentille'], raw[raw.culture=='ble']
    h = hyp_values(hypotheses())
    reference = pd.read_csv(args.reference, dtype={'dep':str})
    rows, audits = [], []
    started = time.monotonic()
    for year in range(2016,2026):
        checkpoint=args.output/f'year-{year}.json'
        if checkpoint.exists():
            saved=json.loads(checkpoint.read_text())
            assert saved['signature']==signature
            rows.extend(saved['rows']); audits.extend(saved['audit'])
            print(f'QRF {year}: repris',flush=True)
            continue
        before=len(rows)
        histL=L[L.annee<year]; histW=W[W.annee<year]
        # Raw distribution only: fit_base is identical to the final all-past fit
        # of RollingCalibrated; interval calibration does not enter these prices.
        lentil=RollingCalibrated('qrf').fit_base(histL)
        wheat=RollingCalibrated('linear').fit_base(histW)
        test=L[(L.annee==year)&L.dep.isin(set(lentil.levels.index)&set(wheat.levels.index))]
        realW=W[W.annee==year].set_index('dep')
        test=test[test.dep.isin(realW.index)].sort_values('dep')
        if year>=2019:
            assert set(test.dep)==set(reference.loc[reference.year==year,'dep']), f'Cohort mismatch {year}'
        train=histL[histL.dep.isin(lentil.levels.index)]
        X=lentil.features.transform(train)
        y=train.rendement_qha.to_numpy()/lentil.levels.reindex(train.dep).to_numpy()
        fitted={'base':lentil.model.model}
        for key, config in CONFIGS.items():
            if key!='base':
                fitted[key]=RandomForestQuantileRegressor(n_estimators=300,max_features=.8,
                    random_state=42,n_jobs=1,**config).fit(X,y)
        for _, r in test.iterrows():
            pool=weather[(weather.dep==r.dep)&(weather.annee<year)].copy()
            pool['annee']=year
            rng=np.random.default_rng(42+year*100)
            ix=rng.integers(len(pool),size=args.samples)
            uL,uW=rng.random(args.samples),rng.random(args.samples)
            yW=sample_quantile(wheat.predict_quantiles(pool)[ix],uW)*wheat.levels[r.dep]/10
            numerator=pool.prix_ble.to_numpy()[ix]*yW-h['charges_ble']+h['charges_lentille']-h['bonus']
            realised=(r.prix_ble*realW.loc[r.dep,'rendement_qha']/10-h['charges_ble']+h['charges_lentille']-h['bonus'])/(r.rendement_qha/10)
            features=lentil.features.transform(pool)
            distributions={key:m.predict(features,quantiles=GRID.tolist()) for key,m in fitted.items()}
            for name,(key,dense) in VARIANTS.items():
                q=distributions[key]
                sampled=dense_sample(q,ix,uL) if dense else sample_quantile(q[ix][:,[10,50,90]],uL)
                yL=sampled*lentil.levels[r.dep]/10
                price=float(np.quantile(numerator/yL,h['tau'],method='inverted_cdf'))
                rows.append({'year':year,'dep':r.dep,'model':name,'price':price,
                    'realised_break_even':float(realised),'held':bool(price>=realised),
                    'contract_loss':float(quantile_loss(realised,price,.8)),
                    'shortfall_eur_ha':float(max(0,realised-price)*r.rendement_qha/10),
                    'pinball':None,'coverage':None,'width':None})
        audit={'year':year,'train_max':int(histL.annee.max()),'n_train':len(train),'n_test':len(test),
               'models':list(VARIANTS),'selection_uses_future':False}
        audits.append(audit)
        atomic_json(checkpoint,{'signature':signature,'rows':rows[before:],'audit':[audit]})
        pd.DataFrame(rows).to_csv(args.output/'predictions_partial.csv',index=False)
        atomic_json(args.output/'progress.json',{'completed':year-2015,'total':10,'year':year,'status':'running'})
        print(f'QRF {year}: {year-2015}/10 années sauvegardées · {len(test)} départements',flush=True)
    all_rows=pd.DataFrame(rows)
    selected=[]; selections=[]
    for year in range(2019,2026):
        chosen=choose_from_past(all_rows,year)
        selected.append(all_rows[(all_rows.year==year)&(all_rows.model==chosen)].assign(model='qrf_past_selected'))
        selections.append({'year':year,'chosen':chosen,'validation_years':list(range(year-3,year))})
    detail=pd.concat([all_rows[all_rows.year>=2019],*selected],ignore_index=True)
    # Matching the old baseline checks normalization, RNG and retained cohorts.
    base=detail[detail.model=='qrf_sparse'].merge(reference[reference.model=='qrf'],on=['year','dep'],suffixes=('_new','_ref'),validate='one_to_one')
    assert len(base)==192
    max_delta=float(np.abs(base.price_new-base.price_ref).max())
    assert max_delta<1e-7, f'Control does not reproduce Colab QRF: {max_delta}'
    all_rows.to_csv(args.output/'predictions_with_warmup.csv',index=False)
    detail.to_csv(args.output/'predictions.csv',index=False)
    result={'spec':spec,'summary':summarize(detail),'selection':selections,'audit':audits,
        'baseline_max_abs_price_difference':max_delta,'seconds':time.monotonic()-started,
        'status':'exploratory_past_only_selection','objective':'contract_pinball_0.8',
        'distribution':'Same historical weather/price years and fixed wheat linear model; only lentil distribution changes.'}
    atomic_json(args.output/'results.json',result)
    atomic_json(args.output/'progress.json',{'completed':10,'total':10,'status':'complete'})
    print(pd.DataFrame(result['summary']).to_string(index=False),flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--reference',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    p.add_argument('--samples',type=int,default=20000)
    main(p.parse_args())
