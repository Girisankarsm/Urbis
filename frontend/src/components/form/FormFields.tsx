import { useEffect, useRef, useState, type DragEvent, type ReactNode } from 'react'

import { CameraDoodleIcon } from './FormIcons'

export function PhotoUploadZone({
  preview,
  onFileSelect,
  onRemove,
}: {
  preview: string | null
  onFileSelect: (file: File) => void
  onRemove: () => void
}) {
  const inputRef = useRef<HTMLInputElement>(null)
  const [dragOver, setDragOver] = useState(false)

  const pickFile = (file: File | undefined) => {
    if (!file || !file.type.startsWith('image/')) return
    onFileSelect(file)
  }

  const onDrop = (e: DragEvent) => {
    e.preventDefault()
    setDragOver(false)
    pickFile(e.dataTransfer.files[0])
  }

  return (
    <div
      className={`form-upload-zone relative rounded-[1.25rem] border-2 border-dashed p-[clamp(1rem,3vw,1.5rem)] text-center transition-colors duration-200 ease-out ${
        dragOver
          ? 'border-civic-400/70 bg-civic-50/60'
          : 'border-stone-200/90 bg-stone-50/40 hover:border-civic-300/50'
      }`}
      onDragOver={(e) => {
        e.preventDefault()
        setDragOver(true)
      }}
      onDragLeave={() => setDragOver(false)}
      onDrop={onDrop}
    >
      {preview ? (
        <div className="form-upload-preview">
          <img src={preview} alt="Issue preview" className="max-h-52 mx-auto rounded-[1rem] mb-4 object-cover" />
          <button
            type="button"
            onClick={onRemove}
            className="text-sm text-slate-500 hover:text-red-600 transition-colors duration-200 underline-offset-2 hover:underline"
          >
            Remove
          </button>
        </div>
      ) : (
        <div className="py-6 sm:py-8">
          <CameraDoodleIcon className="w-12 h-10 mx-auto mb-4 text-civic-500/60" />
          <p className="text-slate-500 text-sm mb-1">Drag a photo here, or choose one below</p>
          <p className="text-slate-400 text-xs">Upload a photo</p>
        </div>
      )}

      <input
        ref={inputRef}
        type="file"
        accept="image/*"
        capture="environment"
        className="sr-only"
        onChange={(e) => pickFile(e.target.files?.[0])}
      />

      <button
        type="button"
        onClick={() => inputRef.current?.click()}
        className="form-btn-secondary mt-4 inline-flex items-center justify-center min-h-[44px] px-5 py-2 rounded-[1rem] text-sm font-medium text-civic-700"
      >
        Choose file
      </button>
    </div>
  )
}

export function FormSection({
  children,
  delay = 0,
  visible,
}: {
  children: ReactNode
  delay?: number
  visible: boolean
}) {
  return (
    <div
      className={`form-section ${visible ? 'form-section-visible' : ''}`}
      style={{ transitionDelay: visible ? `${delay}ms` : '0ms' }}
    >
      {children}
    </div>
  )
}

export function FormLabel({ children, required }: { children: ReactNode; required?: boolean }) {
  return (
    <label className="block text-sm font-medium text-civic-900 mb-2.5">
      {children}
      {required && <span className="text-warm-500 ml-0.5 font-normal">*</span>}
    </label>
  )
}

export function useFormReveal() {
  const [visible, setVisible] = useState(false)
  useEffect(() => {
    const id = requestAnimationFrame(() => setVisible(true))
    return () => cancelAnimationFrame(id)
  }, [])
  return visible
}
