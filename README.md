\# Explainable Hybrid Resume–Job Matching Engine



An evidence-aware hybrid AI/ML system that matches resumes to job descriptions at the \*\*requirement level\*\* instead of relying on simple keyword overlap or whole-document similarity.



\## Problem



Traditional resume matching can fail when:



\* A resume says `React` while a job asks for `Frontend Development`.

\* A candidate has an adjacent skill such as `Angular`, but the system treats it as either an exact match or no match.

\* A resume repeats job-description keywords without providing evidence of real capability.

\* A candidate explicitly states that they have no experience with a required technology.

\* A critical requirement is missing even though the overall resume appears similar.



The goal is not to find the resume that looks most similar to the job description.



The goal is to determine whether the candidate has \*\*evidence that they can satisfy each requirement\*\*, and explain why.



\## Solution



The system uses an explainable hybrid pipeline:



\*\*Resume / Job Description → Evidence \& Requirement Extraction → Skill Normalization → Skill Relationship Analysis → Requirement-Level Matching → Evidence-Aware Scoring → Critical Requirement Guardrails → Confidence Estimation → Explainable Recommendation\*\*



\### Matching Relationships



The engine distinguishes between:



\* `EXACT` — direct skill match

\* `CAPABILITY` — candidate evidence demonstrates the required capability

\* `RELATED` — related technology or ecosystem evidence

\* `TRANSFERABLE` — transferable skill evidence

\* `ADJACENT` — nearby but non-equivalent skill

\* `SEMANTIC` — semantic evidence supports the requirement

\* `PARTIAL` — incomplete support

\* `MISSING` — no supporting evidence



| Candidate Evidence            | Job Requirement      | Relationship |

| ----------------------------- | -------------------- | ------------ |

| React                         | React                | EXACT        |

| React                         | Frontend Development | CAPABILITY   |

| Angular                       | React                | ADJACENT     |

| Redux                         | React                | RELATED      |

| HTML                          | Kubernetes           | MISSING      |

| No experience with Kubernetes | Kubernetes           | MISSING      |



\## Evidence-Aware Design



The system does not treat a keyword as proof of experience.



Evidence is extracted from resume context and classified using:



\* Section

\* Source type

\* Action performed

\* Context

\* Polarity

\* Learning status

\* Evidence strength



For example:



`Currently learning Kubernetes`



is not treated the same as:



`Deployed production services using Kubernetes`.



Negative evidence is also handled. Statements such as:



`No experience with Kubernetes`



cannot create a positive match.



\## Scoring and Guardrails



Requirements are evaluated individually using multiple signals:



\* Relationship quality

\* Semantic similarity

\* Evidence strength

\* Requirement importance

\* Relevant experience



The overall score is then passed through guardrails.



Critical `MUST\_HAVE` gaps can reduce the decision-adjusted score and prevent a recommendation even when other requirements are supported.



The system reports \*\*confidence separately from fit score\*\*.



This prevents a high similarity score from being interpreted as high certainty.



\## Evaluation



The project includes deterministic automated tests and adversarial evaluation.



\### Adversarial Benchmark



An 8-case adversarial benchmark covers:



\* Synonyms

\* Capability relationships

\* Adjacent technologies

\* Related technologies

\* Unrelated skills

\* Negated experience

\* Learning status

\* Keyword stuffing



| Approach         | Accuracy |

| ---------------- | -------: |

| Keyword baseline |    50.0% |

| TF-IDF baseline  |    50.0% |

| Hybrid matcher   |   100.0% |



These results are from the project's \*\*small, deliberately constructed adversarial benchmark\*\* and are not presented as a general industry benchmark.



Benchmark artifacts are available under:



`evaluation/experiments/`



and:



`evaluation/baselines/baseline\_results.txt`



\### Automated Tests



The adversarial/integration test suite currently passes:



\*\*10 tests passed\*\*



The tests verify semantic relationships, missing requirements, and negated evidence.



\## Example Decision



For a candidate evaluated against a demanding data-science role, the engine can produce:



\* Decision Fit: `23.91 / 100`

\* Raw Fit: `33.91 / 100`

\* Evidence Coverage: `41%`

\* Confidence: `40%`

\* Recommendation: `NOT\_RECOMMENDED`



The important part is not only the score.



The system explains that the candidate has several supported or transferable matches but is missing a critical must-have requirement.



