import { useRef } from 'react'

export function ToastContainer() {
  const containerRef = useRef<HTMLDivElement>(null)

  return (
    <div ref={containerRef} className="fixed inset-0 z-[200] flex flex-col items-end justify-start gap-2 p-4 pointer-events-none">
    </div>
  )
}