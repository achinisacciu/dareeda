function PageSkeleton() {
  return (
    <div className="h-full flex flex-col gap-[--space-4] p-[--space-6] animate-pulse">
      <div className="skeleton skeleton-heading w-48" />
      <div className="grid grid-cols-3 gap-[--space-3]">
        {Array.from({ length: 6 }).map((_, i) => (
          <div key={i} className="skeleton h-20 rounded-[--radius-lg]" />
        ))}
      </div>
      <div className="skeleton flex-1 rounded-[--radius-lg]" />
    </div>
  )
}

export default PageSkeleton
