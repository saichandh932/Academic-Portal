import { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import axios from 'axios';
import {
  AlertCircle, CheckCircle2, BookOpen, GraduationCap,
  ClipboardList, Activity, LogOut, User, ChevronDown,
  ChevronUp, Brain, TrendingUp, TrendingDown, Minus,
  Lightbulb, Award, ShieldAlert
} from 'lucide-react';
import {
  PieChart, Pie, Cell, ResponsiveContainer, Tooltip,
  LineChart, Line, XAxis, YAxis, CartesianGrid, Legend,
  RadialBarChart, RadialBar
} from 'recharts';
import Loader from '../components/Loader';
import TopicMastery from '../components/TopicMastery';

// ── Grade Prediction Card ─────────────────────────────────────────────────────
function GradeCard({ registrationNumber }) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    axios.get(`/api/predict/grade/${registrationNumber}`)
      .then(r => { if (r.data.success) setData(r.data); })
      .catch(() => {})
      .finally(() => setLoading(false));
  }, [registrationNumber]);

  if (loading) return (
    <div className="glass-panel" style={{ padding: '2rem', textAlign: 'center', background: 'var(--surface-solid)' }}>
      <Award size={28} style={{ opacity: 0.3 }} />
      <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem', marginTop: '0.5rem' }}>Computing predicted grade…</p>
    </div>
  );
  if (!data) return null;

  const { expected_percentage, grade_letter, grade_points, risk_score, risk_level, risk_color, grade_table } = data;

  // Gauge data for risk score
  const gaugeData = [{ value: risk_score, fill: risk_color }, { value: 100 - risk_score, fill: 'rgba(0,0,0,0.06)' }];

  const gradeColors = { S: '#22c55e', A: '#16a34a', B: '#3b82f6', C: '#f59e0b', D: '#f97316', E: '#ef4444', F: '#dc2626' };
  const gradeColor = gradeColors[grade_letter] || '#94a3b8';

  return (
    <div className="glass-panel" style={{ overflow: 'hidden', background: 'var(--surface-solid)' }}>
      {/* Header */}
      <div style={{ padding: '1.5rem', borderBottom: '1px solid var(--border-color)', background: `linear-gradient(135deg, ${gradeColor}12, transparent)`, display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
        <Award size={22} color={gradeColor} />
        <div>
          <h2 className="font-bold" style={{ margin: 0 }}>Predicted Semester Grade</h2>
          <p style={{ margin: 0, fontSize: '0.8rem', color: 'var(--text-muted)' }}>AI-Powered Prediction · Vignan 10-point grading scale</p>
        </div>
      </div>

      <div style={{ padding: '1.5rem', display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))', gap: '1.5rem' }}>

        {/* Left: Grade pill + stats */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
          {/* Big grade pill */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '1.5rem' }}>
            <div style={{ width: '90px', height: '90px', borderRadius: '1.2rem', background: `${gradeColor}18`, border: `3px solid ${gradeColor}`, display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0 }}>
              <span style={{ fontSize: '2.8rem', fontWeight: '900', color: gradeColor }}>{grade_letter}</span>
            </div>
            <div>
              <div style={{ fontSize: '0.75rem', fontWeight: '800', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.5px' }}>Expected Score</div>
              <div style={{ fontSize: '2rem', fontWeight: '900' }}>{expected_percentage}%</div>
              <div style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>GPA Points: <b style={{ color: gradeColor }}>{grade_points} / 10.0</b></div>
            </div>
          </div>

          {/* Grade scale pills */}
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.4rem' }}>
            {grade_table.map(g => (
              <span key={g.letter} style={{
                padding: '0.2rem 0.6rem', borderRadius: '99px', fontSize: '0.7rem', fontWeight: '700',
                background: g.is_predicted ? gradeColor : 'rgba(0,0,0,0.05)',
                color: g.is_predicted ? 'white' : 'var(--text-muted)',
                border: g.is_predicted ? `1px solid ${gradeColor}` : '1px solid transparent',
                transition: 'all 0.2s'
              }}>
                {g.letter} ({g.range})
              </span>
            ))}
          </div>
        </div>

        {/* Right: Risk Score gauge */}
        <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '0.5rem' }}>
          <div style={{ fontSize: '0.75rem', fontWeight: '800', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.5px', marginBottom: '0.25rem' }}>
            <ShieldAlert size={13} style={{ display: 'inline', marginRight: '0.3rem' }} />
            At-Risk Score
          </div>
          <div style={{ position: 'relative', width: '160px', height: '100px' }}>
            <ResponsiveContainer width="100%" height="100%">
              <RadialBarChart cx="50%" cy="90%" innerRadius="70%" outerRadius="100%"
                startAngle={180} endAngle={0} data={gaugeData}>
                <RadialBar dataKey="value" cornerRadius={6} background={false} />
              </RadialBarChart>
            </ResponsiveContainer>
            <div style={{ position: 'absolute', bottom: '0', left: '50%', transform: 'translateX(-50%)', textAlign: 'center' }}>
              <div style={{ fontSize: '2rem', fontWeight: '900', color: risk_color, lineHeight: 1 }}>{risk_score}</div>
              <div style={{ fontSize: '0.7rem', fontWeight: '800', color: risk_color, textTransform: 'uppercase' }}>{risk_level}</div>
            </div>
          </div>
          <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', textAlign: 'center', maxWidth: '180px' }}>
            {risk_level === 'safe' && '✅ You are on a good academic trajectory.'}
            {risk_level === 'moderate' && '⚡ Some areas need attention to stay on track.'}
            {risk_level === 'high' && '⚠️ Several risk factors detected. Seek help early.'}
            {risk_level === 'critical' && '🚨 Immediate intervention recommended.'}
          </div>
        </div>
      </div>
    </div>
  );
}


const SYLLABUS_SUBJECTS = ['SE', 'CNS', 'PADCOM', 'ML', 'QALR'];

const PERF_COLORS = { High: '#22c55e', Medium: '#f59e0b', Low: '#ef4444' };
const IMPACT_COLORS = { positive: '#22c55e', negative: '#ef4444', neutral: '#94a3b8' };

function AIInsightCard({ registrationNumber }) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    axios.get(`/api/predict/student/${registrationNumber}`)
      .then(r => setData(r.data))
      .catch(() => setData(null))
      .finally(() => setLoading(false));
  }, [registrationNumber]);

  if (loading) return (
    <div className="glass-panel" style={{ padding: '2rem', textAlign: 'center', background: 'var(--surface-solid)' }}>
      <Brain size={28} style={{ opacity: 0.4, marginBottom: '0.5rem' }} />
      <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem' }}>Running AI analysis…</p>
    </div>
  );

  if (!data?.success) return null;

  const { prediction, confidence, explanation } = data;
  const color = PERF_COLORS[prediction] || '#94a3b8';
  const confPct = Math.round((confidence || 0) * 100);

  return (
    <div className="glass-panel" style={{ overflow: 'hidden', background: 'var(--surface-solid)' }}>
      {/* Header */}
      <div style={{ padding: '1.5rem', borderBottom: '1px solid var(--border-color)', background: `linear-gradient(135deg, ${color}15, transparent)`, display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
        <Brain color={color} size={22} />
        <div>
          <h2 className="font-bold" style={{ margin: 0 }}>AI Performance Prediction</h2>
          <p style={{ margin: 0, fontSize: '0.8rem', color: 'var(--text-muted)' }}>Live analysis from your real attendance & marks data</p>
        </div>
        <div style={{ marginLeft: 'auto', textAlign: 'center' }}>
          <div style={{ fontSize: '1.8rem', fontWeight: '900', color }}>{prediction}</div>
          <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>AI Certainty: {confPct}%</div>
        </div>
      </div>

      <div style={{ padding: '1.5rem' }}>
        {/* Probability bars */}
        {data.probabilities && (
          <div style={{ marginBottom: '1.5rem', display: 'flex', gap: '0.75rem', flexWrap: 'wrap' }}>
            {Object.entries(data.probabilities).map(([cls, prob]) => (
              <div key={cls} style={{ flex: 1, minWidth: '100px' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.75rem', marginBottom: '0.3rem' }}>
                  <span style={{ fontWeight: '700', color: PERF_COLORS[cls] }}>{cls}</span>
                  <span>{Math.round(prob * 100)}%</span>
                </div>
                <div style={{ height: '6px', borderRadius: '99px', background: 'rgba(0,0,0,0.07)' }}>
                  <div style={{ height: '100%', borderRadius: '99px', width: `${prob * 100}%`, background: PERF_COLORS[cls], transition: 'width 0.8s ease' }} />
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Feature factors */}
        {explanation?.factors && (
          <div style={{ marginBottom: '1.5rem' }}>
            <div style={{ fontSize: '0.75rem', fontWeight: '800', textTransform: 'uppercase', color: 'var(--text-muted)', marginBottom: '0.75rem', letterSpacing: '0.5px' }}>
              Key Factors Driving This Prediction
            </div>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(200px, 1fr))', gap: '0.75rem' }}>
              {explanation.factors.slice(0, 5).map(f => (
                <div key={f.feature} style={{ padding: '0.9rem 1rem', borderRadius: '0.75rem', background: `${IMPACT_COLORS[f.impact]}12`, border: `1px solid ${IMPACT_COLORS[f.impact]}30` }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.25rem' }}>
                    <span style={{ fontSize: '0.75rem', fontWeight: '700', color: 'var(--text-muted)' }}>{f.label}</span>
                    <span style={{ fontSize: '0.7rem', fontWeight: '800', color: IMPACT_COLORS[f.impact], textTransform: 'uppercase' }}>{f.impact}</span>
                  </div>
                  <div style={{ fontSize: '1.3rem', fontWeight: '900' }}>{f.value}{f.feature === 'study_hours' ? 'h' : '%'}</div>
                  <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)', marginTop: '0.2rem', lineHeight: 1.3 }}>{f.message}</div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Recommendations */}
        {explanation?.recommendations?.length > 0 && (
          <div style={{ background: 'rgba(245,158,11,0.08)', border: '1px solid rgba(245,158,11,0.25)', borderRadius: '0.75rem', padding: '1rem 1.25rem' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.75rem' }}>
              <Lightbulb size={16} color="#f59e0b" />
              <span style={{ fontWeight: '800', fontSize: '0.85rem', color: '#92400e' }}>AI Recommendations</span>
            </div>
            <ul style={{ margin: 0, paddingLeft: '1.2rem' }}>
              {explanation.recommendations.map((r, i) => (
                <li key={i} style={{ fontSize: '0.85rem', color: '#78350f', marginBottom: '0.4rem', lineHeight: 1.5 }}>{r}</li>
              ))}
            </ul>
          </div>
        )}
      </div>
    </div>
  );
}

function TrendChart({ registrationNumber }) {
  const [trend, setTrend] = useState([]);
  const [direction, setDirection] = useState('stable');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    axios.get(`/api/predict/trend/${registrationNumber}?limit=10`)
      .then(r => {
        if (r.data.success) {
          setTrend(r.data.trend || []);
          setDirection(r.data.trend_direction || 'stable');
        }
      })
      .catch(() => {})
      .finally(() => setLoading(false));
  }, [registrationNumber]);

  if (loading || trend.length < 2) return null;

  const DirectionIcon = direction === 'improving' ? TrendingUp : direction === 'declining' ? TrendingDown : Minus;
  const dirColor = direction === 'improving' ? '#22c55e' : direction === 'declining' ? '#ef4444' : '#94a3b8';

  const chartData = trend.map(t => ({
    date: t.date,
    'High %': Math.round(t.prob_high * 100),
    'Medium %': Math.round(t.prob_medium * 100),
    'Low %': Math.round(t.prob_low * 100),
  }));

  return (
    <div className="glass-panel" style={{ overflow: 'hidden', background: 'var(--surface-solid)' }}>
      <div style={{ padding: '1.5rem', borderBottom: '1px solid var(--border-color)', display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
        <DirectionIcon size={22} color={dirColor} />
        <div>
          <h2 className="font-bold" style={{ margin: 0 }}>Performance Trend</h2>
          <p style={{ margin: 0, fontSize: '0.8rem', color: 'var(--text-muted)' }}>
            Trajectory: <span style={{ fontWeight: '700', color: dirColor, textTransform: 'capitalize' }}>{direction.replace('_', ' ')}</span>
          </p>
        </div>
      </div>
      <div style={{ padding: '1.5rem' }}>
        <ResponsiveContainer width="100%" height={220}>
          <LineChart data={chartData}>
            <CartesianGrid strokeDasharray="3 3" stroke="rgba(0,0,0,0.06)" />
            <XAxis dataKey="date" tick={{ fontSize: 11 }} />
            <YAxis domain={[0, 100]} tickFormatter={v => `${v}%`} tick={{ fontSize: 11 }} />
            <Tooltip formatter={v => `${v}%`} />
            <Legend />
            <Line type="monotone" dataKey="High %" stroke="#22c55e" strokeWidth={2} dot={{ r: 3 }} />
            <Line type="monotone" dataKey="Medium %" stroke="#f59e0b" strokeWidth={2} dot={{ r: 3 }} />
            <Line type="monotone" dataKey="Low %" stroke="#ef4444" strokeWidth={2} dot={{ r: 3 }} />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}

export default function StudentDashboard() {
  const { id } = useParams();
  const [marks, setMarks] = useState([]);
  const [attendance, setAttendance] = useState([]);
  const [studentProfile, setStudentProfile] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const navigate = useNavigate();
  const [expandedSubject, setExpandedSubject] = useState(null);

  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        const delay = new Promise(resolve => setTimeout(resolve, 2000));
        const [studentRes, marksRes, attnRes] = await Promise.all([
          axios.get(`/api/db/students/reg/${id}`),
          axios.get(`/api/db/students/${id}/marks`),
          axios.get(`/api/db/attendance/summary/student/${id}`),
          delay
        ]);
        if (studentRes.data?.success) setStudentProfile(studentRes.data.student);
        setMarks(marksRes.data.marks || []);
        setAttendance(attnRes.data.summary || []);
      } catch (err) {
        console.error('Student Fetch Error:', err);
        setError('Failed to load dashboard data. Ensure backend is running.');
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, [id]);

  useEffect(() => {
    if (id) {
      new Image().src = `https://raw.githubusercontent.com/saichandh932/photos/main/${id}.webp`;
      new Image().src = 'https://raw.githubusercontent.com/saichandh932/photos/main/def-image.webp';
    }
  }, [id]);

  if (loading) return <Loader text="Loading student record..." />;
  if (error) return <div className="container mt-4 text-center" style={{ color: 'var(--danger)' }}>{error}</div>;

  const belowThresholdMarks = marks.filter(m => m.performance_status === 'Below Threshold');
  const avgAttendance = attendance.length > 0
    ? (attendance.reduce((a, s) => a + s.percentage, 0) / attendance.length).toFixed(1)
    : '0';

  return (
    <div className="container animate-fade-in" style={{ paddingBottom: '4rem' }}>
      {/* Header */}
      <div style={{ marginBottom: '2.5rem', display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: '1rem' }}>
        <div>
          <h1 className="font-bold" style={{ fontSize: 'clamp(1.5rem, 5vw, 2.5rem)', marginBottom: '0.5rem' }}>Performance Panel</h1>
          <p style={{ color: 'var(--text-muted)' }}>Reg No: <b style={{ fontFamily: 'monospace', background: 'rgba(0,33,71,0.05)', padding: '0.2rem 0.6rem', borderRadius: '4px', color: 'var(--vignan-blue)' }}>{id}</b></p>
        </div>
        <button className="btn btn-outline" onClick={() => { sessionStorage.clear(); navigate('/', { replace: true }); }}
          style={{ borderColor: 'var(--danger)', color: 'var(--danger)', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <LogOut size={16} /> <span className="hide-on-mobile">Logout</span>
        </button>
      </div>

      <div className="grid gap-8">
        {/* Profile Card */}
        {studentProfile && (
          <div className="glass-panel" style={{ background: 'var(--surface-solid)', padding: 'clamp(1rem,3vw,2rem)', marginBottom: '1rem', display: 'flex', gap: '2rem', alignItems: 'center', flexWrap: 'wrap', justifyContent: 'center' }}>
            <div style={{ width: 'clamp(140px,30vw,180px)', aspectRatio: '1/1', borderRadius: '50%', background: 'linear-gradient(135deg,var(--bg-color) 0%,#e2e8f0 100%)', border: '4px solid white', boxShadow: '0 4px 20px rgba(0,0,0,0.08)', overflow: 'hidden', position: 'relative', flexShrink: 0 }}>
              <img src={`https://raw.githubusercontent.com/saichandh932/photos/main/${id}.webp`} alt={studentProfile.name}
                style={{ width: '100%', height: '100%', objectFit: 'cover', display: 'block', borderRadius: '50%' }}
                onError={e => { if (!e.target.src.includes('def-image')) e.target.src = 'https://raw.githubusercontent.com/saichandh932/photos/main/def-image.webp'; else { e.target.style.display = 'none'; if (e.target.nextSibling) e.target.nextSibling.style.display = 'flex'; } }} />
              <div style={{ display: 'none', alignItems: 'center', justifyContent: 'center', width: '100%', height: '100%' }}>
                <User size={60} color="var(--text-muted)" style={{ opacity: 0.4 }} />
              </div>
            </div>
            <div style={{ flex: 1, minWidth: 'min(100%,300px)' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '1.5rem', borderBottom: '1px solid var(--border-color)', paddingBottom: '1rem' }}>
                <Activity color="var(--primary)" size={20} />
                <h2 className="font-bold" style={{ margin: 0, fontSize: '1.4rem' }}>Institutional Identity</h2>
              </div>
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(200px, 1fr))', gap: '1.2rem' }}>
                {[['Full Name', studentProfile.name || 'N/A'], ['Course & Branch', `${studentProfile.course} | ${studentProfile.branch}`], ['Academic Batch', `Year ${studentProfile.year} (Sem ${studentProfile.semester}) - Sec ${studentProfile.section}`], ['Gender / DOB', `${studentProfile.gender || 'N/A'} | ${studentProfile.dob ? new Date(studentProfile.dob).toLocaleDateString() : 'N/A'}`]].map(([label, val]) => (
                  <div key={label}>
                    <div style={{ fontSize: '0.7rem', fontWeight: '800', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.5px' }}>{label}</div>
                    <div style={{ fontSize: '1rem', fontWeight: '600' }}>{val}</div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* Stat highlights */}
        <div className="stat-grid">
          <div className="glass-panel card">
            <div className="flex items-center gap-2" style={{ color: 'var(--text-muted)', marginBottom: '0.5rem' }}>
              <GraduationCap size={18} /><span style={{ fontSize: '0.8rem', fontWeight: '600', textTransform: 'uppercase' }}>Total Assessments</span>
            </div>
            <div className="card-value">{marks.length}</div>
          </div>
          <div className="glass-panel card" style={{ borderLeft: `4px solid ${belowThresholdMarks.length > 0 ? 'var(--danger)' : 'var(--success)'}`, background: 'var(--surface-solid)' }}>
            <div className="flex items-center gap-2" style={{ color: 'var(--text-muted)', marginBottom: '0.5rem' }}>
              {belowThresholdMarks.length > 0 ? <AlertCircle size={18} color="var(--danger)" /> : <CheckCircle2 size={18} color="var(--success)" />}
              <span style={{ fontSize: '0.8rem', fontWeight: '600', textTransform: 'uppercase' }}>Status Overview</span>
            </div>
            <div className="card-value" style={{ fontSize: '1.5rem', color: belowThresholdMarks.length > 0 ? 'var(--danger)' : 'var(--success)' }}>
              {belowThresholdMarks.length > 0 ? `${belowThresholdMarks.length} Critical Flags` : 'All Performance Good'}
            </div>
          </div>
          <div className="glass-panel card" style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', position: 'relative' }}>
            <div style={{ width: '100%', height: '140px', position: 'relative' }}>
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie data={[{ name: 'Present', value: attendance.reduce((a, s) => a + s.present_count, 0) }, { name: 'Absent', value: attendance.reduce((a, s) => a + (s.total_classes - s.present_count), 0) }]}
                    cx="50%" cy="50%" innerRadius={45} outerRadius={60} startAngle={90} endAngle={450} dataKey="value" stroke="none">
                    <Cell fill="var(--primary)" /><Cell fill="rgba(0,0,0,0.05)" />
                  </Pie>
                </PieChart>
              </ResponsiveContainer>
              <div style={{ position: 'absolute', top: '50%', left: '50%', transform: 'translate(-50%,-50%)', textAlign: 'center' }}>
                <div style={{ fontSize: '1.4rem', fontWeight: '900' }}>{avgAttendance}%</div>
              </div>
            </div>
            <div style={{ paddingLeft: '1rem' }}>
              <div style={{ fontSize: '0.75rem', fontWeight: '800', color: 'var(--text-muted)' }}>OVERALL ATTENDANCE</div>
              <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>Across All Subjects</div>
            </div>
          </div>
        </div>

        {/* ── AI INSIGHT CARD ────────────────────────────────────── */}
        <AIInsightCard registrationNumber={id} />

        {/* ── GRADE + AT-RISK CARD ───────────────────────────────── */}
        <GradeCard registrationNumber={id} />

        {/* ── TREND CHART ────────────────────────────────────────── */}
        <TrendChart registrationNumber={id} />

        {/* Attendance Breakdown */}
        <div className="glass-panel" style={{ overflow: 'hidden', background: 'var(--surface-solid)' }}>
          <div style={{ padding: '1.5rem', borderBottom: '1px solid var(--border-color)', background: 'rgba(0,96,156,0.05)', display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
            <Activity color="var(--primary)" /><h2 className="font-bold" style={{ margin: 0 }}>Subject-wise Attendance</h2>
          </div>
          <div style={{ padding: '1.5rem' }}>
            {attendance.length === 0 ? <p style={{ textAlign: 'center', color: 'var(--text-muted)' }}>No attendance records found.</p> : (
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(200px, 1fr))', gap: '1.5rem' }}>
                {attendance.map((a, i) => (
                  <div key={i} className="glass-panel" style={{ padding: '1.2rem', borderLeft: `4px solid ${a.percentage < 75 ? 'var(--danger)' : 'var(--success)'}` }}>
                    <div style={{ fontSize: '0.75rem', fontWeight: '800', opacity: 0.6, marginBottom: '0.5rem' }}>{a.subject_name}</div>
                    <div style={{ fontSize: '1.8rem', fontWeight: '900' }}>{a.percentage}%</div>
                    <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>{a.present_count} / {a.total_classes} Classes</div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Gradebook */}
        <div className="glass-panel" style={{ overflow: 'hidden', background: 'var(--surface-solid)' }}>
          <div style={{ padding: '1.5rem', borderBottom: '1px solid var(--border-color)', background: 'rgba(0,0,0,0.02)', display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
            <ClipboardList color="var(--primary)" /><h2 className="font-bold" style={{ margin: 0 }}>Academic Gradebook</h2>
          </div>
          <div className="table-container">
            <table className="w-full" style={{ borderCollapse: 'collapse', textAlign: 'left', minWidth: '600px' }}>
              <thead style={{ background: 'rgba(0,0,0,0.03)', color: 'var(--text-muted)' }}>
                <tr>{['Subject', 'Assessment', 'Marks Obtained', 'Status'].map(h => <th key={h} style={{ padding: '1rem', fontSize: '0.85rem' }}>{h}</th>)}</tr>
              </thead>
              <tbody style={{ borderTop: '1px solid var(--border-color)' }}>
                {marks.length === 0 ? <tr><td colSpan="4" style={{ padding: '3rem', textAlign: 'center', color: 'var(--text-muted)' }}>No grades recorded yet.</td></tr> :
                  marks.map((m, idx) => (
                    <tr key={idx} style={{ borderBottom: '1px solid var(--border-color)' }}>
                      <td style={{ padding: '1rem', fontWeight: '600' }}>{m.subject_name}</td>
                      <td style={{ padding: '1rem', color: 'var(--text-muted)' }}>{m.assessment_name}</td>
                      <td style={{ padding: '1rem' }}><span style={{ fontWeight: '700' }}>{Number(m.marks_obtained).toFixed(1)}</span><span style={{ color: 'var(--text-muted)', marginLeft: '0.3rem' }}>/ {Number(m.max_marks).toFixed(0)}</span></td>
                      <td style={{ padding: '1rem' }}><span className={`badge ${m.performance_status === 'Below Threshold' ? 'badge-danger' : 'badge-success'}`}>{m.performance_status}</span></td>
                    </tr>
                  ))}
              </tbody>
            </table>
          </div>
        </div>

        {/* Topic Mastery */}
        <div className="glass-panel" style={{ overflow: 'hidden', background: 'var(--surface-solid)' }}>
          <div style={{ padding: '1.5rem', borderBottom: '1px solid var(--border-color)', background: 'linear-gradient(135deg,rgba(0,96,156,0.06) 0%,rgba(0,33,71,0.04) 100%)', display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
            <BookOpen color="var(--primary)" />
            <div>
              <h2 className="font-bold" style={{ margin: 0 }}>Topic Mastery (AI Prediction)</h2>
              <p style={{ margin: 0, fontSize: '0.8rem', color: 'var(--text-muted)' }}>Click a subject to see per-topic proficiency powered by AI</p>
            </div>
          </div>
          <div style={{ padding: '1.5rem' }}>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(160px, 1fr))', gap: '0.75rem', marginBottom: '1rem' }}>
              {SYLLABUS_SUBJECTS.map(subj => (
                <button key={subj} onClick={() => setExpandedSubject(expandedSubject === subj ? null : subj)}
                  style={{ padding: '0.85rem 1rem', borderRadius: '0.75rem', border: `2px solid ${expandedSubject === subj ? 'var(--vignan-blue)' : 'var(--border-color)'}`, background: expandedSubject === subj ? 'rgba(0,96,156,0.08)' : 'white', cursor: 'pointer', fontWeight: '700', fontSize: '0.9rem', color: expandedSubject === subj ? 'var(--vignan-blue)' : 'inherit', display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: '0.5rem', transition: 'all 0.2s', fontFamily: 'inherit' }}>
                  {subj}
                  {expandedSubject === subj ? <ChevronUp size={15} /> : <ChevronDown size={15} />}
                </button>
              ))}
            </div>
            {expandedSubject && (
              <div className="animate-fade-in" style={{ borderTop: '1px solid var(--border-color)', paddingTop: '1rem' }}>
                <TopicMastery registrationNumber={id} subjectCode={expandedSubject} subjectLabel={expandedSubject} />
              </div>
            )}
            {!expandedSubject && <p style={{ textAlign: 'center', color: 'var(--text-muted)', fontSize: '0.85rem', padding: '1rem 0' }}>Select a subject above to view AI-powered topic mastery predictions.</p>}
          </div>
        </div>
      </div>
    </div>
  );
}
