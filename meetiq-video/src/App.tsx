import { useEffect, useMemo, useRef, useState } from 'react'
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
  const [isAuthenticated, setIsAuthenticated] = useState(false)
  const [authEmail, setAuthEmail] = useState('')
  const [authPassword, setAuthPassword] = useState('')
  const [authError, setAuthError] = useState('')
  const [authLoading, setAuthLoading] = useState(false)
  const [authMode, setAuthMode] = useState<'login' | 'register'>('login')
    const handleRegister = async () => {
    if (!authEmail.trim() || !authPassword.trim()) {
      setAuthError('Please enter your email and password.')
      return
    }

    setAuthLoading(true)
    setAuthError('')

    try {
      const response = await fetch(
        'http://127.0.0.1:8000/auth/register',
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            email: authEmail,
            password: authPassword,
          }),
        }
      )

      const data = await response.json().catch(() => ({}))

      if (!response.ok) {
        throw new Error(
          data.detail || 'Registration failed.'
        )
      }

      setAuthMode('login')
      setAuthError('')
      alert('Account created successfully. Please login.')
    } catch (error) {
      setAuthError(
        error instanceof Error
          ? error.message
          : 'Registration failed.'
      )
    } finally {
      setAuthLoading(false)
    }
  }

  const handleLogin = async () => {
    if (!authEmail.trim() || !authPassword.trim()) {
      setAuthError('Please enter your email and password.')
      return
    }

    setAuthLoading(true)
    setAuthError('')

    try {
      const response = await fetch(
        'http://127.0.0.1:8000/auth/login',
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            email: authEmail,
            password: authPassword,
          }),
        }
      )

      const data = await response.json().catch(() => ({}))

      if (!response.ok) {
        throw new Error(
          data.detail || 'Login failed.'
        )
      }

      localStorage.setItem(
        'meetIQ_token',
        data.access_token
      )

      localStorage.setItem(
        'meetIQ_user',
        JSON.stringify(data.user)
      )

      setIsAuthenticated(true)
      setAuthError('')
      setActivePage('Dashboard')
    } catch (error) {
      setAuthError(
        error instanceof Error
          ? error.message
          : 'Login failed.'
      )
    } finally {
      setAuthLoading(false)
    }
  }
  const [period, setPeriod] = useState('Last 7 days')
  const [insightPeriod, setInsightPeriod] = useState('Last 30 days')
  const [showNotifications, setShowNotifications] = useState(false)
  const [showProfile, setShowProfile] = useState(false)
  const [selectedFile, setSelectedFile] = useState('')
  const [transcript, setTranscript] = useState('')
  const [isTranscribing, setIsTranscribing] = useState(false)
  const [transcriptionError, setTranscriptionError] = useState('')
  const [selectedAudioFile, setSelectedAudioFile] = useState<File | null>(null)
  const [meetingIntelligence, setMeetingIntelligence] = useState<any>(null)
  const [meetingHistory, setMeetingHistory] = useState<any[]>([])
  const [selectedMeeting, setSelectedMeeting] = useState<any>(null)
  const [referenceTranscript, setReferenceTranscript] = useState('')
  const [accuracyResult, setAccuracyResult] = useState<any>(null)
  const [isCheckingAccuracy, setIsCheckingAccuracy] = useState(false)
  const [accuracyError, setAccuracyError] = useState('')
  const [knowledgeQuestion, setKnowledgeQuestion] = useState('')
  const [knowledgeAnswer, setKnowledgeAnswer] = useState('')
  const [knowledgeSources, setKnowledgeSources] = useState<any[]>([])
  const [isKnowledgeSearching, setIsKnowledgeSearching] = useState(false)
  const [knowledgeError, setKnowledgeError] = useState('')
  const [zoomRecordings, setZoomRecordings] = useState<any[]>([])
  const [zoomMeetingId, setZoomMeetingId] = useState('')
  const [zoomTranscript, setZoomTranscript] = useState('')
  const [zoomError, setZoomError] = useState('')
  const [isZoomLoading, setIsZoomLoading] = useState(false)
  const fileInput = useRef<HTMLInputElement>(null)

  const filteredMeetings = useMemo(
    () => meetings.filter((meeting) =>
      `${meeting.title} ${meeting.date} ${meeting.status}`
        .toLowerCase()
        .includes(search.toLowerCase())
    ),
    [search]
  )
