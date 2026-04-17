import { useEffect, useState } from 'react';
import axios from 'axios';
import { useSearchParams, useNavigate } from 'react-router-dom';
import { Users, RefreshCcw, LayoutDashboard, ClipboardCheck, LogOut, Activity, AlertTriangle, Search, ChevronDown, ChevronRight, Lock, Mail, ShieldCheck, ClipboardList, Menu, X } from 'lucide-react';
import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip } from 'recharts';
import ManualUpload from './ManualUpload';
import AttendanceUpload from './AttendanceUpload';
import Loader from '../components/Loader';

export default function AdminDashboard() {
  const [searchParams] = useSearchParams();
  const subject = searchParams.get('subject') || "Assigned Subject";
  const navigate = useNavigate();

  const [data, setData] = useState({ total_students: 70, total_marks: 0, lowPerformers: 0 });
  const [history, setHistory] = useState([]);
  const [locks, setLocks] = useState([]);
  const [isHistoryVisible, setIsHistoryVisible] = useState(false);
  const [expandedAssessment, setExpandedAssessment] = useState(null);
  const [assessmentFilter, setAssessmentFilter] = useState('');
  const [selectedAssessmentGroup, setSelectedAssessmentGroup] = useState('All');
  const [loading, setLoading] = useState(true);
  const [isAlertDetailsOpen, setIsAlertDetailsOpen] = useState(false);
  const [error, setError] = useState('');
  const [activeTab, setActiveTab] = useState('marks'); // 'marks' | 'add-marks' | 'attendance' | 'settings'
  const [isSidebarOpen, setIsSidebarOpen] = useState(false);

  const [compactMode] = useState(() => localStorage.getItem('vignan_compact_mode') === 'true');

  useEffect(() => {
    if (compactMode) document.body.classList.add('compact-table');
    else document.body.classList.remove('compact-table');
    localStorage.setItem('vignan_compact_mode', compactMode);
  }, [compactMode]);


  const [attnSummary, setAttnSummary] = useState([]);

  const fetchDashboard = async () => {
    try {
      setLoading(true);
      setError('');
      const delay = new Promise(resolve => setTimeout(resolve, 2000));
      const [, marksRes, attnRes] = await Promise.all([
        axios.get("/api/db/students"),
        axios.get(`/api/db/marks?_t=${Date.now()}`),
        axios.get(`/api/db/attendance/summary/subject/${subject}`),
        delay
      ]);

      const marks = (marksRes.data.marks || []).filter(m => m.subject_name === subject);
      const critical = marks.filter(m => m.performance_status === "Low").length;
      const totalStudents = 70;

      // Logic to find the "Particular Assessment" (Latest entry)
      const uniqueAssessments = [...new Set(marks.map(m => m.assessment_name))];
      const latestAssessmentName = uniqueAssessments.length > 0 ? uniqueAssessments[uniqueAssessments.length - 1] : "No Assessments";
      const latestCount = marks.filter(m => m.assessment_name === latestAssessmentName).length;

      setAttnSummary(attnRes.data.summary || []);
      setData({
        total_students: totalStudents,
        total_marks: marks.length,
        lowPerformers: critical,
        latest_assessment: latestAssessmentName,
        latest_count: latestCount
      });
      setHistory(marks);
      setLocks(marksRes.data.locks || []);
      fetchAttendance();
    } catch (err) {
      console.error("Dashboard Fetch Error:", err);
      setError('Could not connect to the Backend API. Please ensure "python run.py" is running.');
    } finally {
      setLoading(false);
    }
  };

  const fetchAttendance = async () => {
/*
    try {
      const res = await axios.get(`/api/db/attendance?subject=${subject}`);
      // setAttnHistory(res.data.records || []);
    } catch (err) {
      console.error("Attendance Fetch Error:", err);
    }
*/
  };

  useEffect(() => {
    fetchDashboard();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [subject]);

  const groupedHistory = history.reduce((acc, current) => {
    const key = current.assessment_name;
    if (!acc[key]) acc[key] = [];
    acc[key].push(current);
    return acc;
  }, {});

  // Chart Data Preparation (Placeholder)




  const COLORS = ['var(--success)', 'var(--danger)'];
  const allAssessmentNames = Object.keys(groupedHistory).sort();

  const assessmentKeys = allAssessmentNames
    .filter(k => {
      const matchesSearch = k.toLowerCase().includes(assessmentFilter.toLowerCase());
      const matchesDropdown = selectedAssessmentGroup === 'All' || k === selectedAssessmentGroup;
      return matchesSearch && matchesDropdown;
    })
    .sort();

  if (loading && history.length === 0) {
    return <Loader text="Loading Gradebook Records..." />;
  }

  return (
    <div style={{ display: 'flex', minHeight: '100vh', background: 'var(--bg-color)' }}>
      {/* Sidebar Overlay (Mobile) */}
      <div 
        className={`sidebar-overlay ${isSidebarOpen ? 'open' : ''}`} 
        onClick={() => setIsSidebarOpen(false)}
      />

      {/* Sidebar Navigation */}
      <aside className={`sidebar ${isSidebarOpen ? 'open' : ''}`}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '3rem' }}>
          <div>
            <h2 style={{ fontSize: '1.2rem', fontWeight: '800', letterSpacing: '1px', color: 'white', margin: 0 }}>VIGNAN ACADEMIC PORTAL</h2>
            <p style={{ fontSize: '0.75rem', opacity: 0.5, textTransform: 'uppercase', marginTop: '0.4rem' }}>Management Console</p>
          </div>
          <button 
            className="show-on-mobile" 
            style={{ background: 'none', border: 'none', color: 'white' }}
            onClick={() => setIsSidebarOpen(false)}
          >
            <X size={24} />
          </button>
        </div>

        <nav style={{ flex: 1, display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
          <button
            className={`btn ${activeTab === 'marks' ? 'btn-primary' : 'btn-outline'}`}
            style={{
              justifyContent: 'flex-start',
              border: activeTab === 'marks' ? 'none' : '1px solid rgba(255,255,255,0.1)',
              color: 'white',
              background: activeTab === 'marks' ? 'var(--primary)' : 'rgba(255,255,255,0.02)',
              padding: '0.8rem 1.2rem'
            }}
            onClick={() => { setActiveTab('marks'); setIsSidebarOpen(false); }}
          >
            <LayoutDashboard size={18} style={{ marginRight: '0.8rem' }} /> Section Overview
          </button>

          <button
            className={`btn ${activeTab === 'add-marks' ? 'btn-primary' : 'btn-outline'}`}
            style={{
              justifyContent: 'flex-start',
              border: activeTab === 'add-marks' ? 'none' : '1px solid rgba(255,255,255,0.1)',
              color: 'white',
              background: activeTab === 'add-marks' ? 'var(--primary)' : 'rgba(255,255,255,0.02)',
              padding: '0.8rem 1.2rem'
            }}
            onClick={() => { setActiveTab('add-marks'); setIsSidebarOpen(false); }}
          >
            <RefreshCcw size={18} style={{ marginRight: '0.8rem' }} /> Post New Marks
          </button>

          <button
            className={`btn ${activeTab === 'attendance' ? 'btn-primary' : 'btn-outline'}`}
            style={{
              justifyContent: 'flex-start',
              border: activeTab === 'attendance' ? 'none' : '1px solid rgba(255,255,255,0.1)',
              color: 'white',
              background: activeTab === 'attendance' ? 'var(--primary)' : 'rgba(255,255,255,0.02)',
              padding: '0.8rem 1.2rem'
            }}
            onClick={() => { setActiveTab('attendance'); setIsSidebarOpen(false); }}
          >
            <ClipboardCheck size={18} style={{ marginRight: '0.8rem' }} /> Attendance Registry
          </button>

        </nav>

        <div style={{ marginTop: 'auto' }}>
          <button
            className="btn btn-outline"
            style={{ width: '100%', borderColor: 'rgba(239, 68, 68, 0.2)', color: 'var(--danger)' }}
            onClick={() => {
              sessionStorage.clear();
              navigate("/", { replace: true });
            }}
          >
            <LogOut size={16} style={{ marginRight: '0.6rem' }} /> Exit Portal
          </button>
        </div>
      </aside>

      {/* Main Content Area */}
      <main className="main-content">
        <div className="flex justify-between items-center" style={{ marginBottom: '2rem', flexWrap: 'wrap', gap: '1rem' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
            <button 
              className="show-on-mobile btn btn-outline" 
              style={{ padding: '0.5rem', borderColor: 'var(--border-color)' }}
              onClick={() => setIsSidebarOpen(true)}
            >
              <Menu size={20} />
            </button>
            <div>
              <h1 className="font-bold text-xl" style={{ fontSize: 'clamp(1.5rem, 5vw, 2.5rem)', marginBottom: '0.2rem' }}>{subject}</h1>
              <p style={{ color: 'var(--text-muted)', fontSize: 'clamp(0.9rem, 2vw, 1.2rem)' }}>
                {activeTab === 'marks' ? 'CLASS PERFORMANCE OVERVIEW' :
                  activeTab === 'add-marks' ? 'ENTER STUDENT SCORES' : 'MANAGE DAILY ATTENDANCE'}
              </p>
            </div>
          </div>
          <button className="btn btn-primary" onClick={fetchDashboard} style={{ width: 'auto' }}>
            <RefreshCcw size={16} /> <span className="hide-on-mobile">Sync Subject Data</span>
          </button>
        </div>

        {activeTab === 'marks' ? (
          <div className="animate-fade-in">
            {error && (
              <div className="glass-panel" style={{ padding: '1.5rem', borderLeft: '4px solid var(--danger)', marginBottom: '2rem', background: 'var(--surface-solid)' }}>
                <h3 style={{ color: 'var(--danger)', margin: 0 }}>Connection Error</h3>
                <p style={{ margin: '0.5rem 0 0', color: 'var(--text-main)' }}>{error}</p>
              </div>
            )}

            {/* Simplified Header Stats */}
            <div className="stat-grid" style={{ marginBottom: '2.5rem' }}>
              <div className="glass-panel card">
                <h3 className="card-title text-muted"><Users size={18} color="var(--primary)" /> Total Registered Students</h3>
                <div className="card-value">{data.total_students}</div>
              </div>
              <div className="glass-panel card">
                <h3 className="card-title text-muted">
                    <ClipboardCheck size={18} color="var(--success)" /> 
                    {data.latest_assessment} Entries
                </h3>
                <div className="card-value" style={{ color: 'var(--success)' }}>
                    {data.latest_count} / {data.total_students}
                </div>
              </div>
              {/* NEW: LIVE ATTENDANCE STAT */}
              <div className="glass-panel card">
                <h3 className="card-title text-muted"><Activity size={18} color="var(--primary)" /> Avg Subject Attendance</h3>
                <div className="card-value" style={{ color: 'var(--primary)' }}>
                  {attnSummary.length > 0
                    ? (attnSummary.reduce((acc, s) => acc + s.percentage, 0) / attnSummary.length).toFixed(1)
                    : "0"}%
                </div>
              </div>
            </div>

            {/* Performance & Attendance Round Charts */}
            <div className="grid" style={{ gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: '1.5rem', marginBottom: '3rem' }}>
              {/* Performance Circle */}
              <div className="glass-panel card" style={{ height: '400px', padding: '2rem', textAlign: 'center' }}>
                <h3 style={{ fontSize: '1.1rem', fontWeight: '800', marginBottom: '1.5rem', color: 'var(--text-main)' }}>Student Performance</h3>
                <div style={{ flex: 1, height: '240px', position: 'relative' }}>
                  <ResponsiveContainer width="100%" height="100%">
                    <PieChart>
                      <Pie
                        data={[
                          { name: 'Doing Well', value: history.filter(m => m.performance_status !== "Low").length },
                          { name: 'Needs Help', value: history.filter(m => m.performance_status === "Low").length }
                        ]}
                        cx="50%" cy="50%" innerRadius={85} outerRadius={110} paddingAngle={8} dataKey="value" stroke="none"
                      >
                        <Cell fill="#10b981" />
                        <Cell fill="#ef4444" />
                      </Pie>
                      <Tooltip />
                    </PieChart>
                  </ResponsiveContainer>
                  <div style={{ position: 'absolute', top: '50%', left: '50%', transform: 'translate(-50%, -50%)' }}>
                    <div style={{ fontSize: '2.5rem', fontWeight: '900', color: 'var(--primary)' }}>
                      {Math.round((history.filter(m => m.performance_status !== "Low").length / (history.length || 1)) * 100)}%
                    </div>
                    <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)', fontWeight: '600' }}>SUCCESS</div>
                  </div>
                </div>
                <div className="flex justify-center gap-6 mt-4">
                  <div className="flex items-center gap-2"><div style={{ width: 12, height: 12, borderRadius: '50%', background: '#10b981' }}></div> <span style={{ fontSize: '0.85rem', fontWeight: '700' }}>Doing Well</span></div>
                  <div className="flex items-center gap-2"><div style={{ width: 12, height: 12, borderRadius: '50%', background: '#ef4444' }}></div> <span style={{ fontSize: '0.85rem', fontWeight: '700' }}>Needs Help</span></div>
                </div>
              </div>

              {/* Attendance Circle */}
              <div className="glass-panel card" style={{ height: '400px', padding: '2rem', textAlign: 'center' }}>
                <h3 style={{ fontSize: '1.1rem', fontWeight: '800', marginBottom: '1.5rem', color: 'var(--text-main)' }}>Class Attendance Score</h3>
                <div style={{ flex: 1, height: '240px', position: 'relative' }}>
                  <ResponsiveContainer width="100%" height="100%">
                    <PieChart>
                      <Pie
                        data={[
                          { name: 'Present', value: attnSummary.reduce((acc, s) => acc + s.present_count, 0) },
                          { name: 'Absent', value: attnSummary.reduce((acc, s) => acc + (s.total_classes - s.present_count), 0) }
                        ]}
                        cx="50%" cy="50%" innerRadius={85} outerRadius={110} startAngle={90} endAngle={450} dataKey="value" stroke="none"
                      >
                        <Cell fill="var(--primary)" />
                        <Cell fill="rgba(0,0,0,0.05)" />
                      </Pie>
                    </PieChart>
                  </ResponsiveContainer>
                  <div style={{ position: 'absolute', top: '50%', left: '50%', transform: 'translate(-50%, -50%)' }}>
                    <div style={{ fontSize: '2.5rem', fontWeight: '900' }}>
                      {attnSummary.length > 0
                        ? (attnSummary.reduce((acc, s) => acc + s.percentage, 0) / attnSummary.length).toFixed(1)
                        : "0"}%
                    </div>
                    <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)', fontWeight: '600' }}>CLASS AVERAGE</div>
                  </div>
                </div>
              </div>
            </div>

            <div className="flex justify-center" style={{ marginBottom: '3rem' }}>
              <button
                className="btn btn-primary"
                style={{ width: '100%', maxWidth: '500px', fontWeight: '900', height: '60px', borderRadius: '15px', fontSize: '1.1rem', letterSpacing: '1px' }}
                onClick={() => setIsHistoryVisible(!isHistoryVisible)}
              >
                {isHistoryVisible ? "CLOSE RECORDS" : "📂 VIEW STUDENT SCORES"}
              </button>
            </div>

            {/* The Marks Sheet Section */}
            {isHistoryVisible && (
              <div className="animate-fade-in">
                <>
                  {/* Threshold Tracker Moved to Marks Sheet */}
                  <div className="glass-panel card" style={{ position: 'relative', overflow: 'hidden', padding: '1.5rem', borderLeft: '4px solid var(--danger)', marginBottom: '1.5rem', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <div>
                      <h3 className="card-title text-muted" style={{ margin: 0, fontSize: '1rem', textTransform: 'uppercase' }}><AlertTriangle size={18} color="var(--danger)" /> Students Needing Help</h3>
                      <div className="card-value" style={{ color: 'var(--danger)', fontSize: '2.5rem', marginTop: '0.4rem' }}>{data.lowPerformers}</div>
                    </div>
                    <button
                      className="btn btn-outline"
                      style={{ borderColor: 'var(--danger)', color: 'var(--danger)', fontSize: '0.75rem' }}
                      onClick={() => setIsAlertDetailsOpen(!isAlertDetailsOpen)}
                    >
                      {isAlertDetailsOpen ? "Hide Breakdown" : "View Details"}
                    </button>
                  </div>

                  {isAlertDetailsOpen && (
                    <div className="glass-panel animate-fade-in" style={{ padding: '1.2rem', marginBottom: '1.5rem', border: '1px solid rgba(239, 68, 68, 0.1)', background: 'rgba(239, 68, 68, 0.02)' }}>
                      <p style={{ fontSize: '0.7rem', fontWeight: '800', color: 'var(--danger)', marginBottom: '0.8rem', textTransform: 'uppercase' }}>Attention Needed for:</p>
                      <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.6rem' }}>
                        {history.filter(m => m.performance_status === "Low").map((m, i) => (
                          <span key={i} style={{ fontSize: '0.75rem', background: 'white', border: '1px solid rgba(239, 68, 68, 0.2)', padding: '0.2rem 0.6rem', borderRadius: '4px', fontWeight: '700' }}>
                            {m.registration_number} • {m.assessment_name}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}

                  <div className="glass-panel animate-fade-in" style={{ background: 'var(--surface-solid)', overflow: 'hidden' }}>
                    <div style={{ padding: '1.5rem', borderBottom: '1px solid var(--border-color)', display: 'flex', alignItems: 'center', gap: '0.5rem', justifyContent: 'space-between' }}>
                      <div className="flex items-center gap-2">
                        <ClipboardList color="var(--primary)" />
                        <h2 className="font-bold" style={{ margin: 0 }}>Recent Gradebook Activity</h2>
                      </div>

                      <div className="flex gap-3">
                        <select
                          className="form-input"
                          style={{ width: '180px', fontSize: '0.85rem', height: '35px', padding: '0 0.8rem' }}
                          value={selectedAssessmentGroup}
                          onChange={(e) => setSelectedAssessmentGroup(e.target.value)}
                        >
                          <option value="All">All Assessments</option>
                          {allAssessmentNames.map((name, i) => (
                            <option key={i} value={name}>{name}</option>
                          ))}
                        </select>

                        <div style={{ position: 'relative' }}>
                          <Search size={14} style={{ position: 'absolute', left: '12px', top: '50%', transform: 'translateY(-50%)', color: 'var(--text-muted)' }} />
                          <input
                            type="text"
                            placeholder="Search titles..."
                            className="form-input"
                            style={{ paddingLeft: '2.5rem', width: '160px', fontSize: '0.85rem', height: '35px' }}
                            value={assessmentFilter}
                            onChange={(e) => setAssessmentFilter(e.target.value)}
                          />
                        </div>
                      </div>
                    </div>

                    <div style={{ padding: '0 1.5rem 1.5rem', marginTop: '1.5rem' }}>
                      {assessmentKeys.length === 0 ? (
                        <div style={{ padding: '3rem', textAlign: 'center', color: 'var(--text-muted)' }}>
                          {assessmentFilter ? "No assessments match your search." : "No assessment data has been entered yet."}
                        </div>
                      ) : (
                        assessmentKeys.map((assKey) => (
                          <AssessmentSection
                            key={assKey}
                            assKey={assKey}
                            students={groupedHistory[assKey]}
                            isExpanded={expandedAssessment === assKey}
                            onToggle={() => setExpandedAssessment(expandedAssessment === assKey ? null : assKey)}
                            isLocked={locks.some(l => l.subject_name === subject && l.assessment_name === assKey)}
                            onLock={fetchDashboard}
                          />
                        ))
                      )}
                    </div>
                  </div>
                </>
              </div>
            )}
          </div>
        ) : activeTab === 'add-marks' ? (
          <div className="animate-fade-in">
            <ManualUpload subject={subject} onUploadSuccess={() => { fetchDashboard(); setActiveTab('marks'); }} />
          </div>
        ) : (
          <div className="animate-fade-in">
            <AttendanceUpload subject={subject} onUploadSuccess={() => { fetchAttendance(); setActiveTab('marks'); }} />
          </div>
        )}
      </main>
    </div>
  );
}

// ── Sub-Component for Individual Assessment Cards ────────────────────────────
function AssessmentSection({ assKey, students, isExpanded, onToggle, isLocked, onLock }) {
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState('All');
  const [notifying, setNotifying] = useState({}); // {reg_num: true/false}

  const filteredStudents = students.filter(item => {
    const reg = (item.registration_number || "").toLowerCase();
    const sea = searchTerm.toLowerCase();
    const matchesSearch = reg.includes(sea);
    const matchesStatus = statusFilter === 'All' || item.performance_status === statusFilter;
    return matchesSearch && matchesStatus;
  });

  const handleNotify = async (row) => {
    const regNum = row.registration_number;
    try {
      setNotifying(prev => ({ ...prev, [regNum]: true }));
      await axios.post("/api/db/marks/notify-student", {
        registration_number: regNum,
        subject_name: students[0]?.subject_name || "Subject",
        assessment_name: assKey,
        marks_obtained: row.marks_obtained,
        max_marks: row.max_marks
      });
      alert(`Instructional email sent to Student ${regNum}`);
    } catch (err) {
      console.error("Alert send error:", err);
      alert(`Failed to send email: ${err.response?.data?.error || err.message}`);
    } finally {
      setNotifying(prev => ({ ...prev, [regNum]: false }));
    }
  };

  const handleNotifyAll = async (e) => {
    e.stopPropagation();
    const criticalStudents = students.filter(i => i.performance_status === 'Low');
    if (criticalStudents.length === 0) return;

    if (!window.confirm(`Are you sure you want to notify all ${criticalStudents.length} students currently below the threshold?`)) return;

    try {
      setNotifying({ ALL: true });
      const res = await axios.post("/api/db/marks/notify-all", {
        subject_name: students[0]?.subject_name || "Subject",
        assessment_name: assKey,
        students: criticalStudents.map(s => ({
          registration_number: s.registration_number,
          marks_obtained: s.marks_obtained,
          max_marks: s.max_marks
        }))
      });
      alert(res.data.message);
    } catch (err) {
      console.error("Bulk alert error:", err);
      alert(`Failed to send bulk emails: ${err.response?.data?.error || err.message}`);
    } finally {
      setNotifying({});
    }
  };

  const criticalCount = students.filter(i => i.performance_status === 'Low').length;

  return (
    <div style={{ marginBottom: '1rem', border: '1px solid var(--border-color)', borderRadius: '0.8rem', overflow: 'hidden' }}>
      {/* Assessment Header */}
      <div
        onClick={onToggle}
        style={{
          padding: '1.2rem',
          background: isExpanded ? 'rgba(0, 96, 156, 0.05)' : 'var(--surface-solid)',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          cursor: 'pointer',
          transition: 'background 0.2s',
          flexWrap: 'wrap',
          gap: '1rem'
        }}
      >
        <div className="flex items-center gap-4">
          {isExpanded ? <ChevronDown size={20} color="var(--primary)" /> : <ChevronRight size={20} color="var(--text-muted)" />}
          <div>
            <h3 style={{ margin: 0, fontSize: '1.05rem', fontWeight: '700' }}>{assKey}</h3>
            <p style={{ margin: 0, fontSize: '0.85rem', color: 'var(--text-muted)' }}>
              {students.length} Student Records • Max: {students[0]?.max_marks}
            </p>
          </div>
        </div>

        <div className="flex items-center gap-3 flex-wrap">
          {isLocked && (
            <span className="badge" style={{ background: 'rgba(0,0,0,0.05)', color: 'var(--text-muted)', display: 'flex', alignItems: 'center', gap: '0.4rem', border: '1px solid var(--border-color)' }}>
              <Lock size={12} /> <span className="hide-on-mobile">Permanently</span> Locked
            </span>
          )}

          {criticalCount > 0 && (
            <>
              <button
                className="btn btn-primary"
                disabled={notifying.ALL}
                style={{ padding: '0.4rem 0.8rem', fontSize: '0.75rem', display: 'flex', alignItems: 'center', gap: '0.4rem' }}
                onClick={handleNotifyAll}
              >
                <Mail size={14} />
                <span className="hide-on-mobile">{notifying.ALL ? "Sending..." : "Notify All Low Performers"}</span>
                <span className="show-on-mobile">{notifying.ALL ? "..." : "Notify All"}</span>
              </button>
              <span className="badge badge-danger" style={{ fontSize: '0.7rem' }}>
                {criticalCount} <span className="hide-on-mobile">Low Performers</span>
              </span>
            </>
          )}
        </div>
      </div>

      {/* Assessment Data Table (Expanded) */}
      {isExpanded && (
        <div className="animate-fade-in" style={{ borderTop: '1px solid var(--border-color)', overflowX: 'auto' }}>
          {isLocked && (
            <div style={{ background: 'rgba(0,0,0,0.02)', padding: '0.8rem 1.2rem', borderBottom: '1px solid var(--border-color)', display: 'flex', alignItems: 'center', gap: '0.6rem', color: 'var(--text-muted)', fontSize: '0.85rem' }}>
              <ShieldCheck size={16} color="var(--success)" />
              <span>This assessment is <strong>finalized</strong>. Marks cannot be modified by any faculty member.</span>
            </div>
          )}
          {/* LOCAL SEARCH/FILTER */}
          <div className="flex justify-between items-center" style={{ padding: '1rem', background: 'rgba(0,0,0,0.01)', borderBottom: '1px solid var(--border-color)', flexWrap: 'wrap', gap: '1rem' }}>
            <p style={{ margin: 0, fontSize: '0.8rem', color: 'var(--text-muted)', fontWeight: '600' }}>SEARCH & FILTER</p>
            <div className="flex gap-4 flex-wrap">
              <select
                className="form-input"
                style={{ width: '150px', fontSize: '0.85rem', padding: '0.4rem 0.8rem' }}
                value={statusFilter}
                onChange={(e) => setStatusFilter(e.target.value)}
                onClick={(e) => e.stopPropagation()}
              >
                <option value="All">All Statuses</option>
                <option value="Good">Good Only</option>
                <option value="Below Threshold">Low Performers Only</option>
              </select>

              <div style={{ position: 'relative' }} onClick={(e) => e.stopPropagation()}>
                <Search size={14} style={{ position: 'absolute', left: '10px', top: '50%', transform: 'translateY(-50%)', color: 'var(--text-muted)' }} />
                <input
                  type="text"
                  placeholder="Filter students..."
                  className="form-input"
                  style={{ paddingLeft: '2.2rem', width: '150px', fontSize: '0.85rem', padding: '0.4rem 0.8rem' }}
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                />
              </div>
            </div>
          </div>

          <div className="table-container">
            <table className="w-full" style={{ borderCollapse: 'collapse', textAlign: 'left', minWidth: '600px' }}>
            <thead style={{ background: 'rgba(0,0,0,0.02)', color: 'var(--text-muted)' }}>
              <tr>
                <th style={{ padding: '0.8rem 1rem', fontSize: '0.8rem' }}>Registration ID</th>
                <th style={{ padding: '0.8rem 1rem', fontSize: '0.8rem' }}>Score</th>
                <th style={{ padding: '0.8rem 1rem', fontSize: '0.8rem' }}>Status</th>
                <th style={{ padding: '0.8rem 1rem', fontSize: '0.8rem', textAlign: 'right' }}>Actions</th>
              </tr>
            </thead>
            <tbody>
              {filteredStudents.length === 0 ? (
                <tr>
                  <td colSpan="4" style={{ padding: '2rem', textAlign: 'center', color: 'var(--text-muted)' }}>
                    No students match your filter in this assessment.
                  </td>
                </tr>
              ) : (
                filteredStudents.map((row, idx) => (
                  <tr key={idx} style={{ borderBottom: idx === filteredStudents.length - 1 ? 'none' : '1px solid rgba(0,0,0,0.05)' }}>
                    <td style={{ padding: '0.8rem 1rem', fontWeight: '600', fontFamily: 'monospace' }}>{row.registration_number}</td>
                    <td style={{ padding: '0.8rem 1rem' }}>
                      <span style={{ fontWeight: '700' }}>{Number(row.marks_obtained).toFixed(1)}</span>
                      <span style={{ color: 'var(--text-muted)', fontSize: '0.8rem' }}> / {Number(row.max_marks).toFixed(0)}</span>
                    </td>
                    <td style={{ padding: '0.8rem 1rem' }}>
                      <span className={`badge ${row.performance_status === 'Low' ? 'badge-danger' : 'badge-success'}`} style={{ fontSize: '0.65rem', padding: '0.2rem 0.5rem' }}>
                        {row.performance_status === 'Low' ? 'Low Performer' : 'Good'}
                      </span>
                    </td>
                    <td style={{ padding: '0.8rem 1rem', textAlign: 'right' }}>
                      {row.performance_status === 'Below Threshold' && (
                        <button
                          className="btn btn-outline"
                          style={{ padding: '0.3rem 0.6rem', fontSize: '0.75rem', borderColor: 'var(--danger)', color: 'var(--danger)' }}
                          disabled={notifying[row.registration_number] || notifying.ALL}
                          onClick={(e) => {
                            e.stopPropagation();
                            handleNotify(row);
                          }}
                        >
                          <Mail size={12} style={{ marginRight: '0.4rem' }} />
                          {notifying[row.registration_number] ? "Sending..." : "Notify Student"}
                        </button>
                      )}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
          </div>

          {!isLocked && (
            <div style={{ padding: '1.5rem', background: 'rgba(239, 68, 68, 0.02)', borderTop: '1px solid var(--border-color)', display: 'flex', justifyContent: 'flex-end', alignItems: 'center', gap: '1rem', flexWrap: 'wrap' }}>
              <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)', textAlign: 'right' }}>
                <strong>Integrity Action:</strong> Once locked, these marks <br /> are permanent and cannot be changed.
              </div>
              <button
                className="btn btn-outline"
                style={{ borderColor: 'var(--danger)', color: 'var(--danger)', background: 'white' }}
                onClick={async (e) => {
                  e.stopPropagation();
                  if (window.confirm("PERMANENT LOCK: Are you absolutely sure? Once locked, NO ONE can modify these marks again.")) {
                    try {
                      await axios.post("/api/db/assessments/lock", {
                        subject_name: students[0].subject_name,
                        assessment_name: assKey
                      });
                      onLock();
                    } catch (err) {
                      alert("Failed to lock: " + (err.response?.data?.error || err.message));
                    }
                  }
                }}
              >
                <Lock size={14} style={{ marginRight: '0.5rem' }} /> Finalize & Lock Marks
              </button>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
