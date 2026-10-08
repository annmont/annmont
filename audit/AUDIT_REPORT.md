# Data / variable feasibility audit — HTOPS Mar-2026, SHED 2025, EWCS 2024

Audit date: 2026-10-08. Target: CJAS special issue "AI, Future Skills, and Productivity" (deadline 2026-12-15).
No regressions, no draft, no causal claims. Everything below is counts, tabulations, weighted shares and the documentation they come from.

## 0. Evidence status (read first)

| Dataset | What was inspected | Status |
|---|---|---|
| **HTOPS Mar-2026** | PUF CSV + replicate-weight CSV + data dictionary (xlsx) + Source & Accuracy + user notes, all downloaded from census.gov | **Verified in file** |
| **SHED 2025** | public2025.dta / .csv, official codebook PDF, Appendix A questionnaire, plus the SHED 2024 public file for linkage | **Verified in file** |
| **EWCS 2024** | **No microdata.** UKDS QA report, UKDS coding report, a 2026 arXiv paper that uses the file | **Documentation only** — file needs a UKDS login; Eurofound's site blocks automated access (Vercel bot challenge, HTTP 429), which I did not bypass |

Tiers used: **F** = read in the file/official document; **S** = secondary (search summary or third-party paper); **U** = unknown.
File hashes are in `outputs/*_audit_log.json`. Code: `audit/src/` (`00_fetch.py`, `run_audit.py`, `htops_checks.py`, `shed_checks.py`), maps in `audit/config/`. Reproduce with `audit/README.md`.

**Corrections to earlier assumptions (and my own first-pass report):**
- HTOPS "136,000" is the **households sampled/invited**, not respondents. The PUF has **12,521** respondents; response rate **9.2%** (10.4% weighted) [F: Source & Accuracy].
- HTOPS March 2026 is cross-sectional [F: user notes, S&A]. Confirmed; no linkage.
- HTOPS PUF covers adults **25–88** only [F]. Weights were **re-issued 10 Sep 2026** (group-quarters control error) [F]; the zip contents are dated 1 Sep 2026. Use the current file and record the hash.
- SHED **does** have a recontact panel: 4,419 respondents carry `panel_weight`, and their `shedid` matches the 2024 public file (section 2).
- SHED public CSV stores answers as **text labels**; the `.dta` has numeric codes. I audited the `.dta`.

---

## 1. US Census HTOPS, March 2026 (priority 1) — all [F] unless noted

### Counts
| Quantity | Value |
|---|---|
| Total N (PUF rows) | **12,521** (219 variables; `SCRAMID` unique; replicate file merges 1:1) |
| Eligible workers (`ANYWORK`=1, worked for pay/profit last 7 days) | **6,680** (148 DK; 5,693 no). Includes 996 self-employed/family-business (`CLASS_WORKER` 4,5) |
| AI users (yes to ≥1 of 11 tasks) | **4,091** |
| Non-users (valid "No" on all 11) | **2,186** |
| Ambiguous (no "yes", ≥1 DK) / all 11 missing | 296 / 107 → valid denominator **6,277** |
| Weighted prevalence (valid denominator) | **55.6%** (SE 2.1, SDR) — reproduces Census' 56% |
| Same, ambiguous+missing counted as non-users | 51.2% (SE 1.9) — this is the "51%" in third-party posts |
| Used AI last week (`AIWRK_FREQ`=1,2) | 3,042 (35.3% of workers, SE 1.8) |
| Last-week users with valid time-saved answer | **2,991** (51 DK) |
| Weights | `PWEIGHT` (= `PWEIGHT0`, verified), `HWEIGHT`; `PWEIGHT1–80` in a separate file keyed on `SCRAMID`; SDR, Var = 4/80 Σ(θᵢ−θ)² [F: S&A] |

Published figures reproduced: tasks (search 38.3%, comms 33.9%, ideas 33.2%, interpret 32.0%, admin 28.4%), frequency 24/46/31%, hours <1h 25.1% and 1–2h 31.5% — all match Census' August 2026 story.

