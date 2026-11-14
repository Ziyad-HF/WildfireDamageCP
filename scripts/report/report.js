const fs = require("fs");
const { Document, Packer, Paragraph, TextRun, ImageRun, Table, TableRow, TableCell, WidthType, ShadingType, AlignmentType,
  HeadingLevel, BorderStyle, LevelFormat, PageBreak, Footer, PageNumber, TableOfContents } = require("docx");
const T = JSON.parse(fs.readFileSync("/tmp/final/tables.json"));
const IMG = "/tmp/final/img/";
const GREEN = "275D37", FONT = "Arial", W = 9360;
const sizeOf = (f) => { const b = fs.readFileSync(f); return [b.readUInt32BE(16), b.readUInt32BE(20)]; };

function P(text, opts = {}) {
  const runs = (Array.isArray(text) ? text : [text]).map(t => typeof t === "string" ? new TextRun({ text: t }) : new TextRun(t));
  return new Paragraph({ children: runs, spacing: { after: 120, line: 276 }, alignment: opts.align || AlignmentType.JUSTIFIED, ...opts.p });
}
const H1 = t => new Paragraph({ heading: HeadingLevel.HEADING_1, children: [new TextRun(t)] });
const H2 = t => new Paragraph({ heading: HeadingLevel.HEADING_2, children: [new TextRun(t)] });
const B = (text) => new Paragraph({ numbering: { reference: "bul", level: 0 }, spacing: { after: 60 },
  children: (Array.isArray(text) ? text : [text]).map(t => typeof t === "string" ? new TextRun(t) : new TextRun(t)) });
let figN = 0, tabN = 0;
function FIG(file, caption, widthIn = 6.5) {
  const [w, h] = sizeOf(IMG + file); figN++;
  const wp = widthIn * 96, hp = wp * h / w;
  return [new Paragraph({ alignment: AlignmentType.CENTER, keepNext: true, spacing: { before: 120, after: 60 },
      children: [new ImageRun({ type: "png", data: fs.readFileSync(IMG + file), transformation: { width: wp, height: hp } })] }),
    new Paragraph({ spacing: { after: 200 }, alignment: AlignmentType.LEFT,
      children: [new TextRun({ text: `Figure ${figN}. `, bold: true, size: 18 }), new TextRun({ text: caption, size: 18 })] })];
}
const border = { style: BorderStyle.SINGLE, size: 4, color: "BFBFBF" };
function TAB(caption, header, rows, widths, note, lab) {
  if (!lab) { tabN++; lab = `Table ${tabN}`; }
  const tot = widths.reduce((a, b) => a + b, 0); const ws = widths.map(x => Math.round(x * W / tot));
  ws[ws.length - 1] += W - ws.reduce((a, b) => a + b, 0);
  const cell = (t, i, hdr) => new TableCell({ width: { size: ws[i], type: WidthType.DXA }, borders: { top: border, bottom: border, left: border, right: border },
    shading: hdr ? { fill: GREEN, type: ShadingType.CLEAR, color: "auto" } : undefined, margins: { top: 40, bottom: 40, left: 70, right: 70 },
    children: [new Paragraph({ alignment: i === 0 ? AlignmentType.LEFT : AlignmentType.CENTER, children: [new TextRun({ text: String(t), size: 16, bold: hdr, color: hdr ? "FFFFFF" : "222222" })] })] });
  const out = [new Paragraph({ keepNext: true, spacing: { before: 160, after: 80 }, children: [new TextRun({ text: `${lab}. `, bold: true, size: 18 }), new TextRun({ text: caption, size: 18 })] }),
    new Table({ width: { size: W, type: WidthType.DXA }, columnWidths: ws,
      rows: [new TableRow({ tableHeader: true, children: header.map((h, i) => cell(h, i, true)) }), ...rows.map(r => new TableRow({ children: r.map((x, i) => cell(x, i, false)) }))] })];
  out.push(new Paragraph({ spacing: { before: 60, after: 200 }, children: note ? [new TextRun({ text: note, size: 16, italics: true })] : [] }));
  return out;
}
const short = m => m.replace("ConvNeXt", "CNN").replace("VLM zero-shot", "VLM zero-shot").replace(" + ", "+");

