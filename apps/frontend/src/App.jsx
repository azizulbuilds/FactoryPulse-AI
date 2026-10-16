import { useCallback, useEffect, useMemo, useState } from 'react';
import './App.css';

const API_BASE = (import.meta.env.VITE_API_BASE_URL || '').replace(/\/$/, '');
const API_PREFIX = `${API_BASE}/api/v1`;

const sampleMachines = [
  {
    machine_id: 'CNC-MILL-001',
    name: 'CNC Milling Cell 01',
    area: 'Machining · Line A',
    health_score: 100,
    condition: 'healthy',
    open_alerts: 0,
    latest_reading: { process_temperature: 308.2, air_temperature: 298.5, rotational_speed: 1500, torque: 42.3, tool_wear: 100 },
  },
  {
    machine_id: 'PRECISION-LATHE-001',
    name: 'Precision Lathe 01',
    area: 'Machining · Line A',
    health_score: 61,
    condition: 'attention_required',
    open_alerts: 3,
    latest_reading: { process_temperature: 316.2, air_temperature: 298.5, rotational_speed: 1520, torque: 62, tool_wear: 225 },
  },
  {
    machine_id: 'HYDRAULIC-PRESS-001',
    name: 'Hydraulic Press 01',
    area: 'Forming · Line B',
    health_score: 10,
    condition: 'critical',
    open_alerts: 4,
    latest_reading: { process_temperature: 325, air_temperature: 300, rotational_speed: 1100, torque: 72, tool_wear: 260 },
  },
];

const sampleAlerts = [
  { id: 'preview-1', machine_id: 'HYDRAULIC-PRESS-001', severity: 'critical', title: 'Critical process temperature', message: 'The illustrative reading is 325 K and exceeds the configured critical threshold. Review the machine using site procedures.', status: 'open', created_at: new Date(Date.now() - 6 * 60 * 1000).toISOString() },
  { id: 'preview-2', machine_id: 'HYDRAULIC-PRESS-001', severity: 'critical', title: 'Torque above configured limit', message: 'The illustrative torque reading is 72 Nm. Inspect load and tooling using approved procedures.', status: 'open', created_at: new Date(Date.now() - 12 * 60 * 1000).toISOString() },
  { id: 'preview-3', machine_id: 'PRECISION-LATHE-001', severity: 'warning', title: 'Tool wear requires attention', message: 'The illustrative tool-wear reading is elevated. Plan an inspection as appropriate.', status: 'open', created_at: new Date(Date.now() - 24 * 60 * 1000).toISOString() },
];

// Used only when the API is unavailable. This is explicitly labelled as illustrative.
const demoTemperature = [318.0, 319.0, 319.5, 320.0, 321.0, 320.8, 322.0, 322.6, 323.0, 324.0, 323.5, 324.2, 324.8, 324.0, 324.5, 324.4, 325.0, 325.0];

const DEMO_MACHINE_LABELS = {
  'CNC-MILL-001': { name: 'CNC Milling Cell 01', area: 'Machining · Line A' },
  'PRECISION-LATHE-001': { name: 'Precision Lathe 01', area: 'Machining · Line A' },
  'HYDRAULIC-PRESS-001': { name: 'Hydraulic Press 01', area: 'Forming · Line B' },
};

function Icon({ name, size = 19, strokeWidth = 1.8 }) {
  const paths = {
    grid: <><rect x="3" y="3" width="7" height="7" rx="1.5"/><rect x="14" y="3" width="7" height="7" rx="1.5"/><rect x="3" y="14" width="7" height="7" rx="1.5"/><rect x="14" y="14" width="7" height="7" rx="1.5"/></>,
    machine: <><rect x="3" y="5" width="18" height="14" rx="2"/><path d="M7 5V3h10v2M7 19v2m10-2v2M8 10h3m2 0h3M8 14h8"/></>,
    activity: <><path d="M3 12h4l3-8 4 16 3-8h4"/></>,
    bell: <><path d="M18 8a6 6 0 0 0-12 0c0 7-3 7-3 9h18c0-2-3-2-3-9"/><path d="M10 21h4"/></>,
    spark: <><path d="m12 3 1.7 5.3L19 10l-5.3 1.7L12 17l-1.7-5.3L5 10l5.3-1.7L12 3Z"/><path d="m19 16 .8 2.2L22 19l-2.2.8L19 22l-.8-2.2L16 19l2.2-.8L19 16Z"/></>,
    settings: <><circle cx="12" cy="12" r="3"/><path d="m19.4 15 .1.1 1.1 1.8-1.7 2.9-2.1-.6a8 8 0 0 1-1.6.9l-.7 2h-3.4l-.7-2a8 8 0 0 1-1.6-.9l-2.1.6L5 16.9l1.1-1.8a7.8 7.8 0 0 1 0-1.9L5 11.4l1.7-2.9 2.1.6a8 8 0 0 1 1.6-.9l.7-2h3.4l.7 2a8 8 0 0 1 1.6.9l2.1-.6 1.7 2.9-1.1 1.8c.1.6.1 1.2 0 1.8Z" transform="translate(-1 -1) scale(1.08)"/></>,
    search: <><circle cx="10.8" cy="10.8" r="6.8"/><path d="m16 16 5 5"/></>,
    refresh: <><path d="M20 7v5h-5M4 17v-5h5"/><path d="M5.6 9a7 7 0 0 1 11.8-2L20 12M4 12l2.6 5a7 7 0 0 0 11.8-2"/></>,
    arrow: <><path d="M5 12h14M13 6l6 6-6 6"/></>,
    chevron: <path d="m9 18 6-6-6-6"/>,
    check: <path d="m5 12 4 4L19 6"/>,
    clock: <><circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/></>,
    thermometer: <><path d="M14 14.8V5a3 3 0 0 0-6 0v9.8a5 5 0 1 0 6 0Z"/><path d="M11 11v6"/></>,
    gauge: <><path d="M4.9 19a9 9 0 1 1 14.2 0"/><path d="m12 13 4-4M5 19h14"/></>,
    wrench: <><path d="M14.7 6.3a5 5 0 0 0-6.4 6.4L3 18l3 3 5.3-5.3a5 5 0 0 0 6.4-6.4L14 12l-3-3 3.7-2.7Z"/></>,
    download: <><path d="M12 3v12m-5-5 5 5 5-5M5 21h14"/></>,
    help: <><circle cx="12" cy="12" r="9"/><path d="M9.6 9a2.5 2.5 0 1 1 4.5 1.5c-1 1.1-2.1 1.4-2.1 3M12 17.5h.01"/></>,
    shield: <><path d="M12 22s8-4 8-11V5l-8-3-8 3v6c0 7 8 11 8 11Z"/><path d="m9 12 2 2 4-4"/></>,
    close: <><path d="m6 6 12 12M18 6 6 18"/></>,
    external: <><path d="M14 3h7v7M21 3l-9 9"/><path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"/></>,
    layers: <><path d="m12 3 9 5-9 5-9-5 9-5Z"/><path d="m3 12 9 5 9-5M3 16l9 5 9-5"/></>,
    menu: <><path d="M4 6h16M4 12h16M4 18h16"/></>,
  };
  return <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={strokeWidth} strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">{paths[name] || paths.activity}</svg>;
}

