import json
from pathlib import Path
from jinja2 import Environment, FileSystemLoader

def to_persian_num(number):
    persian_digits = "۰۱۲۳۴۵۶۷۸۹"
    return "".join(persian_digits[int(d)] if d.isdigit() else d for d in str(number))

def generate_dari_qa_report(survey, form_results, output_html_path):
    """Generates the official Dari HTML QA report based on Jinja2 template."""
    total_students = len(form_results)
    
    metadata = {
        "teacher_name": survey.professor or "نامعلوم",
        "subject": survey.subject or "نامعلوم",
        "department": survey.department or "نامعلوم",
        "semester": f"{survey.semester} / {survey.academic_year}",
        "total_students": to_persian_num(total_students),
        "total_students_raw": total_students
    }
    
    if total_students == 0:
        raise ValueError("No results available to generate report.")

    results_counts = {f"Q{i}": [0, 0, 0] for i in range(1, 15)}
    
    for fr in form_results:
        answers = fr.answers()
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

    chart_data_positive = []
    chart_data_neutral = []
    chart_data_negative = []

    questions_info = {
        1: "آیا در آغاز سمستر کورس پالیسی تشریح گردیده است؟",
        2: "آیا تدریس مطابق کورس پالیسی صورت گرفته است؟",
        3: "آیا مواد درسی برای شما معرفی شده و موجود است؟",
        4: "آیا تدریس استاد قابل فهم است؟",
        5: "آیا از میتود تدریس استاد راضی هستید؟",
        6: "آیا استاد محصلان را در تدریس سهم میسازد؟",
        7: "آیا از سلوک و رویه اکادمیک استاد راضی هستید؟",
        8: "آیا استاد با پلان درسی منظم داخل صنف میشود؟",
        9: "آیا استاد به سوالات شما جواب قناعتبخش میدهد؟",
        10: "آیا استاد پابند به اصول، وقت و زمان معین میباشد؟",
        11: "<strong>(معکوس)</strong> آیا استاد به موضوعات غیرمرتبط تماس میگیرد؟",
        12: "آیا مشکلات درسی شما توسط استاد حل میگردد؟",
        13: "آیا از شیوههای ارزیابی استاد راضی هستید؟",
        14: "آیا استاد از تکنالوژی معلوماتی استفاده مینماید؟",
    }
    
    categories = [
        {"name": "۱. نصاب، پلانگذاری و مواد درسی", "q_nums": [1, 2, 3, 8]},
        {"name": "۲. میتودولوژی تدریس و تعامل صنف", "q_nums": [4, 5, 6, 9]},
        {"name": "۳. مدیریت صنف و مسلکی بودن", "q_nums": [7, 10, 11]},
        {"name": "۴. ارزیابی، تکنالوژی و حل مشکلات", "q_nums": [12, 13, 14]},
    ]
    
    table_data = []

    for key, values in results_counts.items():
        q_total = sum(values)
        if q_total == 0:
            yes_pct = partial_pct = no_pct = 0.0
        else:
            yes_pct = (values[0] / q_total) * 100
            partial_pct = (values[1] / q_total) * 100
            no_pct = (values[2] / q_total) * 100

        if key == "Q11":
            chart_data_positive.append(round(no_pct))
            chart_data_neutral.append(round(partial_pct))
            chart_data_negative.append(round(yes_pct))
        else:
            chart_data_positive.append(round(yes_pct))
            chart_data_neutral.append(round(partial_pct))
            chart_data_negative.append(round(no_pct))

    if chart_data_positive:
        overall_score = round(sum(chart_data_positive) / len(chart_data_positive))
    else:
        overall_score = 0

    for cat in categories:
        cat_data = {"name": cat["name"], "questions": []}
        for q_num in cat["q_nums"]:
            q_key = f"Q{q_num}"
            vals = results_counts[q_key]
            q_total = sum(vals)
            yes_c, partial_c, no_c = vals
            
            if q_total == 0:
                y_p = p_p = n_p = 0
            else:
                y_p = round((yes_c / q_total) * 100)
                p_p = round((partial_c / q_total) * 100)
                n_p = round((no_c / q_total) * 100)
                
            if q_num == 11:
                green_pct, green_c = n_p, no_c
                yellow_pct, yellow_c = p_p, partial_c
                red_pct, red_c = y_p, yes_c
                suffix_green = " <br><small>(نخیر)</small>"
            else:
                green_pct, green_c = y_p, yes_c
                yellow_pct, yellow_c = p_p, partial_c
                red_pct, red_c = n_p, no_c
                suffix_green = ""
                
            cat_data["questions"].append({
                "num": to_persian_num(q_num),
                "text": questions_info[q_num],
                "green_text": f"{to_persian_num(green_pct)}٪ ({to_persian_num(green_c)}){suffix_green}",
                "yellow_text": f"{to_persian_num(yellow_pct)}٪ ({to_persian_num(yellow_c)})",
                "red_text": f"{to_persian_num(red_pct)}٪ ({to_persian_num(red_c)})",
                "green_bg": "bg-green" if green_pct > 0 else "",
                "yellow_bg": "bg-yellow" if yellow_pct > 0 else "",
                "red_bg": "bg-red" if red_pct > 0 else ""
            })
        table_data.append(cat_data)

    template_dir = Path(__file__).parent / "templates"
    env = Environment(loader=FileSystemLoader(str(template_dir)))
    env.filters['persian_num'] = to_persian_num
    
    template = env.get_template('qa_template.html')

    html_output = template.render(
        meta=metadata,
        overall_score=to_persian_num(overall_score),
        positive_data=json.dumps(chart_data_positive),
        neutral_data=json.dumps(chart_data_neutral),
        negative_data=json.dumps(chart_data_negative),
        table_data=table_data
    )

    with open(output_html_path, 'w', encoding='utf-8') as f:
        f.write(html_output)

    return output_html_path
