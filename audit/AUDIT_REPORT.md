# Data / variable feasibility audit — HTOPS Mar-2026, SHED 2025, EWCS 2024

Audit date: 2026-10-08. Target: CJAS special issue "AI, Future Skills, and Productivity" (deadline 2026-12-15).
No regressions, no draft, no causal claims.

## 0. READ FIRST: what this audit is and is not

**No microdata file, codebook PDF or questionnaire PDF was opened.** From the sandbox, census.gov, www2.census.gov,
federalreserve.gov and eurofound.europa.eu all returned 403 on CONNECT (organization network policy), for both `curl` and WebFetch.
I did not attempt to bypass this. Consequently:

- Every "usable N" below is **NOT COMPUTED**. Nothing was estimated from data.
- Everything stated here comes from **web-search summaries** of official pages (evidence tier **S**) and is a *lead to verify*, not a verified fact.
  Tier **U** = nothing found, unknown. Tier **F** (verified in file) = nothing yet.
- Search summaries are model-generated paraphrases. Quotation marks around survey wording below mean "as reported by a summary", not "copied from the questionnaire".
- Verdicts are therefore **provisional** and conditional on named kill-checks that the scripts in `audit/` perform in ~1 hour once files are in hand.

Reproducibility: `audit/src/` (fetch, generic stage-1/stage-2 runner), `audit/config/` (source URLs, construct regexes, map templates),
`audit/tests/run_tests.sh` (logic test on synthetic data; passes). See `audit/README.md`.

### Two unblock routes
1. Add to the environment's allowed domains: `www.census.gov`, `www2.census.gov`, `www.federalreserve.gov`, `eurofound.europa.eu`, `ukdataservice.ac.uk`, `doc.ukdataservice.ac.uk` (Environment settings → Network access → Allowed domains), then I rerun in a new turn.
2. Run `00_fetch.py` + `run_audit.py` locally and commit/upload `audit/outputs/`; I will fill the tables from them.

---

## 1. US Census HTOPS, March 2026 (priority 1)

### Facts gathered (all tier S unless noted)
| Item | Finding | Source |
|---|---|---|
| Design | From March 2026 HTOPS is **cross-sectional** (earlier 2025 waves longitudinal). Consistent with your correction. Treat as cross-section; do not link to 2025 waves. | PUF-page summary |
| Collection window | 13–30 Mar 2026 → one wave spanning ~2.5 weeks; interview date/week variable existence **U** | PUF page |
| Sample | "about 136,000 households" (tip sheet) — this reads as **sample/invitations, not respondents or workers**; respondent N **U** | Tip Sheet 13 |
| Files | Each release = PUF + **separate replicate-weight file** + data dictionary | PUF page |
| File version risk | PUF **corrected 10 Sep 2026** with revised weights; Census story figures revised 24 Sep. Must pin download date + SHA-256 and use the corrected file. | Census story; May user notes |
| AI exposure | Workers asked about AI use for **11 job tasks**; AI defined broadly ("computational systems performing tasks typically associated with human intelligence", e.g. ML, NLP, virtual agents, voice recognition). **Not GenAI-specific.** | Census story |
| Headline | ~56% of workers used AI for ≥1 of 11 tasks (Census); a third-party post reports 51% on a different base → prevalence is **definition- and universe-sensitive**; reproduce before relying on any number | Census story; Substack |
| Task items | search/technical help 37%, writing 32%, idea generation 32%, interpret/summarise 31%, admin 27%; coding, customer support, logistics lower | Census story |
| Frequency | "last week" use: every day ~24%, some days ~46%, none ~31% (among ever-users) | Census story |
| Time saved | Among last-week users: "additional hours needed without AI" categories (<1h ≈25%, 1–2h ≈31%) | Census story |
| Employer encouragement/policy | **Not found** in any summary | — |
| Skills/training, autonomy/job design | **Not found**; HTOPS is a household survey, expect none or one-off items | — |
| Variance | Pulse historically used Fay-BRR with 80 replicates (ρ = 0.5 ⇒ factor 4/80), but a secondary source cites ρ≈0.5005; **HTOPS value must be read from the March documentation** | secondary |

