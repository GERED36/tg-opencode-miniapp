import { useEffect, useState } from 'react'

interface ToastProps {
  message: string
  type?: 'error' | 'success' | 'info'
  onClose: () => void
}

export default function Toast({ message, type = 'info', onClose }: ToastProps) {
  const [visible, setVisible] = useState(false)

  useEffect(() => {
    requestAnimationFrame(() => setVisible(true))
    const timer = setTimeout(() => {
      setVisible(false)
      setTimeout(onClose, 300)
    }, 3000)
    return () => clearTimeout(timer)
  }, [onClose])

  const bgColor = type === 'error' ? 'bg-oc-red/20 border-oc-red/40' :
                  type === 'success' ? 'bg-oc-green/20 border-oc-green/40' :
                  'bg-oc-surface/90 border-oc-border/40'

  return (
    <div className={`fixed top-20 left-3 right-3 z-50 max-w-[768px] mx-auto transition-all duration-300 ${
      visible ? 'opacity-100 translate-y-0' : 'opacity-0 -translate-y-4'
    }`}>
      <div className={`rounded-2xl backdrop-blur-[16px] border px-4 py-3 text-sm text-oc-text ${bgColor}`}>
        {message}
      </div>
    </div>
  )
}
