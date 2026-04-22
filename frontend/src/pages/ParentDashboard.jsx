import { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import axios from 'axios';
import { 
  Users, BookOpen, GraduationCap, ClipboardList, Activity,
  LogOut, User, Calendar, CheckCircle2, AlertCircle,
  FileText, Printer, ChevronRight, Brain, Award, ShieldAlert
} from 'lucide-react';
import { RadialBarChart, RadialBar, ResponsiveContainer } from 'recharts';
import Loader from '../components/Loader';

// ── ML Panel for Parent Dashboard ────────────────────────────────────────────
function MLParentPanel({ studentId }) {
  const [pred, setPred]   = useState(null);
  const [grade, setGrade] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.allSettled([
      axios.get(`/api/predict/student/${studentId}`),
      axios.get(`/api/predict/grade/${studentId}`),
    ]).then(([predRes, gradeRes]) => {
      if (predRes.status === 'fulfilled' && predRes.value.data.success) setPred(predRes.value.data);
      if (gradeRes.status === 'fulfilled' && gradeRes.value.data.success) setGrade(gradeRes.value.data);
    }).finally(() => setLoading(false));
  }, [studentId]);

  if (loading) return (
    <div style={{ padding: '2rem', textAlign: 'center', color: '#aaa' }}>
      <Brain size={28} style={{ opacity: 0.3, marginBottom: '0.5rem' }} />
      <p style={{ fontSize: '0.9rem', margin: 0 }}>Running AI analysis…</p>
    </div>
  );

  if (!pred && !grade) return null;

  const PERF_COLORS = { High: '#22c55e', Medium: '#f59e0b', Low: '#ef4444' };
  const predColor = PERF_COLORS[pred?.prediction] || '#94a3b8';
  const gradeColors = { S: '#22c55e', A: '#16a34a', B: '#3b82f6', C: '#f59e0b', D: '#f97316', E: '#ef4444', F: '#dc2626' };
  const gradeColor = gradeColors[grade?.grade_letter] || '#94a3b8';

  return (
    <section style={{ marginBottom: '3rem' }}>
      <div className="glass-panel" style={{ padding: 0, background: 'var(--surface-solid)', overflow: 'hidden' }}>
        {/* Header */}
        <div style={{ padding: '1.5rem 2rem', borderBottom: '1px solid #eee', background: 'linear-gradient(135deg, rgba(76,114,176,0.07) 0%, rgba(85,168,104,0.05) 100%)', display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
          <Brain size={22} color="#4C72B0" />
          <div>
            <h2 style={{ margin: 0, fontSize: '1.2rem', fontWeight: '800' }}>AI Academic Analysis</h2>
            <p style={{ margin: 0, fontSize: '0.8rem', color: '#888' }}>AI predictions based on live attendance & marks data</p>
          </div>
        </div>

        <div style={{ padding: '1.5rem 2rem', display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '1.5rem' }}>

          {/* Performance Classification */}
          {pred && (
            <div style={{ padding: '1.25rem', borderRadius: '0.9rem', background: `${predColor}10`, border: `1px solid ${predColor}30` }}>
              <div style={{ fontSize: '0.7rem', fontWeight: '800', color: '#888', textTransform: 'uppercase', letterSpacing: '0.5px', marginBottom: '0.75rem' }}>Predicted Academic Standing</div>
              <div style={{ fontSize: '2rem', fontWeight: '900', color: predColor }}>{pred.prediction}</div>
              <div style={{ fontSize: '0.8rem', color: '#888', marginTop: '0.25rem' }}>AI Certainty: {Math.round((pred.confidence || 0) * 100)}%</div>
              {/* Prob bars */}
              <div style={{ marginTop: '0.75rem', display: 'flex', flexDirection: 'column', gap: '0.3rem' }}>
                {pred.probabilities && Object.entries(pred.probabilities).map(([cls, prob]) => (
                  <div key={cls}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.7rem', marginBottom: '0.15rem' }}>
                      <span style={{ color: PERF_COLORS[cls], fontWeight: '700' }}>{cls}</span>
                      <span>{Math.round(prob * 100)}%</span>
                    </div>
                    <div style={{ height: '4px', borderRadius: '99px', background: 'rgba(0,0,0,0.06)' }}>
                      <div style={{ height: '100%', borderRadius: '99px', width: `${prob * 100}%`, background: PERF_COLORS[cls] }} />
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Predicted Grade */}
          {grade && (
            <div style={{ padding: '1.25rem', borderRadius: '0.9rem', background: `${gradeColor}10`, border: `1px solid ${gradeColor}30` }}>
              <div style={{ fontSize: '0.7rem', fontWeight: '800', color: '#888', textTransform: 'uppercase', letterSpacing: '0.5px', marginBottom: '0.75rem' }}>
                <Award size={12} style={{ display: 'inline', marginRight: '0.3rem' }} />Predicted Grade
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
                <div style={{ width: '60px', height: '60px', borderRadius: '0.8rem', background: `${gradeColor}20`, border: `2px solid ${gradeColor}`, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                  <span style={{ fontSize: '1.8rem', fontWeight: '900', color: gradeColor }}>{grade.grade_letter}</span>
                </div>
                <div>
                  <div style={{ fontSize: '1.4rem', fontWeight: '900' }}>{grade.expected_percentage}%</div>
                  <div style={{ fontSize: '0.8rem', color: '#888' }}>GPA: <b style={{ color: gradeColor }}>{grade.grade_points}/10</b></div>
                </div>
              </div>
            </div>
          )}

          {/* At-Risk Score */}
          {grade && (
            <div style={{ padding: '1.25rem', borderRadius: '0.9rem', background: `${grade.risk_color}08`, border: `1px solid ${grade.risk_color}30`, display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
              <div style={{ fontSize: '0.7rem', fontWeight: '800', color: '#888', textTransform: 'uppercase', letterSpacing: '0.5px', marginBottom: '0.5rem' }}>
                <ShieldAlert size={12} style={{ display: 'inline', marginRight: '0.3rem' }} />At-Risk Score
              </div>
              <div style={{ position: 'relative', width: '130px', height: '80px' }}>
                <ResponsiveContainer width="100%" height="100%">
                  <RadialBarChart cx="50%" cy="90%" innerRadius="70%" outerRadius="100%"
                    startAngle={180} endAngle={0}
                    data={[{ value: grade.risk_score, fill: grade.risk_color }, { value: 100 - grade.risk_score, fill: 'rgba(0,0,0,0.05)' }]}>
                    <RadialBar dataKey="value" cornerRadius={5} background={false} />
                  </RadialBarChart>
                </ResponsiveContainer>
                <div style={{ position: 'absolute', bottom: 0, left: '50%', transform: 'translateX(-50%)', textAlign: 'center' }}>
                  <div style={{ fontSize: '1.5rem', fontWeight: '900', color: grade.risk_color, lineHeight: 1 }}>{grade.risk_score}</div>
                  <div style={{ fontSize: '0.65rem', fontWeight: '800', color: grade.risk_color, textTransform: 'uppercase' }}>{grade.risk_level}</div>
                </div>
              </div>
              <p style={{ margin: '0.5rem 0 0', fontSize: '0.75rem', color: '#888', textAlign: 'center' }}>
                {grade.risk_level === 'safe' && 'Student is performing well.'}
                {grade.risk_level === 'moderate' && 'Some areas need improvement.'}
                {grade.risk_level === 'high' && 'Parental support recommended.'}
                {grade.risk_level === 'critical' && 'Urgent academic intervention needed.'}
              </p>
            </div>
          )}

          {/* Recommendations */}
          {pred?.explanation?.recommendations?.length > 0 && (
            <div style={{ padding: '1.25rem', borderRadius: '0.9rem', background: 'rgba(245,158,11,0.06)', border: '1px solid rgba(245,158,11,0.2)' }}>
              <div style={{ fontSize: '0.7rem', fontWeight: '800', color: '#888', textTransform: 'uppercase', letterSpacing: '0.5px', marginBottom: '0.75rem' }}>💡 AI Recommendations</div>
              <ul style={{ margin: 0, paddingLeft: '1rem' }}>
                {pred.explanation.recommendations.slice(0, 3).map((r, i) => (
                  <li key={i} style={{ fontSize: '0.8rem', color: '#78350f', marginBottom: '0.4rem', lineHeight: 1.4 }}>{r}</li>
                ))}
              </ul>
            </div>
          )}
        </div>
      </div>
    </section>
  );
}



export default function ParentDashboard() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [student, setStudent] = useState(null);
  const [marks, setMarks] = useState([]);
  const [attendance, setAttendance] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  // Institutional Subject Order (as per your reference photo)
  const SUBJECT_ORDER = ['SE', 'PADCOM', 'CNS', 'CLSA', 'ML', 'IT', 'TRG', 'Training (TRG)', 'TRg'];

  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        const delay = new Promise(resolve => setTimeout(resolve, 1500));
        const [studentRes, marksRes, attnRes] = await Promise.all([
          axios.get(`/api/db/students/reg/${id}`),
          axios.get(`/api/db/students/${id}/marks`),
          axios.get(`/api/db/attendance/summary/student/${id}`),
          delay
        ]);

        if (studentRes.data.success) {
          setStudent(studentRes.data.student);
        }
        setMarks(marksRes.data.marks || []);
        setAttendance(attnRes.data.summary || []);
      } catch (err) {
        console.error("Parent Dashboard Fetch Error:", err);
        setError("Unable to connect to academic records. Please try again later.");
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, [id]);

  // Preload Images for "Instant" feel
  useEffect(() => {
    if (id) {
      const studentImg = new Image();
      studentImg.src = `https://raw.githubusercontent.com/saichandh932/photos/main/${id}.webp`;
      const fallbackImg = new Image();
      fallbackImg.src = "https://raw.githubusercontent.com/saichandh932/photos/main/def-image.webp";
    }
  }, [id]);

  if (loading) return <Loader text="Retrieving student academic records..." />;
  if (error) return (
    <div className="container mt-4 text-center">
      <div className="glass-panel" style={{ padding: '3rem', maxWidth: '500px', margin: '0 auto' }}>
        <AlertCircle size={48} color="var(--danger)" style={{ marginBottom: '1rem' }} />
        <h2 style={{ color: 'var(--danger)' }}>Access Error</h2>
        <p>{error}</p>
        <button className="btn btn-primary mt-4" onClick={() => navigate("/")}>Return to Login</button>
      </div>
    </div>
  );

  // --- DATA PROCESSING ---

  // 1. Calculate Overall Attendance
  const totalClasses = attendance.reduce((acc, curr) => acc + curr.total_classes, 0);
  const presentClasses = attendance.reduce((acc, curr) => acc + curr.present_count, 0);
  const overallAttendance = totalClasses > 0 ? ((presentClasses / totalClasses) * 100).toFixed(2) : "0.00";

  // 2. Pivot Marks for the Grid
  const uniqueAssessments = [...new Set(marks.map(m => m.assessment_name))].sort((a, b) => {
    // Basic sorting to try to group Module 1 together etc if possible
    return a.localeCompare(b);
  });
  
  const subjectsInMarks = [...new Set(marks.map(m => m.subject_name))];
  const displaySubjects = SUBJECT_ORDER.filter(s => subjectsInMarks.includes(s))
    .concat(subjectsInMarks.filter(s => !SUBJECT_ORDER.includes(s)));

  const getMarkFor = (assessment, subject) => {
    const record = marks.find(m => m.assessment_name === assessment && m.subject_name === subject);
    return record ? record.marks_obtained : '-';
  };

  return (
    <div className="min-h-screen" style={{ background: 'var(--bg-color)', color: 'var(--text-main)', paddingBottom: '5rem' }}>
      
      {/* Premium Header */}
      <header className="vignan-nav" style={{ justifyContent: 'space-between', padding: '0 1.5rem', background: 'var(--vignan-navy)', border: 'none', height: 'auto', minHeight: '80px', flexWrap: 'wrap', gap: '1rem' }}>
        <div className="flex items-center gap-4">
           <img src="/vignan_logo.png" alt="Vignan logo" style={{ height: '40px', filter: 'brightness(0) invert(1)' }} />
           <div className="hide-on-mobile" style={{ height: '30px', width: '1px', background: 'rgba(255,255,255,0.2)', margin: '0 0.5rem' }}></div>
           <h2 className="hide-on-mobile" style={{ margin: 0, color: 'white', fontSize: '1.2rem', fontWeight: '800', letterSpacing: '1px' }}>PARENT PORTAL</h2>
        </div>
        <button 
          className="btn" 
          onClick={() => { sessionStorage.clear(); navigate("/"); }}
          style={{ background: 'rgba(255,255,255,0.1)', color: 'white', border: '1px solid rgba(255,255,255,0.2)', borderRadius: '2rem', padding: '0.4rem 1rem', fontSize: '0.85rem' }}
        >
          <LogOut size={14} style={{ marginRight: '0.4rem' }} /> Logout
        </button>
      </header>

      {/* Hero / Quick Stats */}
      <div style={{ 
        background: 'linear-gradient(135deg, var(--vignan-navy) 0%, var(--vignan-blue) 100%)', 
        padding: '3rem 1.5rem 6rem',
        color: 'white',
        position: 'relative',
        overflow: 'hidden'
      }}>
        <div style={{ position: 'relative', zIndex: 2, display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '2rem' }}>
          <div className="flex items-center gap-6" style={{ flexWrap: 'wrap' }}>
            <div style={{ 
              width: 'clamp(80px, 20vw, 120px)', 
              height: 'clamp(80px, 20vw, 120px)', 
              borderRadius: '1rem', 
              background: 'white', 
              padding: '0.4rem',
              boxShadow: '0 10px 25px rgba(0,0,0,0.2)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center'
            }}>
              <img 
                src={`https://raw.githubusercontent.com/saichandh932/photos/main/${id}.webp`} 
                alt="Student" 
                style={{ 
                  width: '100%', 
                  height: '100%', 
                  objectFit: 'cover', 
                  borderRadius: '0.8rem',
                  display: 'block'
                }} 
                onError={(e) => { 
                  if (e.target.src !== "https://raw.githubusercontent.com/saichandh932/photos/main/def-image.webp") {
                    e.target.src = "https://raw.githubusercontent.com/saichandh932/photos/main/def-image.webp";
                  } else {
                    e.target.src = "/placeholder_student.png"; // Final local fallback
                  }
                }}
              />
            </div>
            <div>
              <h1 style={{ fontSize: 'clamp(1.5rem, 5vw, 2.5rem)', fontWeight: '800', margin: 0 }}>{student?.name || 'Academic Record'}</h1>
              <p style={{ opacity: 0.8, fontSize: 'clamp(0.9rem, 2vw, 1.1rem)', marginTop: '0.5rem' }}>
                <Users size={18} style={{ display: 'inline', marginRight: '0.5rem' }} />
                Reg No: <b style={{ letterSpacing: '1px' }}>{id}</b> | Batch {student?.batch || '2023-27'}
              </p>
            </div>
          </div>

          <div className="flex gap-4 flex-wrap">
             <div className="glass-panel" style={{ background: 'rgba(255,255,255,0.1)', border: '1px solid rgba(255,255,255,0.2)', padding: '1rem 1.5rem', textAlign: 'center', flex: '1' }}>
                <p style={{ fontSize: '0.7rem', textTransform: 'uppercase', letterSpacing: '1px', marginBottom: '0.4rem', opacity: 0.8 }}>Overall Attendance</p>
                <h3 style={{ fontSize: 'clamp(1.5rem, 4vw, 2rem)', fontWeight: '900', margin: 0, color: 'white' }}>{overallAttendance}%</h3>
             </div>
             <div className="glass-panel" style={{ background: 'rgba(255,255,255,0.1)', border: '1px solid rgba(255,255,255,0.2)', padding: '1rem 1.5rem', textAlign: 'center', flex: '1' }}>
                <p style={{ fontSize: '0.7rem', textTransform: 'uppercase', letterSpacing: '1px', marginBottom: '0.4rem', opacity: 0.8 }}>Academic Standing</p>
                <h3 style={{ fontSize: 'clamp(1.5rem, 4vw, 2rem)', fontWeight: '900', margin: 0, color: student?.performance === 'Low' ? '#ff6b6b' : '#51cf66' }}>
                  {student?.performance?.toUpperCase() || 'GOOD'}
                </h3>
             </div>
          </div>
        </div>
      </div>

      {/* Main Content Sections */}
      <div className="container" style={{ marginTop: '-4rem', position: 'relative', zIndex: 10 }}>
        
        {/* 1. INTRA SEMESTER EXAMINATIONS GRID (From Photo) */}
        <section style={{ marginBottom: '3rem' }}>
          <div className="glass-panel" style={{ padding: '0', background: 'var(--surface-solid)', overflow: 'hidden' }}>
            <div style={{ padding: '1.5rem 2rem', background: 'white', borderBottom: '1px solid #eee', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
               <h2 style={{ fontSize: '1.25rem', fontWeight: '800', margin: 0, display: 'flex', alignItems: 'center', gap: '0.8rem' }}>
                 <ClipboardList color="var(--primary)" /> Intra Semester Examinations
               </h2>
               <button className="btn btn-outline" style={{ fontSize: '0.8rem' }} onClick={() => window.print()}>
                 <Printer size={14} style={{ marginRight: '0.4rem' }} /> Print Scorecard
               </button>
            </div>
            
            <div className="table-container">
              <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'center', minWidth: '800px' }}>
                <thead>
                  <tr style={{ background: 'var(--vignan-light)', borderBottom: '2px solid #ddd' }}>
                    <th style={{ padding: '1.2rem', textAlign: 'left', minWidth: '200px', background: '#fcfcfc', color: '#666', borderRight: '1px solid #eee' }}>Assessment Name</th>
                    {displaySubjects.map(sub => (
                      <th key={sub} style={{ padding: '1.2rem', fontWeight: '800', color: 'var(--vignan-navy)' }}>
                        {sub}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {uniqueAssessments.length === 0 ? (
                    <tr>
                      <td colSpan={displaySubjects.length + 1} style={{ padding: '4rem', color: 'var(--text-muted)' }}>
                        No examination records found for the current semester.
                      </td>
                    </tr>
                  ) : (
                    uniqueAssessments.map((ass, idx) => (
                      <tr key={ass} style={{ borderBottom: '1px solid #eee', background: idx % 2 === 0 ? 'white' : 'rgba(0,0,0,0.01)' }}>
                        <td style={{ padding: '1.2rem', textAlign: 'left', fontWeight: '600', color: '#444', borderRight: '1px solid #eee' }}>
                          <span style={{ display: 'block', fontSize: '1rem' }}>{ass}</span>
                          <span style={{ fontSize: '0.7rem', color: '#999', textTransform: 'uppercase' }}>Consolidated Record</span>
                        </td>
                        {displaySubjects.map(sub => {
                          const val = getMarkFor(ass, sub);
                          return (
                            <td key={sub} style={{ padding: '1.2rem', fontSize: '1.1rem', fontWeight: '700' }}>
                              <span style={{ 
                                color: val === '-' ? '#ccc' : (val < 10 ? 'var(--vignan-red)' : 'var(--vignan-navy)') 
                              }}>
                                {val}
                              </span>
                            </td>
                          );
                        })}
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          </div>
        </section>

        {/* 2. AI PANEL */}
        <MLParentPanel studentId={id} />

        <div className="grid gap-8" style={{ gridTemplateColumns: 'repeat(auto-fit, minmax(clamp(300px, 100%, 450px), 1fr))' }}>
          
          {/* 2. SUBJECT-WISE ATTENDANCE */}
          <section>
             <div className="glass-panel card" style={{ background: 'var(--surface-solid)', padding: '0' }}>
                <div style={{ padding: '1.5rem', borderBottom: '1px solid #eee' }}>
                   <h2 style={{ fontSize: '1.2rem', fontWeight: '800', margin: 0, display: 'flex', alignItems: 'center', gap: '0.6rem' }}>
                     <Activity color="var(--primary)" /> Attendance Breakdown
                   </h2>
                </div>
                <div style={{ padding: '1rem' }}>
                  {attendance.length === 0 ? (
                    <div className="text-center py-8 text-muted">No attendance logs available for this student.</div>
                  ) : (
                    attendance.map(item => (
                      <div key={item.subject_name} style={{ 
                        padding: '1rem', 
                        borderBottom: '1px solid #f5f5f5',
                        display: 'flex',
                        justifyContent: 'space-between',
                        alignItems: 'center'
                      }}>
                        <div>
                           <div style={{ fontWeight: '700', color: 'var(--vignan-navy)' }}>{item.subject_name}</div>
                           <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                             Classes: {item.present_count} / {item.total_classes} attended
                           </div>
                        </div>
                        <div style={{ textAlign: 'flex-end', display: 'flex', alignItems: 'center', gap: '1rem' }}>
                           <div style={{ width: '100px', height: '8px', background: '#eee', borderRadius: '4px', overflow: 'hidden' }}>
                              <div style={{ 
                                width: `${item.percentage}%`, 
                                height: '100%', 
                                background: item.percentage < 75 ? 'var(--vignan-red)' : 'var(--vignan-blue)' 
                              }}></div>
                           </div>
                           <span style={{ fontWeight: '800', width: '50px', fontSize: '0.9rem', color: item.percentage < 75 ? 'var(--vignan-red)' : 'var(--vignan-navy)' }}>
                             {item.percentage}%
                           </span>
                        </div>
                      </div>
                    ))
                  )}
                </div>
             </div>
          </section>

          {/* 3. STUDENT PROFILE DETAILS */}
          <section>
             <div className="glass-panel card" style={{ background: 'var(--surface-solid)', padding: '2rem' }}>
                <h2 style={{ fontSize: '1.2rem', fontWeight: '800', marginBottom: '1.5rem', borderBottom: '2px solid var(--vignan-blue)', paddingBottom: '0.5rem', display: 'inline-block' }}>
                  Official Profile
                </h2>
                
                <div className="responsive-grid" style={{ gridTemplateColumns: 'repeat(auto-fill, minmax(140px, 1fr))', gap: '1.5rem' }}>
                   <div>
                      <p style={{ margin: 0, fontSize: '0.8rem', color: '#999', textTransform: 'uppercase' }}>Parent/Guardian</p>
                      <p style={{ margin: '0.2rem 0 0', fontWeight: '600' }}>{student?.parent_name || 'N/A'}</p>
                   </div>
                   <div>
                      <p style={{ margin: 0, fontSize: '0.8rem', color: '#999', textTransform: 'uppercase' }}>Phone</p>
                      <p style={{ margin: '0.2rem 0 0', fontWeight: '600' }}>{student?.phone || 'N/A'}</p>
                   </div>
                   <div>
                      <p style={{ margin: 0, fontSize: '0.8rem', color: '#999', textTransform: 'uppercase' }}>Batch</p>
                      <p style={{ margin: '0.2rem 0 0', fontWeight: '600' }}>{student?.batch || '2023-2027'}</p>
                   </div>
                   <div>
                      <p style={{ margin: 0, fontSize: '0.8rem', color: '#999', textTransform: 'uppercase' }}>Department</p>
                      <p style={{ margin: '0.2rem 0 0', fontWeight: '600' }}>CS & Engineering</p>
                   </div>
                </div>

                <div style={{ marginTop: '2rem', padding: '1rem', border: '1px dashed #ddd', borderRadius: '0.8rem', background: '#fcfcfc' }}>
                   <div style={{ display: 'flex', gap: '1rem', alignItems: 'center' }}>
                      <AlertCircle size={24} color={student?.performance === 'Low' ? 'var(--danger)' : 'var(--success)'} />
                      <p style={{ margin: 0, fontSize: '0.85rem', color: '#666' }}>
                        {student?.performance === 'Low' 
                          ? 'Automated alerts for low attendance/performance are currently ACTIVE for this account.'
                          : 'Student performance is within institutional expectations. Keep up the good work!'}
                      </p>
                   </div>
                </div>
             </div>
          </section>

        </div>
      </div>
    </div>
  );
}
