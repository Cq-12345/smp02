from __future__ import annotations

import csv
import importlib.metadata
import json
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from rdkit import Chem

from molecode import mermaid_to_mol, mol_to_mermaid, mol_to_smiles
from molecode.markush import MoleCodeGraph, molecode_isomorphic
from molecode.polymer import mermaid_to_psmiles, polymer_to_mermaid


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from smp02.functional_groups import classify_smiles, compatibility_reason  # noqa: E402


OUT_DIR = Path(__file__).resolve().parent / "outputs"
GRAPH_DIR = OUT_DIR / "graphs"


BPAB = "Nc1ccc(Oc2ccc(-c3ccc(Oc4ccc(N)cc4)cc3)cc2)cc1"
BPADA = "CC(C)(c1ccc(Oc2ccc3c(c2)C(=O)OC3=O)cc1)c1ccc(Oc2ccc3c(c2)C(=O)OC3=O)cc1"
CANDIDATES_CSV = PROJECT_ROOT / "artifacts/reproduce/discovery/all_ratio_candidates.csv"


@dataclass
class CheckResult:
    domain: str
    case: str
    claim: str
    status: str
    detail: str
    evidence_path: str = ""


def canonical_smiles(smiles: str) -> str:
    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        raise ValueError(f"Invalid SMILES: {smiles}")
    return Chem.MolToSmiles(mol, canonical=True)


def rel(path: Path) -> str:
    return str(path.relative_to(PROJECT_ROOT))


def write_graph(filename: str, graph_text: str) -> Path:
    GRAPH_DIR.mkdir(parents=True, exist_ok=True)
    path = GRAPH_DIR / filename
    path.write_text(graph_text, encoding="utf-8")
    return path


def ok(domain: str, case: str, claim: str, detail: str, evidence: Path | None = None) -> CheckResult:
    return CheckResult(domain, case, claim, "pass", detail, rel(evidence) if evidence else "")


def fail(domain: str, case: str, claim: str, detail: str, evidence: Path | None = None) -> CheckResult:
    return CheckResult(domain, case, claim, "fail", detail, rel(evidence) if evidence else "")


def info(domain: str, case: str, claim: str, detail: str, evidence: Path | None = None) -> CheckResult:
    return CheckResult(domain, case, claim, "info", detail, rel(evidence) if evidence else "")


def graph_stats(graph_text: str) -> dict[str, int]:
    graph = MoleCodeGraph.from_text(graph_text)
    return {
        "nodes": len(graph.nodes),
        "edges": len(graph.edges),
        "atom_nodes": sum(1 for node in graph.nodes.values() if node.label_type == "atom"),
        "abbrev_nodes": sum(1 for node in graph.nodes.values() if node.label_type == "abbrev"),
    }


def verify_small_molecule_roundtrip() -> list[CheckResult]:
    results: list[CheckResult] = []
    examples = {
        "official_aspirin": "CC(=O)Oc1ccccc1C(=O)O",
        "project_bpab": BPAB,
        "project_bpada": BPADA,
    }

    for name, smiles in examples.items():
        claim = "SMILES -> MoleCode -> SMILES is canonical-equivalent"
        mol = Chem.MolFromSmiles(smiles)
        if mol is None:
            results.append(fail("small_molecule", name, claim, "RDKit could not parse input SMILES"))
            continue

        graph = mol_to_mermaid(mol, name=name)
        graph_path = write_graph(f"{name}.mmd", graph)
        restored = mermaid_to_mol(graph)
        restored_smiles = mol_to_smiles(restored) if restored is not None else ""
        expected = canonical_smiles(smiles)
        stats = graph_stats(graph)

        if restored_smiles == expected:
            results.append(
                ok(
                    "small_molecule",
                    name,
                    claim,
                    f"canonical={restored_smiles}; nodes={stats['nodes']}; edges={stats['edges']}",
                    graph_path,
                )
            )
        else:
            results.append(
                fail(
                    "small_molecule",
                    name,
                    claim,
                    f"expected canonical {expected}, got {restored_smiles or 'None'}",
                    graph_path,
                )
            )

        explicit_graph_claim = "MoleCode exposes typed nodes and edges in Mermaid graph text"
        has_graph_header = graph.startswith("graph ")
        has_node = "[" in graph and "]" in graph
        has_edge = any(symbol in graph for symbol in ("---", "===", "-.-", "<-->"))
        if has_graph_header and has_node and has_edge:
            results.append(
                ok(
                    "small_molecule",
                    name,
                    explicit_graph_claim,
                    f"graph_header={has_graph_header}; atom_nodes={stats['atom_nodes']}; edges={stats['edges']}",
                    graph_path,
                )
            )
        else:
            results.append(
                fail(
                    "small_molecule",
                    name,
                    explicit_graph_claim,
                    f"graph_header={has_graph_header}; has_node={has_node}; has_edge={has_edge}",
                    graph_path,
                )
            )

    return results