### A. Variable dictionary (March 2026 file — none verified; variable names U)
| Construct | Variable | Wording | Coding | Universe | Usable N | Limitation |
|---|---|---|---|---|---|---|
| Total sample | – | – | – | all respondents | NOT COMPUTED | – |
| Employed/eligible | U | U | U | U | NOT COMPUTED | definition of "worker" (employed last week? incl. self-employed?) decides the 51% vs 56% gap |
| Any AI use at work (≥1 of 11 tasks) | U | AI defined broadly (S) | U | workers (S) | NOT COMPUTED | not GenAI; includes voice recognition/virtual agents |
| Task-level AI use ×11 | U | U (verbatim not found) | U | U | NOT COMPUTED | skip logic may put "no" vs "missing" in different cells |
| Last-week frequency | U | U | 3 categories (S) | AI users (S) | NOT COMPUTED | conditional on use; "last week" ≠ habitual |
| Hours saved / extra hours w/o AI | U | U | ordinal bins (S) | last-week users | NOT COMPUTED | self-report, counterfactual recall, selected sample, no quality measure |
| Quality / output | U | – | – | – | – | likely absent |
| Skills / training | U | – | – | – | – | likely absent |
| Autonomy / job design | U | – | – | – | – | likely absent |
| Employer encouragement/policy | U | – | – | – | – | **not found**; if absent, HTOPS cannot address "who is allowed/encouraged" |
| Occupation / industry | U | – | – | – | – | HPS-style files historically carry only coarse groups, if any; check |
| Demographics | U | – | – | – | – | HPS-style: age, sex, race/ethnicity, education, household size/income bins expected (U) |
| Earnings | U | – | – | – | – | household income *bins* expected, not individual earnings (U) |
| Weights / replicates | U | – | – | – | – | separate file (S); merge key U; replicate count/ρ U |
| Interview date/month | U | – | – | – | – | single wave; week may exist |
| Person/panel ID | U | – | – | – | – | even if an ID exists, March 2026 is cross-section (S) → no linkage |
| Missing coding | U | – | – | – | – | Census convention is negative codes (e.g. −99/−88) — **assumption, verify** |

### B. Candidate estimands the data *could* support (conditional on checks)
1. Weighted distribution of AI task breadth (count of 11 tasks) and last-week frequency across worker groups (education, age, household income band, any occupation/industry grouping). Descriptive/associational only.
2. Among last-week AI users, association between task profile (e.g. writing/analysis vs search) and reported hours saved. Conditional-on-use, descriptive only.

### C. Fatal / major risks
- **Selection into outcome**: hours-saved is asked only of last-week users → no non-user comparison; any "productivity gain" is conditional on adoption.
- **Measurement**: broad AI definition (not GenAI); self-reported time savings; counterfactual-hours recall.
- **No employer, skills, or job-design variables** (not found): the file may not speak to "future skills" at all. This is the main scientific risk for a CJAS skills/productivity special issue.
- **Coarse controls**: occupation/industry/earnings likely coarse or absent.
- **Temporal**: one 2.5-week cross-section; no pre-period, no trajectory.
- **Contribution risk**: Census already published the headline tabulations (story, tables); novelty must come from cross-classifications the tables do not offer.
- **Version risk**: corrected/revised PUF; Census-vs-third-party prevalence discrepancy; risk of building on a superseded file.
- **Inference**: replicate-weight merge and ρ/R must be right or SEs are wrong (the script requires them explicitly).
- **Access**: public, but not reachable from sandbox; no registration expected (S).

### D. Verdict: **AUDIT FURTHER** (leaning NO-GO unless kill-checks pass)
Kill (→ NO-GO) if any: (i) no occupation/industry detail beyond ≤5 broad groups **and** no employer/skills items; (ii) worker N < ~5,000 or AI-user N < ~1,500 after valid-code filtering; (iii) frequency/hours items cover <~1,000 users; (iv) replicate weights cannot be merged 1:1 or documentation gives no ρ/R.

---

## 2. Federal Reserve SHED 2025 (priority 2)

### Facts gathered (tier S; from summaries of Fed Appendix A and the May-2026 report)
| Item | Finding |
|---|---|
| Fieldwork | 17–28 Oct 2025 (single survey; cross-sectional public file). Respondent N **not retrieved** (U). |
| **D50** | Defines generative AI (creates text, images, audio, video from prompts; examples **ChatGPT, Gemini, Midjourney**; do not count AI results from search engines) and asks whether R **used it at their job last month**. Yes=1/No=0. **Universe: those who worked last month.** |
| **D51** | How often used at job last month (several frequency categories, from multiple times per day down to <1 day per week). **Universe: D50 = Yes only.** |
| **D52** | Banked agree/disagree grid, **universe: everyone who worked last month** (so *non-users also answer*). Six statements as summarised: saves time; improves quality; enables new tasks; **employer encourages its use**; availability will improve my career; worried about AI replacing my job. |
| **User vs non-user wording** | Non-users (D50 = No) get an inserted preface: although not currently using AI at work, give your view of the technology *for jobs like yours*. So the **same statements are factual-experience items for users and hypothetical/attitudinal items for non-users**. Exact statement wording: **U** (snippet truncated; see Appendix A page). |
| Published results | ~25% of workers used GenAI last month; among users 81% agree saves time, 52% quality, 55% new tasks; among *all* workers 44% agree saves time (hence non-user answers are included); 20% of all workers worry about replacement; graduate-degree workers >4× as likely as ≤HS to use. |
| Not found | skills match, training, autonomy/job-design, task-level AI items, panel/ID structure, replicate weights, month of interview (single fielding window ⇒ none useful). |

