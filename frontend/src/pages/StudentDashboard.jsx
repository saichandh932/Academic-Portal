import { useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';
import axios from 'axios';
import { AlertCircle, CheckCircle2, BookOpen, GraduationCap, ClipboardList, Activity, LogOut, User } from 'lucide-react';
import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip } from 'recharts';
import { useNavigate } from 'react-router-dom';
import Loader from '../components/Loader';

export default function StudentDashboard() {
  const { id } = useParams();
  const [marks, setMarks] = useState([]);
  const [attendance, setAttendance] = useState([]);
  const [studentProfile, setStudentProfile] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const navigate = useNavigate();

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

        if (studentRes.data && studentRes.data.success) {
          setStudentProfile(studentRes.data.student);
        }
        setMarks(marksRes.data.marks || []);
        setAttendance(attnRes.data.summary || []);
      } catch (err) {
        console.error("Student Fetch Error:", err);
        setError('Failed to load dashboard data. Ensure backend is running.');
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, [id]);

  if (loading) return <Loader text="Loading student record..." />;
  if (error) return <div className="container mt-4 text-center" style={{color: 'var(--danger)'}}>{error}</div>;

  const belowThresholdMarks = marks.filter(m => m.performance_status === 'Below Threshold');

  return (
    <div className="container animate-fade-in" style={{ paddingBottom: '4rem' }}>
      <div style={{ marginBottom: '2.5rem', display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
        <div>
          <h1 className="font-bold text-xl" style={{ fontSize: '2.5rem', marginBottom: '0.5rem' }}>
            Performance Panel
          </h1>
          <p style={{ color: 'var(--text-muted)' }}>Registration Number: <b style={{ fontFamily: 'monospace', background: 'rgba(0,33,71,0.05)', padding: '0.2rem 0.6rem', borderRadius: '4px', color: 'var(--vignan-blue)' }}>{id}</b></p>
        </div>
        <button 
          className="btn btn-outline" 
          onClick={() => {
            sessionStorage.clear();
            navigate('/', { replace: true });
          }} 
          style={{ borderColor: 'var(--danger)', color: 'var(--danger)', display: 'flex', alignItems: 'center', gap: '0.5rem' }}
        >
          <LogOut size={16} /> Logout
        </button>
      </div>

      <div className="grid gap-8">
        
        {/* Student Profile Card */}
        {studentProfile && (
          <div className="glass-panel" style={{ background: 'var(--surface-solid)', padding: '2rem', marginBottom: '1rem', display: 'flex', gap: '2rem', alignItems: 'center', flexWrap: 'wrap' }}>
            
            {/* Profile Photo Section */}
            <div style={{ 
              width: '180px', 
              height: '180px', 
              borderRadius: '50%', 
              background: 'linear-gradient(135deg, var(--bg-color) 0%, #e2e8f0 100%)',
              border: '4px solid white',
              boxShadow: '0 4px 20px rgba(0,0,0,0.08)',
              overflow: 'hidden',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              flexShrink: 0
            }}>
              {/* Note for User: Replace 'PHOTO_BASE_URL' with your GitHub link later */}
              {studentProfile.photo_url ? (
                <img 
                  src={studentProfile.photo_url} 
                  alt={studentProfile.name}
                  style={{ width: '100%', height: '100%', objectFit: 'cover' }}
                  onError={(e) => { e.target.style.display = 'none'; e.target.nextSibling.style.display = 'flex'; }}
                />
              ) : null}
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', width: '100%', height: '100%' }}>
                <User size={80} color="var(--text-muted)" style={{ opacity: 0.4 }} />
              </div>
            </div>

            <div style={{ flex: 1, minWidth: '300px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '1.5rem', borderBottom: '1px solid var(--border-color)', paddingBottom: '1rem' }}>
                <Activity color="var(--primary)" size={20} />
                <h2 className="font-bold" style={{ margin: 0, fontSize: '1.4rem' }}>Institutional Identity</h2>
              </div>
              
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(200px, 1fr))', gap: '1.2rem' }}>
                <div>
                  <div style={{ fontSize: '0.7rem', fontWeight: '800', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.5px' }}>Full Name</div>
                  <div style={{ fontSize: '1.1rem', fontWeight: '800', color: 'var(--primary)' }}>{studentProfile.name || 'N/A'}</div>
                </div>
                <div>
                  <div style={{ fontSize: '0.7rem', fontWeight: '800', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.5px' }}>Course & Branch</div>
                  <div style={{ fontSize: '1rem', fontWeight: '600' }}>{studentProfile.course} | {studentProfile.branch}</div>
                </div>
                <div>
                  <div style={{ fontSize: '0.7rem', fontWeight: '800', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.5px' }}>Academic Batch</div>
                  <div style={{ fontSize: '1rem', fontWeight: '600' }}>Year {studentProfile.year} (Sem {studentProfile.semester}) - Section {studentProfile.section}</div>
                </div>
                <div>
                  <div style={{ fontSize: '0.7rem', fontWeight: '800', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.5px' }}>Gender</div>
                  <div style={{ fontSize: '1rem', fontWeight: '600' }}>{studentProfile.gender || 'N/A'}</div>
                </div>
                <div>
                  <div style={{ fontSize: '0.7rem', fontWeight: '800', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.5px' }}>Date of Birth</div>
                  <div style={{ fontSize: '1rem', fontWeight: '600' }}>{studentProfile.dob ? new Date(studentProfile.dob).toLocaleDateString() : 'N/A'}</div>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Status Highlights */}
        <div className="stat-grid">
          <div className="glass-panel card">
             <div className="flex items-center gap-2" style={{ color: 'var(--text-muted)', marginBottom: '0.5rem' }}>
               <GraduationCap size={18} />
               <span style={{ fontSize: '0.8rem', fontWeight: '600', textTransform: 'uppercase' }}>Total Assessments</span>
             </div>
             <div className="card-value">{marks.length}</div>
          </div>

          <div className="glass-panel card" style={{ 
            borderLeft: `4px solid ${belowThresholdMarks.length > 0 ? 'var(--danger)' : 'var(--success)'}`,
            background: 'var(--surface-solid)'
          }}>
             <div className="flex items-center gap-2" style={{ color: 'var(--text-muted)', marginBottom: '0.5rem' }}>
               {belowThresholdMarks.length > 0 ? <AlertCircle size={18} color="var(--danger)" /> : <CheckCircle2 size={18} color="var(--success)" />}
               <span style={{ fontSize: '0.8rem', fontWeight: '600', textTransform: 'uppercase' }}>Status Overview</span>
             </div>
             <div className="card-value" style={{ fontSize: '1.5rem', color: belowThresholdMarks.length > 0 ? 'var(--danger)' : 'var(--success)' }}>
                {belowThresholdMarks.length > 0 
                  ? `${belowThresholdMarks.length} Critical Flags` 
                  : 'All Performance Good'}
             </div>
          </div>

          {/* New Attendance Round Chart */}
          <div className="glass-panel card" style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', position: 'relative' }}>
             <div style={{ width: '100%', height: '140px', position: 'relative' }}>
                <ResponsiveContainer width="100%" height="100%">
                    <PieChart>
                        <Pie 
                            data={[
                                { name: 'Present', value: attendance.reduce((acc, s) => acc + s.present_count, 0) },
                                { name: 'Absent', value: attendance.reduce((acc, s) => acc + (s.total_classes - s.present_count), 0) }
                            ]} 
                            cx="50%" cy="50%" innerRadius={45} outerRadius={60} startAngle={90} endAngle={450} dataKey="value" stroke="none"
                        >
                            <Cell fill="var(--primary)" />
                            <Cell fill="rgba(0,0,0,0.05)" />
                        </Pie>
                    </PieChart>
                </ResponsiveContainer>
                <div style={{ position: 'absolute', top: '50%', left: '50%', transform: 'translate(-50%, -50%)', textAlign: 'center' }}>
                    <div style={{ fontSize: '1.4rem', fontWeight: '900' }}>
                        {attendance.length > 0 
                          ? (attendance.reduce((acc, s) => acc + s.percentage, 0) / attendance.length).toFixed(1) 
                          : "0"}%
                    </div>
                </div>
             </div>
             <div style={{ paddingLeft: '1rem' }}>
                <div style={{ fontSize: '0.75rem', fontWeight: '800', color: 'var(--text-muted)' }}>OVERALL ATTENDANCE</div>
                <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>Across All Subjects</div>
             </div>
          </div>
        </div>

        {/* Attendance Breakdown */}
        <div className="glass-panel" style={{ overflow: 'hidden', background: 'var(--surface-solid)' }}>
          <div style={{ padding: '1.5rem', borderBottom: '1px solid var(--border-color)', background: 'rgba(0, 96, 156, 0.05)', display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
            <Activity color="var(--primary)" />
            <h2 className="font-bold" style={{ margin: 0 }}>Subject-wise Attendance</h2>
          </div>
          <div style={{ padding: '1.5rem' }}>
            {attendance.length === 0 ? (
              <p style={{ textAlign: 'center', color: 'var(--text-muted)' }}>No attendance records found.</p>
            ) : (
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

        {/* Gradebook Table */}
        <div className="glass-panel" style={{ overflow: 'hidden', background: 'var(--surface-solid)' }}>
          <div style={{ padding: '1.5rem', borderBottom: '1px solid var(--border-color)', background: 'rgba(0,0,0,0.02)', display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
            <ClipboardList color="var(--primary)" />
            <h2 className="font-bold" style={{ margin: 0 }}>Academic Gradebook</h2>
          </div>
          
          <div style={{ overflowX: 'auto' }}>
            <table className="w-full" style={{ borderCollapse: 'collapse', textAlign: 'left' }}>
              <thead style={{ background: 'rgba(0,0,0,0.03)', color: 'var(--text-muted)' }}>
                <tr>
                  <th style={{ padding: '1rem', fontSize: '0.85rem' }}>Subject</th>
                  <th style={{ padding: '1rem', fontSize: '0.85rem' }}>Assessment</th>
                  <th style={{ padding: '1rem', fontSize: '0.85rem' }}>Marks Obtained</th>
                  <th style={{ padding: '1rem', fontSize: '0.85rem' }}>Status</th>
                </tr>
              </thead>
              <tbody style={{ borderTop: '1px solid var(--border-color)' }}>
                {marks.length === 0 ? (
                  <tr>
                    <td colSpan="4" style={{ padding: '3rem', textAlign: 'center', color: 'var(--text-muted)' }}>No grades recorded yet.</td>
                  </tr>
                ) : (
                  marks.map((m, idx) => (
                    <tr key={idx} style={{ borderBottom: '1px solid var(--border-color)' }}>
                      <td style={{ padding: '1rem', fontWeight: '600' }}>{m.subject_name}</td>
                      <td style={{ padding: '1rem', color: 'var(--text-muted)' }}>{m.assessment_name}</td>
                      <td style={{ padding: '1rem' }}>
                        <span style={{ fontWeight: '700' }}>{Number(m.marks_obtained).toFixed(1)}</span>
                        <span style={{ color: 'var(--text-muted)', marginLeft: '0.3rem' }}>/ {Number(m.max_marks).toFixed(0)}</span>
                      </td>
                      <td style={{ padding: '1rem' }}>
                        <span className={`badge ${m.performance_status === 'Below Threshold' ? 'badge-danger' : 'badge-success'}`}>
                          {m.performance_status}
                        </span>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>

      </div>
    </div>
  );
}