### A. Variable dictionary
| Construct | Variable | Exact wording | Coding | Universe | Usable N | Limitation |
|---|---|---|---|---|---|---|
| Employed | `ANYWORK` | "In the last 7 days, did you do ANY work for either pay or profit?" | 1 Yes, 2 No, −99 DK | all | 6,680 yes | 7-day window; includes self-employed |
| Any AI use (11 items) | `AIWRK_ADMIN, _CODE, _CUSTSUPP, _DATAVIS, _GENIDEA, _INTERP, _LOG, _MED, _SEARCH, _TUTOR, _COMM` | "AI is the capability of computational systems to perform tasks typically associated with human intelligence… (Examples: machine learning, natural language processing, virtual agents, voice recognition, etc.) IN YOUR WORK, have you used AI to do any of the following tasks? Select Yes or No for each." | 1 Yes, 2 No, −99 DK, −88 NIU | workers | 4,091 users / 2,186 non-users | **Not GenAI-specific**; reference period unspecified; "ever in work" |
| Frequency | `AIWRK_FREQ` | "AT WORK, how often did you use AI last week?" | 1 every day, 2 ≥1 day not every day, 3 used but not last week | users (any task) | 4,068 (+23 DK) | 3 coarse bins; users only |
| Time saved | `AIWRK_HOURS` | "If you had NOT been able to use AI at work last week, how many additional hours would you have needed to complete the same amount of work?" | 1 <1h … 6 >4h, 7 no saving, 8 required more time | used ≥1 day last week | 2,991 | Counterfactual self-report; users-only; no non-user comparison |
| Quality | — | — | — | — | — | **Absent** |
| Skills / training | — | — | — | — | — | **Absent** (education only) |
| Autonomy / job design | `TWDAYS` | "In the last 7 days, have you teleworked or worked from home?" | 1 1–2d, 2 3–4d, 3 5+, 4 no | workers | 6,633 | Only job-organisation variable |
| Employer encouragement / policy | — | — | — | — | — | **Absent** |
| Occupation | `AI_OCC` | "What is your occupation?" | **10 broad groups** | workers | 6,439 (241 DK) | Very coarse; group 5 has 21 workers |
| Industry | — | — | — | — | — | **Absent** |
| Class of worker | `CLASS_WORKER` | gov't/private/nonprofit/self-emp/family | 1–5 | workers | 6,526 | — |
| Demographics | `TAGE` (25–88), `ESEX`, `RRACETH`, `REDUC` (7 levels), `MS`, `THHLD_*`, `REGION`, `METRO` (10 MSAs) | — | — | all | no missing on age/education | Age ≥25 only |
| Earnings | `RHHINCOME` | "In 2025 what was your total household income before taxes?" | 7 bins | all | 5,950 of 6,680 workers | **Household income bins; no individual earnings** |
| Interview date | — | — | — | — | — | None; single wave 13–30 Mar 2026 [F: user notes] |
| ID / linkage | `SCRAMID` | — | unique | — | — | Cross-section; no linkage possible |
| Missing codes | — | −99 DK/no answer, −88 not in universe | — | — | — | Consistent across items |

### Usable analytic N (workers, valid AI)
| Combination | AI users | Non-users |
|---|---|---|
| AI × frequency | 4,068 | n/a (users only) |
| AI × time saved | 2,991 | n/a |
| AI × occupation (10 groups) | 4,014 | 2,094 |
| AI × telework days | 4,068 | 2,179 |
| AI × class of worker | 4,027 | 2,131 |
| AI × household income bin | 3,727 | 1,956 |

### B. Candidate estimands the data support (max 2)
1. Weighted distribution of AI **task breadth** (count of the 11 tasks) and last-week intensity by occupation group × education × class of worker.
2. Among last-week users, the **association between task profile and reported time saved** (ordinal), by occupation group.

### C. Fatal / major risks
- **Content gap for this special issue:** no employer policy, no skills/training, no autonomy beyond telework, no industry, no quality. "Future skills" and "productivity" cannot be addressed beyond a self-reported hours item.
- **Selection:** 9.2% response, online self-response; productivity item only for users.
- **Measurement:** broad AI definition (voice recognition, virtual agents) → not GenAI; counterfactual hours.
- **Coarse controls:** 10 occupation groups, household (not personal) income bins, no industry.
- **Temporal:** one 18-day cross-section.
- **Contribution:** Census has already published the headline tabulations; my checks reproduce them to the decimal.
- **Version:** weights re-issued 10 Sep 2026; any earlier download is wrong.

### D. Verdict: **NO-GO as primary dataset**
(The literal kill rule I proposed earlier — ≤5 occupation groups — is *not* triggered; this is a judgement on content: employer, skills and autonomy are missing.) Keep only as a US descriptive benchmark.

---

## 2. Federal Reserve SHED 2025 (priority 2) — all [F]