### A. Variable dictionary (file variable names U; D50–D52 are questionnaire item numbers)
| Construct | Variable | Wording | Coding | Universe | Usable N | Limitation |
|---|---|---|---|---|---|---|
| Total sample | – | – | – | all | NOT COMPUTED | – |
| Worked last month | U | U | U | all | NOT COMPUTED | the *D50 universe* is "worked last month", not an LFS employed concept |
| GenAI use at work | D50 | defined GenAI; "used … at your job last month"; exclude search-engine AI (S) | 1/0 (S) | worked last month | NOT COMPUTED | 1-month window; single binary; self-defined by definition text |
| Frequency | D51 | how often last month (S) | ordinal categories | D50=1 | NOT COMPUTED | users only; categories U |
| Task-level use | – | – | – | – | – | **absent** (none found) |
| Saves time | D52 item | "saves time" (S) | Likert agree/disagree (levels U) | all who worked | NOT COMPUTED | user=experience, non-user=hypothetical |
| Quality | D52 item | "improves quality" (S) | same | same | NOT COMPUTED | same |
| New tasks | D52 item | "enables new tasks" (S) | same | same | NOT COMPUTED | same |
| Employer encouragement | D52 item | "employer encourages its use" (S) | same | same | NOT COMPUTED | single perceived item; no policy/provision detail; reverse causality with use possible |
| Career / displacement worry | D52 items | (S) | same | same | NOT COMPUTED | attitudes, not outcomes |
| Skills / training | U | – | – | – | – | none found in AI block; check rest of SHED (education, credentials) |
| Autonomy / job design | U | – | – | – | – | probably absent; SHED has employment/job-quality items (U) |
| Occupation / industry | U | – | – | – | – | SHED historically has coarse occupation/industry (U) — verify |
| Demographics / income | U | – | – | – | – | SHED has age, sex, race, education, income categories (from prior waves; **verify**) |
| Weights | U | – | – | – | – | SHED typically ships population weights; **no replicate weights expected** (assumption) → SEs via linearisation/Taylor needs strata/PSU, likely unavailable |
| Interview date | – | – | – | – | – | one 12-day window |
| Person ID / panel linkage | U | – | – | – | – | public file expected cross-sectional; repeated-wave linkage not possible for GenAI (items new in 2025) |
| Missing coding | U | – | – | – | – | assumption: −1 = refused/skip; **verify** |

### B. Candidate estimands
1. Weighted GenAI use (D50) and intensity (D51) by worker characteristics and by perceived employer encouragement (D52). Associational.
2. Among users only, association between intensity (D51) and agreement that GenAI saves time / improves quality / enables new tasks (D52). Perception outcomes, user-conditional.

### C. Fatal / major risks
- **Perceived, not measured, productivity** — all D52 outcomes are attitudes.
- **Non-user D52 answers are hypothetical** → never pool users and non-users on D52 without an explicit flag; do not compare "agree saves time" across the D50 split.
- **Reverse causality / common-cause** between employer encouragement and use (same-wave, self-report).
- **Universe**: "worked last month" is looser than employment; self-employed/gig treatment U.
- **Sample size**: user N drives power; prevalence ~25% × (worked-last-month N, **U**). Frequency categories × covariates may be thin.
- **No skills/training/autonomy variables, no task-level items** → thin on the "Future Skills" theme.
- **Inference**: replicate weights probably absent; design-based SEs approximate.
- **Contribution risk**: Fed's report already gives the headline cuts.
- Access: public, no registration expected (S); not verified.

### D. Verdict: **AUDIT FURTHER** (cleanest and fastest, but narrow)
Kill (→ NO-GO) if: (i) D50–D52 not in the public file or D52 absent for non-users in the file; (ii) AI-user N < ~800 or D51 non-missing < ~700; (iii) no occupation or industry variable at all and no employer variable beyond D52; (iv) weights missing.

