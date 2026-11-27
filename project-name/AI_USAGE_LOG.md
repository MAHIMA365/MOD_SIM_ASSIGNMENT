# AI Usage Log

## Purpose

This log records AI assistance used while preparing and improving this
simulation project. It is for academic transparency and does not replace the
student's independent review or submission declaration.

The student remains responsible for checking the accuracy of all project
content, following the assignment requirements and approving the submitted
files.

## AI Tool Used

| Item | Details |
|---|---|
| AI system | GitHub Copilot, using the Copilot SDK in Visual Studio Code |
| Report date | 27 November 2026 |
| Assistance type | Code and documentation editing, document generation, project inspection and test execution |
| Files inspected | README, theory, user guide, verification CSV, experiment CSV files, notebooks, source code and test files |
| Human approval | The student requested each listed deliverable and may review or change the result before submission |

## Scope of this Log

This record covers AI assistance provided during the visible assistance
session beginning on 27 November 2026. It does not claim to describe AI use
from earlier development that occurred before this session or by a different
person or tool.

## Complete Session Log

| Date and time | Student request | AI task performed | Result and project impact |
|---|---|---|---|
| 27 November 2026, about 12:07 | Asked whether a report should be made and how to guide report creation. | Reviewed the project README, theory, user guide, verification data and experiment structure. | Confirmed that the project had results suitable for an academic report. |
| 27 November 2026, about 12:07 | Selected PDF as the report format. | Checked for a PDF-generation package, installed ReportLab when it was unavailable, and created a report-generation script in the session workspace. | Prepared the PDF report content and inserted theory, experiments, figures, verification and references. |
| 27 November 2026, about 12:19 | Asked for a simple report summary. | Produced a plain-English summary of bays, queue results, high-demand behaviour and conclusions. | Provided an understandable explanation separate from the technical PDF. |
| 27 November 2026, about 12:29 | Asked whether the work matched the assignment. | Searched project files and compared the implementation and documents with the assignment-style deliverables visible in the workspace. | Identified completed work and remaining presentation issues, including placeholders, README wording and notebook selection. |
| 27 November 2026, about 12:41 | Asked to complete the user guide. | Replaced the placeholder user guide with complete instructions for opening the demo, controls, stability, visualisation, outputs, examples and limitations. | Completed [`USER_GUIDE.md`](USER_GUIDE.md). |
| 27 November 2026, about 12:54 | Asked to update the README and theory verification section. | Updated the README's status wording and quick-start instructions. Replaced planned verification content in THEORY.md with completed verification evidence and pass results. | Removed obsolete “pending” and “not run” statements from both files. |
| 27 November 2026, about 13:06 | Requested a complete AI usage log. | Created this log and added a README link for academic transparency. | Added the present AI assistance record to the project. |

## Documents Created or Revised

| File | Work performed |
|---|---|
| [`Bus_Halt_Queue_Simulation_Report.pdf`](Bus_Halt_Queue_Simulation_Report.pdf) | Generated an academic PDF report containing a summary, model, equations, methods, results, verification, limitations and references. |
| [`USER_GUIDE.md`](USER_GUIDE.md) | Replaced placeholder content with the complete browser-demo guide. |
| [`README.md`](README.md) | Updated project status, notebook instructions, verification links, limitations and AI assistance section. |
| [`THEORY.md`](THEORY.md) | Updated the verification section from planned checks to completed checks with obtained values and pass status. |
| [`AI_USAGE_LOG.md`](AI_USAGE_LOG.md) | Added this transparency record. |

## Technical Assistance

AI assistance was used to inspect and summarise:

- M/M/1 and M/M/2 theory
- Discrete-event simulation implementation
- Arrival and service sensitivity experiments
- One-bay and two-bay comparison experiments
- Replication confidence intervals
- Event accounting and passenger conservation
- Analytical verification
- Python and browser consistency checks
- Project README, theory and user documentation

AI assistance was also used to:

- Generate a report PDF
- Identify missing or outdated placeholder text
- Recommend report structure and simple-English explanations
- Run the automated Python test suite
- Inspect the output files and figures

## Verification of AI Work

The project test suite was run with the Python environment in the project
virtual environment. The result was:

```text
69 passed
```

The AI also inspected the following evidence:

- [`verification_results.csv`](verification_results.csv)
- [`data/python_javascript_consistency.csv`](data/python_javascript_consistency.csv)
- [`data/experiment_1_arrival_sensitivity.csv`](data/experiment_1_arrival_sensitivity.csv)
- [`data/experiment_3_bay_comparison.csv`](data/experiment_3_bay_comparison.csv)
- [`figures/verification.png`](figures/verification.png)
- [`figures/bay_model_comparison.png`](figures/bay_model_comparison.png)
- [`figures/arrival_waiting_time.png`](figures/arrival_waiting_time.png)
- [`figures/arrival_queue_length.png`](figures/arrival_queue_length.png)
- [`figures/arrival_server_utilization.png`](figures/arrival_server_utilization.png)
- [`figures/paired_bay_benefit_confidence_intervals.png`](figures/paired_bay_benefit_confidence_intervals.png)

Running or inspecting these checks does not remove the student's
responsibility to verify the report and submission.

## AI-Generated Content That Requires Review

Before submission, the student should review:

1. The PDF report's student name, student number and submission details.
2. The report's title and assignment-specific formatting requirements.
3. The notebook used for submission.
4. All numerical results and uncertainty statements.
5. The references and citation format.
6. The README and user-guide links.
7. Whether GitHub Pages publication or a screenshot is required.

## Human Responsibilities

The student or project author is responsible for:

- Understanding the submitted model and theory
- Checking every result against the source code and CSV files
- Ensuring the work follows the exact assignment instructions
- Replacing placeholder personal details if required
- Selecting the correct notebook and final PDF
- Running and validating the final submission
- Declaring the AI assistance truthfully

## Declaration for the Student

The following wording may be included in the student's assignment declaration:

> AI assistance was used through GitHub Copilot in Visual Studio Code for
> project-document review, report generation, documentation editing and
> summarising existing verification and experiment results. The AI-generated
> output was checked against project source files and automated tests. I
> reviewed and remain responsible for the submitted work.
