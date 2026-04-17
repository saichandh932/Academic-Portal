import { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import axios from 'axios';
import { 
  Users, 
  BookOpen, 
  GraduationCap, 
  ClipboardList, 
  Activity, 
  LogOut, 
  User, 
  Calendar,
  CheckCircle2,
  AlertCircle,
  FileText,
  Printer,
  ChevronRight
} from 'lucide-react';
import Loader from '../components/Loader';

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
      <header className="vignan-nav" style={{ justifyContent: 'space-between', padding: '0 3rem', background: 'var(--vignan-navy)', border: 'none' }}>
        <div className="flex items-center gap-4">
           <img src="/vignan_logo.png" alt="Vignan logo" style={{ height: '50px', filter: 'brightness(0) invert(1)' }} />
           <div style={{ height: '30px', width: '1px', background: 'rgba(255,255,255,0.2)', margin: '0 1rem' }}></div>
           <h2 style={{ margin: 0, color: 'white', fontSize: '1.2rem', fontWeight: '800', letterSpacing: '1px' }}>PARENT PORTAL</h2>
        </div>
        <button 
          className="btn" 
          onClick={() => { sessionStorage.clear(); navigate("/"); }}
          style={{ background: 'rgba(255,255,255,0.1)', color: 'white', border: '1px solid rgba(255,255,255,0.2)', borderRadius: '2rem', padding: '0.6rem 1.2rem' }}
        >
          <LogOut size={16} style={{ marginRight: '0.6rem' }} /> Logout
        </button>
      </header>

      {/* Hero / Quick Stats */}
      <div style={{ 
        background: 'linear-gradient(135deg, var(--vignan-navy) 0%, var(--vignan-blue) 100%)', 
        padding: '3rem 3rem 6rem',
        color: 'white',
        position: 'relative',
        overflow: 'hidden'
      }}>
        <div style={{ position: 'relative', zIndex: 2, display: 'flex', justifyContent: 'space-between', alignItems: 'flex-end', flexWrap: 'wrap', gap: '2rem' }}>
          <div className="flex items-center gap-6">
            <div style={{ 
              width: '120px', 
              height: '120px', 
              borderRadius: '1rem', 
              background: 'white', 
              padding: '0.5rem',
              boxShadow: '0 10px 25px rgba(0,0,0,0.2)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center'
            }}>
              <img src={student?.photo_url || "/placeholder_student.png"} alt="Student" style={{ width: '100%', height: '100%', objectFit: 'cover', borderRadius: '0.8rem' }} />
            </div>
            <div>
              <h1 style={{ fontSize: '2.5rem', fontWeight: '800', margin: 0 }}>{student?.name || 'Academic Record'}</h1>
              <p style={{ opacity: 0.8, fontSize: '1.1rem', marginTop: '0.5rem' }}>
                <Users size={18} style={{ display: 'inline', marginRight: '0.5rem' }} />
                Reg No: <b style={{ letterSpacing: '1px' }}>{id}</b> | Batch {student?.batch || '2023-27'}
              </p>
            </div>
          </div>

          <div className="flex gap-4">
             <div className="glass-panel" style={{ background: 'rgba(255,255,255,0.1)', border: '1px solid rgba(255,255,255,0.2)', padding: '1.2rem 2rem', textAlign: 'center' }}>
                <p style={{ fontSize: '0.8rem', textTransform: 'uppercase', letterSpacing: '1px', marginBottom: '0.4rem', opacity: 0.8 }}>Overall Attendance</p>
                <h3 style={{ fontSize: '2rem', fontWeight: '900', margin: 0, color: 'white' }}>{overallAttendance}%</h3>
             </div>
             <div className="glass-panel" style={{ background: 'rgba(255,255,255,0.1)', border: '1px solid rgba(255,255,255,0.2)', padding: '1.2rem 2rem', textAlign: 'center' }}>
                <p style={{ fontSize: '0.8rem', textTransform: 'uppercase', letterSpacing: '1px', marginBottom: '0.4rem', opacity: 0.8 }}>Academic Standing</p>
                <h3 style={{ fontSize: '2rem', fontWeight: '900', margin: 0, color: student?.performance === 'Low' ? '#ff6b6b' : '#51cf66' }}>
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
            
            <div style={{ overflowX: 'auto' }}>
              <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'center' }}>
                <thead>
                  <tr style={{ background: 'var(--vignan-light)', borderBottom: '2px solid #ddd' }}>
                    <th style={{ padding: '1.2rem', textAlign: 'left', minWidth: '250px', background: '#fcfcfc', color: '#666', borderRight: '1px solid #eee' }}>Assessment Name</th>
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

        <div className="grid gap-8" style={{ gridTemplateColumns: 'repeat(auto-fit, minmax(450px, 1fr))' }}>
          
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
                
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1.5rem' }}>
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