---

## 3. Eurofound EWCS 2024 (priority 3)

### Facts gathered (tier S)
| Item | Finding |
|---|---|
| Access | 2024 cross-section and 1990–2024 harmonised file distributed via **UK Data Service** (the integrated 1991–2024 file is SN 7363, 9th release Mar 2026). **2024 cross-section SN: U.** Registration/licence terms (end-user licence, academic vs other users, approval turnaround): **U – must read on UKDS**. Questionnaire is public on Eurofound's site. |
| Design | EU27 + others; **first round mixing face-to-face and online (CAWI)** → mode effects. Respondent N/country N **U**. |
| AI item | Per a 2026 arXiv paper (secondary on secondary): "At work, do you use artificial intelligence that simplifies complex mental tasks or makes recommendations (e.g. ChatGPT, LLAMA, DALL-E, Midjourney, Jasper)?" — **verify against official questionnaire.** Note: this is a broad "AI" item with GenAI examples, **not a clean GenAI-only measure**. EU27 prevalence ≈12%. |
| Related items | technology-impact battery: "Technology has removed some of your tasks" / "…created new tasks for you" (binary, per same paper). |
| **Skills match / need for training** | Eurofound overview reports **overskilling 30%** and **13% say they need more training** ⇒ the *survey* contains these measures. **Whether they are in the public 2024 file with usable coding: U.** (This answers your correction request only at the survey level, not the file level.) |
| Repeated waves | Harmonised 1990–2024 file = **repeated cross-sections, not a panel**; the AI item exists only in 2024 ("first time") ⇒ no pre/post AI linkage possible. |
| Occupation/industry | ISCO/NACE coding report exists (S); detail level in public file **U**. |
| Weights | U (expect a design weight; replicate weights unlikely). Countries are strata; country FE and clustered SEs likely. |

### A. Variable dictionary (names U; none verified)
| Construct | Variable | Wording | Coding | Universe | Usable N | Limitation |
|---|---|---|---|---|---|---|
| Total sample | – | – | – | all | NOT COMPUTED | – |
| Employed/eligible | U | – | – | EWCS targets employed persons (S, standard) | NOT COMPUTED | includes self-employed; check employee-only job-design items |
| AI use | U | see above (S, secondary-of-secondary) | binary? U | U | NOT COMPUTED | not GenAI-only; wording must be checked |
| Frequency/intensity | U | – | – | – | – | none found |
| Task-level AI | – | – | – | – | – | none; only tech removed/created tasks |
| Productivity/time-saving/quality | – | – | – | – | – | **none found** (EWCS is not a productivity survey) |
| Skills match / training need | U | – | – | U | NOT COMPUTED | exists in survey (S); file presence U |
| Training received | U | – | – | – | – | EWCS usually has paid/own-account training items (prior rounds; verify) |
| Autonomy / job design | U | – | – | – | – | EWCS strength historically (task order, pace, methods, learning, complexity, intensity); verify items |
| Employer encouragement/policy | – | – | – | – | – | none found |
| Occupation / industry | U | – | – | – | – | verify ISCO digits, NACE sections |
| Demographics / earnings | U | – | – | – | – | earnings likely **banded/quintile**; verify |
| Weights / replicates | U | – | – | – | – | verify |
| Interview date | U | – | – | – | – | verify; mode flag needed |
| ID / linkage | U | – | – | – | – | cross-section |
| Missing coding | U | – | – | – | – | EWCS uses 7/8/9-style DK/refusal codes in past rounds (**assumption**) |

### B. Candidate estimands (conditional on file checks)
1. Association of AI use with job-design/work-organisation measures (autonomy, intensity, task variety), within country and occupation group. Associational.
2. Association of AI use with skills-match / training-need and training participation. Associational.

### C. Fatal / major risks
- **Access**: UKDS registration/licence not yet verified → schedule risk; the kill-check sets mid-Nov as the latest acceptable approval date.
- **Measurement**: broad AI wording, 12% prevalence (small user N within country), binary only, no intensity.
- **No productivity or time-saving outcome** → "productivity" must be proxied (work intensity, quality-of-output items) — likely weak; the theme match rests on skills and job design.
- **Mode mixing** (F2F + web) can confound AI-use reporting and attitudes.
- **Temporal**: single 2024 cross-section; skills mismatch/training and AI use measured at the same time ⇒ direction unidentifiable.
- **Country heterogeneity**: tiny cells at occupation × country.
- Non-Canadian sample (applies also to the two US surveys): CJAS relevance must be argued, not assumed.