const body = [];
// ---------- title ----------
body.push(new Paragraph({ alignment: AlignmentType.CENTER, spacing: { before: 600, after: 200 }, children: [new TextRun({ text: "Knowing When to Ask an Inspector", bold: true, size: 44, color: GREEN, font: FONT })] }));
body.push(new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 400 }, children: [new TextRun({ text: "Calibrated vision-language damage assessment for wildfires, with conformal prediction sets and inspector routing", size: 28, font: FONT })] }));
body.push(new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 80 }, children: [new TextRun({ text: "Ziyad ElFayoumy, Ayman Saeed, Yeganeh", size: 24 })] }));
body.push(new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 80 }, children: [new TextRun({ text: "CIV E 779: Machine Learning for Engineers (Dr. Qipei (Gavin) Mei), University of Alberta, Fall 2026", size: 22 })] }));
body.push(new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 600 }, children: [new TextRun({ text: "Draft report, November 2026", size: 22, italics: true })] }));
body.push(new Paragraph({ spacing: { after: 120 }, children: [new TextRun({ text: "Abstract", bold: true, size: 24, color: GREEN })] }));
body.push(P("After a wildfire, field crews inspect damaged buildings one by one. Satellite-based classifiers are fast, but they do not say when they are unsure, and their accuracy drops on fires unlike the ones they were trained on. We tested whether calibrated probabilities and split conformal prediction sets can decide which buildings may be auto-labelled and which should be sent to an inspector. We trained three model tiers on 74,622 buildings from four xBD wildfires: a Siamese ConvNeXt-Tiny CNN (T1), a zero-shot vision-language model, Qwen3-VL-8B-Instruct (T2), and the same model fine-tuned with LoRA (T3). Each was evaluated with leave-one-fire-out cross-validation and on an external test of 8,457 buildings from the 2025 Eaton Fire, labelled by CAL FIRE field inspections. LoRA fine-tuning raised the VLM from 0.31–0.43 to 0.52–0.69 macro-F1, matching the CNN. After temperature scaling, T1 and T3 were well calibrated (ECE 0.010–0.036). On Eaton, T3 with APS prediction sets auto-labelled 93.4% of buildings and missed 1.0% of destroyed homes. However, the conformal 90% coverage target and the ≤ 5% missed-destroyed routing target, both set on the training fires, did not transfer to fires that looked different. Destroyed-class coverage fell to 0.24–0.40 on Portugal, and 9–43% of destroyed homes were missed on Woolsey, Pinery and Portugal. An added analysis showed that recalibrating on about 100–300 labelled houses from the new fire restored coverage but not the 5% miss target. Calibrated sets are useful for triage when the new fire resembles past fires; detecting and correcting fire shift is the main open problem."));
body.push(new Paragraph({ children: [new PageBreak()] }));

// ---------- 1 intro ----------
body.push(H1("1. Introduction"));
body.push(P("Building damage assessment after a wildfire decides where recovery funds, insurance claims and rebuilding permits go. Field inspection is the reference standard but is slow and limited by access: after the January 2025 Eaton Fire, CAL FIRE's Damage Inspection (DINS) teams recorded 18,428 structures. In Canada, the July 2024 Jasper wildfire caused over $880 million in insured damage (Insurance Bureau of Canada, 2024). Deep-learning models trained on satellite image pairs, such as those from the xView2 challenge, can label buildings in minutes, but they generalise poorly to new regions (Kshirsagar et al., 2026) and give a label without a reliable statement of how likely it is to be wrong."));
body.push(P("This project asks a practical question: can a model tell an inspection team which buildings it is sure about, with a known error rate, so that crews visit only the rest? We combine three ingredients that are standard in machine learning but, to our knowledge, have not been tested together for building damage under held-out disasters (based on targeted literature searches, not a systematic review): (1) temperature scaling, which makes predicted probabilities match observed accuracy (Guo et al., 2017); (2) split conformal prediction, which turns probabilities into sets of labels with a target coverage (Angelopoulos and Bates, 2021); and (3) a routing rule that auto-labels a building only when its set has one label, tuned so that at most 5% of destroyed homes are missed."));
body.push(P("We answer three research questions:"));
body.push(B([{ text: "RQ1 (calibration): ", bold: true }, "after temperature scaling, how well calibrated are a CNN, a zero-shot vision-language model (VLM) and a LoRA-fine-tuned VLM on wildfires they never saw?"]));
body.push(B([{ text: "RQ2 (coverage): ", bold: true }, "do conformal prediction sets keep their 90% target coverage on held-out fires and on an external field-inspected fire?"]));
body.push(B([{ text: "RQ3 (workload): ", bold: true }, "while missing at most 5% of destroyed homes, what share of buildings can be auto-labelled without a field visit?"]));
body.push(...FIG("rep_pipeline.png", "Overview of the approach. A model produces class probabilities from pre- and post-fire images; temperature scaling calibrates them; a conformal step turns them into a prediction set; one-label sets are auto-labelled and larger sets go to an inspector. The example sets are schematic."));

