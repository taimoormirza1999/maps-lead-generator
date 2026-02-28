const { Client, LocalAuth } = require('whatsapp-web.js');
const qrcode = require('qrcode-terminal');
const fs = require('fs');
const path = require('path');
const csv = require('csv-parser');
const { createObjectCsvWriter } = require('csv-writer');

// Get CSV file path from command line args
const csvFile = process.argv[2];
if (!csvFile) {
    console.log('Usage: node whatsapp_checker.js <path-to-csv>');
    process.exit(1);
}

const client = new Client({
    authStrategy: new LocalAuth(),
    puppeteer: { headless: true }
});

client.on('qr', (qr) => {
    console.log('\nScan this QR code with WhatsApp on your phone:\n');
    qrcode.generate(qr, { small: true });
});

client.on('ready', async () => {
    console.log('\nWhatsApp connected! Checking numbers...\n');

    // Read CSV
    const rows = [];
    const headers = [];

    await new Promise((resolve) => {
        fs.createReadStream(csvFile)
            .pipe(csv())
            .on('headers', (h) => headers.push(...h))
            .on('data', (row) => rows.push(row))
            .on('end', resolve);
    });

    // Check each phone number
    for (let i = 0; i < rows.length; i++) {
        const row = rows[i];
        let phone = row.Phone || '';

        // Clean phone number: remove ', spaces, dashes, +
        const cleaned = phone.replace(/['\s\-\+\(\)]/g, '');

        if (cleaned) {
            try {
                // WhatsApp ID format: number@c.us
                const numberId = await client.getNumberId(cleaned);
                if (numberId) {
                    row.WhatsApp = 'Yes';
                    console.log(`  [${i + 1}/${rows.length}] ${row.Name}: ${phone} -> WhatsApp: Yes`);
                } else {
                    row.WhatsApp = 'No';
                    console.log(`  [${i + 1}/${rows.length}] ${row.Name}: ${phone} -> WhatsApp: No`);
                }
            } catch (err) {
                row.WhatsApp = 'Error';
                console.log(`  [${i + 1}/${rows.length}] ${row.Name}: ${phone} -> Error: ${err.message}`);
            }
        } else {
            row.WhatsApp = 'No Phone';
            console.log(`  [${i + 1}/${rows.length}] ${row.Name}: No phone number`);
        }

        // Small delay to avoid rate limiting
        await new Promise(r => setTimeout(r, 1000));
    }

    // Write updated CSV
    const outputFile = csvFile.replace('.csv', '_whatsapp.csv');
    const csvWriter = createObjectCsvWriter({
        path: outputFile,
        header: [...headers, 'WhatsApp'].map(h => ({ id: h, title: h }))
    });

    await csvWriter.writeRecords(rows);
    console.log(`\nDone! Results saved to: ${outputFile}`);
    console.log(`Total: ${rows.length} | WhatsApp: ${rows.filter(r => r.WhatsApp === 'Yes').length} | Not on WhatsApp: ${rows.filter(r => r.WhatsApp === 'No').length}`);

    await client.destroy();
    process.exit(0);
});

client.on('auth_failure', (msg) => {
    console.error('Authentication failed:', msg);
    process.exit(1);
});

console.log('Initializing WhatsApp client...');
client.initialize();
