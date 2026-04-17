import React, { useState, useEffect } from "react";
import axios from "axios";
import { UserCheck, UserX, Calendar, Save, CheckCircle, ShieldCheck } from "lucide-react";

export default function AttendanceUpload({ subject, onUploadSuccess }) {
  const [students, setStudents] = useState([]);
  const [absentIds, setAbsentIds] = useState(new Set());
  const [date, setDate] = useState(new Date().toISOString().split('T')[0]);
  const [period, setPeriod] = useState(1);
  const [isVerified, setIsVerified] = useState(false);
  const [lockedBy, setLockedBy] = useState(""); // Which subject locked it
  const [lockedSlots, setLockedSlots] = useState([]); // List of {date, period}
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");

  const isLocked = lockedSlots.some(s => s.date === date && s.period === parseInt(period));

  useEffect(() => {
    // 1. Initial students fetch
    if (students.length === 0) fetchStudents();
    
    // 2. Clear status
    setAbsentIds(new Set());
    setIsVerified(false);
    setMessage("");
    setError("");

    // 3. Sync locks and existing data
    fetchLocks();
    fetchExistingAttendance();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [date, subject, period]);

  const fetchLocks = async () => {
    try {
      const res = await axios.get(`/api/db/attendance/locks?subject=${subject}`);
      setLockedSlots(res.data.locked_slots || []);
    } catch (err) {
      console.error("Failed to fetch locks:", err);
    }
  };

  const fetchStudents = async () => {
    try {
      const res = await axios.get("/api/db/students");
      setStudents(res.data.students || []);
      } catch {
        setError("Failed to fetch students.");
      }
  };

  const fetchExistingAttendance = async () => {
    try {
      setLoading(true);
      const res = await axios.get(`/api/db/attendance?subject=${subject}&date=${date}&period=${period}`);
      const dailyRecords = res.data.records || [];
      
      const newAbsents = new Set();
      if (dailyRecords.length > 0) {
          setLockedBy(dailyRecords[0]._locked_by || "");
          dailyRecords.forEach(r => {
            if (r.status === 'Absent') newAbsents.add(r.registration_number);
          });
          setAbsentIds(newAbsents);
          setIsVerified(true);
      } else {
          setLockedBy("");
      }
    } catch (err) {
      console.error("Existing attendance fetch error:", err);
    } finally {
      setLoading(false);
    }
  };

  const toggleAttendance = (regId) => {
    if (isLocked) return; // Prevent edits if locked
    const newAbsents = new Set(absentIds);
    if (newAbsents.has(regId)) {
      newAbsents.delete(regId);
    } else {
      newAbsents.add(regId);
    }
    setAbsentIds(newAbsents);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setMessage("");
    setError("");

    const records = students.map(s => ({
      registration_number: s.registration_number,
      status: absentIds.has(s.registration_number) ? 'Absent' : 'Present'
    }));

    try {
      const payload = {
        subject_name: subject,
        date: date,
        period: period,
        records: records
      };

      const res = await axios.post("/api/db/attendance/upload", payload);
      setMessage(res.data.message);
      
      // SHOW DETAILED SUCCESS POPUP
      const notifiedIDs = res.data.alerted_students || [];
      if (notifiedIDs.length > 0) {
          const idsString = notifiedIDs.length > 5 
            ? notifiedIDs.slice(0, 5).join(', ') + ` and ${notifiedIDs.length - 5} more`
            : notifiedIDs.join(', ');
            
          alert(
            `✅ ATTENDANCE FINALIZED & EMAILS DISPATCHED\n` +
            `------------------------------------------\n\n` +
            `📧 Emails sent to: ${idsString}\n\n` +
            `📄 Message Sent Preview:\n` +
            `"Hello Student, this is an automated notification regarding your attendance in ${subject} on ${date}. Status: ABSENT. Please maintain required attendance."\n\n` +
            `This record is now permanently locked.`
          );
      } else {
          alert(`✅ Attendance Finalized Successfully!\n\nNo absence alerts were triggered.`);
      }

      // Refresh locks so the UI updates to locked state
      fetchLocks();
      if (onUploadSuccess) onUploadSuccess();
    } catch (err) {
      setError(err.response?.data?.error || "Connection error to Attendance API.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="glass-panel" style={{ padding: '2rem', marginTop: '2rem' }}>
      <div style={{ marginBottom: '1.5rem', display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '1rem' }}>
        <div>
          <h2 className="font-bold text-xl">Attendance Registry: {subject}</h2>
          <div className="flex items-center gap-2 mt-1 flex-wrap">
              <p style={{ color: 'var(--text-muted)', margin: 0, fontSize: '0.9rem' }}>
                {isLocked ? (lockedBy ? `Finalized by ${lockedBy}. Records are immutable.` : "Records for this slot are finalized.") : "Tick the checkbox to mark a student as Absent."}
              </p>
             {isLocked ? (
                <span className="badge" style={{ background: 'var(--danger)', color: 'white', padding: '0.5rem 1rem', fontSize: '0.8rem', display: 'flex', alignItems: 'center', gap: '6px', fontWeight: '900', borderRadius: '30px' }}>
                   🔒 <span className="hide-on-mobile">PERMANENTLY</span> FINALIZED
                </span>
             ) : isVerified ? (
                <span className="badge badge-success" style={{ fontSize: '0.65rem', display: 'flex', alignItems: 'center', gap: '4px' }}>
                   <CheckCircle size={10} /> VERIFIED
                </span>
             ) : (
                <span className="badge" style={{ background: 'rgba(79, 70, 229, 0.1)', color: 'var(--primary)', fontSize: '0.65rem' }}>
                   NEW ENTRY
                </span>
             )}
          </div>
        </div>
        <div className="flex items-center gap-3 flex-wrap">
            <div className="flex items-center gap-2">
                <span style={{ fontSize: '0.8rem', fontWeight: '700', color: 'var(--text-muted)' }}>PERIOD:</span>
                <select 
                    className="form-input"
                    style={{ width: '80px', height: '38px', fontSize: '0.9rem' }}
                    value={period}
                    onChange={(e) => setPeriod(parseInt(e.target.value))}
                >
                    {[1,2,3,4,5,6,7,8].map(p => <option key={p} value={p}>P{p}</option>)}
                </select>
            </div>
            <div className="flex items-center gap-2">
                <Calendar size={18} color="var(--primary)" />
                <input 
                  type="date" 
                  className="form-input" 
                  style={{ width: '150px', height: '38px', fontSize: '0.9rem' }}
                  value={date}
                  onChange={(e) => setDate(e.target.value)}
                />
            </div>
        </div>
      </div>

      {error && <div style={{ color: 'var(--danger)', padding: '1rem', background: 'rgba(227, 30, 36, 0.05)', borderRadius: '0.5rem', marginBottom: '1rem', border: '1px solid rgba(227, 30, 36, 0.1)' }}>{error}</div>}
      {message && <div style={{ color: 'var(--vignan-blue)', padding: '1rem', background: 'rgba(0, 96, 156, 0.08)', borderRadius: '0.5rem', marginBottom: '1rem', border: '1px solid rgba(0, 96, 156, 0.1)' }}>{message}</div>}

      <div style={{ maxHeight: '500px', overflowY: 'auto', background: 'rgba(0,0,0,0.02)', padding: '1.5rem', borderRadius: '1rem', border: '1px solid var(--border-color)' }}>
         {loading ? (
             <div className="flex flex-col items-center justify-center py-10">
                 <div className="animate-spin" style={{ width: '30px', height: '30px', border: '3px solid var(--primary)', borderTopColor: 'transparent', borderRadius: '50%' }}></div>
                 <p style={{ marginTop: '1rem', color: 'var(--text-muted)', fontSize: '0.9rem' }}>Finalizing Records...</p>
             </div>
         ) : isLocked ? (
            <div className="animate-fade-in" style={{ textAlign: 'center', padding: '2rem' }}>
                <div style={{ marginBottom: '1.5rem' }}>
                    <div style={{ display: 'inline-flex', padding: '1rem', background: 'rgba(0, 96, 156, 0.1)', borderRadius: '50%', color: 'var(--vignan-blue)', marginBottom: '1rem' }}>
                        <ShieldCheck size={32} />
                    </div>
                    <h3 style={{ fontSize: '1.4rem', fontWeight: '900', margin: 0, color: 'var(--primary)' }}>ATTENDANCE IS ALREADY MARKED</h3>
                    <p style={{ color: 'var(--text-muted)', fontSize: '0.95rem', marginTop: '0.5rem' }}>Below is the official record for {date} (Period {period}).</p>
                </div>
                
                <div style={{ marginTop: '2rem' }}>
                    {absentIds.size > 0 ? (
                        <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.8rem', justifyContent: 'center' }}>
                            {[...absentIds].map(id => (
                                <div key={id} style={{ padding: '0.6rem 1.2rem', background: 'var(--surface-solid)', border: '2px solid var(--vignan-red)', borderRadius: '8px', color: 'var(--vignan-red)', fontWeight: '800', fontSize: '1.1rem', fontFamily: 'monospace' }}>
                                    {id}
                                </div>
                            ))}
                        </div>
                    ) : (
                        <div style={{ padding: '2rem', background: 'rgba(5, 150, 105, 0.05)', borderRadius: '12px', color: 'var(--success)', fontWeight: '700' }}>
                           ✅ ALL STUDENTS WERE PRESENT
                        </div>
                    )}
                </div>
                
                <div style={{ marginTop: '2.5rem', paddingTop: '2rem', borderTop: '1px solid var(--border-color)', color: 'var(--text-muted)', fontSize: '0.8rem' }}>
                    <ShieldCheck size={14} style={{ verticalAlign: 'middle', marginRight: '4px' }} /> 
                    THIS RECORD WAS PERMANENTLY FINALIZED ON {new Date().toLocaleDateString()}
                </div>
            </div>
         ) : (
            <div className="grid" style={{ gridTemplateColumns: 'repeat(auto-fill, minmax(clamp(200px, 100%, 300px), 1fr))', gap: '1rem' }}>
               {students.map((student) => {
                  const isAbsent = absentIds.has(student.registration_number);
                  return (
                     <div 
                       key={student.registration_number} 
                       onClick={() => toggleAttendance(student.registration_number)}
                       className="flex justify-between items-center" 
                       style={{ 
                           padding: '1rem', 
                           background: isAbsent ? 'rgba(227, 30, 36, 0.04)' : 'var(--surface-solid)', 
                           borderRadius: '0.8rem', 
                           border: '1px solid',
                           borderColor: isAbsent ? 'var(--danger)' : 'var(--border-color)',
                           cursor: 'pointer',
                           transition: 'all 0.2s'
                       }}
                     >
                        <div className="flex items-center gap-3">
                            <div style={{ 
                                width: '20px', 
                                height: '20px', 
                                border: '2px solid', 
                                borderColor: isAbsent ? 'var(--danger)' : 'var(--text-muted)',
                                borderRadius: '4px',
                                background: isAbsent ? 'var(--danger)' : 'transparent',
                                display: 'flex',
                                alignItems: 'center',
                                justifyContent: 'center'
                            }}>
                               {isAbsent && <span style={{ color: 'white', fontSize: '12px' }}>✓</span>}
                            </div>
                            <span style={{ fontFamily: 'monospace', fontWeight: '600', color: isAbsent ? 'var(--danger)' : 'inherit' }}>
                               {student.registration_number}
                            </span>
                        </div>
                        
                        <div className="flex items-center gap-2">
                            {isAbsent ? (
                                <span style={{ color: 'var(--danger)', fontSize: '0.75rem', fontWeight: '700', display: 'flex', alignItems: 'center', gap: '4px' }}>
                                    <UserX size={14} /> ABSENT
                                </span>
                            ) : (
                                <span style={{ color: 'var(--success)', fontSize: '0.75rem', fontWeight: '700', display: 'flex', alignItems: 'center', gap: '4px' }}>
                                    <UserCheck size={14} /> PRESENT
                                </span>
                            )}
                        </div>
                     </div>
                  );
               })}
            </div>
         )}
      </div>

      <div className="flex justify-between items-center mt-6 gap-4" style={{ borderTop: '1px solid var(--border-color)', paddingTop: '1.5rem', flexWrap: 'wrap' }}>
        <div>
            <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem', margin: 0 }}>
              Recording <b>{absentIds.size} absences</b> out of {students.length} students.
            </p>
            {!isLocked && (
                <p className="hide-on-mobile" style={{ color: 'var(--danger)', fontSize: '0.75rem', fontWeight: '800', marginTop: '0.4rem' }}>
                   ⚠️ NOTE: Saving will permanently lock this record.
                </p>
            )}
        </div>
        
        {!isLocked && (
            <button 
              className="btn btn-primary" 
              disabled={loading}
              onClick={handleSubmit}
              style={{ gap: '0.5rem', width: 'auto', minWidth: '180px' }}
            >
              {loading ? "Finalizing..." : (
                <>
                  <Save size={18} /> Mark Attendance
                </>
              )}
            </button>
        )}
      </div>
    </div>
  );
}
