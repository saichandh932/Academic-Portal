import { useEffect, useState } from 'react';
import axios from 'axios';
import {
  RadarChart, Radar, PolarGrid, PolarAngleAxis, PolarRadiusAxis,
  ResponsiveContainer, PieChart, Pie, Cell, Tooltip
} from 'recharts';

const STATUS_COLOR = {
  strong:      '#22c55e',
  moderate:    '#f59e0b',
  needs_focus: '#ef4444',
  no_data:     '#cbd5e1',
};
const STATUS_LABEL = {
  strong:      '✅ Strong',
  moderate:    '⚠️ Moderate',
  needs_focus: '🔴 Needs Focus',
  no_data:     '⬜ No Data',
};

function DonutCard({ topic, mastery, status, marksObtained, marksAllotted }) {
  const pct = mastery ?? 0;
  const data = [
    { name: 'Mastery', value: pct },
    { name: 'Gap',     value: Math.max(0, 100 - pct) },
  ];
  const color = STATUS_COLOR[status] || '#cbd5e1';

  return (
    <div style={{
      background: 'white',
      borderRadius: '1rem',
      padding: '1.2rem',
      boxShadow: '0 2px 12px rgba(0,0,0,0.06)',
      border: `2px solid ${color}22`,
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      gap: '0.4rem',
      transition: 'transform 0.2s',
    }}
      onMouseEnter={e => e.currentTarget.style.transform = 'translateY(-3px)'}
      onMouseLeave={e => e.currentTarget.style.transform = 'translateY(0)'}
    >
      <div style={{ width: 100, height: 100, position: 'relative' }}>
        <ResponsiveContainer width="100%" height="100%">
          <PieChart>
            <Pie data={data} cx="50%" cy="50%" innerRadius={30} outerRadius={46}
              startAngle={90} endAngle={-270} dataKey="value" stroke="none">
              <Cell fill={color} />
              <Cell fill="#f1f5f9" />
            </Pie>
          </PieChart>
        </ResponsiveContainer>
        <div style={{
          position: 'absolute', top: '50%', left: '50%',
          transform: 'translate(-50%, -50%)', textAlign: 'center',
        }}>
          <div style={{ fontSize: '1rem', fontWeight: '900', color }}>
            {mastery !== null ? `${pct}%` : '—'}
          </div>
        </div>
      </div>
      <div style={{ textAlign: 'center' }}>
        <div style={{ fontSize: '0.72rem', fontWeight: '700', color: '#64748b' }}>
          {STATUS_LABEL[status]}
        </div>
        {/* Show actual marks breakdown */}
        {marksAllotted > 0 && (
          <div style={{ fontSize: '0.7rem', color: '#94a3b8', marginTop: '0.15rem' }}>
            {marksObtained.toFixed(1)} / {marksAllotted.toFixed(1)} marks
          </div>
        )}
        <div style={{ fontSize: '0.78rem', fontWeight: '600', marginTop: '0.2rem', maxWidth: '130px', lineHeight: 1.3 }}>
          {topic}
        </div>
      </div>
    </div>
  );
}

