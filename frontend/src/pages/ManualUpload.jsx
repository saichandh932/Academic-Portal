import React, { useState, useEffect, useRef } from "react";
import axios from "axios";

const ASSESSMENTS = [
  { name: "Module 1 - Pre-Test 1 (R22)", max: 10 },
  { name: "Module 2 - Pre-Test 1 (R22)", max: 10 },
  { name: "Module 1 - Test 1 (R22)", max: 20 },
  { name: "Module 2 - Test 1 (R22)", max: 20 },
  { name: "Module 1 - Test 2 Review 1 (R22)", max: 5 },
  { name: "Module 1 - Test 2 Review 2 (R22)", max: 5 },
  { name: "Module 1 - Test 3 IEEE/APA Format (R22)", max: 5 },
  { name: "Module 1 - Test 3 In-built Voice Presentation (R22)", max: 5 },
  { name: "Module 2 - Test 3 In-built Voice Presentation (R22)", max: 5 },
  { name: "Module 2 - Test 3 IEEE/APA Format (R22)", max: 5 },
  { name: "Module 1 - Test 4 (R22)", max: 20 },
  { name: "Module 2 - Test 4 (R22)", max: 20 },
  { name: "Module 1 - Test 5 Assignment (CLA)", max: 20 },
  { name: "Final Assessment (FA)", max: 100 }
];