// ---------- 2 related ----------
body.push(H1("2. Related Work"));
body.push(P("xBD (Gupta et al., 2019) provides pre/post satellite pairs and four ordinal damage levels for 19 disasters and underlies most building-damage models. BRIGHT (Chen et al., 2025) adds optical pre-event and radar post-event images. Recent work applies vision-language models to disaster imagery: DisasterM3 (Wang et al., 2025) is a large instruction dataset, and DisasterInsight (Tehrani et al., 2026, preprint) benchmarks building-level VLMs on xBD, including LoRA fine-tuning of Qwen3-VL-8B; both focus on accuracy. Uncertainty for damage assessment has mainly used Bayesian approaches, such as Monte Carlo dropout (Cheng et al., 2022) and BayeSiamMTL (Hertel et al., 2025), which give uncertainty scores but no guaranteed error rate. Conformal prediction has been benchmarked on VLMs for multiple-choice tasks (Azad et al., 2025, preprint), applied to remote-sensing land-cover classes (Schweden et al., 2026), and used for ordinal severity grading in medical imaging (MICCAI 2022, arXiv:2207.02238). Kshirsagar et al. (2026) show that top xView2 models degrade under geographic shift. Our contribution is to test conformal sets for building damage on held-out wildfires and an external field-inspected fire, for both a CNN and a VLM, and to express the result as an inspector-workload metric."));

// ---------- 3 data ----------
body.push(H1("3. Data"));
body.push(H2("3.1 Sources"));
body.push(B([{ text: "xBD / xView2 ", bold: true }, "(full GeoTIFF release, ~55 GB in 6 parts; SHA1 checksums verified). Wildfire events: Santa Rosa (California, 2017), Woolsey (California, 2018), Pinery (South Australia, 2015) and Portugal (2017). The xBD events socal-fire and woolsey-fire cover the same area four days apart, so we merged them into one 'Woolsey' fire to avoid leakage. No Carr Fire event was present in the downloaded labels."]));
body.push(B([{ text: "CAL FIRE DINS 2025 Eaton ", bold: true }, "(Data.gov): field-inspection damage labels for 18,428 structures."]));
body.push(B([{ text: "Maxar Open Data ", bold: true }, "(WildFires-LosAngeles-Jan-2025): a WorldView-3 pair from the same satellite, before (1 January 2025) and after (14 January 2025), both cloud-free. 8,457 of the 12,739 non-shed DINS structures fall inside this pair's footprint with valid pixels."]));
body.push(P("BRIGHT was examined and not used because its post-event images are single-band radar, while our models need colour before/after pairs."));
body.push(H2("3.2 Labels and crops"));
body.push(P("Labels were harmonised to three classes: no damage; damaged (xBD minor + major; DINS Affected 1–9%, Minor 10–25% and Major 26–50%); and destroyed (xBD destroyed; DINS Destroyed > 50%). xBD 'un-classified', DINS 'Inaccessible' and utility/miscellaneous structures were excluded. For each building we cut a 64 m × 64 m ground square, resized to 224 × 224 px, from the pre- and post-fire images. A first version padded buildings near xBD tile edges with black (about 20% of crops had more than 25% black pixels). The final version shifts the window inside the tile and stores the building's position in the crop; 0.25% of sampled crops exceed 25% black. 138 xBD buildings whose centre fell outside the crop were excluded. An automated overlay check on 30 Eaton buildings found DINS points on or within a few metres of the house, and a pre/post image shift with a median of 2.33 m (max 5.20 m)."));
body.push(...TAB("Buildings per fire after harmonisation and exclusions.", ["Fire", "Role", "No damage", "Damaged", "Destroyed", "Total"],
  [["Santa Rosa", "xBD, fold 1 test", "15,843", "216", "5,810", "21,869"], ["Woolsey", "xBD, fold 2 test", "20,238", "558", "4,180", "24,976"],
   ["Pinery", "xBD, fold 3 test", "5,019", "180", "229", "5,428"], ["Portugal", "xBD, fold 4 test", "20,787", "472", "1,090", "22,349"],
   ["Eaton 2025", "external test", "4,007", "543", "3,907", "8,457"]], [2, 2.2, 1.4, 1.2, 1.2, 1.2],
  "'Damaged' is 1.0–3.3% of buildings in the xBD fires and 6.4% in Eaton. xBD total: 74,622 buildings; all buildings: 83,079."));

