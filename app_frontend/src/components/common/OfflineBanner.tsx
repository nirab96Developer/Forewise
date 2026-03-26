// components/common/OfflineBanner.tsx
// פס צר בראש המסך כשאין חיבור + אתחול globalShowToast

import { useEffect } from 'react';
import { useToast } from './Toast';
import { setGlobalToast } from './Toast';
import { useOfflineSync } from '../../hooks/useOfflineSync';

export function OfflineBanner() {
  const { showToast } = useToast();
  const { isOnline } = useOfflineSync();

  // Wire up the global showToast so it works from outside React
  useEffect(() => {
    setGlobalToast(showToast);
  }, [showToast]);

  if (isOnline) return null;

  return (
    <div
      className="fixed top-0 left-0 right-0 z-[9999] flex items-center justify-center gap-2 py-2 px-4 text-white text-sm font-medium"
      style={{ backgroundColor: '#F59E0B' }}
    >
<span></span>
      <span>אין חיבור לאינטרנט — השינויים נשמרים במכשיר</span>
    </div>
  );
}