### Counts
| Quantity | Value |
|---|---|
| Total N | **12,934** (815 variables; `shedid` unique) |
| Worked last month (`D1A`=1; universe of D50 and D52) | **7,488** |
| GenAI users (`D50`=1) / non-users | **1,850** / 5,638 |
| Weighted prevalence (`weight_pop`) | **24.7%** (unweighted 24.7%) — matches Fed "one in four" |
| `D51` frequency (users) | 1,850 valid: multiple/day 270, daily 269, several days/wk 441, weekly 326, <1/wk 544 |
| `D52` a–f | 7,488 valid each (1,850 users / 5,638 non-users) |
| Employees (`D3A`=0) with autonomy items | 6,285 (1,626 users / 4,659 non-users) |
| Weights | `weight`, `weight_pop` (main), `panel_weight`, `panel_weight_pop` (recontact; 4,419 non-missing). **No strata/PSU, no replicate weights** |
| Imputation | `*_iflag` columns; D50 flagged imputed for 18 rows |

### Who gets D50–D52 and how wording differs (verified in Appendix A)
- **D50:** base = `D1A`=1 (worked last month). Wording: "Generative AI is a type of artificial intelligence that creates text, images, audio, or video in response to prompts. Some examples … include ChatGPT, Gemini, and Midjourney. Did you use Generative AI at your job last month? Please do not include seeing AI results from search engines."
- **D51:** base = `D50`=1 only.
- **D52 (6-item grid, 1 Agree / 2 Neither / 3 Disagree):** base = `D1A`=1, i.e. **all workers**. If `D50`=0 an extra preface is inserted: "Even though you aren't currently using AI at work, we're interested in your perspective on the technology for jobs like yours." The statements are identical for users and non-users (the stem still says "using Generative AI for your job"). So for non-users D52 is **hypothetical/attitudinal**, for users it is **experience**.
- Published figures reproduced (Agree, weighted): saves time **users 81.0% / non-users 31.5% / all 43.7%**; improves quality 51.8 / 15.4 / 24.4; new tasks 55.5 / 19.5 / 28.4; **employer encourages** 50.8 / 8.5 / 19.0; career 48.1 / 11.0 / 20.2; worried about replacement 22.1 / 19.7 / 20.3.

### A. Variable dictionary
| Construct | Variable | Exact wording | Coding | Universe | Usable N | Limitation |
|---|---|---|---|---|---|---|
| Employed | `D1A` | "Last month, did you do any work for either pay or profit?" | 1/0 | all | 7,488 | 1-month window |
| GenAI use | `D50` | see above | 1 Yes / 0 No | worked last month | 7,488 | Binary; 1-month window; single item |
| Frequency | `D51` | "Last month, about how often did you use Generative AI at your job?" | 1–5 (see above) | D50=1 | 1,850 | Cells 269–544; users only |
| Task-level AI use | — | — | — | — | — | **Absent** |
| Saves time / quality / new tasks | `D52_a/_b/_c` | "It saves time" / "It improves quality" / "It enables me to do new tasks" | 1–3 | workers | 7,488 | Perceived; hypothetical for non-users |
| Employer encouragement | `D52_d` | "My employer encourages me to use it" | 1–3 | workers | 7,488 | One perceived item; no policy/provision detail |
| Career / replacement worry | `D52_e`, `D52_f` | "Having it available will improve my career" / "I am worried about AI replacing my job" | 1–3 | workers | 7,488 | Attitudes |
| Skills / training | — | — | — | — | — | **Absent** (only `D22_h` "in school or training" as a reason for not working) |
| Autonomy | `D28_a`, `D28_b` | "I can choose what tasks I work on" / "I can choose how I complete tasks at work" — "How often do each of these statements describe your work situation (at your main job)?" | 1 Never … 5 Always | employees (`D3A`=0) | 6,285 | Employees only; self-employed (935) excluded |
| Job organisation | `D30` (hours schedule), `D34A/D34D` (telework), `D36B`, `D44_a/_b` (raise/promotion) | — | — | various | D34D 1,726 | `D34D` asked only if some telework |
| Occupation | `ppcm0160` | "Q26: Occupation (tight scale) in current or main job" | codes 1–35 with overlapping categories (e.g. 2/30 both Business Operations) | workers | 6,926 | Needs recoding before use; −2 "Not asked" |
| Industry | `ind1` | "IND1: Industry (tight scale)" | 27 codes with overlaps (e.g. 3/22, 14/23) | workers | 6,949 | Needs harmonising |
| Employer type | `ppcm1301` | "GOVEMP1: Employer type" | 1–5 | workers | 6,962 | — |
| Demographics | `ppage`, `ppgender`, `ppethm`, `ppeducat`/`ppeduc5`, `ppstaten`, `ppmsacat` | — | — | all | complete | — |
| Earnings | `ppinc7` (household income, 7 cat), `inc_4cat_50k` | — | — | all | complete | **No individual earnings** |
| Interview date | — | — | — | — | — | None (only `duration`); fielded 17–28 Oct 2025 [S] |
| ID | `shedid` | — | unique | — | — | **Matches 2024 file for 4,420 respondents** (below) |
| Missing | — | −1 Refused, −2 Not asked | — | — | — | Skip-pattern missing is system-missing (.) |

