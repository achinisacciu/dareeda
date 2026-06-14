import {
  useRef, useState, useCallback,
  type DragEvent, type ChangeEvent,
} from 'react'
import { useAnalysisStore } from '@/stores/analysisStore'
import { useUIStore } from '@/stores/uiStore'
import { Button } from '@/components/ui/Button'
import { Badge } from '@/components/ui/Badge'
import { Card, CardBody } from '@/components/ui/Card'
import type { ProjectSummary } from '@/api/analysis'
import { UploadCloud, FileText, Trash2, ChevronRight, FolderArchive, ArrowRight } from 'lucide-react'

// ── Helpers ───────────────────────────────────────────────────────────────────

const ACCEPTED_EXTENSIONS = ['.csv', '.parquet', '.pq']

function isAccepted(file: File): boolean {
  const name = file.name.toLowerCase()
  return ACCEPTED_EXTENSIONS.some((ext) => name.endsWith(ext))
}

function formatDate(iso: string): string {
  try {
    return new Intl.DateTimeFormat('it-IT', { day: '2-digit', month: 'short', year: 'numeric' }).format(new Date(iso))
  } catch {
    return iso
  }
}

function formatRows(n: number | null): string {
  if (n == null) return '—'
  if (n >= 1_000_000) return `${(n / 1_000_000).toFixed(1)}M`
  if (n >= 1_000) return `${(n / 1_000).toFixed(0)}K`
  return n.toLocaleString('it-IT')
}

// ── UploadProgressBar ─────────────────────────────────────────────────────────

function UploadProgressBar({ pct }: { pct: number }) {
  return (
    <div className="flex items-center gap-4 w-full" role="progressbar" aria-valuenow={pct} aria-valuemin={0} aria-valuemax={100}>
      <div className="flex-1 h-2 rounded-full bg-neutral-200 overflow-hidden">
        <div
          className="h-full rounded-full bg-[--color-primary] transition-all duration-300"
          style={{ width: `${pct}%` }}
        />
      </div>
      <span className="text-xs font-bold tabular-nums text-[--color-primary] w-8 text-right shrink-0">
        {pct}%
      </span>
    </div>
  )
}

// ── DropZone ──────────────────────────────────────────────────────────────────

interface DropZoneProps {
  onFile: (file: File) => void
  isUploading: boolean
  uploadPct: number
  uploadError: boolean
}

function DropZone({ onFile, isUploading, uploadPct, uploadError }: DropZoneProps) {
  const inputRef   = useRef<HTMLInputElement>(null)
  const [isDragging, setIsDragging] = useState(false)

  const handleFile = useCallback((file: File | undefined) => {
    if (!file || !isAccepted(file)) return
    onFile(file)
  }, [onFile])

  function onDragOver(e: DragEvent) {
    e.preventDefault()
    setIsDragging(true)
  }

  function onDragLeave(e: DragEvent) {
    if (!e.currentTarget.contains(e.relatedTarget as Node)) setIsDragging(false)
  }

  function onDrop(e: DragEvent) {
    e.preventDefault()
    setIsDragging(false)
    handleFile(e.dataTransfer.files[0])
  }

  function onInputChange(e: ChangeEvent<HTMLInputElement>) {
    handleFile(e.target.files?.[0])
    e.target.value = ''
  }

  return (
    <div
      onDragOver={onDragOver}
      onDragEnter={onDragOver}
      onDragLeave={onDragLeave}
      onDrop={onDrop}
      className={`
        relative rounded-2xl border-2 border-dashed
        flex flex-col items-center justify-center gap-4
        px-8 py-16 text-center
        transition-all duration-200
        ${isUploading
          ? 'border-[--color-primary] bg-[--color-primary]/5 pointer-events-none'
          : uploadError
          ? 'border-[--color-error] bg-[--color-error]/5'
          : isDragging
          ? 'border-[--color-primary] bg-[--color-primary]/5'
          : 'border-neutral-300 bg-white hover:border-[--color-primary] hover:shadow-md cursor-pointer'
        }
      `}
      onClick={() => !isUploading && inputRef.current?.click()}
    >
      <input
        ref={inputRef}
        type="file"
        accept={ACCEPTED_EXTENSIONS.join(',')}
        className="sr-only"
        onChange={onInputChange}
        aria-label="Carica file"
      />

      <div className={`
        flex items-center justify-center w-16 h-16 rounded-full mb-2
        ${isUploading || isDragging
          ? 'bg-[--color-primary] text-white'
          : uploadError
          ? 'bg-[--color-error] text-white'
          : 'bg-neutral-100 text-[--color-primary]'
        }
      `}>
        <UploadCloud className="w-8 h-8" />
      </div>

      <div className="flex flex-col gap-1.5 items-center">
        {isUploading ? (
          <p className="text-lg font-bold font-headline text-[--color-primary]">
            Caricamento in corso…
          </p>
        ) : uploadError ? (
          <p className="text-lg font-bold font-headline text-[--color-error]">
            Upload fallito — riprova
          </p>
        ) : (
          <>
            <p className="text-xl font-bold font-headline text-[--color-on-surface]">
              {isDragging ? 'Rilascia il file qui' : 'Trascina e rilascia il dataset'}
            </p>
            <p className="text-sm font-medium text-neutral-500">
              oppure clicca per sfogliare
            </p>
          </>
        )}
        <p className="text-xs font-bold uppercase tracking-widest text-neutral-400 mt-2">
          CSV, Parquet — max 500 MB
        </p>
      </div>

      {isUploading && (
        <div className="w-full max-w-md mt-4">
          <UploadProgressBar pct={uploadPct} />
        </div>
      )}
    </div>
  )
}

