import React, { useEffect, useState } from 'react';
import { Snackbar, Alert, Button } from '@mui/material';
import { useRegisterSW } from 'virtual:pwa-register/react';

const ServiceWorkerManager = () => {
  const [showReloadPrompt, setShowReloadPrompt] = useState(false);
  const [showOfflineAlert, setShowOfflineAlert] = useState(false);
  
  const {
    offlineReady: [offlineReady, setOfflineReady],
    needRefresh: [needRefresh, setNeedRefresh],
    updateServiceWorker,
  } = useRegisterSW({
    onRegistered(r) {
      console.log('Service Worker registered:', r);
    },
    onRegisterError(error) {
      console.error('Service Worker registration error:', error);
    },
  });
  
  // Handle online/offline status
  useEffect(() => {
    const handleOnline = () => setShowOfflineAlert(false);
    const handleOffline = () => setShowOfflineAlert(true);
    
    window.addEventListener('online', handleOnline);
    window.addEventListener('offline', handleOffline);
    
    // Check initial state
    if (!navigator.onLine) {
      setShowOfflineAlert(true);
    }
    
    return () => {
      window.removeEventListener('online', handleOnline);
      window.removeEventListener('offline', handleOffline);
    };
  }, []);
  
  useEffect(() => {
    if (offlineReady || needRefresh) {
      setShowReloadPrompt(true);
    }
  }, [offlineReady, needRefresh]);
  
  const handleReload = () => {
    updateServiceWorker(true);
    setShowReloadPrompt(false);
  };
  
  const handleClose = () => {
    setShowReloadPrompt(false);
    setOfflineReady(false);
    setNeedRefresh(false);
  };
  
  return (
    <>
      {/* Update available notification */}
      <Snackbar
        open={showReloadPrompt}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'center' }}
        onClose={handleClose}
      >
        <Alert
          severity="info"
          action={
            <>
              <Button color="inherit" size="small" onClick={handleReload}>
                Reload
              </Button>
              <Button color="inherit" size="small" onClick={handleClose}>
                Later
              </Button>
            </>
          }
        >
          {offlineReady
            ? 'App ready to work offline'
            : 'New content available, click reload to update'}
        </Alert>
      </Snackbar>
      
      {/* Offline notification */}
      <Snackbar
        open={showOfflineAlert}
        anchorOrigin={{ vertical: 'top', horizontal: 'center' }}
      >
        <Alert severity="warning">
          You are currently offline. Some features may be limited.
        </Alert>
      </Snackbar>
    </>
  );
};

export default ServiceWorkerManager;