### Repeated-wave linkage (the one place SHED beats the others)
- `shedid` appears in both the 2025 and 2024 public files for **4,420** respondents (4,419 = those with `panel_weight`).
- Same persons: age is exactly +1 in 4,241/4,420 (96%); gender identical in 99.9%; education 92%, race 98%, state 97%.
- Of those: **2,727** worked in 2025 (662 GenAI users); **2,478** worked in both years; **2,117 employees** have 2024 `D28_a` and a valid 2025 `D50` (**534 users**, all with `panel_weight_pop`).
- `D28_a/_b` labels and value labels are identical across 2024 and 2025 [F]. The 2024 file has **no GenAI items** [F] and GenAI was already widespread by Oct 2024, so 2024 autonomy is *pre-measurement*, not *pre-exposure*.
- Linked sample is a recontact subset (≈36% of 2025 respondents): selection must be checked against unlinked respondents.

### Usable analytic N
| Combination | Users | Non-users |
|---|---|---|
| D50/D51 × D52 outcomes (all workers) | 1,850 | 5,638 |
| × autonomy (D28), employees | 1,626 | 4,659 |
| × occupation / industry | 1,764 / 1,767 | 5,162 / 5,182 |
| 2024 autonomy → 2025 use (linked employees) | 534 | 1,583 |
| D51 × D52 (users only) | 1,850 | — |

### B. Candidate estimands (max 2)
1. **Prospective association:** 2024 task autonomy (`D28_a/_b`) and occupation/industry → 2025 GenAI use and intensity (`D50/D51`), among linked employees (N = 2,117; users 534), with panel weights. Associational.
2. **Cross-sectional, users only:** association of intensity (`D51`) and perceived employer encouragement (`D52_d`) with perceived time saving/quality/new tasks (`D52_a–c`), 1,850 users. Perception outcomes only.

### C. Fatal / major risks
- All productivity outcomes are **perceived** and the D52 statements are **hypothetical for non-users** — never pool users and non-users on D52.
- Same-wave employer encouragement and use: reverse causality/common cause.
- **No skills/training measure, no individual earnings, no task-level AI items.**
- Linked N is modest (534 users); D51 cells are 269–544, so any covariate interaction will be thin.
- **No strata/PSU or replicate weights:** only weighted point estimates and robust SEs; state this openly.
- Selection into the recontact panel; D28 only for employees.
- GenAI already diffused in 2024 → 2024 autonomy is not a clean pre-period.
- Contribution: Fed and others published the headline shares; novelty rests on the linked-autonomy design.

### D. Verdict: **GO — narrow scope**
Conditions before committing: (i) compare linked vs unlinked 2025 respondents on observables; (ii) recode `ppcm0160`/`ind1` to a single scheme; (iii) pre-specify that D52 is analysed separately for users and non-users. Kill if the linked users' autonomy association is not estimable at a usable precision once (i)–(ii) are done (suggested floor: 400 linked users).

---

## 3. Eurofound EWCS 2024 (priority 3) — documentation only

### What I could and could not do
- **Microdata not obtained.** The 2024 cross-section is UK Data Service **SN 9511** (cited as such in the arXiv paper; DOI 10.5255/UKDA-SN-9511-1 from search [S]). Access requires a UKDS login and licence acceptance; the licence tier is **not verified**. The UKDS catalogue is a JavaScript shell I could not read, and `eurofound.europa.eu` returns an anti-bot challenge (HTTP 429) to scripted requests. A CESSDA record (search summary [S]) says the **online-mode data are not available until late 2026**.
- The integrated 1991–2024 file is SN 7363 (9th release Mar 2026) [F].