// ── ProjectCard ───────────────────────────────────────────────────────────────

interface ProjectCardProps {
  project:    ProjectSummary
  isCurrent:  boolean
  onSelect:   (project: ProjectSummary) => void
  onDelete:   (project: ProjectSummary) => void
  isLoading:  boolean
}

function ProjectCard({ project, isCurrent, onSelect, onDelete, isLoading }: ProjectCardProps) {
  const ext = project.filename.split('.').pop()?.toLowerCase() ?? 'file'

  return (
    <Card
      variant="default"
      interactive
      selected={isCurrent}
      onClick={() => onSelect(project)}
      className="group hover:border-[--color-primary] transition-colors"
    >
      <CardBody>
        <div className="flex flex-col gap-4">
          <div className="flex items-start justify-between gap-2">
            <div className="flex items-center gap-3 min-w-0">
              <div className="shrink-0 flex items-center justify-center w-10 h-10 rounded-lg bg-neutral-100 text-[--color-primary]">
                <FileText className="w-5 h-5" />
              </div>
              <p className="text-sm font-bold font-headline text-[--color-on-surface] truncate leading-tight" title={project.filename}>
                {project.filename}
              </p>
            </div>
            <button
              aria-label={`Elimina ${project.filename}`}
              onClick={(e) => { e.stopPropagation(); onDelete(project) }}
              className={`
                shrink-0 flex items-center justify-center w-8 h-8 rounded-md
                text-neutral-400 hover:text-[--color-error] hover:bg-neutral-100
                opacity-0 group-hover:opacity-100 transition-all
              `}
            >
              <Trash2 className="w-4 h-4" />
            </button>
          </div>

          <div className="flex flex-wrap items-center gap-x-3 gap-y-2">
            <span className="text-xs font-mono font-medium text-neutral-500 bg-neutral-100 px-2 py-1 rounded">
              {formatRows(project.n_rows)} × {project.n_cols ?? '—'}
            </span>
            <Badge variant="muted" size="sm">{ext.toUpperCase()}</Badge>
            {project.has_result && <Badge variant="success" size="sm" dot>Analizzato</Badge>}
          </div>

          <div className="flex items-center justify-between gap-2 mt-2 pt-4 border-t border-neutral-100">
            <span className="text-xs font-medium text-neutral-400">
              {formatDate(project.created_at)}
            </span>
            <span className={`
              flex items-center gap-1 text-xs font-bold uppercase tracking-widest
              ${isCurrent ? 'text-[--color-primary]' : 'text-neutral-400'}
              opacity-0 group-hover:opacity-100 transition-opacity
            `}>
              {isLoading ? 'Apertura…' : project.has_result ? 'Apri analisi' : 'Avvia analisi'}
              <ChevronRight className="w-4 h-4" />
            </span>
          </div>
        </div>
      </CardBody>
    </Card>
  )
}

// ── ProjectsList ──────────────────────────────────────────────────────────────

