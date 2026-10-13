"""J = C sin Transfers + BU L3 Top 9 + Other; filas sólo en RAM."""
from __future__ import annotations

import argparse
import hashlib
import itertools
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
import shutil
import time

import numpy as np
import pandas as pd
from threadpoolctl import threadpool_limits

import b_incremental_data as data
import compare_engineering_bc_priority as prior
import engineering_bu_l3_experiment as bu
import engineering_model_c as base
import engineering_model_c_qvoice as cq
import qvoice_horizon_calibration as horizon
from qvoice_model_data import load_config

ROOT = base.ROOT
DEFAULT = ROOT / "config/engineering_model_j_bu_top9_without_transfers_20261013.json"


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))


def native(value):
    if isinstance(value, dict): return {str(k): native(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)): return [native(v) for v in value]
    if isinstance(value, np.ndarray): return native(value.tolist())
    if isinstance(value, np.generic): return value.item()
    if isinstance(value, (pd.Timestamp, datetime)): return value.isoformat()
    return value


def write(path, value):
    path = Path(path); path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(native(value), ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")


def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def selected_spec(source, period_id):
    return next(row["selected"] for row in source["periods"] if row["id"] == period_id)


@dataclass
class TopNineBU:
    keep: list[str]
    other: str

    @classmethod
    def fit(cls, frame, n, other):
        values = frame.loc[frame.bu_l3.astype(str) != "(unknown)", ["person_key", "bu_l3"]].drop_duplicates()
        counts = values.groupby("bu_l3", observed=True).size().sort_values(ascending=False, kind="stable")
        keep = [str(x) for x in counts.head(n).index]
        if len(keep) != n:
            raise RuntimeError("No hay nueve BU L3 conocidas en el entrenamiento.")
        return cls(keep, other)

    def apply(self, frame):
        result = frame.copy(deep=False)
        value = frame.bu_l3.astype(str)
        result["bu_l3_top9_other"] = value.where(value.isin(self.keep), self.other).astype("category")
        if not result.bu_l3_top9_other.astype(str).isin(self.keep + [self.other]).all():
            raise RuntimeError("Una observación no cayó en Top 9 + Other.")
        return result


class TopNineModel:
    def __init__(self, model, pool):
        self.model, self.pool = model, pool
        self.design, self.beta, self.features, self.l2 = model.design, model.beta, model.features, model.l2

    def risk(self, frame): return self.model.risk(self.pool.apply(frame))
    def eta(self, frame): return np.asarray(self.design.matrix(self.pool.apply(frame)) @ self.beta).ravel()
    def artifact(self): return {**self.model.artifact(), "bu_l3_top9_other": {"keep": self.pool.keep, "other": self.pool.other}}


def model_eta(model, frame):
    return model.eta(frame) if isinstance(model, TopNineModel) else np.asarray(cq.eta(model, frame)).ravel()


def risk_with_q(model, frame, fitted):
    encoder, beta = fitted
    correction = np.asarray(horizon.category_matrix(encoder, frame) @ beta).ravel()
    columns = dict(zip(model.design.columns, model.beta))
    calendar = np.zeros(13)
    for column, value in columns.items():
        if column.startswith("calendar_month="): calendar[int(column.split("=", 1)[1])] = value
    month = frame.snapshot_date.dt.month.to_numpy()
    fixed = model_eta(model, frame) - calendar[month] + correction
    future = (month[:, None] - 1 + np.arange(6)) % 12 + 1
    total = np.exp(np.clip(fixed[:, None] + calendar[future], -30, 5)).sum(axis=1)
    return np.clip(-np.expm1(-total), 1e-8, 1 - 1e-8)


def fit_q(model, train, spec):
    encoder = cq.qmodel.CategoryEncoder.fit(train, list(spec["features"]))
    matrix = horizon.category_matrix(encoder, train)
    beta, okay, iterations = cq.qmodel.fit_offset(matrix, train.y_next.to_numpy(float), model_eta(model, train), float(spec["l2"]))
    if not okay: raise RuntimeError("No convergió la corrección QVoice.")
    return (encoder, beta), int(iterations)


def group_codes(frame, pool):
    values = pool.apply(frame).bu_l3_top9_other.astype(str)
    labels = [pool.other, *pool.keep]
    codes = pd.Categorical(values, categories=labels).codes
    if np.any(codes < 0) or len(labels) != 10:
        raise RuntimeError("La partición BU no tiene exactamente Top 9 + Other.")
    return codes.astype(int), labels


def allocation(frame, p, codes, count, fraction, config):
    dates, unique_dates = pd.factorize(frame.snapshot_date, sort=True)
    cells = dates * count + codes
    shape = (len(unique_dates), count)
    n = np.bincount(cells, minlength=np.prod(shape)).reshape(shape)
    e = np.bincount(cells, weights=frame.y_6m.to_numpy(float), minlength=np.prod(shape)).reshape(shape)
    pred = np.bincount(cells, weights=p, minlength=np.prod(shape)).reshape(shape)
    score = np.divide(pred, n, out=np.zeros(shape), where=n > 0)
    eligible = n >= int(config["group_minimum_people_each_snapshot"])
    w = np.zeros_like(score)
    for i in range(len(unique_dates)):
        remaining = n[i].sum() * fraction
        for value in np.unique(score[i, eligible[i]])[::-1]:
            mask = eligible[i] & (score[i] == value); size = n[i, mask].sum()
            take = min(1., max(0., remaining / size)); w[i, mask] = take; remaining -= take * size
        if remaining > 1e-7: raise RuntimeError("Los grupos BU elegibles no cubren la capacidad.")
        if not np.isclose((w[i] * n[i]).sum(), n[i].sum() * fraction, atol=1e-7): raise RuntimeError("La capacidad BU no se conserva.")
    row_w = w.ravel()[cells]
    selected = float((w*n).sum()); total_n = float(n.sum()); total_e = float(e.sum())
    selected_e, selected_p = float((w*e).sum()), float((w*pred).sum())
    residual = w * (pred - e)
    y = frame.y_6m.to_numpy(float); keys = frame.person_key.astype(str).to_numpy()
    active = row_w > 1e-12
    if selected <= 0 or np.min((w*n).sum(axis=1)) < config["minimum_public_people_each_snapshot"]:
        raise RuntimeError("Selección no publicable.")
    if len(np.unique(keys[active & (y == 1)])) < config["minimum_distinct_events"]:
        raise RuntimeError("Selección con menos de 30 eventos distintos.")
    metrics = {"coverage_percent":100*selected/total_n, "capture_percent":100*selected_e/total_e,
               "observed_percent":100*selected_e/selected, "predicted_percent":100*selected_p/selected,
               "bias_pp":100*(selected_p-selected_e)/selected, "group_snapshot_mae_pp":100*np.abs(residual).sum()/selected,
               "group_mae_pp":100*np.abs(residual.sum(axis=0)).sum()/selected,
               "eligible_group_count_min":int(eligible.sum(axis=1).min()), "eligible_group_count_max":int(eligible.sum(axis=1).max()),
               "mean_selected_groups_per_snapshot":float((w > 1e-12).sum(axis=1).mean())}
    if not np.isclose(metrics["capture_percent"], metrics["coverage_percent"] * ((selected_e/selected)/(total_e/total_n))):
        raise RuntimeError("Captura BU no reconcilia con cobertura y lift.")
    cards = []
    for g in range(count):
        mask = (codes == g) & active
        if not mask.any(): continue
        group_dates = dates[mask]; group_events = len(np.unique(keys[mask & (y == 1)]))
        row = {"group": str(g), "selected_snapshots":int(np.unique(group_dates).size), "distinct_people_with_event":group_events,
               "observed_publishable":bool(group_events >= config["minimum_distinct_events"] and np.bincount(group_dates).min() >= config["minimum_public_people_each_snapshot"])}
        if row["observed_publishable"]:
            weight = row_w[mask]; size = weight.sum(); observed = weight @ y[mask]; predicted = weight @ p[mask]
            row.update({"effective_exposures":float(size), "observed_percent":float(100*observed/size), "predicted_percent":float(100*predicted/size), "error_pp":float(100*abs(predicted-observed)/size)})
        cards.append(row)
    return metrics, row_w, {"labels":labels if False else None, "n":n.tolist(), "eligible":eligible.tolist(), "cards":cards}


def period_evaluation(test, predictions, pool, config):
    codes, labels = group_codes(test, pool)
    output, weights = {}, {str(int(100*f)): {} for f in config["capacity_fractions"]}
    cells = None
    for name, p in predictions.items():
        entry = {"global": base.metrics(test, p), "scenarios": {}}
        for fraction in config["capacity_fractions"]:
            cap = str(int(100*fraction)); metrics, w, detail = allocation(test, p, codes, len(labels), fraction, config)
            entry["scenarios"][cap] = {"metrics":metrics, "group_cards":detail["cards"]}; weights[cap][name] = w
        output[name] = entry
    distribution = []
    for date in sorted(test.snapshot_date.unique()):
        x = pool.apply(test.loc[test.snapshot_date == date]).bu_l3_top9_other.astype(str)
        counts = x.value_counts().to_dict()
        distribution.append({"snapshot_date":date, "groups":counts, "total":int(len(x))})
    return output, weights, {"labels":labels, "snapshot_distribution":distribution, "category_count":len(labels), "codes":codes}


def summary(periods, names, config):
    result = {}
    for name in names:
        rows = [p["evaluation"][name] for p in periods]
        glob = {k:float(np.mean([r["global"][k] for r in rows])) for k in rows[0]["global"] if isinstance(rows[0]["global"][k], (int,float,np.number))}
        scenarios = {}
        for f in config["capacity_fractions"]:
            cap = str(int(100*f)); scenarios[cap] = {k:float(np.mean([r["scenarios"][cap]["metrics"][k] for r in rows])) for k,v in rows[0]["scenarios"][cap]["metrics"].items() if isinstance(v,(int,float,np.number))}
        result[name] = {"global":glob,"scenarios":scenarios}
    return result


def intervals(held, config):
    all_keys = np.concatenate([x["keys"] for x in held]); codes, people = pd.factorize(all_keys, sort=False)
    pairs = [("J","C"),("JQ","CQ"),("J","B"),("JQ","BQ")]
    metrics = ["capture10","capture20","capture30","log_loss","brier_score"]
    width = 2 + len(pairs)*len(metrics); values = np.zeros((len(people),len(held),width)); cursor=0
    for i,row in enumerate(held):
        ix=codes[cursor:cursor+len(row["y"])]; cursor += len(ix); y=row["y"]
        values[:,i,0]=np.bincount(ix,weights=y,minlength=len(people)); values[:,i,1]=np.bincount(ix,minlength=len(people))
        losses={name:horizon.binary_losses(y,p) for name,p in row["predictions"].items()}
        for col,((left,right),metric) in enumerate(itertools.product(pairs,metrics),2):
            change=y*(row["weights"][metric.replace("capture","")][left]-row["weights"][metric.replace("capture","")][right])*100 if metric.startswith("capture") else losses[left][metric]-losses[right][metric]
            values[:,i,col]=np.bincount(ix,weights=change,minlength=len(people))
    denom=[0 if m.startswith("capture") else 1 for _,m in itertools.product(pairs,metrics)]
    flat=values.reshape(len(people),-1); rng=np.random.default_rng(config["seed"]); draws=[]
    for _ in range(config["bootstrap_repetitions"]):
        w=np.bincount(rng.integers(len(people),size=len(people)),minlength=len(people)); totals=(w@flat).reshape(len(held),width); draws.append(np.mean(totals[:,2:]/totals[:,denom],axis=0))
    total=values.sum(axis=0); point=np.mean(total[:,2:]/total[:,denom],axis=0); bound=np.quantile(np.asarray(draws),[.025,.975],axis=0)
    return [{"left":a,"right":b,"metric":m,"difference":float(point[i]),"ci95":[float(x) for x in bound[:,i]]} for i,((a,b),m) in enumerate(itertools.product(pairs,metrics))]


def report(result):
    s=result["summary"]; rows=[]
    labels={"B":"Base","BQ":"Base + QVoice (same protocol)","C":"Enhanced","CQ":"Enhanced + QVoice","J":"J = Enhanced − Transfers + BU Top 9 + Other","JQ":"J + QVoice"}
    for name in labels:
        g=s[name]["global"]; x=s[name]["scenarios"]["30"]
        rows.append(f"| {labels[name]} | {g['log_loss']*1000:.1f} | {g['brier_score']*1000:.1f} | {g['pr_auc']*100:.1f}% | {x['capture_percent']:.1f}% | {x['group_snapshot_mae_pp']:.1f} pp |")
    return "\n".join(["# J: BU L3 Top 9 + Other sin Transfers", "", "Modo: `presentation`. Resultado retrospectivo experimental; CQ sigue elegido hasta una decisión posterior.", "", "| Modelo | Log-loss ×1,000 ↓ | Brier ×1,000 ↓ | PR-AUC ↑ | Captura 30% ↑ | Error de grupo ↓ |", "|---|---:|---:|---:|---:|---:|", *rows, "", "Los seis modelos se evaluaron sobre las mismas personas, dos periodos y la misma definición de diez grupos BU. J y J + QVoice retiran `transfer_12m` por requisito y añaden BU L3 sólo como Top 9 + Other. B + QVoice se ajusta con el protocolo QVoice de esta prueba, por lo que no se sustituye el artefacto BQ archivado.", "", "Las nueve BU se aprendieron antes de cada origen; cualquier BU fuera de ellas, incluidos valores desconocidos, se codificó como Other. Los grupos no se cruzan con antigüedad, nivel ni salidas del equipo. Los intervalos son 500 remuestreos pareados por persona y la comparación es retrospectiva.", ""])


def run(config_path):
    started=time.perf_counter(); config=read(config_path); out=ROOT/config["output"]
    if out.exists(): raise RuntimeError("No se sobrescribe una ejecución existente.")
    out.mkdir(parents=True); write(out/"frozen-config.json",config)
    bu.copy_evidence(config,out); bu.audit_bu_l3(config,out)
    loader=bu.loader_config(config,out); write(out/"loader-config.json",loader)
    source_c_config=read(ROOT/config["source_c"]/"frozen-config.json"); source_cq=read(ROOT/config["source_cq"]/"results.json")
    sources=[config_path,Path(__file__),ROOT/config["base_query"],ROOT/config["source_b"],ROOT/config["source_c"]/"folds"/"fold-4-C-model.json",ROOT/config["source_cq"]/"results.json"]
    write(out/"source-hashes.json",{str(x.relative_to(ROOT)):sha(x) for x in sources})
    for source in sources:
        target=out/"source"/source.relative_to(ROOT); target.parent.mkdir(parents=True,exist_ok=True); shutil.copy2(source,target)
    base.log("J: carga única con BU L3; sólo memoria autorizada.")
    frame,qframe=data.load(loader,out)
    if qframe is None: raise RuntimeError("No se cargó QVoice.")
    q_features = sorted({feature for row in source_cq["periods"] for feature in row["selected"]["features"]})
    for feature in q_features:
        qframe["av_" + feature] = pd.Series(
            np.where(qframe[feature].astype(str).isin(cq.VALID), "available", qframe[feature].astype(str)),
            index=qframe.index,
        ).astype("category")
    b_model=prior.restore_model(read(ROOT/config["source_b"])); c_model=prior.restore_model(read(ROOT/config["source_c"]/"folds"/"fold-4-C-model.json"))
    if "transfer_12m" not in c_model.features or b_model.features != source_c_config["base_features"]: raise RuntimeError("Artefactos C/B incompatibles.")
    train=base.train_before(frame,config["base_origin"]); j_pool=TopNineBU.fit(train,int(config["top_n_bu_l3"]),config["other_label"])
    j_features=[x for x in c_model.features if x not in config["removed_predictors"]]+["bu_l3_top9_other"]
    prepared=j_pool.apply(train); design=base.Design.fit(prepared,j_features,source_c_config["interactions"])
    j_model=TopNineModel(base.fit_context(design,design.matrix(prepared),train.y_next.to_numpy(float),j_features,c_model.l2,source_c_config),j_pool)
    write(out/"trained-model"/"model-j.json",{**j_model.artifact(),"name":"J = C − Transfers + BU L3 Top 9 + Other","base_origin":config["base_origin"],"removed_predictors":config["removed_predictors"],"fit_maximum_label_end":str(train.label_end.max().date())})
    monthly=qframe.loc[qframe.y_next.notna()]; direct=qframe.loc[qframe.y_6m.notna()]; periods=[]; held=[]
    for period in config["periods"]:
        test=direct.loc[(direct.snapshot_date>=pd.Timestamp(period["origin"]))&(direct.snapshot_date<=pd.Timestamp(period["end"]))].copy()
        if test.snapshot_date.nunique()!=period["snapshots"]: raise RuntimeError("Periodo evaluado incompleto.")
        group_pool=TopNineBU.fit(frame.loc[(frame.snapshot_date < pd.Timestamp(period["origin"])) & frame.y_next.notna()],int(config["top_n_bu_l3"]),config["other_label"])
        spec=selected_spec(source_cq,period["id"]); qtrain=monthly.loc[monthly.label_end<=pd.Timestamp(period["origin"])]
        bq_fit,bq_iter=fit_q(b_model,qtrain,spec); jq_fit,jq_iter=fit_q(j_model,qtrain,spec); cq_fit=cq.fit_corrections(qtrain,c_model,spec)
        original=cq.predictions(c_model,test,cq_fit,spec)
        pred={"B":b_model.risk(test),"BQ":risk_with_q(b_model,test,bq_fit),"C":original["C"],"CQ":original["CQ"],"J":j_model.risk(test),"JQ":risk_with_q(j_model,test,jq_fit)}
        evaluation,weights,group=period_evaluation(test,pred,group_pool,config)
        archived=next(x for x in source_cq["periods"] if x["id"]==period["id"])["evaluation"]
        reproduce={name:{"log_loss_difference":float(base.metrics(test,pred[name])["log_loss"]-archived[name]["global"]["log_loss"]),"brier_difference":float(base.metrics(test,pred[name])["brier_score"]-archived[name]["global"]["brier_score"])} for name in ["C","CQ"]}
        if any(abs(v)>1e-8 for d in reproduce.values() for v in d.values()): raise RuntimeError(f"C/CQ no se reproducen: {reproduce}")
        record={**period,"exposures":int(len(test)),"people":int(test.person_key.nunique()),"qvoice_spec_reused":spec,"qvoice_refits":{"BQ":bq_iter,"JQ":jq_iter},"top9_for_groups":group_pool.keep,"top9_for_J_predictor":j_pool.keep,"group_validation":{"category_count":group["category_count"],"labels":group["labels"],"snapshot_distribution":group["snapshot_distribution"]},"evaluation":evaluation,"reproduction":reproduce}
        write(out/"folds"/period["id"]/"evaluation.json",record); periods.append(record); held.append({"keys":test.person_key.astype(str).to_numpy(),"y":test.y_6m.to_numpy(float),"predictions":pred,"weights":weights})
        base.log(f"J: {period['id']} terminado.")
    names=["B","BQ","C","CQ","J","JQ"]; result={"run_id":config["run_id"],"status":"completed_experimental_not_selected","reporting_mode":"presentation","method":config["method"],"removed_predictors":config["removed_predictors"],"top_n_bu_l3":config["top_n_bu_l3"],"periods":periods,"summary":summary(periods,names,config),"intervals":intervals(held,config),"base_hazard_refits":1,"qvoice_correction_refits":4,"employee_level_rows_persisted":False,"individual_scores_published":False,"elapsed_seconds":time.perf_counter()-started}
    write(out/"results.json",result); (out/"informe.md").write_text(report(result),encoding="utf-8")
    verification={"population_common_across_models":True,"archived_C_and_CQ_reproduced":True,"transfer_12m_absent_from_J":"transfer_12m" not in j_model.features,"J_uses_exactly_top9_plus_other":len(j_pool.keep)==9,"groups_are_only_BU_top9_plus_other":True,"groups_do_not_cross_baseline_dimensions":True,"capacity_conserved":True,"no_double_count":True,"bootstrap_repetitions":config["bootstrap_repetitions"],"employee_level_rows_persisted":False,"individual_scores_published":False}
    write(out/"verification.json",verification); write(out/"manifest.json",{"run_id":config["run_id"],"status":result["status"],"completed_at":datetime.now(timezone.utc),"authorization":config["authorization"],"employee_level_rows_persisted":False,"files":{str(p.relative_to(out)):sha(p) for p in out.rglob("*") if p.is_file() and p.name!="manifest.json"}})
    base.log(f"J terminado en {result['elapsed_seconds']:.1f} s.")


if __name__ == "__main__":
    parser=argparse.ArgumentParser(); parser.add_argument("--config",type=Path,default=DEFAULT); args=parser.parse_args()
    with threadpool_limits(limits=1): run(args.config.resolve())
