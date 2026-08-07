"use client";

import { useEffect, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import { useQueryClient } from "@tanstack/react-query";
import { ArrowRight, Check, ChevronDown, RefreshCw, Sparkles, Target } from "lucide-react";

import { listResumes } from "@/lib/api/resumeApi";
import { generateRoadmap } from "@/lib/api/learningApi";
import { useJobStatus } from "@/lib/hooks/useJobStatus";
import {
  useAvailableRoles,
  useGenerateSkillGapReport,
  useGenerateSkillVector,
  useRefreshSkillGapReport,
  useSkillGapReport,
} from "@/lib/hooks/useSkill";
import { ContourProgress } from "@/components/ui/ContourProgress";
import { MissingSkillsTable, SkillGapRadarChart } from "@/components/skill";

export default function SkillPage() {
  const router = useRouter();
  const queryClient = useQueryClient();
  const [targetRole, setTargetRole] = useState("");
  const [activeJobId, setActiveJobId] = useState<string | null>(null);
  const [activeJobStep, setActiveJobStep] = useState<"vector" | "gap" | "roadmap" | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [isNavigating, setIsNavigating] = useState(false);

  // Combobox state
  const [isOpen, setIsOpen] = useState(false);
  const [searchQuery, setSearchQuery] = useState("");
  const dropdownRef = useRef<HTMLDivElement>(null);

  // Available roles query
  const { data: availableRoles = [], isLoading: isRolesLoading } = useAvailableRoles();

  // TanStack Query for existing gap report
  const { data: gapReport, isLoading: isReportLoading, refetch: refetchReport } = useSkillGapReport();

  // Mutations
  const generateVectorMutation = useGenerateSkillVector();
  const generateGapMutation = useGenerateSkillGapReport();
  const refreshGapMutation = useRefreshSkillGapReport();

  // Only poll background job status when there is an active job step explicitly initiated by user action
  const currentPollingJobId = activeJobStep !== null ? activeJobId : null;
  const { data: jobStatus } = useJobStatus(currentPollingJobId);

  // Pre-fill target role if gap report exists and ensure no stale job polling on page mount
  useEffect(() => {
    if (gapReport) {
      if (gapReport.target_role && activeJobStep === null) {
        setTargetRole(gapReport.target_role);
      }
      if (activeJobStep === null && activeJobId !== null) {
        setActiveJobId(null);
      }
    }
  }, [gapReport, activeJobStep, activeJobId]);

  // Keep searchQuery synced with targetRole
  useEffect(() => {
    if (targetRole) {
      setSearchQuery(targetRole);
    }
  }, [targetRole]);

  // Close combobox when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    };
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  // Filter available roles client-side
  const filteredRoles = availableRoles.filter((role) =>
    role.toLowerCase().includes(searchQuery.toLowerCase())
  );

  // Handle Job Completion Flow State Machine
  useEffect(() => {
    if (!jobStatus || !currentPollingJobId || activeJobStep === null) return;

    if (jobStatus.status === "complete") {
      if (activeJobStep === "vector") {
        // Step 1 Complete -> Trigger Step 2 (Gap Report)
        setActiveJobStep("gap");
        generateGapMutation
          .mutateAsync(targetRole)
          .then((res) => {
            setActiveJobId(res.job_id);
          })
          .catch((err) => {
            setErrorMessage(err.message || "Failed to enqueue skill gap report computation.");
            setActiveJobId(null);
            setActiveJobStep(null);
          });
      } else if (activeJobStep === "gap") {
        // Step 2 Complete -> Refresh query & show results
        setActiveJobId(null);
        setActiveJobStep(null);
        queryClient.invalidateQueries({ queryKey: ["skillGapReport"] });
        refetchReport();
      } else if (activeJobStep === "roadmap") {
        // Roadmap job complete -> Redirect to /learning
        setActiveJobId(null);
        setActiveJobStep(null);
        setIsNavigating(true);
        router.push("/learning");
      }
    } else if (jobStatus.status === "failed") {
      const errDetail =
        typeof jobStatus.result === "object" && jobStatus.result !== null
          ? (jobStatus.result as any).error || "Background job failed."
          : "Background job execution failed.";
      setErrorMessage(errDetail);
      setActiveJobId(null);
      setActiveJobStep(null);
    }
  }, [jobStatus, currentPollingJobId, activeJobStep, targetRole, generateGapMutation, queryClient, refetchReport, router]);

  // Handle "Generate Skill Analysis" Action
  const handleGenerateAnalysis = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMessage(null);
    setIsOpen(false);

    if (!targetRole.trim()) {
      setErrorMessage("Please select a target career role.");
      return;
    }

    try {
      // 1. Fetch user resumes and find most recent parsed resume
      const resumes = await listResumes();
      const parsedResumes = resumes.filter((r) => r.parsed_json !== null && r.parsed_json !== undefined);

      if (parsedResumes.length === 0) {
        setErrorMessage("No parsed resume found. Please upload a resume first on the Resume page.");
        return;
      }

      const latestResume = parsedResumes[0];

      // 2. Trigger skill vector generation
      setActiveJobStep("vector");
      const vectorRes = await generateVectorMutation.mutateAsync(latestResume.id);
      setActiveJobId(vectorRes.job_id);
    } catch (err: any) {
      setErrorMessage(err.message || "Failed to start skill vector generation.");
      setActiveJobStep(null);
      setActiveJobId(null);
    }
  };

  // Handle "Refresh Analysis" Action
  const handleRefreshAnalysis = async () => {
    setErrorMessage(null);
    setIsOpen(false);
    if (!targetRole.trim()) return;

    try {
      setActiveJobStep("gap");
      const refreshRes = await refreshGapMutation.mutateAsync(targetRole);
      setActiveJobId(refreshRes.job_id);
    } catch (err: any) {
      setErrorMessage(err.message || "Failed to refresh skill gap report.");
      setActiveJobStep(null);
      setActiveJobId(null);
    }
  };

  // Handle "Generate Learning Roadmap" Action
  const handleGenerateRoadmap = async () => {
    if (!gapReport?.id) return;
    setErrorMessage(null);

    try {
      setActiveJobStep("roadmap");
      const res = await generateRoadmap(gapReport.id);
      setActiveJobId(res.job_id);
    } catch (err: any) {
      setErrorMessage(err.message || "Failed to enqueue roadmap generation.");
      setActiveJobStep(null);
      setActiveJobId(null);
    }
  };

  const isJobRunning = !!currentPollingJobId && activeJobStep !== null;

  return (
    <div className="max-w-7xl mx-auto space-y-8 pb-12">
      {/* Header Section */}
      <div>
        <div className="flex items-center gap-3 mb-2">
          <span className="p-2 rounded-md bg-teal/15 text-teal border border-teal/30">
            <Target className="w-6 h-6" />
          </span>
          <h1 className="font-display text-display-lg text-ink">Skill Intelligence</h1>
        </div>
        <p className="text-body-lg text-ink-muted">
          Extract your skill vector from parsed resume data and benchmark against real market demand for your target role.
        </p>
      </div>

      {/* Target Role Form Card */}
      <div className="bg-paper-raised rounded-xl p-6 md:p-8 border border-line shadow-sm">
        <form onSubmit={handleGenerateAnalysis} className="space-y-4">
          <div className="relative" ref={dropdownRef}>
            <label htmlFor="targetRole" className="block text-body font-medium text-ink mb-2">
              Target Career Role
            </label>
            <div className="flex flex-col sm:flex-row gap-4">
              <div className="relative flex-1">
                <div className="relative flex items-center">
                  <input
                    id="targetRole"
                    type="text"
                    value={searchQuery}
                    onChange={(e) => {
                      setSearchQuery(e.target.value);
                      setTargetRole(e.target.value);
                      setIsOpen(true);
                    }}
                    onFocus={() => setIsOpen(true)}
                    placeholder={isRolesLoading ? "Loading benchmark roles..." : "Select or search a benchmark role"}
                    disabled={isJobRunning}
                    className="w-full px-4 py-3 pr-10 bg-paper border border-line rounded-md font-sans text-body text-ink placeholder:text-ink-muted focus:outline-none focus:ring-2 focus:ring-forest focus:border-transparent transition-all disabled:opacity-50"
                  />
                  <button
                    type="button"
                    onClick={() => !isJobRunning && setIsOpen(!isOpen)}
                    className="absolute right-3 text-ink-muted hover:text-ink focus:outline-none"
                    tabIndex={-1}
                  >
                    <ChevronDown className={`w-4 h-4 transition-transform ${isOpen ? "rotate-180" : ""}`} />
                  </button>
                </div>

                {/* Combobox Dropdown List */}
                {isOpen && !isJobRunning && (
                  <div className="absolute z-20 w-full mt-1 bg-paper-raised border border-line rounded-md shadow-lg max-h-60 overflow-y-auto py-1">
                    {filteredRoles.length > 0 ? (
                      filteredRoles.map((role) => {
                        const isSelected = role.toLowerCase() === targetRole.toLowerCase();
                        return (
                          <div
                            key={role}
                            onClick={() => {
                              setTargetRole(role);
                              setSearchQuery(role);
                              setIsOpen(false);
                            }}
                            className={`px-4 py-2.5 text-body cursor-pointer transition-colors font-sans flex items-center justify-between ${isSelected
                                ? "bg-forest/15 text-forest font-medium"
                                : "text-ink hover:bg-forest/10 hover:text-forest"
                              }`}
                          >
                            <span>{role}</span>
                            {isSelected && <Check className="w-4 h-4 text-forest" />}
                          </div>
                        );
                      })
                    ) : (
                      <div className="px-4 py-3 text-body-sm text-ink-muted font-sans">
                        No matching benchmark roles found.
                      </div>
                    )}
                  </div>
                )}
              </div>

              <button
                type="submit"
                disabled={isJobRunning || !targetRole.trim()}
                className="px-6 py-3 bg-forest hover:bg-forest-hover text-paper font-sans font-medium text-body rounded-md transition-colors flex items-center justify-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed shadow-sm shrink-0"
              >
                <Sparkles className="w-4 h-4 text-brass" />
                <span>{gapReport ? "Update Analysis" : "Generate Skill Analysis"}</span>
              </button>

              {gapReport && (
                <button
                  type="button"
                  onClick={handleRefreshAnalysis}
                  disabled={isJobRunning}
                  className="px-4 py-3 border border-line hover:border-teal text-ink hover:text-teal font-sans font-medium text-body rounded-md transition-colors flex items-center justify-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed shrink-0"
                >
                  <RefreshCw className={`w-4 h-4 ${isJobRunning ? "animate-spin" : ""}`} />
                  <span>Refresh</span>
                </button>
              )}
            </div>

            {/* Helper note per Step 5 & design_system.md §6 voice */}
            <p className="mt-2 text-body-sm text-ink-muted">
              Select from available benchmark roles. Role names must match exactly for accurate results.
            </p>
          </div>
        </form>

        {/* Error Notification */}
        {errorMessage && (
          <div className="mt-4 p-4 rounded-md bg-clay-alert/10 border border-clay-alert/30 text-clay-alert text-body-sm font-medium">
            {errorMessage}
          </div>
        )}

        {/* ContourProgress Bar & Honest Copy */}
        {isJobRunning && (
          <div className="mt-6 p-6 rounded-md bg-paper border border-teal/30 space-y-3 animate-fade-in">
            <div className="flex items-center justify-between">
              <div className="font-mono text-data text-teal font-medium flex items-center gap-2">
                <span className="w-2 h-2 rounded-full bg-teal animate-pulse" />
                <span>
                  {activeJobStep === "vector" && "Analysing your skills..."}
                  {activeJobStep === "gap" && `Comparing against market demand for "${targetRole}"...`}
                  {activeJobStep === "roadmap" && "Building personalized step-by-step learning roadmap..."}
                </span>
              </div>
              <span className="font-mono text-xs text-ink-muted">Processing</span>
            </div>
            <ContourProgress active={true} className="text-teal" />
          </div>
        )}
      </div>

      {/* Main Results View (Radar Chart + Missing Skills Table) */}
      {isReportLoading ? (
        <div className="p-12 text-center bg-paper-raised rounded-xl border border-line">
          <ContourProgress active={true} className="max-w-md mx-auto mb-4 text-teal" />
          <p className="font-mono text-data text-ink-muted">Loading skill gap report...</p>
        </div>
      ) : gapReport ? (
        <div className="space-y-8">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
            <SkillGapRadarChart
              missingSkills={gapReport.missing_skills || []}
              targetRole={gapReport.target_role || targetRole}
            />
            <MissingSkillsTable missingSkills={gapReport.missing_skills || []} />
          </div>

          {/* Learning Roadmap Handoff Card */}
          <div className="bg-paper-raised rounded-xl p-6 md:p-8 border border-brass/40 shadow-sm flex flex-col md:flex-row items-start md:items-center justify-between gap-6">
            <div className="space-y-1">
              <div className="flex items-center gap-2 text-brass font-mono text-data font-semibold">
                <Sparkles className="w-4 h-4" />
                <span>Next Career Action</span>
              </div>
              <h3 className="font-display text-display-md text-ink">
                Ready to bridge your skill gap?
              </h3>
              <p className="text-body-sm text-ink-muted max-w-2xl">
                Generate a sequenced learning path targeting the{" "}
                <strong className="text-ink font-semibold">
                  {(gapReport.missing_skills || []).length} missing skill gaps
                </strong>{" "}
                identified for {gapReport.target_role}.
              </p>
            </div>

            <button
              onClick={handleGenerateRoadmap}
              disabled={isJobRunning || isNavigating}
              className="px-6 py-3.5 bg-forest hover:bg-forest-hover text-paper font-sans font-medium text-body rounded-md transition-colors flex items-center gap-3 disabled:opacity-50 shadow-sm shrink-0"
            >
              <span>Generate Learning Roadmap</span>
              <ArrowRight className="w-4 h-4 text-brass" />
            </button>
          </div>
        </div>
      ) : !isJobRunning ? (
        <div className="p-12 text-center bg-paper-raised rounded-xl border border-line space-y-3">
          <Target className="w-12 h-12 text-teal mx-auto" />
          <h3 className="font-display text-display-md text-ink">No Skill Analysis Found</h3>
          <p className="text-body-sm text-ink-muted max-w-md mx-auto">
            Select your target career role above and click &quot;Generate Skill Analysis&quot; to benchmark your resume skills against market requirements.
          </p>
        </div>
      ) : null}
    </div>
  );
}


