#!/usr/bin/env python3
"""Auto-grader สำหรับ Nmap Lab — รันโดย GitHub Actions"""
import yaml, sys, json
from pathlib import Path

ANSWER_KEYS = {
    "lab01": {
        "total": 20,
        "questions": {
            "q1_target_ip":     {"answers": ["192.168.40.145"], "score": 3},
            "q2_time_seconds":  {"answers": ["4.33"], "score": 1.5},
            "q2_closed_ports":  {"answers": ["994"], "score": 1.5},
            "q4_os":            {"answers": ["windows"], "score": 2},
            "q4_is_vm":         {"answers": ["yes"], "score": 2},
            "q5_attack_name":   {"answers": ["eternalblue"], "score": 2},
            "q5_attack_year":   {"answers": ["2017"], "score": 2},
        }
    },
    "lab02": {
        "total": 20,
        "questions": {
            "q1_hostname":         {"answers": ["scanme.nmap.org"], "score": 1.5},
            "q1_actual_ip":        {"answers": ["45.33.32.156"], "score": 1.5},
            "q4_version":          {"answers": ["openssh 6.6.1p1", "6.6.1p1"], "score": 2},
        }
    },
    "lab03": {
        "total": 20,
        "questions": {
            "q1_total_ports":    {"answers": ["65535"], "score": 1},
            "q1_time_seconds":   {"answers": ["96.42"], "score": 1},
            "q2_filtered_count": {"answers": ["65525"], "score": 2},
            "q3_open_ports":     {"answers": ["22,53,80,443,3306,8080", "22, 53, 80, 443, 3306, 8080"], "score": 3},
            "q3_closed_ports":   {"answers": ["21,25,110,3389", "21, 25, 110, 3389"], "score": 3},
        }
    },
    "lab04": {
        "total": 20,
        "questions": {
            "q1_feature_count": {"answers": ["4"], "score": 4},
            "q3_os":            {"answers": ["linux"], "score": 2},
            "q3_hop_count":     {"answers": ["1"], "score": 2},
        }
    },
    "lab05": {
        "total": 20,
        "questions": {}
    },
}

def normalize(text):
    if text is None:
        return ""
    return str(text).strip().lower().replace("  ", " ")

def grade_lab(lab_id, student_file):
    if lab_id not in ANSWER_KEYS:
        return None, f"ไม่พบเฉลยสำหรับ {lab_id}"
    try:
        with open(student_file, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
    except Exception as e:
        return None, f"อ่านไฟล์ไม่ได้: {e}"
    if not data or "answers" not in data:
        return None, "ไม่พบ key 'answers'"

    key = ANSWER_KEYS[lab_id]
    student_answers = data.get("answers", {})
    student_id = data.get("student_id", "unknown")
    student_name = data.get("student_name", "unknown")

    if not key["questions"]:
        return {
            "student_id": student_id, "student_name": student_name, "lab": lab_id,
            "score": 0, "auto_gradable_max": 0, "lab_total": key["total"],
            "manual_grading": True, "results": []
        }, None

    results = []
    total_earned = 0
    auto_gradable_total = 0

    for q_key, q_data in key["questions"].items():
        correct_answers = [normalize(a) for a in q_data["answers"]]
        student_ans = normalize(student_answers.get(q_key, ""))
        q_score = q_data["score"]
        auto_gradable_total += q_score

        is_correct = student_ans in correct_answers
        if not is_correct and student_ans:
            is_correct = any(ca in student_ans or student_ans in ca
                           for ca in correct_answers if len(ca) > 3)

        earned = q_score if is_correct else 0
        total_earned += earned
        results.append({
            "question": q_key, "student_answer": str(student_answers.get(q_key, "")),
            "correct": is_correct, "earned": earned, "max": q_score
        })

    return {
        "student_id": student_id, "student_name": student_name, "lab": lab_id,
        "score": round(total_earned, 2), "auto_gradable_max": round(auto_gradable_total, 2),
        "lab_total": key["total"], "results": results
    }, None


def main():
    answers_dir = Path("answers")
    all_results = []
    total_score = 0
    total_max = 0

    print("=" * 60)
    print("📊 ผลการตรวจ Nmap Lab")
    print("=" * 60)

    for lab_num in range(1, 6):
        lab_id = f"lab{lab_num:02d}"
        lab_file = answers_dir / f"{lab_id}.yml"
        if not lab_file.exists():
            continue
        result, error = grade_lab(lab_id, lab_file)
        if error:
            print(f"\n❌ {lab_id}: {error}")
            continue
        all_results.append(result)

        if result.get("manual_grading"):
            print(f"\n📝 {lab_id.upper()} — {result['student_name']} ({result['student_id']})")
            print(f"   *** Lab นี้ครูตรวจด้วยตนเอง (ไม่ auto-grade) ***")
            continue

        total_score += result["score"]
        total_max += result["auto_gradable_max"]
        pct = (result["score"] / result["auto_gradable_max"] * 100) if result["auto_gradable_max"] > 0 else 0
        emoji = "✅" if pct >= 70 else "⚠️" if pct >= 50 else "❌"
        print(f"\n{emoji} {lab_id.upper()} — {result['student_name']} ({result['student_id']})")
        print(f"   คะแนน: {result['score']}/{result['auto_gradable_max']} ({pct:.1f}%)")
        for r in result["results"]:
            mark = "✓" if r["correct"] else "✗"
            print(f"     [{mark}] {r['question']}: {r['student_answer'][:50]} (+{r['earned']}/{r['max']})")

    print("\n" + "=" * 60)
    print(f"📈 สรุปรวม (เฉพาะ auto-grade): {round(total_score, 2)}/{round(total_max, 2)} คะแนน")
    print("   (Lab 05 ครูตรวจแยกต่างหาก)")
    print("=" * 60)

    with open("grade_results.json", "w", encoding="utf-8") as f:
        json.dump({"total_score": round(total_score, 2), "total_max": round(total_max, 2), "labs": all_results},
                   f, ensure_ascii=False, indent=2)

    sys.exit(0)

if __name__ == "__main__":
    main()