async function getJson(path, options = {}) {
  const response = await fetch(`${API_PREFIX}${path}`, {
    headers: { 'Content-Type': 'application/json', ...(options.headers || {}) },
    ...options,
  });
  const contentType = response.headers.get('content-type') || '';
  const payload = contentType.includes('application/json') ? await response.json() : await response.text();
  if (!response.ok) {
    const detail = payload && typeof payload === 'object' ? (payload.detail || payload.message) : payload;
    throw new Error(detail || `Request failed (${response.status})`);
  }
  return payload;
}

function unwrapList(data, keys = []) {
  if (Array.isArray(data)) return data;
  for (const key of keys) if (Array.isArray(data?.[key])) return data[key];
  return [];
}

function firstDefined(object, keys, fallback = undefined) {
  for (const key of keys) if (object && object[key] !== undefined && object[key] !== null) return object[key];
  return fallback;
}

function toNumber(value, fallback = null) {
  if (value === null || value === undefined || value === '') return fallback;
  const result = Number(value);
  return Number.isFinite(result) ? result : fallback;
}

function getSensor(reading, aliases, fallback = null) {
  return toNumber(firstDefined(reading, aliases, fallback), fallback);
}

function normalizeMachine(machine, index = 0) {
  // /fleet/overview uses sensor_readings; monitoring history rows put sensors at top level.
  const reading = firstDefined(
    machine,
    ['latest_reading', 'latestReading', 'sensor_readings', 'sensorReadings', 'reading', 'sensors'],
    machine,
  ) || machine;
  const id = String(firstDefined(
    machine,
    ['machine_id', 'machineId', 'id', 'asset_id', 'assetId'],
    `MACHINE-${String(index + 1).padStart(2, '0')}`,
  ));
  const display = DEMO_MACHINE_LABELS[id] || {};
  const score = Math.round(Math.max(0, Math.min(100, toNumber(
    firstDefined(machine, ['health_score', 'healthScore', 'score']),
    null,
  ) ?? 88)));
  const rawCondition = String(firstDefined(
    machine,
    ['condition', 'status', 'health_status', 'healthStatus'],
    score >= 85 ? 'healthy' : score >= 60 ? 'attention_required' : 'critical',
  )).toLowerCase();
  const condition = rawCondition.includes('critical') || rawCondition === 'offline'
    ? 'critical'
    : rawCondition.includes('attention') || rawCondition.includes('warning') || rawCondition.includes('maintenance')
      ? 'attention'
      : 'healthy';

  return {
    ...machine,
    machine_id: id,
    name: firstDefined(machine, ['name', 'machine_name', 'machineName', 'label'], display.name || id),
    area: firstDefined(machine, ['area', 'location', 'line', 'site'], display.area || 'Production floor'),
    health_score: score,
    condition,
    open_alerts: toNumber(firstDefined(machine, ['open_alerts', 'openAlerts', 'alert_count', 'alertCount']), 0),
    latest_reading: {
      ...reading,
      air_temperature: getSensor(reading, ['air_temperature', 'air_temperature_k', 'airTemperature', 'airTemperatureK']),
      process_temperature: getSensor(reading, ['process_temperature', 'process_temperature_k', 'processTemperature', 'processTemperatureK', 'process_temp_k']),
      rotational_speed: getSensor(reading, ['rotational_speed', 'rotational_speed_rpm', 'rotationalSpeed', 'rotationalSpeedRpm', 'speed_rpm']),
      torque: getSensor(reading, ['torque', 'torque_nm', 'torqueNm']),
      tool_wear: getSensor(reading, ['tool_wear', 'tool_wear_min', 'toolWear', 'toolWearMin']),
      timestamp: firstDefined(
        reading,
        ['received_at', 'timestamp', 'recorded_at', 'created_at', 'createdAt'],
        firstDefined(machine, ['latest_reading_at', 'received_at', 'updated_at', 'updatedAt', 'timestamp'], null),
      ),
    },
  };
}

function normalizeAlert(alert, index = 0) {
  return {
    ...alert,
    id: String(firstDefined(alert, ['id', 'alert_id', 'alertId'], `ALERT-${index + 1}`)),
    machine_id: String(firstDefined(alert, ['machine_id', 'machineId', 'asset_id'], 'Unknown machine')),
    severity: String(firstDefined(alert, ['severity', 'priority', 'level'], 'warning')).toLowerCase(),
    title: firstDefined(alert, ['title', 'name', 'rule_name'], 'Machine alert'),
    message: firstDefined(alert, ['message', 'description', 'detail'], 'Review the latest machine telemetry.'),
    status: String(firstDefined(alert, ['status', 'state'], 'open')).toLowerCase(),
    created_at: firstDefined(alert, ['created_at', 'createdAt', 'timestamp'], null),
  };
}

function getTemperature(reading) {
  return getSensor(reading, ['process_temperature', 'process_temperature_k', 'processTemperature', 'processTemperatureK', 'process_temp_k'], null);
}

function getTorque(reading) {
  return getSensor(reading, ['torque', 'torque_nm', 'torqueNm'], null);
}

function machineStatusLabel(condition) {
  if (condition === 'critical') return 'Critical';
  if (condition === 'attention') return 'Needs attention';
  return 'Healthy';
}

function severityClass(severity) {
  if (String(severity).toLowerCase().includes('critical') || String(severity).toLowerCase().includes('high')) return 'critical';
  if (String(severity).toLowerCase().includes('info') || String(severity).toLowerCase().includes('low')) return 'info';
  return 'warning';
}