// ---------- 4 methods ----------
body.push(H1("4. Methods"));
body.push(H2("4.1 Evaluation design"));
body.push(P("We used leave-one-fire-out cross-validation: fold k tests on one xBD fire, and the other three fires are split into train (70%), validation (10%) and calibration (20%) by 0.005° × 0.005° grid cells (about 500 m), so that neighbouring houses never fall into different roles. Each fold model also scores all 8,457 Eaton buildings, which no model saw during training. The models, metrics, α, routing rule and bootstrap procedure were written down and committed before any model was trained (configs/preregistration.md, commit 47a8a44); implementation details D1–D14 were fixed before the analyses that use them."));
body.push(...FIG("rep_design.png", "Leave-one-fire-out design. In each fold one xBD fire is the test fire (red); the other three are split into train/validation/calibration by grid cell. Every fold model also scores the external Eaton Fire (gold)."));
body.push(H2("4.2 Models"));
body.push(B([{ text: "T1 (CNN): ", bold: true }, "Siamese ConvNeXt-Tiny with ImageNet weights, pre/post crops with a red marker on the target building, class-weighted cross-entropy and early stopping on validation; 4 folds × 3 seeds."]));
body.push(B([{ text: "T2 (VLM zero-shot): ", bold: true }, "Qwen3-VL-8B-Instruct with one frozen prompt asking for answer A, B or C. Class probabilities are the softmax over the three answer-token logits; one deterministic run over all buildings."]));
body.push(B([{ text: "T3 (VLM + LoRA): ", bold: true }, "the same VLM fine-tuned with LoRA (rank 16) using a 3-way cross-entropy on the A/B/C logits, at most 3 epochs, early stopping on validation; 4 folds × 3 seeds. A pilot of 50 LoRA steps peaked at 44 GB of GPU memory."]));
body.push(P("All training and inference ran on H200 GPUs."));
body.push(H2("4.3 Calibration"));
body.push(P("One temperature T per run was fitted on the calibration split by minimising the negative log-likelihood (bounded search over log T in [−3, 3]) and applied to all roles (Guo et al., 2017). We report expected calibration error (ECE; 15 equal-width bins over the top-class probability) and the Brier score before and after scaling."));
body.push(H2("4.4 Conformal prediction sets"));
body.push(P("Using the temperature-scaled probabilities, we applied split conformal prediction at α = 0.10 (target coverage 90%) with four scores: LAC (s = 1 − p_y); non-randomised APS (probability mass ranked strictly above y); ordinal-contiguous sets; and Mondrian (class-conditional LAC, one threshold per true class, so coverage of 'destroyed' is targeted separately). The threshold is the ⌈(n+1)(1−α)⌉-th smallest calibration score. LAC and Mondrian sets can be empty; empty sets count as not auto-labelled."));
body.push(H2("4.5 Inspector routing"));
body.push(P("A building is auto-labelled when its prediction set contains exactly one class; otherwise it is routed to an inspector. A destroyed building is 'missed' if it is auto-labelled as another class. The routing α is chosen on the calibration split over a grid from 0.005 to 0.5. The preregistered rule (rule 8) takes the largest α whose calibration missed-destroyed rate is ≤ 5%. Amendment A1 instead takes the α that maximises the calibration auto-labelled share subject to the same constraint (see Section 6.3). The chosen α is applied unchanged to the test fire and Eaton."));
body.push(H2("4.6 Metrics and uncertainty"));
body.push(P("Accuracy: macro-F1 and per-class F1. Calibration: ECE and Brier. Conformal: coverage overall and per class, and mean set size. Workload: auto-labelled share and missed-destroyed rate. For test fires we report the mean ± SD over seeds and a 95% cluster-bootstrap confidence interval over grid cells (1,000 resamples; model, T and thresholds held fixed). For Eaton we report the mean ± SD across the four fold models (T1/T3: 12 runs)."));

// ---------- 5 results ----------
body.push(H1("5. Results"));
body.push(H2("5.1 Accuracy"));
body.push(P("LoRA fine-tuning raised the VLM from 0.31–0.43 to 0.52–0.69 macro-F1, the same level as the CNN (Figure 3, Table 2). All models were most accurate on Santa Rosa and Eaton and least accurate on Portugal. The 'damaged' class was barely learned: its F1 was 0.09–0.22 for T1 and T3 on every test fire (Figure 4). Differences between T1 and T3 are descriptive; we did not run a paired test."));
body.push(...FIG("figA_macroF1.png", "Macro-F1 by test fire and model (seed mean; whiskers: 95% cluster-bootstrap CI for test fires). Eaton (shaded) is the external test, averaged over the four fold models."));
body.push(...FIG("figA2_perclassF1.png", "Per-class F1 for T3 (seed mean). The 'damaged' class stays below 0.25 on every fire.", 6.2));
body.push(...TAB("Accuracy by model and fire. Test fires: mean ± SD over seeds, 95% CI from the cluster bootstrap; Eaton: mean ± SD across fold models.",
  ["Model", "Evaluation", "Macro-F1", "95% CI", "F1 no damage", "F1 damaged", "F1 destroyed"], T.acc.map(r => [short(r[0]), ...r.slice(1)]), [1.6, 1.7, 1.2, 1.2, 1.1, 1.1, 1.1]));
