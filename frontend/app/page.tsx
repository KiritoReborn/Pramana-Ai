"use client";

import { useMemo, useState } from "react";
import {
  ArrowRight,
  BadgeCheck,
  Bell,
  CalendarClock,
  ClipboardList,
  Download,
  ExternalLink,
  FileCheck2,
  FileSpreadsheet,
  Globe2,
  Languages,
  LayoutDashboard,
  LogOut,
  Menu,
  Search,
  SearchCheck,
  ShieldAlert,
  ShieldCheck,
  Upload,
  UploadCloud,
  UserRound,
  Users,
  Loader2
} from "lucide-react";
import {
  uploadBidderDocuments,
  uploadTenderDocument,
  runEvaluation,
  getEvaluationResults,
  getReviewEvidence,
  submitOverride,
  generateReport,
  downloadBlob,
  type EvaluationResult,
  type ReviewEvidence,
  type TenderUploadResponse
} from "../lib/api";

type Role = "bidder" | "officer" | null;
type Verdict = "Eligible" | "Not Eligible" | "Needs Review";
type BidderView = "dashboard" | "tenders" | "uploads" | "submissions" | "help";
type OfficerView = "overview" | "config" | "matrix" | "review" | "reports";

type BidderRecord = {
  id: string;
  bidder: string;
  score: number;
  status: Verdict;
  criterion: string;
  extractedText: string;
  confidence: number;
};

const activeTenders = [
  { id: "KAR-INFRA-2026-019", title: "Smart City CCTV Upgrade", deadline: "30 Apr 2026" },
  { id: "KAR-HEALTH-2026-004", title: "District Hospital IT Modernization", deadline: "04 May 2026" },
  { id: "KAR-EDU-2026-011", title: "Digital Classrooms Supply & Setup", deadline: "12 May 2026" }
];

const extractedCriteria = [
  "Minimum Turnover: 5 Cr",
  "Prior Government Project Experience: 3 years",
  "ISO 27001 Compliance",
  "GST and PAN Validation",
  "Bid Security Declaration Submitted"
];

const bidderMatrix: BidderRecord[] = [
  {
    id: "BID-001",
    bidder: "Nava Tech Systems",
    score: 89,
    status: "Eligible",
    criterion: "ISO 27001 Compliance",
    extractedText: "ISO/IEC 27001:2022 certificate attached and valid till Dec 2027.",
    confidence: 98
  },
  {
    id: "BID-002",
    bidder: "Delta Infra Solutions",
    score: 74,
    status: "Needs Review",
    criterion: "Minimum Turnover: 5 Cr",
    extractedText: "Annual turnover appears as 4.8 Cr in audited statement; scanned copy is blurred.",
    confidence: 62
  },
  {
    id: "BID-003",
    bidder: "Kaveri Digital Works",
    score: 59,
    status: "Not Eligible",
    criterion: "Prior Government Project Experience: 3 years",
    extractedText: "Only one qualifying project found in submitted credentials.",
    confidence: 91
  }
];

function statusClass(status: Verdict): string {
  if (status === "Eligible") return "bg-green-100 text-gov-success ring-1 ring-green-300";
  if (status === "Not Eligible") return "bg-red-100 text-gov-danger ring-1 ring-red-300";
  return "bg-amber-100 text-gov-warning ring-1 ring-amber-300";
}