const loadMeetingHistory = async () => {
  try {
    const response = await fetch('http://127.0.0.1:8000/meetings')

    const data = await response.json()

    if (!response.ok) {
      throw new Error(data.detail || 'Failed to load meeting history.')
    }

    setMeetingHistory(data.meetings ?? data.data ?? [])
  } catch (error) {
    console.error('Failed to load meeting history:', error)
  }
}
useEffect(() => {
  loadMeetingHistory()
}, [])
const loadZoomRecordings = async () => {
  setIsZoomLoading(true)
  setZoomError('')

  try {
    const response = await fetch(
      'http://127.0.0.1:8000/zoom-process',
      {
        method: 'POST',
      }
    )

    const data = await response.json().catch(() => ({}))

    if (!response.ok) {
      throw new Error(
        data.detail || `Failed to load Zoom recordings.`
      )
    }

    setZoomRecordings(data.recordings ?? [])
  } catch (error) {
    setZoomError(
      error instanceof Error
        ? error.message
        : 'Failed to load Zoom recordings.'
    )
  } finally {
    setIsZoomLoading(false)
  }
}
const loadMeetingDetails = async (meetingId: number) => {
  try {
    const response = await fetch(
      `http://127.0.0.1:8000/meetings/${meetingId}`
    )

    const data = await response.json()

    if (!response.ok) {
      throw new Error(data.detail || 'Failed to load meeting details.')
    }

    setSelectedMeeting(data.data ?? data.meeting ?? null)
  } catch (error) {
    console.error('Failed to load meeting details:', error)
  }
}
  const choosePage = (page: string) => {
  setActivePage(page)

  if (page === 'Generate Transcript') {
    fileInput.current?.click()
  }

  if (page === 'Meeting History') {
    loadMeetingHistory()
  }
}
  const onFileSelected = (event: React.ChangeEvent<HTMLInputElement>) => {
  const file = event.target.files?.[0]
  if (file) {
    setSelectedFile(file.name)
    setSelectedAudioFile(file)
    setTranscript('')
    setTranscriptionError('')
    setActivePage('Generate Transcript')
  }
}
const transcribeSelectedFile = async () => {
  if (!selectedAudioFile) {
    setTranscriptionError('Please choose an audio or video file first.')
    return
  }

  setIsTranscribing(true)
  setTranscriptionError('')
  setTranscript('')

  try {
    const formData = new FormData()
    formData.append('file', selectedAudioFile)

    const response = await fetch(
      'http://127.0.0.1:8000/transcribe',
      {
        method: 'POST',
        body: formData,
      }
    )

    const data = await response.json().catch(() => ({}))

    if (!response.ok) {
      throw new Error(
        data.detail ||
          `Transcription failed with status ${response.status}.`
      )
    }

    const result =
      data.transcript ??
      data.transcription ??
      data.text

    if (
      typeof result !== 'string' ||
      !result.trim()
    ) {
      throw new Error(
        'The backend response did not contain transcript text.'
      )
    }

    setTranscript(result)
  } catch (error) {
    setTranscriptionError(
      error instanceof Error
        ? error.message
        : 'An unexpected error occurred while transcribing the file.'
    )
  } finally {
    setIsTranscribing(false)
  }
}


const checkTranscriptionAccuracy = async () => {
  if (!referenceTranscript.trim()) {
    setAccuracyError(
      'Please enter the reference transcript.'
    )
    return
  }

  if (!transcript.trim()) {
    setAccuracyError(
      'Please generate a transcript first.'
    )
    return
  }

  setIsCheckingAccuracy(true)
  setAccuracyError('')
  setAccuracyResult(null)

  try {
  const response = await fetch(
  'http://127.0.0.1:8000/transcription-accuracy',
  {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
  body: JSON.stringify({
  reference: referenceTranscript,
  hypothesis: transcript,
}),
  }
)

    const data = await response.json().catch(() => ({}))

    if (!response.ok) {
      throw new Error(
        data.detail ||
          `Accuracy check failed with status ${response.status}.`
      )
    }

    setAccuracyResult(data)
  } catch (error) {
    setAccuracyError(
      error instanceof Error
        ? error.message
        : 'An unexpected error occurred while checking accuracy.'
    )
  } finally {
    setIsCheckingAccuracy(false)
  }
}


