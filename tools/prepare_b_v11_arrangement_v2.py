"""Reconcilia el rótulo abreviado V11 con su categoría fuente completa."""
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]


def main():
    source=ROOT/'queries/profiles/engineering_b_v11_categories_person_month_20261011.sql'
    target=source.with_name(source.stem+'_v2.sql')
    audit=ROOT/'queries/audits/engineering_b_v11_arrangement_20261011_v2.sql'
    contract_path=ROOT/'config/b_playbook_v11_contracts/arrangement-v2.json'
    if target.exists() or audit.exists() or contract_path.exists():
        raise RuntimeError('La revisión ya existe.')
    def correct(sql):
        return sql.replace("NULLIF(UPPER(TRIM(work_arrangement)),'') AS arrangement",
           "NULLIF(REPLACE(REPLACE(UPPER(TRIM(work_arrangement)),'–','-'),'—','-'),'') AS arrangement") \
           .replace("'SHORT-TERM REMOTE WORK'","'INTERIM MODIFIED - SHORT-TERM REMOTE WORK'")
    target.write_text(correct(source.read_text(encoding='utf-8')),encoding='utf-8')
    text=correct((ROOT/'queries/audits/engineering_b_v11_arrangement_20261011.sql').read_text(encoding='utf-8'))
    text=text.replace('\nFROM encoded GROUP BY',",\n SUM(CASE WHEN work_arrangement_v11='Short-Term Remote Work' THEN 1 ELSE 0 END) AS short_remote_rows,\n"+
        " SUM(CASE WHEN (arrangement LIKE 'INTERIM MODIFIED%SHORT%TERM REMOTE WORK') <>\n"+
        " (work_arrangement_v11='Short-Term Remote Work') THEN 1 ELSE 0 END) AS pattern_mapping_mismatches\nFROM encoded GROUP BY")
    audit.write_text(text,encoding='utf-8')
    contract=json.loads((ROOT/'config/b_playbook_v11_contracts/arrangement.json').read_text(encoding='utf-8'))
    contract.update(id='arrangement-v2',query=audit.relative_to(ROOT).as_posix(),
                    source_query=target.relative_to(ROOT).as_posix())
    contract['zero_fields'].append('pattern_mapping_mismatches')
    contract['positive_fields'].append('short_remote_rows')
    contract['history']+=' La primera implementación no identificaba el rótulo completo; esta revisión usa la correspondencia explícita de tools/build_distribution_html_v7.py y la contrasta con un patrón independiente.'
    contract['acceptance_rule']+=' Se exige además presencia del grupo de remoto temporal y cero diferencias frente al patrón independiente.'
    contract['supersedes']='v11-arrangement.json: prueba mecánica de un mapping incompleto; no apta para declarar equivalencia con V11.'
    contract_path.write_text(json.dumps(contract,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print('Revisión preparada: remoto temporal usa la categoría fuente completa.')


if __name__=='__main__':
    main()
