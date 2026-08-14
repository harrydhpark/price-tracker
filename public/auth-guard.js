/**
 * LGE TV Europe/CIS Sub-Dashboard Unified Auth Guard & SSO Handler
 * - SHA-256 Credentials Verification (LGE135 / LGE246)
 * - 30-Minute Session Timeout with Activity Auto-Extension
 * - Portal SSO URL Token Parser & Address Bar Cleanup
 */
(function() {
  const AUTH_CONFIG = {
    ID_HASH: '4ed89d4c95cd896421176fe47e4c9ee9a0baad02dae39f57ce32eef58ec8e942', // 'LGE135'
    PW_HASH: '618db43b60c434d96fa46606dfd55e64a4ee7321f05b6dd846f5b5bea2e7cade', // 'LGE246'
    SESSION_KEY: 'lge_subdash_auth_user',
    TIMESTAMP_KEY: 'lge_subdash_auth_timestamp',
    TIMEOUT_MS: 30 * 60 * 1000, // 30 minutes
    SECRET: 'LGE_TV_EU_PORTAL_SECRET_2026'
  };

  async function sha256(message) {
    const msgBuffer = new TextEncoder().encode(message);
    const hashBuffer = await crypto.subtle.digest('SHA-256', msgBuffer);
    const hashArray = Array.from(new Uint8Array(hashBuffer));
    return hashArray.map(b => b.toString(16).padStart(2, '0')).join('');
  }

  // Inject critical CSS immediately into <head> to block unauthenticated page render
  const style = document.createElement('style');
  style.id = 'authGuardStyles';
  style.textContent = `
    .ag-login-overlay {
      position: fixed;
      top: 0;
      left: 0;
      width: 100vw;
      height: 100vh;
      background-color: #0f172a;
      background-image: 
        radial-gradient(at 0% 0%, rgba(13, 148, 136, 0.2) 0px, transparent 50%),
        radial-gradient(at 100% 100%, rgba(59, 130, 246, 0.15) 0px, transparent 50%);
      z-index: 9999999;
      display: flex;
      align-items: center;
      justify-content: center;
      padding: 20px;
      box-sizing: border-box;
      font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
      opacity: 1;
      visibility: visible;
      transition: opacity 0.2s ease, visibility 0.2s ease;
    }
    .ag-login-overlay.hidden {
      opacity: 0 !important;
      visibility: hidden !important;
      pointer-events: none !important;
      display: none !important;
    }
    .ag-login-card {
      background: #ffffff;
      border-radius: 12px;
      box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.5);
      padding: 36px 32px;
      width: 100%;
      max-width: 420px;
      box-sizing: border-box;
    }
    .ag-login-header {
      text-align: center;
      margin-bottom: 24px;
    }
    .ag-login-icon {
      width: 52px;
      height: 52px;
      border-radius: 14px;
      background: #0f172a;
      color: #0d9488;
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 26px;
      margin: 0 auto 14px;
    }
    .ag-login-title {
      font-size: 20px;
      font-weight: 700;
      color: #0f172a;
      margin: 0 0 6px;
    }
    .ag-login-subtitle {
      font-size: 13px;
      color: #64748b;
      margin: 0;
    }
    .ag-input-group {
      margin-bottom: 16px;
      text-align: left;
    }
    .ag-input-group label {
      display: block;
      font-size: 12px;
      font-weight: 600;
      color: #0f172a;
      margin-bottom: 6px;
    }
    .ag-input-wrapper {
      position: relative;
    }
    .ag-input-wrapper input {
      width: 100%;
      padding: 11px 14px;
      font-size: 14px;
      color: #0f172a;
      background: #f8fafc;
      border: 1px solid #cbd5e1;
      border-radius: 8px;
      outline: none;
      box-sizing: border-box;
      transition: border-color 0.2s;
    }
    .ag-input-wrapper input:focus {
      border-color: #0d9488;
      background: #ffffff;
    }
    .ag-error-msg {
      display: none;
      align-items: center;
      gap: 6px;
      padding: 8px 12px;
      background: #fef2f2;
      border: 1px solid #fecaca;
      border-radius: 6px;
      color: #dc2626;
      font-size: 12px;
      font-weight: 600;
      margin-bottom: 16px;
    }
    .ag-submit-btn {
      width: 100%;
      padding: 12px;
      background: linear-gradient(135deg, #0d9488 0%, #0f766e 100%);
      color: #ffffff;
      border: none;
      border-radius: 8px;
      font-size: 14px;
      font-weight: 600;
      cursor: pointer;
      transition: transform 0.15s, background 0.2s;
    }
    .ag-submit-btn:hover {
      transform: translateY(-1px);
    }
    .ag-footer-info {
      font-size: 11px;
      color: #94a3b8;
      border-top: 1px solid #e2e8f0;
      margin-top: 20px;
      padding-top: 14px;
      text-align: center;
    }
  `;
  if (document.head) {
    document.head.appendChild(style);
  } else {
    document.addEventListener('DOMContentLoaded', () => document.head.appendChild(style));
  }

  function injectOverlayHtml() {
    if (document.getElementById('authGuardLoginOverlay')) return;
    const overlay = document.createElement('div');
    overlay.className = 'ag-login-overlay';
    overlay.id = 'authGuardLoginOverlay';
    overlay.innerHTML = `
      <div class="ag-login-card">
        <div class="ag-login-header">
          <div class="ag-login-icon">🔒</div>
          <h2 class="ag-login-title">TV EU/CIS Dashboard System</h2>
          <p class="ag-login-subtitle">보안 대시보드 접속을 위해 인증 정보를 입력하세요.</p>
        </div>
        <form id="agLoginForm" autocomplete="off" onsubmit="return false;">
          <div class="ag-input-group">
            <label for="agUsernameInput">아이디 (ID)</label>
            <div class="ag-input-wrapper">
              <input type="text" id="agUsernameInput" placeholder="아이디 입력 (대소문자 구분)" required autocomplete="username">
            </div>
          </div>
          <div class="ag-input-group">
            <label for="agPasswordInput">비밀번호 (Password)</label>
            <div class="ag-input-wrapper">
              <input type="password" id="agPasswordInput" placeholder="비밀번호 입력 (대소문자 구분)" required autocomplete="current-password">
            </div>
          </div>
          <div id="agErrorMsg" class="ag-error-msg">
            <span>아이디 또는 비밀번호가 일치하지 않습니다.</span>
          </div>
          <button type="submit" id="agSubmitBtn" class="ag-submit-btn">대시보드 접속하기</button>
        </form>
        <div class="ag-footer-info">LGE TV EU/CIS Sales & Marketing Security Portal</div>
      </div>
    `;
    (document.body || document.documentElement).appendChild(overlay);

    const form = document.getElementById('agLoginForm');
    if (form) form.addEventListener('submit', handleLogin);
  }

  function updateAuthActivity() {
    const authUser = sessionStorage.getItem(AUTH_CONFIG.SESSION_KEY);
    if (authUser) {
      sessionStorage.setItem(AUTH_CONFIG.TIMESTAMP_KEY, Date.now().toString());
    }
  }

  function clearAuthSession() {
    sessionStorage.removeItem(AUTH_CONFIG.SESSION_KEY);
    sessionStorage.removeItem(AUTH_CONFIG.TIMESTAMP_KEY);
  }

  async function checkSsoUrlToken() {
    const params = new URLSearchParams(window.location.search);
    const token = params.get('auth_token');
    const tsStr = params.get('auth_ts');
    const user = params.get('auth_user');

    if (token && tsStr && user) {
      const ts = parseInt(tsStr, 10);
      const now = Date.now();
      if (!isNaN(ts) && Math.abs(now - ts) < 5 * 60 * 1000) {
        const expectedSig = await sha256(user + ":" + ts + ":" + AUTH_CONFIG.SECRET);
        if (expectedSig === token) {
          sessionStorage.setItem(AUTH_CONFIG.SESSION_KEY, user);
          sessionStorage.setItem(AUTH_CONFIG.TIMESTAMP_KEY, now.toString());

          const cleanUrl = window.location.pathname + window.location.hash;
          window.history.replaceState({}, document.title, cleanUrl);
          return true;
        }
      }
    }
    return false;
  }

  async function checkAuthStatus() {
    const ssoSuccess = await checkSsoUrlToken();
    const authUser = sessionStorage.getItem(AUTH_CONFIG.SESSION_KEY);
    const lastActivity = sessionStorage.getItem(AUTH_CONFIG.TIMESTAMP_KEY);
    const now = Date.now();

    const isValid = ssoSuccess || (authUser && lastActivity && (now - parseInt(lastActivity, 10) < AUTH_CONFIG.TIMEOUT_MS));

    const overlay = document.getElementById('authGuardLoginOverlay');
    if (isValid) {
      updateAuthActivity();
      if (overlay) overlay.classList.add('hidden');
    } else {
      clearAuthSession();
      if (overlay) overlay.classList.remove('hidden');
      const input = document.getElementById('agUsernameInput');
      if (input) setTimeout(() => input.focus(), 100);
    }
  }

  async function handleLogin(e) {
    if (e) e.preventDefault();
    const userInput = document.getElementById('agUsernameInput');
    const pwInput = document.getElementById('agPasswordInput');
    const errorMsg = document.getElementById('agErrorMsg');
    const submitBtn = document.getElementById('agSubmitBtn');

    if (!userInput || !pwInput) return;
    const enteredId = userInput.value.trim();
    const enteredPw = pwInput.value.trim();

    if (!enteredId || !enteredPw) return;
    if (submitBtn) submitBtn.disabled = true;

    try {
      const idHash = await sha256(enteredId);
      const pwHash = await sha256(enteredPw);

      if (idHash === AUTH_CONFIG.ID_HASH && pwHash === AUTH_CONFIG.PW_HASH) {
        sessionStorage.setItem(AUTH_CONFIG.SESSION_KEY, enteredId);
        sessionStorage.setItem(AUTH_CONFIG.TIMESTAMP_KEY, Date.now().toString());
        if (errorMsg) errorMsg.style.display = 'none';
        userInput.value = '';
        pwInput.value = '';
        checkAuthStatus();
      } else {
        if (errorMsg) errorMsg.style.display = 'flex';
        pwInput.value = '';
        pwInput.focus();
      }
    } catch (err) {
      console.error("Auth Error", err);
    } finally {
      if (submitBtn) submitBtn.disabled = false;
    }
  }

  let activityThrottleTimer = null;
  function setupActivityListeners() {
    const events = ['mousemove', 'keydown', 'click', 'scroll', 'touchstart'];
    events.forEach(evt => {
      window.addEventListener(evt, () => {
        if (!activityThrottleTimer) {
          updateAuthActivity();
          activityThrottleTimer = setTimeout(() => {
            activityThrottleTimer = null;
          }, 10000);
        }
      }, { passive: true });
    });

    setInterval(checkAuthStatus, 60000);
  }

  function init() {
    injectOverlayHtml();
    setupActivityListeners();
    checkAuthStatus();
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
