// Build docs/WildfireDamageCP_Report.docx from the repository's figures and result tables.
// Usage: python scripts/report/report_data.py /tmp/report_data.json
//        node scripts/report/build_report.js /tmp/report_data.json docs/WildfireDamageCP_Report.docx
const fs = require("fs"), path = require("path");
const D = require("docx");
const { Document, Packer, Paragraph, TextRun, ImageRun, Table, TableRow, TableCell, WidthType, ShadingType,
  AlignmentType, HeadingLevel, BorderStyle, LevelFormat, PageBreak, Footer, PageNumber } = D;

const DATA = JSON.parse(fs.readFileSync(process.argv[2], "utf8"));
const OUT = process.argv[3];
const ROOT = path.resolve(__dirname, "..", "..");
const FIG = (p) => path.join(ROOT, "outputs", "figures", p);
const FONT = "Times New Roman", GREEN = "275D37", W = 9360;

// ---------- helpers ----------
const run = (t) => (typeof t === "string" ? new TextRun({ text: t }) : new TextRun(t));
function P(text, o = {}) {
  return new Paragraph({ children: (Array.isArray(text) ? text : [text]).map(run), alignment: o.align || AlignmentType.JUSTIFIED,
    spacing: { after: 120, line: 276 }, indent: o.indent ? { firstLine: 360 } : undefined, keepNext: o.keepNext });
}
const H1 = (t) => new Paragraph({ heading: HeadingLevel.HEADING_1, children: [new TextRun(t)] });
const H2 = (t) => new Paragraph({ heading: HeadingLevel.HEADING_2, children: [new TextRun(t)] });
const H3 = (t) => new Paragraph({ heading: HeadingLevel.HEADING_3, children: [new TextRun(t)] });
const B = (text) => new Paragraph({ numbering: { reference: "bul", level: 0 }, spacing: { after: 60, line: 276 },
  alignment: AlignmentType.LEFT, children: (Array.isArray(text) ? text : [text]).map(run) });
const N = (text) => new Paragraph({ numbering: { reference: "num", level: 0 }, spacing: { after: 60, line: 276 },
  alignment: AlignmentType.LEFT, children: (Array.isArray(text) ? text : [text]).map(run) });
const b = (t) => ({ text: t, bold: true });
const i = (t) => ({ text: t, italics: true });

let figN = 0, tabN = 0;
function pngSize(f) { const x = fs.readFileSync(f); return [x.readUInt32BE(16), x.readUInt32BE(20)]; }
function FIGURE(file, caption, widthIn = 6.5) {
  const f = FIG(file); const [w, h] = pngSize(f); figN++;
  const wp = widthIn * 96, hp = wp * h / w;
  return [new Paragraph({ alignment: AlignmentType.CENTER, keepNext: true, spacing: { before: 120, after: 60 },
      children: [new ImageRun({ type: "png", data: fs.readFileSync(f), transformation: { width: wp, height: hp },
        altText: { title: `Figure ${figN}`, description: caption, name: `Figure ${figN}` } })] }),
    new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 200 },
      children: [new TextRun({ text: `Figure ${figN}. `, bold: true, size: 20 }), new TextRun({ text: caption, size: 20 })] })];
}
const border = { style: BorderStyle.SINGLE, size: 4, color: "BFBFBF" };
const noB = { style: BorderStyle.NONE, size: 0, color: "FFFFFF" };
function TABLE(caption, header, rows, widths, o = {}) {
  tabN++; const lab = o.label || `Table ${tabN}`; const sz = o.size || 18;
  const tot = widths.reduce((a, c) => a + c, 0); const ws = widths.map((x) => Math.round((x * W) / tot));
  ws[ws.length - 1] += W - ws.reduce((a, c) => a + c, 0);
  const cell = (t, j, head) => new TableCell({ width: { size: ws[j], type: WidthType.DXA },
    shading: head ? { fill: "D9D9D9", type: ShadingType.CLEAR, color: "auto" } : undefined,
    margins: { top: 30, bottom: 30, left: 70, right: 70 },
    borders: { top: border, bottom: border, left: noB, right: noB },
    children: [new Paragraph({ alignment: j < (o.leftCols || 1) ? AlignmentType.LEFT : AlignmentType.CENTER,
      children: [new TextRun({ text: String(t), bold: !!head, size: sz })] })] });
  const tbl = new Table({ width: { size: W, type: WidthType.DXA }, columnWidths: ws,
    rows: [new TableRow({ tableHeader: true, children: header.map((t, j) => cell(t, j, true)) }),
      ...rows.map((r) => new TableRow({ cantSplit: true, children: r.map((t, j) => cell(t, j, false)) }))] });
  const out = [new Paragraph({ alignment: AlignmentType.CENTER, keepNext: true, spacing: { before: 160, after: 80 },
      children: [new TextRun({ text: `${lab}. `, bold: true, size: 20 }), new TextRun({ text: caption, size: 20 })] }), tbl];
  if (o.note) out.push(new Paragraph({ spacing: { before: 60, after: 200 }, children: [new TextRun({ text: o.note, italics: true, size: 18 })] }));
  else out.push(new Paragraph({ spacing: { after: 120 }, children: [] }));
  return out;
}
const pageBreak = () => new Paragraph({ children: [new PageBreak()] });

// ---------- content ----------
const body = [];

// Cover page
body.push(new Paragraph({ spacing: { before: 1800, after: 120 }, alignment: AlignmentType.CENTER,
  children: [new TextRun({ text: "UNIVERSITY OF ALBERTA", bold: true, size: 40, color: GREEN })] }));
body.push(new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 1400 },
  children: [new TextRun({ text: "Department of Civil and Environmental Engineering", size: 24, color: GREEN })] }));
body.push(new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 160 },
  children: [new TextRun({ text: "Knowing When to Ask an Inspector:", size: 36, color: "1F4E79" })] }));