\## Technology Stack



\### Backend



\* Python

\* FastAPI

\* Pydantic

\* Sentence Transformers

\* scikit-learn

\* NumPy

\* Pandas



\### Frontend



\* React

\* Vite

\* JavaScript

\* CSS



\### Matching



\* Deterministic skill normalization

\* Skill relationship taxonomy

\* Sentence-transformer semantic similarity

\* Evidence-aware requirement matching

\* Rule-based guardrails

\* Explainable recommendation generation



\## API



\### Health Check



`GET /health`



\### Match Candidate to Job



`POST /matches`



Example request:



```json

{

&#x20; "candidate\_id": "C\_RANK\_000002",

&#x20; "job\_id": "J\_JSS\_000833"

}

```



The response contains:



\* Fit score

\* Confidence

\* Evidence coverage

\* Recommendation

\* Strong matches

\* Partial/transferable matches

\* Missing requirements

\* Critical gaps

\* Requirement-level explanations



Interactive API documentation is available through FastAPI Swagger at:



`/docs`



\## Frontend



The React frontend provides an interactive demonstration where a candidate ID and job ID can be submitted to view the complete explainable matching result.



Run the frontend:



```bash

cd frontend

npm install

npm run dev

```



\## Backend Setup



Create a virtual environment:



```bash

python -m venv .venv

```



Windows PowerShell:



```powershell

.venv\\Scripts\\Activate.ps1

```



Install dependencies:



```powershell

pip install -r requirements.txt

```



Start the API:



```powershell

python -m uvicorn app.main:app --reload

```



API:



`http://127.0.0.1:8000`



Swagger:



`http://127.0.0.1:8000/docs`



\## Data Pipeline



The repository intentionally does not commit raw or processed datasets.



The local data pipeline is:



\*\*Raw Resume / Job Data → Dataset Audit → Preprocessing → Evidence Extraction → Requirement Extraction → Skill Normalization → Requirement Matching → Scoring + Guardrails → Explanation\*\*



Dataset and preprocessing artifacts are generated locally under:



`data/`



Raw and processed data are excluded from Git using `.gitignore`.



\## Project Structure



```text

Resume\_matching\_engine/

│

├── app/

│   ├── extraction/

│   ├── matching/

│   ├── pipeline/

│   ├── scoring/

│   ├── explanation/

│   ├── skills/

│   └── main.py

│

├── evaluation/

│   ├── baselines/

│   └── experiments/

│

├── frontend/

│   └── src/

│

├── scripts/

│   ├── audit\_datasets.py

│   ├── preprocess\_datasets.py

│   ├── extract\_evidence\_dataset.py

│   └── extract\_jd\_requirements\_dataset.py

│

├── tests/

│   └── adversarial/

│

├── requirements.txt

├── .gitignore

└── README.md

```



\## Design Principles



1\. Requirement-level matching instead of whole-document similarity.

2\. Evidence before explanation.

3\. Embeddings support matching but do not prove experience.

4\. Adjacent skills are not treated as exact equivalents.

5\. Negated evidence cannot produce a positive match.

6\. Critical requirements receive explicit guardrails.

7\. Fit and confidence are separate signals.

8\. Keyword frequency is not treated as evidence of capability.

9\. Every recommendation should be explainable.

10\. Evaluation includes adversarial cases designed to expose keyword-matching failures.



\## Limitations



This is a hackathon-grade prototype rather than a production hiring system.



Important limitations include:



\* The adversarial benchmark is intentionally small.

\* Skill relationships are currently taxonomy/rule assisted.

\* Resume parsing quality depends on document structure.

\* Some requirements require richer domain knowledge.

\* Confidence calibration can be improved with a larger human-labeled dataset.

\* Production deployment would require stronger data governance, privacy controls, monitoring, and human oversight.



\## Future Improvements



\* Larger human-annotated evaluation dataset

\* Learned skill relationship model

\* Better experience/date extraction

\* Confidence calibration and reliability curves

\* Human feedback loop

\* Fairness and bias monitoring

\* PostgreSQL-backed production storage

\* Authentication and role-based access

\* Production observability and model monitoring



\## Core Idea



> The goal isn't to find the resume that looks most similar to the job description. The goal is to determine whether the candidate has evidence that they can satisfy the requirements — and explain that decision.



