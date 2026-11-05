import csv
import json
import pathlib
from qa.llm_eval.judge_reliability import (
    compute_cohen_kappa,
    bootstrap_cohen_kappa_ci,
    interpret_kappa,
    VALID_LABELS,
)
from sklearn.metrics import confusion_matrix

orig_path = pathlib.Path("qa/data/human_labels.csv")
blinded_path = pathlib.Path("qa/data/blinded_labeling_sheet.csv")

with open(orig_path, encoding="utf-8-sig") as f:
    orig_rows = list(csv.DictReader(f))

with open(blinded_path, encoding="utf-8-sig") as f:
    user_rows = list(csv.DictReader(f))

assert len(orig_rows) == len(user_rows) == 30

updated_rows = []
for idx, (orig, user) in enumerate(zip(orig_rows, user_rows)):
    q_orig = orig["question"].strip()
    q_user = user["question"].strip()
    if q_orig != q_user:
        print(f"Warning: row {idx+1} mismatch: {q_orig[:30]} vs {q_user[:30]}")
    row = dict(orig)
    row["human_label"] = user["user_label"].strip()
    row["notes"] = f"Human verified (user ground truth). {user.get('user_notes', '')}".strip()
    updated_rows.append(row)

# Write updated human_labels.csv
fieldnames = list(orig_rows[0].keys())
with open(orig_path, "w", encoding="utf-8", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(updated_rows)

print("Updated qa/data/human_labels.csv with genuine human labels.")

# Now compute statistics
all_human = [r["human_label"] for r in updated_rows]
all_judge = [r["judge_label"] for r in updated_rows]

total = len(updated_rows)
matches = sum(1 for h, j in zip(all_human, all_judge) if h == j)
overall_acc = round(matches / total, 4)
overall_kappa = compute_cohen_kappa(all_human, all_judge)
overall_ci_low, overall_ci_high = bootstrap_cohen_kappa_ci(all_human, all_judge)

print(f"Overall samples: {total}")
print(f"Overall matches: {matches}")
print(f"Overall accuracy: {overall_acc * 100:.2f}%")
print(f"Overall Cohen's Kappa: {overall_kappa} ({interpret_kappa(overall_kappa)})")
print(f"Bootstrap 95% CI: [{overall_ci_low}, {overall_ci_high}]")

by_lang = {}
for lang in ["en", "hi", "te"]:
    lang_rows = [r for r in updated_rows if r["language"] == lang]
    l_human = [r["human_label"] for r in lang_rows]
    l_judge = [r["judge_label"] for r in lang_rows]
    l_total = len(lang_rows)
    l_matches = sum(1 for h, j in zip(l_human, l_judge) if h == j)
    l_acc = round(l_matches / l_total, 4) if l_total > 0 else 0.0
    l_kappa = compute_cohen_kappa(l_human, l_judge)
    l_ci_low, l_ci_high = bootstrap_cohen_kappa_ci(l_human, l_judge)

    by_lang[lang] = {
        "sample_size": l_total,
        "matches": l_matches,
        "accuracy": l_acc,
        "cohen_kappa": l_kappa,
        "ci_95": [l_ci_low, l_ci_high],
        "interpretation": interpret_kappa(l_kappa),
        "note": "Per-language kappa on n=10 items has high variance and wide confidence intervals.",
    }
    print(f"\nLanguage: {lang.upper()} (n={l_total})")
    print(f"  Matches: {l_matches}/{l_total} ({l_acc * 100:.2f}%)")
    print(f"  Cohen's Kappa: {l_kappa} ({interpret_kappa(l_kappa)})")
    print(f"  Bootstrap 95% CI: [{l_ci_low}, {l_ci_high}]")

# Confusion matrix
present_labels = sorted(set(all_human + all_judge))
cm = confusion_matrix(all_human, all_judge, labels=present_labels).tolist()

results_data = {
    "provider": "mock",
    "model": "rule_based_judge",
    "embedder": "mock",
    "label_origin": "Human verified (job applicant ground truth)",
    "overall": {
        "total_samples": total,
        "matches": matches,
        "accuracy": overall_acc,
        "cohen_kappa": overall_kappa,
        "ci_95": [overall_ci_low, overall_ci_high],
        "interpretation": interpret_kappa(overall_kappa),
    },
    "by_language": by_lang,
    "confusion_matrix": {
        "labels": present_labels,
        "matrix": cm,
    },
    "disclaimer": "Ground-truth human labels provided by job applicant on blinded sample of 30 items. Per-language kappa on n=10 items has high variance and wide confidence intervals; overall kappa provides the statistically meaningful estimate."
}

with open("results/judge_reliability_results.json", "w", encoding="utf-8") as f:
    json.dump(results_data, f, indent=2)

print("\nSaved updated results to results/judge_reliability_results.json")