body.push(new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 900 },
  children: [new TextRun({ text: "Calibrated Building-Damage Assessment after Wildfires with Conformal Prediction Sets and Inspector Routing", size: 30, color: "1F4E79" })] }));
for (const [t, s] of [["CIV E 779: Machine Learning for Engineers", 24], ["Group [number]:", 24], ["Ziyad ElFayoumy", 24], ["Ayman Saeed", 24], ["Yeganeh", 24]])
  body.push(new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 100 }, children: [new TextRun({ text: t, size: s })] }));
body.push(new Paragraph({ alignment: AlignmentType.CENTER, spacing: { before: 700 }, children: [new TextRun({ text: "November 2026", size: 24 })] }));
body.push(pageBreak());

// Abstract
body.push(H1("Abstract"));
body.push(P("After a wildfire, inspection crews visit damaged buildings one by one to record their condition. Satellite-based classifiers are much faster, but they rarely say when they are unsure, and their accuracy drops on fires unlike the ones they were trained on. This study tests whether calibrated probabilities and split conformal prediction sets can decide which buildings may be labelled automatically and which should be sent to an inspector, while missing at most 5% of destroyed homes. Three model types were trained on 74,622 buildings from four xBD wildfires: a Siamese ConvNeXt-Tiny CNN (T1), the vision-language model Qwen3-VL-8B-Instruct used zero-shot (T2), and the same model fine-tuned with LoRA (T3). They were evaluated with leave-one-fire-out cross-validation and on 8,457 buildings from the 2025 Eaton Fire labelled by CAL FIRE field inspections. Fine-tuning raised the vision-language model from 0.31–0.43 to 0.52–0.69 macro-F1, matching the CNN, and both were well calibrated after temperature scaling (ECE 0.010–0.036). On Eaton, T3 with APS prediction sets auto-labelled 93% of buildings and missed 1.0% of destroyed homes. The 90% coverage target and the 5% miss target, both set on the training fires, did not transfer to fires that looked different: 9–43% of destroyed homes were missed on Woolsey, Pinery and Portugal, although the models still ranked destroyed homes well (AUROC ≥ 0.93). Additional stress tests showed that a simple confidence threshold saves as much work as conformal routing, that inspecting a few hundred local houses restores the miss target only by routing most buildings to inspectors, and that no method kept the target for single models on the two least familiar fires. Calibrated prediction sets are useful for triage when a new fire resembles past fires; detecting and adapting to unfamiliar fires remains the main open problem."));
body.push(pageBreak());

// 1 Introduction
body.push(H1("1. Introduction"));
body.push(P("Building damage assessment after a wildfire determines where recovery funds, insurance payments and rebuilding permits go. Field inspection is the reference standard, but it is slow and limited by access: after the January 2025 Eaton Fire, CAL FIRE Damage Inspection (DINS) teams recorded 18,428 structures [1]. In Canada, the July 2024 Jasper wildfire caused more than $880 million in insured damage [2]. Deep-learning models trained on pairs of satellite images taken before and after a disaster, such as those developed on the xBD dataset [3], can label thousands of buildings in minutes, but they generalise poorly to new regions [4] and give a label without a reliable statement of how likely it is to be wrong.", { indent: true }));
body.push(P("This project asks a practical question: can a model tell an inspection team which buildings it is sure about, with a known error rate, so that crews visit only the rest? It combines three standard machine-learning tools that, to our knowledge, have not been tested together for building damage under held-out disasters: temperature scaling, which makes predicted probabilities match observed accuracy [5]; split conformal prediction, which turns probabilities into sets of labels with a target coverage [6]; and a routing rule that labels a building automatically only when its set contains a single class, tuned so that at most 5% of destroyed homes are missed.", { indent: true }));
body.push(P("Three research questions guided the main analysis:", { keepNext: true }));
body.push(B([b("RQ1 (calibration): "), "after temperature scaling, how well calibrated are a CNN, a zero-shot vision-language model (VLM) and a LoRA-fine-tuned VLM on wildfires they never saw?"]));
body.push(B([b("RQ2 (coverage): "), "do conformal prediction sets keep their 90% target coverage on held-out fires and on an external, field-inspected fire?"]));
body.push(B([b("RQ3 (workload): "), "while missing at most 5% of destroyed homes, what share of buildings can be labelled without a field visit?"]));
body.push(P("After the main results showed that the guarantees did not transfer to unfamiliar fires, a set of added analyses (Section 4.7) asked whether simpler rules would do as well, whether the 5% target can be kept on a new fire, and whether the conclusions hold for other prompts and models. Figure 1 summarises the approach.", { indent: true }));
body.push(...FIGURE("report/rep_pipeline.png", "Overview of the approach: a model produces class probabilities from pre- and post-fire images, temperature scaling calibrates them, a conformal step turns them into a prediction set, and single-class sets are auto-labelled while larger sets go to an inspector."));

