import json
from pathlib import Path
from jinja2 import Environment, FileSystemLoader

def generate_dari_qa_report(survey, form_results, output_html_path):
    """Generates the official Dari HTML QA report based on Jinja2 template."""
    # 1. Prepare Metadata
    total_students = len(form_results)
    
    metadata = {
        "teacher_name": survey.professor or "نامعلوم",
        "subject": survey.subject or "نامعلوم",
        "department": survey.department or "نامعلوم",
        "semester": f"{survey.semester} / {survey.academic_year}",
        "total_students": total_students
    }
    
    if total_students == 0:
        raise ValueError("No results available to generate report.")

    # 2. Count Answers (Q1 to Q14)
    # Format: "Q1": [Yes_Count, Partial_Count, No_Count]
    results_counts = {f"Q{i}": [0, 0, 0] for i in range(1, 15)}
    
    for fr in form_results:
        answers = fr.answers()  # List of answers, e.g., ["Yes", "No", "Somewhat", ...]
        for i in range(14):
            if i >= len(answers):
                continue
            ans = answers[i]
            if ans == "Yes":
                results_counts[f"Q{i+1}"][0] += 1
            elif ans == "Somewhat":
                results_counts[f"Q{i+1}"][1] += 1
            elif ans == "No":
                results_counts[f"Q{i+1}"][2] += 1

    # 3. Data Processing & The "Advanced Analysis" Logic
    chart_data_positive = []
    chart_data_neutral = []
    chart_data_negative = []

    analysis_insights = [] # We will dynamically add text analysis here

    for key, values in results_counts.items():
        q_total = sum(values)
        if q_total == 0:
            yes_pct = partial_pct = no_pct = 0.0
        else:
            yes_pct = (values[0] / q_total) * 100
            partial_pct = (values[1] / q_total) * 100
            no_pct = (values[2] / q_total) * 100

        # REVERSE CODING FOR Q11
        if key == "Q11":
            # For Q11, 'No' is positive, 'Yes' is negative
            chart_data_positive.append(round(no_pct))
            chart_data_neutral.append(round(partial_pct))
            chart_data_negative.append(round(yes_pct))
            
            if no_pct == 100:
                analysis_insights.append("✅ <strong>تمرکز عالی بر درس:</strong> ۱۰۰٪ محصلان تایید کرده‌اند که استاد در جریان صنف به موضوعات غیرمرتبط نمی‌پردازد که نشان‌دهنده مدیریت عالی زمان است.")
        else:
            chart_data_positive.append(round(yes_pct))
            chart_data_neutral.append(round(partial_pct))
            chart_data_negative.append(round(no_pct))

        # AUTOMATED ANALYSIS RULES (Quality Assurance Engine)
        if key == "Q4" and yes_pct <= 60 and q_total > 0:
            analysis_insights.append(f"⚠️ <strong>هشدار میتودولوژی (Q4):</strong> تنها {round(yes_pct)}٪ محصلان تدریس را کاملاً قابل فهم دانسته‌اند. پیشنهاد می‌گردد روش‌های تشریحی بازنگری شود.")
        
        if key == "Q1" and yes_pct == 100 and q_total > 0:
            analysis_insights.append("⭐ <strong>نقطه قوت (Q1):</strong> کورس پالیسی در آغاز سمستر با موفقیت کامل (۱۰۰٪) تشریح شده است.")
            
        if key == "Q14" and yes_pct >= 90 and q_total > 0:
            analysis_insights.append("✅ <strong>تکنالوژی (Q14):</strong> استفاده استاد از تکنالوژی معلوماتی در سطح عالی قرار دارد.")

    # Calculate Overall Score (Average of all Positive outcomes)
    if chart_data_positive:
        overall_score = round(sum(chart_data_positive) / len(chart_data_positive))
    else:
        overall_score = 0

    # 4. Pass data to the HTML Template
    template_dir = Path(__file__).parent / "templates"
    env = Environment(loader=FileSystemLoader(str(template_dir)))
    template = env.get_template('qa_template.html')

    html_output = template.render(
        meta=metadata,
        overall_score=overall_score,
        positive_data=json.dumps(chart_data_positive),
        neutral_data=json.dumps(chart_data_neutral),
        negative_data=json.dumps(chart_data_negative),
        insights=analysis_insights
    )

    # 5. Save the generated HTML
    with open(output_html_path, 'w', encoding='utf-8') as f:
        f.write(html_output)

    return output_html_path