body.push(H2("5.2 Calibration (RQ1)"));
body.push(P("After temperature scaling, T1 and T3 were close to calibrated on every fire: ECE 0.010–0.036 (Table 3, Figure 5). T2 was strongly overconfident: its fitted temperature was 6.8–11.9, and its ECE was still 0.07–0.23 after scaling. Temperature scaling changed T1 and T3 only slightly because they were already well calibrated (T between 0.8 and 1.5)."));
body.push(...FIG("fig1_reliability.png", "Reliability diagrams before (grey, dashed) and after temperature scaling, per fire (columns) and model (rows). The diagonal is perfect calibration. Pooled ECE values differ slightly from the per-run means in Table 3."));
body.push(...TAB("Calibration before and after temperature scaling (T fitted on the calibration split).",
  ["Model", "Evaluation", "T", "ECE before", "ECE after", "Brier before", "Brier after"], T.cal.map(r => [short(r[0]), ...r.slice(1)]), [1.6, 1.7, 1.2, 1.1, 1.1, 1.1, 1.1]));
body.push(H2("5.3 Coverage of prediction sets (RQ2)"));
body.push(P("With Mondrian sets, coverage of destroyed homes met the 90% target on Santa Rosa (0.97–0.99) and on Eaton (0.93–0.99), but not on Woolsey (0.69–0.83), Pinery (0.46–0.71) or Portugal (0.24–0.40) (Figure 6, Table A1). Overall coverage on the test fires ranged from 0.72 to 0.97 and was mostly below 0.90. Conformal coverage guarantees assume that the test data are exchangeable with the calibration data; a new fire in another country, with another sensor and building style, breaks that assumption. Non-randomised APS and ordinal sets reduced to the single top class for T1 and T3 (mean set size 1.00), because their calibration accuracy was above 0.90, so the threshold was zero."));
body.push(...FIG("figC_destroyed_coverage.png", "Coverage of destroyed homes by Mondrian prediction sets at α = 0.10 (target 0.90, red dashed line)."));
body.push(...FIG("fig2_coverage_alpha.png", "Empirical versus nominal coverage for Mondrian sets across α, overall (top) and for destroyed homes (bottom). Markers show α = 0.10; points below the diagonal under-cover."));
body.push(H2("5.4 Inspector workload (RQ3)"));
body.push(P("On the external Eaton Fire, the routing rule worked as intended. With APS sets, T3 auto-labelled 93.4% ± 4.4% of buildings (about 7,900 of 8,457) and missed 1.0% ± 0.6% of destroyed homes; T1 auto-labelled 91.0% and missed 2.8% (Figure 8, Table A2). Figure 9 maps one run. On the xBD test fires, the same rule kept missed-destroyed low only on Santa Rosa (0.9–1.1%). On Woolsey, Pinery and Portugal it missed 9.4–42.7% of destroyed homes while still auto-labelling 90–95% of buildings: the models were confidently wrong rather than unsure. In one recorded failure, T3 fold 4 seed 1 chose α = 0.5, auto-labelled all of Portugal and missed 54% of its destroyed homes. The rule protects only 'destroyed'; most truly damaged houses were auto-labelled as another class, and the error rate among auto-labelled Eaton buildings was 6.3% for T3."));
body.push(...FIG("figD_routing.png", "Routing with APS sets (α chosen on calibration fires). Left: share of buildings auto-labelled. Right: share of destroyed homes auto-labelled as another class (target ≤ 5%). Whiskers: 95% cluster-bootstrap CI."));
body.push(...FIG("fig5_eaton_map.png", "Eaton Fire, one run (T3 fold 1 seed 0): auto-labelled and routed buildings under APS (top) and Mondrian (bottom) sets.", 5.6));
body.push(...FIG("fig3_workload.png", "Workload trade-off traced over α: auto-labelled share versus missed-destroyed rate for APS (top) and Mondrian (bottom). Markers show each run's operating point chosen on the calibration fires."));
body.push(...FIG("fig4_examples.png", "Eaton examples (T3 fold 1 seed 0, Mondrian sets). Each pair shows pre and post crops (64 m wide); p = calibrated probabilities of no damage / damaged / destroyed.", 5.4));
body.push(H2("5.5 Post-hoc analysis: randomised APS (P1)"));
body.push(P("Because the non-randomised APS sets collapsed to one class, we added randomised APS after seeing the results (not preregistered). It lowered T3's missed-destroyed rate on the test fires to 0.9 / 3.7 / 9.2 / 15.1% at 72–83% auto-labelled, and to 0.6% on Eaton at 80% auto-labelled (Table 4). These numbers are exploratory and are not a headline result."));
body.push(...TAB("POST-HOC (P1): routing with randomised APS under A1. Not preregistered.",
  ["Model", "Evaluation", "Auto-labelled", "Missed destroyed", "Missed 95% CI"], T.post.map(r => [short(r[0]), ...r.slice(1)]), [1.6, 1.9, 1.3, 1.3, 1.3]));