### D. Verdict: **AUDIT FURTHER**
Kill (→ NO-GO) if: (i) AI item not in public file or user N < ~1,500 employees; (ii) neither skills-match nor training-need item present; (iii) fewer than ~3 usable job-autonomy items; (iv) UKDS licence bars the intended use or approval cannot clear by ~mid-Nov.

---

## 4. Rankings (provisional; conditional on kill-checks)

| Criterion | 1st | 2nd | 3rd | One-line reason |
|---|---|---|---|---|
| Scientific contribution | EWCS | HTOPS | SHED | Only EWCS can speak to AI × skills/job design in a harmonised multi-country frame, **if** the file items exist; HTOPS adds task-level + time-saving but nothing on skills; SHED is thin beyond what the Fed published |
| CJAS fit (management/admin, skills, productivity) | EWCS | SHED | HTOPS | work organisation + skills vs employer encouragement + perceived productivity vs household-survey tasks |
| Feasibility by 15 Dec 2026 | SHED | HTOPS | EWCS | SHED: one file, simple weights; HTOPS: replicate-weight file + corrected-version handling; EWCS: registration/licence plus coding of mixed-mode, multi-country data |

None of the three is a GO until its kill-checks pass. If the one-hour file checks must be spent on only one dataset first, **SHED (fastest to kill or confirm), then EWCS (highest upside)**; HTOPS is the likeliest to be killed on content (no employer/skills variables).
A combined design (SHED/HTOPS for US task-and-time descriptives; EWCS for skills/job design) is *not* assessed here: the three surveys have non-overlapping populations and constructs, and I would not recommend pooling.

## 5. Checks that fill the empty cells (in order)
1. `00_fetch.py` → read landing pages → fix `config/sources.yaml` file names → download PUF/dictionary/questionnaire/weights; record SHA-256 & date.
2. `run_audit.py --file …` stage 1 → `*_inventory.csv`: confirm which constructs have any candidate variable at all.
3. Fill `config/*_map.yaml` from the official dictionary (variable names, codes, missing codes, weights, ρ/R).
4. Stage 2 → `*_audit_log.json`, `*_analytic_n.csv`: N, eligible N, AI-user N, weighted prevalence (+BRR SE for HTOPS), raw missing-code tabs, analytic N for AI × outcome.
5. Reconcile against published figures (HTOPS 56%/51%; SHED ≈25% and 81%/52%/55%/44%; EWCS ≈12%). A mismatch in universe or weights is itself a finding.

## Sources (search-surfaced; none fetched in full)
- [Census HTOPS PUF page 2026](https://www.census.gov/programs-surveys/household-pulse-survey/data/datasets.2026.html), [Tip Sheet 13](https://www.census.gov/newsroom/tip-sheets/2026/tp26-13.html), [Census story: AI use at work](https://www.census.gov/library/stories/2026/08/ai-use-at-work.html), [HTOPS user notes 2026](https://www.census.gov/programs-surveys/household-pulse-survey/technical-documentation/user-notes/2026.html), [May 2026 user notes PDF](https://www2.census.gov/programs-surveys/demo/technical-documentation/hhp/2605_HTOPS_Household_Pulse_User_Notes_09102026.pdf)
- [SHED 2025 Appendix A](https://www.federalreserve.gov/publications/2026-supplemental-appendixes-report-economic-well-being-us-households-2025-appendix-a.htm), [Employment and Job Quality](https://www.federalreserve.gov/publications/2026-economic-well-being-of-us-households-in-2025-employment-and-job-quality.htm), [Fact sheet](https://www.federalreserve.gov/newsevents/pressreleases/files/other20260513a1.pdf)
- [EWCS 2024 page](https://www.eurofound.europa.eu/en/surveys-and-data/surveys/european-working-conditions-survey/ewcs-2024), [First findings](https://www.eurofound.europa.eu/en/publications/all/european-working-conditions-survey-2024-first-findings), [Overview report](https://www.eurofound.europa.eu/en/publications/all/european-working-conditions-survey-2024-overview-report), [UKDS 7363](https://doc.ukdataservice.ac.uk/doc/7363/mrdoc/UKDA/UKDA_Study_7363_Information.htm), [CESSDA record](https://datacatalogue.cessda.eu/detail/31741ebe15b48694177b7274afa2b7af5a7ec43d10bfdb5c172eed6bc69002cf?lang=en), [arXiv 2604.18849](https://arxiv.org/html/2604.18849)
