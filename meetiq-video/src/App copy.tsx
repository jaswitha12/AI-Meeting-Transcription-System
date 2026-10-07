
import { useMemo, useRef, useState } from 'react'
import './App.css'


const navigation = [
  { label: 'Dashboard', icon: '⌂' },
  { label: 'Generate Transcript', icon: '🎙' },
  { label: 'Meeting Intelligence', icon: '🧠' },
  { label: 'Meeting Details & Analytics', icon: '▥' },
  { label: 'Decisions', icon: '✓' },
  { label: 'Participants & Responsibilities', icon: '♟' },
  { label: 'Deadlines', icon: '▦' },
  { label: 'Priorities', icon: '♨' },
  { label: 'Transcription Accuracy Testing', icon: '◎' },
  { label: 'Meeting History', icon: '▣' },
  { label: 'Knowledge Search', icon: '⌕' },
  { label: 'Zoom Integration', icon: '▤' },
]

const meetings = [
  { title: 'Project Review Meeting', date: 'Oct 04, 2026 · 10:30 AM', duration: '45 min', status: 'Completed', color: 'purple' },
  { title: 'Team Sync', date: 'Oct 03, 2026 · 02:00 PM', duration: '30 min', status: 'Completed', color: 'pink' },
  { title: 'Client Discussion', date: 'Oct 02, 2026 · 11:00 AM', duration: '60 min', status: 'Processing', color: 'blue' },
  { title: 'Design Review', date: 'Oct 01, 2026 · 03:00 PM', duration: '45 min', status: 'Completed', color: 'green' },
  { title: 'Weekly Standup', date: 'Sep 30, 2026 · 09:30 AM', duration: '20 min', status: 'Completed', color: 'orange' },
]