interface ProjectsListProps {
  projects:        ProjectSummary[]
  currentId:       string | null
  loadingId:       string | null
  onSelect:        (project: ProjectSummary) => void
  onDelete:        (project: ProjectSummary) => void
}

function ProjectsList({ projects, currentId, loadingId, onSelect, onDelete }: ProjectsListProps) {
  if (projects.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center p-16 border border-dashed border-neutral-300 rounded-2xl bg-white/50">
        <FolderArchive className="w-16 h-16 text-neutral-300 mb-4" />
        <h3 className="text-xl font-bold font-headline text-neutral-600 mb-2">Nessun progetto</h3>
        <p className="text-sm font-medium text-neutral-400 text-center max-w-sm">
          Carica il tuo primo file CSV o Parquet utilizzando l'area qui sopra per iniziare.
        </p>
      </div>
    )
  }

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-3 2xl:grid-cols-4 gap-6">
      {projects.map((p) => (
        <ProjectCard
          key={p.id}
          project={p}
          isCurrent={p.id === currentId}
          isLoading={p.id === loadingId}
          onSelect={onSelect}
          onDelete={onDelete}
        />
      ))}
    </div>
  )
}

// ╔══════════════════════════════════════════════════════════════════════════╗
// ║  UploadPage                                                              ║
// ╚══════════════════════════════════════════════════════════════════════════╝

export default function UploadPage() {
  const projects        = useAnalysisStore((s) => s.projects)
  const currentProject  = useAnalysisStore((s) => s.currentProject)
  const uploadStatus    = useAnalysisStore((s) => s.uploadStatus)
  const uploadProgress  = useAnalysisStore((s) => s.uploadProgress)
  const uploadFile      = useAnalysisStore((s) => s.uploadFile)
  const selectProject   = useAnalysisStore((s) => s.selectProject)
  const openModal       = useUIStore((s) => s.openModal)
  const setActivePage   = useUIStore((s) => s.setActivePage)

  const [loadingId, setLoadingId] = useState<string | null>(null)

  async function handleFile(file: File) {
    try {
      await uploadFile(file)
      setActivePage('analysis')
    } catch {
      // Handled in store
    }
  }

  async function handleSelectProject(project: ProjectSummary) {
    if (loadingId) return
    setLoadingId(project.id)
    try {
      await selectProject(project.id)
      setActivePage('analysis')
    } catch {
      // Handled in store
    } finally {
      setLoadingId(null)
    }
  }

  function handleDeleteProject(project: ProjectSummary) {
    openModal('delete_project', { projectId: project.id, filename: project.filename })
  }

  const isUploading = uploadStatus === 'uploading'
  const uploadError = uploadStatus === 'error'

  return (
    <div className="h-full overflow-y-auto bg-[--color-surface-container-lowest]">
      <div className="max-w-[1400px] mx-auto px-8 py-12 flex flex-col gap-12 animate-fade-in">
        
        {/* Page Header */}
        <div className="flex items-center gap-3">
          <div className="w-1.5 h-10 bg-[--color-primary] rounded-full"></div>
          <div>
            <h1 className="text-3xl font-bold font-headline text-[--color-on-surface] tracking-tight">
              Dataset Upload
            </h1>
            <p className="text-sm font-bold uppercase tracking-widest text-neutral-400 mt-1">
              Workspace Inizialization
            </p>
          </div>
        </div>

        {/* Drop zone */}
        <DropZone
          onFile={handleFile}
          isUploading={isUploading}
          uploadPct={uploadProgress}
          uploadError={uploadError}
        />

        {/* Projects list */}
        <section aria-labelledby="projects-heading" className="mt-4">
          <div className="flex items-center justify-between mb-6">
            <h2 id="projects-heading" className="text-xl font-bold font-headline text-[--color-on-surface]">
              Progetti Recenti
              {projects.length > 0 && (
                <span className="text-[--color-primary] ml-2 font-black">{projects.length}</span>
              )}
            </h2>
            <Button variant="ghost" className="text-[--color-primary] text-xs font-bold tracking-widest uppercase">
              Visualizza Tutti <ArrowRight className="w-4 h-4 ml-1" />
            </Button>
          </div>

          <ProjectsList
            projects={projects}
            currentId={currentProject?.id ?? null}
            loadingId={loadingId}
            onSelect={handleSelectProject}
            onDelete={handleDeleteProject}
          />
        </section>

      </div>
    </div>
  )
}