function timeAgo(timestamp) {
  if (!timestamp) return 'Time not recorded';
  const date = new Date(timestamp);
  if (Number.isNaN(date.getTime())) return String(timestamp);
  const minutes = Math.max(0, Math.round((Date.now() - date.getTime()) / 60000));
  if (minutes < 1) return 'Just now';
  if (minutes < 60) return `${minutes} min ago`;
  const hours = Math.floor(minutes / 60);
  if (hours < 24) return `${hours} hr${hours === 1 ? '' : 's'} ago`;
  return `${Math.floor(hours / 24)} day${Math.floor(hours / 24) === 1 ? '' : 's'} ago`;
}

function formatTime(timestamp) {
  if (!timestamp) return '—';
  const date = new Date(timestamp);
  if (Number.isNaN(date.getTime())) return '—';
  return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
}

function formatValue(value, digits = 1) {
  if (value === null || value === undefined || !Number.isFinite(Number(value))) return '—';
  return Number(value).toLocaleString(undefined, { maximumFractionDigits: digits, minimumFractionDigits: digits });
}

function LogoMark() {
  return <div className="brand-mark" aria-hidden="true"><span /><span /><span /><span /></div>;
}

function StatusBadge({ condition }) {
  return <span className={`status-badge status-${condition}`}><span className="status-dot" />{machineStatusLabel(condition)}</span>;
}

function SeverityBadge({ severity }) {
  const value = severityClass(severity);
  return <span className={`severity-badge severity-${value}`}><span />{value === 'critical' ? 'Critical' : value === 'info' ? 'Info' : 'Warning'}</span>;
}

function MetricCard({ icon, label, value, note, accent, spark = [] }) {
  return (
    <article className={`metric-card metric-${accent}`}>
      <div className="metric-topline"><span className="metric-icon"><Icon name={icon} size={18} /></span><span className="metric-caption">{note}</span></div>
      <div className="metric-label">{label}</div>
      <div className="metric-value">{value}</div>
      <div className="metric-bottom"><span className="metric-footnote">{accent === 'critical' ? 'Requires review' : accent === 'amber' ? 'Monitor closely' : accent === 'mint' ? 'Operating normally' : 'Across this workspace'}</span><Sparkline values={spark.length ? spark : [4, 5, 3, 6, 5, 7, 6]} accent={accent} /></div>
    </article>
  );
}

function Sparkline({ values, accent = 'mint' }) {
  const max = Math.max(...values, 1);
  const min = Math.min(...values, 0);
  const range = max - min || 1;
  const points = values.map((value, index) => `${values.length < 2 ? 50 : (index / (values.length - 1)) * 100},${25 - ((value - min) / range) * 21}`).join(' ');
  return <svg className={`sparkline sparkline-${accent}`} viewBox="0 0 100 28" preserveAspectRatio="none" aria-hidden="true"><polyline points={points} fill="none" stroke="currentColor" strokeWidth="2.4" strokeLinecap="round" strokeLinejoin="round" /></svg>;
}