function App() {
  const [activePage, setActivePage] = useState('Dashboard')
  const [search, setSearch] = useState('')
  const [period, setPeriod] = useState('Last 7 days')
  const [insightPeriod, setInsightPeriod] = useState('Last 30 days')
  const [showNotifications, setShowNotifications] = useState(false)
  const [showProfile, setShowProfile] = useState(false)
  const [selectedFile, setSelectedFile] = useState('')
  const fileInput = useRef<HTMLInputElement>(null)

  const filteredMeetings = useMemo(
    () => meetings.filter((meeting) =>
      `${meeting.title} ${meeting.date} ${meeting.status}`
        .toLowerCase()
        .includes(search.toLowerCase())
    ),
    [search]
  )

  const choosePage = (page: string) => {
    setActivePage(page)
    if (page === 'Generate Transcript') fileInput.current?.click()
  }

  const onFileSelected = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0]
    if (file) {
      setSelectedFile(file.name)
      setActivePage('Generate Transcript')
    }
  }

  return (
    <div className="dashboard-app">
      <aside className="sidebar">
        <a className="brand" href="#" onClick={(e) => { e.preventDefault(); choosePage('Dashboard') }}>
          <span className="brand-icon">🎙</span>
          <span>
            <strong>MeetIQ</strong>
            <small>Turn meetings into intelligence.</small>
          </span>
        </a>

        <div className="nav-heading">WORKSPACE</div>
        <nav className="navigation">
          {navigation.map((item) => (
            <button
              key={item.label}
              className={`nav-item ${activePage === item.label ? 'active' : ''}`}
              onClick={() => choosePage(item.label)}
            >
              <span className="nav-icon">{item.icon}</span>
              <span>{item.label}</span>
            </button>
          ))}
        </nav>

        <div className="sidebar-bottom">
          <div className="nav-heading">SYSTEM</div>
          <div className="engine-status">
            <span className="live-dot" />
            <div><strong>AI ENGINE ONLINE</strong><small>Backend connection status</small></div>
          </div>
          <button className="sidebar-profile" onClick={() => setShowProfile(!showProfile)}>
            <span className="profile-avatar">J</span>
            <span><strong>Jaswitha</strong><small>MeetIQ workspace</small></span>
            <span className="profile-arrow">›</span>
          </button>
          {showProfile && (
            <div className="profile-menu">
              <strong>Jaswitha</strong>
              <p>MeetIQ workspace</p>
              <button onClick={() => setShowProfile(false)}>Close profile</button>
            </div>
          )}
        </div>
      </aside>

      <main className="dashboard-main">
        <header className="topbar">
          <label className="global-search">
            <span>⌕</span>
            <input
              value={search}
              onChange={(event) => setSearch(event.target.value)}
              placeholder="Search meetings, transcripts, decisions..."
            />
            <kbd>⌘ K</kbd>
          </label>
          <div className="topbar-actions">
            <div className="notification-wrap">
              <button className="icon-button" aria-label="Notifications" onClick={() => setShowNotifications(!showNotifications)}>
                ♧<span className="notification-dot" />
              </button>
              {showNotifications && (
                <div className="floating-menu">
                  <strong>Notifications</strong>
                  <p>You are all caught up.</p>
                </div>
              )}
            </div>
            <div className="topbar-divider" />
            <button className="user-menu" onClick={() => setShowProfile(!showProfile)}>
              <span className="profile-avatar">J</span>
              <strong>Jaswitha</strong>
              <span>⌄</span>
            </button>
          </div>
        </header>

        <div className="dashboard-content">
          {activePage === 'Dashboard' ? (
            <>
              <section className="welcome-banner">
                <div className="welcome-copy">
                  <span className="eyebrow">YOUR MEETING WORKSPACE</span>
                  <h1>Welcome back, Jaswitha! <span>👋</span></h1>
                  <p>Your intelligent workspace for meeting transcripts, decisions, action items, and AI-powered insights.</p>
                  <div className="welcome-actions">
                    <button className="primary-button" onClick={() => fileInput.current?.click()}>
                      ↑ <span>Upload Meeting</span>
                    </button>
                    <button className="secondary-button" onClick={() => choosePage('Zoom Integration')}>
                      ▣ <span>Connect Zoom</span>
                    </button>
                    <input
                      ref={fileInput}
                      className="hidden-input"
                      type="file"
                      accept="audio/*,video/*,.mp3,.wav,.m4a,.mp4,.mov,.avi,.mkv,.flac,.aac"
                      onChange={onFileSelected}
                    />
                  </div>
                  {selectedFile && <p className="selected-file">Selected file: {selectedFile}</p>}
                </div>
                <div className="welcome-art" aria-hidden="true">
                  <div className="art-orbit orbit-one" />
                  <div className="art-orbit orbit-two" />
                  <div className="art-document"><span>✓</span><i /><i /><i /><i /></div>
                  <div className="art-mic">🎙</div>
                  <div className="art-calendar">▦</div>
                  <div className="art-people">♟</div>
                  <div className="art-check">✓</div>
                </div>
              </section>

              <section className="metrics-grid">
                <article className="metric-card metric-blue">
                  <div className="metric-icon">▤</div>
                  <div className="metric-info"><span>Total Meetings</span><strong>37</strong><small><b>↗ 12%</b> from last month</small></div>
                  <svg className="sparkline" viewBox="0 0 90 50" aria-label="Meeting trend"><polyline points="2,39 14,28 24,34 36,14 47,28 58,20 69,8 82,23 89,5" /></svg>
                </article>
                <article className="metric-card metric-pink">
                  <div className="metric-icon">⚑</div>
                  <div className="metric-info"><span>Action Items</span><strong>82</strong><small><b>↗ 18%</b> from last month</small></div>
                  <svg className="sparkline" viewBox="0 0 90 50" aria-label="Action item trend"><polyline points="2,37 13,22 24,30 35,17 45,26 56,13 67,22 78,5 89,18" /></svg>
                </article>
                <article className="metric-card metric-green">
                  <div className="metric-icon">✓</div>
                  <div className="metric-info"><span>Decisions</span><strong>19</strong><small><b>↗ 27%</b> from last month</small></div>
                  <svg className="sparkline" viewBox="0 0 90 50" aria-label="Decision trend"><polyline points="2,39 14,27 25,35 36,17 47,23 59,13 70,20 80,8 89,4" /></svg>
                </article>
                <article className="metric-card metric-purple">
                  <div className="metric-icon">♟</div>
                  <div className="metric-info"><span>Participants</span><strong>116</strong><small><b>↗ 15%</b> from last month</small></div>
                  <svg className="sparkline" viewBox="0 0 90 50" aria-label="Participant trend"><polyline points="2,38 13,29 23,35 35,18 45,28 56,19 67,23 78,7 89,3" /></svg>
                </article>
              </section>

              <section className="dashboard-panels">
                <article className="panel activity-panel">
                  <div className="panel-heading">
                    <h2><span className="heading-icon">▥</span> Meeting Activity</h2>
                    <select value={period} onChange={(event) => setPeriod(event.target.value)} aria-label="Activity time period">
                      <option>Last 7 days</option><option>Last 30 days</option><option>Last 90 days</option>
                    </select>
                  </div>
                  <div className="chart-area">
                    <div className="y-labels"><span>10</span><span>8</span><span>6</span><span>4</span><span>2</span><span>0</span></div>
                    <svg className="activity-chart" viewBox="0 0 460 210" preserveAspectRatio="none" role="img" aria-label="Illustrative meeting, action item and decision trends">
                      <defs>
                        <pattern id="chartGrid" width="65" height="34" patternUnits="userSpaceOnUse"><path d="M 65 0 L 0 0 0 34" fill="none" stroke="#e8edf6" strokeWidth="1" /></pattern>
                        <linearGradient id="greenFill" x1="0" x2="0" y1="0" y2="1"><stop offset="0%" stopColor="#22c55e" stopOpacity=".23"/><stop offset="100%" stopColor="#22c55e" stopOpacity=".02"/></linearGradient>
                      </defs>
                      <rect width="460" height="204" fill="url(#chartGrid)" />
                      <path d="M0 168 L65 147 L130 154 L195 116 L260 112 L325 78 L390 25 L455 65 L455 204 L0 204 Z" fill="#ff426e" opacity=".06"/>
                      <path d="M0 168 L65 147 L130 154 L195 116 L260 112 L325 78 L390 25 L455 65" fill="none" stroke="#ff426e" strokeWidth="2.5"/>
                      <path d="M0 182 L65 160 L130 166 L195 155 L260 126 L325 119 L390 126 L455 145" fill="none" stroke="#3985ff" strokeWidth="2.5"/>
                      <path d="M0 194 L65 188 L130 191 L195 188 L260 165 L325 166 L390 183 L455 189 L455 204 L0 204 Z" fill="url(#greenFill)"/>
                      <path d="M0 194 L65 188 L130 191 L195 188 L260 165 L325 166 L390 183 L455 189" fill="none" stroke="#22c55e" strokeWidth="2.5"/>
                      {[['3','168'],['65','147'],['130','154'],['195','116'],['260','112'],['325','78'],['390','25'],['455','65']].map(([x,y]) => <circle key={`${x}-${y}`} cx={x} cy={y} r="4" fill="#ff426e" stroke="white" strokeWidth="2"/>)}
                    </svg>
                  </div>
                  <div className="chart-x-labels"><span>Sep 28</span><span>Sep 29</span><span>Sep 30</span><span>Oct 01</span><span>Oct 02</span><span>Oct 03</span><span>Oct 04</span></div>
                  <div className="chart-legend"><span><i className="legend-blue"/>Meetings</span><span><i className="legend-pink"/>Action Items</span><span><i className="legend-green"/>Decisions</span></div>
                </article>

                <article className="panel recent-panel">
                  <div className="panel-heading">
                    <h2><span className="heading-icon">▤</span> Recent Meetings</h2>
                    <button className="text-button" onClick={() => choosePage('Meeting History')}>View All →</button>
                  </div>
                  <div className="meeting-list">
                    {filteredMeetings.length ? filteredMeetings.map((meeting) => (
                      <div className="meeting-row" key={meeting.title}>
                        <div className={`meeting-symbol ${meeting.color}`}>▤</div>
                        <div className="meeting-description">
                          <strong>{meeting.title}</strong>
                          <div><span>▦ {meeting.date}</span><span>◷ {meeting.duration}</span></div>
                        </div>
                        <span className={`status-pill ${meeting.status === 'Completed' ? 'completed' : 'processing'}`}>{meeting.status}</span>
                        <span className="row-arrow">›</span>
                      </div>
                    )) : <p className="empty-state">No meetings match your search.</p>}
                  </div>
                </article>

                <article className="panel insights-panel">
                  <div className="panel-heading">
                    <h2><span className="heading-icon">◕</span> Meeting Insights</h2>
                    <select value={insightPeriod} onChange={(event) => setInsightPeriod(event.target.value)} aria-label="Insights time period">
                      <option>Last 30 days</option><option>Last 7 days</option><option>Last 90 days</option>
                    </select>
                  </div>
                  <div className="donut-section">
                    <div className="donut-chart"><div className="donut-center"><strong>82</strong><span>Total</span><span>Action Items</span></div></div>
                    <div className="donut-legend">
                      <div><i className="legend-green"/>Completed <strong>48 (58%)</strong></div>
                      <div><i className="legend-blue"/>In Progress <strong>22 (27%)</strong></div>
                      <div><i className="legend-orange"/>Pending <strong>12 (15%)</strong></div>
                    </div>
                  </div>
                  <div className="insight-stats">
                    <div><span>♟</span><small>Avg. Participants</small><strong>5.2</strong></div>
                    <div><span>◷</span><small>Avg. Duration</small><strong>38 min</strong></div>
                    <div><span>✓</span><small>Completion Rate</small><strong>78%</strong></div>
                  </div>
                </article>
              </section>
              <footer className="dashboard-footer">MeetIQ · Meeting Intelligence <span>Designed for productive meetings</span></footer>
            </>
          ) : (
            <section className="page-placeholder">
              <span className="eyebrow">MEETIQ WORKSPACE</span>
              <h1>{activePage}</h1>
              <p>This workspace section is ready for its existing backend integration.</p>
              {activePage === 'Generate Transcript' && (
                <button className="primary-button" onClick={() => fileInput.current?.click()}>↑ Choose audio or video file</button>
              )}
              {activePage === 'Zoom Integration' && (
                <p className="integration-note">Connect this page to your existing Zoom integration before using it for live recordings.</p>
              )}
              <button className="secondary-button back-button" onClick={() => choosePage('Dashboard')}>← Back to Dashboard</button>
              <input ref={fileInput} className="hidden-input" type="file" accept="audio/*,video/*,.mp3,.wav,.m4a,.mp4,.mov,.avi,.mkv,.flac,.aac" onChange={onFileSelected}/>
              {selectedFile && <p className="selected-file">Selected file: {selectedFile}</p>}
            </section>
          )}
        </div>
      </main>
    </div>
  )
}

export default App
