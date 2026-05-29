import { useEffect, useState } from 'react'
import Sidebar from './components/Sidebar'
import Dashboard from './pages/Dashboard'
import ApplicationTracker from './pages/ApplicationTracker'
import StartApply from './pages/StartApply'
import SettingsPage from './pages/SettingsPage'
import { getHealth } from './api/api'
import { fetchTrackerItems } from './services/trackerService'

const PAGE_COMPONENTS = {
	dashboard: Dashboard,
	applications: ApplicationTracker,
	resume: StartApply,
	settings: SettingsPage,
}

export default function App() {
	const [page, setPage] = useState(() => {
		// Restore last visited page from localStorage
		const savedPage = localStorage.getItem('currentPage')
		return savedPage && PAGE_COMPONENTS[savedPage] ? savedPage : 'dashboard'
	})
	const [collapsed, setCollapsed] = useState(false)
	const [status, setStatus] = useState({ online: false, label: 'Checking status...' })
	const [trackerItems, setTrackerItems] = useState([])

	// Persist page changes to localStorage
	useEffect(() => {
		localStorage.setItem('currentPage', page)
	}, [page])

	useEffect(() => {
		let mounted = true
		getHealth()
			.then(() => {
				if (mounted) setStatus({ online: true, label: 'Ready' })
			})
			.catch(() => {
				if (mounted) setStatus({ online: false, label: 'Offline' })
			})
		return () => {
			mounted = false
		}
	}, [])

	useEffect(() => {
		let mounted = true

		fetchTrackerItems()
			.then((items) => {
				if (mounted) setTrackerItems(items)
			})
			.catch(() => {
				if (mounted) setTrackerItems([])
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
					trackerItems={trackerItems}
					onNavigate={setPage}
					onTrackerLoaded={setTrackerItems}
				/>
			</main>
		</div>
	)
}