body.push(H2("5.6 Added analysis: recalibrating on the new fire (E1)"));
body.push(P("If inspectors first label a small batch of houses on the new fire, can that batch replace the calibration fires? This analysis was designed after the main results were seen; its rules were committed before computing (commit 64faa7f). We drew samples of about 100, 200 and 300 buildings from each target fire by whole grid cells (20 repeats each), refitted T, the conformal thresholds and the routing α on the sample, and evaluated on the rest of the fire, comparing with the original calibration on the same remaining buildings. A random-house sample was run as a check."));
body.push(P("Recalibration restored coverage of destroyed homes on every shifted fire (T3, Mondrian: Woolsey 0.75 → 0.90–0.92, Pinery 0.60 → 0.89–0.97, Portugal 0.30 → 0.91–0.98). It did not restore the 5% miss target: with APS routing, missed destroyed fell (Pinery 20.2% → 8.0–12.3%, Portugal 38.3% → 12.1–13.8%) but stayed above 5% on average, met in only 30–50% of repeats, and the auto-labelled share dropped (Portugal 95% → 67–69%). Samples from Pinery and Portugal held only 6–16 destroyed homes, too few to check a 5% rate. On Santa Rosa and Eaton, where the original calibration already worked, recalibration only added sampling noise (missed 1% → 2–4%). T1 and random-house samples gave the same picture (Figure 12, Table A3). The analysis assumes that inspector labels equal the dataset labels."));
body.push(...FIG("figE_recalibration.png", "E1 (added analysis, T3, grid-cell samples, mean of 20 repeats): calibrating on other fires (grey) versus on a local sample of about 100, 200 or 300 buildings (greens). Left: coverage of destroyed homes (Mondrian). Right: missed destroyed (APS routing)."));

// ---------- 6 discussion ----------
body.push(H1("6. Discussion"));
body.push(H2("6.1 What worked"));
body.push(P("Fine-tuning a general vision-language model with LoRA on building crops was enough to match a purpose-built CNN, and both produced well-calibrated probabilities. On the external Eaton Fire, a field-inspected event seven to ten years after the training fires and from a different satellite pair, calibrated prediction sets let more than nine in ten buildings be labelled without a visit while missing about 1% of destroyed homes. For a fire similar to past ones, this would reduce field work substantially."));
body.push(H2("6.2 What did not work"));
body.push(P("The guarantees came from the calibration fires and did not hold on fires that looked different. On Portugal and Pinery the models were confidently wrong about destroyed homes, which conformal sets calibrated elsewhere cannot detect. A few hundred local labels fixed coverage but not the miss rate, because those fires have few destroyed homes and a 5% rate cannot be estimated from a dozen examples. The 'damaged' class was not learned by any model, in part because it is rare (1–6%) and in part because many DINS 'Affected 1–9%' houses look intact from above."));
body.push(H2("6.3 Changes to the preregistered plan"));
body.push(B([{ text: "A1 (amendment, proposed after test results were seen): ", bold: true }, "with LAC, larger α gives more empty sets, so the 'largest α' rule always picked the grid edge (0.5) and auto-labelled few buildings. A1 maximises the calibration auto-labelled share subject to ≤ 5% missed destroyed. The original-rule results are kept in the full tables; A1 changes only the LAC rows."]));
body.push(B([{ text: "P1 (post-hoc): ", bold: true }, "randomised APS/ordinal sets, added because the non-randomised sets collapsed to one class for T1 and T3."]));
body.push(B([{ text: "E1 (added analysis): ", bold: true }, "few-shot recalibration on the target fire (Section 5.6)."]));
body.push(H2("6.4 Limitations"));
body.push(B("Only four distinct xBD wildfires plus one external fire; results on other fires and sensors may differ."));
body.push(B("DINS labels are field observations; some 'damaged' houses are not visible from above, which caps achievable accuracy for that class."));
body.push(B("Temperature and conformal thresholds were fitted on the same calibration split; T is a single parameter, so the effect is small but not zero."));
body.push(B("T1 versus T3 comparisons are descriptive; the confidence intervals are per model and not paired."));
body.push(B("xBD and Maxar Open Data are licensed for non-commercial use; an operational tool would need other imagery and re-validation."));
body.push(H2("6.5 Future work"));
body.push(P("Weighted conformal prediction under covariate shift (Tibshirani et al., 2019) could reweight calibration buildings toward the new fire; a shift detector could flag when a fire is unlike the training fires and switch to full inspection or local recalibration; more fires and sensors, and a destroyed-versus-not formulation, would test generality."));