// 2 Literature review
body.push(H1("2. Literature Review"));
body.push(P("xBD [3] provides pre- and post-disaster satellite image pairs with four ordinal damage levels for 19 disasters and underlies most building-damage models. BRIGHT [7] adds optical pre-event and radar post-event images. Recent work applies vision-language models to disaster imagery: DisasterM3 [8] is a large instruction dataset, and DisasterInsight [9] benchmarks building-level VLMs on xBD, including LoRA fine-tuning of Qwen3-VL-8B; both focus on accuracy. Kshirsagar et al. [4] show that top-performing xBD models degrade under geographic shift, especially for intermediate damage levels.", { indent: true }));
body.push(P("Uncertainty in damage assessment has mainly been addressed with Bayesian approaches such as Monte Carlo dropout [10] and BayeSiamMTL [11], which give uncertainty scores but no guaranteed error rate. Conformal prediction has been benchmarked on VLMs for multiple-choice tasks [12], applied to remote-sensing land-cover classification [13] and used for ordinal severity grading in medical imaging [14]. The closest work found is a 2026 conference paper by Soyhan and Elgazzar [15], which reports that a satellite-trained damage classifier transferred to drone imagery becomes confidently wrong on collapsed buildings, that calibration fitted on the source domain fails, and that a small number of target labels or a collapse-aware ranking reduces missed collapses; it does not use conformal sets. Damage-TriageFormer [16] frames building damage typing as a triage problem for the 2025 Los Angeles fires without uncertainty quantification.", { indent: true }));
body.push(P("A targeted search (one Consensus query returning 49 records and six web searches; abstracts only, not a systematic review) found no study that applies conformal prediction sets to building damage on held-out disasters. This project tests such sets for a CNN and two VLMs on held-out wildfires and an external field-inspected fire, expresses the result as an inspector-workload metric, and stress-tests methods for keeping the error target on a new fire.", { indent: true }));

// 3 Dataset
body.push(H1("3. Dataset"));
body.push(H2("3.1 Sources"));
body.push(B([b("xBD / xView2 "), "(full GeoTIFF release, about 55 GB; checksums verified). The four wildfire events are Santa Rosa (California, 2017), Woolsey (California, 2018), Pinery (South Australia, 2015) and Portugal (2017). The xBD events socal-fire and woolsey-fire cover the same area four days apart and were merged into one Woolsey fire to avoid leakage."]));
body.push(B([b("CAL FIRE DINS 2025 Eaton "), "[1]: field-inspection damage records for 18,428 structures."]));
body.push(B([b("Maxar Open Data "), "[20]: a WorldView-3 image pair from 1 January 2025 (before) and 14 January 2025 (after), both cloud-free; 8,457 of the 12,739 non-shed DINS structures fall inside its footprint with valid pixels."]));
body.push(P("BRIGHT was examined and not used because its post-event images are single-band radar, while the models here need colour before-and-after pairs.", { indent: true }));
body.push(H2("3.2 Damage classes"));
body.push(P("Labels from both sources were harmonised into three classes:", { keepNext: true }));
body.push(N([b("No damage: "), "xBD no-damage; DINS No Damage."]));
body.push(N([b("Damaged: "), "xBD minor and major damage; DINS Affected (1–9%), Minor (10–25%) and Major (26–50%)."]));
body.push(N([b("Destroyed: "), "xBD destroyed; DINS Destroyed (more than 50%)."]));
body.push(P("xBD ‘un-classified’, DINS ‘Inaccessible’ and utility or miscellaneous structures were excluded.", { indent: true }));
body.push(H2("3.3 Building crops and examples"));
body.push(P("For every building, a 64 m × 64 m ground square was cut from the pre- and post-fire images and resized to 224 × 224 pixels. A first version padded buildings near xBD tile edges with black (about 20% of crops had more than 25% black pixels); the final version shifts the window inside the tile and records the building’s position in the crop, leaving 0.25% of sampled crops above 25% black. The 138 xBD buildings whose centre fell outside the crop were excluded. An automated overlay check on 30 Eaton buildings found DINS points on or within a few metres of the house and a median pre/post image shift of 2.33 m. Figure 2 shows example crop pairs from Eaton with the red circle that marks the building of interest.", { indent: true }));
body.push(...FIGURE("fig4_examples.png", "Example pre- and post-fire crop pairs from the Eaton Fire (64 m wide), one building drawn at random per category, with the T3 prediction set and calibrated probabilities of no damage / damaged / destroyed.", 5.6));
body.push(H2("3.4 Class distribution and imbalance"));
body.push(P("Table 1 lists the buildings per fire. The damaged class is rare: 1.0–3.3% of buildings in the xBD fires and 6.4% on Eaton. The share of destroyed buildings also varies strongly, from 4.2% on Pinery to 46.2% on Eaton, which affects every metric that depends on the class mix.", { indent: true }));
body.push(...TABLE("Buildings per fire after harmonisation and exclusions.", ["Fire", "Role", "No damage", "Damaged", "Destroyed", "Total"],
  DATA.data, [1.3, 1.6, 1.1, 1, 1, 1], { leftCols: 2, size: 20, note: "xBD total: 74,622 buildings; all buildings including Eaton: 83,079." }));
body.push(H2("3.5 Ground-truth quality"));
body.push(P("xBD labels were assigned by annotators from the satellite images, whereas DINS labels come from field inspections by trained crews walking around each structure. Many DINS ‘Affected 1–9%’ houses look intact from above, which limits what any image-based model can achieve for the damaged class and must be kept in mind when reading the Eaton results.", { indent: true }));