// Topic multi-select dropdown component
function TopicDropdown({ topics, selectedTopics, onChange, disabled }) {
  const [open, setOpen] = useState(false);
  const ref = useRef(null);

  useEffect(() => {
    const handleClickOutside = (e) => {
      if (ref.current && !ref.current.contains(e.target)) setOpen(false);
    };
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  const toggle = (topic) => {
    if (disabled) return;
    if (selectedTopics.includes(topic)) {
      onChange(selectedTopics.filter((t) => t !== topic));
    } else {
      onChange([...selectedTopics, topic]);
    }
  };

  const toggleAll = () => {
    if (disabled) return;
    if (selectedTopics.length === topics.length) {
      onChange([]);
    } else {
      onChange([...topics]);
    }
  };

  const label =
    selectedTopics.length === 0
      ? "Select topics covered in this assessment..."
      : selectedTopics.length === topics.length
      ? "All Topics"
      : `${selectedTopics.length} topic${selectedTopics.length > 1 ? "s" : ""} selected`;

  return (
    <div ref={ref} style={{ position: "relative" }}>
      <button
        type="button"
        onClick={() => !disabled && setOpen((o) => !o)}
        style={{
          width: "100%",
          padding: "0.6rem 1rem",
          borderRadius: "0.5rem",
          border: "1px solid var(--border-color)",
          background: disabled ? "rgba(0,0,0,0.03)" : "white",
          textAlign: "left",
          cursor: disabled ? "not-allowed" : "pointer",
          fontSize: "0.9rem",
          color: selectedTopics.length === 0 ? "var(--text-muted)" : "inherit",
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          fontFamily: "inherit",
        }}
      >
        <span>{label}</span>
        <span style={{ fontSize: "0.7rem", opacity: 0.6 }}>
          {open ? "▲" : "▼"}
        </span>
      </button>

      {open && !disabled && (
        <div
          style={{
            position: "absolute",
            zIndex: 1000,
            top: "calc(100% + 4px)",
            left: 0,
            right: 0,
            background: "white",
            border: "1px solid var(--border-color)",
            borderRadius: "0.75rem",
            boxShadow: "0 8px 30px rgba(0,0,0,0.12)",
            maxHeight: "260px",
            overflowY: "auto",
            padding: "0.5rem",
          }}
        >
          {/* Select All */}
          <label
            style={{
              display: "flex",
              alignItems: "center",
              gap: "0.6rem",
              padding: "0.5rem 0.75rem",
              borderRadius: "0.5rem",
              cursor: "pointer",
              fontWeight: "700",
              fontSize: "0.82rem",
              background: "rgba(0, 96, 156, 0.06)",
              marginBottom: "0.4rem",
              color: "var(--vignan-blue)",
            }}
          >
            <input
              type="checkbox"
              checked={selectedTopics.length === topics.length}
              onChange={toggleAll}
              style={{ accentColor: "var(--vignan-blue)" }}
            />
            Select All Topics
          </label>

          {topics.map((topic) => (
            <label
              key={topic}
              style={{
                display: "flex",
                alignItems: "center",
                gap: "0.6rem",
                padding: "0.45rem 0.75rem",
                borderRadius: "0.4rem",
                cursor: "pointer",
                fontSize: "0.82rem",
                transition: "background 0.15s",
                background: selectedTopics.includes(topic)
                  ? "rgba(0,96,156,0.07)"
                  : "transparent",
              }}
              onMouseEnter={(e) =>
                (e.currentTarget.style.background = "rgba(0,0,0,0.04)")
              }
              onMouseLeave={(e) =>
                (e.currentTarget.style.background = selectedTopics.includes(
                  topic
                )
                  ? "rgba(0,96,156,0.07)"
                  : "transparent")
              }
            >
              <input
                type="checkbox"
                checked={selectedTopics.includes(topic)}
                onChange={() => toggle(topic)}
                style={{ accentColor: "var(--vignan-blue)", flexShrink: 0 }}
              />
              {topic}
            </label>
          ))}
        </div>
      )}
    </div>
  );
}

export default function ManualUpload({ subject, onUploadSuccess }) {
  const [students, setStudents] = useState([]);
  const [showGrid, setShowGrid] = useState(false);
  const [selectedAssessmentIdx, setSelectedAssessmentIdx] = useState(0);
  const [grades, setGrades] = useState({});
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const [isLocked, setIsLocked] = useState(false);

  // Topic selection state
  const [syllabusTopics, setSyllabusTopics] = useState([]);
  const [selectedTopics, setSelectedTopics] = useState([]);
  const [syllabusLoading, setSyllabusLoading] = useState(false);

  useEffect(() => {
    fetchStudents();
    fetchSyllabus();
  }, [subject]);

  const fetchStudents = async () => {
    try {
      const res = await axios.get("/api/db/students");
      setStudents(res.data.students || []);
    } catch (err) {
      console.error("Student Fetch Error:", err);
      setError("Failed to fetch students. Ensure backend is running at http://127.0.0.1:5000");
    }
  };

  const fetchSyllabus = async () => {
    try {
      setSyllabusLoading(true);
      const subjectCode = subject.split(" ")[0].toUpperCase();
      const res = await axios.get(`/api/syllabus/${subjectCode}`);
      if (res.data.success) {
        setSyllabusTopics(res.data.data.topics || []);
      } else {
        setSyllabusTopics([]);
      }
    } catch {
      setSyllabusTopics([]); // No syllabus for this subject, hide the dropdown
    } finally {
      setSyllabusLoading(false);
    }
  };

  const handleLoadGrid = async () => {
    if (students.length === 0) {
      setError("No students found in database. Please run /setup_db first!");
      return;
    }

    try {
      setLoading(true);
      setError("");
      setMessage("");

      const res = await axios.get(`/api/db/marks?_t=${Date.now()}`);
      const allMarks = res.data.marks || [];
      const allLocks = res.data.locks || [];

      const locked = allLocks.some(
        (l) =>
          l.subject_name === subject &&
          l.assessment_name === selectedAssessment.name
      );
      setIsLocked(locked);

      const existingMarks = allMarks.filter(
        (m) =>
          m.subject_name === subject &&
          m.assessment_name === selectedAssessment.name
      );

      const prefilledGrades = {};
      let prefilledTopics = [];
      existingMarks.forEach((m) => {
        prefilledGrades[m.registration_number] = m.marks_obtained;
        if (m.topics && m.topics.length > 0) prefilledTopics = m.topics;
      });

      setGrades(prefilledGrades);
      if (prefilledTopics.length > 0) setSelectedTopics(prefilledTopics);

      if (locked) {
        setMessage("VIEW ONLY: This assessment is permanently locked. You can view the records but changes cannot be saved.");
      } else if (existingMarks.length > 0) {
        setMessage(`RESTORING DATA: Found ${existingMarks.length} existing records for this assessment.`);
      }

      setShowGrid(true);
    } catch (err) {
      console.error("Data fetch failed:", err);
      setError("Failed to load existing assessment data. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  const selectedAssessment = ASSESSMENTS[selectedAssessmentIdx] || ASSESSMENTS[0];

  const handleGradeChange = (registration_number, value) => {
    if (isLocked) return;
    setGrades((prev) => ({ ...prev, [registration_number]: value }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (isLocked) return;

    setLoading(true);
    setMessage("");
    setError("");

    const payloadGrades = students
      .map((s) => ({
        registration_number: s.registration_number,
        marks_obtained: grades[s.registration_number],
      }))
      .filter((g) => g.marks_obtained !== undefined && g.marks_obtained !== "");

    if (payloadGrades.length === 0) {
      setError("Please enter at least one grade before saving.");
      setLoading(false);
      return;
    }

    const invalidGrades = payloadGrades.filter(
      (g) => Number(g.marks_obtained) > selectedAssessment.max
    );
    if (invalidGrades.length > 0) {
      const ids = invalidGrades.map((g) => g.registration_number).join(", ");
      setError(`Validation Error: Student(s) [${ids}] have marks exceeding the maximum (${selectedAssessment.max}).`);
      setLoading(false);
      return;
    }

    try {
      const payload = {
        subject_name: subject,
        assessment_name: selectedAssessment.name,
        max_marks: selectedAssessment.max,
        topics: selectedTopics,
        grades: payloadGrades.map((g) => ({
          ...g,
          marks_obtained: Number(g.marks_obtained),
        })),
      };

      const res = await axios.post("/api/db/marks/upload", payload);
      setMessage(res.data.message);
      setIsLocked(true);
      if (onUploadSuccess) onUploadSuccess();
    } catch (err) {
      setError(err.response?.data?.error || "Connection error to Gradebook API.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="glass-panel" style={{ padding: "2rem", marginTop: "2rem", border: isLocked ? "2px solid var(--border-color)" : "none" }}>
      <div style={{ marginBottom: "1.5rem", display: "flex", justifyContent: "space-between", alignItems: "flex-start", flexWrap: "wrap", gap: "1rem" }}>
        <div>
          <h2 className="font-bold text-xl">Marks Entry: {subject}</h2>
          <p style={{ color: "var(--text-muted)" }}>Enter grades or view existing records for this subject.</p>
        </div>
        {isLocked && (
          <span className="badge" style={{ background: "rgba(0,0,0,0.05)", display: "flex", alignItems: "center", gap: "0.4rem" }}>
            LOCKED - READ ONLY
          </span>
        )}
      </div>

      {error && (
        <div style={{ color: "var(--danger)", padding: "1rem", background: "rgba(227, 30, 36, 0.05)", borderRadius: "0.5rem", marginBottom: "1rem", border: "1px solid rgba(227, 30, 36, 0.1)" }}>{error}</div>
      )}
      {message && (
        <div style={{ color: isLocked ? "var(--text-muted)" : "var(--vignan-blue)", padding: "1rem", background: isLocked ? "rgba(0,0,0,0.03)" : "rgba(0, 96, 156, 0.05)", borderRadius: "0.5rem", marginBottom: "1rem", fontSize: "0.9rem", fontWeight: "600", border: isLocked ? "none" : "1px solid rgba(0, 96, 156, 0.1)" }}>{message}</div>
      )}

      <div className="grid gap-6" style={{ gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))", background: "rgba(0,0,0,0.03)", padding: "clamp(1rem, 3vw, 1.5rem)", borderRadius: "1rem", alignItems: "flex-end" }}>
        <div className="form-group" style={{ marginBottom: 0 }}>
          <label className="form-label">Subject</label>
          <input className="form-input" value={subject} readOnly disabled style={{ opacity: 0.7 }} />
        </div>

        <div className="form-group" style={{ marginBottom: 0 }}>
          <label className="form-label">Assessment Type</label>
          <select
            className="form-input"
            value={selectedAssessmentIdx}
            onChange={(e) => {
              setSelectedAssessmentIdx(Number(e.target.value));
              setShowGrid(false);
              setIsLocked(false);
              setMessage("");
              setSelectedTopics([]);
            }}
          >
            {ASSESSMENTS.map((assm, idx) => (
              <option key={idx} value={idx}>
                {assm.name} (Max: {assm.max})
              </option>
            ))}
          </select>
        </div>

        <button className="btn btn-outline" onClick={handleLoadGrid} disabled={loading} style={{ height: "42px", width: "100%" }}>
          {loading ? "Checking..." : "Load Assessment Grid"}
        </button>
      </div>

      {/* Topic Selector - only shown if syllabus topics are available */}
      {syllabusTopics.length > 0 && (
        <div style={{ marginTop: "1.5rem", padding: "1.25rem", background: "rgba(0, 96, 156, 0.04)", border: "1px solid rgba(0, 96, 156, 0.12)", borderRadius: "0.75rem" }}>
          <div style={{ display: "flex", alignItems: "center", gap: "0.5rem", marginBottom: "0.75rem" }}>
            <span style={{ fontSize: "1rem" }}>📚</span>
            <label style={{ fontWeight: "700", fontSize: "0.85rem", color: "var(--vignan-blue)" }}>
              Topics Covered in This Assessment
            </label>
            <span style={{ marginLeft: "auto", fontSize: "0.75rem", color: "var(--text-muted)" }}>
              {selectedTopics.length === 0 ? "None selected (applies globally)" : `${selectedTopics.length} of ${syllabusTopics.length}`}
            </span>
          </div>
          <TopicDropdown
            topics={syllabusTopics}
            selectedTopics={selectedTopics}
            onChange={setSelectedTopics}
            disabled={isLocked}
          />
          <p style={{ fontSize: "0.75rem", color: "var(--text-muted)", marginTop: "0.5rem", margin: "0.5rem 0 0 0" }}>
            Selecting topics helps the ML model predict student mastery per topic.
          </p>
        </div>
      )}

      {showGrid && (
        <form onSubmit={handleSubmit} className="animate-fade-in" style={{ marginTop: "2rem" }}>
          <div className="grid" style={{ gridTemplateColumns: "repeat(auto-fill, minmax(300px, 1fr))", gap: "1rem" }}>
            {students.map((student) => (
              <div
                key={student.registration_number}
                className="flex justify-between items-center"
                style={{ padding: "1rem", background: isLocked ? "rgba(0,33,71,0.02)" : "var(--surface-solid)", borderRadius: "0.8rem", border: "1px solid var(--border-color)", opacity: isLocked ? 0.8 : 1 }}
              >
                <span style={{ fontFamily: "monospace", fontWeight: "600", color: isLocked ? "var(--text-muted)" : "inherit" }}>
                  {student.registration_number}
                </span>
                <input
                  type="number"
                  min="0"
                  max={selectedAssessment.max}
                  step="0.1"
                  placeholder="--"
                  readOnly={isLocked}
                  className="form-input"
                  style={{ width: "80px", textAlign: "right", padding: "0.4rem", background: isLocked ? "transparent" : "white", border: isLocked ? "none" : "1px solid var(--border-color)" }}
                  value={grades[student.registration_number] || ""}
                  onChange={(e) => handleGradeChange(student.registration_number, e.target.value)}
                />
              </div>
            ))}
          </div>

          <div className="flex justify-between items-center mt-4 gap-4" style={{ borderTop: "1px solid var(--border-color)", paddingTop: "1.5rem", flexWrap: "wrap" }}>
            <p style={{ color: "var(--text-muted)", fontSize: "0.9rem", margin: 0 }}>
              {isLocked
                ? "This record is finalized and cannot be edited."
                : `Recording grades for ${students.length} students in ${subject}.`}
            </p>
            {!isLocked && (
              <button type="submit" className="btn btn-primary" disabled={loading} style={{ width: "auto", minWidth: "200px" }}>
                {loading ? "Saving..." : "Save All to Gradebook"}
              </button>
            )}
          </div>
        </form>
      )}
    </div>
  );
}