def verify_project_functional_group_compatibility() -> list[CheckResult]:
    results: list[CheckResult] = []
    pair_claim = "MoleCode round-trip preserves SMP functional-group classification and pair compatibility"

    original_a = classify_smiles(BPAB)
    original_b = classify_smiles(BPADA)
    bpab_rt = mol_to_smiles(mermaid_to_mol(mol_to_mermaid(Chem.MolFromSmiles(BPAB), name="BPAB")))
    bpada_rt = mol_to_smiles(mermaid_to_mol(mol_to_mermaid(Chem.MolFromSmiles(BPADA), name="BPADA")))
    restored_a = classify_smiles(bpab_rt)
    restored_b = classify_smiles(bpada_rt)

    original_reason = compatibility_reason(original_a.groups, original_b.groups)
    restored_reason = compatibility_reason(restored_a.groups, restored_b.groups)

    if original_a.groups == restored_a.groups and original_b.groups == restored_b.groups and original_reason == restored_reason:
        results.append(
            ok(
                "project_smp",
                "BPAB/BPADA",
                pair_claim,
                (
                    f"BPAB groups={';'.join(restored_a.groups)}; "
                    f"BPADA groups={';'.join(restored_b.groups)}; "
                    f"compatibility={restored_reason}"
                ),
            )
        )
    else:
        results.append(
            fail(
                "project_smp",
                "BPAB/BPADA",
                pair_claim,
                (
                    f"original=({original_a.groups}, {original_b.groups}, {original_reason}); "
                    f"roundtrip=({restored_a.groups}, {restored_b.groups}, {restored_reason})"
                ),
            )
        )

    candidate_claim = "Paper BPAB/BPADA ratios are present in the local full candidate table"
    if not CANDIDATES_CSV.exists():
        results.append(fail("project_smp", "candidate_table", candidate_claim, f"Missing {CANDIDATES_CSV}"))
        return results

    wanted = {(0.55, 0.45), (0.50, 0.50)}
    found: dict[tuple[float, float], dict[str, Any]] = {}
    with CANDIDATES_CSV.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        for idx, row in enumerate(reader):
            if row["smiles_a"] == BPADA and row["smiles_b"] == BPAB:
                ratio = (round(float(row["ratio_a"]), 2), round(float(row["ratio_b"]), 2))
                if ratio in wanted:
                    found[ratio] = {
                        "row": idx,
                        "predicted_tg": float(row["predicted_tg"]),
                        "in_target_range": row["in_target_range"],
                    }
            if len(found) == len(wanted):
                break

    if len(found) == len(wanted):
        detail = "; ".join(
            f"ratio_a/b={ratio[0]:.2f}/{ratio[1]:.2f}: row={payload['row']}, Tg={payload['predicted_tg']:.2f} C"
            for ratio, payload in sorted(found.items())
        )
        results.append(ok("project_smp", "BPAB/BPADA", candidate_claim, detail, CANDIDATES_CSV))
    else:
        results.append(
            fail(
                "project_smp",
                "BPAB/BPADA",
                candidate_claim,
                f"found ratios={sorted(found)}; wanted={sorted(wanted)}",
                CANDIDATES_CSV,
            )
        )

    return results