// 4 Methodology
body.push(H1("4. Methodology"));
body.push(H2("4.1 Evaluation design"));
body.push(P("Leave-one-fire-out cross-validation was used: in each of four folds one xBD fire is the test fire, and the other three fires are split into training (70%), validation (10%) and calibration (20%) sets by grid cells of 0.005° × 0.005° (about 500 m), so that neighbouring houses never fall into different sets (Figure 3). Each fold model also scores all 8,457 Eaton buildings, which no model saw during training. The models, metrics, target coverage, routing rule and bootstrap procedure were written down and committed before any model was trained; analyses added later are labelled as such throughout.", { indent: true }));
body.push(...FIGURE("report/rep_design.png", "Leave-one-fire-out design. In each fold one xBD fire is the test fire; the other three are split into training, validation and calibration sets by grid cell. Every fold model also scores the external Eaton Fire."));
body.push(H2("4.2 Models"));
body.push(B([b("T1, CNN: "), "a Siamese ConvNeXt-Tiny with ImageNet weights applied to the pre- and post-fire crops, with a red marker on the target building, class-weighted cross-entropy and early stopping on validation macro-F1; 4 folds × 3 random seeds."]));
body.push(B([b("T2, VLM zero-shot: "), "Qwen3-VL-8B-Instruct [22] with one fixed prompt asking for answer A, B or C. Class probabilities are the softmax over the logits of the three answer letters; one deterministic run over all buildings."]));
body.push(B([b("T3, VLM + LoRA: "), "the same VLM fine-tuned with LoRA [17] (rank 16) using a three-way cross-entropy on the A/B/C logits, at most three epochs, early stopping on validation; 4 folds × 3 seeds."]));
body.push(P("All training and inference ran on NVIDIA H200 GPUs; runs that are compared with each other used the same GPU type.", { indent: true }));
body.push(H2("4.3 Calibration"));
body.push(P("One temperature T per run was fitted on the calibration set by minimising the negative log-likelihood and applied to all buildings [5]. Calibration is reported with the expected calibration error (ECE, 15 equal-width bins of the top-class probability) and the Brier score, before and after scaling.", { indent: true }));
body.push(H2("4.4 Conformal prediction sets"));
body.push(P("Split conformal prediction [6] was applied to the temperature-scaled probabilities at α = 0.10 (target coverage 90%) with four scores: LAC (s = 1 − p_y), non-randomised APS (probability mass ranked strictly above the true class), ordinal-contiguous sets, and Mondrian (class-conditional LAC with one threshold per true class, so that coverage of destroyed homes is targeted separately). The threshold is the ⌈(n + 1)(1 − α)⌉-th smallest calibration score.", { indent: true }));
body.push(H2("4.5 Inspector routing"));
body.push(P("A building is auto-labelled when its prediction set contains exactly one class; otherwise it is routed to an inspector. A destroyed building counts as missed if it is auto-labelled as another class, and the missed-destroyed rate is the share of truly destroyed buildings that are missed. The routing α is chosen on the calibration set from a grid between 0.005 and 0.5: the pre-registered rule takes the largest α whose calibration missed-destroyed rate is at most 5%; amendment A1 instead takes the α that labels the most buildings under the same limit (Section 6.3). The chosen α is then applied unchanged to the test fire and to Eaton.", { indent: true }));
body.push(H2("4.6 Metrics and uncertainty"));
body.push(P("Accuracy is measured with macro-F1 and per-class F1; calibration with ECE and Brier score; prediction sets with coverage (overall and per class) and mean set size; and workload with the auto-labelled share and the missed-destroyed rate. For test fires, results are the mean ± standard deviation over seeds with a 95% cluster-bootstrap confidence interval over grid cells (1,000 resamples). For Eaton, results are the mean ± standard deviation across the four fold models.", { indent: true }));
body.push(H2("4.7 Added analyses"));
body.push(P("Two groups of analyses were defined after the main results had been seen; their rules were committed before they were computed.", { indent: true }));
body.push(B([b("E1, local recalibration: "), "samples of about 100, 200 and 300 buildings were drawn from each target fire by whole grid cells (20 repeats); the temperature, conformal thresholds and routing α were refitted on the sample and evaluated on the rest of the fire."]));
body.push(B([b("E2, stress tests: "), "(i) simple confidence rules (top probability, margin, entropy, agreement between seeds or between T1 and T3) compared with conformal routing under the same 5% rule; (ii) five methods for keeping the limit on a new fire: risk control on the miss rate [19] fitted on calibration data or a local sample (M1), a threshold that adapts as inspections proceed with random audits of auto-labelled houses [24] (M2), label-shift reweighting [23] (M3), a shift alarm (M4) and covariate-shift weighting of calibration houses that look like the new fire [18] (M5); (iii) distribution distances between calibration and target predictions; (iv) a destroyed-versus-not version of the task; (v) a paired bootstrap comparison of T1 and T3; (vi) inspection workload in team-days; and (vii) three alternative prompts, a second zero-shot VLM (Gemma 4 12B [21]) and a 6-epoch training cap for T3. The pre-specified main comparison was M2 with 5% audits against conformal APS routing, for T3 on the destroyed-versus-not task. A method ‘fixes transfer’ if it misses at most 5% of destroyed homes while auto-labelling at least half of the buildings on at least four of the five targets."]));

// 5 Results
body.push(H1("5. Results"));
body.push(H2("5.1 Accuracy"));
body.push(P("LoRA fine-tuning raised the VLM from 0.31–0.43 to 0.52–0.69 macro-F1, the same level as the CNN (Table 2, Figure 4). All models were most accurate on Santa Rosa and Eaton and least accurate on Portugal. The damaged class was barely learned: its F1 stayed between 0.09 and 0.22 for T1 and T3 on every test fire. A paired bootstrap (Section 5.6) found T1 and T3 equivalent within ±0.02 macro-F1 on Santa Rosa, Woolsey and Eaton.", { indent: true }));
body.push(...TABLE("Accuracy by model and fire. Test fires: mean ± SD over seeds with 95% cluster-bootstrap CI; Eaton: mean ± SD across the four fold models.",
  ["Model", "Fire", "Macro-F1", "95% CI", "F1 no damage", "F1 damaged", "F1 destroyed"], DATA.accuracy, [1.4, 1.5, 1.1, 1.1, 1.05, 1.05, 1.05], { leftCols: 2 }));
body.push(...FIGURE("report/figA_macroF1.png", "Macro-F1 by test fire and model (seed mean; whiskers: 95% cluster-bootstrap CI). Eaton is the external test, averaged over the four fold models."));
body.push(H2("5.2 Calibration (RQ1)"));
body.push(P("After temperature scaling, T1 and T3 were close to calibrated on every fire, with ECE between 0.010 and 0.036 (Table 3, Figure 5). T2 was strongly overconfident: its fitted temperature was 6.8–11.9 and its ECE was still 0.07–0.23 after scaling. Scaling changed T1 and T3 only slightly because they were already well calibrated.", { indent: true }));
body.push(...TABLE("Calibration before and after temperature scaling (temperature fitted on the calibration set).",
  ["Model", "Fire", "T", "ECE before", "ECE after", "Brier before", "Brier after"], DATA.calibration, [1.4, 1.5, 1.05, 1.05, 1.05, 1.05, 1.05], { leftCols: 2 }));
