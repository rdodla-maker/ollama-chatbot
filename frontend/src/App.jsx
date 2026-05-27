import { useEffect, useState } from 'react'
import Sidebar from './components/Sidebar'
import Dashboard from './pages/Dashboard'
import JobApplications from './pages/JobApplications'
import ResumeAnalyzer from './pages/ResumeAnalyzer'
import CoverLetterGenerator from './pages/CoverLetterGenerator'
import ApplicationTracker from './pages/ApplicationTracker'
import StartApply from './pages/StartApply'
import { getHealth } from './api/api'

const PAGE_COMPONENTS = {
	dashboard: Dashboard,
	applications: JobApplications,
    'start-apply': StartApply,
	resume: ResumeAnalyzer,
	'cover-letter': CoverLetterGenerator,
	tracker: ApplicationTracker,
}

export default function App() {
	const [page, setPage] = useState('dashboard')
	const [collapsed, setCollapsed] = useState(false)
	const [status, setStatus] = useState({ online: false, label: 'Checking...' })
	const [latestResult, setLatestResult] = useState(null)
	const [trackerItems, setTrackerItems] = useState([])

	useEffect(() => {
		let mounted = true
		getHealth()
			.then(() => {
				if (mounted) setStatus({ online: true, label: 'Backend online' })
			})
			.catch(() => {
				if (mounted) setStatus({ online: false, label: 'Backend offline' })
			})
		return () => {
			mounted = false
		}
	}, [])

	const ActivePage = PAGE_COMPONENTS[page]

	return (
		<div className="dashboard-shell">
			<Sidebar
				status={status}
				page={page}
				onNavigate={setPage}
				collapsed={collapsed}
				onToggle={() => setCollapsed((value) => !value)}
			/>

			<main className="dashboard-main page-transition">
				<ActivePage
					status={status}
					latestResult={latestResult}
					trackerItems={trackerItems}
					onNavigate={setPage}
					onGenerated={(result) => {
						setLatestResult(result)
						setPage('cover-letter')
					}}
					onTrackerLoaded={setTrackerItems}
				/>
			</main>
		</div>
	)
}

