import { useState } from 'react'
import { Outlet } from 'react-router-dom'
import { AnimatePresence, motion } from 'framer-motion'
import { X } from 'lucide-react'
import { Sidebar } from '@/components/Sidebar'
import { Topbar } from '@/components/Topbar'
import { PageTransition } from '@/components/PageTransition'
import { FarmDataProvider } from '@/context/FarmDataContext'

export function AppLayout() {
  const [mobileOpen, setMobileOpen] = useState(false)

  return (
    <FarmDataProvider>
      <div className="field-grid flex h-screen overflow-hidden bg-[var(--bg-app)]">
        <div className="hidden lg:block">
          <Sidebar />
        </div>

        <AnimatePresence>
          {mobileOpen && (
            <>
              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                className="fixed inset-0 z-40 bg-black/30 lg:hidden"
                onClick={() => setMobileOpen(false)}
              />
              <motion.div
                initial={{ x: -260 }}
                animate={{ x: 0 }}
                exit={{ x: -260 }}
                transition={{ type: 'tween', duration: 0.2 }}
                className="fixed inset-y-0 left-0 z-50 lg:hidden"
              >
                <div className="relative h-full">
                  <Sidebar onNavigate={() => setMobileOpen(false)} />
                  <button
                    onClick={() => setMobileOpen(false)}
                    aria-label="Close menu"
                    className="absolute right-3 top-4 rounded-lg bg-[var(--bg-surface-muted)] p-1.5"
                  >
                    <X size={16} aria-hidden="true" />
                  </button>
                </div>
              </motion.div>
            </>
          )}
        </AnimatePresence>

        <div className="flex min-w-0 flex-1 flex-col">
          <Topbar onMenuClick={() => setMobileOpen(true)} />
          <main className="flex-1 overflow-y-auto px-4 py-5 sm:px-6 sm:py-6">
            <PageTransition>
              <Outlet />
            </PageTransition>
          </main>
        </div>
      </div>
    </FarmDataProvider>
  )
}