body.push(...FIGURE("fig1_reliability.png", "Reliability diagrams before (grey, dashed) and after temperature scaling, per fire (columns) and model (rows). The diagonal is perfect calibration."));
body.push(H2("5.3 Coverage of prediction sets (RQ2)"));
body.push(P("With Mondrian sets, coverage of destroyed homes met the 90% target on Santa Rosa (0.97–0.99) and Eaton (0.93–0.99) but not on Woolsey (0.69–0.83), Pinery (0.46–0.71) or Portugal (0.24–0.40) (Figure 6, Table A1). Conformal guarantees assume that test and calibration data are exchangeable; a new fire in another country, imaged by another sensor and with other building styles, breaks that assumption. Non-randomised APS and ordinal sets reduced to the single top class for T1 and T3 (mean set size 1.00), because their calibration accuracy exceeded 90% and the threshold became zero.", { indent: true }));
body.push(...FIGURE("report/figC_destroyed_coverage.png", "Coverage of destroyed homes by Mondrian prediction sets at α = 0.10 (target 0.90, dashed line)."));
body.push(H2("5.4 Inspector workload (RQ3)"));
body.push(P("On the external Eaton Fire, routing worked as intended: with APS sets, T3 auto-labelled 93.4% of buildings and missed 1.0% of destroyed homes, and T1 auto-labelled 91.0% and missed 2.8% (Figure 7, Figure 8, Table A2). On the xBD test fires, the same rule kept the miss rate low only on Santa Rosa (0.9–1.1%). On Woolsey, Pinery and Portugal it missed 9.4–42.7% of destroyed homes while still auto-labelling 90–95% of buildings: the models were confidently wrong rather than uncertain. In one recorded failure, a T3 Portugal model chose α = 0.5, auto-labelled every building and missed 54% of destroyed homes. The rule protects only the destroyed class: most truly damaged houses were auto-labelled as another class.", { indent: true }));
body.push(...FIGURE("report/figD_routing.png", "Routing with APS sets (α chosen on the calibration fires). Left: share of buildings auto-labelled. Right: share of destroyed homes auto-labelled as another class (target at most 5%). Whiskers: 95% cluster-bootstrap CI."));
body.push(...FIGURE("fig5_eaton_map.png", "Eaton Fire, one T3 model: buildings auto-labelled (correct or wrong) and routed to an inspector under APS (top) and Mondrian (bottom) sets.", 5.8));
body.push(H2("5.5 Local recalibration (added analysis E1)"));
body.push(P("Recalibrating on a few hundred labelled buildings from the new fire restored coverage of destroyed homes on every shifted fire (T3, Mondrian: Woolsey 0.75 to 0.90–0.92, Pinery 0.60 to 0.89–0.97, Portugal 0.30 to 0.91–0.98). It did not restore the 5% miss target: with APS routing, the miss rate fell (Pinery 20.2% to 8.0–12.3%, Portugal 38.3% to 12.1–13.8%) but stayed above 5% on average, and the auto-labelled share dropped (Portugal from 95% to 67–69%). Samples from Pinery and Portugal contained only 6–16 destroyed homes, too few to check a 5% rate (Figure 9, Table A3).", { indent: true }));
body.push(...FIGURE("report/figE_recalibration.png", "Added analysis E1 (T3, grid-cell samples, mean of 20 repeats): calibrating on other fires (grey) versus on a local sample of about 100, 200 or 300 buildings. Left: coverage of destroyed homes (Mondrian). Right: missed destroyed homes (APS routing)."));
body.push(H2("5.6 Stress tests (added analysis E2)"));
body.push(P([b("Simple rules. "), "Accepting the model’s answer whenever its top probability exceeds a cut-off chosen on the calibration set performed within about three percentage points of conformal APS routing on every target. Both kept the 5% limit only on Santa Rosa and Eaton (Table 4). Conformal routing therefore does not save more work than a well-tuned confidence rule; its value lies in a guarantee that can be checked when the new fire resembles the calibration fires."]));
body.push(P([b("Why routing fails. "), "On the destroyed-versus-not task, ranking quality was high on every target (T3 AUROC 0.931 on Portugal to 0.997 on Eaton), so the failures arise from where the calibration-fire cut-off lands on a new fire rather than from poor ranking. Distribution distances between calibration and target predictions did not predict the failures: Eaton was the most distant target yet kept the limit, and Woolsey the least distant yet did not (Figure 12)."]));
body.push(P([b("Repair methods. "), "Figure 10 compares all methods. In the pre-specified main comparison, the adaptive threshold with 5% random audits (M2) reduced missed destroyed homes on Portugal from 46.0% to 6.5% and on Pinery from 20.2% to 14.1%, at the cost of auto-labelling only 24% and 56% of buildings, and kept the limit on two of five targets, the same as conformal APS. Without audits it never observed its own errors and missed 62% of destroyed homes on Portugal (Figure 13). Risk control fitted on 300 locally inspected buildings kept the limit on all five targets but auto-labelled only 20–24% of buildings on Pinery and Portugal. Covariate-shift weighting with T1 image features was the only method that met the success criterion on average (four of five targets; Portugal 5.05%), but for single models it was safe and useful on only one of three Pinery models and none of three Portugal models (Table 5). Label-shift reweighting did not help, and the shift alarm fired on every target, so it could not separate good fires from bad ones. With a stricter 2% limit, conformal APS still missed 10.0% of destroyed homes on Pinery and 20.9% on Portugal, so the conclusions do not depend on the choice of 5%."]));
body.push(...FIGURE("e2/fig7_methods_tradeoff.png", "Work saved versus destroyed homes missed for T3 on the destroyed-versus-not task (limit 5%). Blue: baselines; orange: repair methods. Safe and useful methods lie to the right of the grey line and below the dotted line."));
const em = DATA.e2_methods;
body.push(...TABLE("Methods compared for T3 on the destroyed-versus-not task (limit 5%). Cells: auto-labelled share / missed-destroyed rate.",
  ["Method", "Santa Rosa", "Woolsey", "Pinery", "Portugal", "Eaton", "Safe on", "Safe and useful on"],
  em.slice(1).map((r) => [r[1], r[2], r[3], r[4], r[5], r[6], r[7], r[8]]), [2.6, 1.05, 1.05, 1.05, 1.05, 1.05, 0.65, 0.8], { size: 16,
    note: "Safe: missed destroyed at most 5%. Useful: at least 50% auto-labelled. Test fires: mean over seeds; Eaton: mean over the four fold models." }));