function TemperatureChart({ values, preview, snapshotOnly = false }) {
  const data = values.length ? values : demoTemperature;
  const width = 700;
  const height = 210;
  const left = 41;
  const right = 12;
  const top = 17;
  const bottom = 27;
  const innerW = width - left - right;
  const innerH = height - top - bottom;
  const minValue = Math.floor((Math.min(...data) - 2) / 5) * 5;
  const maxValue = Math.ceil((Math.max(...data) + 2) / 5) * 5;
  const range = maxValue - minValue || 1;
  const pts = data.map((v, i) => ({ x: left + (data.length < 2 ? innerW : (i / (data.length - 1)) * innerW), y: top + ((maxValue - v) / range) * innerH }));
  const line = pts.map((p, i) => `${i === 0 ? 'M' : 'L'} ${p.x.toFixed(2)} ${p.y.toFixed(2)}`).join(' ');
  const area = `${line} L ${pts[pts.length - 1].x} ${top + innerH} L ${pts[0].x} ${top + innerH} Z`;
  const yTicks = [0, 1, 2, 3].map(i => maxValue - ((maxValue - minValue) * i / 3));
  return (
    <div className="chart-wrap">
      <svg className="temperature-chart" viewBox={`0 0 ${width} ${height}`} role="img" aria-label="Process temperature trend">
        <defs><linearGradient id="tempArea" x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stopColor="#58A8FF" stopOpacity=".27"/><stop offset="100%" stopColor="#58A8FF" stopOpacity=".015"/></linearGradient></defs>
        {yTicks.map((value, i) => { const y = top + (innerH * i / 3); return <g key={i}><line x1={left} x2={width - right} y1={y} y2={y} stroke="#E1E8F2" strokeDasharray="4 5"/><text x="0" y={y + 4} fill="#8290A4" fontSize="11">{value.toFixed(0)} K</text></g>; })}
        <path d={area} fill="url(#tempArea)" />
        <path d={line} fill="none" stroke="#3568ED" strokeWidth="2.7" strokeLinecap="round" strokeLinejoin="round" />
        {pts.length > 0 && <><circle cx={pts[pts.length - 1].x} cy={pts[pts.length - 1].y} r="5" fill="#FFFFFF" stroke="#3568ED" strokeWidth="3"/><circle cx={pts[pts.length - 1].x} cy={pts[pts.length - 1].y} r="9" fill="#3568ED" opacity=".12"/></>}
        <text x={left} y={height - 5} fill="#92A0B3" fontSize="11">Earlier</text><text x={width - right} y={height - 5} textAnchor="end" fill="#92A0B3" fontSize="11">{snapshotOnly ? 'Current snapshot' : preview ? 'Latest sample' : 'Latest reading'}</text>
      </svg>
      {preview && <span className="chart-preview-note">Illustrative trend · connect the backend to view stored readings</span>}
      {snapshotOnly && <span className="chart-preview-note">Historical samples unavailable · showing the selected machine's latest stored reading.</span>}
    </div>
  );
}

function HealthDistribution({ machines }) {
  const total = machines.length || 1;
  const healthy = machines.filter(m => m.condition === 'healthy').length;
  const attention = machines.filter(m => m.condition === 'attention').length;
  const critical = machines.filter(m => m.condition === 'critical').length;
  return <div className="distribution">
    <div className="distribution-bar"><span className="dist-healthy" style={{ width: `${healthy / total * 100}%` }} /><span className="dist-attention" style={{ width: `${attention / total * 100}%` }} /><span className="dist-critical" style={{ width: `${critical / total * 100}%` }} /></div>
    <div className="distribution-legend">
      <span><i className="legend-dot legend-healthy" />Healthy <b>{healthy}</b></span>
      <span><i className="legend-dot legend-attention" />Attention <b>{attention}</b></span>
      <span><i className="legend-dot legend-critical" />Critical <b>{critical}</b></span>
    </div>
  </div>;
}

function MachineRow({ machine, onSelect }) {
  const reading = machine.latest_reading || {};
  return <tr onClick={() => onSelect(machine)} className="machine-row" tabIndex="0" onKeyDown={event => { if (event.key === 'Enter') onSelect(machine); }}>
    <td><div className="asset-cell"><div className={`asset-avatar avatar-${machine.condition}`}><Icon name="machine" size={17} /></div><div><strong>{machine.name}</strong><span>{machine.machine_id} <i>·</i> {machine.area}</span></div></div></td>
    <td><div className="health-cell"><div className="health-track"><span className={`health-fill health-${machine.condition}`} style={{ width: `${machine.health_score}%` }} /></div><b>{machine.health_score}</b></div></td>
    <td><StatusBadge condition={machine.condition} /></td>
    <td><span className="table-reading">{formatValue(getTemperature(reading), 1)} <small>K</small></span></td>
    <td><span className="table-reading">{formatValue(getTorque(reading), 1)} <small>Nm</small></span></td>
    <td><span className={`open-alert-count ${machine.open_alerts > 0 ? 'has-alert' : ''}`}>{machine.open_alerts}</span></td>
    <td><button className="icon-button row-arrow" onClick={event => { event.stopPropagation(); onSelect(machine); }} aria-label={`View ${machine.machine_id}`}><Icon name="chevron" size={17} /></button></td>
  </tr>;
}

function AlertRow({ alert, onAcknowledge, busy }) {
  const severity = severityClass(alert.severity);
  return <div className="alert-row">
    <div className={`alert-symbol alert-symbol-${severity}`}><Icon name={severity === 'critical' ? 'activity' : 'bell'} size={17} /></div>
    <div className="alert-copy"><div className="alert-titleline"><strong>{alert.title}</strong><SeverityBadge severity={alert.severity} /></div><p>{alert.message}</p><div className="alert-meta"><span>{alert.machine_id}</span><span className="meta-divider">·</span><span><Icon name="clock" size={12} /> {timeAgo(alert.created_at)}</span></div></div>
    {alert.status !== 'acknowledged' && alert.status !== 'resolved' && !String(alert.id).startsWith('preview-') && <button className="ack-button" disabled={busy} onClick={() => onAcknowledge(alert)}>{busy ? 'Saving…' : 'Acknowledge'}</button>}
    {(alert.status === 'acknowledged' || alert.status === 'resolved') && <span className="acknowledged-label"><Icon name="check" size={14} /> {alert.status === 'resolved' ? 'Resolved' : 'Acknowledged'}</span>}
  </div>;
}

function App() {
  const [fleetPayload, setFleetPayload] = useState(null);
  const [summaryPayload, setSummaryPayload] = useState(null);
  const [historyPayload, setHistoryPayload] = useState(null);
  const [alertsPayload, setAlertsPayload] = useState(null);
  const [apiOnline, setApiOnline] = useState(false);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [lastUpdated, setLastUpdated] = useState(null);
  const [loadError, setLoadError] = useState('');
  const [search, setSearch] = useState('');
  const [activeNav, setActiveNav] = useState('overview');
  const [selectedMachine, setSelectedMachine] = useState(null);
  const [alertFilter, setAlertFilter] = useState('all');
  const [acknowledgingId, setAcknowledgingId] = useState(null);
  const [question, setQuestion] = useState('');
  const [assistantResult, setAssistantResult] = useState(null);
  const [assistantLoading, setAssistantLoading] = useState(false);
  const [assistantError, setAssistantError] = useState('');
  const [mobileNavOpen, setMobileNavOpen] = useState(false);
  const [chartMachineId, setChartMachineId] = useState('');

  const loadDashboard = useCallback(async (isRefresh = false) => {
    if (isRefresh) setRefreshing(true);
    else setLoading(true);
    setLoadError('');
    const endpoints = [
      ['fleet', '/fleet/overview'],
      ['summary', '/monitoring/summary'],
      ['history', '/monitoring/readings?limit=100'],
      ['alerts', '/alerts?limit=12'],
    ];
    const results = await Promise.allSettled(endpoints.map(([, path]) => getJson(path)));
    let successes = 0;
    results.forEach((result, index) => {
      if (result.status !== 'fulfilled') return;
      successes += 1;
      const key = endpoints[index][0];
      if (key === 'fleet') setFleetPayload(result.value);
      if (key === 'summary') setSummaryPayload(result.value);
      if (key === 'history') setHistoryPayload(result.value);
      if (key === 'alerts') setAlertsPayload(result.value);
    });
    setApiOnline(successes > 0);
    if (successes === 0) setLoadError('The API could not be reached. Showing clearly labelled preview data until the backend is available.');
    else if (successes < endpoints.length) setLoadError('Some API endpoints could not be loaded. Available live data is shown; missing sections may use preview data.');
    setLastUpdated(new Date());
    setLoading(false);
    setRefreshing(false);
  }, []);

  useEffect(() => {
    loadDashboard();
    const timer = window.setInterval(() => loadDashboard(true), 30000);
    return () => window.clearInterval(timer);
  }, [loadDashboard]);

  const machines = useMemo(() => {
    const fleetRows = unwrapList(fleetPayload, ['machines', 'items', 'fleet', 'machine_list', 'assets']);
    if (fleetRows.length) return fleetRows.map(normalizeMachine);
    const summaryRows = unwrapList(summaryPayload, ['latest_readings', 'machines', 'items', 'readings']);
    if (summaryRows.length) {
      const byMachine = new Map();
      summaryRows.forEach((row, index) => {
        const machine = normalizeMachine(row, index);
        byMachine.set(machine.machine_id, machine);
      });
      return [...byMachine.values()];
    }
    const historyRows = unwrapList(historyPayload, ['readings', 'items', 'results', 'data']);
    if (historyRows.length) {
      const latest = new Map();
      historyRows.forEach((row, index) => {
        const machine = normalizeMachine(row, index);
        const current = latest.get(machine.machine_id);
        const timestamp = new Date(machine.latest_reading.timestamp || 0).getTime();
        const currentTimestamp = new Date(current?.latest_reading?.timestamp || 0).getTime();
        if (!current || timestamp >= currentTimestamp) latest.set(machine.machine_id, machine);
      });
      if (latest.size) return [...latest.values()];
    }
    return [];
  }, [fleetPayload, summaryPayload, historyPayload]);

  const previewMode = machines.length === 0;
  const displayedMachines = previewMode ? sampleMachines : machines;
  const rawAlerts = unwrapList(alertsPayload, ['alerts', 'items', 'results', 'data']);
  const displayedAlerts = (rawAlerts.length ? rawAlerts.map(normalizeAlert) : previewMode ? sampleAlerts : []).sort((a, b) => {
    const sev = value => severityClass(value.severity) === 'critical' ? 0 : severityClass(value.severity) === 'warning' ? 1 : 2;
    return sev(a) - sev(b) || new Date(b.created_at || 0) - new Date(a.created_at || 0);
  });
  const openAlerts = displayedAlerts.filter(alert => !['acknowledged', 'resolved', 'closed'].includes(alert.status));
  // The alerts endpoint is paginated, so prefer the fleet overview's aggregate count when available.
  const reportedOpenAlertCount = previewMode ? null : toNumber(
    firstDefined(fleetPayload?.summary, ['total_open_alerts', 'open_alerts', 'openAlerts', 'open_alert_count']),
    null,
  );
  const openAlertCount = reportedOpenAlertCount ?? openAlerts.length;
  const healthyCount = toNumber(firstDefined(fleetPayload?.summary, ['healthy_machines', 'healthy', 'healthy_count']), displayedMachines.filter(m => m.condition === 'healthy').length) ?? 0;
  const attentionCount = toNumber(firstDefined(fleetPayload?.summary, ['attention_machines', 'attention_required', 'attention_count']), displayedMachines.filter(m => m.condition === 'attention').length) ?? 0;
  const criticalCount = toNumber(firstDefined(fleetPayload?.summary, ['critical_machines', 'critical', 'critical_count']), displayedMachines.filter(m => m.condition === 'critical').length) ?? 0;
  const averageHealth = displayedMachines.length ? Math.round(displayedMachines.reduce((sum, m) => sum + m.health_score, 0) / displayedMachines.length) : 0;
  const filteredMachines = displayedMachines.filter(machine => `${machine.machine_id} ${machine.name} ${machine.area}`.toLowerCase().includes(search.toLowerCase()));
  const filteredAlerts = displayedAlerts.filter(alert => alertFilter === 'all' || (alertFilter === 'open' ? !['acknowledged', 'resolved', 'closed'].includes(alert.status) : severityClass(alert.severity) === alertFilter));
  const historyRows = unwrapList(historyPayload, ['readings', 'items', 'results', 'data']);
  const orderedHistoryRows = [...historyRows].sort((a, b) => {
    const timeA = new Date(firstDefined(a, ['received_at', 'timestamp', 'recorded_at', 'created_at', 'createdAt'], 0)).getTime() || 0;
    const timeB = new Date(firstDefined(b, ['received_at', 'timestamp', 'recorded_at', 'created_at', 'createdAt'], 0)).getTime() || 0;
    if (timeA !== timeB) return timeA - timeB;
    // The backend may assign identical timestamps to different demo-machine readings.
    return (Number(a.id) || 0) - (Number(b.id) || 0);
  });
  const chartMachine = displayedMachines.find(machine => machine.machine_id === chartMachineId)
    || displayedMachines.find(machine => machine.condition === 'critical')
    || displayedMachines[0]
    || null;
  const effectiveChartMachineId = chartMachine?.machine_id || '';
  const selectedMachineHistory = orderedHistoryRows.filter(row => String(row.machine_id || '') === effectiveChartMachineId);
  const chartTemps = selectedMachineHistory
    .map(row => getTemperature(firstDefined(row, ['latest_reading', 'sensor_readings', 'reading', 'sensors'], row)))
    .filter(value => value !== null);
  const selectedLatestTemperature = chartMachine ? getTemperature(chartMachine.latest_reading) : null;
  const chartPreview = previewMode;
  const chartSnapshotOnly = !previewMode && chartTemps.length === 0 && selectedLatestTemperature !== null;
  const chartValues = chartTemps.length
    ? chartTemps
    : chartSnapshotOnly
      ? [selectedLatestTemperature]
      : [];
  const latestTemperature = chartTemps.length
    ? chartTemps[chartTemps.length - 1]
    : selectedLatestTemperature;
  const totalReadingCount = firstDefined(summaryPayload, ['total_readings', 'readings_count', 'totalReadings'], firstDefined(summaryPayload?.summary, ['total_readings', 'readings_count'], historyRows.length));

  const navigate = (id) => {
    setActiveNav(id);
    setMobileNavOpen(false);
    const targetId = id === 'overview' ? 'overview-section' : id === 'machines' ? 'machines-section' : id === 'alerts' ? 'alerts-section' : 'assistant-section';
    document.getElementById(targetId)?.scrollIntoView({ behavior: 'smooth', block: 'start' });
  };

  const acknowledgeAlert = async (alert) => {
    setAcknowledgingId(alert.id);
    try {
      await getJson(`/alerts/${encodeURIComponent(alert.id)}/acknowledge`, { method: 'PATCH' });
      await loadDashboard(true);
    } catch (error) {
      setLoadError(`Couldn't acknowledge alert: ${error.message}. Check that the backend endpoint is available.`);
    } finally {
      setAcknowledgingId(null);
    }
  };

  const askAssistant = async (event) => {
    event.preventDefault();
    const cleanQuestion = question.trim();
    if (!cleanQuestion) return;
    setAssistantLoading(true);
    setAssistantError('');
    setAssistantResult(null);
    try {
      const result = await getJson('/maintenance/assistant', {
        method: 'POST',
        body: JSON.stringify({ question: cleanQuestion }),
      });
      setAssistantResult(result);
    } catch (error) {
      setAssistantError(`The maintenance assistant isn't available yet: ${error.message}. Confirm that the backend route and any required LLM configuration are enabled.`);
    } finally {
      setAssistantLoading(false);
    }
  };

  const assistantAnswer = assistantResult && typeof assistantResult === 'object'
    ? firstDefined(assistantResult, ['answer', 'response', 'message', 'result', 'summary'], null)
    : assistantResult;
  const assistantSources = assistantResult && typeof assistantResult === 'object' ? unwrapList(assistantResult, ['sources', 'references', 'documents']) : [];

  return (
    <div className="app-shell">
      <aside className={`sidebar ${mobileNavOpen ? 'sidebar-open' : ''}`}>
        <div className="brand"><LogoMark /><div className="brand-copy"><strong>FactoryPulse<span> AI</span></strong><small>INDUSTRIAL INTELLIGENCE</small></div><button className="mobile-close icon-button" onClick={() => setMobileNavOpen(false)} aria-label="Close navigation"><Icon name="close" /></button></div>
        <div className="workspace-label">WORKSPACE</div>
        <button className={`workspace-switch ${activeNav === 'overview' ? 'workspace-selected' : ''}`} onClick={() => navigate('overview')}><div className="workspace-avatar">N</div><span><strong>Northstar Manufacturing</strong><small>Production environment</small></span><span className="switch-chevron">⌄</span></button>
        <div className="nav-label">MONITOR</div>
        <nav className="side-nav" aria-label="Main navigation">
          <button className={`nav-item ${activeNav === 'overview' ? 'nav-active' : ''}`} onClick={() => navigate('overview')}><Icon name="grid"/><span>Overview</span><span className="nav-active-line" /></button>
          <button className={`nav-item ${activeNav === 'machines' ? 'nav-active' : ''}`} onClick={() => navigate('machines')}><Icon name="machine"/><span>Machine fleet</span><span className="nav-count">{displayedMachines.length}</span></button>
          <button className={`nav-item ${activeNav === 'alerts' ? 'nav-active' : ''}`} onClick={() => navigate('alerts')}><Icon name="bell"/><span>Alerts center</span>{openAlertCount > 0 && <span className="nav-alert-count">{openAlertCount}</span>}</button>
          <button className={`nav-item ${activeNav === 'assistant' ? 'nav-active' : ''}`} onClick={() => navigate('assistant')}><Icon name="spark"/><span>Maintenance copilot</span><span className="nav-new">AI</span></button>
        </nav>
        <div className="sidebar-bottom">
          <div className="sidebar-help"><div className="help-icon"><Icon name="help" size={17}/></div><div><strong>Need a hand?</strong><p>Explore your machine data with your maintenance copilot.</p><button onClick={() => navigate('assistant')}>Ask a question <Icon name="arrow" size={14}/></button></div></div>
          <div className="profile-row"><div className="profile-avatar">OP</div><div className="profile-copy"><strong>Operations team</strong><small>Factory administrator</small></div><button className="profile-menu icon-button" aria-label="Profile options"><span>···</span></button></div>
        </div>
      </aside>

      {mobileNavOpen && <button className="mobile-overlay" onClick={() => setMobileNavOpen(false)} aria-label="Close navigation overlay" />}

      <main className="main-area">
        <header className="topbar">
          <div className="topbar-left"><button className="mobile-menu icon-button" onClick={() => setMobileNavOpen(true)} aria-label="Open navigation"><Icon name="menu"/></button><div className="breadcrumb"><span>Workspace</span><Icon name="chevron" size={13}/><strong>{activeNav === 'machines' ? 'Machine fleet' : activeNav === 'alerts' ? 'Alerts center' : activeNav === 'assistant' ? 'Maintenance copilot' : 'Overview'}</strong></div></div>
          <div className="topbar-actions"><div className={`connection-pill ${(!apiOnline || previewMode || loadError) ? 'connection-demo' : 'connection-live'}`} title={loadError || (previewMode ? 'Illustrative machine data is being shown.' : 'Dashboard data is available from the backend.')}><span className="connection-dot" />{previewMode ? 'Preview data' : loadError ? 'Partial connection' : 'Backend connected'}</div><div className="topbar-divider"/><span className="topbar-date">{new Date().toLocaleDateString(undefined, { weekday: 'short', day: 'numeric', month: 'short' })}</span><button className={`icon-button refresh-button ${refreshing ? 'rotating' : ''}`} onClick={() => loadDashboard(true)} aria-label="Refresh dashboard" title="Refresh data"><Icon name="refresh" size={18}/></button><div className="topbar-profile">OP</div></div>
        </header>

        <div className="page-content">
          <section className="page-heading" id="overview-section">
            <div><div className="eyebrow"><span className="eyebrow-line"/> OPERATIONS INTELLIGENCE <span className="eyebrow-dot">·</span> LIVE WORKSPACE</div><h1>Know your floor.<br/><span>Before it stops.</span></h1><p className="page-subtitle">A clearer picture of machine health, emerging risks, and the next best maintenance action.</p></div>
            <div className="heading-actions"><button className="button button-secondary" onClick={() => navigate('machines')}><Icon name="layers" size={16}/> Explore fleet</button><button className="button button-primary" onClick={() => navigate('assistant')}><Icon name="spark" size={16}/> Ask maintenance AI <Icon name="arrow" size={15}/></button></div>
          </section>

          {loadError && <div className={`system-banner ${apiOnline ? 'banner-warning' : 'banner-preview'}`}><span className="banner-mark"><Icon name={apiOnline ? 'help' : 'activity'} size={16}/></span><p><strong>{apiOnline ? 'Partial data connection' : 'Preview data is on'}</strong>{loadError}</p><button className="banner-action" onClick={() => loadDashboard(true)}>Retry <Icon name="arrow" size={13}/></button></div>}
          {previewMode && !loadError && <div className="system-banner banner-preview"><span className="banner-mark"><Icon name="activity" size={16}/></span><p><strong>Preview data is on</strong>The dashboard is showing illustrative machines and signals. Connect the FastAPI service to display operational data.</p><button className="banner-action" onClick={() => loadDashboard(true)}>Retry <Icon name="arrow" size={13}/></button></div>}

          <section className="metrics-grid" aria-label="Fleet health summary">
            <MetricCard icon="machine" label="Machines monitored" value={String(previewMode ? displayedMachines.length : toNumber(firstDefined(fleetPayload?.summary, ['total_machines', 'machines_monitored', 'total']), displayedMachines.length)).padStart(2, '0')} note={previewMode ? 'Preview inventory' : loadError ? 'Partial inventory' : 'Live inventory'} accent="dark" spark={[3, 3, 4, 4, 4, 4, 4]} />
            <MetricCard icon="check" label="Healthy machines" value={String(healthyCount).padStart(2, '0')} note={`${Math.round(healthyCount / Math.max(displayedMachines.length, 1) * 100)}% of fleet`} accent="mint" spark={[5, 6, 5, 7, 7, 8, 8]} />
            <MetricCard icon="activity" label="Need attention" value={String(attentionCount).padStart(2, '0')} note="Early intervention" accent="amber" spark={[2, 3, 2, 4, 3, 4, 4]} />
            <MetricCard icon="bell" label="Critical machines" value={String(criticalCount).padStart(2, '0')} note={`${openAlertCount} open alert${openAlertCount === 1 ? '' : 's'}`} accent="critical" spark={[1, 1, 2, 1, 2, 3, 2]} />
          </section>

          <section className="insights-grid">
            <article className="panel temperature-panel">
              <div className="panel-header"><div><div className="section-kicker">SENSOR TELEMETRY</div><h2>Process temperature</h2><p>One machine at a time, ordered by stored reading time.</p></div><div className="panel-header-right"><select className="chart-machine-select" value={effectiveChartMachineId} onChange={event => setChartMachineId(event.target.value)} aria-label="Select machine for temperature chart" title="Select machine for temperature chart" style={{ height: 30, maxWidth: 155, minWidth: 0, padding: "0 7px", border: "1px solid #dfe6f0", borderRadius: 7, color: "#34435b", background: "#fff", fontSize: 10 }}>{displayedMachines.map(machine => <option key={machine.machine_id} value={machine.machine_id}>{machine.name}</option>)}</select><span className={`data-tag ${(chartPreview || chartSnapshotOnly) ? 'tag-preview' : 'tag-live'}`}><i/>{chartPreview ? 'Sample trend' : chartSnapshotOnly ? 'Snapshot only' : chartTemps.length ? 'Stored history' : 'No history'}</span><button className="icon-button panel-menu" aria-label="More temperature options">···</button></div></div>
              <div className="temperature-summary"><div><span className="current-reading">{formatValue(latestTemperature ?? getTemperature(displayedMachines[0]?.latest_reading), 1)}<small> K</small></span><span className="reading-caption">{chartMachine ? `${chartMachine.name} · latest process reading` : 'Latest process reading'}</span></div><div className="temperature-delta"><span className="delta-icon"><Icon name="activity" size={15}/></span><span><strong>{latestTemperature === null ? '—' : 'Monitoring'}</strong><small>Signal status</small></span></div></div>
              <TemperatureChart values={chartValues} preview={chartPreview} snapshotOnly={chartSnapshotOnly}/>
              <div className="chart-footer"><span><i className="chart-legend-line"/>Process temperature (K) · {chartMachine?.machine_id || 'No machine selected'}</span><span>Refreshes every 30 seconds <Icon name="clock" size={13}/></span></div>
            </article>

            <article className="panel fleet-health-panel">
              <div className="panel-header"><div><div className="section-kicker">FLEET CONDITION</div><h2>Machine health</h2><p>One view across your production floor.</p></div><button className="icon-button panel-menu" aria-label="More fleet health options">···</button></div>
              <div className="health-overview"><div className="health-ring" style={{ '--health-value': `${averageHealth}%` }}><div className="health-ring-inner"><strong>{averageHealth}</strong><span>avg. score</span></div></div><div className="health-overview-copy"><span className="health-overview-label">Overall condition</span><strong>{criticalCount > 0 ? 'Intervention needed' : attentionCount > 0 ? 'A few things to watch' : 'Running smoothly'}</strong><p>{criticalCount > 0 ? `${criticalCount} machine${criticalCount > 1 ? 's' : ''} need immediate review.` : attentionCount > 0 ? `${attentionCount} machine${attentionCount > 1 ? 's' : ''} may benefit from a check.` : 'No critical condition detected in the current view.'}</p></div></div>
              <div className="panel-rule"/><div className="distribution-heading"><strong>Condition breakdown</strong><span>{displayedMachines.length} assets</span></div><HealthDistribution machines={displayedMachines}/>
              <button className="text-link" onClick={() => navigate('machines')}>View all machines <Icon name="arrow" size={15}/></button>
            </article>
          </section>

          <section className="panel fleet-panel" id="machines-section">
            <div className="panel-header fleet-panel-header"><div><div className="section-kicker">ASSET MONITORING</div><h2>Machine fleet <span className="heading-count">{displayedMachines.length}</span></h2><p>Health scores and latest available sensor readings.</p></div><div className="table-actions"><label className="table-search"><Icon name="search" size={16}/><input value={search} onChange={event => setSearch(event.target.value)} placeholder="Search machines..." aria-label="Search machines"/><kbd>⌘ K</kbd></label><button className="button button-secondary button-small" onClick={() => loadDashboard(true)}><Icon name="refresh" size={15}/> Sync</button></div></div>
            <div className="table-scroll"><table className="fleet-table"><thead><tr><th>Machine / asset</th><th>Health score</th><th>Condition</th><th>Process temp.</th><th>Torque</th><th>Alerts</th><th aria-label="Open details"/></tr></thead><tbody>{filteredMachines.map(machine => <MachineRow key={machine.machine_id} machine={machine} onSelect={setSelectedMachine}/>)}{filteredMachines.length === 0 && <tr><td className="empty-table" colSpan="7">No machines match “{search}”. Try another search.</td></tr>}</tbody></table></div>
            <div className="table-footer"><span>Showing <strong>{filteredMachines.length}</strong> of <strong>{displayedMachines.length}</strong> machines{previewMode ? ' · illustrative preview' : ''}</span><button className="text-link" onClick={() => navigate('machines')}>Fleet details <Icon name="arrow" size={14}/></button></div>
          </section>

          <section className="bottom-grid">
            <article className="panel alerts-panel" id="alerts-section">
              <div className="panel-header"><div><div className="section-kicker">ATTENTION REQUIRED</div><h2>Latest alerts <span className="heading-count heading-count-alert">{openAlertCount}</span></h2><p>Prioritised events from your machine fleet.</p></div><button className="quiet-button" onClick={() => { setAlertFilter('all'); navigate('alerts'); }}>View all <Icon name="arrow" size={14}/></button></div>
              <div className="alert-filters" role="group" aria-label="Filter alerts">{[{ id: 'all', label: 'All' }, { id: 'open', label: 'Open' }, { id: 'critical', label: 'Critical' }, { id: 'warning', label: 'Warning' }].map(filter => <button key={filter.id} className={alertFilter === filter.id ? 'alert-filter active-filter' : 'alert-filter'} onClick={() => setAlertFilter(filter.id)}>{filter.label}{filter.id === 'open' && <span>{openAlerts.length}</span>}</button>)}</div>
              <div className="alert-list">{filteredAlerts.slice(0, 4).map(alert => <AlertRow key={alert.id} alert={alert} onAcknowledge={acknowledgeAlert} busy={acknowledgingId === alert.id}/>)}{filteredAlerts.length === 0 && <div className="empty-state"><div className="empty-icon"><Icon name="check" size={21}/></div><strong>You're all caught up</strong><p>No alerts match this filter.</p></div>}</div>
              <div className="alerts-footer"><span><span className="tiny-status-dot"/> {openAlertCount} open alerts</span><button className="text-link" onClick={() => navigate('alerts')}>Go to alerts center <Icon name="arrow" size={14}/></button></div>
            </article>

            <article className="copilot-card" id="assistant-section">
              <div className="copilot-glow copilot-glow-one"/><div className="copilot-glow copilot-glow-two"/>
              <div className="copilot-top"><div className="copilot-icon"><Icon name="spark" size={21}/></div><span className="copilot-chip"><span/> MAINTENANCE COPILOT</span></div>
              <h2>Turn machine signals<br/>into <em>next steps.</em></h2><p>Ask a maintenance question, explore your knowledge base, and get a more grounded starting point for investigation.</p>
              <form className="copilot-form" onSubmit={askAssistant}><label className="sr-only" htmlFor="copilot-question">Ask maintenance copilot</label><input id="copilot-question" value={question} onChange={event => setQuestion(event.target.value)} placeholder="e.g. What should I check for high torque?"/><button type="submit" disabled={assistantLoading || !question.trim()} aria-label="Send question">{assistantLoading ? <span className="button-loader"/> : <Icon name="arrow" size={18}/>}</button></form>
              <div className="suggested-prompts"><span>Try asking</span><button onClick={() => setQuestion('What should I inspect when process temperature is high?')}>High temperature <Icon name="arrow" size={12}/></button><button onClick={() => setQuestion('What are the first checks for elevated torque?')}>Elevated torque <Icon name="arrow" size={12}/></button></div>
              {assistantError && <div className="assistant-error">{assistantError}</div>}
              {assistantResult && <div className="assistant-result"><div className="assistant-result-title"><Icon name="spark" size={15}/> Suggested guidance</div><p>{typeof assistantAnswer === 'string' ? assistantAnswer : JSON.stringify(assistantAnswer ?? assistantResult, null, 2)}</p>{assistantSources.length > 0 && <div className="assistant-sources"><strong>Sources</strong>{assistantSources.map((source, index) => <span key={index}>{typeof source === 'string' ? source : firstDefined(source, ['title', 'name', 'source', 'filename'], `Reference ${index + 1}`)}</span>)}</div>}<small>Use as a starting point. Follow site procedures and the manufacturer's guidance.</small></div>}
              <div className="copilot-footer"><span><Icon name="shield" size={13}/> Grounded in available maintenance knowledge</span><span>Human review required</span></div>
            </article>
          </section>

          <footer className="page-footer"><div className="footer-brand"><LogoMark/><span>FactoryPulse AI</span><i>·</i><span>Industrial intelligence, made practical.</span></div><div className="footer-meta"><span>{!previewMode && apiOnline && !loadError ? `Last synced ${lastUpdated ? formatTime(lastUpdated) : 'just now'}` : 'Preview / partial workspace'}</span><span className="footer-dot">·</span><span>v0.1.0</span></div></footer>
        </div>
      </main>

      {selectedMachine && <div className="modal-backdrop" role="presentation" onClick={() => setSelectedMachine(null)}><section className="machine-drawer" role="dialog" aria-modal="true" aria-labelledby="machine-drawer-title" onClick={event => event.stopPropagation()}><div className="drawer-top"><div><div className="section-kicker">MACHINE DETAILS</div><h2 id="machine-drawer-title">{selectedMachine.name}</h2><span className="drawer-machine-id">{selectedMachine.machine_id} · {selectedMachine.area}</span></div><button className="icon-button" onClick={() => setSelectedMachine(null)} aria-label="Close details"><Icon name="close"/></button></div><div className="drawer-status"><StatusBadge condition={selectedMachine.condition}/><div className="drawer-score"><strong>{selectedMachine.health_score}</strong><span>/ 100 health score</span></div></div><div className="drawer-health-track"><span className={`health-fill health-${selectedMachine.condition}`} style={{ width: `${selectedMachine.health_score}%` }}/></div><div className="drawer-metrics"><div><span><Icon name="thermometer" size={16}/> Process temp.</span><strong>{formatValue(getTemperature(selectedMachine.latest_reading), 1)} <small>K</small></strong></div><div><span><Icon name="gauge" size={16}/> Torque</span><strong>{formatValue(getTorque(selectedMachine.latest_reading), 1)} <small>Nm</small></strong></div><div><span><Icon name="activity" size={16}/> Speed</span><strong>{formatValue(firstDefined(selectedMachine.latest_reading, ['rotational_speed']), 0)} <small>RPM</small></strong></div><div><span><Icon name="wrench" size={16}/> Tool wear</span><strong>{formatValue(firstDefined(selectedMachine.latest_reading, ['tool_wear']), 0)} <small>min</small></strong></div></div><div className="drawer-section"><h3>Current assessment</h3><p>{selectedMachine.condition === 'critical' ? 'This asset is marked critical by the current rules. Prioritise operator review and follow local safety and maintenance procedures.' : selectedMachine.condition === 'attention' ? 'Some signals may be approaching configured thresholds. Review the most recent telemetry and plan inspection as appropriate.' : 'No critical rule-based condition is currently identified for this asset. Continue normal monitoring and scheduled maintenance.'}</p><span className="drawer-caveat">Rule-based health indicator · Not a certified safety assessment</span></div><button className="button button-primary drawer-button" onClick={() => { setQuestion(`What should I inspect for machine ${selectedMachine.machine_id}?`); setSelectedMachine(null); navigate('assistant'); }}>Ask copilot about this machine <Icon name="arrow" size={15}/></button></section></div>}
    </div>
  );
}

export default App;