export default function TopicMastery({ registrationNumber, subjectCode, subjectLabel }) {
  const [data, setData]     = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError]   = useState('');

  useEffect(() => {
    if (!registrationNumber || !subjectCode) return;
    setLoading(true);
    setError('');
    axios.get(`/api/syllabus/mastery/${registrationNumber}/${subjectCode}`)
      .then(res => {
        if (res.data.success) setData(res.data);
        else setError(res.data.error || 'Failed to load mastery data.');
      })
      .catch(() => setError('Could not fetch topic mastery data.'))
      .finally(() => setLoading(false));
  }, [registrationNumber, subjectCode]);

  if (loading) return (
    <div style={{ padding: '2rem', textAlign: 'center', color: 'var(--text-muted)', fontSize: '0.9rem' }}>
      ⏳ Computing topic mastery...
    </div>
  );

  if (error) return (
    <div style={{ padding: '1rem', color: '#94a3b8', fontSize: '0.85rem', textAlign: 'center' }}>
      {error}
    </div>
  );

  if (!data) return null;

  // No topic-tagged assessments have been submitted yet
  if (data.tagged_records === 0) {
    return (
      <div style={{ padding: '2rem', textAlign: 'center' }}>
        <div style={{ fontSize: '2.5rem', marginBottom: '0.75rem' }}>📋</div>
        <h3 style={{ margin: '0 0 0.5rem', fontWeight: '800', color: 'var(--vignan-blue)' }}>
          No Topic Data Yet
        </h3>
        <p style={{ color: '#64748b', fontSize: '0.9rem', maxWidth: '400px', margin: '0 auto 0.75rem' }}>
          Topic mastery predictions will appear here once your faculty submits assessments with specific topics selected.
        </p>
        <div style={{ display: 'inline-block', padding: '0.5rem 1rem', background: 'rgba(0,96,156,0.07)', borderRadius: '0.5rem', fontSize: '0.8rem', color: 'var(--vignan-blue)', fontWeight: '600' }}>
          {data.total_marks_records > 0
            ? `${data.total_marks_records} assessment record${data.total_marks_records !== 1 ? 's' : ''} found — none have topics tagged yet.`
            : 'No assessments recorded for this subject yet.'}
        </div>
      </div>
    );
  }

  const topicEntries = Object.entries(data.topics || {});

  // Radar data (only topics with data)
  const radarData = topicEntries
    .filter(([, v]) => v.mastery_pct !== null)
    .map(([topic, v]) => ({
      topic: topic.length > 22 ? topic.slice(0, 21) + '…' : topic,
      fullTopic: topic,
      mastery: v.mastery_pct,
    }));

  const overallColor =
    data.overall_mastery === null ? '#94a3b8'
    : data.overall_mastery >= 75  ? '#22c55e'
    : data.overall_mastery >= 50  ? '#f59e0b'
    : '#ef4444';

  return (
    <div style={{ padding: '1.5rem 0 0.5rem' }}>
      {/* Header */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '0.5rem', marginBottom: '1.5rem' }}>
        <div>
          <h3 style={{ margin: 0, fontSize: '1rem', fontWeight: '800' }}>
            📊 Topic Mastery — {data.subject_name}
          </h3>
          <p style={{ margin: '0.25rem 0 0', fontSize: '0.78rem', color: '#64748b' }}>
            Based on {data.tagged_records} topic-tagged assessment{data.tagged_records !== 1 ? 's' : ''} ({data.total_marks_records} total records)
          </p>
        </div>
        <div style={{
          padding: '0.4rem 1rem', borderRadius: '2rem',
          background: `${overallColor}18`, color: overallColor,
          fontWeight: '800', fontSize: '0.9rem', border: `1px solid ${overallColor}44`
        }}>
          Overall: {data.overall_mastery !== null ? `${data.overall_mastery}%` : 'No Data'}
        </div>
      </div>

      {/* Radar Chart */}
      {radarData.length >= 3 && (
        <div style={{ marginBottom: '2rem', background: 'rgba(0,96,156,0.03)', borderRadius: '1rem', padding: '1rem' }}>
          <p style={{ fontSize: '0.75rem', fontWeight: '700', color: '#94a3b8', textTransform: 'uppercase', letterSpacing: '0.5px', margin: '0 0 0.75rem' }}>
            Subject Overview (Radar)
          </p>
          <div style={{ width: '100%', height: 280 }}>
            <ResponsiveContainer>
              <RadarChart data={radarData} margin={{ top: 10, right: 30, bottom: 10, left: 30 }}>
                <PolarGrid stroke="#e2e8f0" />
                <PolarAngleAxis dataKey="topic" tick={{ fontSize: 10, fill: '#64748b' }} />
                <PolarRadiusAxis angle={30} domain={[0, 100]} tick={{ fontSize: 9 }} tickCount={4} />
                <Radar name="Mastery" dataKey="mastery" stroke="#0060a0" fill="#0060a0" fillOpacity={0.25} strokeWidth={2} />
                <Tooltip
                  formatter={(val, _name, props) => [`${val}%`, props.payload.fullTopic || 'Mastery']}
                  contentStyle={{ borderRadius: '0.5rem', fontSize: '0.8rem' }}
                />
              </RadarChart>
            </ResponsiveContainer>
          </div>
        </div>
      )}

      {/* Doughnut Cards Grid */}
      <p style={{ fontSize: '0.75rem', fontWeight: '700', color: '#94a3b8', textTransform: 'uppercase', letterSpacing: '0.5px', margin: '0 0 0.75rem' }}>
        Per-Topic Breakdown
      </p>
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fill, minmax(150px, 1fr))',
        gap: '1rem',
      }}>
        {topicEntries.map(([topic, v]) => (
          <DonutCard
            key={topic}
            topic={topic}
            mastery={v.mastery_pct}
            status={v.status}
            marksObtained={v.marks_obtained ?? 0}
            marksAllotted={v.marks_allotted ?? 0}
          />
        ))}
      </div>

      {/* Legend */}
      <div style={{ display: 'flex', gap: '1rem', flexWrap: 'wrap', marginTop: '1.25rem' }}>
        {Object.entries(STATUS_LABEL).map(([k, label]) => (
          <span key={k} style={{ display: 'flex', alignItems: 'center', gap: '0.35rem', fontSize: '0.75rem', color: '#64748b' }}>
            <span style={{ width: 10, height: 10, borderRadius: '50%', background: STATUS_COLOR[k], display: 'inline-block' }} />
            {label}
          </span>
        ))}
      </div>
    </div>
  );
}