const er = DATA.e2_robust;
body.push(...TABLE("Number of single models that are both safe and useful (T3, destroyed versus not, limit 5%).",
  er[0], er.slice(1), [3, 1, 1, 1, 1, 1], { size: 18 }));
body.push(P([b("T1 versus T3. "), "In a paired cluster bootstrap with the same resamples for both models, T1 and T3 were equivalent in macro-F1 within ±0.02 on Santa Rosa, Woolsey and Eaton, the comparison was inconclusive on Pinery, and T1 was slightly better on Portugal (Table 6, Figure 11). Under APS routing, T3 missed significantly fewer destroyed homes on Woolsey, Pinery, Portugal and Eaton."]));
body.push(...TABLE("Paired difference T3 − T1 with 95% cluster-bootstrap CI.", ["Metric", "Santa Rosa", "Woolsey", "Pinery", "Portugal", "Eaton"],
  DATA.e2_paired, [1.9, 1.5, 1.5, 1.5, 1.5, 1.5], { size: 16 }));
body.push(...FIGURE("e2/fig10_t1_vs_t3.png", "Paired comparison of T3 and T1 with 95% cluster-bootstrap CIs (grey band: ±0.02 equivalence margin for macro-F1)."));
body.push(P([b("Other prompts and models. "), "Three alternative prompts did not improve the zero-shot Qwen model; reversing the order of the answer options lowered macro-F1 to 0.25–0.40, which shows sensitivity to option order (Table 7). A second zero-shot model, Gemma 4 12B, reached macro-F1 0.46–0.64, well above zero-shot Qwen and closer to the fine-tuned model, so fine-tuning matters less with a stronger base model. Doubling the training cap of T3 changed test macro-F1 by at most 0.003."]));
body.push(...TABLE("Vision-language model checks: macro-F1 and destroyed-versus-not AUROC per target.", ["Model / prompt", "Metric", "Santa Rosa", "Woolsey", "Pinery", "Portugal", "Eaton"],
  DATA.e2_vlm, [2.8, 1.3, 0.95, 0.95, 0.95, 0.95, 0.95], { leftCols: 2, size: 16 }));
body.push(P([b("Inspection workload. "), "Expressed as inspection effort at 100 houses per team per day, conformal APS routing on Woolsey (24,976 buildings) required about 37 team-days instead of 250 for full inspection, but missed about 350 destroyed homes. On Portugal, local risk control missed about 26 destroyed homes instead of about 500 but required about 179 team-days instead of 9."]));
body.push(P([b("Second external fire. "), "The 2025 Palisades Fire could not be used as a second external test: the only pre-fire WorldView-3 image in Maxar Open Data covers 1,546 of 10,288 structures, and the pre/post alignment check failed its preset threshold (median shift 5.93 m against 5 m)."]));
body.push(...FIGURE("e2/fig9_shift_vs_gap.png", "Distance between calibration and target predictions (no labels needed) versus the transfer gap of the 5% rule, per model and target.", 4.6));
body.push(...FIGURE("e2/fig8_m2_audits.png", "Adaptive threshold (M2, T3, destroyed versus not): missed destroyed homes (left) and auto-labelled share (right) as a function of the random audit rate.", 6));

