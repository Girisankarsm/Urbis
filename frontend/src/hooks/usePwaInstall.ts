import { useCallback, useEffect, useRef, useState } from 'react'

interface BeforeInstallPromptEvent extends Event {
  prompt: () => Promise<void>
  userChoice: Promise<{ outcome: 'accepted' | 'dismissed' }>
}

function isStandalone(): boolean {
  return (
    window.matchMedia('(display-mode: standalone)').matches ||
    (window.navigator as Navigator & { standalone?: boolean }).standalone === true
  )
}

export function usePwaInstall() {
  const deferredRef = useRef<BeforeInstallPromptEvent | null>(null)
  const [isInstalled, setIsInstalled] = useState(isStandalone)
  const [canNativeInstall, setCanNativeInstall] = useState(false)

  useEffect(() => {
    setIsInstalled(isStandalone())

    const onBeforeInstall = (event: Event) => {
      event.preventDefault()
      deferredRef.current = event as BeforeInstallPromptEvent
      setCanNativeInstall(true)
    }

    const onInstalled = () => {
      setIsInstalled(true)
      setCanNativeInstall(false)
      deferredRef.current = null
    }

    window.addEventListener('beforeinstallprompt', onBeforeInstall)
    window.addEventListener('appinstalled', onInstalled)
    return () => {
      window.removeEventListener('beforeinstallprompt', onBeforeInstall)
      window.removeEventListener('appinstalled', onInstalled)
    }
  }, [])

  const install = useCallback(async () => {
    if (isInstalled) return

    if (deferredRef.current) {
      await deferredRef.current.prompt()
      const { outcome } = await deferredRef.current.userChoice
      if (outcome === 'accepted') {
        setIsInstalled(true)
      }
      deferredRef.current = null
      setCanNativeInstall(false)
      return
    }

    const isIOS = /iphone|ipad|ipod/i.test(navigator.userAgent)
    if (isIOS) {
      window.alert(
        'Install Urbis on your iPhone:\n\n1. Tap Share (square with arrow)\n2. Tap "Add to Home Screen"\n3. Tap Add',
      )
      return
    }

    window.alert(
      'Install Urbis on your phone:\n\nOpen the browser menu (⋮) and choose "Install app" or "Add to Home screen".',
    )
  }, [isInstalled])

  const showInstall = !isInstalled

  return { install, showInstall, isInstalled, canNativeInstall }
}