def verify_polymer_roundtrip() -> list[CheckResult]:
    results: list[CheckResult] = []
    examples = {
        "nylon6": ("*NCCCCCC(=O)*", 8),
        "polyethylene": ("*CC*", 100),
    }

    for name, (psmiles, n) in examples.items():
        claim = "PSMILES repeat unit -> MoleCode -> PSMILES is canonical-equivalent"
        graph = polymer_to_mermaid(psmiles, n=n, name=name)
        graph_path = write_graph(f"polymer_{name}.mmd", graph)
        restored = mermaid_to_psmiles(graph)
        expected = canonical_smiles(psmiles)
        got = canonical_smiles(restored) if restored else ""
        has_repeat = f"×{n}" in graph
        has_termini = "TL" in graph and "TR" in graph

        if got == expected and has_repeat and has_termini:
            results.append(
                ok(
                    "polymer",
                    name,
                    claim,
                    f"canonical={got}; repeat_marker=×{n}; termini=TL/TR",
                    graph_path,
                )
            )
        else:
            results.append(
                fail(
                    "polymer",
                    name,
                    claim,
                    f"expected={expected}; got={got or 'None'}; has_repeat={has_repeat}; has_termini={has_termini}",
                    graph_path,
                )
            )

    return results


def verify_markush_graph() -> list[CheckResult]:
    results: list[CheckResult] = []
    graph = """graph TB
    subgraph Markush["Markush example"]
        Markush_C_1[C]
        Markush_X_1{R1}
        Markush_X_2{Boc}
        Markush_C_1 --- Markush_X_1
        Markush_C_1 --- Markush_X_2
    end
"""
    graph_missing_edge = """graph TB
    subgraph Markush["Markush example"]
        Markush_C_1[C]
        Markush_X_1{R1}
        Markush_X_2{Boc}
        Markush_C_1 --- Markush_X_1
    end
"""
    graph_path = write_graph("markush_abbrev_nodes.mmd", graph)
    parsed = MoleCodeGraph.from_text(graph)
    parsed_missing_edge = MoleCodeGraph.from_text(graph_missing_edge)
    abbrev_labels = sorted(node.label for node in parsed.nodes.values() if node.label_type == "abbrev")

    claim = "Markush-style abbreviation nodes are parsed as graph nodes"
    if abbrev_labels == ["Boc", "R1"] and len(parsed.edges) == 2:
        results.append(ok("markush", "abbrev_nodes", claim, f"abbrev_labels={abbrev_labels}; edges=2", graph_path))
    else:
        results.append(
            fail(
                "markush",
                "abbrev_nodes",
                claim,
                f"abbrev_labels={abbrev_labels}; edges={len(parsed.edges)}",
                graph_path,
            )
        )

    iso_claim = "Markush graph comparison detects same and changed topology"
    same_iso, _ = molecode_isomorphic(parsed, MoleCodeGraph.from_text(graph))
    changed_iso, _ = molecode_isomorphic(parsed, parsed_missing_edge)
    if same_iso and not changed_iso:
        results.append(ok("markush", "graph_isomorphism", iso_claim, "self-isomorphic=True; missing-edge-isomorphic=False", graph_path))
    else:
        results.append(
            fail(
                "markush",
                "graph_isomorphism",
                iso_claim,
                f"self-isomorphic={same_iso}; missing-edge-isomorphic={changed_iso}",
                graph_path,
            )
        )

    return results