// 6 Discussion
body.push(H1("6. Discussion"));
body.push(H2("6.1 What worked"));
body.push(P("Fine-tuning a general vision-language model with LoRA on building crops was enough to match a purpose-built CNN, and both produced well-calibrated probabilities. On the external Eaton Fire, a field-inspected event seven to ten years after the training fires and imaged by a different satellite pair, calibrated prediction sets allowed more than nine in ten buildings to be labelled without a visit while missing about 1% of destroyed homes. For a fire similar to past ones, this would reduce field work substantially.", { indent: true }));
body.push(H2("6.2 What did not work"));
body.push(P("The guarantees came from the calibration fires and did not hold on fires that looked different. On Portugal and Pinery the models were confidently wrong about destroyed homes, which conformal sets calibrated elsewhere cannot detect. The stress tests show that this is a trade-off rather than a modelling gap that a better rule can close: every method that kept the miss target on the two least familiar fires did so by sending most buildings to inspectors, and a shift alarm based on the model’s predictions could not tell good fires from bad ones. A few hundred local labels fixed coverage but not the miss rate, because those fires have few destroyed homes and a 5% rate cannot be estimated from a dozen examples. The damaged class was not learned by any model, partly because it is rare and partly because many lightly damaged houses look intact from above.", { indent: true }));
body.push(H2("6.3 Changes to the pre-registered plan"));
body.push(B([b("A1 (amendment, proposed after test results were seen): "), "with LAC, larger α gives more empty sets, so the ‘largest α’ rule always chose the grid edge (0.5) and auto-labelled few buildings. A1 maximises the auto-labelled share under the same 5% limit; it changes only the LAC results, and the original-rule results are kept."]));
body.push(B([b("P1 (post-hoc): "), "randomised APS and ordinal sets, added because the non-randomised sets collapsed to one class for T1 and T3."]));
body.push(B([b("E1 and E2 (added analyses): "), "local recalibration and the stress tests of Sections 5.5 and 5.6, defined after the main results and labelled as such in every table."]));
body.push(H2("6.4 Limitations"));
body.push(B("Only four distinct xBD wildfires and one external fire could be used; the planned second external fire (Palisades) failed its data checks."));
body.push(B("Many methods were compared on five targets; one main comparison was fixed in advance, and all other results should be read as secondary."));
body.push(B("DINS labels are field observations, so some damaged houses are not visible from above, which caps achievable accuracy for that class."));
body.push(B("The temperature and conformal thresholds were fitted on the same calibration set; the temperature is a single parameter, so the effect is small but not zero."));
body.push(B("Zero-shot VLM scores are not bit-identical across GPU types (logit differences up to about 1 between two GPU types), so compared VLM runs were scored on the same hardware."));
body.push(B("xBD and Maxar Open Data are licensed for non-commercial use; an operational tool would need other imagery and new validation."));
body.push(H2("6.5 Future work"));
body.push(P("The most promising lead is covariate-shift weighting based on image features, which should be confirmed on new fires and with single models rather than seed averages. Further steps are a second external fire with well-aligned imagery, shift detection that uses image features instead of predictions, and a destroyed-versus-not formulation designed around inspection practice.", { indent: true }));
body.push(H2("6.6 Conclusion"));
body.push(P("Calibrated CNN and vision-language models, combined with conformal prediction sets, can triage post-wildfire damage inspections when the new fire resembles past fires: on the 2025 Eaton Fire, 93% of buildings could be auto-labelled with about 1% of destroyed homes missed. The same guarantees broke on fires that looked different, and none of the tested repairs kept the miss target while still saving most of the inspection work on the least familiar fires. Recognising when a fire is new is therefore as important as the classifier itself.", { indent: true }));

body.push(H1("Team Contributions"));
body.push(P("Ziyad ElFayoumy: data acquisition and preparation, modelling and analysis, tables and figures. Ayman Saeed and Yeganeh: review of methods and results, the analysis plan for the added analyses, report writing and presentation. [To be confirmed by the team before submission.]"));
body.push(H1("Code and Data Availability"));
body.push(P("Code, analysis rules, per-building predictions, result tables and figures are in the project repository (GitHub: Ziyad-HF/WildfireDamageCP). The use of AI tools for coding was permitted by the course instructor; Claude (Anthropic) was used for coding and drafting, and all numbers were taken from the generated result tables."));

// References
body.push(H1("References"));
const REFS = [
  "CAL FIRE, “DINS 2025 Eaton Public View,” Data.gov. [Online]. Available: https://catalog.data.gov/dataset/dins-2025-eaton-public-view",
  "Insurance Bureau of Canada, “Insured losses from Jasper wildfire surpass $880 million,” 2024. [Online]. Available: https://www.ibc.ca/news-insights/news/insured-losses-from-jasper-wildfire-surpass-880-million",
  "R. Gupta et al., “xBD: A dataset for assessing building damage from satellite imagery,” arXiv:1911.09296, 2019.",
  "S. Kshirsagar et al., “Geographic bias analysis and cross-domain generalization in deep learning-based building damage assessment,” Remote Sensing, 2026. [DOI to be added]",
  "C. Guo, G. Pleiss, Y. Sun, and K. Q. Weinberger, “On calibration of modern neural networks,” in Proc. ICML, PMLR 70, 2017. [Online]. Available: https://proceedings.mlr.press/v70/guo17a.html",
  "A. N. Angelopoulos and S. Bates, “A gentle introduction to conformal prediction and distribution-free uncertainty quantification,” arXiv:2107.07511, 2021.",
  "H. Chen et al., “BRIGHT: A globally distributed multimodal building damage assessment dataset with very-high-resolution for all-weather disaster response,” Earth System Science Data, vol. 17, p. 6217, 2025. arXiv:2501.06019.",
  "J. Wang et al., “DisasterM3: A remote sensing vision-language dataset for disaster damage assessment and response,” in Proc. NeurIPS, 2025. arXiv:2505.21089.",
  "S. Tehrani et al., “DisasterInsight: A building-centric benchmark for evaluating vision-language models in disaster response,” arXiv:2601.18493, 2026 (preprint).",
  "C.-S. Cheng et al., “Uncertainty-aware convolutional neural network for explainable artificial intelligence-assisted disaster damage assessment,” Structural Control and Health Monitoring, 2022. [DOI to be added]",
  "V. Hertel et al., “BayeSiamMTL: Uncertainty-aware multitask learning for post-disaster building damage assessment,” Int. J. Applied Earth Observation and Geoinformation, 2025. [DOI to be added]",
  "A. Azad et al., “The art of saying ‘maybe’: A conformal lens for uncertainty benchmarking in VLMs,” arXiv:2509.13379, 2025 (preprint).",
  "C. Schweden et al., “Assessing conformal prediction for remote sensing: Application to local climate zone classification,” IEEE Trans. Geoscience and Remote Sensing, 2026. [DOI to be added]",
  "“Improving trustworthiness of AI disease severity rating in medical imaging with ordinal conformal prediction sets,” in Proc. MICCAI, 2022. arXiv:2207.02238. [Authors to be added]",
  "M. E. Soyhan and K. Elgazzar, “From satellite to UAV imagery: Calibration and collapse-aware triage for trustworthy post-earthquake building damage assessment,” in Proc. UBMK, 2026, paper 3319. [Listed in the conference programme; proceedings details to be verified]",
  "Y. Xiao et al., “Damage-TriageFormer: A foundation-model framework for typology-based building damage assessment from mono-temporal imagery,” arXiv:2606.12248, 2026.",
  "E. J. Hu et al., “LoRA: Low-rank adaptation of large language models,” arXiv:2106.09685, 2021.",
  "R. J. Tibshirani, R. F. Barber, E. J. Candès, and A. Ramdas, “Conformal prediction under covariate shift,” in Proc. NeurIPS, 2019. arXiv:1904.06019.",
  "A. N. Angelopoulos et al., “Conformal risk control,” in Proc. ICLR, 2024. arXiv:2208.02814. [Details to be verified]",
  "Maxar Open Data Program, Registry of Open Data on AWS. [Online]. Available: https://registry.opendata.aws/maxar-open-data/",
  "Google, “Gemma 4 12B (instruction-tuned),” model card, Hugging Face. [Online]. Available: https://huggingface.co/google/gemma-4-12B-it",
  "Qwen Team, “Qwen3-VL-8B-Instruct,” model card, Hugging Face. [Online]. Available: https://huggingface.co/Qwen/Qwen3-VL-8B-Instruct",
  "Z. C. Lipton, Y.-X. Wang, and A. J. Smola, “Detecting and correcting for label shift with black box predictors,” in Proc. ICML, 2018. [Recalled from memory; to be verified]",
  "I. Gibbs and E. J. Candès, “Adaptive conformal inference under distribution shift,” in Proc. NeurIPS, 2021. [Recalled from memory; to be verified]",
];
REFS.forEach((r, k) => body.push(new Paragraph({ spacing: { after: 80 }, indent: { left: 540, hanging: 540 }, alignment: AlignmentType.LEFT,
  children: [new TextRun({ text: `[${k + 1}]\t`, size: 22 }), new TextRun({ text: r, size: 22 })] })));
