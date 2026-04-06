# main
import os
import shutil , time
from flask import Flask, request, render_template
from agents.jd_summarizer import JDSummarizerAgent
from agents.cv_parser import CVParserAgent
from agents.matcher import MatcherAgent
from agents.scheduler import SchedulerAgent

app = Flask(__name__)
UPLOAD_FOLDER = "uploaded_cvs"
# Always reset the upload folder
if os.path.exists(UPLOAD_FOLDER):
    shutil.rmtree(UPLOAD_FOLDER)
os.makedirs(UPLOAD_FOLDER)

@app.route("/", methods=["GET", "POST"])
def shortlist():
    results = []

    if request.method == "POST":
        jd_text = request.form["job_description"]
        count = int(request.form["candidate_count"])
        uploaded_files = request.files.getlist("cv_files")

        # Clear previously uploaded files
        for f in os.listdir(UPLOAD_FOLDER):
            os.remove(os.path.join(UPLOAD_FOLDER, f))

        # Save uploaded PDFs
        saved_paths = []
        for file in uploaded_files:
            if file and file.filename.endswith(".pdf"):
                path = os.path.join(UPLOAD_FOLDER, file.filename)
                file.save(path)
                saved_paths.append(path)

        # Process Job Description
        lines = jd_text.strip().splitlines()
        job_title_extracted = lines[0].strip() if lines else "Job Role"
        jd_agent = JDSummarizerAgent({job_title_extracted: jd_text})
        jd_titles, jd_texts_clean = jd_agent.get_summary()
        
        # Process CVs
        cv_agent = CVParserAgent()
        matcher = MatcherAgent()
        num = 1
        for path in saved_paths:
            parsed = cv_agent.parse(path)
            match_title, score = matcher.match(parsed["clean_text"], jd_texts_clean, jd_titles)
            results.append({
                "pdf_number": num,
                "name": parsed["name"],
                "email": parsed["email"],
                "phone": parsed["phone"],
                "job_match": match_title,
                "score": round(score * 100, 2)
            })
           
            num += 1

        # Sort and get top N
        results.sort(key=lambda r: r["score"], reverse=True)
        results = results[:count]

        # ✅ Send emails to selected candidates
        # my passkey name = HackTrail , passkey = "rmft fmil xtld ohwl"
        scheduler = SchedulerAgent("priyaganjawala2512@gmail.com", "rzrmhdjvzxaskfkn")
        for r in results:
            scheduler.schedule_interview(
                to_email=r["email"],
                candidate_name=r["name"],
                job_role=r["job_match"]
            )
            time.sleep(1.5) # To avoid hitting the rate limit
    return render_template("shortlist_ui.html", results=results)
if __name__ == "__main__":
    app.run(debug=True)