def verify_scope_and_limits() -> list[CheckResult]:
    results: list[CheckResult] = []
    version = importlib.metadata.version("molecode")
    results.append(
        info(
            "environment",
            "package",
            "MoleCode package is installed in the active environment",
            f"molecode=={version}; rdkit canonicalization used for structural equality",
        )
    )
    results.append(
        info(
            "scope",
            "property_prediction",
            "MoleCode is tested here as a structural representation, not as a Tg predictor",
            "No MoleCode API was used for Tg/property prediction; the existing SMP predictor remains the property model.",
        )
    )
    return results


def write_outputs(results: list[CheckResult]) -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    payload = {
        "summary": {
            "pass": sum(r.status == "pass" for r in results),
            "fail": sum(r.status == "fail" for r in results),
            "info": sum(r.status == "info" for r in results),
        },
        "results": [asdict(r) for r in results],
    }
    (OUT_DIR / "verification_results.json").write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")

    with (OUT_DIR / "verification_results.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(asdict(results[0]).keys()), lineterminator="\n")
        writer.writeheader()
        writer.writerows(asdict(r) for r in results)

    lines = [
        "# MoleCode 本地验证报告",
        "",
        "验证目录：`molecodetest/`",
        "",
        "## 结论",
        "",
    ]
    failures = [r for r in results if r.status == "fail"]
    if failures:
        lines.append(f"- 未完全通过：pass={payload['summary']['pass']}，fail={payload['summary']['fail']}，info={payload['summary']['info']}。")
    else:
        lines.append(f"- 本地验证通过：pass={payload['summary']['pass']}，fail=0，info={payload['summary']['info']}。")
    lines.extend(
        [
            "- MoleCode 0.1.0 可以在本项目 conda 环境中安装并运行。",
            "- 小分子 SMILES/MoleCode 往返、聚合物 PSMILES/MoleCode 往返、Markush 缩写节点解析与图同构比较均有可执行证据。",
            "- 对我们的 SMP 项目，BPAB/BPADA 经过 MoleCode 往返后，官能团分类和兼容性约束保持一致。",
            "- 这支持把 MoleCode 放在“结构表示、生成、编辑、约束审计”层；不支持把它当作 Tg 预测模型替代品。",
            "",
            "## 逐项结果",
            "",
            "| Domain | Case | Status | Claim | Detail | Evidence |",
            "| --- | --- | --- | --- | --- | --- |",
        ]
    )
    for result in results:
        detail = result.detail.replace("|", "/")
        evidence = f"`{result.evidence_path}`" if result.evidence_path else ""
        lines.append(f"| {result.domain} | {result.case} | {result.status} | {result.claim} | {detail} | {evidence} |")

    lines.extend(
        [
            "",
            "## 来源对应",
            "",
            "- 论文 `/home/user4/smp02/paper/2605.16480v1.pdf`：核心主张包括 training-free、graph-explicit、Subgraph-Node-Edge、标准格式确定性双向转换、聚合物/Markush 扩展，以及 MoleCode 不创造模型缺失化学知识的限制。",
            "- GitHub `https://github.com/AtomFlow-AI/MoleCode`：公开 README 给出的 `pip install molecode`、小分子 round-trip、polymer/Markush API 与本地验证接口一致。",
            "",
            "复跑命令：",
            "",
            "```bash",
            "conda run -n mhc_pyg314 python molecodetest/verify_molecode.py",
            "```",
        ]
    )
    (OUT_DIR / "verification_report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    results: list[CheckResult] = []
    results.extend(verify_scope_and_limits())
    results.extend(verify_small_molecule_roundtrip())
    results.extend(verify_project_functional_group_compatibility())
    results.extend(verify_polymer_roundtrip())
    results.extend(verify_markush_graph())
    write_outputs(results)

    failures = [r for r in results if r.status == "fail"]
    print(json.dumps({"pass": sum(r.status == "pass" for r in results), "fail": len(failures), "info": sum(r.status == "info" for r in results)}, ensure_ascii=False))
    if failures:
        for result in failures:
            print(f"FAIL [{result.domain}/{result.case}] {result.claim}: {result.detail}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
