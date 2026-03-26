import { NavLink } from 'react-router-dom';
import { useStore } from '../store/useStore';

export function Sidebar() {
  const projects = useStore(state => state.projects);
  const activeProject = useStore(state => state.activeProject);
  const primaryProject = activeProject || projects[0] || null;
  const projectHref = primaryProject ? `/projects/${primaryProject.id}` : '/';
  const uploadHref = primaryProject ? `/projects/${primaryProject.id}/upload` : '/';
  const recentProjects = projects.slice(0, 5);
  const datasetCount = primaryProject?.datasets?.length || 0;

  const navItems = [
    {
      to: '/',
      label: 'Projects',
      meta: 'Workspace registry',
      icon: (
        <svg viewBox="0 0 24 24" aria-hidden="true">
          <rect x="3" y="3" width="7" height="7" rx="1.5" />
          <rect x="14" y="3" width="7" height="7" rx="1.5" />
          <rect x="3" y="14" width="7" height="7" rx="1.5" />
          <rect x="14" y="14" width="7" height="7" rx="1.5" />
        </svg>
      ),
    },
    {
      to: projectHref,
      label: 'Workspace',
      meta: primaryProject ? 'Current project context' : 'Select a project first',
      icon: (
        <svg viewBox="0 0 24 24" aria-hidden="true">
          <path d="M4 6.5h16v11H4z" />
          <path d="M8 6.5V5a1 1 0 0 1 1-1h6a1 1 0 0 1 1 1v1.5" />
        </svg>
      ),
    },
    {
      to: uploadHref,
      label: 'Upload + Setup',
      meta: primaryProject ? 'Dataset intake and launch' : 'Create a workspace to continue',
      icon: (
        <svg viewBox="0 0 24 24" aria-hidden="true">
          <path d="M12 16V4" />
          <path d="m7.5 8.5 4.5-4.5 4.5 4.5" />
          <path d="M4 19.5h16" />
        </svg>
      ),
    },
  ];

  return (
    <aside className="sidebar" aria-label="Navigazione principale">
      <div className="sidebar__brand">
        <div className="sidebar__brand-mark">D</div>
        <div>
          <div className="sidebar__brand-name">DAREEDA</div>
          <p className="sidebar__brand-tagline">Executive-grade analytical delivery</p>
        </div>
      </div>

      <div className="sidebar__dataset-card">
        <div className="sidebar__dataset-icon">
          <svg viewBox="0 0 24 24" aria-hidden="true">
            <ellipse cx="12" cy="6" rx="7" ry="3" />
            <path d="M5 6v6c0 1.7 3.1 3 7 3s7-1.3 7-3V6" />
            <path d="M5 12v6c0 1.7 3.1 3 7 3s7-1.3 7-3v-6" />
          </svg>
        </div>
        <div className="sidebar__dataset-copy">
          <span className="sidebar__dataset-label">Active Workspace</span>
          <strong className="sidebar__dataset-name">
            {primaryProject?.name || 'No workspace selected'}
          </strong>
          <span className="sidebar__dataset-meta">
            {primaryProject
              ? `${datasetCount} dataset${datasetCount === 1 ? '' : 's'} tracked`
              : 'Create a project to start a new analysis'}
          </span>
        </div>
      </div>

      <nav className="sidebar__nav" aria-label="Menu principale">
        <span className="sidebar__section-title">Workbench</span>
        {navItems.map(item => (
          <NavLink
            key={item.label}
            to={item.to}
            className={({ isActive }) => `sidebar__item${isActive ? ' sidebar__item--active' : ''}`}
          >
            <span className="sidebar__item-icon" aria-hidden="true">{item.icon}</span>
            <span className="sidebar__item-copy">
              <span className="sidebar__item-text">{item.label}</span>
              <span className="sidebar__item-meta">{item.meta}</span>
            </span>
          </NavLink>
        ))}
      </nav>

      {recentProjects.length > 0 && (
        <div className="sidebar__section">
          <span className="sidebar__section-title">Progetti recenti</span>
          <ul className="sidebar__projects" aria-label="Progetti">
            {recentProjects.map(project => (
              <li key={project.id}>
                <NavLink
                  to={`/projects/${project.id}`}
                  className={({ isActive }) => `sidebar__item sidebar__item--sub${isActive ? ' sidebar__item--active' : ''}`}
                  title={project.name}
                >
                  <span className="sidebar__proj-dot" aria-hidden="true" />
                  <span className="sidebar__item-copy">
                    <span className="sidebar__item-text sidebar__proj-name">{project.name}</span>
                    <span className="sidebar__item-meta">
                      {project.description || 'No description provided'}
                    </span>
                  </span>
                </NavLink>
              </li>
            ))}
          </ul>
        </div>
      )}

      <div className="sidebar__footer-card">
        <span className="sidebar__footer-label">Delivery Scope</span>
        <strong className="sidebar__footer-title">All outputs, no missing sections</strong>
        <p className="sidebar__footer-text">
          Workspace, upload, analysis and reporting stay aligned to the enterprise report structure.
        </p>
      </div>
    </aside>
  );
}