// ---------- 7 conclusion ----------
body.push(H1("7. Conclusion"));
body.push(P("Calibrated vision-language and CNN models, combined with conformal prediction sets, can triage post-wildfire damage inspections when the new fire resembles past fires: on the 2025 Eaton Fire, 93% of buildings could be auto-labelled with about 1% of destroyed homes missed. The same guarantees broke on fires that looked different, and a small local sample restored coverage but not the miss target. Knowing when a fire is 'new' is therefore as important as the classifier itself."));

// ---------- contributions, data, refs ----------
body.push(H1("Team Contributions"));
body.push(P("Ziyad ElFayoumy: data acquisition and preparation, all modelling and analysis, tables and figures. Ayman Saeed and Yeganeh: second-opinion review of methods and results, report writing and presentation. (To be confirmed by the team before submission.)"));
body.push(H1("Code and Data Availability"));
body.push(P("All code, the preregistration file, prediction files, tables and figures are in the project repository WildfireDamageCP (git; analysis code in src/, rules in configs/preregistration.md, full tables in results/tables/report_tables.md and e1_summary.csv). The use of AI tools for coding was permitted by the course instructor; Claude (Anthropic) was used for coding and drafting, and all numbers were taken from the generated result tables."));
body.push(H1("References"));
const refs = [
  "Angelopoulos, A. N., & Bates, S. (2021). A gentle introduction to conformal prediction and distribution-free uncertainty quantification. arXiv:2107.07511.",
  "Azad, A., Hossain, M. S., Shanto, M. S. H., Rahman, M. S., & Parvez, M. R. (2025). The art of saying \"maybe\": A conformal lens for uncertainty benchmarking in VLMs. arXiv:2509.13379 (preprint).",
  "CAL FIRE. DINS 2025 Eaton Public View. Data.gov. https://catalog.data.gov/dataset/dins-2025-eaton-public-view",
  "Chen, H., Song, J., Dietrich, O., et al. (2025). BRIGHT: A globally distributed multimodal building damage assessment dataset with very-high-resolution for all-weather disaster response. Earth System Science Data, 17, 6217. arXiv:2501.06019.",
  "Cheng, C.-S., et al. (2022). Uncertainty-aware convolutional neural network for explainable artificial intelligence-assisted disaster damage assessment. Structural Control and Health Monitoring. [DOI to be added]",
  "Guo, C., Pleiss, G., Sun, Y., & Weinberger, K. Q. (2017). On calibration of modern neural networks. Proceedings of ICML 2017, PMLR 70. https://proceedings.mlr.press/v70/guo17a.html",
  "Gupta, R., Hosfelt, R., Sajeev, S., et al. (2019). xBD: A dataset for assessing building damage from satellite imagery. arXiv:1911.09296.",
  "Hertel, V., et al. (2025). BayeSiamMTL: Uncertainty-aware multitask learning for post-disaster building damage assessment. International Journal of Applied Earth Observation and Geoinformation. [DOI to be added]",
  "Hu, E. J., et al. (2021). LoRA: Low-rank adaptation of large language models. arXiv:2106.09685.",
  "Insurance Bureau of Canada (2024). Insured losses from Jasper wildfire surpass $880 million. https://www.ibc.ca/news-insights/news/insured-losses-from-jasper-wildfire-surpass-880-million",
  "Kshirsagar, S., et al. (2026). Geographic bias analysis and cross-domain generalization in deep learning-based building damage assessment. Remote Sensing. [DOI to be added]",
  "Maxar Open Data Program. Registry of Open Data on AWS. https://registry.opendata.aws/maxar-open-data/",
  "Improving trustworthiness of AI disease severity rating in medical imaging with ordinal conformal prediction sets (2022). MICCAI 2022. arXiv:2207.02238. [authors to be added]",
  "Schweden, C., et al. (2026). Assessing conformal prediction for remote sensing: Application to local climate zone classification. IEEE Transactions on Geoscience and Remote Sensing. [DOI to be added]",
  "Tehrani, S., Xu, Y., Haglund, L., Berg, A., Zhambulova, G., & Felsberg, M. (2026). DisasterInsight: A building-centric benchmark for evaluating vision-language models in disaster response. arXiv:2601.18493 (preprint).",
  "Tibshirani, R. J., Barber, R. F., Candès, E. J., & Ramdas, A. (2019). Conformal prediction under covariate shift. NeurIPS 2019. arXiv:1904.06019.",
  "Wang, J., et al. (2025). DisasterM3: A remote sensing vision-language dataset for disaster damage assessment and response. NeurIPS 2025. arXiv:2505.21089.",
];
refs.forEach(r => body.push(new Paragraph({ spacing: { after: 80 }, indent: { left: 360, hanging: 360 }, children: [new TextRun({ text: r, size: 20 })] })));
body.push(new Paragraph({ spacing: { before: 160 }, children: [new TextRun({ text: "Reference check before submission: the bibliographic details above come from abstracts, dataset pages and repository READMEs, not full texts. Items marked [DOI to be added] or [authors to be added] must be completed and every reference verified against the published version.", italics: true, size: 18, color: "C00000" })] }));

