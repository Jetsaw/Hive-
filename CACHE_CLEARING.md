# HIVE - Cache Clearing Guide

## ⚠️ Important: Clear Browser Cache After Updates

After deploying new frontend code, users need to clear their browser cache to see the latest changes.

### Quick Instructions

**Chrome/Edge/Brave:**
- Windows: `Ctrl + Shift + R`
- Mac: `Cmd + Shift + R`

**Firefox:**
- Windows: `Ctrl + F5`
- Mac: `Cmd + Shift + R`

**Safari:**
- Mac: `Cmd + Option + E` (Empty Caches), then `Cmd + R` (Reload)

### Full Cache Clear (if hard refresh doesn't work)

**Chrome/Edge/Brave:**
1. Press `F12` to open DevTools
2. Click "Application" tab
3. Click "Clear storage" in left sidebar
4. Click "Clear site data" button
5. Close DevTools and reload

**Firefox:**
1. Press `Ctrl+Shift+Delete` (Windows) or `Cmd+Shift+Delete` (Mac)
2. Select "Cached Web Content"
3. Click "Clear Now"
4. Reload the page

### For Developers

When deploying frontend updates, consider adding a cache-busting parameter:

```javascript
// In HTML
<script src="/js/main.js?v=2.0.1"></script>

// Or dynamic versioning
<script src="/js/main.js?v=<%= BUILD_TIMESTAMP %>"></script>
```

### Verifying Cache Clear

1. Open browser DevTools (`F12`)
2. Go to Network tab
3. Check "Disable cache" option
4. Reload page
5. Verify files are loaded from server (Status 200, not 304)

---

**Last Updated:** 2026-01-29  
**Related Files:**
- `hive-frontend/js/services/api.js` - API response handling
- `hive-frontend/js/main.js` - Main application