body.push(new Paragraph({ spacing: { before: 120 }, children: [new TextRun({ text: "Reference check before submission: details come from abstracts, dataset pages and repository pages, not full texts. Items marked [to be added] or [to be verified] must be completed, and every reference checked against the published version.", italics: true, size: 20 })] }));

// Appendix
body.push(pageBreak());
body.push(H1("Appendix A. Full Result Tables"));
body.push(P("Test fires: mean ± SD over seeds; Eaton: mean ± SD across the four fold models. All values are taken from the result tables in the project repository."));
body.push(...TABLE("Conformal prediction sets at α = 0.10: coverage overall and per class, and mean set size (ordinal sets are identical to APS here).",
  ["Model", "Method", "Fire", "Coverage", "No damage", "Damaged", "Destroyed", "Set size"], DATA.conformal, [1.35, 0.9, 1.15, 1.05, 1.05, 1.05, 1.05, 0.9],
  { label: "Table A1", leftCols: 3, size: 16 }));
body.push(...TABLE("Routing under amendment A1 (for APS and Mondrian, A1 chose the same α as the pre-registered rule).",
  ["Model", "Method", "Fire", "Auto-labelled", "Missed destroyed", "Missed 95% CI", "Error among auto"], DATA.routing, [1.35, 0.9, 1.15, 1.1, 1.1, 1.2, 1.1],
  { label: "Table A2", leftCols: 3, size: 16 }));
body.push(...TABLE("Local recalibration E1 (grid-cell samples, mean over 20 repeats). Sample: realised size with the number of destroyed homes in brackets.",
  ["Model", "Fire", "Calibrated on", "Sample (destroyed)", "Destroyed coverage (Mondrian)", "Auto (APS)", "Missed (APS)", "Repeats ≤ 5%"],
  DATA.e1, [0.7, 1.1, 1.1, 1.2, 1.3, 0.9, 0.9, 0.9], { label: "Table A3", leftCols: 3, size: 16 }));

// ---------- document ----------
const doc = new Document({
  creator: "WildfireDamageCP", title: "Knowing When to Ask an Inspector",
  styles: {
    default: { document: { run: { font: FONT, size: 24 } } },
    paragraphStyles: [
      { id: "Heading1", name: "Heading 1", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { font: FONT, size: 32, bold: true, color: "1F4E79" }, paragraph: { spacing: { before: 300, after: 140 }, keepNext: true, outlineLevel: 0 } },
      { id: "Heading2", name: "Heading 2", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { font: FONT, size: 26, bold: true, italics: true }, paragraph: { spacing: { before: 200, after: 100 }, keepNext: true, outlineLevel: 1 } },
      { id: "Heading3", name: "Heading 3", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { font: FONT, size: 24, italics: true }, paragraph: { spacing: { before: 160, after: 80 }, keepNext: true, outlineLevel: 2 } },
    ],
  },
  numbering: { config: [
    { reference: "bul", levels: [{ level: 0, format: LevelFormat.BULLET, text: "•", alignment: AlignmentType.LEFT, style: { paragraph: { indent: { left: 720, hanging: 360 } } } }] },
    { reference: "num", levels: [{ level: 0, format: LevelFormat.DECIMAL, text: "%1.", alignment: AlignmentType.LEFT, style: { paragraph: { indent: { left: 720, hanging: 360 } } } }] },
  ] },
  sections: [{
    properties: { page: { size: { width: 12240, height: 15840 }, margin: { top: 1440, bottom: 1440, left: 1440, right: 1440 } }, titlePage: true },
    footers: { default: new Footer({ children: [new Paragraph({ alignment: AlignmentType.CENTER, children: [new TextRun({ children: [PageNumber.CURRENT], size: 20 })] })] }),
      first: new Footer({ children: [new Paragraph({ children: [] })] }) },
    children: body,
  }],
});
Packer.toBuffer(doc).then((buf) => { fs.writeFileSync(OUT, buf); console.log(`wrote ${OUT}: ${figN} figures, ${tabN} tables, ${REFS.length} references`); });