const analyzeTranscript = async () => {
  if (!transcript.trim()) {
    setTranscriptionError(
      'Please generate a transcript first.'
    )
    return
  }

  try {
    const response = await fetch(
      'http://127.0.0.1:8000/analyze',
      {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          transcript: transcript,
        }),
      }
    )

    const data = await response.json().catch(() => ({}))

    if (!response.ok) {
      throw new Error(
        data.detail ||
          `Analysis failed with status ${response.status}.`
      )
    }

    setMeetingIntelligence(data)
  } catch (error) {
    setTranscriptionError(
      error instanceof Error
        ? error.message
        : 'An unexpected error occurred while analyzing the transcript.'
    )
  }
}
const askKnowledgeQuestion = async () => {
  if (!knowledgeQuestion.trim()) {
    setKnowledgeError('Please enter a question first.')
    return
  }

  setIsKnowledgeSearching(true)
  setKnowledgeError('')
  setKnowledgeAnswer('')
  setKnowledgeSources([])

  try {
    const response = await fetch(
      'http://127.0.0.1:8000/rag-question',
      {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          question: knowledgeQuestion.trim(),
        }),
      }
    )

    const data = await response.json().catch(() => ({}))

    if (!response.ok) {
      throw new Error(
        data.detail ||
          `Knowledge search failed with status ${response.status}.`
      )
    }

    const result = data.data ?? {}

    setKnowledgeAnswer(
      result.answer || 'No answer was generated.'
    )

    setKnowledgeSources(result.sources ?? [])
  } catch (error) {
    setKnowledgeError(
      error instanceof Error
        ? error.message
        : 'An unexpected error occurred while searching meetings.'
    )
  } finally {
    setIsKnowledgeSearching(false)
  }
}
  if (!isAuthenticated) {
  return (
    <div className="auth-page">
      <div className="auth-card">
        <h1>MeetIQ</h1>
        <p>Turn meetings into intelligence.</p>

        <h2>
          {authMode === 'login' ? 'Welcome Back' : 'Create Your Account'}
        </h2>

        <input
          type="email"
          placeholder="Email"
          value={authEmail}
          onChange={(e) => setAuthEmail(e.target.value)}
        />

        <input
          type="password"
          placeholder="Password"
          value={authPassword}
          onChange={(e) => setAuthPassword(e.target.value)}
        />

        {authError && (
          <p className="auth-error">{authError}</p>
        )}

        <button
          className="primary-button"
          onClick={
            authMode === 'login'
              ? handleLogin
              : handleRegister
          }
          disabled={authLoading}
        >
          {authLoading
            ? 'Please wait...'
            : authMode === 'login'
              ? 'Login'
              : 'Register'}
        </button>

        <button
          className="auth-switch"
          onClick={() => {
            setAuthMode(
              authMode === 'login' ? 'register' : 'login'
            )
            setAuthError('')
          }}
        >
          {authMode === 'login'
            ? "Don't have an account? Register"
            : 'Already have an account? Login'}
        </button>
      </div>
    </div>
  )
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
                  <div className="metric-info"><span>Total Meetings</span><strong>{meetingHistory.length}</strong><small><b>↗ 12%</b> from last month</small></div>
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
              {activePage === 'Meeting Intelligence' && (
  <button
    className="primary-button"
    onClick={analyzeTranscript}
    disabled={!transcript}
  >
    Analyze Meeting
  </button>
)}
{activePage === 'Meeting History' && (
  <div className="meeting-history-list">
    {meetingHistory.length > 0 ? (
      meetingHistory.map((meeting: any) => (
       <div
  className="meeting-history-card"
  key={meeting.id}
  onClick={() => {
  loadMeetingDetails(meeting.id)
  setActivePage('Meeting Details & Analytics')
}}
>
          <h3>{meeting.filename || meeting.title || 'Untitled Meeting'}</h3>

          <p>
            {meeting.summary || 'No summary available.'}
          </p>

          <small>
            {meeting.created_at
              ? new Date(meeting.created_at).toLocaleString()
              : 'Date not available'}
          </small>
        </div>
      ))
    ) : (
      <p>No meetings found.</p>
    )}
  </div>
)}
{activePage === 'Meeting Details & Analytics' && selectedMeeting && (
  <div className="meeting-details-card">
    <h2>
      {selectedMeeting.filename ||
        selectedMeeting.title ||
        'Meeting Details'}
    </h2>

    <p>
      {selectedMeeting.created_at
        ? new Date(selectedMeeting.created_at).toLocaleString()
        : 'Date not available'}
    </p>

    <div className="analytics-grid">
      <div className="analytics-card">
        <strong>{selectedMeeting.key_points?.length || 0}</strong>
        <span>Key Points</span>
      </div>

      <div className="analytics-card">
        <strong>{selectedMeeting.decisions?.length || 0}</strong>
        <span>Decisions</span>
      </div>

      <div className="analytics-card">
        <strong>{selectedMeeting.action_items?.length || 0}</strong>
        <span>Action Items</span>
      </div>

      <div className="analytics-card">
        <strong>{selectedMeeting.participants?.length || 0}</strong>
        <span>Participants</span>
      </div>

      <div className="analytics-card">
        <strong>{selectedMeeting.deadlines?.length || 0}</strong>
        <span>Deadlines</span>
      </div>

      <div className="analytics-card">
        <strong>{selectedMeeting.priorities?.length || 0}</strong>
        <span>Priorities</span>
      </div>
    </div>

    <div className="meeting-details-section">
      <h3>📝 Summary</h3>
      <p>
        {selectedMeeting.summary || 'No summary available.'}
      </p>
    </div>

    <div className="meeting-details-section">
      <h3>🔑 Key Points</h3>

      {selectedMeeting.key_points?.length ? (
        <ul>
          {selectedMeeting.key_points.map(
            (point: string, index: number) => (
              <li key={index}>{point}</li>
            )
          )}
        </ul>
      ) : (
        <p>No key points identified.</p>
      )}
    </div>

    <div className="meeting-details-section">
      <h3>📌 Action Items</h3>

      {selectedMeeting.action_items?.length ? (
        <ul>
          {selectedMeeting.action_items.map(
            (item: any, index: number) => (
              <li key={index}>
                <strong>
                  {item.task || 'Task not specified'}
                </strong>

                <br />
                Assigned to:{' '}
                {item.assigned_to || 'Not specified'}

                <br />
                Deadline:{' '}
                {item.deadline || 'Not specified'}

                <br />
                Priority:{' '}
                {item.priority || 'Medium'}

                <br />
                Status:{' '}
                {item.status || 'Pending'}
              </li>
            )
          )}
        </ul>
      ) : (
        <p>No action items identified.</p>
      )}
    </div>

    <div className="meeting-details-section">
      <h3>🎙️ Transcript</h3>

      <p className="meeting-transcript">
        {selectedMeeting.transcript ||
          'No transcript available.'}
      </p>
    </div>

    <button
      className="primary-button"
      onClick={() => {
        setSelectedMeeting(null)
        setActivePage('Meeting History')
        loadMeetingHistory()
      }}
    >
      ← Back to Meeting History
    </button>
  </div>
)}
              <span className="eyebrow">MEETIQ WORKSPACE</span>
              <h1>{activePage}</h1>
             {activePage === 'Transcription Accuracy Testing' && (
  <div className="accuracy-page">
    <div className="accuracy-page-header">
      <span className="eyebrow">MEETIQ WORKSPACE</span>

      <h1>Transcription Accuracy Testing</h1>

      <p>
        Compare the generated transcript with the reference transcript
        to evaluate transcription accuracy.
      </p>
    </div>

    {/* Reference Transcript */}
    <div className="accuracy-card">
      <div className="accuracy-card-header">
        <div className="accuracy-icon">▤</div>

        <div>
          <h2>Reference Transcript</h2>
          <p>Enter the correct/reference transcript here.</p>
        </div>

        <span className="character-count">
          {referenceTranscript.length}/5000 characters
        </span>
      </div>

      <textarea
        className="accuracy-textarea"
        value={referenceTranscript}
        onChange={(e) => setReferenceTranscript(e.target.value)}
        placeholder="Enter the correct/reference transcript..."
        rows={6}
        maxLength={5000}
      />
    </div>

    {/* Accuracy Button */}
    <div className="accuracy-button-wrapper">
      <button
        className="accuracy-check-button"
        onClick={checkTranscriptionAccuracy}
        disabled={
          !referenceTranscript.trim() ||
          !transcript.trim() ||
          isCheckingAccuracy
        }
      >
        <span>◎</span>

        {isCheckingAccuracy
          ? 'Checking Accuracy...'
          : 'Check Transcription Accuracy'}
      </button>
    </div>

    {/* Generated Transcript */}
    <div className="accuracy-card">
      <div className="accuracy-card-header">
        <div className="accuracy-icon generated">▤</div>

        <div>
          <h2>Generated Transcript</h2>
          <p>The transcript generated by the system will be shown here.</p>
        </div>
      </div>

      <textarea
        className="accuracy-textarea"
        value={transcript}
        readOnly
        placeholder="Generate a transcript first..."
        rows={6}
      />
    </div>

    {/* Error */}
    {accuracyError && (
      <div className="accuracy-error">
        {accuracyError}
      </div>
    )}

    {/* Accuracy Result */}
    {accuracyResult !== null && (
      <div className="accuracy-result-card">
        <div className="accuracy-result-header">
          <div className="accuracy-result-icon">▥</div>

          <div>
            <h2>Accuracy Result</h2>
            <p>
              The transcription accuracy compared to the reference
              transcript.
            </p>
          </div>
        </div>

        <div className="accuracy-result-value">
          <span>Transcription Accuracy:</span>

          <strong>
            {typeof accuracyResult === 'number'
              ? accuracyResult.toFixed(2)
              : accuracyResult.accuracy !== undefined
                ? Number(accuracyResult.accuracy).toFixed(2)
                : '—'}
            %
          </strong>
        </div>
      </div>
    )}
  </div>
)}
              {activePage === 'Meeting Intelligence' && (
  <button
    className="primary-button"
    onClick={analyzeTranscript}
    disabled={!transcript}
  >
    Analyze Meeting
  </button>
)}
{activePage === 'Decisions' && (
  <div className="meeting-details-card">
    <h2>Decisions</h2>

    {selectedMeeting?.decisions?.length ? (
      <ul>
        {selectedMeeting.decisions.map(
          (decision: string, index: number) => (
            <li key={index}>{decision}</li>
          )
        )}
      </ul>
    ) : (
      <p>No decisions identified for this meeting.</p>
    )}
  </div>
)}
{activePage === 'Participants & Responsibilities' && (
  <div className="meeting-details-card">
    <h2>Participants & Responsibilities</h2>

    {selectedMeeting?.participants?.length ? (
      <ul>
        {selectedMeeting.participants.map(
          (participant: any, index: number) => (
            <li key={index}>
              <strong>{participant.name}</strong>

              {participant.role && (
                <>
                  <br />
                  Role: {participant.role}
                </>
              )}

              {participant.responsibilities?.length > 0 && (
                <>
                  <br />
                  Responsibilities:
                  <ul>
                    {participant.responsibilities.map(
                      (responsibility: string, responsibilityIndex: number) => (
                        <li key={responsibilityIndex}>
                          {responsibility}
                        </li>
                      )
                    )}
                  </ul>
                </>
              )}
            </li>
          )
        )}
      </ul>
    ) : (
      <p>No participants identified for this meeting.</p>
    )}
  </div>
)}
{activePage === 'Deadlines' && (
  <div className="meeting-details-card">
    <h2>Deadlines</h2>

    {selectedMeeting?.deadlines?.length ? (
      <ul>
        {selectedMeeting.deadlines.map(
          (deadline: string, index: number) => (
            <li key={index}>{deadline}</li>
          )
        )}
      </ul>
    ) : (
      <p>No deadlines identified for this meeting.</p>
    )}
  </div>
)}
{activePage === 'Priorities' && (
  <div className="meeting-details-card">
    <h2>Priorities</h2>

    {selectedMeeting?.priorities?.length ? (
      <ul>
        {selectedMeeting.priorities.map(
          (priority: string, index: number) => (
            <li key={index}>{priority}</li>
          )
        )}
      </ul>
    ) : (
      <p>No priorities identified for this meeting.</p>
    )}
  </div>
)}
{activePage === 'Knowledge Search' && (
  <div className="knowledge-search-panel">

    <div className="knowledge-search-intro">
      <div className="knowledge-icon">🔎</div>

      <div>
        <h2>Ask Your Meeting Assistant</h2>
        <p>
          Search across your meeting transcripts and extracted knowledge
          using AI-powered semantic search.
        </p>
      </div>
    </div>

    <div className="knowledge-question-card">

      <div className="knowledge-question-header">
        <div className="knowledge-question-icon">🤖</div>

        <div>
          <h3>Ask a question about your meetings</h3>
          <p>
            Example: What decisions were made in the meetings?
          </p>
        </div>
      </div>

      <textarea
        className="knowledge-question-input"
        value={knowledgeQuestion}
        onChange={(event) =>
          setKnowledgeQuestion(event.target.value)
        }
        placeholder="Type your question here..."
        rows={6}
      />

      <div className="knowledge-action-row">
        <button
          className="primary-button knowledge-ask-button"
          onClick={askKnowledgeQuestion}
          disabled={isKnowledgeSearching}
        >
          {isKnowledgeSearching
            ? 'Searching...'
            : '🤖 Ask AI Assistant'}
        </button>
      </div>

    </div>

    {knowledgeError && (
      <div className="knowledge-error">
        {knowledgeError}
      </div>
    )}

    {knowledgeAnswer && (
      <div className="knowledge-results">

        <div className="knowledge-result-card">
          <div className="knowledge-result-header">
            <span className="knowledge-result-icon">💡</span>

            <div>
              <h3>AI Answer</h3>
              <p>Answer generated from your processed meetings.</p>
            </div>
          </div>

          <div className="knowledge-answer">
            {knowledgeAnswer}
          </div>
        </div>

        {knowledgeSources.length > 0 && (
          <div className="knowledge-result-card">

            <div className="knowledge-result-header">
              <span className="knowledge-result-icon">📚</span>

              <div>
                <h3>Source Meetings</h3>
                <p>Meetings used to generate this answer.</p>
              </div>
            </div>

            <ul className="knowledge-source-list">
              {knowledgeSources.map(
                (source: any, index: number) => (
                  <li key={index}>
                    {source.filename ||
                      source.title ||
                      `Meeting ${source.meeting_id || index + 1}`}
                  </li>
                )
              )}
            </ul>

          </div>
        )}

      </div>
    )}

  </div>
)}
              {activePage === 'Zoom Integration' && (
  <div className="meeting-details-card">
    <h2>🎥 Zoom Integration</h2>

    <p>
      Connect to your Zoom meeting recordings and process them through MeetIQ.
    </p>

    <button
      className="primary-button"
      onClick={loadZoomRecordings}
      disabled={isZoomLoading}
    >
      {isZoomLoading
        ? 'Connecting to Zoom...'
        : '🔗 Connect to Zoom'}
    </button>

    {zoomError && (
      <p className="selected-file">
        {zoomError}
      </p>
    )}

    {zoomRecordings.length > 0 ? (
      <div className="meeting-intelligence-content">
        <div className="intelligence-section">
          <h3>🎥 Zoom Recordings</h3>

          <ul>
            {zoomRecordings.map(
              (recording: any, index: number) => (
                <li key={index}>
                  {recording.filename ||
                    recording.title ||
                    recording.id ||
                    `Recording ${index + 1}`}
                </li>
              )
            )}
          </ul>
        </div>
      </div>
    ) : (
      <p className="selected-file">
        No Zoom recordings available yet.
      </p>
    )}
  </div>
)}
<button
  className="secondary-button back-button"
  onClick={() => choosePage('Dashboard')}
>
  ← Back to Dashboard
</button>

<input
  ref={fileInput}
  className="hidden-input"
  type="file"
  accept="audio/*,video/*,.mp3,.wav,.m4a,.mp4,.mov,.avi,.mkv,.flac,.aac"
  onChange={onFileSelected}
/>

{/* Generate Transcript */}
{activePage === 'Generate Transcript' && selectedFile && (
  <>
    <p className="selected-file">
      Selected file: {selectedFile}
    </p>

    <button
      className="primary-button"
      onClick={transcribeSelectedFile}
      disabled={isTranscribing}
    >
      {isTranscribing ? 'Transcribing...' : 'Generate Transcript'}
    </button>
  </>
)}

{/* Transcription Error */}
{activePage === 'Generate Transcript' && transcriptionError && (
  <p className="selected-file">
    {transcriptionError}
  </p>
)}

{/* Transcript Result */}
{activePage === 'Generate Transcript' && transcript && (
  <div className="transcript-result">
    <h2>Transcript</h2>
    <p>{transcript}</p>
  </div>
)}

{/* Meeting Intelligence */}
{activePage === 'Meeting Intelligence' && meetingIntelligence && (
  <div className="transcript-result">
    <h2>Meeting Intelligence Result</h2>

    <div className="meeting-intelligence-content">

      {/* Summary */}
      <div className="intelligence-section">
        <h3>📝 Summary</h3>
        <p>
          {meetingIntelligence.data?.summary ||
            'No summary available.'}
        </p>
      </div>

      {/* Key Points */}
      <div className="intelligence-section">
        <h3>🔑 Key Points</h3>

        {meetingIntelligence.data?.key_points?.length ? (
          <ul>
            {meetingIntelligence.data.key_points.map(
              (point: string, index: number) => (
                <li key={index}>{point}</li>
              )
            )}
          </ul>
        ) : (
          <p>No key points available.</p>
        )}
      </div>

      {/* Decisions */}
      <div className="intelligence-section">
        <h3>✅ Decisions</h3>

        {meetingIntelligence.data?.decisions?.length ? (
          <ul>
            {meetingIntelligence.data.decisions.map(
              (decision: string, index: number) => (
                <li key={index}>{decision}</li>
              )
            )}
          </ul>
        ) : (
          <p>No decisions identified.</p>
        )}
      </div>

      {/* Action Items */}
      <div className="intelligence-section">
        <h3>📌 Action Items</h3>

        {meetingIntelligence.data?.action_items?.length ? (
          <ul>
            {meetingIntelligence.data.action_items.map(
              (item: any, index: number) => (
                <li key={index}>
                  <strong>{item.task}</strong>
                  <br />
                  Assigned to:{' '}
                  {item.assigned_to || 'Not specified'}
                  <br />
                  Deadline:{' '}
                  {item.deadline || 'Not specified'}
                  <br />
                  Priority:{' '}
                  {item.priority || 'Medium'}
                  <br />
                  Status:{' '}
                  {item.status || 'Pending'}
                </li>
              )
            )}
          </ul>
        ) : (
          <p>No action items identified.</p>
        )}
      </div>

      {/* Participants */}
      <div className="intelligence-section">
        <h3>👥 Participants</h3>

        {meetingIntelligence.data?.participants?.length ? (
          <ul>
            {meetingIntelligence.data.participants.map(
              (participant: any, index: number) => (
                <li key={index}>
                  <strong>{participant.name}</strong>

                  {participant.role && (
                    <>
                      {' — '}
                      {participant.role}
                    </>
                  )}
                </li>
              )
            )}
          </ul>
        ) : (
          <p>No participants identified.</p>
        )}
      </div>

      {/* Deadlines */}
      <div className="intelligence-section">
        <h3>📅 Deadlines</h3>

        {meetingIntelligence.data?.deadlines?.length ? (
          <ul>
            {meetingIntelligence.data.deadlines.map(
              (deadline: string, index: number) => (
                <li key={index}>{deadline}</li>
              )
            )}
          </ul>
        ) : (
          <p>No deadlines identified.</p>
        )}
      </div>

      {/* Priorities */}
      <div className="intelligence-section">
        <h3>🔥 Priorities</h3>

        {meetingIntelligence.data?.priorities?.length ? (
          <ul>
            {meetingIntelligence.data.priorities.map(
              (priority: string, index: number) => (
                <li key={index}>{priority}</li>
              )
            )}
          </ul>
        ) : (
          <p>No priorities identified.</p>
        )}
      </div>

    </div>
  </div>
)}

</section>
          )}
        </div>
      </main>
    </div>
  )
}

export default App