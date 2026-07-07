const { Client, LocalAuth } = require('whatsapp-web.js');
const qrcode = require('qrcode-terminal');

const numbers = [
    '302109219994',
    '302103212858',
    '302103426794',
    '302103300864',
    '302109212280',
    '302103210181',
    '302103252255',
    '302105202339',
    '302103247797',
    '302105243987',
    '302103252282',
    '302103222227',
    '302103248782',
    '302110171862',
    '302155017853',
    '302103417010',
    '302103458463',
    '302103469077',
    '302103216001',
    '306982247704',
    '306936060481',
    '302155400334',
    '302111821935',
    '302103251361',
    '302160047777',
    '302105222633',
];

const client = new Client({
    authStrategy: new LocalAuth(),
    puppeteer: { headless: true }
});

client.on('qr', (qr) => {
    console.log('\n📱 Scan this QR code with WhatsApp:\n');
    qrcode.generate(qr, { small: true });
});

client.on('ready', async () => {
    console.log('\n✅ WhatsApp connected! Checking numbers...\n');

    const results = { whatsapp: [], notWhatsapp: [] };

    for (const number of numbers) {
        try {
            const numberId = await client.getNumberId(number);
            if (numberId) {
                results.whatsapp.push(number);
                console.log(`✅ +${number} — ON WhatsApp`);
            } else {
                results.notWhatsapp.push(number);
                console.log(`❌ +${number} — NOT on WhatsApp`);
            }
        } catch (err) {
            results.notWhatsapp.push(number);
            console.log(`❌ +${number} — NOT on WhatsApp (error)`);
        }
    }

    console.log('\n========== SUMMARY ==========');
    console.log(`\n✅ On WhatsApp (${results.whatsapp.length}):`);
    results.whatsapp.forEach(n => console.log(`  +${n}`));
    console.log(`\n❌ Not on WhatsApp (${results.notWhatsapp.length}):`);
    results.notWhatsapp.forEach(n => console.log(`  +${n}`));

    console.log('\nDone! Closing...');
    await client.destroy();
    process.exit(0);
});

client.on('auth_failure', () => {
    console.error('Authentication failed. Try deleting .wwebjs_auth folder and retry.');
    process.exit(1);
});

console.log('Starting WhatsApp client...');
client.initialize();