export default function Home() {
  const [role, setRole] = useState<Role>(null);
  const [uploadProgress] = useState(62);
  const [reviewing, setReviewing] = useState<BidderRecord | null>(null);
  const [overrideVerdict, setOverrideVerdict] = useState<"Eligible" | "Not Eligible">("Eligible");
  const [overrideNote, setOverrideNote] = useState("");
  const [overrideError, setOverrideError] = useState("");
  const [fontScale, setFontScale] = useState(100);
  const [language, setLanguage] = useState<"English" | "Kannada">("English");
  const [activeNav, setActiveNav] = useState("Home");
  const [searchQuery, setSearchQuery] = useState("");
  const [bidderView, setBidderView] = useState<BidderView>("dashboard");
  const [officerView, setOfficerView] = useState<OfficerView>("overview");
  const [selectedTender, setSelectedTender] = useState<string | null>(null);
  const [toast, setToast] = useState<string>("");
  
  // Loading states
  const [isUploading, setIsUploading] = useState(false);
  const [isTenderUploading, setIsTenderUploading] = useState(false);
  const [isEvaluating, setIsEvaluating] = useState(false);
  const [isLoadingEvidence, setIsLoadingEvidence] = useState(false);
  const [isSubmittingOverride, setIsSubmittingOverride] = useState(false);
  const [isGeneratingReport, setIsGeneratingReport] = useState(false);
  
  // File selection states
  const [selectedFiles, setSelectedFiles] = useState<File[]>([]);
  const [selectedTenderFile, setSelectedTenderFile] = useState<File | null>(null);
  
  // Real data states
  const [realExtractedCriteria, setRealExtractedCriteria] = useState<string[]>([]);
  const [realBidderMatrix, setRealBidderMatrix] = useState<BidderRecord[]>([]);
  const [reviewEvidenceData, setReviewEvidenceData] = useState<ReviewEvidence | null>(null);
  const notices = [
    "Corrigendum published for KAR-INFRA-2026-019.",
    "Bid submission window extended till 30 Apr 2026, 5:00 PM.",
    "Mandatory DSC validation before final submission."
  ];
  const quickLinks = ["Tender Search", "Bidder Registration", "Department Circulars", "Awarded Contracts", "FAQs", "Contact Helpdesk"];

  const mySubmissions = useMemo(
    () => [
      { name: "Technical_Proposal.pdf", status: "Pending Evaluation" },
      { name: "PAN_and_GST_Documents.png", status: "Pending Evaluation" },
      { name: "Previous_Project_Experience.pdf", status: "Pending Evaluation" }
    ],
    []
  );

  // API Integration Functions
  const handleFileUpload = async () => {
    if (selectedFiles.length === 0) {
      triggerToast("Please select files to upload");
      return;
    }
    
    setIsUploading(true);
    try {
      const bidderId = `BID-${Date.now()}`; // Generate bidder ID
      const response = await uploadBidderDocuments(selectedFiles, bidderId);
      triggerToast(response.message || "Documents uploaded successfully!");
      setSelectedFiles([]);
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : "Failed to upload documents";
      triggerToast(`Error: ${errorMessage}`);
    } finally {
      setIsUploading(false);
    }
  };

  const handleTenderUpload = async () => {
    if (!selectedTenderFile) {
      triggerToast("Please select a tender document");
      return;
    }
    
    setIsTenderUploading(true);
    try {
      const response = await uploadTenderDocument(selectedTenderFile);
      triggerToast(response.message || "Tender document processed successfully!");
      
      // Update extracted criteria with real data
      if (response.criteria && response.criteria.length > 0) {
        const criteriaDescriptions = response.criteria.map(c => c.description);
        setRealExtractedCriteria(criteriaDescriptions);
      }
      
      setSelectedTenderFile(null);
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : "Failed to upload tender document";
      triggerToast(`Error: ${errorMessage}`);
    } finally {
      setIsTenderUploading(false);
    }
  };

  const handleRunEvaluation = async () => {
    setIsEvaluating(true);
    try {
      // Use real criteria if available, otherwise use mock
      const criteria = realExtractedCriteria.length > 0 ? realExtractedCriteria : extractedCriteria;
      const bidderIds = bidderMatrix.map(b => b.id);
      
      const response = await runEvaluation(bidderIds, criteria);
      triggerToast(response.message || "Evaluation completed successfully!");
      
      // Fetch updated results for each bidder
      const updatedMatrix: BidderRecord[] = [];
      for (const bidderId of bidderIds) {
        try {
          const result = await getEvaluationResults(bidderId);
          updatedMatrix.push({
            id: result.bidder_id,
            bidder: result.bidder_name,
            score: calculateScore(result),
            status: result.final_verdict as Verdict,
            criterion: result.criterion_evaluations[0]?.criterion.description || "",
            extractedText: result.criterion_evaluations[0]?.decision.rationale || "",
            confidence: Math.round(result.criterion_evaluations[0]?.extraction_confidence * 100 || 0)
          });
        } catch (err) {
          console.error(`Failed to fetch results for ${bidderId}:`, err);
        }
      }
      
      if (updatedMatrix.length > 0) {
        setRealBidderMatrix(updatedMatrix);
      }
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : "Failed to run evaluation";
      triggerToast(`Error: ${errorMessage}`);
    } finally {
      setIsEvaluating(false);
    }
  };

  const handleReviewCase = async (row: BidderRecord) => {
    setIsLoadingEvidence(true);
    setReviewing(row);
    
    try {
      const criterionId = `CRIT-${row.criterion.substring(0, 10)}`; // Generate criterion ID
      const evidence = await getReviewEvidence(row.id, criterionId);
      setReviewEvidenceData(evidence);
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : "Failed to load evidence";
      triggerToast(`Error: ${errorMessage}`);
    } finally {
      setIsLoadingEvidence(false);
    }
  };

  const handleConfirmOverride = async () => {
    if (!overrideNote.trim()) {
      setOverrideError("Reviewer Justification is mandatory.");
      return;
    }
    
    if (!reviewing) return;
    
    setIsSubmittingOverride(true);
    setOverrideError("");
    
    try {
      const overrideData = {
        session_id: "", // Will be set by API client
        bidder_id: reviewing.id,
        criterion_id: `CRIT-${reviewing.criterion.substring(0, 10)}`,
        original_verdict: reviewing.status,
        new_verdict: overrideVerdict,
        reviewer_id: "OFFICER-001", // In real app, get from auth
        justification: overrideNote
      };
      
      const response = await submitOverride(overrideData);
      triggerToast(response.message || "Manual override recorded and audit trail updated.");
      
      setReviewing(null);
      setOverrideNote("");
      setReviewEvidenceData(null);
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : "Failed to submit override";
      triggerToast(`Error: ${errorMessage}`);
    } finally {
      setIsSubmittingOverride(false);
    }
  };

  const handleDownloadReport = async (bidderId?: string) => {
    setIsGeneratingReport(true);
    
    try {
      const targetBidderId = bidderId || bidderMatrix[0]?.id || "BID-001";
      const blob = await generateReport(targetBidderId);
      downloadBlob(blob, `pramana-report-${targetBidderId}.pdf`);
      triggerToast("Report generated and downloaded successfully!");
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : "Failed to generate report";
      triggerToast(`Error: ${errorMessage}`);
    } finally {
      setIsGeneratingReport(false);
    }
  };

  // Helper function to calculate score from evaluation result
  const calculateScore = (result: EvaluationResult): number => {
    const total = result.summary.mandatory_satisfied + result.summary.desirable_satisfied;
    const max = Object.values(result.summary).reduce((a, b) => a + b, 0);
    return Math.round((total / max) * 100);
  };

  const confirmOverride = handleConfirmOverride;

  const navItems = ["Home", "Live Tenders", "Corrigendum", "Awarded Contracts", "Circulars", "Helpdesk"];
  const dateLabel = "Saturday, 25 Apr 2026";
  const filteredTenders = activeTenders.filter((tender) =>
    `${tender.id} ${tender.title}`.toLowerCase().includes(searchQuery.toLowerCase())
  );
  const needsReview = bidderMatrix.filter((row) => row.status === "Needs Review");

  const triggerToast = (message: string) => {
    setToast(message);
    setTimeout(() => setToast(""), 2200);
  };

  const downloadAudit = () => handleDownloadReport();

  const GovTopShell = (
    <>
      <div className="border-b border-slate-300 bg-slate-100">
        <div className="mx-auto flex max-w-7xl flex-wrap items-center justify-between gap-2 px-4 py-2 text-xs text-slate-700">
          <div className="flex items-center gap-3">
            <span className="font-semibold">Government of Karnataka</span>
            <span className="hidden text-slate-400 md:inline">|</span>
            <span className="hidden md:inline">Centre for e-Governance</span>
          </div>
          <div className="flex items-center gap-3">
            <button onClick={() => setFontScale((v) => Math.max(90, v - 5))} className="rounded border border-slate-300 bg-white px-1.5 py-0.5" aria-label="Decrease font size">
              A-
            </button>
            <button onClick={() => setFontScale(100)} className="rounded border border-slate-300 bg-white px-1.5 py-0.5" aria-label="Reset font size">
              A
            </button>
            <button onClick={() => setFontScale((v) => Math.min(115, v + 5))} className="rounded border border-slate-300 bg-white px-1.5 py-0.5" aria-label="Increase font size">
              A+
            </button>
            <button
              onClick={() => setLanguage((value) => (value === "English" ? "Kannada" : "English"))}
              className="inline-flex items-center gap-1 rounded border border-slate-300 bg-white px-2 py-0.5"
            >
              <Languages className="h-3 w-3" />
              {language === "English" ? "English / Kannada" : "Kannada / English"}
            </button>
          </div>
        </div>
      </div>

      <header className="border-b-4 border-[#8b0000] bg-white">
        <div className="mx-auto flex max-w-7xl flex-wrap items-center justify-between gap-4 px-4 py-4">
          <div className="flex items-center gap-3">
            <img src="/karnataka-emblem.svg" alt="Government of Karnataka emblem" className="h-14 w-14 rounded-sm border border-slate-200 bg-white object-contain p-1" />
            <div>
              <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">Government e-Procurement Platform</p>
              <h1 className="text-2xl font-bold text-navy-900">Pramana AI</h1>
              <p className="text-sm text-slate-600">Transparent, accountable, AI-assisted public procurement workflow</p>
            </div>
          </div>
          <div className="flex items-center gap-2 text-sm text-slate-600">
            <CalendarClock className="h-4 w-4" />
            <span>{dateLabel}</span>
          </div>
        </div>
      </header>

      <nav className="bg-[#0f2d56] text-white">
        <div className="mx-auto flex max-w-7xl items-center justify-between px-4">
          <ul className="hidden items-center md:flex">
            {navItems.map((item) => (
              <li key={item}>
                <button
                  onClick={() => setActiveNav(item)}
                  className={`border-r border-white/15 px-4 py-3 text-sm hover:bg-white/10 ${activeNav === item ? "bg-white/20 font-semibold" : ""}`}
                >
                  {item}
                </button>
              </li>
            ))}
          </ul>
          <button className="flex items-center gap-2 py-3 text-sm md:hidden">
            <Menu className="h-4 w-4" />
            Menu
          </button>
          <div className="hidden items-center gap-4 md:flex">
            <button onClick={() => setActiveNav("Live Tenders")} className="inline-flex items-center gap-1 text-sm hover:underline">
              <Search className="h-4 w-4" />
              Search Tenders
            </button>
            <button className="inline-flex items-center gap-1 rounded bg-[#8b0000] px-3 py-1.5 text-xs font-semibold">
              <Bell className="h-3.5 w-3.5" />
              Alerts
            </button>
          </div>
        </div>
      </nav>

      <div className="border-b border-[#d4a017]/50 bg-[#fff8e1]">
        <div className="mx-auto flex max-w-7xl items-center gap-2 px-4 py-2 text-sm text-[#7c5700]">
          <Globe2 className="h-4 w-4" />
          <p>Official portal simulation inspired by Karnataka e-governance patterns for realistic procurement workflows. | ಅಧಿಕೃತ ಮಾದರಿ ಪೋರ್ಟಲ್</p>
        </div>
      </div>
    </>
  );

  if (!role) {
    return (
      <main className="min-h-screen bg-[#f3f6fa]">
        {GovTopShell}
        <section className="mx-auto max-w-7xl px-4 py-6">
          <div className="rounded-xl border border-slate-200 bg-white shadow-gov">
            <div className="border-b border-slate-200 bg-slate-50 px-6 py-4">
              <p className="text-xs font-semibold uppercase tracking-[0.2em] text-slate-500">Secure Role Access</p>
              <h2 className="mt-1 text-2xl font-bold text-navy-900">National Public Procurement Console</h2>
              <p className="mt-1 max-w-3xl text-sm text-slate-600">
                Select your role to continue. Every action is time-stamped and audit-logged according to government digital governance standards.
              </p>
            </div>
            <div className="grid gap-6 p-6 md:grid-cols-2">
              <button
                onClick={() => setRole("bidder")}
                className="rounded-xl border border-slate-200 bg-white p-6 text-left shadow-sm transition hover:-translate-y-0.5 hover:border-[#0f2d56]"
              >
                <div className="flex items-center gap-2 text-[#0f2d56]">
                  <UserRound className="h-5 w-5" />
                  <p className="text-sm font-semibold">Bidder Access</p>
                </div>
                <h3 className="mt-3 text-xl font-bold text-navy-900">Log in as Bidder</h3>
                <p className="mt-2 text-sm text-slate-600">
                  Browse live tenders, upload compliance documents, and track evaluations in your submission dashboard.
                </p>
                <span className="mt-4 inline-flex items-center gap-1 text-sm font-semibold text-[#8b0000]">
                  Continue <ArrowRight className="h-4 w-4" />
                </span>
              </button>
              <button
                onClick={() => setRole("officer")}
                className="rounded-xl border border-slate-200 bg-white p-6 text-left shadow-sm transition hover:-translate-y-0.5 hover:border-[#0f2d56]"
              >
                <div className="flex items-center gap-2 text-[#0f2d56]">
                  <ShieldCheck className="h-5 w-5" />
                  <p className="text-sm font-semibold">Procurement Authority Access</p>
                </div>
                <h3 className="mt-3 text-xl font-bold text-navy-900">Log in as Officer</h3>
                <p className="mt-2 text-sm text-slate-600">
                  Configure tender criteria, run eligibility matrix, complete human review overrides, and export final audits.
                </p>
                <span className="mt-4 inline-flex items-center gap-1 text-sm font-semibold text-[#8b0000]">
                  Continue <ArrowRight className="h-4 w-4" />
                </span>
              </button>
            </div>
          </div>
        </section>

        <footer className="border-t border-slate-300 bg-white">
          <div className="mx-auto max-w-7xl px-4 py-4 text-xs text-slate-500">
            Designed, Developed and Hosted by: Centre for e-Governance, Government of Karnataka (UI-inspired prototype)
          </div>
        </footer>
      </main>
    );
  }

  return (
    <main className="min-h-screen bg-[#f3f6fa]" style={{ fontSize: `${fontScale}%` }}>
      {GovTopShell}

      <section className="border-b border-slate-300 bg-white">
        <div className="mx-auto flex max-w-7xl flex-wrap items-center justify-between gap-2 px-4 py-3">
          <div className="flex items-center gap-2">
            <LayoutDashboard className="h-4 w-4 text-[#0f2d56]" />
            <p className="text-sm font-semibold text-navy-900">
              Active Workspace: {role === "bidder" ? "Bidder Dashboard" : "Procurement Officer Dashboard"}
            </p>
          </div>
          <div className="flex items-center gap-2">
            <button onClick={() => triggerToast("User manual will open in the next release.")} className="inline-flex items-center gap-1 rounded border border-slate-300 bg-white px-3 py-1.5 text-xs font-semibold text-slate-700">
              User Manual <ExternalLink className="h-3.5 w-3.5" />
            </button>
          <button
            onClick={() => setRole(null)}
              className="inline-flex items-center gap-2 rounded border border-[#8b0000]/30 bg-[#8b0000] px-3 py-1.5 text-xs font-semibold text-white"
          >
            <LogOut className="h-4 w-4" />
            Switch Role
          </button>
        </div>
        </div>
      </section>
      <section className="border-b border-slate-300 bg-[#f8fafc]">
        <div className="mx-auto grid max-w-7xl gap-4 px-4 py-4 lg:grid-cols-[2fr_1fr]">
          <div className="rounded border border-[#d4a017]/50 bg-[#fffdf5] p-3">
            <p className="text-xs font-semibold uppercase tracking-wide text-[#7c5700]">Latest Notices | ಇತ್ತೀಚಿನ ಸೂಚನೆಗಳು</p>
            <ul className="mt-2 space-y-1 text-sm text-slate-700">
              {notices.map((notice) => (
                <li key={notice}>• {notice}</li>
              ))}
            </ul>
          </div>
          <div className="rounded border border-slate-200 bg-white p-3">
            <p className="text-xs font-semibold uppercase tracking-wide text-slate-600">Quick Links | ತ್ವರಿತ ಕೊಂಡಿಗಳು</p>
            <div className="mt-2 grid grid-cols-2 gap-1 text-sm">
              {quickLinks.map((link) => (
                <button key={link} onClick={() => triggerToast(`${link} page will open in next update.`)} className="rounded px-2 py-1 text-left text-[#0f2d56] hover:bg-slate-100">
                  {link}
                </button>
              ))}
            </div>
          </div>
        </div>
      </section>

      {role === "bidder" ? (
        <section className="mx-auto grid max-w-7xl gap-6 px-4 py-6 lg:grid-cols-[260px_1fr]">
          <aside className="rounded-xl border border-slate-200 bg-white shadow-gov">
            <div className="border-b border-slate-200 px-4 py-3">
              <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">Bidder Menu | ಬಿಡ್ದಾರ ಮೆನು</p>
            </div>
            <div className="p-3">
              {[
                ["dashboard", "Dashboard / ಡ್ಯಾಶ್‌ಬೋರ್ಡ್"],
                ["tenders", "Active Tenders / ಸಕ್ರಿಯ ಟೆಂಡರ್‌ಗಳು"],
                ["uploads", "Document Uploads / ದಸ್ತಾವೇಜು ಅಪ್‌ಲೋಡ್"],
                ["submissions", "My Submissions / ನನ್ನ ಸಲ್ಲಿಕೆಗಳು"],
                ["help", "Helpdesk / ಸಹಾಯ ಕೇಂದ್ರ"]
              ].map(([id, label]) => (
                <button
                  key={id}
                  onClick={() => setBidderView(id as BidderView)}
                  className={`mb-2 w-full rounded px-3 py-2 text-left text-sm ${bidderView === id ? "bg-[#0f2d56] text-white" : "hover:bg-slate-100"}`}
                >
                  {label}
                </button>
              ))}
            </div>
          </aside>
          <div className="grid gap-6">
          {(bidderView === "dashboard" || bidderView === "tenders") && (
          <div className="rounded-xl border border-slate-200 bg-white shadow-gov">
            <div className="border-b border-slate-200 bg-slate-50 px-6 py-4">
              <h2 className="section-title">Tender Discovery & Submission | ಟೆಂಡರ್ ಹುಡುಕಾಟ ಮತ್ತು ಸಲ್ಲಿಕೆ</h2>
            </div>
            <div className="p-6">
            <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
              <div className="relative">
                <Search className="pointer-events-none absolute left-3 top-2.5 h-4 w-4 text-slate-400" />
                <input
                  value={searchQuery}
                  onChange={(event) => setSearchQuery(event.target.value)}
                  placeholder="Search by tender ID or title"
                  className="w-72 rounded border border-slate-300 py-2 pl-9 pr-3 text-sm outline-none ring-navy-500 focus:ring-2"
                />
              </div>
              <p className="text-xs text-slate-500">Current language: {language}</p>
            </div>
            <div className="mb-4 flex items-center gap-2">
              <ClipboardList className="h-5 w-5 text-navy-700" />
              <h2 className="section-title">Active Tenders | ಸಕ್ರಿಯ ಟೆಂಡರ್‌ಗಳು</h2>
            </div>
            <div className="overflow-x-auto">
              <table className="w-full min-w-[640px] text-left text-sm">
                <thead className="bg-navy-50 text-navy-800">
                  <tr>
                    <th className="px-4 py-3">ID</th>
                    <th className="px-4 py-3">Title / ಶೀರ್ಷಿಕೆ</th>
                    <th className="px-4 py-3">Deadline / ಕೊನೆಯ ದಿನ</th>
                    <th className="px-4 py-3">Action / ಕ್ರಮ</th>
                  </tr>
                </thead>
                <tbody>
                  {filteredTenders.map((tender) => (
                    <tr key={tender.id} className="border-b border-slate-200">
                      <td className="px-4 py-3 font-medium text-navy-700">{tender.id}</td>
                      <td className="px-4 py-3">{tender.title}</td>
                      <td className="px-4 py-3">{tender.deadline}</td>
                      <td className="px-4 py-3">
                        <button
                          onClick={() => {
                            setSelectedTender(tender.id);
                            triggerToast(`Tender ${tender.id} opened for application.`);
                          }}
                          className="rounded border border-[#0f2d56] bg-[#0f2d56] px-3 py-1.5 font-medium text-white hover:bg-[#173c70]"
                        >
                          Apply
                        </button>
                      </td>
                    </tr>
                  ))}
                  {filteredTenders.length === 0 && (
                    <tr>
                      <td colSpan={4} className="px-4 py-6 text-center text-slate-500">
                        No tenders match the current search.
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
            </div>
          </div>
          )}

          {(bidderView === "dashboard" || bidderView === "uploads" || bidderView === "submissions") && (
          <div className="grid gap-6 lg:grid-cols-2">
            <div className="rounded-xl border border-slate-200 bg-white p-6 shadow-gov">
              <div className="mb-4 flex items-center gap-2">
                <UploadCloud className="h-5 w-5 text-navy-700" />
                <h2 className="section-title">Document Upload Portal | ದಸ್ತಾವೇಜು ಅಪ್‌ಲೋಡ್ ಪೋರ್ಟಲ್</h2>
              </div>
              <div className="rounded-xl border-2 border-dashed border-navy-300 bg-navy-50/40 p-8 text-center">
                <UploadCloud className="mx-auto h-10 w-10 text-navy-600" />
                <p className="mt-3 font-medium text-navy-800">Drag and drop documents here</p>
                <p className="muted mt-1">Accepted formats: .pdf, .png, .jpg</p>
                <input
                  type="file"
                  id="bidder-file-input"
                  multiple
                  accept=".pdf,.png,.jpg,.jpeg"
                  onChange={(e) => {
                    if (e.target.files) {
                      setSelectedFiles(Array.from(e.target.files));
                      triggerToast(`${e.target.files.length} file(s) selected`);
                    }
                  }}
                  className="hidden"
                />
                <button 
                  onClick={() => document.getElementById('bidder-file-input')?.click()}
                  className="mt-4 rounded border border-[#0f2d56] px-4 py-2 text-sm font-semibold text-[#0f2d56] hover:bg-navy-100"
                  disabled={isUploading}
                >
                  Choose Files
                </button>
                {selectedFiles.length > 0 && (
                  <p className="mt-2 text-sm text-slate-600">
                    {selectedFiles.length} file(s) selected
                  </p>
                )}
              </div>
              <div className="mt-4 flex items-center gap-2">
                <button
                  onClick={handleFileUpload}
                  disabled={isUploading || selectedFiles.length === 0}
                  className="inline-flex items-center gap-1 rounded border border-[#0f2d56] bg-[#0f2d56] px-3 py-1.5 text-sm font-semibold text-white disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {isUploading ? (
                    <>
                      <Loader2 className="h-4 w-4 animate-spin" />
                      Uploading...
                    </>
                  ) : (
                    <>
                      <Upload className="h-4 w-4" />
                      Start Upload
                    </>
                  )}
                </button>
              </div>
              <div className="mt-5">
                <div className="mb-2 flex justify-between text-sm">
                  <span className="font-medium text-slate-700">Upload Progress</span>
                    <span className="font-semibold text-[#8b0000]">{uploadProgress}%</span>
                </div>
                <div className="h-3 rounded-full bg-slate-200">
                    <div className="h-3 rounded-full bg-[#0f2d56]" style={{ width: `${uploadProgress}%` }} />
                </div>
              </div>
            </div>

            <div className="rounded-xl border border-slate-200 bg-white p-6 shadow-gov">
              <div className="mb-4 flex items-center gap-2">
                <FileCheck2 className="h-5 w-5 text-navy-700" />
                <h2 className="section-title">My Submissions | ನನ್ನ ಸಲ್ಲಿಕೆಗಳು</h2>
              </div>
              <ul className="space-y-3">
                {mySubmissions.map((doc) => (
                  <li key={doc.name} className="flex items-center justify-between rounded-lg border border-slate-200 p-3">
                    <span className="font-medium text-slate-700">{doc.name}</span>
                    <span className="rounded-full bg-amber-100 px-3 py-1 text-xs font-semibold text-gov-warning">
                      {doc.status}
                    </span>
                  </li>
                ))}
              </ul>
            </div>
          </div>
          )}
          {bidderView === "help" && (
            <div className="rounded-xl border border-slate-200 bg-white p-6 shadow-gov">
              <h2 className="section-title">Bidder Helpdesk | ಬಿಡ್ದಾರ ಸಹಾಯ ಕೇಂದ್ರ</h2>
              <p className="mt-2 text-sm text-slate-600">For registration, DSC issues, and bid submission support:</p>
              <div className="mt-4 rounded border border-slate-200 bg-slate-50 p-4 text-sm text-slate-700">
                <p>Phone: 080-49203888 / 8904085030</p>
                <p>Email: onehelpdesk@karnataka.gov.in</p>
              </div>
            </div>
          )}
          </div>
        </section>
      ) : (
        <section className="mx-auto grid max-w-7xl gap-6 px-4 py-6 lg:grid-cols-[260px_1fr]">
          <aside className="rounded-xl border border-slate-200 bg-white shadow-gov">
            <div className="border-b border-slate-200 px-4 py-3">
              <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">Officer Menu | ಅಧಿಕಾರಿ ಮೆನು</p>
            </div>
            <div className="p-3">
              {[
                ["overview", "Overview / ಅವಲೋಕನ"],
                ["config", "Tender Configuration / ಟೆಂಡರ್ ಸಂರಚನೆ"],
                ["matrix", "Evaluation Matrix / ಮೌಲ್ಯಮಾಪನ ಮ್ಯಾಟ್ರಿಕ್ಸ್"],
                ["review", "Review Queue / ಪರಿಶೀಲನಾ ಪಟ್ಟಿಗೆ"],
                ["reports", "Audit Reports / ಆಡಿಟ್ ವರದಿ"]
              ].map(([id, label]) => (
                <button
                  key={id}
                  onClick={() => setOfficerView(id as OfficerView)}
                  className={`mb-2 w-full rounded px-3 py-2 text-left text-sm ${officerView === id ? "bg-[#0f2d56] text-white" : "hover:bg-slate-100"}`}
                >
                  {label}
                </button>
              ))}
            </div>
          </aside>
          <div className="grid gap-6">
          {(officerView === "overview" || officerView === "config") && (
          <div className="grid gap-6 lg:grid-cols-3">
            <div className="rounded-xl border border-slate-200 bg-white p-6 shadow-gov lg:col-span-2">
              <div className="mb-4 flex items-center gap-2">
                <FileSpreadsheet className="h-5 w-5 text-navy-700" />
                <h2 className="section-title">Tender Configuration | ಟೆಂಡರ್ ಸಂರಚನೆ</h2>
              </div>
              <div className="rounded-xl border border-slate-200 bg-slate-50 p-4">
                <p className="text-sm font-medium text-slate-700">Master Tender Document</p>
                <div className="mt-2 flex flex-wrap items-center gap-3">
                  <input
                    type="file"
                    id="tender-file-input"
                    accept=".pdf"
                    onChange={(e) => {
                      if (e.target.files && e.target.files[0]) {
                        setSelectedTenderFile(e.target.files[0]);
                        triggerToast(`Selected: ${e.target.files[0].name}`);
                      }
                    }}
                    className="hidden"
                  />
                  <button 
                    onClick={() => {
                      if (selectedTenderFile) {
                        handleTenderUpload();
                      } else {
                        document.getElementById('tender-file-input')?.click();
                      }
                    }}
                    disabled={isTenderUploading}
                    className="rounded border border-[#0f2d56] bg-[#0f2d56] px-3 py-2 text-sm font-medium text-white hover:bg-[#173c70] disabled:opacity-50 disabled:cursor-not-allowed inline-flex items-center gap-2"
                  >
                    {isTenderUploading ? (
                      <>
                        <Loader2 className="h-4 w-4 animate-spin" />
                        Processing...
                      </>
                    ) : selectedTenderFile ? (
                      <>
                        <Upload className="h-4 w-4" />
                        Upload & Process
                      </>
                    ) : (
                      "Upload Master Document"
                    )}
                  </button>
                  <span className="text-sm text-slate-500">
                    {selectedTenderFile ? selectedTenderFile.name : "Tender_Master_v3.pdf"}
                  </span>
                </div>
              </div>
              <div className="mt-5">
                <h3 className="text-sm font-semibold uppercase tracking-wide text-slate-500">Extracted Criteria</h3>
                <ul className="mt-3 grid gap-2 sm:grid-cols-2">
                  {(realExtractedCriteria.length > 0 ? realExtractedCriteria : extractedCriteria).map((criterion) => (
                    <li key={criterion} className="rounded-lg border border-navy-200 bg-navy-50 px-3 py-2 text-sm text-navy-800">
                      {criterion}
                    </li>
                  ))}
                </ul>
              </div>
            </div>

            <div className="rounded-xl border border-slate-200 bg-white p-6 shadow-gov">
              <div className="mb-4 flex items-center gap-2">
                <BadgeCheck className="h-5 w-5 text-navy-700" />
                <h2 className="section-title">Audit Report | ಆಡಿಟ್ ವರದಿ</h2>
              </div>
              <p className="muted">Generate signed final report with eligibility outcomes and reviewer overrides.</p>
              <button 
                onClick={downloadAudit} 
                disabled={isGeneratingReport}
                className="mt-4 inline-flex w-full items-center justify-center gap-2 rounded border border-[#8b0000] bg-[#8b0000] px-4 py-2.5 font-semibold text-white hover:bg-[#9a1111] disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {isGeneratingReport ? (
                  <>
                    <Loader2 className="h-4 w-4 animate-spin" />
                    Generating...
                  </>
                ) : (
                  <>
                    <Download className="h-4 w-4" />
                    Export Final PDF Report
                  </>
                )}
              </button>
            </div>
          </div>
          )}

          {(officerView === "overview" || officerView === "matrix") && (
          <div className="rounded-xl border border-slate-200 bg-white p-6 shadow-gov">
            <div className="mb-4 flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Users className="h-5 w-5 text-navy-700" />
                <h2 className="section-title">The Evaluation Matrix | ಮೌಲ್ಯಮಾಪನ ಮ್ಯಾಟ್ರಿಕ್ಸ್</h2>
              </div>
              <button
                onClick={handleRunEvaluation}
                disabled={isEvaluating}
                className="inline-flex items-center gap-2 rounded border border-[#0f2d56] bg-[#0f2d56] px-3 py-1.5 text-sm font-semibold text-white hover:bg-[#173c70] disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {isEvaluating ? (
                  <>
                    <Loader2 className="h-4 w-4 animate-spin" />
                    Evaluating...
                  </>
                ) : (
                  "Run Evaluation"
                )}
              </button>
            </div>
            <div className="overflow-x-auto">
              <table className="w-full min-w-[720px] text-left text-sm">
                <thead className="bg-navy-50 text-navy-800">
                  <tr>
                    <th className="px-4 py-3">Bidder ID</th>
                    <th className="px-4 py-3">Bidder Name</th>
                    <th className="px-4 py-3">AI Score</th>
                    <th className="px-4 py-3">Status</th>
                    <th className="px-4 py-3">Action</th>
                  </tr>
                </thead>
                <tbody>
                  {(realBidderMatrix.length > 0 ? realBidderMatrix : bidderMatrix).map((row) => (
                    <tr key={row.id} className="border-b border-slate-200">
                      <td className="px-4 py-3 font-medium text-navy-700">{row.id}</td>
                      <td className="px-4 py-3">{row.bidder}</td>
                      <td className="px-4 py-3">{row.score}</td>
                      <td className="px-4 py-3">
                        <span className={`rounded-full px-3 py-1 text-xs font-semibold ${statusClass(row.status)}`}>
                          {row.status}
                        </span>
                      </td>
                      <td className="px-4 py-3">
                        {row.status === "Needs Review" ? (
                          <button
                            onClick={() => handleReviewCase(row)}
                            disabled={isLoadingEvidence}
                            className="inline-flex items-center gap-1 rounded border border-amber-300 bg-amber-50 px-3 py-1.5 font-medium text-amber-800 hover:bg-amber-100 disabled:opacity-50 disabled:cursor-not-allowed"
                          >
                            {isLoadingEvidence ? (
                              <>
                                <Loader2 className="h-4 w-4 animate-spin" />
                                Loading...
                              </>
                            ) : (
                              <>
                                <SearchCheck className="h-4 w-4" />
                                Review Case
                              </>
                            )}
                          </button>me="h-4 w-4" />
                            Review Case
                          </button>
                        ) : (
                          <span className="text-slate-400">No action required</span>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
          )}
          {officerView === "review" && (
            <div className="rounded-xl border border-slate-200 bg-white p-6 shadow-gov">
              <h2 className="section-title">Needs Review Queue | ಪರಿಶೀಲನೆ ಅಗತ್ಯ ಪಟ್ಟಿಗೆ</h2>
              <p className="mt-2 text-sm text-slate-600">Priority cases requiring human validation due to low AI confidence.</p>
              <div className="mt-4 space-y-3">
                {(realBidderMatrix.length > 0 ? realBidderMatrix : bidderMatrix).filter((row) => row.status === "Needs Review").map((row) => (
                  <div key={row.id} className="flex flex-wrap items-center justify-between gap-3 rounded border border-amber-200 bg-amber-50 p-3">
                    <div>
                      <p className="font-semibold text-slate-800">{row.bidder}</p>
                      <p className="text-sm text-slate-600">
                        {row.criterion} | OCR Confidence {row.confidence}%
                      </p>
                    </div>
                    <button
                      onClick={() => handleReviewCase(row)}
                      disabled={isLoadingEvidence}
                      className="rounded border border-amber-300 bg-white px-3 py-1.5 text-sm font-semibold text-amber-800 disabled:opacity-50 disabled:cursor-not-allowed inline-flex items-center gap-2"
                    >
                      {isLoadingEvidence ? (
                        <>
                          <Loader2 className="h-4 w-4 animate-spin" />
                          Loading...
                        </>
                      ) : (
                        "Open Review"
                      )}
                    </button>
                  </div>
                ))}
              </div>
            </div>
          )}
          {officerView === "reports" && (
            <div className="rounded-xl border border-slate-200 bg-white p-6 shadow-gov">
              <h2 className="section-title">Reports & Exports | ವರದಿ ಮತ್ತು ರಫ್ತು</h2>
              <p className="mt-2 text-sm text-slate-600">Download officer-ready reports for approval committees and audit agencies.</p>
              <div className="mt-4 flex flex-wrap gap-3">
                <button 
                  onClick={downloadAudit} 
                  disabled={isGeneratingReport}
                  className="rounded border border-[#8b0000] bg-[#8b0000] px-4 py-2 text-sm font-semibold text-white disabled:opacity-50 disabled:cursor-not-allowed inline-flex items-center gap-2"
                >
                  {isGeneratingReport ? (
                    <>
                      <Loader2 className="h-4 w-4 animate-spin" />
                      Generating...
                    </>
                  ) : (
                    "Export Final PDF Report"
                  )}
                </button>
                <button onClick={() => triggerToast("CSV export generated.")} className="rounded border border-[#0f2d56] px-4 py-2 text-sm font-semibold text-[#0f2d56]">
                  Export Matrix CSV
                </button>
              </div>
            </div>
          )}
          </div>
        </section>
      )}

      {reviewing && (
        <div className="fixed inset-0 z-20 flex items-center justify-center bg-slate-900/55 p-4">
          <div className="max-h-[92vh] w-full max-w-6xl overflow-auto rounded-lg border border-slate-300 bg-white">
            <div className="flex items-center justify-between border-b border-slate-200 bg-slate-50 px-6 py-4">
              <div>
                <h3 className="text-xl font-semibold text-navy-800">Human Review - {reviewing.bidder}</h3>
                <p className="text-sm text-slate-500">Bidder ID: {reviewing.id}</p>
              </div>
              <button onClick={() => setReviewing(null)} className="rounded-md border border-slate-300 px-3 py-1.5 text-sm">
                Close
              </button>
            </div>

            <div className="grid gap-0 border-b border-slate-200 lg:grid-cols-2">
              <div className="border-r border-slate-200 p-6">
                <div className="mb-4 flex items-center gap-2 border-b border-slate-200 pb-3">
                  <ShieldAlert className="h-5 w-5 text-gov-warning" />
                  <h4 className="font-semibold text-navy-800">AI Analysis</h4>
                </div>
                {isLoadingEvidence ? (
                  <div className="flex items-center justify-center py-8">
                    <Loader2 className="h-8 w-8 animate-spin text-navy-600" />
                  </div>
                ) : (
                  <div className="space-y-3 text-sm">
                    <div>
                      <p className="text-slate-500">Criterion Under Review</p>
                      <p className="font-semibold text-slate-800">
                        {reviewEvidenceData?.criterion.description || reviewing.criterion}
                      </p>
                    </div>
                    <div>
                      <p className="text-slate-500">Extracted Text</p>
                      <p className="rounded-lg border border-slate-200 bg-slate-50 p-3 text-slate-700">
                        {reviewEvidenceData?.decision.rationale || reviewing.extractedText}
                      </p>
                    </div>
                    {reviewEvidenceData?.evidence_chunks && reviewEvidenceData.evidence_chunks.length > 0 && (
                      <div>
                        <p className="text-slate-500">Evidence Chunks ({reviewEvidenceData.evidence_chunks.length})</p>
                        <div className="mt-2 space-y-2 max-h-48 overflow-y-auto">
                          {reviewEvidenceData.evidence_chunks.map((chunk, idx) => (
                            <div key={idx} className="rounded border border-slate-200 bg-slate-50 p-2 text-xs">
                              <p className="text-slate-700">{chunk.text}</p>
                              <p className="mt-1 text-slate-500">
                                Page {chunk.page_number} | Confidence: {Math.round(chunk.confidence * 100)}%
                              </p>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                    <div className="rounded-lg border border-amber-300 bg-amber-50 p-3 text-amber-900">
                      <p className="font-semibold">Low Confidence Warning</p>
                      <p className="mt-1">OCR Confidence: {reviewing.confidence}% - Manual verification required.</p>
                    </div>
                  </div>
                )}
              </div>
              <div className="p-6">
                <div className="mb-4 flex items-center gap-2 border-b border-slate-200 pb-3">
                  <FileCheck2 className="h-5 w-5 text-navy-700" />
                  <h4 className="font-semibold text-navy-800">Evidence Viewer</h4>
                </div>
                <div className="flex h-[300px] items-center justify-center rounded-lg border border-dashed border-slate-300 bg-slate-50 text-center text-slate-500">
                  <div>
                    <FileCheck2 className="mx-auto h-8 w-8" />
                    <p className="mt-2 text-sm">PDF / Image source preview placeholder</p>
                  </div>
                </div>
              </div>
            </div>

            <div className="p-6">
              <h4 className="mb-4 text-lg font-semibold text-navy-800">Manual Override</h4>
              <div className="grid gap-4 lg:grid-cols-2">
                <div>
                  <label className="mb-2 block text-sm font-medium text-slate-700">Override Verdict</label>
                  <select
                    value={overrideVerdict}
                    onChange={(event) => setOverrideVerdict(event.target.value as "Eligible" | "Not Eligible")}
                    className="w-full rounded border border-slate-300 px-3 py-2 outline-none ring-navy-500 focus:ring-2"
                  >
                    <option>Eligible</option>
                    <option>Not Eligible</option>
                  </select>
                </div>
                <div className="lg:col-span-2">
                  <label className="mb-2 block text-sm font-medium text-slate-700">Reviewer Justification (mandatory)</label>
                  <textarea
                    value={overrideNote}
                    onChange={(event) => setOverrideNote(event.target.value)}
                    rows={4}
                    className="w-full rounded border border-slate-300 px-3 py-2 outline-none ring-navy-500 focus:ring-2"
                    placeholder="Provide a clear and auditable reason for overriding AI verdict..."
                  />
                  {overrideError && <p className="mt-2 text-sm font-medium text-gov-danger">{overrideError}</p>}
                </div>
              </div>
              <div className="mt-5 flex items-center justify-between">
                <p className="text-sm text-slate-500">This action is audit-logged with timestamp and reviewer credentials.</p>
                <button
                  onClick={confirmOverride}
                  disabled={isSubmittingOverride}
                  className="rounded border border-[#8b0000] bg-[#8b0000] px-4 py-2 font-semibold text-white hover:bg-[#9a1111] disabled:opacity-50 disabled:cursor-not-allowed inline-flex items-center gap-2"
                >
                  {isSubmittingOverride ? (
                    <>
                      <Loader2 className="h-4 w-4 animate-spin" />
                      Submitting...
                    </>
                  ) : (
                    "Confirm Override"
                  )}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      <footer className="mt-8 border-t border-slate-300 bg-white">
        <div className="mx-auto grid max-w-7xl gap-4 px-4 py-6 text-xs text-slate-600 md:grid-cols-4">
          <div>
            <p className="font-semibold text-slate-700">About Portal</p>
            <p className="mt-2">AI-assisted public procurement workflow prototype for hackathon demonstration.</p>
          </div>
          <div>
            <p className="font-semibold text-slate-700">Important Links</p>
            <ul className="mt-2 space-y-1">
              <li>Terms and Conditions</li>
              <li>Privacy Policy</li>
              <li>Website Policy</li>
            </ul>
          </div>
          <div>
            <p className="font-semibold text-slate-700">Contact</p>
            <ul className="mt-2 space-y-1">
              <li>080-49203888 / 8904085030</li>
              <li>onehelpdesk@karnataka.gov.in</li>
              <li>Bengaluru, Karnataka</li>
            </ul>
          </div>
          <div>
            <p className="font-semibold text-slate-700">Accessibility</p>
            <ul className="mt-2 space-y-1">
              <li>Screen Reader Support</li>
              <li>Text Resize Support</li>
              <li>Bilingual Interface</li>
            </ul>
          </div>
        </div>
        <div className="border-t border-slate-200 bg-slate-50">
          <div className="mx-auto flex max-w-7xl flex-wrap items-center justify-between gap-2 px-4 py-3 text-xs text-slate-500">
            <p>Designed, Developed and Hosted by: Centre for e-Governance, Government of Karnataka</p>
            <p>Version: CeG/KRN 2.0 | All Rights Reserved</p>
          </div>
        </div>
      </footer>
      {selectedTender && (
        <div className="fixed bottom-4 right-4 rounded border border-[#0f2d56] bg-white px-4 py-2 text-sm shadow-gov">
          Selected Tender: <span className="font-semibold text-[#0f2d56]">{selectedTender}</span>
        </div>
      )}
      {toast && (
        <div className="fixed bottom-4 left-4 rounded border border-slate-300 bg-white px-4 py-2 text-sm shadow-gov">{toast}</div>
      )}
    </main>
  );
}