### Facts from documents
| Item | Finding | Tier |
|---|---|---|
| Sample | Face-to-face **36,644** interviews, 35 countries; parallel **online** segment **15,250** [QA report Table 2b] | F |
| Mode | Mixed: F2F main + online test. Online: full questionnaire for 50%, shortened M1/M2 for the rest; **routing error (Q53, Q63, Q66) caused missing data for ~2,000 online respondents** | F |
| AI item | "At work, do you use artificial intelligence that simplifies complex mental tasks or makes recommendations (e.g. ChatGPT, LLAMA, DALL-E, Midjourney, Jasper)?" 1 Yes / 2 No — **broader than GenAI; binary; no frequency** (the paper itself says so). Country adoption 3%–25% | S (arXiv 2604.18849) |
| Consequence items | "Technology has removed some of your tasks" / "…created new tasks for you" | S |
| Skills / training | Workplace training (employer-provided or self-financed, last 12 months), task discretion index (order, methods, speed; α=.85), organisational-influence index (4 items), abstract/routine task factors (8 items), computer use, tenure, workplace size, 2-digit ISCO and NACE | S |
| **Skills match / need for training** | **Not found** in the paper or reports. Eurofound's overview cites overskilling 30% / need more training 13% (survey-level), but whether those items are in SN 9511 with usable coding is **unverified** | S/U |
| Weight | "EWCS calibrated survey weight"; no replicate weights known | S |
| Earnings | Unknown | U |
| Productivity / time-saving | **Not found** | — |
| Employer AI policy | **Not found** | — |
| Linkage | Harmonised 1990–2024 is repeated cross-sections; the AI item exists only in 2024 → no pre/post | S |

### A. Variable dictionary
All "usable N" cells: **NOT COMPUTED**. Wording/coding for the AI item and the paper's constructs as above; item names, universes, and missing codes are **U** until the codebook is opened. Skills-match / need-training items: **U** (see above).

### B. Candidate estimands (conditional on the file)
1. Association between AI use and **task discretion / organisational influence / task variety**, within country × 2-digit ISCO.
2. Association between AI use and **training received and skills-match / training-need items** — only if the latter exist in SN 9511.

### C. Fatal / major risks
- **Prior art on the same file and item:** arXiv 2604.18849 (2026) already studies AI adoption × skills, training, task discretion and organisational influence, with occupational exposure and cross-country moderators. A new paper needs a different outcome (e.g. skills-match) or design, or it is a replication.
- **Measurement:** the AI item is broader than GenAI, binary, and has no intensity or task information; no productivity measure.
- **Mode:** F2F vs online with a split/short form and a known routing defect; online availability unclear.
- **Skills-match / need-for-training items unconfirmed** — this is the theme-critical variable.
- **Access:** UKDS login/licence unverified; I cannot rule out delay.
- Single cross-section; country × occupation cells thin at 3–25% prevalence.

### D. Verdict: **AUDIT FURTHER** (one decisive check)
Open the SN 9511 codebook/questionnaire. **Kill (→ NO-GO)** if (i) no skills-match or need-for-training item is in the public file, because then the paper duplicates arXiv 2604.18849; (ii) AI-user N < ~1,500 employees; (iii) the licence or timing prevents access by mid-November.

---

## 4. Rankings

| Criterion | 1st | 2nd | 3rd | Reason |
|---|---|---|---|---|
| Scientific contribution | **SHED** | EWCS | HTOPS | SHED: verified linked autonomy → GenAI adoption + intensity + employer encouragement; EWCS: strong constructs but direct prior art and unverified key item; HTOPS: nothing beyond published descriptives |
| CJAS fit | **EWCS** | SHED | HTOPS | EWCS = work organisation/skills (if item exists); SHED = employer encouragement + autonomy, no skills; HTOPS has neither. None is Canadian |
| Feasibility by 15 Dec | **SHED** | HTOPS | EWCS | SHED and HTOPS are downloaded and audited; EWCS needs UKDS registration and codebook check |

Rankings for EWCS rest on documents, not the file.

## 5. What I need from you
1. **EWCS:** register at the UK Data Service, download SN 9511 (and its questionnaire/codebook), place them in `audit/data/raw/ewcs/`, tell me — I will run the stage-1 inventory and fill the map. (Eurofound's site blocks scripts.)
2. **Decision:** SHED as the lead dataset (GO, narrow scope), EWCS as a conditional second, HTOPS dropped or used only as a US descriptive benchmark.