body.push(new Paragraph({ children: [new PageBreak()] }));
body.push(H1("Appendix A. Full Result Tables"));
body.push(P("All values from results/tables (report_tables.md, table4_conformal.csv, table5b_routing_A1.csv, e1_summary.csv). Test fires: mean ± SD over seeds; Eaton: mean ± SD across fold models."));
body.push(...TAB("Conformal sets at α = 0.10: coverage overall and per class, and mean set size (LAC, APS and Mondrian; ordinal sets are identical to APS here and are in the full tables).",
  ["Model", "Method", "Evaluation", "Coverage", "Cov. no dmg", "Cov. damaged", "Cov. destroyed", "Set size"], T.conf.map(r => [short(r[0]), ...r.slice(1)]), [1.5, 1.0, 1.6, 1.1, 1.0, 1.0, 1.1, 0.9], null, "Table A1"));
body.push(...TAB("Routing under amendment A1 (for APS and Mondrian, A1 chose the same α as the preregistered rule 8). Missed destroyed = share of destroyed homes auto-labelled as another class.",
  ["Model", "Method", "Evaluation", "Auto-labelled", "Missed destroyed", "Missed 95% CI", "Error among auto"], T.rout.map(r => [short(r[0]), ...r.slice(1)]), [1.5, 1.0, 1.6, 1.2, 1.2, 1.2, 1.1], null, "Table A2"));
body.push(...TAB("E1 summary (grid-cell sampling, mean over 20 repeats). Sample size is the realised mean with the number of destroyed homes in brackets.",
  ["Model", "Fire", "Calibrated on", "Sample (destroyed)", "Destroyed cov. (Mondrian)", "Auto (APS)", "Missed (APS)", "Repeats ≤ 5%"], T.e1, [0.8, 1.2, 1.2, 1.2, 1.3, 1.0, 1.0, 1.0], null, "Table A3"));

const doc = new Document({
  creator: "WildfireDamageCP team", title: "Knowing When to Ask an Inspector",
  styles: {
    default: { document: { run: { font: FONT, size: 22 } } },
    paragraphStyles: [
      { id: "Heading1", name: "Heading 1", basedOn: "Normal", next: "Normal", quickFormat: true, run: { font: FONT, size: 30, bold: true, color: GREEN }, paragraph: { spacing: { before: 320, after: 140 }, keepNext: true, outlineLevel: 0 } },
      { id: "Heading2", name: "Heading 2", basedOn: "Normal", next: "Normal", quickFormat: true, run: { font: FONT, size: 24, bold: true, color: GREEN }, paragraph: { spacing: { before: 220, after: 100 }, keepNext: true, outlineLevel: 1 } },
    ],
  },
  numbering: { config: [{ reference: "bul", levels: [{ level: 0, format: LevelFormat.BULLET, text: "•", alignment: AlignmentType.LEFT, style: { paragraph: { indent: { left: 540, hanging: 270 } } } }] }] },
  sections: [{ properties: { page: { size: { width: 12240, height: 15840 }, margin: { top: 1440, bottom: 1440, left: 1440, right: 1440 } } },
    footers: { default: new Footer({ children: [new Paragraph({ alignment: AlignmentType.CENTER, children: [new TextRun({ children: [PageNumber.CURRENT], size: 18 })] })] }) },
    children: body }],
});
Packer.toBuffer(doc).then(b => { fs.writeFileSync("/tmp/final/WildfireDamageCP_Report.docx", b); console.log("ok"); });
